-- ============================================================================
-- MIGRAÇÃO: Adicionar campo link_no_drive na tabela questoes_arquivos
-- Data: 29/11/2025
-- Descrição: Permite armazenar o link do Google Drive para imagens de questões
-- ============================================================================

-- Adicionar coluna link_no_drive se não existir
SET @column_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'questoes_arquivos' 
    AND COLUMN_NAME = 'link_no_drive'
);

SET @sql = IF(@column_exists = 0, 
    'ALTER TABLE questoes_arquivos ADD COLUMN link_no_drive VARCHAR(500) DEFAULT NULL COMMENT ''Link do arquivo no Google Drive'' AFTER caminho',
    'SELECT ''Coluna link_no_drive já existe'''
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Adicionar coluna drive_file_id para referência direta ao arquivo no Drive
SET @column_exists2 = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'questoes_arquivos' 
    AND COLUMN_NAME = 'drive_file_id'
);

SET @sql2 = IF(@column_exists2 = 0, 
    'ALTER TABLE questoes_arquivos ADD COLUMN drive_file_id VARCHAR(100) DEFAULT NULL COMMENT ''ID do arquivo no Google Drive'' AFTER link_no_drive',
    'SELECT ''Coluna drive_file_id já existe'''
);

PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- Criar índice para busca pelo drive_file_id
-- CREATE INDEX IF NOT EXISTS não é suportado em MySQL, então verificamos primeiro
SET @index_exists = (
    SELECT COUNT(1) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'questoes_arquivos' 
    AND INDEX_NAME = 'idx_drive_file_id'
);

SET @sql3 = IF(@index_exists = 0, 
    'CREATE INDEX idx_drive_file_id ON questoes_arquivos(drive_file_id)',
    'SELECT ''Índice idx_drive_file_id já existe'''
);

PREPARE stmt3 FROM @sql3;
EXECUTE stmt3;
DEALLOCATE PREPARE stmt3;
