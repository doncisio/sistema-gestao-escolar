-- ============================================================================
-- EXPORTAÇÃO DE DADOS - BANCO DE QUESTÕES
-- Gerado em: 2025-12-13 06:36:10
-- ============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- 1. CRIAR TABELAS
-- ============================================================================

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


-- ============================================================================
-- 2. TEXTOS BASE
-- ============================================================================

-- Total de textos base: 4
DELETE FROM textos_base;
ALTER TABLE textos_base AUTO_INCREMENT = 1;

INSERT INTO textos_base (`id`, `titulo`, `tipo`, `conteudo`, `escola_id`, `autor_id`, `created_at`, `updated_at`) VALUES (1, 'Texto A - Sustentabilidade Ambiental', 'texto', 'A sustentabilidade ambiental tornou-se um tema central nas discussoes globais. Preservar os recursos naturais e adotar praticas sustentaveis sao fundamentais para garantir um futuro melhor as proximas geracoes. O equilibrio entre desenvolvimento economico e conservacao ambiental e o grande desafio do seculo XXI. As empresas precisam repensar seus modelos de producao, reduzindo o desperdicio e investindo em tecnologias limpas. Da mesma forma, os cidadaos devem incorporar habitos mais conscientes no dia a dia, como a reducao do consumo de plastico e a economia de agua e energia.', 60, 1, '2025-12-12 21:28:52', '2025-12-12 21:28:52');
INSERT INTO textos_base (`id`, `titulo`, `tipo`, `conteudo`, `escola_id`, `autor_id`, `created_at`, `updated_at`) VALUES (2, 'Texto B - Tecnologia Digital', 'texto', 'A tecnologia digital transformou profundamente a forma como nos comunicamos. As redes sociais conectam pessoas ao redor do mundo instantaneamente, mas tambem trazem desafios relacionados a privacidade e ao uso consciente da informacao. E fundamental educar as novas geracoes para um uso responsavel da tecnologia. O excesso de exposicao as telas pode causar problemas de saude fisica e mental, especialmente entre criancas e adolescentes. Por outro lado, a tecnologia oferece oportunidades incriveis de aprendizado, trabalho remoto e acesso a cultura. O desafio e encontrar o equilibrio.', 60, 1, '2025-12-12 21:28:52', '2025-12-12 21:28:52');
INSERT INTO textos_base (`id`, `titulo`, `tipo`, `conteudo`, `escola_id`, `autor_id`, `created_at`, `updated_at`) VALUES (3, 'Texto A - Sustentabilidade Ambiental', 'texto', 'A sustentabilidade ambiental tornou-se um tema central nas discussoes globais. Preservar os recursos naturais e adotar praticas sustentaveis sao fundamentais para garantir um futuro melhor as proximas geracoes. O equilibrio entre desenvolvimento economico e conservacao ambiental e o grande desafio do seculo XXI.', 60, 1, '2025-12-12 21:33:04', '2025-12-12 21:33:04');
INSERT INTO textos_base (`id`, `titulo`, `tipo`, `conteudo`, `escola_id`, `autor_id`, `created_at`, `updated_at`) VALUES (4, 'Texto B - Tecnologia Digital', 'texto', 'A tecnologia digital transformou profundamente a forma como nos comunicamos. As redes sociais conectam pessoas ao redor do mundo instantaneamente, mas tambem trazem desafios relacionados a privacidade e ao uso consciente da informacao. O desafio e encontrar o equilibrio entre beneficios e riscos.', 60, 1, '2025-12-12 21:33:04', '2025-12-12 21:33:04');

-- ✓ 4 textos base exportados

-- ============================================================================
-- 3. QUESTÕES
-- ============================================================================

-- Total de questões: 9
-- ATENÇÃO: Não apaga questões existentes, apenas insere novas
-- Se quiser substituir, execute: DELETE FROM questoes; antes

-- Questão original ID: 2
INSERT INTO questoes (`componente_curricular`, `ano_escolar`, `habilidade_bncc_codigo`, `tipo`, `dificuldade`, `tempo_estimado`, `enunciado`, `texto_apoio`, `gabarito_dissertativa`, `pontuacao_maxima`, `contexto`, `vezes_aplicada`, `status`, `visibilidade`, `escola_id`, `autor_id`, `created_at`, `updated_at`) VALUES ('História', '7º ano', 'EF07HI01', 'dissertativa', 'media', 3, 'Observe a imagem', 'De acordo com esse exemplo', '', 10.00, 'escolar', 0, 'revisao', 'escola', 60, 1, '2025-11-29 14:01:25', '2025-11-29 14:01:25');
SET @questao_2_id = LAST_INSERT_ID();

