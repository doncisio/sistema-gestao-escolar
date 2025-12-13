-- Tabela para armazenar textos/imagens base usados em avaliações
-- Um texto base pode ser um texto literário, científico, uma imagem, gráfico, etc.
-- Cada avaliação pode ter zero ou mais textos base vinculados

CREATE TABLE IF NOT EXISTS textos_base (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL COMMENT 'Título/identificação do material',
    tipo ENUM('texto', 'imagem') NOT NULL DEFAULT 'texto' COMMENT 'Tipo do material base',
    conteudo TEXT NULL COMMENT 'Conteúdo textual (quando tipo=texto)',
    caminho_imagem VARCHAR(500) NULL COMMENT 'Caminho relativo da imagem (quando tipo=imagem)',
    link_drive VARCHAR(500) NULL COMMENT 'Link do Google Drive (quando tipo=imagem)',
    drive_file_id VARCHAR(100) NULL COMMENT 'ID do arquivo no Google Drive',
    largura INT NULL COMMENT 'Largura da imagem em pixels',
    altura INT NULL COMMENT 'Altura da imagem em pixels',
    escola_id INT NOT NULL,
    autor_id INT NULL COMMENT 'Professor/coordenador que criou',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_escola (escola_id),
    INDEX idx_tipo (tipo),
    FOREIGN KEY (escola_id) REFERENCES escolas(id) ON DELETE CASCADE,
    FOREIGN KEY (autor_id) REFERENCES funcionarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Textos, imagens e materiais base para avaliações';

-- Tabela de relacionamento: avaliação <-> textos base
-- Uma avaliação pode ter múltiplos textos base ordenados
CREATE TABLE IF NOT EXISTS avaliacoes_textos_base (
    id INT AUTO_INCREMENT PRIMARY KEY,
    avaliacao_id INT NOT NULL,
    texto_base_id INT NOT NULL,
    ordem INT NOT NULL DEFAULT 1 COMMENT 'Ordem de exibição (1, 2, 3...)',
    layout ENUM('completo', 'lado_esquerdo', 'lado_direito', 'superior', 'inferior') 
        DEFAULT 'completo' 
        COMMENT 'Layout do texto no PDF quando múltiplos',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_avaliacao_texto (avaliacao_id, texto_base_id),
    INDEX idx_avaliacao (avaliacao_id),
    INDEX idx_ordem (avaliacao_id, ordem),
    FOREIGN KEY (avaliacao_id) REFERENCES avaliacoes(id) ON DELETE CASCADE,
    FOREIGN KEY (texto_base_id) REFERENCES textos_base(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Relacionamento entre avaliações e textos base';
