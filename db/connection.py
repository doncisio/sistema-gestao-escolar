from contextlib import contextmanager
from typing import Generator, Optional

from conexao import conectar_bd
from config_logs import get_logger
from mysql.connector.errors import InternalError as MySQLInternalError

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

    # Proxy leve que força cursores buffered por padrão e delega demais operações
    class _ConnProxy:
        def __init__(self, _conn):
            self._conn = _conn

        def cursor(self, *args, **kwargs):
            # Se o chamador não especificou 'buffered', ativamos por padrão.
            if 'buffered' not in kwargs:
                kwargs['buffered'] = True
            # Preservar possibilidade de solicitar dictionary=True via kwargs
            return self._conn.cursor(*args, **kwargs)

        def __getattr__(self, name):
            return getattr(self._conn, name)

    proxy_conn = _ConnProxy(conn)

    try:
        # Entregar um proxy para que chamadas antigas a conn.cursor() recebam
        # cursores buffered por padrão sem necessidade de alterar todo o código.
        yield proxy_conn
    finally:
        # Tentativa padrão de fechar/retornar a conexão ao pool.
        try:
            conn.close()
            return
        except MySQLInternalError as e:
            # Erro quando há resultados não lidos em cursores (unread result).
            logger.warning("Unread result found ao fechar conexão: %s. Tentando limpeza segura.", e)

            # Tentar limpar/rollback no objeto subjacente de forma defensiva.
            try:
                # Se o objeto de pool expõe _cnx (conexão subjacente), usá-lo.
                sub = getattr(conn, '_cnx', None)
                if sub:
                    try:
                        sub.rollback()
                    except Exception:
                        logger.exception("Rollback falhou no objeto subjacente da conexão")
                else:
                    # Caso não exista _cnx, tentar rollback direto (pode falhar)
                    if hasattr(conn, 'rollback'):
                        try:
                            conn.rollback()
                        except Exception:
                            logger.exception("Rollback direto falhou na conexão")

            except Exception:
                logger.exception("Erro durante tentativa defensiva de rollback para conexão com resultado não lido")

            # Tentar fechar novamente de forma segura.
            try:
                if hasattr(conn, 'close'):
                    conn.close()
                else:
                    logger.warning("Conexão não possui método close() após erro de resultado não lido")
            except Exception:
                logger.exception("Erro ao fechar conexão após tentativa de limpeza")

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
        # Usar cursor 'buffered' para evitar erros de 'Unread result found'
        # quando o caller não consumir explicitamente todos os resultados.
        cursor = conn.cursor(dictionary=True, buffered=True)
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

