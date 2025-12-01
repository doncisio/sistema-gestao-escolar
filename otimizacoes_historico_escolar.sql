-- ============================================================================
-- SCRIPT DE OTIMIZAÇÕES PARA HISTÓRICO ESCOLAR
-- Arquivo: otimizacoes_historico_escolar.sql
-- 
-- INSTRUÇÕES PARA EXECUÇÃO:
-- 1. Conecte ao seu banco MySQL
-- 2. Execute este arquivo completo
-- 3. Aguarde a conclusão (pode demorar alguns minutos)
-- ============================================================================

-- Usar o banco de dados (substitua pelo nome correto do seu banco)
-- USE redeescola;  -- Descomente e ajuste o nome do seu banco

-- ============================================================================
-- VERIFICAÇÃO DE ESTRUTURA
-- ============================================================================
SELECT 'Verificando estrutura do banco...' as status;

-- Verificar se tabelas necessárias existem
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN CONCAT('✓ Tabela ', table_name, ' encontrada')
        ELSE CONCAT('✗ Tabela ', table_name, ' NÃO encontrada')
    END as verificacao
FROM information_schema.tables 
WHERE table_schema = DATABASE() 
AND table_name IN ('historico_escolar', 'alunos', 'disciplinas', 'serie', 'escolas', 'anosletivos')
GROUP BY table_name;

-- ============================================================================
-- PARTE 1: ÍNDICES ESPECÍFICOS PARA HISTÓRICO ESCOLAR
-- ============================================================================
SELECT 'Aplicando índices específicos para histórico escolar...' as status;

-- Remover índices se já existirem (para evitar erros)
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM information_schema.STATISTICS 
     WHERE table_schema = DATABASE() AND table_name = 'historico_escolar' AND index_name = 'idx_aluno_historico') > 0,
    'DROP INDEX idx_aluno_historico ON historico_escolar',
    'SELECT "Índice idx_aluno_historico não existe, criando..." as info'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM information_schema.STATISTICS 
     WHERE table_schema = DATABASE() AND table_name = 'historico_escolar' AND index_name = 'idx_historico_filtros') > 0,
    'DROP INDEX idx_historico_filtros ON historico_escolar',
    'SELECT "Índice idx_historico_filtros não existe, criando..." as info'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM information_schema.STATISTICS 
     WHERE table_schema = DATABASE() AND table_name = 'historico_escolar' AND index_name = 'idx_escola_serie') > 0,
    'DROP INDEX idx_escola_serie ON historico_escolar',
    'SELECT "Índice idx_escola_serie não existe, criando..." as info'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM information_schema.STATISTICS 
     WHERE table_schema = DATABASE() AND table_name = 'historico_escolar' AND index_name = 'idx_disciplinas_disponiveis') > 0,
    'DROP INDEX idx_disciplinas_disponiveis ON historico_escolar',
    'SELECT "Índice idx_disciplinas_disponiveis não existe, criando..." as info'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Criar os novos índices para histórico escolar
SELECT 'Criando índice principal para consultas de histórico por aluno...' as status;
CREATE INDEX idx_aluno_historico ON historico_escolar (aluno_id, ano_letivo_id DESC, serie_id);

SELECT 'Criando índice para aplicação de filtros no histórico...' as status;
CREATE INDEX idx_historico_filtros ON historico_escolar (aluno_id, disciplina_id, serie_id, escola_id, ano_letivo_id);

SELECT 'Criando índice para consultas por escola e série...' as status;
CREATE INDEX idx_escola_serie ON historico_escolar (escola_id, serie_id, ano_letivo_id);

SELECT 'Criando índice para listar disciplinas disponíveis...' as status;
CREATE INDEX idx_disciplinas_disponiveis ON historico_escolar (escola_id, serie_id, ano_letivo_id, disciplina_id);

-- ============================================================================
-- PARTE 2: ÍNDICES COMPLEMENTARES (FULLTEXT E OUTROS)
-- ============================================================================
SELECT 'Verificando e criando índices complementares...' as status;

