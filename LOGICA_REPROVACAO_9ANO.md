# 📊 Lógica de Reprovação - 9º Ano

**Data:** 11 de novembro de 2025  
**Sistema:** Transição de Ano Letivo  

---

## 🎯 Objetivo

Durante a transição de ano letivo, o sistema identifica automaticamente alunos do **9º ano** que foram **reprovados** (não atingiram a média mínima) e os **rematricula no 9º ano** para o próximo ano letivo.

Alunos **aprovados** do 9º ano NÃO são rematriculados, pois **concluíram o ensino fundamental**.

---

## 📐 Cálculo da Média Final

### Fórmula
```
Média Final = (Nota 1º Bim + Nota 2º Bim + Nota 3º Bim + Nota 4º Bim) / 4
```

### Critério de Aprovação
- ✅ **APROVADO**: Média Final ≥ 60
- ❌ **REPROVADO**: Média Final < 60
- ❌ **REPROVADO**: Sem notas cadastradas (NULL)

---

## 🔍 Identificação dos Alunos

### 1. **Buscar Turmas do 9º Ano**
```sql
SELECT t.id
FROM turmas t
JOIN serie s ON t.serie_id = s.id
WHERE s.nome LIKE '9%'
AND t.escola_id = 60
```

### 2. **Calcular Média por Aluno**
```sql
SELECT 
    a.id as aluno_id,
    a.nome,
    m.turma_id,
    -- Média do 1º bimestre
    COALESCE(AVG(CASE WHEN n.bimestre = '1º bimestre' THEN n.nota END), 0) as bim1,
    -- Média do 2º bimestre
    COALESCE(AVG(CASE WHEN n.bimestre = '2º bimestre' THEN n.nota END), 0) as bim2,
    -- Média do 3º bimestre
    COALESCE(AVG(CASE WHEN n.bimestre = '3º bimestre' THEN n.nota END), 0) as bim3,
    -- Média do 4º bimestre
    COALESCE(AVG(CASE WHEN n.bimestre = '4º bimestre' THEN n.nota END), 0) as bim4,
    -- Média Final
    (
        COALESCE(AVG(CASE WHEN n.bimestre = '1º bimestre' THEN n.nota END), 0) +
        COALESCE(AVG(CASE WHEN n.bimestre = '2º bimestre' THEN n.nota END), 0) +
        COALESCE(AVG(CASE WHEN n.bimestre = '3º bimestre' THEN n.nota END), 0) +
        COALESCE(AVG(CASE WHEN n.bimestre = '4º bimestre' THEN n.nota END), 0)
    ) / 4 as media_final
FROM Alunos a
JOIN Matriculas m ON a.id = m.aluno_id
LEFT JOIN notas n ON a.id = n.aluno_id AND n.ano_letivo_id = [ANO_ATUAL_ID]
WHERE m.ano_letivo_id = [ANO_ATUAL_ID]
AND m.status = 'Ativo'
AND a.escola_id = 60
AND m.turma_id IN ([IDS_TURMAS_9ANO])
GROUP BY a.id, a.nome, m.turma_id
```

### 3. **Filtrar Reprovados**
```sql
HAVING media_final < 60 OR media_final IS NULL
```

---

## 📋 Exemplos Práticos

### Exemplo 1: Aluno Aprovado
**Aluno:** João Silva  
**Turma:** 9º Ano A

| Bimestre | Nota |
|----------|------|
| 1º       | 65   |
| 2º       | 70   |
| 3º       | 68   |
| 4º       | 72   |

**Cálculo:**
```
Média Final = (65 + 70 + 68 + 72) / 4 = 275 / 4 = 68.75
```

**Resultado:** ✅ **APROVADO** (68.75 ≥ 60)  
**Ação:** **NÃO será rematriculado** (concluiu o ensino fundamental)

---

### Exemplo 2: Aluno Reprovado por Média Baixa
**Aluno:** Maria Santos  
**Turma:** 9º Ano B

| Bimestre | Nota |
|----------|------|
| 1º       | 45   |
| 2º       | 52   |
| 3º       | 48   |
| 4º       | 50   |

**Cálculo:**
```
Média Final = (45 + 52 + 48 + 50) / 4 = 195 / 4 = 48.75
```

**Resultado:** ❌ **REPROVADO** (48.75 < 60)  
**Ação:** **SERÁ rematriculado no 9º Ano** no próximo ano

---

### Exemplo 3: Aluno Sem Notas
**Aluno:** Pedro Costa  
**Turma:** 9º Ano A

| Bimestre | Nota |
|----------|------|
| 1º       | -    |
| 2º       | -    |
| 3º       | -    |
| 4º       | -    |

**Cálculo:**
```
Média Final = (0 + 0 + 0 + 0) / 4 = 0 / 4 = 0
```

**Resultado:** ❌ **REPROVADO** (0 < 60 ou NULL)  
**Ação:** **SERÁ rematriculado no 9º Ano** no próximo ano

---

### Exemplo 4: Aluno com Notas Parciais
**Aluno:** Ana Oliveira  
**Turma:** 9º Ano B

| Bimestre | Nota |
|----------|------|
| 1º       | 65   |
| 2º       | 60   |
| 3º       | -    |
| 4º       | -    |

**Cálculo:**
```
Média Final = (65 + 60 + 0 + 0) / 4 = 125 / 4 = 31.25
```

**Resultado:** ❌ **REPROVADO** (31.25 < 60)  
**Ação:** **SERÁ rematriculado no 9º Ano** no próximo ano

---

## 🔄 Processo de Transição

