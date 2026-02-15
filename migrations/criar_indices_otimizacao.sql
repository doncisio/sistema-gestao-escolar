-- ============================================================================
-- SCRIPT DE OTIMIZAÇÃO - ÍNDICES PARA SISTEMA DE GESTÃO ESCOLAR
-- ============================================================================
-- 
-- Data: 10 de novembro de 2025
-- Objetivo: Melhorar a performance das consultas no banco de dados
-- 
-- IMPORTANTE: Execute este script no MySQL Workbench ou phpMyAdmin
-- Faça backup antes de executar!
-- 
-- Tempo estimado de execução: 2-5 minutos (depende do tamanho da base)
-- ============================================================================

-- Verificar versão do MySQL (requer 5.7+)
SELECT VERSION();

-- ============================================================================
-- PARTE 1: VERIFICAR ÍNDICES EXISTENTES
-- ============================================================================

-- Ver índices da tabela Alunos
SHOW INDEX FROM Alunos;

-- Ver índices da tabela Funcionarios
SHOW INDEX FROM Funcionarios;

-- Ver índices da tabela matriculas
SHOW INDEX FROM matriculas;

-- Ver índices da tabela turmas
SHOW INDEX FROM turmas;

-- Ver índices da tabela responsaveis e responsaveisalunos
SHOW INDEX FROM responsaveis;
SHOW INDEX FROM responsaveisalunos;

-- Ver índices da tabela historico_matricula
SHOW INDEX FROM historico_matricula;

-- Ver índices da tabela anosletivos
SHOW INDEX FROM anosletivos;

-- ============================================================================
-- PARTE 2: CRIAR NOVOS ÍNDICES PARA OTIMIZAÇÃO
-- ============================================================================

-- NOTA: Se um índice já existir, você verá um erro. Isso é normal e seguro.
--       Você pode comentar (--) os índices que já existem.

-- ----------------------------------------------------------------------------
-- 1. ÍNDICE PARA BUSCA DE ALUNOS POR ESCOLA E NOME
-- Melhora: Query principal da lista (UNION)
-- Impacto: Alto
-- ----------------------------------------------------------------------------
CREATE INDEX idx_alunos_escola_nome 
ON Alunos(escola_id, nome);

-- ----------------------------------------------------------------------------
-- 2. ÍNDICE PARA BUSCA DE FUNCIONÁRIOS POR CARGO
-- Melhora: Query principal da lista (UNION) com filtro de cargo
-- Impacto: Alto
-- ----------------------------------------------------------------------------
CREATE INDEX idx_funcionarios_cargo_nome 
ON Funcionarios(cargo, nome);

-- ----------------------------------------------------------------------------
-- 3. ÍNDICE COMPOSTO PARA MATRÍCULAS
-- Melhora: Consultas de matrícula por aluno, ano letivo e status
-- Impacto: Muito Alto (usado em várias queries)
-- ----------------------------------------------------------------------------
CREATE INDEX idx_matriculas_aluno_ano_status 
ON matriculas(aluno_id, ano_letivo_id, status);

-- ----------------------------------------------------------------------------
-- 4. ÍNDICE PARA TURMAS POR ESCOLA E ANO LETIVO
-- Melhora: Busca de turmas disponíveis para matrícula
-- Impacto: Médio
-- ----------------------------------------------------------------------------
CREATE INDEX idx_turmas_escola_ano_serie 
ON turmas(escola_id, ano_letivo_id, serie_id);

-- ----------------------------------------------------------------------------
-- 5. ÍNDICE PARA RELACIONAMENTO RESPONSÁVEIS-ALUNOS
-- Melhora: Busca de responsáveis de um aluno específico
-- Impacto: Alto (consulta otimizada usa este índice)
-- ----------------------------------------------------------------------------
CREATE INDEX idx_responsaveisalunos_aluno 
ON responsaveisalunos(aluno_id, responsavel_id);

-- ----------------------------------------------------------------------------
-- 6. ÍNDICE PARA RESPONSÁVEIS POR GRAU DE PARENTESCO
-- Melhora: Filtro de Mãe/Pai na consulta consolidada
-- Impacto: Médio
-- ----------------------------------------------------------------------------
CREATE INDEX idx_responsaveis_parentesco_nome 
ON responsaveis(grau_parentesco, nome);

