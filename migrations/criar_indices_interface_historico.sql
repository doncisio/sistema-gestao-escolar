-- Índices para otimizar a interface de histórico escolar
-- Execute este script no banco de dados MySQL

-- Índice composto para historico_escolar (usado nas consultas de histórico do aluno)
-- Se já existir um idx_aluno_historico, este comando vai falhar silenciosamente
CREATE INDEX IF NOT EXISTS idx_aluno_historico ON historico_escolar(aluno_id, ano_letivo_id, serie_id, escola_id);

-- Índice para buscar disciplinas por escola e nível
CREATE INDEX IF NOT EXISTS idx_disciplinas_escola_nivel ON disciplinas(escola_id, nivel_id);

-- Índice para buscar alunos por nome (usado na pesquisa)
CREATE INDEX IF NOT EXISTS idx_alunos_nome ON alunos(nome);

-- Índice para observações de histórico
CREATE INDEX IF NOT EXISTS idx_observacoes_historico ON observacoes_historico(serie_id, ano_letivo_id, escola_id);

-- Índice para carga horária total
CREATE INDEX IF NOT EXISTS idx_carga_horaria_total ON carga_horaria_total(serie_id, ano_letivo_id, escola_id);

-- Verificar estatísticas das tabelas (opcional, para MySQL 5.7+)
-- ANALYZE TABLE historico_escolar, disciplinas, alunos, observacoes_historico, carga_horaria_total;