### Para Alunos do 1º ao 8º Ano
```
┌─────────────────────────────────────┐
│ Aluno: Carlos (7º Ano A)            │
│ Status: Ativo                       │
├─────────────────────────────────────┤
│ Ano 2025: Matrícula → Concluído    │
│ Ano 2026: Nova matrícula → Ativo   │
│ Turma: 7º Ano A (mantém)            │
└─────────────────────────────────────┘
```

### Para Alunos do 9º Ano APROVADOS
```
┌─────────────────────────────────────┐
│ Aluno: João (9º Ano A)              │
│ Média Final: 68.75                  │
│ Status: Ativo → Aprovado            │
├─────────────────────────────────────┤
│ Ano 2025: Matrícula → Concluído    │
│ Ano 2026: SEM MATRÍCULA             │
│ Motivo: Concluiu ensino fundamental │
└─────────────────────────────────────┘
```

### Para Alunos do 9º Ano REPROVADOS
```
┌─────────────────────────────────────┐
│ Aluno: Maria (9º Ano B)             │
│ Média Final: 48.75                  │
│ Status: Ativo → Reprovado           │
├─────────────────────────────────────┤
│ Ano 2025: Matrícula → Concluído    │
│ Ano 2026: Nova matrícula → Ativo   │
│ Turma: 9º Ano B (repete)            │
└─────────────────────────────────────┘
```

---

## ⚠️ Considerações Importantes

### 1. **Notas Não Cadastradas**
- Alunos sem notas são considerados **REPROVADOS**
- É importante lançar todas as notas antes da transição
- **Recomendação:** Verificar notas pendentes no menu "Gerenciamento de Notas → Relatório de Pendências"

### 2. **Média por Disciplina**
- O sistema calcula a média de **todas as disciplinas** em cada bimestre
- Não considera aprovação/reprovação por disciplina individual
- Usa a média geral dos 4 bimestres

### 3. **Alunos Transferidos/Cancelados**
- **NÃO são avaliados** para aprovação/reprovação
- São automaticamente excluídos da transição
- Independente da média final

### 4. **Recuperação**
- O sistema **NÃO considera** notas de recuperação separadamente
- As notas de recuperação devem **substituir** as notas originais no banco
- Antes da transição, certifique-se de atualizar as notas finais

---

## 📊 Relatório de Alunos do 9º Ano

### Consulta SQL para Verificar Status
```sql
SELECT 
    a.nome as aluno,
    CONCAT(s.nome, ' ', t.nome) as turma,
    ROUND((
        COALESCE(AVG(CASE WHEN n.bimestre = '1º bimestre' THEN n.nota END), 0) +
        COALESCE(AVG(CASE WHEN n.bimestre = '2º bimestre' THEN n.nota END), 0) +
        COALESCE(AVG(CASE WHEN n.bimestre = '3º bimestre' THEN n.nota END), 0) +
        COALESCE(AVG(CASE WHEN n.bimestre = '4º bimestre' THEN n.nota END), 0)
    ) / 4, 2) as media_final,
    CASE 
        WHEN (
            COALESCE(AVG(CASE WHEN n.bimestre = '1º bimestre' THEN n.nota END), 0) +
            COALESCE(AVG(CASE WHEN n.bimestre = '2º bimestre' THEN n.nota END), 0) +
            COALESCE(AVG(CASE WHEN n.bimestre = '3º bimestre' THEN n.nota END), 0) +
            COALESCE(AVG(CASE WHEN n.bimestre = '4º bimestre' THEN n.nota END), 0)
        ) / 4 >= 60 THEN 'APROVADO'
        ELSE 'REPROVADO'
    END as situacao
FROM Alunos a
JOIN Matriculas m ON a.id = m.aluno_id
JOIN turmas t ON m.turma_id = t.id
JOIN serie s ON t.serie_id = s.id
LEFT JOIN notas n ON a.id = n.aluno_id AND n.ano_letivo_id = m.ano_letivo_id
WHERE s.nome LIKE '9%'
AND m.ano_letivo_id = [ANO_ATUAL]
AND m.status = 'Ativo'
AND a.escola_id = 60
GROUP BY a.id, a.nome, s.nome, t.nome
ORDER BY situacao, a.nome;
```

---

## ✅ Checklist Pré-Transição

Antes de executar a transição, verifique:

- [ ] **Todas as notas do 4º bimestre foram lançadas**
- [ ] **Notas de recuperação foram atualizadas no sistema**
- [ ] **Status dos alunos transferidos estão corretos**
- [ ] **Alunos evadidos foram marcados como "Evadido"**
- [ ] **Backup do banco de dados foi realizado**
- [ ] **Relatório de Pendências foi verificado**
- [ ] **Coordenação pedagógica aprovou as médias finais**

---

## 🆘 Problemas Comuns

### Problema: "Aluno aprovado foi rematriculado"
**Causa:** Notas não foram cadastradas corretamente  
**Solução:** 
1. Verifique as notas do aluno no banco de dados
2. Se necessário, restaure o backup e corrija as notas
3. Execute a transição novamente

### Problema: "Aluno reprovado não foi rematriculado"
**Causa:** Status da matrícula diferente de "Ativo"  
**Solução:**
1. Verifique o status atual da matrícula
2. Se necessário, corrija para "Ativo"
3. Restaure o backup e execute novamente

### Problema: "Média calculada está incorreta"
**Causa:** Notas de várias disciplinas com valores diferentes  
**Solução:**
1. O sistema calcula a média de todas as disciplinas
2. Verifique se todas as notas foram lançadas
3. Use a consulta SQL acima para conferir

---

## 📞 Suporte

**Desenvolvedor:** Tarcisio Sousa de Almeida  
**Cargo:** Técnico em Administração Escolar  

Em caso de dúvidas sobre a lógica de aprovação/reprovação, consulte a coordenação pedagógica da escola.

---

**Última atualização:** 11 de novembro de 2025
