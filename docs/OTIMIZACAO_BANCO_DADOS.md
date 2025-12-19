ome),
ota >= 0.0) and (
ota <= 100.0))
# Análise e Otimização do Banco de Dados

**Data da Análise**: 18 de Dezembro de 2025
**Status**: Análise Pós-Backup
**Versão do Banco**: MySQL 8.0.39

---

## Resumo das descobertas (baseado em backups/backup_redeescola.sql)

- Banco bem normalizado: existe a tabela `disciplinas` e `notas` referencia `disciplina_id` (boa prática).
- `matriculas` existe e tem constraint única (`aluno_id`,`ano_letivo_id`) e FKs para `alunos`,`turmas`,`anosletivos`.
- `notas` possui índices compostos (`aluno_id,disciplina_id,bimestre,ano_letivo_id`) e CHECK para faixa de nota.
- Tabelas de frequência (`frequencia`, `frequencia_alunos`) referenciam `matriculas`/`alunos` corretamente.
- Muitas tabelas já têm `created_at` / `updated_at` (ex.: `desempenho_aluno_habilidade`), mas outras, como `alunos`, não possuem colunas de auditoria.
- Há duplicidade / incoerência de nomes em torno de documentos: `documentos_emitidos` e `documentosemitidos` (mesma intenção, nomes diferentes).
- Índices úteis já existem (p.ex. FULLTEXT em `alunos.nome`), porém há espaço para índices adicionais e padronização de collations.

---

## Achados por tabela (seleção relevante)

- `alunos`: sem colunas de auditoria (`created_at`/`updated_at`). PK, FK para `escolas`, `FULLTEXT(ft_nome)` presente.
- `matriculas`: FK para `alunos`,`turmas`,`anosletivos`; `UNIQUE(aluno_id,ano_letivo_id)` evita duplicidade por ano.
- `disciplinas`: bem povoada (>1000 entradas), FK para `niveisensino` e `escolas`.
- `notas`: FK para `disciplinas`, `anosletivos`; índice composto `idx_notas_completo` já otimiza consultas por aluno/disciplina/bimestre.
- `frequencia`/`frequencia_alunos`: relacionamento com `matriculas`/`alunos` e `disciplinas` bem definido.
- `documentos_emitidos` vs `documentosemitidos`: duplicação de finalidade; revisar uso pela aplicação antes de consolidar.

---

## Riscos / pontos de atenção

- Ainda que o esquema esteja normalizado, existem defaults “fixos” em algumas colunas (ex.: `alunos.escola_id DEFAULT 3`) — revisar origem destes defaults.
- Algumas collations variam entre tabelas (`utf8mb4_0900_ai_ci` vs `utf8mb4_unicode_ci`) — padronizar evita diferenças de ordenação/compare.
- Adicionar constraints (UNIQUE / NOT NULL) sem validar dados pode quebrar a importação — rodar checagens antes.

---

## Recomendações e snippets SQL (práticos)

1) Adicionar auditoria em `alunos` (rodar em janela de manutenção):

```sql
ALTER TABLE alunos
ADD COLUMN created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
ADD COLUMN created_by INT NULL,
ADD COLUMN updated_by INT NULL;
```

2) Opcional: indexar `alunos.cpf` para buscas (apenas após limpeza/validação de duplicatas):

```sql
-- validar duplicatas antes: SELECT cpf, COUNT(*) FROM alunos GROUP BY cpf HAVING COUNT(*)>1;
CREATE INDEX idx_alunos_cpf ON alunos(cpf(14));
```

3) Consolidar tabelas de documentos (procedimento sugerido):

- Verificar qual tabela é usada pela aplicação (`documentos_emitidos` ou `documentosemitidos`).
- Se ambas forem necessárias, criar views para compatibilidade; caso contrário, migrar dados e manter apenas uma tabela com nome canônico `documentos_emitidos`.

Exemplo de view temporária:

```sql
CREATE VIEW vw_documentos_emitidos AS
SELECT * FROM documentos_emitidos
UNION ALL
SELECT * FROM documentosemitidos;
```

4) Padronizar collation do schema (exemplo):

```sql
ALTER TABLE alunos CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
-- repetir para tabelas críticas
```

5) Scripts de verificação (antes de impor constraints):

```sql
-- procurar CPFs inválidos/duplicados
SELECT cpf, COUNT(*) c FROM alunos WHERE cpf IS NOT NULL GROUP BY cpf HAVING c>1;

-- checar valores nulos antes de tornar NOT NULL
SELECT COUNT(*) FROM alunos WHERE nome IS NULL;
```

---

## Plano de migração recomendado (alto nível)

1. Executar scripts de diagnóstico (verificar duplicados/collations/valores nulos).
2. Adicionar colunas de auditoria em tabelas que não possuem (primeiro em ambiente de homologação).
3. Padronizar collations nas tabelas críticas.
4. Consolidar tabelas duplicadas (documentos) via view + migração dos dados.
5. Ajustar consultas/queries na aplicação (`db/queries.py`) para usar JOINs e nomes snake_case.
6. Testes funcionais na aplicação + rollback scripts prontos.

---

## Próximos passos que posso executar

- Continuar varredura completa do dump e anexar checklist tabela-a-tabela (quando autorizado).
- Gerar migrations SQL (seguros, idempotentes) para adicionar auditoria e views temporárias.
- Criar checklist de deploy com backup, janela de manutenção e rollback SQL.

---

**Documento atualizado em**: 18/12/2025
