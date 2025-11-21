from typing import Dict, Optional
from conexao import conectar_bd
from config_logs import get_logger

_logger = get_logger(__name__)

# Cache em nível de processo para evitar consultas repetidas a escolas
_escola_municipio_cache: Dict[str, Optional[str]] = {}


def get_escola_municipio(escola_nome):
    """Retorna o município da `escola_nome` consultando o cache primeiro.

    Se não encontrado em cache, faz uma consulta mínima ao banco e armazena
    o resultado (pode ser string vazia se não houver valor).
    """
    if not escola_nome:
        return ''

    if escola_nome in _escola_municipio_cache:
        return _escola_municipio_cache[escola_nome]

    try:
        conn = conectar_bd()
        if not conn:
            _logger.info("conexão indisponível para buscar municipio da escola")
            _escola_municipio_cache[escola_nome] = ''
            return ''
        cur = conn.cursor()
        cur.execute("SELECT municipio FROM escolas WHERE nome = %s LIMIT 1", (escola_nome,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        municipio = row[0] if row and row[0] else ''
        _escola_municipio_cache[escola_nome] = municipio
        return municipio
    except Exception:
        _logger.exception(f"Erro ao buscar municipio para escola: {escola_nome}")
        _escola_municipio_cache[escola_nome] = ''
        return ''
