from db.connection import get_cursor

escola_id = 60

with get_cursor() as cur:
    # identificar ano letivo atual
    cur.execute("SELECT id, ano_letivo FROM anosletivos WHERE ano_letivo = YEAR(CURDATE())")
    res = cur.fetchone()
    if not res:
        cur.execute("SELECT id, ano_letivo FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
        res = cur.fetchone()
    if not res:
        raise SystemExit('Nenhum ano letivo encontrado')
    ano_id = res['id']
    ano_val = res['ano_letivo']

    print('Ano detectado:', ano_val, 'id=', ano_id)

    # Dashboard stats
    cur.execute("""
        SELECT 
            COUNT(DISTINCT CASE WHEN m.status = 'Ativo' THEN a.id END) as total_ativos,
            COUNT(DISTINCT CASE WHEN m.status IN ('Transferido','Transferida') THEN a.id END) as total_transferidos
        FROM Alunos a
        JOIN Matriculas m ON a.id = m.aluno_id
        JOIN turmas t ON m.turma_id = t.id
        WHERE m.ano_letivo_id = %s 
        AND a.escola_id = %s
        AND m.status IN ('Ativo', 'Transferido', 'Transferida')
    """, (ano_id, escola_id))
    dash = cur.fetchone()
    print('Dashboard (total_ativos, total_transferidos):', dash)

    # turmas 9ano
    cur.execute("""
        SELECT t.id
        FROM turmas t
        JOIN series s ON t.serie_id = s.id
        WHERE s.nome LIKE '9%'
        AND t.escola_id = %s
    """, (escola_id,))
    rows = cur.fetchall()
    turmas_9ano = [r['id'] for r in rows]
    print('Turmas 9º ano:', turmas_9ano)

    # alunos que continuarão (not in 9º)
    if turmas_9ano:
        placeholders = ','.join(['%s'] * len(turmas_9ano))
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
    r = cur.fetchone()
    alunos_continuar = r['total'] if r else 0
    print('Alunos que continuarão (not 9º):', alunos_continuar)

    # Buscar alunos_normais (list) with ids and turma
    if turmas_9ano:
        q2 = f"""
            SELECT DISTINCT a.id as aluno_id, m.turma_id
            FROM Alunos a
            JOIN Matriculas m ON a.id = m.aluno_id
            WHERE m.ano_letivo_id = %s
            AND m.status = 'Ativo'
            AND a.escola_id = %s
            AND m.turma_id NOT IN ({placeholders})
        """
        params2 = (ano_id, escola_id) + tuple(turmas_9ano)
    else:
        q2 = """
            SELECT DISTINCT a.id as aluno_id, m.turma_id
            FROM Alunos a
            JOIN Matriculas m ON a.id = m.aluno_id
            WHERE m.ano_letivo_id = %s
            AND m.status = 'Ativo'
            AND a.escola_id = %s
        """
        params2 = (ano_id, escola_id)
    cur.execute(q2, params2)
    alunos_normais = cur.fetchall()
    print('Exemplo alunos_normais (5):', alunos_normais[:5])

    # alunos reprovados (todas turmas): média < 60 ou sem notas
    cur.execute("""
        SELECT DISTINCT a.id as aluno_id, m.turma_id,
            (
                COALESCE(AVG(CASE WHEN n.bimestre = '1º bimestre' THEN n.nota END), 0) +
                COALESCE(AVG(CASE WHEN n.bimestre = '2º bimestre' THEN n.nota END), 0) +
                COALESCE(AVG(CASE WHEN n.bimestre = '3º bimestre' THEN n.nota END), 0) +
                COALESCE(AVG(CASE WHEN n.bimestre = '4º bimestre' THEN n.nota END), 0)
            ) / 4 as media_final
        FROM Alunos a
        JOIN Matriculas m ON a.id = m.aluno_id
        LEFT JOIN notas n ON a.id = n.aluno_id AND n.ano_letivo_id = %s
        WHERE m.ano_letivo_id = %s
        AND m.status = 'Ativo'
        AND a.escola_id = %s
        GROUP BY a.id, m.turma_id
        HAVING media_final < 60 OR AVG(n.nota) IS NULL
    """, (ano_id, ano_id, escola_id))
    rows_reprov = cur.fetchall()
    print('Alunos reprovados (count rows):', len(rows_reprov))
    print('Exemplo reprovados (5):', rows_reprov[:5])

    # Excluir alunos com status Transferido/Cancelado/Evadido
    cur.execute("""
        SELECT DISTINCT a.id as aluno_id
        FROM Alunos a
        JOIN Matriculas m ON a.id = m.aluno_id
        WHERE m.ano_letivo_id = %s
        AND m.status IN ('Transferido', 'Transferida', 'Cancelado', 'Evadido')
        AND a.escola_id = %s
    """, (ano_id, escola_id))
    rows_excluir = cur.fetchall()
    excluir_ids = set([r['aluno_id'] for r in rows_excluir])
    print('Alunos a excluir (count):', len(excluir_ids))

    # Montar união - usar map por aluno_id para evitar duplicatas
    alunos_map = {}
    for a in alunos_normais:
        aid = int(a['aluno_id'])
        if aid not in excluir_ids:
            alunos_map[aid] = a
    for a in rows_reprov:
        aid = int(a['aluno_id'])
        if aid not in excluir_ids:
            alunos_map.setdefault(aid, a)

    total_rematricular = len(alunos_map)
    print('Total alunos a rematricular (união sem excluidos):', total_rematricular)

    # pegar amostra com nomes
    sample_ids = list(alunos_map.keys())[:20]
    sample = []
    if sample_ids:
        placeholders = ','.join(['%s']*len(sample_ids))
        qn = f"SELECT id, nome FROM Alunos WHERE id IN ({placeholders})"
        cur.execute(qn, tuple(sample_ids))
        sample = cur.fetchall()
    print('Amostra (até 20) de alunos a rematricular:', sample)

print('\n--- FIM do relatório detalhado ---')

