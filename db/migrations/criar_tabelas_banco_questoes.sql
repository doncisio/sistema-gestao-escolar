-- ============================================================================
-- BANCO DE QUESTÕES BNCC - Sistema de Gestão Escolar
-- Script de criação das tabelas
-- Data: 29/11/2025
-- ============================================================================

-- ============================================================================
-- 1. TABELA: questoes
-- Armazena as questões do banco de questões
-- ============================================================================
CREATE TABLE IF NOT EXISTS questoes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    
    -- Vínculo com BNCC e currículo
    componente_curricular ENUM('Língua Portuguesa', 'Matemática', 'Ciências', 'Geografia', 
                                'História', 'Arte', 'Educação Física', 'Língua Inglesa',
                                'Ensino Religioso') NOT NULL,
    ano_escolar ENUM('1º ano', '2º ano', '3º ano', '4º ano', '5º ano', 
                     '6º ano', '7º ano', '8º ano', '9º ano') NOT NULL,
    habilidade_bncc_codigo VARCHAR(15) NOT NULL COMMENT 'Ex: EF07MA02',
    habilidade_bncc_secundaria VARCHAR(15) DEFAULT NULL COMMENT 'Habilidade secundária opcional',
    
    -- Metadados da questão
    tipo ENUM('multipla_escolha', 'dissertativa', 'verdadeiro_falso', 
              'associacao', 'completar', 'ordenacao') NOT NULL DEFAULT 'multipla_escolha',
    dificuldade ENUM('facil', 'media', 'dificil') NOT NULL DEFAULT 'media',
    tempo_estimado INT UNSIGNED DEFAULT 3 COMMENT 'Tempo em minutos para responder',
    
    -- Conteúdo da questão
    enunciado TEXT NOT NULL COMMENT 'Texto do enunciado (pode conter HTML básico)',
    comando TEXT DEFAULT NULL COMMENT 'Comando específico da questão, se diferente do enunciado',
    texto_apoio TEXT DEFAULT NULL COMMENT 'Texto de apoio, fragmento literário, etc.',
    fonte_texto VARCHAR(500) DEFAULT NULL COMMENT 'Fonte/referência do texto de apoio',
    
    -- Para questões de múltipla escolha
    gabarito_letra CHAR(1) DEFAULT NULL COMMENT 'A, B, C, D ou E',
    
    -- Para questões dissertativas
    gabarito_dissertativa TEXT DEFAULT NULL COMMENT 'Resposta esperada/critérios de correção',
    rubrica_correcao TEXT DEFAULT NULL COMMENT 'Rubrica para correção (JSON ou texto)',
    pontuacao_maxima DECIMAL(5,2) DEFAULT 10.00,
    
    -- Para V/F (JSON array de booleans)
    gabarito_vf JSON DEFAULT NULL,
    
    -- Contexto e tags
    contexto ENUM('cotidiano', 'escolar', 'cientifico', 'literario', 
                  'historico', 'artistico', 'interdisciplinar') DEFAULT 'escolar',
    tags JSON DEFAULT NULL COMMENT 'Array de tags para facilitar busca',
    
    -- Estatísticas de uso
    vezes_aplicada INT UNSIGNED DEFAULT 0,
    taxa_acerto_media DECIMAL(5,2) DEFAULT NULL COMMENT 'Percentual de acerto médio',
    
    -- Controle de qualidade
    status ENUM('rascunho', 'revisao', 'aprovada', 'arquivada') NOT NULL DEFAULT 'rascunho',
    revisada_por BIGINT UNSIGNED DEFAULT NULL,
    revisada_em DATETIME DEFAULT NULL,
    observacoes_revisao TEXT DEFAULT NULL,
    
    -- Visibilidade
    visibilidade ENUM('privada', 'escola', 'rede', 'publica') NOT NULL DEFAULT 'escola',
    escola_id INT UNSIGNED DEFAULT NULL COMMENT 'NULL = todas as escolas da rede',
    
    -- Autoria e controle
    autor_id BIGINT UNSIGNED NOT NULL COMMENT 'Funcionário que criou a questão',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    INDEX idx_questoes_bncc (habilidade_bncc_codigo),
    INDEX idx_questoes_componente_ano (componente_curricular, ano_escolar),
    INDEX idx_questoes_tipo (tipo),
    INDEX idx_questoes_dificuldade (dificuldade),
    INDEX idx_questoes_status (status),
    INDEX idx_questoes_autor (autor_id),
    INDEX idx_questoes_escola (escola_id),
    FULLTEXT INDEX idx_questoes_enunciado (enunciado, texto_apoio),
    
    CONSTRAINT fk_questoes_autor FOREIGN KEY (autor_id) REFERENCES funcionarios(id),
    CONSTRAINT fk_questoes_revisor FOREIGN KEY (revisada_por) REFERENCES funcionarios(id),
    CONSTRAINT fk_questoes_escola FOREIGN KEY (escola_id) REFERENCES escolas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 2. TABELA: questoes_alternativas
