-- ===================================================================
-- Tabela para armazenar seleções do Programa Cuidar dos Olhos
-- ===================================================================
-- Esta tabela persiste as seleções de estudantes e profissionais
-- que assinaram os termos do Programa Cuidar dos Olhos
-- ===================================================================

CREATE TABLE IF NOT EXISTS cuidar_olhos_selecoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo ENUM('estudante', 'profissional') NOT NULL COMMENT 'Tipo de seleção: estudante (aluno+responsável) ou profissional',
    aluno_id INT NULL COMMENT 'ID do aluno (se tipo=estudante)',
    responsavel_id INT NULL COMMENT 'ID do responsável (se tipo=estudante)',
    funcionario_id INT NULL COMMENT 'ID do funcionário (se tipo=profissional)',
    categoria VARCHAR(50) NULL COMMENT 'Categoria: professor ou servidor',
    selecionado BOOLEAN DEFAULT TRUE COMMENT 'Se está selecionado no momento',
    ano_letivo INT NOT NULL COMMENT 'Ano letivo da seleção',
    data_selecao TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Data da seleção',
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Última atualização',
    
    -- Constraints
    INDEX idx_tipo_ano (tipo, ano_letivo),
    INDEX idx_aluno_resp (aluno_id, responsavel_id),
    INDEX idx_funcionario (funcionario_id),
    
    -- Garantir unicidade por tipo
    UNIQUE KEY uk_estudante (tipo, aluno_id, responsavel_id, ano_letivo),
    UNIQUE KEY uk_profissional (tipo, funcionario_id, ano_letivo),
    
    -- Foreign Keys
    FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE,
    FOREIGN KEY (responsavel_id) REFERENCES responsaveis(id) ON DELETE CASCADE,
    FOREIGN KEY (funcionario_id) REFERENCES Funcionarios(id) ON DELETE CASCADE
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Armazena seleções de participantes que assinaram termos do Programa Cuidar dos Olhos';
