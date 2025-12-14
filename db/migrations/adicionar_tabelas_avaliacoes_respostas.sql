-- ============================================================================
-- MIGRAÇÃO: Tabelas para Integração Avaliações + Notas
-- Data: 14/12/2025
-- Objetivo: Vincular banco de questões ao sistema de notas
-- ============================================================================

-- ============================================================================
-- 1. TABELA: avaliacoes_alunos
-- Registra aplicação de avaliação por aluno individual
-- ============================================================================
CREATE TABLE IF NOT EXISTS avaliacoes_alunos (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    
    -- Relacionamentos
    avaliacao_id BIGINT UNSIGNED NOT NULL,
    aluno_id INT NOT NULL,
    turma_id INT NOT NULL,
    avaliacao_aplicada_id BIGINT UNSIGNED DEFAULT NULL COMMENT 'Referência opcional à aplicação por turma',
    
    -- Dados da aplicação
    data_aplicacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_inicio DATETIME DEFAULT NULL COMMENT 'Quando o aluno iniciou',
    data_conclusao DATETIME DEFAULT NULL COMMENT 'Quando o aluno concluiu',
    tempo_gasto INT UNSIGNED DEFAULT NULL COMMENT 'Tempo em minutos',
    
    -- Resultado
    nota_total DECIMAL(5,2) DEFAULT 0.00,
    pontuacao_obtida DECIMAL(5,2) DEFAULT 0.00,
    pontuacao_maxima DECIMAL(5,2) NOT NULL,
    percentual_acerto DECIMAL(5,2) DEFAULT 0.00,
    
    -- Status
    status ENUM('pendente', 'em_andamento', 'aguardando_correcao', 'corrigida', 'finalizada') 
           NOT NULL DEFAULT 'pendente',
    
    presente BOOLEAN DEFAULT TRUE,
    
    -- Auditoria
    lancado_por INT DEFAULT NULL COMMENT 'ID do professor que lançou',
    corrigido_por INT DEFAULT NULL COMMENT 'ID do professor que corrigiu',
    lancado_em DATETIME DEFAULT NULL,
    corrigido_em DATETIME DEFAULT NULL,
    finalizado_em DATETIME DEFAULT NULL,
    
    observacoes TEXT DEFAULT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    
    -- Índices
    INDEX idx_avl_aluno (aluno_id),
    INDEX idx_avl_avaliacao (avaliacao_id),
    INDEX idx_avl_turma (turma_id),
    INDEX idx_avl_status (status),
    INDEX idx_avl_aplicada (avaliacao_aplicada_id),
    INDEX idx_avl_data (data_aplicacao),
    
    -- Chaves estrangeiras
    CONSTRAINT fk_avl_aluno FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE,
    CONSTRAINT fk_avl_avaliacao FOREIGN KEY (avaliacao_id) REFERENCES avaliacoes(id) ON DELETE CASCADE,
    CONSTRAINT fk_avl_turma FOREIGN KEY (turma_id) REFERENCES turmas(id) ON DELETE RESTRICT,
    CONSTRAINT fk_avl_aplicada FOREIGN KEY (avaliacao_aplicada_id) REFERENCES avaliacoes_aplicadas(id) ON DELETE SET NULL,
    CONSTRAINT fk_avl_lancado_por FOREIGN KEY (lancado_por) REFERENCES funcionarios(id) ON DELETE SET NULL,
    CONSTRAINT fk_avl_corrigido_por FOREIGN KEY (corrigido_por) REFERENCES funcionarios(id) ON DELETE SET NULL,
    
    -- Constraint de unicidade: um aluno não pode ter duas respostas para a mesma avaliação
    UNIQUE KEY uk_avl_aluno_avaliacao (avaliacao_id, aluno_id)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Registro de aplicação de avaliação por aluno';


-- ============================================================================
-- 2. TABELA: respostas_questoes
-- Armazena respostas individuais de cada aluno para cada questão
-- ============================================================================
CREATE TABLE IF NOT EXISTS respostas_questoes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    
    -- Relacionamentos
    avaliacao_aluno_id BIGINT UNSIGNED NOT NULL,
    questao_id BIGINT UNSIGNED NOT NULL,
    
    -- Resposta objetiva (múltipla escolha)
    alternativa_id BIGINT UNSIGNED DEFAULT NULL,
    alternativa_letra CHAR(1) DEFAULT NULL COMMENT 'A, B, C, D, E',
    
    -- Resposta dissertativa
    resposta_texto TEXT DEFAULT NULL,
    resposta_imagem VARCHAR(500) DEFAULT NULL COMMENT 'Caminho/URL da imagem da resposta',
    
    -- Pontuação
    pontuacao_obtida DECIMAL(5,2) DEFAULT 0.00,
    pontuacao_maxima DECIMAL(5,2) NOT NULL,
    percentual_acerto DECIMAL(5,2) DEFAULT 0.00,
    
    -- Correção
    correta BOOLEAN DEFAULT NULL COMMENT 'TRUE=correta, FALSE=incorreta, NULL=não corrigida',
    status ENUM('nao_respondida', 'respondida', 'nao_corrigida', 'corrigida') 
           NOT NULL DEFAULT 'nao_respondida',
    
    corrigido_por INT DEFAULT NULL,
    corrigido_em DATETIME DEFAULT NULL,
    comentario_correcao TEXT DEFAULT NULL COMMENT 'Feedback do professor',
    
    -- Metadados
    tempo_resposta INT UNSIGNED DEFAULT NULL COMMENT 'Tempo em segundos',
    tentativas INT UNSIGNED DEFAULT 1,
    marcada_revisao BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    
    -- Índices
    INDEX idx_resp_avl_aluno (avaliacao_aluno_id),
    INDEX idx_resp_questao (questao_id),
    INDEX idx_resp_status (status),
    INDEX idx_resp_corrigido (corrigido_por),
    INDEX idx_resp_alternativa (alternativa_id),
    
    -- Chaves estrangeiras
    CONSTRAINT fk_resp_avl_aluno FOREIGN KEY (avaliacao_aluno_id) 
        REFERENCES avaliacoes_alunos(id) ON DELETE CASCADE,
    CONSTRAINT fk_resp_questao FOREIGN KEY (questao_id) 
        REFERENCES questoes(id) ON DELETE RESTRICT,
    CONSTRAINT fk_resp_alternativa FOREIGN KEY (alternativa_id) 
        REFERENCES questoes_alternativas(id) ON DELETE SET NULL,
    CONSTRAINT fk_resp_corrigido_por FOREIGN KEY (corrigido_por) 
        REFERENCES funcionarios(id) ON DELETE SET NULL,
    
    -- Constraint de unicidade: uma resposta por questão por aluno
    UNIQUE KEY uk_resp_avl_questao (avaliacao_aluno_id, questao_id)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Respostas individuais dos alunos para cada questão';


-- ============================================================================
-- 3. ÍNDICES ADICIONAIS PARA PERFORMANCE
-- ============================================================================

-- Índice composto para buscar respostas não corrigidas por professor
CREATE INDEX idx_resp_pendentes ON respostas_questoes(status, corrigido_por, avaliacao_aluno_id);

-- Índice para relatórios de desempenho por questão
CREATE INDEX idx_resp_questao_correta ON respostas_questoes(questao_id, correta);

-- Índice para buscar avaliações finalizadas por período
CREATE INDEX idx_avl_finalizado ON avaliacoes_alunos(status, finalizado_em);


-- ============================================================================
-- 4. VIEWS AUXILIARES
-- ============================================================================

-- View para facilitar consulta de desempenho do aluno
CREATE OR REPLACE VIEW vw_desempenho_alunos AS
SELECT 
    aa.id AS avaliacao_aluno_id,
    aa.aluno_id,
    a.nome AS aluno_nome,
    aa.avaliacao_id,
    av.titulo AS avaliacao_titulo,
    av.componente_curricular,
    av.ano_escolar,
    av.bimestre,
    aa.turma_id,
    t.nome AS turma_nome,
    aa.data_aplicacao,
    aa.status,
    aa.presente,
    aa.nota_total,
    aa.pontuacao_obtida,
    aa.pontuacao_maxima,
    aa.percentual_acerto,
    aa.tempo_gasto,
    COUNT(rq.id) AS total_questoes,
    SUM(CASE WHEN rq.status = 'corrigida' THEN 1 ELSE 0 END) AS questoes_corrigidas,
    SUM(CASE WHEN rq.correta = TRUE THEN 1 ELSE 0 END) AS questoes_corretas,
    SUM(CASE WHEN rq.correta = FALSE THEN 1 ELSE 0 END) AS questoes_incorretas
FROM avaliacoes_alunos aa
INNER JOIN alunos a ON aa.aluno_id = a.id
INNER JOIN avaliacoes av ON aa.avaliacao_id = av.id
INNER JOIN turmas t ON aa.turma_id = t.id
LEFT JOIN respostas_questoes rq ON aa.id = rq.avaliacao_aluno_id
GROUP BY aa.id;


-- View para fila de correção
CREATE OR REPLACE VIEW vw_fila_correcao AS
SELECT 
    rq.id AS resposta_id,
    rq.avaliacao_aluno_id,
    aa.aluno_id,
    a.nome AS aluno_nome,
    aa.turma_id,
    t.nome AS turma_nome,
    av.id AS avaliacao_id,
    av.titulo AS avaliacao_titulo,
    av.componente_curricular,
    av.professor_id,
    rq.questao_id,
    q.enunciado AS questao_enunciado,
    q.tipo AS questao_tipo,
    rq.resposta_texto,
    rq.resposta_imagem,
    rq.pontuacao_maxima,
    rq.status,
    aa.data_aplicacao
FROM respostas_questoes rq
INNER JOIN avaliacoes_alunos aa ON rq.avaliacao_aluno_id = aa.id
INNER JOIN alunos a ON aa.aluno_id = a.id
INNER JOIN turmas t ON aa.turma_id = t.id
INNER JOIN avaliacoes av ON aa.avaliacao_id = av.id
INNER JOIN questoes q ON rq.questao_id = q.id
WHERE rq.status IN ('nao_corrigida', 'respondida')
ORDER BY aa.data_aplicacao ASC, a.nome ASC;


-- ============================================================================
-- 5. PROCEDURES AUXILIARES
-- ============================================================================

-- Procedure para calcular nota total de um aluno em uma avaliação
DELIMITER $$

CREATE PROCEDURE IF NOT EXISTS calcular_nota_avaliacao_aluno(
    IN p_avaliacao_aluno_id BIGINT UNSIGNED
)
BEGIN
    DECLARE v_pontuacao_obtida DECIMAL(5,2);
    DECLARE v_pontuacao_maxima DECIMAL(5,2);
    DECLARE v_nota_total DECIMAL(5,2);
    DECLARE v_percentual DECIMAL(5,2);
    DECLARE v_todas_corrigidas BOOLEAN;
    
    -- Somar pontuação obtida e máxima
    SELECT 
        COALESCE(SUM(pontuacao_obtida), 0),
        COALESCE(SUM(pontuacao_maxima), 0),
        MIN(CASE WHEN status != 'corrigida' THEN 0 ELSE 1 END) = 1
    INTO 
        v_pontuacao_obtida,
        v_pontuacao_maxima,
        v_todas_corrigidas
    FROM respostas_questoes
    WHERE avaliacao_aluno_id = p_avaliacao_aluno_id;
    
    -- Calcular percentual e nota (escala 0-10)
    IF v_pontuacao_maxima > 0 THEN
        SET v_percentual = (v_pontuacao_obtida / v_pontuacao_maxima) * 100;
        SET v_nota_total = (v_pontuacao_obtida / v_pontuacao_maxima) * 10;
    ELSE
        SET v_percentual = 0;
        SET v_nota_total = 0;
    END IF;
    
    -- Atualizar registro
    UPDATE avaliacoes_alunos
    SET 
        pontuacao_obtida = v_pontuacao_obtida,
        pontuacao_maxima = v_pontuacao_maxima,
        nota_total = v_nota_total,
        percentual_acerto = v_percentual,
        status = CASE 
            WHEN v_todas_corrigidas THEN 'corrigida'
            ELSE status
        END,
        corrigido_em = CASE 
            WHEN v_todas_corrigidas AND corrigido_em IS NULL THEN NOW()
            ELSE corrigido_em
        END
    WHERE id = p_avaliacao_aluno_id;
END$$

DELIMITER ;


-- ============================================================================
-- 6. TRIGGERS PARA ATUALIZAÇÃO AUTOMÁTICA
-- ============================================================================

-- Trigger: atualiza nota total quando resposta é corrigida
DELIMITER $$

CREATE TRIGGER IF NOT EXISTS trg_resposta_corrigida_atualiza_nota
AFTER UPDATE ON respostas_questoes
FOR EACH ROW
BEGIN
    IF NEW.status = 'corrigida' AND OLD.status != 'corrigida' THEN
        CALL calcular_nota_avaliacao_aluno(NEW.avaliacao_aluno_id);
    END IF;
END$$

DELIMITER ;


-- ============================================================================
-- 7. INSERÇÃO DE DADOS DE TESTE (OPCIONAL - COMENTADO)
-- ============================================================================

/*
-- Exemplo de inserção de avaliação de aluno
INSERT INTO avaliacoes_alunos (
    avaliacao_id, aluno_id, turma_id, data_aplicacao, 
    pontuacao_maxima, lancado_por
) VALUES (
    1, 100, 5, NOW(), 10.00, 1
);

-- Exemplo de inserção de resposta objetiva
INSERT INTO respostas_questoes (
    avaliacao_aluno_id, questao_id, alternativa_id, alternativa_letra,
    pontuacao_maxima, status
) VALUES (
    1, 10, 50, 'A', 1.00, 'respondida'
);

-- Exemplo de inserção de resposta dissertativa
INSERT INTO respostas_questoes (
    avaliacao_aluno_id, questao_id, resposta_texto,
    pontuacao_maxima, status
) VALUES (
    1, 11, 'Minha resposta dissertativa aqui...', 2.00, 'nao_corrigida'
);
*/


-- ============================================================================
-- FIM DA MIGRAÇÃO
-- ============================================================================

-- Mensagem de sucesso
SELECT '✅ Migração concluída com sucesso!' AS status,
       'Tabelas avaliacoes_alunos e respostas_questoes criadas' AS resultado;
