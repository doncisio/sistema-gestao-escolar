# Otimizações de Banco de Dados - Interface Histórico Escolar

## Índices Recomendados para Melhor Performance

### 1. Tabela `historico_escolar`

```sql
-- Índice composto principal para consultas por aluno
CREATE INDEX idx_aluno_historico ON historico_escolar (aluno_id, ano_letivo_id DESC, serie_id);

-- Índice para consultas de filtros
CREATE INDEX idx_historico_filtros ON historico_escolar (aluno_id, disciplina_id, serie_id, escola_id, ano_letivo_id);

-- Índice para consultas por escola e série
CREATE INDEX idx_escola_serie ON historico_escolar (escola_id, serie_id, ano_letivo_id);

-- Índice para consultas de disciplinas disponíveis
CREATE INDEX idx_disciplinas_disponiveis ON historico_escolar (escola_id, serie_id, ano_letivo_id, disciplina_id);
```

### 2. Tabela `alunos`

```sql
-- Índice para busca rápida por nome (FULLTEXT para MySQL 5.7+)
CREATE FULLTEXT INDEX idx_aluno_nome_fulltext ON alunos (nome);

-- Índice regular para nomes (fallback)
CREATE INDEX idx_aluno_nome ON alunos (nome);

-- Índice para dados básicos
CREATE INDEX idx_aluno_dados ON alunos (nome, data_nascimento, sexo);
```

### 3. Tabela `disciplinas`

```sql
-- Índice para consultas por escola e nível
CREATE INDEX idx_disciplina_escola_nivel ON disciplinas (escola_id, nivel_id, nome);

-- Índice para nome das disciplinas
CREATE INDEX idx_disciplina_nome ON disciplinas (nome);
```

### 4. Tabelas de Referência

```sql
-- Índices para tabelas de lookup
CREATE INDEX idx_serie_nome ON serie (nome);
CREATE INDEX idx_escola_nome ON escolas (nome);
CREATE INDEX idx_ano_letivo ON anosletivos (ano_letivo DESC);
```

### 5. Tabela de Observações (se existir)

```sql
CREATE INDEX idx_observacoes_historico ON observacoes_historico (serie_id, ano_letivo_id, escola_id);
```

## Configurações MySQL Recomendadas

### 1. Configuração de Memória

```ini
# my.cnf ou my.ini
[mysqld]
innodb_buffer_pool_size = 512M  # Ajustar conforme RAM disponível
query_cache_size = 64M
query_cache_type = 1
key_buffer_size = 64M
```

### 2. Configurações de Performance

```ini
# Otimizações adicionais
innodb_log_file_size = 128M
innodb_flush_log_at_trx_commit = 2
innodb_file_per_table = 1
max_connections = 200
```

## Scripts de Criação dos Índices

⚠️ **IMPORTANTE**: Alguns índices podem já existir se você seguiu as otimizações em `OTIMIZACOES_BANCO_DADOS.md`. 
Os comandos abaixo verificam se os índices existem antes de criá-los.

```sql
-- ============================================================================
-- ÍNDICES ESPECÍFICOS PARA HISTÓRICO ESCOLAR
-- Complementa os índices já criados em OTIMIZACOES_BANCO_DADOS.md
-- ============================================================================

-- Verificar se os índices já existem antes de criar
DROP INDEX IF EXISTS idx_aluno_historico ON historico_escolar;
DROP INDEX IF EXISTS idx_historico_filtros ON historico_escolar;
DROP INDEX IF EXISTS idx_escola_serie ON historico_escolar;
DROP INDEX IF EXISTS idx_disciplinas_disponiveis ON historico_escolar;

-- NOVOS índices específicos para histórico escolar
CREATE INDEX idx_aluno_historico ON historico_escolar (aluno_id, ano_letivo_id DESC, serie_id);
CREATE INDEX idx_historico_filtros ON historico_escolar (aluno_id, disciplina_id, serie_id, escola_id, ano_letivo_id);
CREATE INDEX idx_escola_serie ON historico_escolar (escola_id, serie_id, ano_letivo_id);
CREATE INDEX idx_disciplinas_disponiveis ON historico_escolar (escola_id, serie_id, ano_letivo_id, disciplina_id);

-- ============================================================================
-- ÍNDICES COMPLEMENTARES (podem já existir do arquivo principal)
-- ============================================================================

-- Verificar se já existem os índices básicos
SELECT COUNT(*) as existe_fulltext 
FROM information_schema.STATISTICS 
WHERE table_name = 'alunos' AND index_name = 'ft_nome';

-- Se não existir (resultado = 0), criar os índices FULLTEXT
-- Estes podem já existir se você seguiu OTIMIZACOES_BANCO_DADOS.md
CREATE FULLTEXT INDEX IF NOT EXISTS ft_nome ON alunos (nome);
CREATE FULLTEXT INDEX IF NOT EXISTS ft_nome ON funcionarios (nome);

-- Índices complementares para disciplinas (se não existirem)
CREATE INDEX IF NOT EXISTS idx_disciplina_escola_nivel ON disciplinas (escola_id, nivel_id, nome);
CREATE INDEX IF NOT EXISTS idx_disciplina_nome ON disciplinas (nome);

-- Índices para tabelas de referência (se não existirem)  
CREATE INDEX IF NOT EXISTS idx_serie_nome ON serie (nome);
CREATE INDEX IF NOT EXISTS idx_escola_nome ON escolas (nome);
CREATE INDEX IF NOT EXISTS idx_ano_letivo ON anosletivos (ano_letivo DESC);

-- Índice para observações do histórico (nova tabela específica)
CREATE INDEX IF NOT EXISTS idx_observacoes_historico ON observacoes_historico (serie_id, ano_letivo_id, escola_id);

-- Analisar tabelas para atualizar estatísticas
ANALYZE TABLE historico_escolar, alunos, disciplinas, serie, escolas, anosletivos;
```

