-- SQL para otimização da consulta de folha de ponto
-- Execute este script se quiser melhorar a performance das consultas

-- Verificar se os índices já existem antes de criar
-- Índice para busca por escola_id (caso ainda não exista)
CREATE INDEX IF NOT EXISTS idx_funcionarios_escola 
ON Funcionarios(escola_id);

-- Índice para busca por nome (caso ainda não exista)
CREATE INDEX IF NOT EXISTS idx_funcionarios_nome 
ON Funcionarios(nome);

-- Índice composto para otimizar a query principal
CREATE INDEX IF NOT EXISTS idx_funcionarios_escola_nome 
ON Funcionarios(escola_id, nome);

-- Comentários sobre os índices
-- idx_funcionarios_escola: Melhora JOIN com tabela escolas
-- idx_funcionarios_nome: Melhora ordenação e busca por nome
-- idx_funcionarios_escola_nome: Otimiza a query completa de dados do funcionário