-- Verificar e criar FULLTEXT index para alunos (se não existir)
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM information_schema.STATISTICS 
     WHERE table_schema = DATABASE() AND table_name = 'alunos' AND index_name = 'ft_nome') > 0,
    'SELECT "Índice FULLTEXT ft_nome já existe em alunos" as info',
    'CREATE FULLTEXT INDEX ft_nome ON alunos (nome)'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Índice para disciplinas por nome (se não existir)
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM information_schema.STATISTICS 
     WHERE table_schema = DATABASE() AND table_name = 'disciplinas' AND index_name = 'idx_disciplina_nome') > 0,
    'SELECT "Índice idx_disciplina_nome já existe" as info',
    'CREATE INDEX idx_disciplina_nome ON disciplinas (nome)'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Índice para séries por nome (se não existir)
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM information_schema.STATISTICS 
     WHERE table_schema = DATABASE() AND table_name = 'serie' AND index_name = 'idx_serie_nome') > 0,
    'SELECT "Índice idx_serie_nome já existe" as info',
    'CREATE INDEX idx_serie_nome ON serie (nome)'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Índice para escolas por nome (se não existir)  
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM information_schema.STATISTICS 
     WHERE table_schema = DATABASE() AND table_name = 'escolas' AND index_name = 'idx_escola_nome') > 0,
    'SELECT "Índice idx_escola_nome já existe" as info',
    'CREATE INDEX idx_escola_nome ON escolas (nome)'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Índice para anos letivos (se não existir)
SET @sql = (SELECT IF(
    (SELECT COUNT(*) FROM information_schema.STATISTICS 
     WHERE table_schema = DATABASE() AND table_name = 'anosletivos' AND index_name = 'idx_ano_letivo') > 0,
    'SELECT "Índice idx_ano_letivo já existe" as info',
    'CREATE INDEX idx_ano_letivo ON anosletivos (ano_letivo DESC)'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ============================================================================
-- PARTE 3: ATUALIZAR ESTATÍSTICAS DAS TABELAS
-- ============================================================================
SELECT 'Atualizando estatísticas das tabelas...' as status;

ANALYZE TABLE historico_escolar;
ANALYZE TABLE alunos;
ANALYZE TABLE disciplinas;
ANALYZE TABLE serie;
ANALYZE TABLE escolas;
ANALYZE TABLE anosletivos;

-- ============================================================================
-- PARTE 4: RELATÓRIO FINAL
-- ============================================================================
SELECT 'RELATÓRIO DE OTIMIZAÇÕES APLICADAS' as status;
SELECT '========================================' as separador;

-- Mostrar índices criados na tabela historico_escolar
SELECT 
    'historico_escolar' as tabela,
    index_name as indice_criado,
    GROUP_CONCAT(column_name ORDER BY seq_in_index) as colunas
FROM information_schema.STATISTICS 
WHERE table_schema = DATABASE() 
AND table_name = 'historico_escolar'
AND index_name IN ('idx_aluno_historico', 'idx_historico_filtros', 'idx_escola_serie', 'idx_disciplinas_disponiveis')
GROUP BY index_name;

-- Verificar se FULLTEXT foi criado
SELECT 
    table_name as tabela,
    index_name as indice_fulltext,
    'FULLTEXT search habilitado' as status
FROM information_schema.STATISTICS 
WHERE table_schema = DATABASE() 
AND index_name = 'ft_nome'
AND table_name IN ('alunos', 'funcionarios');

-- Contar total de índices nas tabelas principais
SELECT 
    table_name as tabela,
    COUNT(DISTINCT index_name) as total_indices
FROM information_schema.STATISTICS 
WHERE table_schema = DATABASE() 
AND table_name IN ('historico_escolar', 'alunos', 'disciplinas', 'serie', 'escolas', 'anosletivos')
GROUP BY table_name
ORDER BY table_name;

SELECT 'OTIMIZAÇÕES CONCLUÍDAS COM SUCESSO!' as resultado;
SELECT 'Interface de histórico escolar deve estar mais rápida agora!' as observacao;

-- ============================================================================
-- INSTRUÇÕES PÓS-EXECUÇÃO
-- ============================================================================
SELECT 'PRÓXIMOS PASSOS:' as instrucoes;
SELECT '1. Teste a interface de histórico escolar' as passo_1;
SELECT '2. Monitore a performance das consultas' as passo_2;  
SELECT '3. Verifique o uso de memória do MySQL' as passo_3;
SELECT '4. Documente os resultados obtidos' as passo_4;