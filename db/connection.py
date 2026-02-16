"""
Módulo unificado de conexão com o banco de dados.

Responsabilidades:
- Pool de conexões MySQL (inicialização, obtenção, encerramento)
- Context managers: get_connection(), get_cursor()
- Configuração centralizada via settings ou .env

Este é o ponto único de entrada para acesso ao banco. O módulo
src.core.conexao re-exporta as funções daqui para compatibilidade.
"""

import os
import threading
from contextlib import contextmanager
from typing import Generator, Optional

import mysql.connector
from mysql.connector import Error, pooling
from mysql.connector.errors import InternalError as MySQLInternalError
from dotenv import load_dotenv

from src.core.config_logs import get_logger

# Importar configurações centralizadas
try:
    from src.core.config.settings import settings
except ImportError:
    settings = None

load_dotenv()

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Pool de conexões (singleton)
# ---------------------------------------------------------------------------
_connection_pool = None
_pool_lock = threading.Lock()


def _get_db_config() -> dict:
    """
    Retorna configuração de banco de dados a partir de settings ou .env.

    Returns:
        dict com host, user, password, database, pool_size
    """
    if settings:
        db = settings.database
        return {
            "host": db.host,
            "user": db.user,
            "password": db.password,
            "database": db.name,
            "pool_size": db.pool_size,
        }
    return {
        "host": os.getenv("DB_HOST", ""),
        "user": os.getenv("DB_USER", ""),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", ""),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
    }


def _validar_configuracao_db() -> tuple[bool, list[str]]:
    """
    Valida que todas as variáveis de ambiente necessárias estão configuradas.

    Returns:
        tuple[bool, list[str]]: (is_valid, error_messages)
    """
    cfg = _get_db_config()
    errors = []
    if not cfg["host"]:
        errors.append("DB_HOST não configurado")
    if not cfg["user"]:
        errors.append("DB_USER não configurado")
    if not cfg["password"]:
        errors.append("DB_PASSWORD não configurado")
    if not cfg["database"]:
        errors.append("DB_NAME não configurado")
    return len(errors) == 0, errors


def _testar_conexao_db(host: str, user: str, password: str, database: str) -> tuple[bool, str]:
    """
    Testa se é possível conectar ao banco de dados.

    Returns:
        tuple[bool, str]: (success, message)
    """
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            auth_plugin="mysql_native_password",
            connection_timeout=5,
        )
        if conn.is_connected():
            conn.close()
            return True, "Conexão testada com sucesso"
        return False, "Conexão não está ativa"
    except Error as e:
        return False, f"Erro ao testar conexão: {e}"


# ---------------------------------------------------------------------------
# Gerenciamento do Pool
# ---------------------------------------------------------------------------

def inicializar_pool():
    """
    Inicializa o pool de conexões MySQL com validação robusta.
    Deve ser chamado uma vez no início da aplicação.

    Returns:
        MySQLConnectionPool: Pool de conexões inicializado

    Raises:
        ValueError: Se a configuração do banco estiver inválida
    """
    global _connection_pool

    if _connection_pool is not None:
        return _connection_pool

    with _pool_lock:
        # Double-check locking
        if _connection_pool is not None:
            return _connection_pool

        # Validar configuração
        is_valid, errors = _validar_configuracao_db()
        if not is_valid:
            error_msg = "Configuração do banco de dados inválida:\n" + "\n".join(
                f"  - {err}" for err in errors
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        cfg = _get_db_config()

        # Testar conexão antes de criar o pool
        success, message = _testar_conexao_db(
            cfg["host"], cfg["user"], cfg["password"], cfg["database"]
        )
        if not success:
            logger.error(f"Teste de conexão falhou: {message}")
            raise ValueError(f"Não foi possível conectar ao banco: {message}")

        logger.info(f"✓ {message}")

        try:
            pool_name = "gestao_escolar_pool"
            _connection_pool = pooling.MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=cfg["pool_size"],
                pool_reset_session=True,
                host=cfg["host"],
                user=cfg["user"],
                password=cfg["password"],
                database=cfg["database"],
                auth_plugin="mysql_native_password",
            )
            logger.info(
                f"✓ Connection Pool inicializado: {pool_name} (size={cfg['pool_size']})"
            )
        except Error as e:
            logger.exception(f"Erro ao criar connection pool: {e}")
            _connection_pool = None
            raise

    return _connection_pool


