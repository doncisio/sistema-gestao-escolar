# Arquivo de configuração do sistema
# Mantenha valores sensíveis vazios em repositórios públicos.

import json
from pathlib import Path
from typing import Optional

# Nota: evitar dependências desnecessárias (ex: sympy). Usar booleanos Python nativos.
# ID padrão da escola usado em consultas (substitua conforme necessário em produção)
ESCOLA_ID = 60

# Configurações para integração GEDUC (por segurança manter vazias aqui em repositórios públicos)
# Você pode preencher localmente ou usar variáveis de ambiente para ambientes de produção.
GEDUC_DEFAULT_USER = ""
GEDUC_DEFAULT_PASS = ""

# Outros valores globais podem ser adicionados aqui no futuro.

# Caminho default para os Documentos da Secretaria (pode ser sobrescrito pela
# variável de ambiente `DOCUMENTS_SECRETARIA_ROOT`).
# Ajuste este valor localmente quando for necessário apontar para a pasta do
# Google Drive em outros computadores.
DEFAULT_DOCUMENTS_SECRETARIA_ROOT = r"G:\Meu Drive\Sistema Escolar - Documentos"


# ============================================================================
# SISTEMA DE FEATURE FLAGS
# ============================================================================

# Cache das flags para não reler o arquivo a cada chamada
_feature_flags_cache: Optional[dict] = None


def carregar_feature_flags() -> Optional[dict]:
    """
    Carrega as feature flags do arquivo JSON.
    Usa cache para evitar leituras repetidas do arquivo.
    
    Returns:
        dict: Dicionário com todas as flags e seus valores
    """
    global _feature_flags_cache
    
    if _feature_flags_cache is not None:
        return _feature_flags_cache
    
    arquivo = Path(__file__).parent / 'feature_flags.json'
    
    try:
        if arquivo.exists():
            with open(arquivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _feature_flags_cache = data.get('flags', {})
                return _feature_flags_cache
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠ Erro ao carregar feature_flags.json: {e}")
    
    # Retorna valores padrão se arquivo não existir ou houver erro
    _feature_flags_cache = {}
    return _feature_flags_cache


def get_flag(nome_flag: str, padrao: bool = False) -> bool:
    """
    Obtém o valor de uma feature flag específica.
    
    Args:
        nome_flag: Nome da flag (ex: 'perfis_habilitados')
        padrao: Valor padrão se a flag não existir
        
    Returns:
        bool: True se a flag está habilitada, False caso contrário
    """
    flags = carregar_feature_flags() or {}
    flag_config = flags.get(nome_flag, {})
    
    if isinstance(flag_config, dict):
        return flag_config.get('enabled', padrao)
    elif isinstance(flag_config, bool):
        return flag_config
    
    return padrao


def recarregar_feature_flags() -> Optional[dict]:
    """
    Força a recarga das feature flags do arquivo.
    Útil quando o arquivo foi modificado externamente.
    
    Returns:
        dict: Dicionário atualizado com todas as flags
    """
    global _feature_flags_cache
    _feature_flags_cache = None
    return carregar_feature_flags()


# ============================================================================
# FUNÇÕES DE ACESSO RÁPIDO PARA FEATURE FLAGS ESPECÍFICAS
# ============================================================================

def perfis_habilitados() -> bool:
    """
    Verifica se o sistema de perfis de usuário está habilitado.
    Quando True: Sistema exige login e aplica controle de acesso.
    Quando False: Sistema abre direto sem autenticação (comportamento atual).
    
    Returns:
        bool: True se perfis estão habilitados
    """
    return get_flag('perfis_habilitados', False)


def banco_questoes_habilitado() -> bool:
    """
    Verifica se o módulo de banco de questões BNCC está habilitado.
    
    Returns:
        bool: True se o módulo está habilitado
    """
    return get_flag('banco_questoes_habilitado', True)


def dashboard_bncc_habilitado() -> bool:
    """
    Verifica se o dashboard pedagógico BNCC está habilitado.
    
    Returns:
        bool: True se o dashboard está habilitado
    """
    return get_flag('dashboard_bncc_habilitado', False)


def cache_habilitado() -> bool:
    """
    Verifica se o cache de estatísticas está habilitado.
    
    Returns:
        bool: True se o cache está habilitado
    """
    return get_flag('cache_enabled', True)


def modo_debug() -> bool:
    """
    Verifica se o modo debug está habilitado.
    
    Returns:
        bool: True se o modo debug está habilitado
    """
    return get_flag('modo_debug', False)


def coordenadores_series_map() -> dict:
    """Retorna o mapeamento configurado em `feature_flags.json` para `coordenadores_series`.

    Retorna um dicionário username -> lista de nomes de série.
    """
    flags = carregar_feature_flags() or {}
    cfg = flags.get('coordenadores_series', {})
    if isinstance(cfg, dict):
        return cfg.get('mapping', {}) if 'mapping' in cfg else {}
    return {}


def coordenador_series_para_usuario(username: str):
    """Retorna a lista de séries permitidas para o `username` do coordenador, ou None se não houver restrição."""
    mapping = coordenadores_series_map()
    if not mapping:
        return None
    return mapping.get(username)
