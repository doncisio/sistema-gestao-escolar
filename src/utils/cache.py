"""
Sistema de cache inteligente com TTL, LRU e invalidação.

Este módulo fornece uma classe CacheManager para cachear resultados
de funções custosas com suporte a:
- TTL (Time To Live) configurável
- Tamanho máximo com política LRU (Least Recently Used)
- Invalidação manual ou automática
- Cleanup periódico de entradas expiradas
- Decorator para cache automático
- Estatísticas de cache (hits/misses)
- Tratamento correto de valores ``None`` cacheados
"""

from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Optional, Callable, Dict, Tuple
from functools import wraps
import threading
import logging

logger = logging.getLogger(__name__)

# Sentinel para distinguir "não encontrado" de valor None cacheado
_CACHE_MISS = object()


class CacheManager:
    """
    Gerenciador de cache com TTL e estatísticas.
    
    Exemplo:
        cache = CacheManager(ttl_seconds=300)  # 5 minutos
        
        @cache.cached()
        def funcao_custosa():
            return resultado
        
        # Ou uso manual
        cache.set('chave', valor)
        resultado = cache.get('chave')
    """
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 1024,
                 auto_cleanup_seconds: int = 0):
        """
        Inicializa o gerenciador de cache.

        Args:
            ttl_seconds: Tempo de vida do cache em segundos (padrão: 300 = 5 minutos)
            max_size: Número máximo de entradas (0 = ilimitado). Quando atingido,
                      a entrada menos recentemente usada (LRU) é removida.
            auto_cleanup_seconds: Intervalo em segundos para limpeza automática
                                  de entradas expiradas (0 = desabilitado).
        """
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._ttl = timedelta(seconds=ttl_seconds)
        self._max_size = max_size
        self._lock = threading.Lock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'invalidations': 0,
            'evictions': 0,
        }
        self._cleanup_timer: Optional[threading.Timer] = None
        self._cleanup_interval = auto_cleanup_seconds
        if auto_cleanup_seconds > 0:
            self._start_cleanup_timer()
        logger.debug(
            f"CacheManager inicializado com TTL={ttl_seconds}s, "
            f"max_size={max_size}, cleanup={auto_cleanup_seconds}s"
        )
    
    def get(self, key: str, default: Any = _CACHE_MISS) -> Any:
        """
        Recupera valor do cache se ainda válido.

        Args:
            key: Chave do cache
            default: Valor retornado quando a chave não existe ou expirou.
                     Se omitido, retorna o sentinel ``_CACHE_MISS``.

        Returns:
            Valor cacheado (pode ser ``None``) ou *default*.
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats['misses'] += 1
                logger.debug(f"Cache MISS: {key}")
                return default

            # Verifica se ainda está válido
            if datetime.now() - entry['timestamp'] < self._ttl:
                self._stats['hits'] += 1
                # Promove para o final (mais recente) na OrderedDict
                self._cache.move_to_end(key)
                logger.debug(f"Cache HIT: {key}")
                return entry['data']
            else:
                # Expirou, remove do cache
                del self._cache[key]
                self._stats['misses'] += 1
                logger.debug(f"Cache EXPIRED: {key}")
                return default
    
    def set(self, key: str, data: Any) -> None:
        """
        Armazena valor no cache.

        Args:
            key: Chave do cache
            data: Dados a serem cacheados (inclusive ``None``)
        """
        with self._lock:
            # Se a chave já existe, remova antes para atualizar posição LRU
            if key in self._cache:
                del self._cache[key]

            self._cache[key] = {
                'data': data,
                'timestamp': datetime.now()
            }
            self._stats['sets'] += 1

            # Aplica política LRU se max_size definido
            if self._max_size > 0:
                while len(self._cache) > self._max_size:
                    evicted_key, _ = self._cache.popitem(last=False)
                    self._stats['evictions'] += 1
                    logger.debug(f"Cache EVICT (LRU): {evicted_key}")

            logger.debug(f"Cache SET: {key}")
    
    def invalidate(self, key: Optional[str] = None) -> None:
        """
        Invalida cache.
        
        Args:
            key: Chave específica para invalidar. Se None, limpa todo o cache.
        """
        with self._lock:
            if key:
                if key in self._cache:
                    del self._cache[key]
                    self._stats['invalidations'] += 1
                    logger.info(f"Cache invalidado: {key}")
            else:
                count = len(self._cache)
                self._cache.clear()
                self._stats['invalidations'] += count
                logger.info(f"Cache completo invalidado ({count} entradas)")
    
    def cached(self, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
        """
        Decorator para cache automático de funções.
        
        Args:
            ttl: TTL específico para esta função (usa padrão se None)
            key_func: Função customizada para gerar chave do cache
        
        Exemplo:
            @cache.cached(ttl=600)
            def funcao_lenta(param1, param2):
                return resultado
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Gera chave do cache
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Chave padrão: nome_funcao:args:kwargs
                    args_str = ','.join(str(arg) for arg in args)
                    kwargs_str = ','.join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = f"{func.__name__}:{args_str}:{kwargs_str}"
                
                # Tenta recuperar do cache (usa sentinel para distinguir miss de None)
                cached_result = self.get(cache_key)
                if cached_result is not _CACHE_MISS:
                    return cached_result

                # Executa função e cacheia resultado
                result = func(*args, **kwargs)
                self.set(cache_key, result)

                return result
            
            # Adiciona método para invalidar cache da função (atributo dinâmico)
            setattr(wrapper, 'invalidate_cache', lambda: self.invalidate_pattern(f"{func.__name__}:"))
            
            return wrapper
        return decorator
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalida todas as entradas que correspondem ao padrão.
        
        Suporta wildcard '*' no final do padrão (ex: 'user:*' casa com 'user:1').
        Sem wildcard, usa correspondência exata com startswith.
        
        Args:
            pattern: Padrão de chave para invalidar (suporta * como wildcard)
            
        Returns:
            Número de entradas invalidadas
        """
        with self._lock:
            # Suporte a wildcard: 'user:*' → startswith('user:')
            if pattern.endswith('*'):
                prefix = pattern[:-1]
                keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            else:
                keys_to_delete = [k for k in self._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
            
            count = len(keys_to_delete)
            self._stats['invalidations'] += count
            
            if count > 0:
                logger.info(f"Cache invalidado por padrão '{pattern}': {count} entradas")
            
            return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.

        Returns:
            Dicionário com hits, misses, hit_rate, size, evictions, etc.
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0

            return {
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'sets': self._stats['sets'],
                'invalidations': self._stats['invalidations'],
                'evictions': self._stats['evictions'],
                'hit_rate': round(hit_rate, 2),
                'size': len(self._cache),
                'max_size': self._max_size,
                'total_requests': total_requests
            }
    
    def clear_stats(self) -> None:
        """Reseta estatísticas do cache."""
        with self._lock:
            self._stats = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'invalidations': 0,
                'evictions': 0,
            }
            logger.info("Estatísticas do cache resetadas")
    
    def cleanup_expired(self) -> int:
        """
        Remove entradas expiradas do cache.
        
        Returns:
            Número de entradas removidas
        """
        with self._lock:
            now = datetime.now()
            keys_to_delete = [
                k for k, v in self._cache.items()
                if now - v['timestamp'] >= self._ttl
            ]
            
            for key in keys_to_delete:
                del self._cache[key]
            
            count = len(keys_to_delete)
            if count > 0:
                logger.info(f"Limpeza de cache: {count} entradas expiradas removidas")
            
            return count


    # ------------------------------------------------------------------
    # Cleanup periódico
    # ------------------------------------------------------------------

    def _start_cleanup_timer(self) -> None:
        """Inicia timer para limpeza periódica de entradas expiradas."""
        if self._cleanup_interval <= 0:
            return
        self._cleanup_timer = threading.Timer(
            self._cleanup_interval, self._auto_cleanup
        )
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()

    def _auto_cleanup(self) -> None:
        """Callback do timer — limpa expirados e reagenda."""
        try:
            removed = self.cleanup_expired()
            if removed:
                logger.debug(f"Auto-cleanup removeu {removed} entradas expiradas")
        except Exception:
            logger.exception("Erro no auto-cleanup do cache")
        finally:
            self._start_cleanup_timer()

    def stop_cleanup(self) -> None:
        """Para o timer de limpeza automática."""
        if self._cleanup_timer is not None:
            self._cleanup_timer.cancel()
            self._cleanup_timer = None


# Instância global para uso em toda a aplicação
# TTL padrão de 5 minutos (300 segundos), max 1024 entradas
global_cache = CacheManager(ttl_seconds=300, max_size=1024)

# Cache específico para dashboard com TTL maior (10 minutos)
# Cleanup automático a cada 5 minutos
dashboard_cache = CacheManager(ttl_seconds=600, max_size=256, auto_cleanup_seconds=300)
