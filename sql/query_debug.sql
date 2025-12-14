
        SELECT
            a.nome AS 'NOME DO ALUNO',
            a.sexo AS 'SEXO',
            a.data_nascimento AS 'NASCIMENTO',
            s.nome AS 'NOME_SERIE',
            t.id AS 'ID_TURMA',
            t.nome AS 'NOME_TURMA',
            t.turno AS 'TURNO',
            m.status AS 'STATUS',
            m.data_matricula AS 'DATA_MATRICULA',
            f.nome AS 'NOME_PROFESSOR',
    
            MAX(CASE WHEN d.nome = 'CIÊNCIAS' AND d.nivel_id = 2 AND n.bimestre = '3º BIMESTRE' THEN n.nota END) AS 'CIÊNCIAS',
        
            MAX(CASE WHEN d.nome = 'MATEMÁTICA' AND d.nivel_id = 2 AND n.bimestre = '3º BIMESTRE' THEN n.nota END) AS 'MATEMÁTICA',
        
            MAX(CASE WHEN d.nome = 'PORTUGUÊS' AND d.nivel_id = 2 AND n.bimestre = '3º BIMESTRE' THEN n.nota END) AS 'PORTUGUÊS',
        
            MAX(CASE WHEN d.nome = 'HISTÓRIA' AND d.nivel_id = 2 AND n.bimestre = '3º BIMESTRE' THEN n.nota END) AS 'HISTÓRIA',
        
            MAX(CASE WHEN d.nome = 'GEOGRAFIA' AND d.nivel_id = 2 AND n.bimestre = '3º BIMESTRE' THEN n.nota END) AS 'GEOGRAFIA'
        FROM
            Alunos a
        JOIN
            Matriculas m ON a.id = m.aluno_id
        JOIN
            Turmas t ON m.turma_id = t.id
        JOIN
            Serie s ON t.serie_id = s.id
        LEFT JOIN
            Notas n ON a.id = n.aluno_id AND n.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = 2025)
        LEFT JOIN
            Disciplinas d ON n.disciplina_id = d.id
        LEFT JOIN
            Funcionarios f ON f.turma = t.id AND f.cargo = 'Professor@'
        WHERE
            m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = 2025)
            AND a.escola_id = 60
            AND m.status IN ('Ativo')
            AND s.nome = '3º Ano'
        GROUP BY
            a.id, a.nome, s.nome, t.id, t.nome, t.turno, m.status, m.data_matricula, f.nome
        ORDER BY
            a.nome ASC;
    