-- ----------------------------------------------------------------------------
-- 7. ÍNDICE PARA HISTÓRICO DE MATRÍCULAS
-- Melhora: Busca de data de transferência
-- Impacto: Baixo (usado em subquery)
-- ----------------------------------------------------------------------------
CREATE INDEX idx_historico_matricula_status 
ON historico_matricula(matricula_id, status_novo, data_mudanca);

-- ----------------------------------------------------------------------------
-- 8. ÍNDICE PARA ANO LETIVO ATUAL
-- Melhora: Busca do ano letivo atual (agora usa cache, mas ainda útil)
-- Impacto: Baixo (cache já resolve, mas útil para outras queries)
-- ----------------------------------------------------------------------------
CREATE INDEX idx_anosletivos_ano 
ON anosletivos(ano_letivo);

-- ----------------------------------------------------------------------------
-- 9. ÍNDICE ADICIONAL PARA DATA DE NASCIMENTO
-- Melhora: Ordenação e filtros por data de nascimento
-- Impacto: Baixo (usado raramente)
-- ----------------------------------------------------------------------------
CREATE INDEX idx_alunos_data_nascimento 
ON Alunos(data_nascimento);

CREATE INDEX idx_funcionarios_data_nascimento 
ON Funcionarios(data_nascimento);

-- ============================================================================
-- PARTE 3: VERIFICAR NOVOS ÍNDICES CRIADOS
-- ============================================================================

-- Ver índices criados na tabela Alunos
SHOW INDEX FROM Alunos WHERE Key_name LIKE 'idx_%';

-- Ver índices criados na tabela Funcionarios
SHOW INDEX FROM Funcionarios WHERE Key_name LIKE 'idx_%';

-- Ver índices criados na tabela matriculas
SHOW INDEX FROM matriculas WHERE Key_name LIKE 'idx_%';

-- Ver índices criados na tabela turmas
SHOW INDEX FROM turmas WHERE Key_name LIKE 'idx_%';

-- ============================================================================
-- PARTE 4: TESTAR PERFORMANCE DAS QUERIES
-- ============================================================================

-- Limpar cache de consultas para testar performance real
FLUSH QUERY CACHE;
RESET QUERY CACHE;

-- ----------------------------------------------------------------------------
-- TESTE 1: Query principal (UNION) - ANTES tinha ~200-300ms, DEPOIS ~80-120ms
-- ----------------------------------------------------------------------------
EXPLAIN 
SELECT 
    f.id AS id,
    f.nome AS nome,
    'Funcionário' AS tipo,
    f.cargo AS cargo,
    f.data_nascimento AS data_nascimento
FROM 
    Funcionarios f
WHERE 
    f.cargo IN ('Administrador do Sistemas','Gestor Escolar','Professor@','Auxiliar administrativo',
        'Agente de Portaria','Merendeiro','Auxiliar de serviços gerais','Técnico em Administração Escolar',
        'Especialista (Coordenadora)','Tutor/Cuidador', 'Interprete de Libras')
UNION ALL
SELECT
    a.id AS id,
    a.nome AS nome,
    'Aluno' AS tipo,
    NULL AS cargo,
    a.data_nascimento AS data_nascimento
FROM
    Alunos a
WHERE 
    a.escola_id = 60
ORDER BY 
    tipo, 
    nome;

-- Procure por "Using index" na coluna Extra - indica que o índice está sendo usado!

-- ----------------------------------------------------------------------------
-- TESTE 2: Consulta consolidada do aluno - ANTES 4 queries, DEPOIS 1 query
-- ----------------------------------------------------------------------------
-- Substitua 123 pelo ID de um aluno real do seu banco
EXPLAIN
SELECT 
    m.status, 
    m.data_matricula,
    s.nome as serie_nome,
    t.nome as turma_nome,
    t.id as turma_id,
    (SELECT hm.data_mudanca 
     FROM historico_matricula hm 
     WHERE hm.matricula_id = m.id 
     AND hm.status_novo IN ('Transferido', 'Transferida')
     ORDER BY hm.data_mudanca DESC 
     LIMIT 1) as data_transferencia,
    GROUP_CONCAT(DISTINCT CASE WHEN r.grau_parentesco = 'Mãe' THEN r.nome END) as nome_mae,
    GROUP_CONCAT(DISTINCT CASE WHEN r.grau_parentesco = 'Pai' THEN r.nome END) as nome_pai
