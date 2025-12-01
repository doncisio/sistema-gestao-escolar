USE `redeescola`;

-- Migration: Adicionar campos pedagógicos ausentes em bncc_habilidades
-- Data: 2025-11-27
-- Objetivo: Capturar todos os campos importantes do Excel BNCC

-- Adicionar colunas pedagógicas (sem AFTER para máxima compatibilidade)
ALTER TABLE bncc_habilidades ADD COLUMN unidade_tematica VARCHAR(255) DEFAULT NULL;
ALTER TABLE bncc_habilidades ADD COLUMN classificacao VARCHAR(10) DEFAULT NULL COMMENT 'AF, AC, EF';
ALTER TABLE bncc_habilidades ADD COLUMN objetivos_aprendizagem TEXT DEFAULT NULL;
ALTER TABLE bncc_habilidades ADD COLUMN competencias_relacionadas TEXT DEFAULT NULL;
ALTER TABLE bncc_habilidades ADD COLUMN habilidades_relacionadas TEXT DEFAULT NULL;
ALTER TABLE bncc_habilidades ADD COLUMN comentarios TEXT DEFAULT NULL;
ALTER TABLE bncc_habilidades ADD COLUMN campo_atuacao VARCHAR(100) DEFAULT NULL COMMENT 'Para LP';

-- Índices para busca eficiente
CREATE INDEX idx_bncc_classificacao ON bncc_habilidades(classificacao);
CREATE INDEX idx_bncc_unidade ON bncc_habilidades(unidade_tematica);

-- Comentário sobre a migração
-- Este script adiciona campos que já deveriam ter sido capturados na importação inicial
-- Após executar, será necessário re-importar os dados com o importador corrigido
