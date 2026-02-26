-- Migration: Adicionar campos de RG na tabela funcionarios
-- Data: 2026-02-26
-- Descrição: Adiciona as colunas rg, orgao_expedidor e data_expedicao_rg à tabela funcionarios

USE redeescola;

-- Verificar se as colunas já existem antes de adicionar
SET @dbname = DATABASE();
SET @tablename = 'funcionarios';
SET @columnname = 'rg';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' VARCHAR(20) DEFAULT NULL AFTER cpf')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Adicionar coluna orgao_expedidor
SET @columnname = 'orgao_expedidor';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' VARCHAR(50) DEFAULT NULL AFTER rg')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Adicionar coluna data_expedicao_rg
SET @columnname = 'data_expedicao_rg';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = @columnname)
  ) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE ', @tablename, ' ADD COLUMN ', @columnname, ' DATE DEFAULT NULL AFTER orgao_expedidor')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Verificar resultado
SELECT 
    'Colunas RG adicionadas com sucesso!' AS status,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'funcionarios'
    AND COLUMN_NAME IN ('rg', 'orgao_expedidor', 'data_expedicao_rg')
ORDER BY ORDINAL_POSITION;