def conectar_bd():
    """
    Obtém uma conexão do pool de conexões.
    Se o pool não estiver inicializado, inicializa automaticamente.

    Returns:
        MySQLConnection: Conexão do pool ou None em caso de erro
    """
    global _connection_pool

    try:
        if _connection_pool is None:
            inicializar_pool()

        if _connection_pool is not None:
            conn = _connection_pool.get_connection()
            if conn.is_connected():
                return conn
            logger.warning("Conexão do pool não está ativa, tentando reconectar...")
            conn.reconnect(attempts=3, delay=1)
            return conn if conn.is_connected() else None

        # Fallback: conexão direta
        logger.warning("Pool não disponível, usando conexão direta (fallback)")
        return _conectar_direto()

    except Error as e:
        logger.exception(f"Erro ao obter conexão do pool: {e}")
        return _conectar_direto()


def _conectar_direto():
    """
    Cria uma conexão direta ao banco (fallback quando pool falha).
    """
    try:
        cfg = _get_db_config()
        conn = mysql.connector.connect(
            host=cfg["host"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            auth_plugin="mysql_native_password",
        )
        if conn.is_connected():
            return conn
    except Error as e:
        logger.exception(f"Erro ao conectar diretamente ao banco de dados: {e}")
    return None


def fechar_pool():
    """
    Fecha o pool de conexões, liberando todos os recursos.
    Deve ser chamado ao encerrar a aplicação.
    """
    global _connection_pool

    if _connection_pool is None:
        return

    with _pool_lock:
        pool = _connection_pool
        _connection_pool = None

    # Drenar conexões do pool
    closed = 0
    try:
        while True:
            try:
                conn = pool.get_connection()
                conn.close()
                closed += 1
            except Exception:
                break
    except Exception:
        pass

    logger.debug(f"Connection Pool encerrado ({closed} conexões fechadas)")


def obter_info_pool() -> Optional[dict]:
    """
    Retorna informações sobre o estado atual do pool.

    Returns:
        dict com pool_name, pool_size, host, database, user — ou None
    """
    if _connection_pool is None:
        return None
    try:
        pool_config = _connection_pool._cnx_config
        return {
            "pool_name": _connection_pool.pool_name,
            "pool_size": _connection_pool._pool_size,
            "host": pool_config.get("host", "N/A"),
            "database": pool_config.get("database", "N/A"),
            "user": pool_config.get("user", "N/A"),
        }
    except Exception as e:
        logger.exception(f"Erro ao obter informações do pool: {e}")
        return None


# ---------------------------------------------------------------------------
# Context Managers
# ---------------------------------------------------------------------------

class _ConnProxy:
    """Proxy leve que força cursores buffered por padrão."""

    __slots__ = ("_conn",)

    def __init__(self, conn):
        self._conn = conn

    def cursor(self, *args, **kwargs):
        if "buffered" not in kwargs:
            kwargs["buffered"] = True
        return self._conn.cursor(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._conn, name)


@contextmanager
def get_connection():
    """
    Context manager que fornece uma conexão ao banco e garante o fechamento.

    Usage::

        with get_connection() as conn:
            cursor = conn.cursor()
            ...
    """
    conn = conectar_bd()
    if conn is None:
        logger.error("Não foi possível obter conexão com o banco de dados")
        raise RuntimeError("Não foi possível obter conexão com o banco de dados")

    proxy = _ConnProxy(conn)
    try:
        yield proxy
    finally:
        try:
            conn.close()
        except MySQLInternalError as e:
            logger.warning("Unread result ao fechar conexão: %s", e)
            # Tentar rollback defensivo
            try:
                sub = getattr(conn, "_cnx", None)
                if sub:
                    sub.rollback()
                elif hasattr(conn, "rollback"):
                    conn.rollback()
            except Exception:
                logger.debug("Rollback defensivo falhou", exc_info=True)
            # Fechar novamente
            try:
                conn.close()
            except Exception:
                logger.debug("Erro ao fechar conexão após cleanup", exc_info=True)
        except Exception:
            logger.exception("Erro ao fechar conexão com o banco de dados")


@contextmanager
def get_cursor(commit: bool = False):
    """
    Context manager que fornece um cursor ``dictionary=True`` e gerencia
    commit/rollback automaticamente.

    Args:
        commit: se True, executa ``conn.commit()`` ao final.

    Usage::

        with get_cursor(commit=True) as cur:
            cur.execute("INSERT ...")
    """
    with get_connection() as conn:
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