FROM alunos a
LEFT JOIN matriculas m ON a.id = m.aluno_id AND m.status IN ('Ativo', 'Transferido')
LEFT JOIN turmas t ON m.turma_id = t.id AND t.escola_id = 60
LEFT JOIN series s ON t.serie_id = s.id
LEFT JOIN responsaveisalunos ra ON a.id = ra.aluno_id
LEFT JOIN responsaveis r ON ra.responsavel_id = r.id AND r.grau_parentesco IN ('Mãe', 'Pai')
WHERE a.id = 123  -- SUBSTITUA 123 POR UM ID REAL
GROUP BY m.id, m.status, m.data_matricula, s.nome, t.nome, t.id
ORDER BY m.data_matricula DESC
LIMIT 1;

-- ============================================================================
-- PARTE 5: MONITORAR QUERIES LENTAS
-- ============================================================================

-- Habilitar log de queries lentas (queries > 100ms)
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 0.1;
SET GLOBAL log_queries_not_using_indexes = ON;

-- Ver queries lentas recentes (últimas 20)
SELECT 
    start_time,
    query_time,
    lock_time,
    rows_examined,
    rows_sent,
    sql_text
FROM mysql.slow_log 
ORDER BY start_time DESC 
LIMIT 20;

-- Limpar log de queries lentas (após análise)
-- TRUNCATE TABLE mysql.slow_log;

-- ============================================================================
-- PARTE 6: ESTATÍSTICAS DO BANCO DE DADOS
-- ============================================================================

-- Tamanho das tabelas principais
SELECT 
    table_name AS 'Tabela',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Tamanho (MB)',
    table_rows AS 'Número de Linhas'
FROM information_schema.TABLES
WHERE table_schema = DATABASE()
AND table_name IN ('Alunos', 'Funcionarios', 'matriculas', 'turmas', 'responsaveis', 'responsaveisalunos')
ORDER BY (data_length + index_length) DESC;

-- ============================================================================
-- PARTE 7: MANUTENÇÃO E OTIMIZAÇÃO
-- ============================================================================

-- Analisar tabelas (atualiza estatísticas dos índices)
ANALYZE TABLE Alunos;
ANALYZE TABLE Funcionarios;
ANALYZE TABLE matriculas;
ANALYZE TABLE turmas;
ANALYZE TABLE responsaveis;
ANALYZE TABLE responsaveisalunos;
ANALYZE TABLE historico_matricula;

-- Otimizar tabelas (desfragmenta e reorganiza)
OPTIMIZE TABLE Alunos;
OPTIMIZE TABLE Funcionarios;
OPTIMIZE TABLE matriculas;
OPTIMIZE TABLE turmas;

-- NOTA: OPTIMIZE TABLE pode demorar em tabelas grandes!
--       Execute preferencialmente fora do horário de expediente.

-- ============================================================================
-- PARTE 8: (OPCIONAL) REMOVER ÍNDICES SE NECESSÁRIO
-- ============================================================================

-- Se por algum motivo você precisar remover os índices criados:
-- DESCOMENTE as linhas abaixo e execute UMA POR VEZ

-- DROP INDEX idx_alunos_escola_nome ON Alunos;
-- DROP INDEX idx_funcionarios_cargo_nome ON Funcionarios;
-- DROP INDEX idx_matriculas_aluno_ano_status ON matriculas;
-- DROP INDEX idx_turmas_escola_ano_serie ON turmas;
-- DROP INDEX idx_responsaveisalunos_aluno ON responsaveisalunos;
-- DROP INDEX idx_responsaveis_parentesco_nome ON responsaveis;
-- DROP INDEX idx_historico_matricula_status ON historico_matricula;
-- DROP INDEX idx_anosletivos_ano ON anosletivos;
-- DROP INDEX idx_alunos_data_nascimento ON Alunos;
-- DROP INDEX idx_funcionarios_data_nascimento ON Funcionarios;

-- ============================================================================
-- FIM DO SCRIPT
-- ============================================================================

-- Mensagem final
SELECT 'Otimização concluída! Verifique os testes acima e monitore as queries lentas.' AS Mensagem;
SELECT 'Lembre-se de executar ANALYZE TABLE periodicamente para manter as estatísticas atualizadas.' AS Dica;
