# Config module initialization
# Re-export all functions and constants from src.core.config.py

import sys
import os

# CRITICAL: Load config.py directly to avoid circular imports
# This __init__.py acts as a re-export layer for the main config.py file

def _load_config():
    """Load config.py from parent directory (src.core.config.py)."""
    import importlib.util
    from pathlib import Path
    
    # Path to src/core/config.py (two levels up from this __init__.py, then back to config.py)
    # __file__ = src/core/config/__init__.py
    # parent = src/core/config/
    # parent.parent = src/core/
    # parent.parent / 'config.py' = src/core/config.py
    config_path = Path(__file__).parent.parent / 'config.py'
    
    if not config_path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")
    
    # Load module from file path
    spec = importlib.util.spec_from_file_location("core_config", config_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    raise ImportError("Não foi possível carregar o módulo de configuração")

# Load config (will raise exception if fails)
_config = _load_config()

# Re-export all functions
perfis_habilitados = _config.perfis_habilitados
get_flag = _config.get_flag
get_icon_path = _config.get_icon_path
get_image_path = _config.get_image_path
get_ico_path = _config.get_ico_path
get_resource_path = _config.get_resource_path
carregar_feature_flags = _config.carregar_feature_flags
recarregar_feature_flags = _config.recarregar_feature_flags
banco_questoes_habilitado = _config.banco_questoes_habilitado
dashboard_bncc_habilitado = _config.dashboard_bncc_habilitado
cache_habilitado = _config.cache_habilitado
modo_debug = _config.modo_debug
coordenadores_series_map = _config.coordenadores_series_map
coordenador_series_para_usuario = _config.coordenador_series_para_usuario
get_ano_letivo_atual = _config.get_ano_letivo_atual

# Re-export all constants (these come directly from config.py)
ESCOLA_ID = _config.ESCOLA_ID
ANO_LETIVO_ATUAL = _config.ANO_LETIVO_ATUAL
DEFAULT_DOCUMENTS_SECRETARIA_ROOT = _config.DEFAULT_DOCUMENTS_SECRETARIA_ROOT
GEDUC_DEFAULT_USER = _config.GEDUC_DEFAULT_USER
GEDUC_DEFAULT_PASS = _config.GEDUC_DEFAULT_PASS
PROJECT_ROOT = _config.PROJECT_ROOT
IMAGENS_DIR = _config.IMAGENS_DIR
ICON_DIR = _config.ICON_DIR
ICO_DIR = _config.ICO_DIR

__all__ = [
    'perfis_habilitados',
    'get_flag',
    'get_icon_path',
    'get_image_path',
    'get_ico_path',
    'get_resource_path',
    'carregar_feature_flags',
    'recarregar_feature_flags',
    'banco_questoes_habilitado',
    'dashboard_bncc_habilitado',
    'cache_habilitado',
    'modo_debug',
    'coordenadores_series_map',
    'coordenador_series_para_usuario',
    'get_ano_letivo_atual',
    'ESCOLA_ID',
    'ANO_LETIVO_ATUAL',
    'DEFAULT_DOCUMENTS_SECRETARIA_ROOT',
    'GEDUC_DEFAULT_USER',
    'GEDUC_DEFAULT_PASS',
    'PROJECT_ROOT',
    'IMAGENS_DIR',
    'ICON_DIR',
    'ICO_DIR',
]

