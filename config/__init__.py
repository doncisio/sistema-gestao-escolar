# Config module initialization
# Re-export functions from root config.py for backward compatibility

import sys
import os

# CRITICAL: Prevent circular imports by importing directly from config.py file
# We need to load config.py as a module without triggering 'import config' which would load this __init__.py

def _load_root_config():
    """Load config.py from root directory directly to avoid circular import."""
    import importlib.util
    from pathlib import Path
    
    # Path to root config.py
    config_path = Path(__file__).parent.parent / 'config.py'
    
    if not config_path.exists():
        return None
    
    # Load module from file path
    spec = importlib.util.spec_from_file_location("root_config", config_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    return None

# Load root config
_root_config = _load_root_config()

if _root_config:
    # Re-export all functions and constants
    perfis_habilitados = _root_config.perfis_habilitados
    get_flag = _root_config.get_flag
    get_icon_path = _root_config.get_icon_path
    get_image_path = _root_config.get_image_path
    get_ico_path = _root_config.get_ico_path
    get_resource_path = _root_config.get_resource_path
    carregar_feature_flags = _root_config.carregar_feature_flags
    recarregar_feature_flags = _root_config.recarregar_feature_flags
    banco_questoes_habilitado = _root_config.banco_questoes_habilitado
    dashboard_bncc_habilitado = _root_config.dashboard_bncc_habilitado
    cache_habilitado = _root_config.cache_habilitado
    modo_debug = _root_config.modo_debug
    coordenadores_series_map = _root_config.coordenadores_series_map
    coordenador_series_para_usuario = _root_config.coordenador_series_para_usuario
    
    # Re-export constants
    ESCOLA_ID = _root_config.ESCOLA_ID
    DEFAULT_DOCUMENTS_SECRETARIA_ROOT = _root_config.DEFAULT_DOCUMENTS_SECRETARIA_ROOT
    GEDUC_DEFAULT_USER = _root_config.GEDUC_DEFAULT_USER
    GEDUC_DEFAULT_PASS = _root_config.GEDUC_DEFAULT_PASS
    PROJECT_ROOT = _root_config.PROJECT_ROOT
    IMAGENS_DIR = _root_config.IMAGENS_DIR
    ICON_DIR = _root_config.ICON_DIR
    ICO_DIR = _root_config.ICO_DIR
    
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
        'ESCOLA_ID',
        'DEFAULT_DOCUMENTS_SECRETARIA_ROOT',
        'GEDUC_DEFAULT_USER',
        'GEDUC_DEFAULT_PASS',
        'PROJECT_ROOT',
        'IMAGENS_DIR',
        'ICON_DIR',
        'ICO_DIR',
    ]
else:
    # Fallback: define minimal functions
    from pathlib import Path
    
    PROJECT_ROOT = Path(__file__).parent.parent
    IMAGENS_DIR = PROJECT_ROOT / 'imagens'
    ICON_DIR = PROJECT_ROOT / 'icon'
    ICO_DIR = PROJECT_ROOT / 'ico'
    
    def perfis_habilitados():
        return False
    
    def get_flag(nome_flag, padrao=False):
        return padrao
    
    def get_icon_path(icon_name):
        if not icon_name.endswith('.png'):
            icon_name += '.png'
        return ICON_DIR / icon_name
    
    def get_image_path(image_name):
        return IMAGENS_DIR / image_name
    
    def get_ico_path(ico_name):
        if not ico_name.endswith('.ico'):
            ico_name += '.ico'
        return ICO_DIR / ico_name
    
    def get_resource_path(relative_path):
        return PROJECT_ROOT / relative_path
    
    def carregar_feature_flags():
        return {}
    
    def recarregar_feature_flags():
        return {}
    
    def banco_questoes_habilitado():
        return True
    
    def dashboard_bncc_habilitado():
        return False
    
    def cache_habilitado():
        return True
    
    def modo_debug():
        return False
    
    def coordenadores_series_map():
        return {}
    
    def coordenador_series_para_usuario(username):
        return None
    
    ESCOLA_ID = 60
    DEFAULT_DOCUMENTS_SECRETARIA_ROOT = r"G:\Meu Drive\Sistema Escolar - Documentos"
    GEDUC_DEFAULT_USER = ""
    GEDUC_DEFAULT_PASS = ""
    
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
        'ESCOLA_ID',
        'DEFAULT_DOCUMENTS_SECRETARIA_ROOT',
        'GEDUC_DEFAULT_USER',
        'GEDUC_DEFAULT_PASS',
        'PROJECT_ROOT',
        'IMAGENS_DIR',
        'ICON_DIR',
        'ICO_DIR',
    ]

