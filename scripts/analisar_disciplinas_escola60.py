"""
Analisa as disciplinas da escola_id=60 (EM Profª Nadir Nascimento Moraes).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import get_cursor

def analisar_disciplinas():
    with get_cursor() as cur:
        # 1. Estrutura da tabela
        print("=" * 80)
        print("ESTRUTURA DA TABELA DISCIPLINAS")
        print("=" * 80)
        cur.execute("DESCRIBE disciplinas")
        for row in cur.fetchall():
            print(f"{row['Field']:20} {row['Type']:20} {row['Null']:5} {row['Key']:5} {row['Default'] or ''}")
        
        # 2. Disciplinas da escola_id=60
        print("\n" + "=" * 80)
        print("DISCIPLINAS DA ESCOLA_ID=60 (EM Profª Nadir Nascimento Moraes)")
        print("=" * 80)
        cur.execute("""
            SELECT *
            FROM disciplinas
            WHERE escola_id = 60
            ORDER BY nome
        """)
        disciplinas = cur.fetchall()
        
        if disciplinas:
            print(f"\nTotal de disciplinas: {len(disciplinas)}\n")
            for d in disciplinas:
                print(f"ID: {d['id']:3} | Nome: {d['nome']:40} | Escola ID: {d['escola_id']}")
        else:
            print("Nenhuma disciplina encontrada para escola_id=60")
        
        # 3. Verificar se há outras escolas com disciplinas
        print("\n" + "=" * 80)
        print("ESCOLAS COM DISCIPLINAS CADASTRADAS")
        print("=" * 80)
        cur.execute("""
            SELECT e.id, e.nome, COUNT(d.id) as total_disciplinas
            FROM escolas e
            LEFT JOIN disciplinas d ON e.id = d.escola_id
            GROUP BY e.id, e.nome
            HAVING total_disciplinas > 0
            ORDER BY total_disciplinas DESC, e.nome
            LIMIT 10
        """)
        escolas_com_disc = cur.fetchall()
        
        print(f"\nTop 10 escolas com mais disciplinas:\n")
        for esc in escolas_com_disc:
            print(f"Escola ID: {esc['id']:3} | {esc['nome']:50} | Disciplinas: {esc['total_disciplinas']:3}")
        
        # 4. Mostrar nomes das disciplinas (distintos)
        print("\n" + "=" * 80)
        print("NOMES DAS DISCIPLINAS (escola_id=60)")
        print("=" * 80)
        if disciplinas:
            nomes = sorted(set(d['nome'] for d in disciplinas))
            for i, nome in enumerate(nomes, 1):
                print(f"{i:2}. {nome}")

if __name__ == "__main__":
    analisar_disciplinas()
