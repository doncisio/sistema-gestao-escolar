"""
Remove disciplinas de uma escola específica.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import get_connection

escola_id = 208

with get_connection() as conn:
    cur = conn.cursor()
    
    # Verificar quantas existem
    cur.execute("SELECT COUNT(*) FROM disciplinas WHERE escola_id = %s", (escola_id,))
    total_antes = cur.fetchone()[0]
    
    print(f"Escola ID {escola_id}: {total_antes} disciplinas encontradas")
    
    # Remover
    cur.execute("DELETE FROM disciplinas WHERE escola_id = %s", (escola_id,))
    removidas = cur.rowcount
    
    conn.commit()
    
    print(f"Disciplinas removidas: {removidas}")
    
    # Verificar
    cur.execute("SELECT COUNT(*) FROM disciplinas WHERE escola_id = %s", (escola_id,))
    total_depois = cur.fetchone()[0]
    
    print(f"Disciplinas restantes: {total_depois}")
