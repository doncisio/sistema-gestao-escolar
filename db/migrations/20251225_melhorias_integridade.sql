-- Migracao: melhorias de integridade e indices (nao executar sem rodar precheck e limpeza)
-- Banco: redeescola (MySQL 8.0)
-- Ordem sugerida: rodar em staging ou container, validar, depois aplicar no ambiente alvo.

-- 0) Padronizar collation em tabelas criticas
ALTER TABLE logs_acesso CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE usuarios CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE sessoes_usuario CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE turmas CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE matriculas CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE notas CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- 1) Turmas: nome obrigatorio e combinacao unica por escola+ano+serie+turno+nome
ALTER TABLE turmas
  MODIFY nome VARCHAR(100) NOT NULL,
  ADD CONSTRAINT uk_turma_combinacao UNIQUE (escola_id, ano_letivo_id, serie_id, turno, nome);
CREATE INDEX idx_turmas_escola_ano_serie ON turmas (escola_id, ano_letivo_id, serie_id);

-- 2) Matriculas: campos chave obrigatorios e indices por turma/ano/status
ALTER TABLE matriculas
  MODIFY aluno_id INT NOT NULL,
  MODIFY turma_id INT NOT NULL,
  MODIFY ano_letivo_id INT NOT NULL,
  MODIFY data_matricula DATE NOT NULL;
CREATE INDEX idx_matriculas_turma_status ON matriculas (turma_id, status);
CREATE INDEX idx_matriculas_ano_status ON matriculas (ano_letivo_id, status);

-- 3) Notas: impedir duplicidade por aluno+disciplina+bimestre+ano
ALTER TABLE notas
  ADD CONSTRAINT uk_notas_completa UNIQUE (aluno_id, disciplina_id, bimestre, ano_letivo_id);

-- 4) Sessoes: indice para invalidacao rapida por usuario
CREATE INDEX idx_sessoes_usuario_ativa ON sessoes_usuario (usuario_id, ativa);

-- 5) Logs: preparar para rotacao/particionamento (opcional); exemplo de renome de tabela atual
-- RENAME TABLE logs_acesso TO logs_acesso_atual;
-- CREATE TABLE logs_acesso LIKE logs_acesso_atual; -- reabre tabela vazia para novos logs
-- Dados antigos ficam em logs_acesso_atual para arquivamento/consulta historica.
