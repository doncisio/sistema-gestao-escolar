"""Teste simples de query de turmas."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_connection

with get_connection() as conn:
    cursor = conn.cursor(dictionary=True)
    
    # Query simples
    query = """
        SELECT t.id, t.nome, t.turno
        FROM turmas t
        WHERE 1=1
        LIMIT 5
    """
    cursor.execute(query)
    result = cursor.fetchall()
    print(f"Total: {len(result)}")
    print(f"Resultado: {result}")
