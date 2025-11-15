from contextlib import contextmanager
from typing import Generator, Any

from conexao import conectar_bd

@contextmanager
def get_connection() -> Generator[Any, None, None]:
    """Context manager simples para obter e garantir fechamento de conexões.

    Uso:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
    """
    conn = None
    try:
        conn = conectar_bd()
        yield conn
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            # Não propagar erros de fechamento
            pass
