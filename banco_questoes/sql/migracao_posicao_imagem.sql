-- Migração para adicionar campo 'posicao' na tabela questoes_arquivos
-- Permite definir onde a imagem será exibida em relação ao texto da questão
-- Data: 2025-11-29

-- Verificar se a coluna já existe antes de adicionar
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'questoes_arquivos' 
    AND COLUMN_NAME = 'posicao'
);

-- Adicionar coluna posicao se não existir
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE questoes_arquivos ADD COLUMN posicao ENUM(''acima'', ''abaixo'', ''esquerda'', ''direita'') DEFAULT ''abaixo'' COMMENT ''Posição da imagem em relação ao texto'' AFTER altura',
    'SELECT ''Coluna posicao já existe'' as resultado'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verificar se a coluna 'ordem' já existe
SET @col_ordem_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'questoes_arquivos' 
    AND COLUMN_NAME = 'ordem'
);

-- Adicionar coluna ordem se não existir
SET @sql2 = IF(@col_ordem_exists = 0, 
    'ALTER TABLE questoes_arquivos ADD COLUMN ordem INT UNSIGNED DEFAULT 1 COMMENT ''Ordem quando há múltiplas imagens'' AFTER posicao',
    'SELECT ''Coluna ordem já existe'' as resultado'
);
PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

-- Adicionar coluna alt_text se não existir
SET @col_alt_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'questoes_arquivos' 
    AND COLUMN_NAME = 'alt_text'
);

SET @sql3 = IF(@col_alt_exists = 0, 
    'ALTER TABLE questoes_arquivos ADD COLUMN alt_text VARCHAR(500) DEFAULT NULL COMMENT ''Texto alternativo / descrição da imagem'' AFTER ordem',
    'SELECT ''Coluna alt_text já existe'' as resultado'
);
PREPARE stmt3 FROM @sql3;
EXECUTE stmt3;
DEALLOCATE PREPARE stmt3;

-- Atualizar índice (remover o antigo se existir e criar o novo)
DROP INDEX IF EXISTS idx_arquivo_questao_completo ON questoes_arquivos;
CREATE INDEX idx_arquivo_questao_completo ON questoes_arquivos(questao_id, alternativa_id, ordem);

SELECT 'Migração concluída com sucesso!' as resultado;
