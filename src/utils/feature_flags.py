"""
Sistema de Feature Flags para habilitar/desabilitar funcionalidades.
Sprint 20 - Tarefa 3

Feature flags permitem ativar/desativar funcionalidades sem alterar código,
útil para:
- Testes A/B
- Rollout gradual de features
- Desabilitar features com problemas
- Desenvolvimento em produção
"""

import json
import os
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
from src.core.config_logs import get_logger

logger = get_logger(__name__)


class FeatureFlags:
    """
    Gerenciador de feature flags.
    
    Permite habilitar/desabilitar features dinamicamente através de:
    - Arquivo de configuração JSON
    - Variáveis de ambiente
    - Código (fallback)
    
    Attributes:
        _flags: Dicionário com estado das flags
        _config_file: Caminho do arquivo de configuração
        _callbacks: Callbacks chamados quando flags mudam
    """
    
    def __init__(self, config_file: str = 'feature_flags.json'):
        """
        Inicializa o sistema de feature flags.
        
        Args:
            config_file: Caminho do arquivo de configuração JSON
        """
        self._config_file = Path(config_file)
        self._flags: Dict[str, Dict[str, Any]] = {}
        self._callbacks: Dict[str, list[Callable]] = {}
        self._load_flags()
    
    def _load_flags(self) -> None:
        """Carrega flags do arquivo de configuração."""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._flags = data.get('flags', {})
                    logger.debug(f"Feature flags carregadas de {self._config_file}")
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao ler feature flags: {e}")
                self._flags = {}
        else:
            logger.debug(f"Arquivo {self._config_file} não encontrado, usando flags padrão")
            self._flags = self._get_default_flags()
            self._save_flags()
    
    def _save_flags(self) -> None:
        """Salva flags no arquivo de configuração."""
        try:
            data = {
                'flags': self._flags,
                'last_updated': datetime.now().isoformat()
            }
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Feature flags salvas em {self._config_file}")
        except Exception as e:
            logger.error(f"Erro ao salvar feature flags: {e}")
    
    def _get_default_flags(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna flags padrão do sistema.
        
        Returns:
            Dicionário com flags padrão
        """
        return {
            'cache_enabled': {
                'enabled': True,
                'description': 'Habilita cache de estatísticas e queries',
                'category': 'performance'
            },
            'pydantic_validation': {
                'enabled': True,
                'description': 'Habilita validação Pydantic em services',
                'category': 'validation'
            },
            'json_logs': {
                'enabled': False,
                'description': 'Usa formato JSON para logs',
                'category': 'logging'
            },
            'backup_automatico': {
                'enabled': True,
                'description': 'Habilita backup automático do banco',
                'category': 'backup'
            },
            'dashboard_avancado': {
                'enabled': True,
                'description': 'Mostra dashboard com estatísticas avançadas',
                'category': 'ui'
            },
            'modo_debug': {
                'enabled': False,
                'description': 'Ativa logs de debug e informações extras',
                'category': 'debug'
            },
            'relatorios_pdf': {
                'enabled': True,
                'description': 'Permite geração de relatórios em PDF',
                'category': 'features'
            },
            'integracao_drive': {
                'enabled': False,
                'description': 'Habilita integração com Google Drive',
                'category': 'integration'
            }
        }
    
    def is_enabled(self, flag_name: str, default: bool = False) -> bool:
        """
        Verifica se uma feature está habilitada.
        
        Ordem de prioridade:
        1. Variável de ambiente FEATURE_<FLAG_NAME>
        2. Arquivo de configuração
        3. Valor default fornecido
        
        Args:
            flag_name: Nome da feature flag
            default: Valor padrão se flag não existir
            
        Returns:
            True se feature está habilitada
            
        Example:
            if flags.is_enabled('cache_enabled'):
                # usar cache
        """
        # Verificar variável de ambiente primeiro
        env_var = f"FEATURE_{flag_name.upper()}"
        env_value = os.getenv(env_var)
        if env_value is not None:
            return env_value.lower() in ('1', 'true', 'yes', 'on')
        
        # Verificar arquivo de configuração
        flag_config = self._flags.get(flag_name, {})
        enabled = flag_config.get('enabled', default)
        return bool(enabled) if enabled is not None else default
    
    def enable(self, flag_name: str, description: str = '', category: str = 'general') -> None:
        """
        Habilita uma feature flag.
        
        Args:
            flag_name: Nome da flag
            description: Descrição da feature
            category: Categoria da feature
        """
        if flag_name not in self._flags:
            self._flags[flag_name] = {
                'description': description,
                'category': category
            }
        
        old_value = self._flags[flag_name].get('enabled', False)
        self._flags[flag_name]['enabled'] = True
        self._save_flags()
        
        logger.info(f"Feature flag '{flag_name}' habilitada")
        
        # Chamar callbacks se valor mudou
        if not old_value:
            self._trigger_callbacks(flag_name, True)
    
    def disable(self, flag_name: str) -> None:
        """
        Desabilita uma feature flag.
        
        Args:
            flag_name: Nome da flag
        """
        if flag_name in self._flags:
            old_value = self._flags[flag_name].get('enabled', False)
            self._flags[flag_name]['enabled'] = False
            self._save_flags()
            
            logger.info(f"Feature flag '{flag_name}' desabilitada")
            
            # Chamar callbacks se valor mudou
            if old_value:
                self._trigger_callbacks(flag_name, False)
    
    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna todas as feature flags.
        
        Returns:
            Dicionário com todas as flags e suas configurações
        """
        return self._flags.copy()
    
    def get_enabled_flags(self) -> list[str]:
        """
        Retorna lista de flags habilitadas.
        
        Returns:
            Lista com nomes das flags habilitadas
        """
        return [
            name for name, config in self._flags.items()
            if self.is_enabled(name)
        ]
    
    def get_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """
        Retorna flags de uma categoria específica.
        
        Args:
            category: Nome da categoria
            
        Returns:
            Dicionário com flags da categoria
        """
        return {
            name: config
            for name, config in self._flags.items()
            if config.get('category') == category
        }
    
    def register_callback(self, flag_name: str, callback: Callable[[bool], None]) -> None:
        """
        Registra callback para ser chamado quando flag mudar.
        
        Args:
            flag_name: Nome da flag
            callback: Função que recebe o novo valor (bool)
            
        Example:
            def on_cache_change(enabled: bool):
                if enabled:
                    init_cache()
                else:
                    clear_cache()
            
            flags.register_callback('cache_enabled', on_cache_change)
        """
        if flag_name not in self._callbacks:
            self._callbacks[flag_name] = []
        self._callbacks[flag_name].append(callback)
        logger.debug(f"Callback registrado para flag '{flag_name}'")
    
    def _trigger_callbacks(self, flag_name: str, new_value: bool) -> None:
        """
        Dispara callbacks registrados para uma flag.
        
        Args:
            flag_name: Nome da flag
            new_value: Novo valor da flag
        """
        if flag_name in self._callbacks:
            for callback in self._callbacks[flag_name]:
                try:
                    callback(new_value)
                except Exception as e:
                    logger.error(f"Erro ao executar callback para '{flag_name}': {e}")
    
    def reload(self) -> None:
        """Recarrega flags do arquivo de configuração."""
        logger.info("Recarregando feature flags")
        self._load_flags()
    
    def reset_to_defaults(self) -> None:
        """Reseta todas as flags para valores padrão."""
        logger.warning("Resetando feature flags para valores padrão")
        self._flags = self._get_default_flags()
        self._save_flags()


# Instância global de feature flags
_global_flags: Optional[FeatureFlags] = None


def get_feature_flags(config_file: str = 'feature_flags.json') -> FeatureFlags:
    """
    Retorna instância global de feature flags.
    
    Args:
        config_file: Caminho do arquivo de configuração
        
    Returns:
        Instância de FeatureFlags
    """
    global _global_flags
    if _global_flags is None:
        _global_flags = FeatureFlags(config_file)
    return _global_flags


def is_feature_enabled(flag_name: str, default: bool = False) -> bool:
    """
    Atalho para verificar se feature está habilitada.
    
    Args:
        flag_name: Nome da feature flag
        default: Valor padrão
        
    Returns:
        True se habilitada
    """
    flags = get_feature_flags()
    return flags.is_enabled(flag_name, default)
