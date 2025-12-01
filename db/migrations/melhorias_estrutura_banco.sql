-- =============================================================================
-- SCRIPT DE MELHORIAS NA ESTRUTURA DO BANCO DE DADOS
-- Sistema de Gestão Escolar
-- Data: 2025
-- =============================================================================

-- =============================================================================
-- 1. EXCLUSÃO DE TABELAS REDUNDANTES/VAZIAS
-- =============================================================================

-- Remover tabela ano_letivo (duplicata de anosletivos - sem dados importantes)
DROP TABLE IF EXISTS ano_letivo;

-- Remover tabela professores (vazia - usar funcionarios com cargo='Professor')
DROP TABLE IF EXISTS professores;


-- =============================================================================
-- 2. ADICIONAR FOREIGN KEYS FALTANTES
-- =============================================================================

-- 2.1 notas.ano_letivo_id → anosletivos.id
ALTER TABLE notas
ADD CONSTRAINT fk_notas_ano_letivo
FOREIGN KEY (ano_letivo_id) REFERENCES anosletivos(id)
ON DELETE RESTRICT ON UPDATE CASCADE;

-- 2.2 turmas.escola_id → escolas.id
ALTER TABLE turmas
ADD CONSTRAINT fk_turmas_escola
FOREIGN KEY (escola_id) REFERENCES escolas(id)
ON DELETE RESTRICT ON UPDATE CASCADE;

-- 2.3 funcionarios.escola_id → escolas.id
ALTER TABLE funcionarios
ADD CONSTRAINT fk_funcionarios_escola
FOREIGN KEY (escola_id) REFERENCES escolas(id)
ON DELETE RESTRICT ON UPDATE CASCADE;

-- 2.4 documentos_emitidos.funcionario_id → funcionarios.id
ALTER TABLE documentos_emitidos
ADD CONSTRAINT fk_documentos_emitidos_funcionario
FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
ON DELETE SET NULL ON UPDATE CASCADE;

-- 2.5 documentosemitidos.aluno_id → alunos.id
ALTER TABLE documentosemitidos
ADD CONSTRAINT fk_documentosemitidos_aluno
FOREIGN KEY (aluno_id) REFERENCES alunos(id)
ON DELETE CASCADE ON UPDATE CASCADE;

-- 2.6 documentosemitidos.funcionario_id → funcionarios.id
ALTER TABLE documentosemitidos
ADD CONSTRAINT fk_documentosemitidos_funcionario
FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
ON DELETE SET NULL ON UPDATE CASCADE;

-- 2.7 funcionario_faltas_mensal.funcionario_id → funcionarios.id
ALTER TABLE funcionario_faltas_mensal
ADD CONSTRAINT fk_func_faltas_mensal_funcionario
FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
ON DELETE CASCADE ON UPDATE CASCADE;

-- 2.8 logs_acesso.usuario_id → usuarios.id
ALTER TABLE logs_acesso
ADD CONSTRAINT fk_logs_acesso_usuario
FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
ON DELETE SET NULL ON UPDATE CASCADE;

-- 2.9 sessoes_usuario.usuario_id → usuarios.id
ALTER TABLE sessoes_usuario
ADD CONSTRAINT fk_sessoes_usuario_usuario
FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
ON DELETE CASCADE ON UPDATE CASCADE;

-- 2.10 usuario_permissoes.usuario_id → usuarios.id
ALTER TABLE usuario_permissoes
ADD CONSTRAINT fk_usuario_permissoes_usuario
FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
ON DELETE CASCADE ON UPDATE CASCADE;

-- 2.11 desempenho_aluno_habilidade.ultima_avaliacao_id → avaliacoes_aplicadas.id
-- Verificar se a FK já não existe antes de adicionar
ALTER TABLE desempenho_aluno_habilidade
ADD CONSTRAINT fk_desemp_ultima_avaliacao
FOREIGN KEY (ultima_avaliacao_id) REFERENCES avaliacoes_aplicadas(id)
ON DELETE SET NULL ON UPDATE CASCADE;


-- =============================================================================
-- 3. CRIAR ÍNDICES COMPOSTOS PARA PERFORMANCE
-- =============================================================================

-- 3.1 Índice composto para busca de notas (query mais frequente)
CREATE INDEX idx_notas_completo 
ON notas(aluno_id, disciplina_id, bimestre, ano_letivo_id);

-- 3.2 Índice composto para busca de faltas bimestrais
CREATE INDEX idx_faltas_aluno_bim_ano 
ON faltas_bimestrais(aluno_id, bimestre, ano_letivo_id);

-- 3.3 Índice composto para busca de questões no banco de questões
CREATE INDEX idx_questoes_busca 
ON questoes(componente_curricular, ano_escolar, habilidade_bncc_codigo, status);


-- =============================================================================
-- 4. VERIFICAÇÃO FINAL
-- =============================================================================

-- Listar FKs criadas para verificação
SELECT 
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE CONSTRAINT_SCHEMA = DATABASE()
    AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME, CONSTRAINT_NAME;