-- Questão original ID: 3
INSERT INTO questoes (`componente_curricular`, `ano_escolar`, `habilidade_bncc_codigo`, `tipo`, `dificuldade`, `tempo_estimado`, `enunciado`, `pontuacao_maxima`, `contexto`, `vezes_aplicada`, `status`, `visibilidade`, `escola_id`, `autor_id`, `created_at`, `updated_at`) VALUES ('Língua Portuguesa', '7º ano', 'EF69LP03', 'dissertativa', 'media', 3, 'Com base nos textos A e B, identifique o tema central de cada um e compare-os quanto a relevancia para a sociedade atual. Justifique sua resposta.', 10.00, 'escolar', 0, 'aprovada', 'escola', 60, 1, '2025-12-12 21:28:52', '2025-12-12 21:28:52');
SET @questao_3_id = LAST_INSERT_ID();

-- Questão original ID: 4
INSERT INTO questoes (`componente_curricular`, `ano_escolar`, `habilidade_bncc_codigo`, `tipo`, `dificuldade`, `tempo_estimado`, `enunciado`, `pontuacao_maxima`, `contexto`, `vezes_aplicada`, `status`, `visibilidade`, `escola_id`, `autor_id`, `created_at`, `updated_at`) VALUES ('Língua Portuguesa', '7º ano', 'EF69LP03', 'dissertativa', 'media', 3, 'Escolha um dos textos e elabore tres perguntas que poderiam ser feitas a partir de sua leitura. Suas perguntas devem explorar diferentes aspectos do texto.', 10.00, 'escolar', 0, 'aprovada', 'escola', 60, 1, '2025-12-12 21:28:52', '2025-12-12 21:28:52');
SET @questao_4_id = LAST_INSERT_ID();

-- Questão original ID: 5
INSERT INTO questoes (`componente_curricular`, `ano_escolar`, `habilidade_bncc_codigo`, `tipo`, `dificuldade`, `tempo_estimado`, `enunciado`, `pontuacao_maxima`, `contexto`, `vezes_aplicada`, `status`, `visibilidade`, `escola_id`, `autor_id`, `created_at`, `updated_at`) VALUES ('Língua Portuguesa', '7º ano', 'EF67LP08', 'multipla_escolha', 'facil', 3, 'Segundo o Texto A, qual e o grande desafio do seculo XXI?', 10.00, 'escolar', 0, 'aprovada', 'escola', 60, 1, '2025-12-12 21:28:52', '2025-12-12 21:28:52');
SET @questao_5_id = LAST_INSERT_ID();

-- Questão original ID: 6
INSERT INTO questoes (`componente_curricular`, `ano_escolar`, `habilidade_bncc_codigo`, `tipo`, `dificuldade`, `tempo_estimado`, `enunciado`, `pontuacao_maxima`, `contexto`, `vezes_aplicada`, `status`, `visibilidade`, `escola_id`, `autor_id`, `created_at`, `updated_at`) VALUES ('Língua Portuguesa', '7º ano', 'EF69LP03', 'dissertativa', 'media', 3, 'Com base nos textos A e B, identifique o tema central de cada um e compare-os quanto a relevancia para a sociedade atual.', 10.00, 'escolar', 0, 'aprovada', 'escola', 60, 1, '2025-12-12 21:33:04', '2025-12-12 21:33:04');
SET @questao_6_id = LAST_INSERT_ID();

-- Questão original ID: 7
INSERT INTO questoes (`componente_curricular`, `ano_escolar`, `habilidade_bncc_codigo`, `tipo`, `dificuldade`, `tempo_estimado`, `enunciado`, `pontuacao_maxima`, `contexto`, `vezes_aplicada`, `status`, `visibilidade`, `escola_id`, `autor_id`, `created_at`, `updated_at`) VALUES ('Língua Portuguesa', '7º ano', 'EF69LP03', 'dissertativa', 'media', 3, 'Escolha um dos textos e elabore tres perguntas sobre seu conteudo.', 10.00, 'escolar', 0, 'aprovada', 'escola', 60, 1, '2025-12-12 21:33:04', '2025-12-12 21:33:04');
SET @questao_7_id = LAST_INSERT_ID();

-- Questão original ID: 8
INSERT INTO questoes (`componente_curricular`, `ano_escolar`, `habilidade_bncc_codigo`, `tipo`, `dificuldade`, `tempo_estimado`, `enunciado`, `pontuacao_maxima`, `contexto`, `vezes_aplicada`, `status`, `visibilidade`, `escola_id`, `autor_id`, `created_at`, `updated_at`) VALUES ('Língua Portuguesa', '7º ano', 'EF67LP08', 'multipla_escolha', 'facil', 3, 'Segundo o Texto A, qual e o grande desafio do seculo XXI?', 10.00, 'escolar', 0, 'aprovada', 'escola', 60, 1, '2025-12-12 21:33:04', '2025-12-12 21:33:04');
SET @questao_8_id = LAST_INSERT_ID();

