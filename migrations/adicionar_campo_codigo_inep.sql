-- Migration: Adicionar campo codigo_inep na tabela alunos
-- Data: 21/02/2026
-- Descrição: Adiciona campo para armazenar o código INEP (Identificação Única) dos alunos

-- Adicionar coluna codigo_inep
ALTER TABLE alunos 
ADD COLUMN codigo_inep VARCHAR(20) NULL AFTER cpf;

-- Criar índice para melhorar desempenho de consultas
CREATE INDEX idx_alunos_codigo_inep ON alunos(codigo_inep);

-- Comentário informativo
ALTER TABLE alunos 
MODIFY COLUMN codigo_inep VARCHAR(20) NULL COMMENT 'Código INEP - Identificação Única do aluno';
