"""
Análise rápida das disciplinas e escolas.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import get_cursor

print("Iniciando análise...")

with get_cursor() as cur:
    # 1. Disciplinas da escola 60
    print("\n1. Disciplinas da escola_id=60:")
    cur.execute("""
        SELECT d.id, d.nome, d.nivel_id, d.carga_horaria
        FROM disciplinas d
        WHERE d.escola_id = 60
        ORDER BY d.id
    """)
    disc60 = cur.fetchall()
    print(f"   Total: {len(disc60)} disciplinas")
    
    # Agrupar por nivel_id
    por_nivel = {}
    for d in disc60:
        nivel = d['nivel_id'] or 0
        if nivel not in por_nivel:
            por_nivel[nivel] = []
        por_nivel[nivel].append(d)
    
    for nivel, disciplinas in sorted(por_nivel.items()):
        print(f"\n   Nível {nivel}:")
        for d in disciplinas:
            ch = f"{d['carga_horaria']}h" if d['carga_horaria'] else "N/A"
            print(f"      ID {d['id']:3} | {d['nome']:35} | CH: {ch}")
    
    # 2. Escolas novas sem disciplinas
    print("\n2. Escolas com id_geduc SEM disciplinas:")
    cur.execute("""
        SELECT e.id, e.nome
        FROM escolas e
        LEFT JOIN disciplinas d ON e.id = d.escola_id
        WHERE e.id_geduc IS NOT NULL
        GROUP BY e.id, e.nome
        HAVING COUNT(d.id) = 0
        ORDER BY e.id
    """)
    sem_disc = cur.fetchall()
    print(f"   Total: {len(sem_disc)} escolas")
    
    if sem_disc:
        print("\n   Primeiras 10:")
        for esc in sem_disc[:10]:
            print(f"      ID {esc['id']:3} | {esc['nome']}")

print("\nAnálise concluída!")
