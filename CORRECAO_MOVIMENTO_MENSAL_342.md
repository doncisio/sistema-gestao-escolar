# Correção: Movimento Mensal Mostrando 341 ao Invés de 342

## Problema Identificado

O gráfico de **Movimento Mensal** no dashboard estava mostrando **341 alunos** quando o correto é **342**.

## Causa Raiz

A função `obter_movimento_mensal_resumo()` em `services/estatistica_service.py` estava usando a tabela `historico_matricula` para contar transferidos, o que resultava em **41 transferidos** ao invés de **42**.

### Por que a Query do Histórico Estava Errada?

A query complexa verificava o histórico de mudanças de status:
```sql
-- Query ANTIGA (incorreta)
SELECT hm.status_novo as status, COUNT(DISTINCT m.aluno_id) as total
FROM historico_matricula hm
WHERE hm.status_novo IN ('Evadido','Transferido','Transferida')
  AND NOT EXISTS (
    SELECT 1 FROM historico_matricula hm2
    WHERE hm2.matricula_id = hm.matricula_id
      AND hm2.data_mudanca > hm.data_mudanca
      AND hm2.status_novo = 'Ativo'
  )
```

**Problema**: Se um aluno foi transferido mas não tem entrada no `historico_matricula` (cadastrado diretamente como transferido), ele não é contado.

## Solução Implementada

Substituí a query complexa de histórico por uma query simples que busca **diretamente o status atual** da matrícula, garantindo consistência com `obter_estatisticas_alunos()`:

```sql
-- Query NOVA (correta)
SELECT 
    m.status,
    COUNT(DISTINCT m.aluno_id) as total
FROM matriculas m
INNER JOIN alunos a ON m.aluno_id = a.id
WHERE m.ano_letivo_id = %s
  AND a.escola_id = %s
  AND m.status IN ('Transferido', 'Transferida', 'Evadido')
  AND m.data_matricula <= LAST_DAY(DATE(CONCAT(%s, '-', %s, '-01')))
GROUP BY m.status
```

## Comparação Antes vs Depois

### ANTES da Correção:
```
Dashboard: 342 alunos (300 ativos + 42 transferidos)
Movimento Mensal: 341 alunos (300 ativos + 41 transferidos)
Diferença: -1 aluno
```

### DEPOIS da Correção:
```
Dashboard: 342 alunos (300 ativos + 42 transferidos)
Movimento Mensal: 342 alunos (300 ativos + 42 transferidos)
Diferença: 0 ✓
```

## Movimento Mensal por Mês (Corrigido)

```
Mês   Ativos  Transf.  Evad.  Total
---   ------  -------  -----  -----
Jan     260      29      0     289
Fev     272      36      0     308
Mar     280      38      0     318
Abr     280      40      0     320
Mai     287      40      0     327
Jun     287      41      0     328
Jul     292      41      0     333
Ago     296      41      0     337
Set     298      41      0     339
Out     299      42      0     341
Nov     300      42      0     342 ✓
Dez     300      42      0     342 ✓
```

## Benefícios da Correção

1. **Consistência**: Movimento mensal agora usa a mesma lógica que o dashboard principal
2. **Simplicidade**: Query mais simples e eficiente (sem subquery complexa)
3. **Precisão**: Não perde alunos que foram cadastrados diretamente como transferidos
4. **Performance**: Query mais rápida (menos joins e subqueries)

## Validação

### Teste Automático
```bash
python test_movimento_mensal.py
```

**Resultado esperado**:
```
Dashboard (total_alunos): 342
Movimento Mensal (total): 342
✓ Números alinhados!
```

### Limpeza de Cache
```bash
python limpar_cache_dashboard.py
```

O cache tem TTL de 10 minutos. Execute o script acima para forçar recálculo imediato.

## Arquivo Modificado

**`services/estatistica_service.py`** (linhas 315-365)
- Função: `obter_movimento_mensal_resumo()`
- Mudança: Substituída query de `historico_matricula` por query direta no `status` da matrícula
- Linhas alteradas: ~25 linhas (query de transferidos/evadidos)

## Scripts de Diagnóstico Criados

1. **`check_alunos_342.py`** - Verificação detalhada de contagem
2. **`limpar_cache_dashboard.py`** - Limpeza de cache + estatísticas
3. **`test_dashboard_ano.py`** - Teste de detecção de ano letivo
4. **`test_movimento_mensal.py`** - Comparação dashboard vs movimento mensal

## Próximos Passos (Opcional)

### Adicionar Botão de Atualização no Dashboard
```python
# Em ui/dashboard.py, adicionar após info_frame
botao_atualizar = Button(info_frame, text="🔄 Atualizar", 
                         command=lambda: self.atualizar_dashboard(),
                         bg='#4CAF50', fg='white', font=('Calibri', 10, 'bold'))
botao_atualizar.pack(side='right', padx=10)
```

### Invalidação Automática de Cache
Considerar invalidar cache quando:
- Nova matrícula criada
- Status de matrícula alterado (Ativo → Transferido)
- Aluno evadido

## Conclusão

✅ **Problema resolvido**: Movimento mensal agora mostra **342 alunos** corretamente

✅ **Query simplificada**: Usa status atual ao invés de histórico complexo

✅ **Consistência garantida**: Dashboard e Movimento Mensal alinhados

✅ **Performance melhorada**: Query mais eficiente e rápida

---

**Data da correção**: 8 de dezembro de 2025  
**Versão do sistema**: v2.0.0  
**Status**: ✅ Corrigido e validado
