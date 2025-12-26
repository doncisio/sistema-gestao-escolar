-- Prechecks e queries de saneamento (nao executar em producao sem revisar)
-- Alvo: banco redeescola (MySQL 8.0)

-- 1) Turmas sem nome (NULL ou vazio)
SELECT id, escola_id, ano_letivo_id, serie_id, turno, nome
FROM turmas
WHERE nome IS NULL OR TRIM(nome) = '';

-- 2) Possiveis duplicadas de turma por combinacao (escola, ano, serie, turno, nome)
SELECT escola_id, ano_letivo_id, serie_id, turno, TRIM(nome) AS nome, COUNT(*) AS qtd
FROM turmas
GROUP BY escola_id, ano_letivo_id, serie_id, turno, TRIM(nome)
HAVING COUNT(*) > 1;

-- 3) Matriculas com campos chave NULL que impedem NOT NULL
SELECT id, aluno_id, turma_id, ano_letivo_id, data_matricula, status
FROM matriculas
WHERE aluno_id IS NULL OR turma_id IS NULL OR ano_letivo_id IS NULL OR data_matricula IS NULL;

-- 4) Duplicadas de notas por aluno+disciplina+bimestre+ano_letivo (impede unique)
SELECT aluno_id, disciplina_id, bimestre, ano_letivo_id, COUNT(*) AS qtd
FROM notas
GROUP BY aluno_id, disciplina_id, bimestre, ano_letivo_id
HAVING COUNT(*) > 1;

-- 5) Collation diferente do padrao sugerido (utf8mb4_0900_ai_ci)
SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_COLLATION
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND (TABLE_COLLATION <> 'utf8mb4_0900_ai_ci' OR TABLE_COLLATION IS NULL);

-- 6) Logs de acesso para avaliar necessidade de particionamento ou rotacao
SELECT COUNT(*) AS total_logs, MIN(created_at) AS primeiro, MAX(created_at) AS ultimo
FROM logs_acesso;

-- 7) Sessoes de usuario ativas expiradas (para limpeza automatica)
SELECT id, usuario_id, expira_em, ativa
FROM sessoes_usuario
WHERE ativa = 1 AND expira_em < NOW();
