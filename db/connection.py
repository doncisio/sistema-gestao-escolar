from contextlib import contextmanager
from typing import Generator, Optional

from conexao import conectar_bd
from config_logs import get_logger

logger = get_logger(__name__)


@contextmanager
def get_connection():
    """
    Context manager que fornece uma conexão ao banco e garante o fechamento.

    Usage:
        with get_connection() as conn:
            cursor = conn.cursor()
            ...
    """
    conn = conectar_bd()
    if conn is None:
        logger.error("Não foi possível obter conexão com o banco de dados")
        raise RuntimeError("Não foi possível obter conexão com o banco de dados")

    try:
        yield conn
    finally:
        try:
            # fechar/retornar conexão ao pool
            conn.close()
        except Exception:
            logger.exception("Erro ao fechar conexão com o banco de dados")


@contextmanager
def get_cursor(commit: bool = False):
    """
    Context manager que fornece um cursor (com `dictionary=True`) e gerencia
    commit/rollback automaticamente.

    Args:
        commit: se True, executa `conn.commit()` ao final se nada ocorreu.

    Usage:
        with get_cursor() as cur:
            cur.execute(...)
            rows = cur.fetchall()
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            yield cursor
            if commit:
                try:
                    conn.commit()
                except Exception:
                    logger.exception("Erro ao commitar transação")
                    raise
        except Exception:
            try:
                conn.rollback()
            except Exception:
                logger.exception("Erro ao dar rollback na transação")
            raise
        finally:
            try:
                cursor.close()
            except Exception:
                logger.exception("Erro ao fechar cursor")

