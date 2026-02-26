from src.core.conexao import conectar_bd

conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

# Buscar JOAO PEDRO no 8º ano
cursor.execute('''
    SELECT a.id, a.nome, a.data_nascimento, s.nome as serie, m.status
    FROM Alunos a
    LEFT JOIN Matriculas m ON a.id = m.aluno_id
    LEFT JOIN Turmas t ON m.turma_id = t.id
    LEFT JOIN series s ON t.serie_id = s.id
    LEFT JOIN AnosLetivos al ON m.ano_letivo_id = al.id
    WHERE a.nome LIKE %s
    AND a.escola_id = 60
    AND al.ano_letivo = 2026
    AND s.nome LIKE %s
''', ('%JOAO PEDRO%', '%8%'))

results = cursor.fetchall()
print(f'Total de João Pedro no 8º ano: {len(results)}')
for r in results:
    print(f"{r['nome']} - Nasc: {r['data_nascimento']} - Status: {r['status']}")

# Buscar alunos do 8º ano nascidos em 2011 (15 anos)
print('\n\nTodos os alunos do 8º ano nascidos em 2011:')
cursor.execute('''
    SELECT a.id, a.nome, a.data_nascimento, m.status
    FROM Alunos a
    LEFT JOIN Matriculas m ON a.id = m.aluno_id
    LEFT JOIN Turmas t ON m.turma_id = t.id
    LEFT JOIN series s ON t.serie_id = s.id
    LEFT JOIN AnosLetivos al ON m.ano_letivo_id = al.id
    WHERE a.escola_id = 60
    AND al.ano_letivo = 2026
    AND s.nome LIKE %s
    AND YEAR(a.data_nascimento) = 2011
''', ('%8%',))

results = cursor.fetchall()
print(f'Total: {len(results)}')
for r in results:
    print(f"{r['nome']} - Nasc: {r['data_nascimento']} - Status: {r['status']}")

cursor.close()
conn.close()
