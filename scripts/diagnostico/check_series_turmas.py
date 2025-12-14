"""Script para verificar estrutura de séries e turmas"""
from db.connection import get_cursor

print("=== SÉRIES ===")
with get_cursor() as c:
    c.execute('SELECT * FROM series ORDER BY id')
    for r in c.fetchall(): 
        print(r)

print("\n=== TURMAS (escola 60) ===")
with get_cursor() as c:
    c.execute('''
        SELECT s.id as serie_id, s.nome as serie_nome, 
               t.id as turma_id, t.nome as turma_nome, t.turno
        FROM series s
        LEFT JOIN turmas t ON s.id = t.serie_id AND t.escola_id = 60
        ORDER BY s.id, t.nome
    ''')
    print('Serie_ID | Serie_Nome      | Turma_ID | Turma_Nome | Turno')
    print('-' * 65)
    for r in c.fetchall(): 
        serie_id = r['serie_id']
        serie_nome = str(r['serie_nome'] or '')[:15]
        turma_id = str(r['turma_id'] or 'N/A')
        turma_nome = str(r['turma_nome'] or '(vazio)')[:10]
        turno = str(r['turno'] or 'N/A')
        print(f"{serie_id:8} | {serie_nome:15} | {turma_id:8} | {turma_nome:10} | {turno}")
