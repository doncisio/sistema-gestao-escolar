-- Tabela para professores do 1º ao 5º ano
CREATE TABLE corpo_docente_1_5 AS
SELECT 
    f.id,
    f.nome,
    f.matricula,
    f.data_admissao,
    f.cpf,
    f.cargo,
    f.funcao,
    f.turno,
    f.carga_horaria,
    f.vinculo,
    f.polivalente,
    GROUP_CONCAT(DISTINCT d.nome SEPARATOR ', ') as disciplinas
FROM 
    funcionarios f
LEFT JOIN 
    funcionario_disciplinas fd ON f.id = fd.funcionario_id
LEFT JOIN 
    disciplinas d ON fd.disciplina_id = d.id
LEFT JOIN 
    turmas t ON f.turma = t.id
LEFT JOIN 
    serie s ON t.serie_id = s.id
WHERE 
    f.escola_id = 60
    AND f.cargo = 'Professor@'
    AND (
        s.nome IN ('1º Ano', '2º Ano', '3º Ano', '4º Ano', '5º Ano')
        OR (f.polivalente = 'sim' AND s.nome IS NULL)
    )
GROUP BY 
    f.id;

-- Tabela para professores do 6º ao 9º ano
CREATE TABLE corpo_docente_6_9 AS
SELECT 
    f.id,
    f.nome,
    f.matricula,
    f.data_admissao,
    f.cpf,
    f.cargo,
    f.funcao,
    f.turno,
    f.carga_horaria,
    f.vinculo,
    f.polivalente,
    GROUP_CONCAT(DISTINCT d.nome SEPARATOR ', ') as disciplinas
FROM 
    funcionarios f
LEFT JOIN 
    funcionario_disciplinas fd ON f.id = fd.funcionario_id
LEFT JOIN 
    disciplinas d ON fd.disciplina_id = d.id
LEFT JOIN 
    turmas t ON f.turma = t.id
LEFT JOIN 
    serie s ON t.serie_id = s.id
WHERE 
    f.escola_id = 60
    AND f.cargo = 'Professor@'
    AND (
        s.nome IN ('6º Ano', '7º Ano', '8º Ano', '9º Ano')
        OR (f.polivalente = 'não' AND s.nome IS NULL)
    )
GROUP BY 
    f.id; 