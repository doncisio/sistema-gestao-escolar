from db.connection import get_connection, get_cursor
from utils.safe import converter_para_int_seguro

# Query A: obter_estatisticas_alunos (resumida)
query_total_ativos = """
SELECT 
    COUNT(DISTINCT CASE WHEN m.status = 'Ativo' THEN a.id END) as total_ativos,
    COUNT(DISTINCT CASE WHEN m.status IN ('Transferido','Transferida') THEN a.id END) as total_transferidos
FROM Alunos a
JOIN Matriculas m ON a.id = m.aluno_id
JOIN turmas t ON m.turma_id = t.id
WHERE m.ano_letivo_id = %s 
AND a.escola_id = %s
AND m.status IN ('Ativo', 'Transferido', 'Transferida')
"""

# Query B: transicao total_matriculas (count distinct m.id where status='Ativo')
query_total_matriculas = """
SELECT COUNT(DISTINCT m.id) as total
FROM Matriculas m
WHERE m.ano_letivo_id = %s
AND m.status = 'Ativo'
"""

# Determine current ano_letivo_id
with get_cursor() as cur:
    cur.execute("SELECT id FROM anosletivos WHERE ano_letivo = YEAR(CURDATE())")
    res = cur.fetchone()
    if not res:
        cur.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
        res = cur.fetchone()
    ano_id = res['id'] if res and 'id' in res else None

print(f"Ano_letivo_id detectado: {ano_id}")

escola_id = 60

with get_cursor() as cur:
    cur.execute(query_total_ativos, (ano_id, escola_id))
    r = cur.fetchone()
    print("Dashboard (obter_estatisticas_alunos):")
    print(r)

with get_cursor() as cur:
    cur.execute(query_total_matriculas, (ano_id,))
    r2 = cur.fetchone()
    print("Transição (total_matriculas):")
    print(r2)

# Additionally compare alunos_continuar logic vs distinct matriculas
# Query for alunos_continuar used by transicao (count distinct a.id where m.turma_id NOT IN turmas_9ano)
with get_cursor() as cur:
    # get turmas_9ano
    cur.execute("""
        SELECT t.id
        FROM turmas t
        JOIN serie s ON t.serie_id = s.id
        WHERE s.nome LIKE '9%'
        AND t.escola_id = %s
    """, (escola_id,))
    rows = cur.fetchall()
    turmas_9ano = [row['id'] for row in rows]

print("Turmas 9º ano:", turmas_9ano)

with get_cursor() as cur:
    if turmas_9ano:
        placeholders = ','.join(['%s']*len(turmas_9ano))
        q = f"""
            SELECT COUNT(DISTINCT a.id) as total
            FROM Alunos a
            JOIN Matriculas m ON a.id = m.aluno_id
            WHERE m.ano_letivo_id = %s
            AND m.status = 'Ativo'
            AND a.escola_id = %s
            AND m.turma_id NOT IN ({placeholders})
        """
        params = (ano_id, escola_id) + tuple(turmas_9ano)
    else:
        q = """
            SELECT COUNT(DISTINCT a.id) as total
            FROM Alunos a
            JOIN Matriculas m ON a.id = m.aluno_id
            WHERE m.ano_letivo_id = %s
            AND m.status = 'Ativo'
            AND a.escola_id = %s
        """
        params = (ano_id, escola_id)
    cur.execute(q, params)
    r3 = cur.fetchone()
    print("Alunos que continuarão (transicao logic):", r3)

print("--- FIM ---")
