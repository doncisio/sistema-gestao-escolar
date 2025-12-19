-- Migration: adicionar colunas de auditoria e padronizar collation (idempotente)
-- Data: 2025-12-18
-- Adiciona colunas created_at/updated_at/created_by/updated_by na tabela alunos
-- Cria índice em alunos.cpf (após limpeza de duplicatas)
-- Ajusta collation da tabela alunos para utf8mb4_0900_ai_ci

-- Adicionar colunas de auditoria somente se não existirem (MySQL 8+ suporta IF NOT EXISTS)
ALTER TABLE alunos
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  ADD COLUMN IF NOT EXISTS created_by INT NULL,
  ADD COLUMN IF NOT EXISTS updated_by INT NULL;

-- Criar índice em cpf de forma segura
DROP INDEX IF EXISTS idx_alunos_cpf ON alunos;
CREATE INDEX idx_alunos_cpf ON alunos (cpf(14));

-- Padronizar collation da tabela alunos (execute em janela de manutenção)
ALTER TABLE alunos CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- Recomendações (não executadas automaticamente):
-- 1) Validar duplicatas de CPF antes de criar índice (remover/mesclar registros duplicados)
-- 2) Estender migraton para outras tabelas críticas (turmas, matriculas, notas) conforme plano
