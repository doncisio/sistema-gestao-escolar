"""
Shim de compatibilidade — toda a lógica de conexão agora vive em db.connection.

Este módulo re-exporta as funções para que imports existentes continuem
funcionando sem alteração:

    from src.core.conexao import conectar_bd        # ✓ funciona
    from src.core.conexao import inicializar_pool    # ✓ funciona
    from db.connection import get_connection          # ✓ recomendado
"""

from db.connection import (  # noqa: F401
    inicializar_pool,
    conectar_bd,
    fechar_pool,
    obter_info_pool,
    get_connection,
    get_cursor,
    _validar_configuracao_db,
    _testar_conexao_db,
)
