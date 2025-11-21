"""
Testes para o sistema de feature flags.
Sprint 20 - Tarefa 3
"""

import pytest
import json
import os
from pathlib import Path
from utils.feature_flags import (
    FeatureFlags,
    get_feature_flags,
    is_feature_enabled
)


class TestFeatureFlags:
    """Testes para a classe FeatureFlags."""
    
    def test_init_creates_default_flags(self, tmp_path):
        """Testa criação de flags padrão."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        assert config_file.exists()
        all_flags = flags.get_all()
        assert 'cache_enabled' in all_flags
        assert 'pydantic_validation' in all_flags
        assert 'json_logs' in all_flags
    
    def test_is_enabled_default(self, tmp_path):
        """Testa verificação de flag habilitada (padrão)."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        # Flags padrão habilitadas
        assert flags.is_enabled('cache_enabled') is True
        assert flags.is_enabled('pydantic_validation') is True
        
        # Flags padrão desabilitadas
        assert flags.is_enabled('json_logs') is False
        assert flags.is_enabled('modo_debug') is False
    
    def test_is_enabled_with_default(self, tmp_path):
        """Testa verificação com valor default."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        # Flag inexistente retorna default
        assert flags.is_enabled('flag_inexistente', default=True) is True
        assert flags.is_enabled('outra_flag', default=False) is False
    
    def test_enable_flag(self, tmp_path):
        """Testa habilitação de flag."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        # Desabilitar primeiro
        flags.disable('json_logs')
        assert flags.is_enabled('json_logs') is False
        
        # Habilitar
        flags.enable('json_logs')
        assert flags.is_enabled('json_logs') is True
    
    def test_disable_flag(self, tmp_path):
        """Testa desabilitação de flag."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        # Habilitar primeiro
        flags.enable('modo_debug')
        assert flags.is_enabled('modo_debug') is True
        
        # Desabilitar
        flags.disable('modo_debug')
        assert flags.is_enabled('modo_debug') is False
    
    def test_enable_new_flag(self, tmp_path):
        """Testa habilitação de nova flag."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        flags.enable('nova_feature', description='Nova funcionalidade', category='test')
        
        assert flags.is_enabled('nova_feature') is True
        all_flags = flags.get_all()
        assert 'nova_feature' in all_flags
        assert all_flags['nova_feature']['description'] == 'Nova funcionalidade'
        assert all_flags['nova_feature']['category'] == 'test'
    
    def test_get_all_flags(self, tmp_path):
        """Testa obtenção de todas as flags."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        all_flags = flags.get_all()
        
        assert isinstance(all_flags, dict)
        assert len(all_flags) > 0
        
        for name, config in all_flags.items():
            assert 'enabled' in config
            assert isinstance(config['enabled'], bool)
    
    def test_get_enabled_flags(self, tmp_path):
        """Testa obtenção de flags habilitadas."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        enabled = flags.get_enabled_flags()
        
        assert isinstance(enabled, list)
        assert 'cache_enabled' in enabled
        assert 'pydantic_validation' in enabled
        assert 'json_logs' not in enabled  # Padrão desabilitada
    
    def test_get_by_category(self, tmp_path):
        """Testa obtenção de flags por categoria."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        performance_flags = flags.get_by_category('performance')
        
        assert 'cache_enabled' in performance_flags
        assert performance_flags['cache_enabled']['category'] == 'performance'
    
    def test_persistence(self, tmp_path):
        """Testa persistência de flags."""
        config_file = tmp_path / "test_flags.json"
        
        # Criar e modificar flags
        flags1 = FeatureFlags(str(config_file))
        flags1.enable('modo_debug')
        flags1.disable('cache_enabled')
        
        # Criar nova instância
        flags2 = FeatureFlags(str(config_file))
        
        # Verificar se mudanças persistiram
        assert flags2.is_enabled('modo_debug') is True
        assert flags2.is_enabled('cache_enabled') is False
    
    def test_env_variable_override(self, tmp_path, monkeypatch):
        """Testa que variável de ambiente sobrescreve arquivo."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        # Flag desabilitada no arquivo
        flags.disable('modo_debug')
        assert flags.is_enabled('modo_debug') is False
        
        # Habilitar via variável de ambiente
        monkeypatch.setenv('FEATURE_MODO_DEBUG', '1')
        assert flags.is_enabled('modo_debug') is True
        
        # Testar diferentes valores
        monkeypatch.setenv('FEATURE_MODO_DEBUG', 'true')
        assert flags.is_enabled('modo_debug') is True
        
        monkeypatch.setenv('FEATURE_MODO_DEBUG', '0')
        assert flags.is_enabled('modo_debug') is False
    
    def test_callback_on_enable(self, tmp_path):
        """Testa callback ao habilitar flag."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        called = []
        
        def callback(enabled: bool):
            called.append(enabled)
        
        flags.register_callback('modo_debug', callback)
        flags.enable('modo_debug')
        
        assert len(called) == 1
        assert called[0] is True
    
    def test_callback_on_disable(self, tmp_path):
        """Testa callback ao desabilitar flag."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        # Habilitar primeiro
        flags.enable('cache_enabled')
        
        called = []
        
        def callback(enabled: bool):
            called.append(enabled)
        
        flags.register_callback('cache_enabled', callback)
        flags.disable('cache_enabled')
        
        assert len(called) == 1
        assert called[0] is False
    
    def test_multiple_callbacks(self, tmp_path):
        """Testa múltiplos callbacks para mesma flag."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        results = []
        
        def callback1(enabled: bool):
            results.append(('callback1', enabled))
        
        def callback2(enabled: bool):
            results.append(('callback2', enabled))
        
        flags.register_callback('modo_debug', callback1)
        flags.register_callback('modo_debug', callback2)
        flags.enable('modo_debug')
        
        assert len(results) == 2
        assert ('callback1', True) in results
        assert ('callback2', True) in results
    
    def test_reload_flags(self, tmp_path):
        """Testa recarga de flags do arquivo."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        flags.enable('modo_debug')
        assert flags.is_enabled('modo_debug') is True
        
        # Modificar arquivo manualmente
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data['flags']['modo_debug']['enabled'] = False
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        # Recarregar
        flags.reload()
        assert flags.is_enabled('modo_debug') is False
    
    def test_reset_to_defaults(self, tmp_path):
        """Testa reset para valores padrão."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        # Modificar flags
        flags.enable('modo_debug')
        flags.disable('cache_enabled')
        
        # Reset
        flags.reset_to_defaults()
        
        # Verificar valores padrão
        assert flags.is_enabled('modo_debug') is False
        assert flags.is_enabled('cache_enabled') is True


class TestGlobalFeatureFlags:
    """Testes para funções globais."""
    
    def test_get_feature_flags_singleton(self):
        """Testa que get_feature_flags retorna singleton."""
        flags1 = get_feature_flags()
        flags2 = get_feature_flags()
        
        assert flags1 is flags2
    
    def test_is_feature_enabled_shortcut(self):
        """Testa atalho is_feature_enabled."""
        # Deve usar instância global
        result = is_feature_enabled('cache_enabled')
        assert isinstance(result, bool)
    
    def test_is_feature_enabled_with_default(self):
        """Testa atalho com valor default."""
        result = is_feature_enabled('flag_inexistente', default=True)
        assert result is True


class TestFeatureFlagsIntegration:
    """Testes de integração do sistema de feature flags."""
    
    def test_json_file_format(self, tmp_path):
        """Testa formato do arquivo JSON."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        flags.enable('test_feature', description='Test', category='test')
        
        # Ler arquivo JSON diretamente
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'flags' in data
        assert 'last_updated' in data
        assert 'test_feature' in data['flags']
        assert data['flags']['test_feature']['enabled'] is True
    
    def test_category_filtering(self, tmp_path):
        """Testa filtragem por categoria."""
        config_file = tmp_path / "test_flags.json"
        flags = FeatureFlags(str(config_file))
        
        # Obter flags de diferentes categorias
        performance = flags.get_by_category('performance')
        ui = flags.get_by_category('ui')
        debug = flags.get_by_category('debug')
        
        assert len(performance) > 0
        assert len(ui) > 0
        assert len(debug) > 0
        
        # Verificar que não há overlap
        for flag_name in performance:
            assert flag_name not in ui
            assert flag_name not in debug
