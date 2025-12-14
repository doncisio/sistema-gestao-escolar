-- Criação da tabela para armazenar documentos emitidos
CREATE TABLE IF NOT EXISTS documentos_emitidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo_documento VARCHAR(50) NOT NULL,
    nome_arquivo VARCHAR(255) NOT NULL,
    data_de_upload DATETIME NOT NULL,
    finalidade VARCHAR(255),
    descricao TEXT,
    link_no_drive VARCHAR(255)
);