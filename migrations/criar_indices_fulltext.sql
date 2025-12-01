-- ============================================================================
-- ÍNDICES FULLTEXT PARA OTIMIZAÇÃO DE PESQUISA
-- Sistema de Gestão Escolar
-- Data: 11 de novembro de 2025
-- ============================================================================

-- Verificar se os índices já existem antes de criar
-- Para remover índices antigos se necessário:
-- ALTER TABLE Alunos DROP INDEX IF EXISTS ft_nome;
-- ALTER TABLE Funcionarios DROP INDEX IF EXISTS ft_nome;

-- 1. Criar índice FULLTEXT para pesquisa de alunos por nome
-- Este índice permite pesquisa mais rápida e inteligente (ignora stopwords, suporta busca parcial)
ALTER TABLE Alunos ADD FULLTEXT INDEX ft_nome (nome);

-- 2. Criar índice FULLTEXT para pesquisa de funcionários por nome
ALTER TABLE Funcionarios ADD FULLTEXT INDEX ft_nome (nome);

-- ============================================================================
-- VERIFICAR ÍNDICES CRIADOS
-- ============================================================================

-- Ver todos os índices da tabela Alunos
SHOW INDEX FROM Alunos WHERE Key_name = 'ft_nome';

-- Ver todos os índices da tabela Funcionarios
SHOW INDEX FROM Funcionarios WHERE Key_name = 'ft_nome';

-- ============================================================================
-- TESTAR PERFORMANCE DA PESQUISA FULLTEXT
-- ============================================================================

-- Exemplo de pesquisa tradicional (LIKE)
EXPLAIN SELECT id, nome 
FROM Alunos 
WHERE nome LIKE '%maria%';

-- Exemplo de pesquisa com FULLTEXT (mais rápido)
EXPLAIN SELECT id, nome 
FROM Alunos 
WHERE MATCH(nome) AGAINST('maria' IN NATURAL LANGUAGE MODE);

-- ============================================================================
-- NOTAS IMPORTANTES
-- ============================================================================

/*
1. FULLTEXT é mais eficiente que LIKE para:
   - Pesquisas em texto
   - Palavras completas ou parciais
   - Grandes volumes de dados

2. Modos de busca FULLTEXT:
   - NATURAL LANGUAGE MODE: busca natural (padrão)
   - BOOLEAN MODE: permite operadores (+, -, *, etc)
   - WITH QUERY EXPANSION: expande resultados

3. Limitações:
   - Palavras muito curtas (<3 caracteres) podem ser ignoradas
   - Stopwords (palavras comuns) são ignoradas por padrão
   - Requer InnoDB ou MyISAM

4. Performance:
   - LIKE '%termo%': O(n) - precisa escanear toda a tabela
   - MATCH AGAINST: O(log n) - usa índice invertido
   - Ganho: 50-90% mais rápido em tabelas grandes
*/
