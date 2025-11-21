"""
Testes para o sistema de cache.
"""

import pytest
import time
from utils.cache import CacheManager, global_cache, dashboard_cache


def test_cache_basico():
    """Testa operações básicas de cache."""
    cache = CacheManager(ttl_seconds=5)
    
    # Teste set/get
    cache.set('chave1', 'valor1')
    assert cache.get('chave1') == 'valor1'
    
    # Teste miss
    assert cache.get('chave_inexistente') is None


def test_cache_ttl():
    """Testa expiração do cache."""
    cache = CacheManager(ttl_seconds=1)
    
    cache.set('chave_temporaria', 'valor')
    assert cache.get('chave_temporaria') == 'valor'
    
    # Aguarda expirar
    time.sleep(1.1)
    assert cache.get('chave_temporaria') is None


def test_cache_invalidacao():
    """Testa invalidação de cache."""
    cache = CacheManager(ttl_seconds=10)
    
    cache.set('chave1', 'valor1')
    cache.set('chave2', 'valor2')
    
    # Invalida específica
    cache.invalidate('chave1')
    assert cache.get('chave1') is None
    assert cache.get('chave2') == 'valor2'
    
    # Invalida todas
    cache.invalidate()
    assert cache.get('chave2') is None


def test_cache_decorator():
    """Testa decorator de cache."""
    cache = CacheManager(ttl_seconds=5)
    call_count = 0
    
    @cache.cached()
    def funcao_lenta(x):
        nonlocal call_count
        call_count += 1
        return x * 2
    
    # Primeira chamada executa função
    resultado1 = funcao_lenta(5)
    assert resultado1 == 10
    assert call_count == 1
    
    # Segunda chamada usa cache
    resultado2 = funcao_lenta(5)
    assert resultado2 == 10
    assert call_count == 1  # Não executou novamente
    
    # Chamada com parâmetro diferente
    resultado3 = funcao_lenta(3)
    assert resultado3 == 6
    assert call_count == 2


def test_cache_estatisticas():
    """Testa estatísticas do cache."""
    cache = CacheManager(ttl_seconds=10)
    
    # Gera hits e misses
    cache.set('chave1', 'valor1')
    cache.get('chave1')  # hit
    cache.get('chave1')  # hit
    cache.get('chave2')  # miss
    
    stats = cache.get_stats()
    
    assert stats['hits'] == 2
    assert stats['misses'] == 1
    assert stats['sets'] == 1
    assert stats['hit_rate'] == 66.67


def test_cache_pattern_invalidation():
    """Testa invalidação por padrão."""
    cache = CacheManager(ttl_seconds=10)
    
    cache.set('funcao1:arg1', 'valor1')
    cache.set('funcao1:arg2', 'valor2')
    cache.set('funcao2:arg1', 'valor3')
    
    # Invalida todas as chaves que começam com 'funcao1:'
    count = cache.invalidate_pattern('funcao1:')
    
    assert count == 2
    assert cache.get('funcao1:arg1') is None
    assert cache.get('funcao1:arg2') is None
    assert cache.get('funcao2:arg1') == 'valor3'


def test_cache_cleanup():
    """Testa limpeza de entradas expiradas."""
    cache = CacheManager(ttl_seconds=1)
    
    cache.set('chave1', 'valor1')
    cache.set('chave2', 'valor2')
    
    # Aguarda expirar
    time.sleep(1.1)
    
    # Adiciona nova chave
    cache.set('chave3', 'valor3')
    
    # Limpa expiradas
    removed = cache.cleanup_expired()
    
    assert removed == 2
    assert cache.get('chave1') is None
    assert cache.get('chave2') is None
    assert cache.get('chave3') == 'valor3'


def test_global_caches_existem():
    """Testa que caches globais foram criados."""
    assert global_cache is not None
    assert dashboard_cache is not None
    
    # Testa que funcionam
    global_cache.set('teste', 'valor')
    assert global_cache.get('teste') == 'valor'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
