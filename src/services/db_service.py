from typing import Callable, ContextManager, Any


class DbService:
    """Pequeno wrapper para injetar o provider de conexão no código.

    Recebe uma callable que retorna um context manager de conexão (ex.: `get_connection`).
    """
    def __init__(self, get_connection_callable: Callable[[], ContextManager[Any]]):
        self._get_connection = get_connection_callable

    def connection(self):
        """Retorna o context manager de conexão (use: `with db_service.connection() as conn:`)."""
        return self._get_connection()