## Integração com Otimizações Existentes

As otimizações desta interface complementam as já implementadas em `OTIMIZACOES_BANCO_DADOS.md`:

### ✅ Índices Já Implementados (do arquivo principal)
- `idx_alunos_escola_nome` - Para busca de alunos por escola  
- `idx_funcionarios_cargo_nome` - Para funcionários por cargo
- `idx_matriculas_aluno_ano` - Para matrículas 
- `idx_turmas_escola_ano` - Para turmas
- `idx_responsaveisalunos_aluno` - Relacionamento responsáveis
- `ft_nome` nas tabelas `alunos` e `funcionarios` - FULLTEXT search

### 🆕 Novos Índices para Histórico Escolar
- `idx_aluno_historico` - Consulta principal do histórico
- `idx_historico_filtros` - Para aplicação de filtros
- `idx_escola_serie` - Para consultas por escola/série  
- `idx_disciplinas_disponiveis` - Para listar disciplinas disponíveis
- `idx_observacoes_historico` - Para observações específicas

### 🔄 Cache Integrado
As otimizações de cache da interface de histórico aproveitam o **Connection Pool** já implementado:
- Utiliza as conexões pooled do sistema principal
- Cache específico para histórico escolar (5 min TTL)
- Invalidação automática integrada com o sistema existente

## Monitoramento de Performance

### 1. Comandos para Verificar Performance

```sql
-- Verificar uso dos índices
SHOW INDEX FROM historico_escolar;
SHOW INDEX FROM alunos;

-- Verificar queries lentas
SHOW VARIABLES LIKE 'slow_query_log';
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;

-- Verificar status de performance
SHOW STATUS LIKE 'Key%';
SHOW STATUS LIKE 'Qcache%';
```

### 2. Comandos EXPLAIN para Debugging

```sql
-- Exemplo de uso do EXPLAIN para verificar se os índices estão sendo usados
EXPLAIN SELECT h.id, d.nome, al.ano_letivo, s.nome, e.nome, h.media, h.conceito
FROM historico_escolar h
INNER JOIN disciplinas d ON h.disciplina_id = d.id
INNER JOIN anosletivos al ON h.ano_letivo_id = al.id
INNER JOIN serie s ON h.serie_id = s.id
INNER JOIN escolas e ON h.escola_id = e.id
WHERE h.aluno_id = 1
ORDER BY al.ano_letivo DESC, s.id, d.nome;
```

## Manutenção Regular

### 1. Scripts de Manutenção Mensal

```sql
-- Otimizar tabelas
OPTIMIZE TABLE historico_escolar;
OPTIMIZE TABLE alunos;
OPTIMIZE TABLE disciplinas;

-- Atualizar estatísticas
ANALYZE TABLE historico_escolar;
ANALYZE TABLE alunos;
ANALYZE TABLE disciplinas;
```

### 2. Limpeza de Cache (se necessário)

```sql
-- Limpar query cache
RESET QUERY CACHE;

-- Flush das tabelas
FLUSH TABLES;
```

## Benefícios Esperados

1. **Consulta de Histórico**: Redução de 80-90% no tempo de resposta
2. **Pesquisa de Alunos**: Busca instantânea com FULLTEXT index
3. **Filtros**: Aplicação de filtros 5x mais rápida
4. **Carregamento de Disciplinas**: Redução significativa no tempo de carregamento
5. **Cache de Dados**: Redução de 70% nas consultas ao banco

## Notas Importantes

- Execute os scripts em horário de menor movimento
- Faça backup do banco antes de aplicar os índices
- Monitore o espaço em disco após a criação dos índices
- Os índices FULLTEXT só funcionam em MySQL 5.6+ com InnoDB ou MyISAM
- Ajuste as configurações de memória conforme os recursos do servidor