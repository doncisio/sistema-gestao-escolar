from typing import Callable, ContextManager, Any, Optional, List
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class DbService:
    """Wrapper para injetar o provider de conexão e simplificar operações DB.

    Recebe uma callable que retorna um context manager de conexão (ex.: ``get_connection``).

    Uso::

        from db.connection import get_connection
        db = DbService(get_connection)

        row = db.fetchone("SELECT * FROM alunos WHERE id = %s", (1,))
        rows = db.fetchall("SELECT * FROM alunos ORDER BY nome")
        affected = db.execute("UPDATE alunos SET nome = %s WHERE id = %s", ("Novo", 1))

        with db.transaction() as conn:
            cur = conn.cursor(dictionary=True, buffered=True)
            cur.execute("INSERT INTO ...")
            cur.execute("UPDATE ...")
            # commit automático ao sair do bloco; rollback em exceção
    """

    def __init__(self, get_connection_callable: Callable[[], ContextManager[Any]]):
        self._get_connection = get_connection_callable

    def connection(self):
        """Retorna o context manager de conexão (use: ``with db.connection() as conn:``)."""
        return self._get_connection()

    # ------------------------------------------------------------------
    # Helpers de alto nível
    # ------------------------------------------------------------------

    def fetchone(self, query: str, params: Any = None) -> Optional[dict]:
        """Executa SELECT e retorna a primeira linha como dict, ou ``None``."""
        with self._get_connection() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            try:
                cursor.execute(query, params or ())
                return cursor.fetchone()
            finally:
                cursor.close()

    def fetchall(self, query: str, params: Any = None) -> List[dict]:
        """Executa SELECT e retorna todas as linhas como lista de dicts."""
        with self._get_connection() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)
            try:
                cursor.execute(query, params or ())
                return cursor.fetchall()
            finally:
                cursor.close()

    def execute(self, query: str, params: Any = None) -> int:
        """Executa INSERT/UPDATE/DELETE com auto-commit. Retorna ``rowcount``."""
        with self._get_connection() as conn:
            cursor = conn.cursor(buffered=True)
            try:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.rowcount
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()

    @contextmanager
    def transaction(self):
        """Context manager para transações explícitas.

        Commit automático ao sair sem exceção; rollback em caso de erro.

        Uso::

            with db.transaction() as conn:
                cur = conn.cursor(dictionary=True, buffered=True)
                cur.execute("INSERT ...")
                cur.execute("UPDATE ...")
        """
        with self._get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    logger.exception("Erro ao dar rollback na transação")
                raise
