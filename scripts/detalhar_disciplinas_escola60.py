"""
Detalha as disciplinas da escola_id=60 com níveis e cargas horárias.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import get_cursor

def detalhar_disciplinas():
    with get_cursor() as cur:
        print("=" * 100)
        print("DISCIPLINAS DA ESCOLA_ID=60 COM DETALHES")
        print("=" * 100)
        
        cur.execute("""
            SELECT 
                d.id,
                d.nome,
                d.nivel_id,
                n.nome as nivel_nome,
                d.carga_horaria,
                d.escola_id
            FROM disciplinas d
            LEFT JOIN niveis n ON d.nivel_id = n.id
            WHERE d.escola_id = 60
            ORDER BY n.nome, d.nome
        """)
        disciplinas = cur.fetchall()
        
        print(f"\nTotal: {len(disciplinas)} disciplinas\n")
        
        nivel_atual = None
        for d in disciplinas:
            nivel = d['nivel_nome'] or f"Nível ID {d['nivel_id']}" if d['nivel_id'] else "Sem nível"
            
            if nivel != nivel_atual:
                print(f"\n--- {nivel} ---")
                nivel_atual = nivel
            
            ch = f"{d['carga_horaria']}h" if d['carga_horaria'] else "N/A"
            print(f"  ID {d['id']:3} | {d['nome']:35} | CH: {ch:5}")
        
        # Verificar quais escolas foram inseridas recentemente (as 48 novas)
        print("\n" + "=" * 100)
        print("ESCOLAS INSERIDAS RECENTEMENTE (últimas 48 com id_geduc)")
        print("=" * 100)
        
        cur.execute("""
            SELECT 
                id,
                nome,
                id_geduc,
                nome_geduc,
                telefone,
                cep
            FROM escolas
            WHERE id_geduc IS NOT NULL
            ORDER BY id DESC
            LIMIT 48
        """)
        novas_escolas = cur.fetchall()
        
        print(f"\nTotal: {len(novas_escolas)} escolas\n")
        for esc in novas_escolas[:10]:  # Mostrar apenas as primeiras 10
            print(f"ID {esc['id']:3} | {esc['nome'][:60]:60} | GEDUC: {esc['id_geduc']}")
        print(f"... e mais {len(novas_escolas) - 10} escolas")
        
        # Verificar quantas dessas novas escolas já têm disciplinas
        print("\n" + "=" * 100)
        print("ESCOLAS NOVAS COM/SEM DISCIPLINAS")
        print("=" * 100)
        
        cur.execute("""
            SELECT 
                e.id,
                e.nome,
                COUNT(d.id) as total_disciplinas
            FROM escolas e
            LEFT JOIN disciplinas d ON e.id = d.escola_id
            WHERE e.id_geduc IS NOT NULL
            GROUP BY e.id, e.nome
            ORDER BY e.id DESC
            LIMIT 48
        """)
        status_disc = cur.fetchall()
        
        com_disc = sum(1 for s in status_disc if s['total_disciplinas'] > 0)
        sem_disc = sum(1 for s in status_disc if s['total_disciplinas'] == 0)
        
        print(f"\nEscolas COM disciplinas: {com_disc}")
        print(f"Escolas SEM disciplinas: {sem_disc}\n")
        
        if sem_disc > 0:
            print("Escolas SEM disciplinas (primeiras 10):")
            count = 0
            for s in status_disc:
                if s['total_disciplinas'] == 0 and count < 10:
                    print(f"  ID {s['id']:3} | {s['nome'][:70]}")
                    count += 1

if __name__ == "__main__":
    detalhar_disciplinas()