-- Armazena as alternativas de questões de múltipla escolha
-- ============================================================================
CREATE TABLE IF NOT EXISTS questoes_alternativas (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    questao_id BIGINT UNSIGNED NOT NULL,
    letra CHAR(1) NOT NULL COMMENT 'A, B, C, D ou E',
    texto TEXT NOT NULL COMMENT 'Texto da alternativa',
    correta BOOLEAN NOT NULL DEFAULT FALSE,
    feedback TEXT DEFAULT NULL COMMENT 'Feedback para o aluno se marcar esta alternativa',
    ordem INT UNSIGNED NOT NULL DEFAULT 0,
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_questao_letra (questao_id, letra),
    INDEX idx_alternativa_questao (questao_id),
    
    CONSTRAINT fk_alt_questao FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 3. TABELA: questoes_arquivos
-- Armazena imagens, vídeos e anexos de questões
-- ============================================================================
CREATE TABLE IF NOT EXISTS questoes_arquivos (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    questao_id BIGINT UNSIGNED NOT NULL,
    alternativa_id BIGINT UNSIGNED DEFAULT NULL COMMENT 'NULL = arquivo do enunciado',
    
    tipo_arquivo ENUM('imagem', 'video', 'audio', 'documento') NOT NULL DEFAULT 'imagem',
    nome_original VARCHAR(255) NOT NULL,
    nome_armazenado VARCHAR(255) NOT NULL COMMENT 'Nome único gerado pelo sistema',
    caminho VARCHAR(500) NOT NULL COMMENT 'Caminho relativo no storage',
    tamanho_bytes BIGINT UNSIGNED NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    
    -- Dimensões para imagens/vídeos
    largura INT UNSIGNED DEFAULT NULL,
    altura INT UNSIGNED DEFAULT NULL,
    
    alt_text VARCHAR(500) DEFAULT NULL COMMENT 'Texto alternativo / descrição da imagem',
    posicao INT UNSIGNED DEFAULT 1 COMMENT 'Ordem de exibição se múltiplos arquivos',
    
    uploaded_by BIGINT UNSIGNED NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    INDEX idx_arquivo_questao (questao_id),
    INDEX idx_arquivo_questao_completo (questao_id, alternativa_id, posicao),
    
    CONSTRAINT fk_arquivo_questao FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE,
    CONSTRAINT fk_arquivo_alternativa FOREIGN KEY (alternativa_id) REFERENCES questoes_alternativas(id) ON DELETE CASCADE,
    CONSTRAINT fk_arquivo_uploader FOREIGN KEY (uploaded_by) REFERENCES funcionarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 4. TABELA: avaliacoes
-- Provas/testes compostos por múltiplas questões
-- ============================================================================
CREATE TABLE IF NOT EXISTS avaliacoes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    
    -- Identificação
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT DEFAULT NULL,
    
    -- Vínculo curricular
    componente_curricular ENUM('Língua Portuguesa', 'Matemática', 'Ciências', 'Geografia', 
                                'História', 'Arte', 'Educação Física', 'Língua Inglesa',
                                'Ensino Religioso') NOT NULL,
    ano_escolar ENUM('1º ano', '2º ano', '3º ano', '4º ano', '5º ano', 
                     '6º ano', '7º ano', '8º ano', '9º ano') NOT NULL,
    bimestre ENUM('1º bimestre', '2º bimestre', '3º bimestre', '4º bimestre') DEFAULT NULL,
    
    -- Tipo de avaliação
    tipo ENUM('diagnostica', 'formativa', 'somativa', 'recuperacao', 'simulado', 'exercicio') 
         NOT NULL DEFAULT 'somativa',
    
    -- Configurações
    pontuacao_total DECIMAL(5,2) DEFAULT 10.00,
    tempo_limite INT UNSIGNED DEFAULT NULL COMMENT 'Tempo em minutos',
    
    -- Configurações de impressão
    instrucoes TEXT DEFAULT NULL COMMENT 'Instruções para os alunos',
    cabecalho_personalizado TEXT DEFAULT NULL,
    mostrar_gabarito_professor BOOLEAN DEFAULT TRUE,
    embaralhar_questoes BOOLEAN DEFAULT FALSE,
    embaralhar_alternativas BOOLEAN DEFAULT FALSE,
    num_versoes INT UNSIGNED DEFAULT 1 COMMENT 'Quantidade de versões embaralhadas',
    
    -- Status
    status ENUM('rascunho', 'pronta', 'aplicada', 'arquivada') NOT NULL DEFAULT 'rascunho',
    
    -- Vínculo com escola
    escola_id INT UNSIGNED NOT NULL,
    professor_id BIGINT UNSIGNED NOT NULL,
    
    -- Controle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    INDEX idx_aval_componente_ano (componente_curricular, ano_escolar),
    INDEX idx_aval_professor (professor_id),
    INDEX idx_aval_escola (escola_id),
    INDEX idx_aval_status (status),
    INDEX idx_aval_bimestre (bimestre),
    
    CONSTRAINT fk_aval_escola FOREIGN KEY (escola_id) REFERENCES escolas(id),
    CONSTRAINT fk_aval_professor FOREIGN KEY (professor_id) REFERENCES funcionarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 5. TABELA: avaliacoes_questoes
-- Relacionamento N:N entre avaliações e questões
-- ============================================================================
CREATE TABLE IF NOT EXISTS avaliacoes_questoes (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    avaliacao_id BIGINT UNSIGNED NOT NULL,
    questao_id BIGINT UNSIGNED NOT NULL,
    
    ordem INT UNSIGNED NOT NULL DEFAULT 0,
    pontuacao DECIMAL(5,2) DEFAULT NULL COMMENT 'Peso/pontuação desta questão na avaliação',
    obrigatoria BOOLEAN DEFAULT TRUE,
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_aval_questao (avaliacao_id, questao_id),
    INDEX idx_avq_avaliacao (avaliacao_id),
    INDEX idx_avq_questao (questao_id),
    
    CONSTRAINT fk_avq_avaliacao FOREIGN KEY (avaliacao_id) REFERENCES avaliacoes(id) ON DELETE CASCADE,
    CONSTRAINT fk_avq_questao FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 6. TABELA: avaliacoes_aplicadas
-- Registro de aplicação de avaliações para turmas
-- ============================================================================
CREATE TABLE IF NOT EXISTS avaliacoes_aplicadas (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    avaliacao_id BIGINT UNSIGNED NOT NULL,
    turma_id INT UNSIGNED NOT NULL,
    
    data_aplicacao DATE NOT NULL,
    data_limite_lancamento DATE DEFAULT NULL COMMENT 'Data limite para lançar notas',
    
    status ENUM('agendada', 'em_andamento', 'aguardando_lancamento', 'concluida', 'cancelada') 
           NOT NULL DEFAULT 'agendada',
    
    -- Estatísticas pós-aplicação
    total_alunos INT UNSIGNED DEFAULT 0,
    total_presentes INT UNSIGNED DEFAULT 0,
    media_turma DECIMAL(5,2) DEFAULT NULL,
    maior_nota DECIMAL(5,2) DEFAULT NULL,
    menor_nota DECIMAL(5,2) DEFAULT NULL,
    
    -- Observações
    observacoes TEXT DEFAULT NULL,
    
    aplicada_por BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_aval_turma_data (avaliacao_id, turma_id, data_aplicacao),
    INDEX idx_aval_apl_status (status),
    INDEX idx_aval_apl_turma (turma_id),
    INDEX idx_aval_apl_data (data_aplicacao),
    
    CONSTRAINT fk_aval_apl_avaliacao FOREIGN KEY (avaliacao_id) REFERENCES avaliacoes(id),
    CONSTRAINT fk_aval_apl_turma FOREIGN KEY (turma_id) REFERENCES turmas(id),
    CONSTRAINT fk_aval_apl_aplicador FOREIGN KEY (aplicada_por) REFERENCES funcionarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 7. TABELA: respostas_alunos
-- Respostas dos alunos às questões
-- ============================================================================
CREATE TABLE IF NOT EXISTS respostas_alunos (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    avaliacao_aplicada_id BIGINT UNSIGNED NOT NULL,
    aluno_id INT UNSIGNED NOT NULL,
    questao_id BIGINT UNSIGNED NOT NULL,
    
    -- Resposta do aluno
    resposta_letra CHAR(1) DEFAULT NULL COMMENT 'Para múltipla escolha',
    resposta_texto TEXT DEFAULT NULL COMMENT 'Para dissertativas',
    resposta_vf JSON DEFAULT NULL COMMENT 'Para V/F: array de booleans',
    
    -- Correção
    correta BOOLEAN DEFAULT NULL COMMENT 'NULL = não corrigida',
    pontuacao_obtida DECIMAL(5,2) DEFAULT NULL,
    
    -- Para correção de dissertativas
    feedback_professor TEXT DEFAULT NULL,
    corrigida_por BIGINT UNSIGNED DEFAULT NULL,
    corrigida_em DATETIME DEFAULT NULL,
    
    -- Controle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_resp_aluno_questao (avaliacao_aplicada_id, aluno_id, questao_id),
    INDEX idx_resp_aluno (aluno_id),
    INDEX idx_resp_questao (questao_id),
    INDEX idx_resp_aplicada (avaliacao_aplicada_id),
    
    CONSTRAINT fk_resp_aplicada FOREIGN KEY (avaliacao_aplicada_id) REFERENCES avaliacoes_aplicadas(id) ON DELETE CASCADE,
    CONSTRAINT fk_resp_aluno FOREIGN KEY (aluno_id) REFERENCES alunos(id),
    CONSTRAINT fk_resp_questao FOREIGN KEY (questao_id) REFERENCES questoes(id),
    CONSTRAINT fk_resp_corretor FOREIGN KEY (corrigida_por) REFERENCES funcionarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 8. TABELA: questoes_favoritas
-- Professores podem favoritar questões para acesso rápido
-- ============================================================================
CREATE TABLE IF NOT EXISTS questoes_favoritas (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    questao_id BIGINT UNSIGNED NOT NULL,
    professor_id BIGINT UNSIGNED NOT NULL,
    
    pasta VARCHAR(100) DEFAULT NULL COMMENT 'Organização por pastas/categorias',
    anotacoes TEXT DEFAULT NULL COMMENT 'Notas pessoais do professor',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_fav_questao_prof (questao_id, professor_id),
    INDEX idx_fav_professor (professor_id),
    INDEX idx_fav_pasta (professor_id, pasta),
    
    CONSTRAINT fk_fav_questao FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE,
    CONSTRAINT fk_fav_professor FOREIGN KEY (professor_id) REFERENCES funcionarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 9. TABELA: questoes_comentarios
-- Comentários e avaliações de questões por outros professores
-- ============================================================================
CREATE TABLE IF NOT EXISTS questoes_comentarios (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    questao_id BIGINT UNSIGNED NOT NULL,
    professor_id BIGINT UNSIGNED NOT NULL,
    
    avaliacao INT UNSIGNED DEFAULT NULL COMMENT '1 a 5 estrelas',
    comentario TEXT DEFAULT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_coment_questao_prof (questao_id, professor_id),
    INDEX idx_coment_questao (questao_id),
    INDEX idx_coment_avaliacao (questao_id, avaliacao),
    
    CONSTRAINT fk_coment_questao FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE,
    CONSTRAINT fk_coment_professor FOREIGN KEY (professor_id) REFERENCES funcionarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 10. TABELA: questoes_historico
-- Histórico de alterações nas questões (versionamento)
-- ============================================================================
CREATE TABLE IF NOT EXISTS questoes_historico (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    questao_id BIGINT UNSIGNED NOT NULL,
    
    campo_alterado VARCHAR(100) NOT NULL,
    valor_anterior TEXT DEFAULT NULL,
    valor_novo TEXT DEFAULT NULL,
    
    alterado_por BIGINT UNSIGNED NOT NULL,
    alterado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    motivo VARCHAR(500) DEFAULT NULL,
    
    PRIMARY KEY (id),
    INDEX idx_hist_questao (questao_id),
    INDEX idx_hist_data (alterado_em),
    
    CONSTRAINT fk_hist_questao FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE,
    CONSTRAINT fk_hist_usuario FOREIGN KEY (alterado_por) REFERENCES funcionarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 11. TABELA: estatisticas_questao_turma
-- Estatísticas de desempenho por questão e turma
-- ============================================================================
CREATE TABLE IF NOT EXISTS estatisticas_questao_turma (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    questao_id BIGINT UNSIGNED NOT NULL,
    turma_id INT UNSIGNED NOT NULL,
    avaliacao_aplicada_id BIGINT UNSIGNED NOT NULL,
    
    total_respostas INT UNSIGNED DEFAULT 0,
    total_acertos INT UNSIGNED DEFAULT 0,
    taxa_acerto DECIMAL(5,2) DEFAULT NULL,
    
    -- Distribuição de respostas (para múltipla escolha)
    dist_alternativa_a INT UNSIGNED DEFAULT 0,
    dist_alternativa_b INT UNSIGNED DEFAULT 0,
    dist_alternativa_c INT UNSIGNED DEFAULT 0,
    dist_alternativa_d INT UNSIGNED DEFAULT 0,
    dist_alternativa_e INT UNSIGNED DEFAULT 0,
    
    -- Para dissertativas
    media_pontuacao DECIMAL(5,2) DEFAULT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_estat_questao_turma (questao_id, turma_id, avaliacao_aplicada_id),
    INDEX idx_estat_questao (questao_id),
    INDEX idx_estat_turma (turma_id),
    
    CONSTRAINT fk_estat_questao FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE,
    CONSTRAINT fk_estat_turma FOREIGN KEY (turma_id) REFERENCES turmas(id),
    CONSTRAINT fk_estat_aplicada FOREIGN KEY (avaliacao_aplicada_id) REFERENCES avaliacoes_aplicadas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- 12. TABELA: desempenho_aluno_habilidade
-- Desempenho do aluno por habilidade BNCC (consolidado)
-- ============================================================================
CREATE TABLE IF NOT EXISTS desempenho_aluno_habilidade (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    aluno_id INT UNSIGNED NOT NULL,
    habilidade_bncc_codigo VARCHAR(15) NOT NULL,
    ano_letivo_id INT UNSIGNED NOT NULL,
    
    -- Estatísticas consolidadas
    total_questoes_respondidas INT UNSIGNED DEFAULT 0,
    total_acertos INT UNSIGNED DEFAULT 0,
    taxa_acerto DECIMAL(5,2) DEFAULT NULL,
    
    -- Evolução
    ultima_avaliacao_id BIGINT UNSIGNED DEFAULT NULL,
    ultima_avaliacao_em DATE DEFAULT NULL,
    
    -- Classificação
    nivel_dominio ENUM('inicial', 'basico', 'intermediario', 'avancado') DEFAULT 'inicial',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_desemp_aluno_hab_ano (aluno_id, habilidade_bncc_codigo, ano_letivo_id),
    INDEX idx_desemp_aluno (aluno_id),
    INDEX idx_desemp_habilidade (habilidade_bncc_codigo),
    INDEX idx_desemp_nivel (nivel_dominio),
    
    CONSTRAINT fk_desemp_aluno FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE,
    CONSTRAINT fk_desemp_ano FOREIGN KEY (ano_letivo_id) REFERENCES anosletivos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- VIEWS ÚTEIS
-- ============================================================================

-- View: Questões com estatísticas
CREATE OR REPLACE VIEW vw_questoes_estatisticas AS
SELECT 
    q.id,
    q.componente_curricular,
    q.ano_escolar,
    q.habilidade_bncc_codigo,
    q.tipo,
    q.dificuldade,
    q.status,
    q.vezes_aplicada,
    q.taxa_acerto_media,
    f.nome AS autor_nome,
    q.created_at,
    (SELECT AVG(avaliacao) FROM questoes_comentarios WHERE questao_id = q.id) AS media_avaliacao,
    (SELECT COUNT(*) FROM questoes_favoritas WHERE questao_id = q.id) AS total_favoritos
FROM questoes q
LEFT JOIN funcionarios f ON f.id = q.autor_id;


-- View: Desempenho consolidado por turma e habilidade
CREATE OR REPLACE VIEW vw_desempenho_turma_habilidade AS
SELECT 
    m.turma_id,
    t.nome AS turma_nome,
    dah.habilidade_bncc_codigo,
    dah.ano_letivo_id,
    COUNT(DISTINCT dah.aluno_id) AS total_alunos,
    AVG(dah.taxa_acerto) AS media_taxa_acerto,
    SUM(CASE WHEN dah.nivel_dominio = 'inicial' THEN 1 ELSE 0 END) AS alunos_inicial,
    SUM(CASE WHEN dah.nivel_dominio = 'basico' THEN 1 ELSE 0 END) AS alunos_basico,
    SUM(CASE WHEN dah.nivel_dominio = 'intermediario' THEN 1 ELSE 0 END) AS alunos_intermediario,
    SUM(CASE WHEN dah.nivel_dominio = 'avancado' THEN 1 ELSE 0 END) AS alunos_avancado
FROM desempenho_aluno_habilidade dah
INNER JOIN matriculas m ON m.aluno_id = dah.aluno_id AND m.status = 'Ativo'
INNER JOIN turmas t ON t.id = m.turma_id
GROUP BY m.turma_id, t.nome, dah.habilidade_bncc_codigo, dah.ano_letivo_id;


-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger: Atualizar estatísticas da questão após nova resposta
DELIMITER //

CREATE TRIGGER trg_atualizar_estatisticas_questao
AFTER INSERT ON respostas_alunos
FOR EACH ROW
BEGIN
    -- Atualizar vezes_aplicada e taxa_acerto_media na questão
    UPDATE questoes q
    SET 
        vezes_aplicada = (
            SELECT COUNT(*) FROM respostas_alunos WHERE questao_id = NEW.questao_id
        ),
        taxa_acerto_media = (
            SELECT AVG(CASE WHEN correta = TRUE THEN 100.0 ELSE 0.0 END)
            FROM respostas_alunos 
            WHERE questao_id = NEW.questao_id AND correta IS NOT NULL
        )
    WHERE q.id = NEW.questao_id;
END//

DELIMITER ;


-- Trigger: Registrar alterações no histórico de questões
DELIMITER //

CREATE TRIGGER trg_questoes_historico_update
AFTER UPDATE ON questoes
FOR EACH ROW
BEGIN
    -- Registrar mudança no enunciado
    IF OLD.enunciado != NEW.enunciado THEN
        INSERT INTO questoes_historico (questao_id, campo_alterado, valor_anterior, valor_novo, alterado_por)
        VALUES (NEW.id, 'enunciado', OLD.enunciado, NEW.enunciado, NEW.autor_id);
    END IF;
    
    -- Registrar mudança no gabarito
    IF OLD.gabarito_letra != NEW.gabarito_letra OR 
       (OLD.gabarito_letra IS NULL AND NEW.gabarito_letra IS NOT NULL) OR
       (OLD.gabarito_letra IS NOT NULL AND NEW.gabarito_letra IS NULL) THEN
        INSERT INTO questoes_historico (questao_id, campo_alterado, valor_anterior, valor_novo, alterado_por)
        VALUES (NEW.id, 'gabarito_letra', OLD.gabarito_letra, NEW.gabarito_letra, NEW.autor_id);
    END IF;
    
    -- Registrar mudança no status
    IF OLD.status != NEW.status THEN
        INSERT INTO questoes_historico (questao_id, campo_alterado, valor_anterior, valor_novo, alterado_por)
        VALUES (NEW.id, 'status', OLD.status, NEW.status, NEW.autor_id);
    END IF;
END//

DELIMITER ;


-- ============================================================================
-- DADOS INICIAIS / SEED
-- ============================================================================

-- Inserir algumas questões de exemplo (comentado - descomentar se desejar)
/*
INSERT INTO questoes (
    componente_curricular, ano_escolar, habilidade_bncc_codigo, tipo, dificuldade,
    enunciado, gabarito_letra, contexto, tags, status, visibilidade, escola_id, autor_id
) VALUES
(
    'Matemática', '7º ano', 'EF07MA02', 'multipla_escolha', 'media',
    'Em uma loja, um produto custa R$ 250,00. Durante uma promoção, o preço teve um desconto de 30%. Qual o valor final do produto?',
    'B', 'cotidiano', '["porcentagem", "desconto", "problema"]', 'aprovada', 'escola', 60, 1
);

INSERT INTO questoes_alternativas (questao_id, letra, texto, correta, ordem) VALUES
(1, 'A', 'R$ 75,00', FALSE, 1),
(1, 'B', 'R$ 175,00', TRUE, 2),
(1, 'C', 'R$ 220,00', FALSE, 3),
(1, 'D', 'R$ 280,00', FALSE, 4);
*/

-- ============================================================================
-- FIM DO SCRIPT
-- ============================================================================
