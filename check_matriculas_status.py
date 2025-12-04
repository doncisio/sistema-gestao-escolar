from db.connection import get_connection

with get_connection() as conn:
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM matriculas WHERE status = %s', ('Ativo',))
    ativo = cur.fetchone()[0]

    cur.execute('SELECT COUNT(*) FROM matriculas WHERE status = %s', ('Concluida',))
    concluida = cur.fetchone()[0]

    cur.execute('SELECT status, COUNT(*) FROM matriculas GROUP BY status')
    grouped = cur.fetchall()

    cur.execute("SELECT id, aluno_id, turma_id, ano_letivo_id, status FROM matriculas WHERE status='Concluida' ORDER BY id DESC LIMIT 10")
    sample = cur.fetchall()

    print('ATIVO:', ativo)
    print('CONCLUIDA:', concluida)
    print('GROUPED:', grouped)
    print('SAMPLE:', sample)
