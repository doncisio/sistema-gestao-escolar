-- ============================================================================
-- MIGRAÇÃO SIMPLIFICADA: Tabelas para Integração Avaliações + Notas
-- Data: 14/12/2025
-- Versão: Sem procedures (para execução via Python)
-- ============================================================================

-- ============================================================================
-- 1. TABELA: avaliacoes_alunos
-- ============================================================================
CREATE TABLE IF NOT EXISTS avaliacoes_alunos (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    
    avaliacao_id BIGINT UNSIGNED NOT NULL,
    aluno_id INT NOT NULL,
    turma_id INT NOT NULL,
    avaliacao_aplicada_id BIGINT UNSIGNED DEFAULT NULL,
    
    data_aplicacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_inicio DATETIME DEFAULT NULL,
    data_conclusao DATETIME DEFAULT NULL,
    tempo_gasto INT UNSIGNED DEFAULT NULL,
    
    nota_total DECIMAL(5,2) DEFAULT 0.00,
    pontuacao_obtida DECIMAL(5,2) DEFAULT 0.00,
    pontuacao_maxima DECIMAL(5,2) NOT NULL,
    percentual_acerto DECIMAL(5,2) DEFAULT 0.00,
    
    status ENUM('pendente', 'em_andamento', 'aguardando_correcao', 'corrigida', 'finalizada') 
           NOT NULL DEFAULT 'pendente',
    
    presente BOOLEAN DEFAULT TRUE,
    
    lancado_por INT DEFAULT NULL,
    corrigido_por INT DEFAULT NULL,
    lancado_em DATETIME DEFAULT NULL,
    corrigido_em DATETIME DEFAULT NULL,
    finalizado_em DATETIME DEFAULT NULL,
    
    observacoes TEXT DEFAULT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    INDEX idx_avl_aluno (aluno_id),
    INDEX idx_avl_avaliacao (avaliacao_id),
    INDEX idx_avl_turma (turma_id),
    INDEX idx_avl_status (status),
    INDEX idx_avl_aplicada (avaliacao_aplicada_id),
    INDEX idx_avl_data (data_aplicacao),
    INDEX idx_avl_finalizado (status, finalizado_em),
    
    CONSTRAINT fk_avl_aluno FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE,
    CONSTRAINT fk_avl_avaliacao FOREIGN KEY (avaliacao_id) REFERENCES avaliacoes(id) ON DELETE CASCADE,
    CONSTRAINT fk_avl_turma FOREIGN KEY (turma_id) REFERENCES turmas(id) ON DELETE RESTRICT,
    CONSTRAINT fk_avl_aplicada FOREIGN KEY (avaliacao_aplicada_id) REFERENCES avaliacoes_aplicadas(id) ON DELETE SET NULL,
    CONSTRAINT fk_avl_lancado_por FOREIGN KEY (lancado_por) REFERENCES funcionarios(id) ON DELETE SET NULL,
    CONSTRAINT fk_avl_corrigido_por FOREIGN KEY (corrigido_por) REFERENCES funcionarios(id) ON DELETE SET NULL,
    
    UNIQUE KEY uk_avl_aluno_avaliacao (avaliacao_id, aluno_id)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 2. TABELA: respostas_questoes
-- ============================================================================
CREATE TABLE IF NOT EXISTS respostas_questoes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    
    avaliacao_aluno_id BIGINT UNSIGNED NOT NULL,
    questao_id BIGINT UNSIGNED NOT NULL,
    
    alternativa_id BIGINT UNSIGNED DEFAULT NULL,
    alternativa_letra CHAR(1) DEFAULT NULL,
    
    resposta_texto TEXT DEFAULT NULL,
    resposta_imagem VARCHAR(500) DEFAULT NULL,
    
    pontuacao_obtida DECIMAL(5,2) DEFAULT 0.00,
    pontuacao_maxima DECIMAL(5,2) NOT NULL,
    percentual_acerto DECIMAL(5,2) DEFAULT 0.00,
    
    correta BOOLEAN DEFAULT NULL,
    status ENUM('nao_respondida', 'respondida', 'nao_corrigida', 'corrigida') 
           NOT NULL DEFAULT 'nao_respondida',
    
    corrigido_por INT DEFAULT NULL,
    corrigido_em DATETIME DEFAULT NULL,
    comentario_correcao TEXT DEFAULT NULL,
    
    tempo_resposta INT UNSIGNED DEFAULT NULL,
    tentativas INT UNSIGNED DEFAULT 1,
    marcada_revisao BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    INDEX idx_resp_avl_aluno (avaliacao_aluno_id),
    INDEX idx_resp_questao (questao_id),
    INDEX idx_resp_status (status),
    INDEX idx_resp_corrigido (corrigido_por),
    INDEX idx_resp_alternativa (alternativa_id),
    INDEX idx_resp_pendentes (status, corrigido_por, avaliacao_aluno_id),
    INDEX idx_resp_questao_correta (questao_id, correta),
    
    CONSTRAINT fk_resp_avl_aluno FOREIGN KEY (avaliacao_aluno_id) 
        REFERENCES avaliacoes_alunos(id) ON DELETE CASCADE,
    CONSTRAINT fk_resp_quest FOREIGN KEY (questao_id) 
        REFERENCES questoes(id) ON DELETE RESTRICT,
    CONSTRAINT fk_resp_alt FOREIGN KEY (alternativa_id) 
        REFERENCES questoes_alternativas(id) ON DELETE SET NULL,
    CONSTRAINT fk_resp_corr_por FOREIGN KEY (corrigido_por) 
        REFERENCES funcionarios(id) ON DELETE SET NULL,
    
    UNIQUE KEY uk_resp_avl_questao (avaliacao_aluno_id, questao_id)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 3. VIEW: vw_desempenho_alunos
-- ============================================================================
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


-- ============================================================================
-- 4. VIEW: vw_fila_correcao
-- ============================================================================
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
-- FIM DA MIGRAÇÃO
-- ============================================================================
SELECT '✅ Migração concluída com sucesso!' AS status;