INSERT INTO questoes_alternativas (questao_id, `letra`, `texto`, `correta`, `ordem`) VALUES (@questao_8_id, 'A', 'Aumentar a producao industrial', 0, 0);
INSERT INTO questoes_alternativas (questao_id, `letra`, `texto`, `correta`, `ordem`) VALUES (@questao_8_id, 'B', 'Equilibrar desenvolvimento economico e conservacao ambiental', 1, 0);
INSERT INTO questoes_alternativas (questao_id, `letra`, `texto`, `correta`, `ordem`) VALUES (@questao_8_id, 'C', 'Reduzir o uso de tecnologias', 0, 0);
INSERT INTO questoes_alternativas (questao_id, `letra`, `texto`, `correta`, `ordem`) VALUES (@questao_8_id, 'D', 'Ignorar problemas ambientais', 0, 0);

-- Questão original ID: 9
INSERT INTO questoes (`componente_curricular`, `ano_escolar`, `habilidade_bncc_codigo`, `tipo`, `dificuldade`, `tempo_estimado`, `enunciado`, `pontuacao_maxima`, `contexto`, `vezes_aplicada`, `status`, `visibilidade`, `escola_id`, `autor_id`, `created_at`, `updated_at`) VALUES ('Língua Portuguesa', '7º ano', 'EF67LP08', 'multipla_escolha', 'facil', 3, 'De acordo com o Texto B, qual e o principal desafio da tecnologia digital?', 10.00, 'escolar', 0, 'aprovada', 'escola', 60, 1, '2025-12-12 21:33:04', '2025-12-12 21:33:04');
SET @questao_9_id = LAST_INSERT_ID();

INSERT INTO questoes_alternativas (questao_id, `letra`, `texto`, `correta`, `ordem`) VALUES (@questao_9_id, 'A', 'Eliminar as redes sociais', 0, 0);
INSERT INTO questoes_alternativas (questao_id, `letra`, `texto`, `correta`, `ordem`) VALUES (@questao_9_id, 'B', 'Encontrar equilibrio entre beneficios e riscos', 1, 0);
INSERT INTO questoes_alternativas (questao_id, `letra`, `texto`, `correta`, `ordem`) VALUES (@questao_9_id, 'C', 'Aumentar exposicao as telas', 0, 0);
INSERT INTO questoes_alternativas (questao_id, `letra`, `texto`, `correta`, `ordem`) VALUES (@questao_9_id, 'D', 'Proibir acesso de criancas', 0, 0);

-- Questão original ID: 10
INSERT INTO questoes (`componente_curricular`, `ano_escolar`, `habilidade_bncc_codigo`, `tipo`, `dificuldade`, `tempo_estimado`, `enunciado`, `pontuacao_maxima`, `contexto`, `vezes_aplicada`, `status`, `visibilidade`, `escola_id`, `autor_id`, `created_at`, `updated_at`) VALUES ('Língua Portuguesa', '7º ano', 'EF67LP32', 'multipla_escolha', 'facil', 3, 'No Texto A, a palavra "sustentaveis" pode ser substituida por:', 10.00, 'escolar', 0, 'aprovada', 'escola', 60, 1, '2025-12-12 21:33:04', '2025-12-12 21:33:04');
SET @questao_10_id = LAST_INSERT_ID();

INSERT INTO questoes_alternativas (questao_id, `letra`, `texto`, `correta`, `ordem`) VALUES (@questao_10_id, 'A', 'Descartaveis', 0, 0);
INSERT INTO questoes_alternativas (questao_id, `letra`, `texto`, `correta`, `ordem`) VALUES (@questao_10_id, 'B', 'Renovaveis e duradouras', 1, 0);
INSERT INTO questoes_alternativas (questao_id, `letra`, `texto`, `correta`, `ordem`) VALUES (@questao_10_id, 'C', 'Caras e inacessiveis', 0, 0);
INSERT INTO questoes_alternativas (questao_id, `letra`, `texto`, `correta`, `ordem`) VALUES (@questao_10_id, 'D', 'Antigas e ultrapassadas', 0, 0);


-- ✓ 9 questões exportadas com suas alternativas

-- ============================================================================
-- 4. AVALIAÇÕES
-- ============================================================================

-- Nenhuma avaliação encontrada

-- ============================================================================
SET FOREIGN_KEY_CHECKS = 1;
-- ✓ EXPORTAÇÃO CONCLUÍDA
-- ============================================================================
