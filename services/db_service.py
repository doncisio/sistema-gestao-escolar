from typing import Callable, ContextManager, Any
from contextlib import contextmanager


class DbService:
    """Pequeno wrapper para injetar o provider de conexão no código.

    Recebe uma callable que retorna um context manager. Tradicionalmente isso
    era `get_connection()` (que fornece uma conexão com método `cursor()`),
    mas pode também ser `get_cursor()` (que fornece diretamente um cursor).

    Este wrapper normaliza ambos os casos expondo um context manager cujo
    objeto retornado possui o método `cursor()` — compatível com o código
    legado que chama `with db_service.connection() as conn: cursor = conn.cursor()`.
    """
    def __init__(self, get_connection_callable: Callable[[], ContextManager[Any]]):
        self._get_connection = get_connection_callable

    def connection(self):
        """Retorna um context manager que sempre fornece um objeto com `.cursor()`.

        Se o context manager provido já retornar um objeto com `.cursor()` (uma
        connection), ele é repassado diretamente. Se o provider retornar um
        cursor (ex.: `get_cursor()`), construímos um wrapper leve que expõe
        `.cursor()` retornando o próprio cursor.
        """
        @contextmanager
        def _cm():
            with self._get_connection() as provided:
                # Caso comum: provider devolve uma connection com método cursor()
                if hasattr(provided, 'cursor'):
                    yield provided
                else:
                    # Provider devolveu um cursor; criar wrapper mínimo
                    class _ConnWrap:
                        def __init__(self, cur):
                            self._cur = cur

                        def cursor(self):
                            return self._cur

                        # For compatibility, expose close() if needed (delegar ao cursor)
                        def close(self):
                            try:
                                # cursor may be a context-managed object; try to close if available
                                if hasattr(self._cur, 'close'):
                                    self._cur.close()
                            except Exception:
                                pass

                    yield _ConnWrap(provided)

        return _cm()
