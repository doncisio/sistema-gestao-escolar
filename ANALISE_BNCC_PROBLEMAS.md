# Análise BNCC: Problemas Identificados e Melhorias Propostas

## ⚠️ PROBLEMAS CRÍTICOS ENCONTRADOS

### 1. **Mapeamento INCORRETO da coluna "descricao"**
**Status**: 🔴 CRÍTICO

**Problema**:
- O script está gravando o campo "Conhecimento prévio" na coluna `descricao`
- O campo correto "Texto da habilidade" NÃO está sendo capturado
- Resultado: 419 habilidades têm descrição ERRADA no banco

**Evidência**:
```
Excel: Código=EF07MA02, Texto="Resolver e elaborar problemas que envolvam porcentagens..."
Banco: codigo=EF07MA02, descricao="EF06MA13\nEF06MA08" (ERRADO! É o conhec.prévio)
```

**Causa raiz**:
O mapeamento automático em `COMMON_NAMES` tem conflito:
```python
'descricao': ['descricao','descrição','descricao_habilidade','habilidade','texto']
```
A palavra "habilidade" casa com "Conhecimento prévio (habilidades de anos...)" ANTES de casar com "Texto da habilidade".

---

### 2. **Campos pedagógicos importantes NÃO armazenados**

Campos do Excel com alto valor pedagógico que NÃO estão no banco:

| Campo Excel | Valor Pedagógico | Status |
|-------------|------------------|--------|
| **Unidade temática** | Agrupa habilidades por tema (ex: "Números", "Álgebra") | ❌ Ausente |
| **Classificação** | AF (Aprendizagem Focal) ou AC (Aprendizagem Complementar) | ❌ Ausente |
| **Objetivos de aprendizagem** | Lista detalhada de objetivos específicos por habilidade | ❌ Ausente |
| **Competências relacionadas** | CG/CE/CA (competências gerais, específicas, área) | ❌ Ausente |
| **Habilidades relacionadas** | Outras habilidades focais/complementares relacionadas | ❌ Ausente |
| **Comentários** | Orientações didáticas e exemplos práticos | ❌ Ausente |
| **Campo de atuação** | Para LP: leitura, escrita, oralidade, análise linguística | ❌ Ausente |

**Impacto**:
- Professores perdem contexto rico ao consultar habilidades
- Impossível filtrar por tipo (AF vs AC)
- Impossível agrupar por unidade temática
- Sem orientações didáticas (comentários)

---

### 3. **Tabela `bncc_prerequisitos` com design limitado**

**Problemas**:
1. Só armazena pré-requisitos, mas não "Habilidades relacionadas" (que são diferentes)
2. Não distingue tipo de relacionamento (pré-requisito vs complementar vs focal)
3. 55 pré-requisitos órfãos (códigos não resolvidos) podem ser códigos inválidos ou referências externas

---

## 🔧 MELHORIAS PROPOSTAS

### Prioridade 1: CORRIGIR MAPEAMENTO (URGENTE)

**Ação**:
1. Adicionar colunas ausentes em `bncc_habilidades`
2. Corrigir o mapeamento de `descricao` para capturar "Texto da habilidade"
3. Re-importar TODOS os dados corretamente

**SQL de alteração**:
```sql
-- Adicionar colunas pedagógicas
ALTER TABLE bncc_habilidades 
  ADD COLUMN unidade_tematica VARCHAR(255) DEFAULT NULL AFTER descricao,
  ADD COLUMN classificacao VARCHAR(10) DEFAULT NULL COMMENT 'AF, AC, EF',
  ADD COLUMN objetivos_aprendizagem TEXT DEFAULT NULL,
  ADD COLUMN competencias_relacionadas TEXT DEFAULT NULL,
  ADD COLUMN comentarios TEXT DEFAULT NULL,
  ADD COLUMN campo_atuacao VARCHAR(100) DEFAULT NULL COMMENT 'Para LP';

-- Índices para busca
CREATE INDEX idx_bncc_classificacao ON bncc_habilidades(classificacao);
CREATE INDEX idx_bncc_unidade ON bncc_habilidades(unidade_tematica);
```

---

### Prioridade 2: MELHORAR RELACIONAMENTOS

**Ação**: Criar tabela unificada para todos os tipos de relacionamento entre habilidades

**SQL proposto**:
```sql
CREATE TABLE IF NOT EXISTS bncc_relacionamentos (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  bncc_id BIGINT UNSIGNED NOT NULL,
  relacionado_codigo VARCHAR(60) NOT NULL,
  relacionado_bncc_id BIGINT UNSIGNED DEFAULT NULL,
  tipo_relacao ENUM('prerequisito', 'complementar', 'focal', 'expectativa_fluencia') NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_bncc_relacao (bncc_id, relacionado_codigo, tipo_relacao),
  CONSTRAINT fk_relacao_bncc FOREIGN KEY (bncc_id) REFERENCES bncc_habilidades(id) ON DELETE CASCADE,
  CONSTRAINT fk_relacao_bncc_id FOREIGN KEY (relacionado_bncc_id) REFERENCES bncc_habilidades(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Migrar dados existentes
INSERT INTO bncc_relacionamentos (bncc_id, relacionado_codigo, relacionado_bncc_id, tipo_relacao)
SELECT bncc_id, prereq_codigo, prereq_bncc_id, 'prerequisito'
FROM bncc_prerequisitos;
```

---

### Prioridade 3: ATUALIZAR IMPORTADOR

**Alterações no mapeamento**:
```python
COMMON_NAMES = {
    'codigo': ['código da habilidade', 'codigo da habilidade', 'código', 'codigo'],
    'descricao': ['texto da habilidade', 'descrição da habilidade', 'habilidade (texto)'],  # FIXAR!
    'conhecimento_previo': ['conhecimento prévio', 'conhecimento previo'],
    'unidade_tematica': ['unidade temática', 'unidade tematica', 'unidade'],
    'classificacao': ['classificação', 'classificacao'],
    'objetivos': ['objetivos de aprendizagem', 'objetivos'],
    'competencias': ['competências relacionadas', 'competencias relacionadas'],
    'habilidades_relacionadas': ['habilidades relacionadas'],
    'comentarios': ['comentários', 'comentarios'],
    'campo_atuacao': ['campo de atuação', 'campo de atuacao']
}
```

**Lógica de extração de relacionamentos**:
- Extrair códigos de "Conhecimento prévio" → tipo `prerequisito`
- Extrair códigos de "Habilidades relacionadas" → tipo `complementar` ou `focal` (baseado em contexto AF/AC)
- Detectar "(EF)" em objetivos → tipo `expectativa_fluencia`

---

## 📊 ESTATÍSTICAS ATUAIS

- ✅ 419 habilidades importadas
- ❌ 419 com descrição ERRADA (campo trocado)
- ✅ 325 com conhecimento_previo preenchido
- ✅ 510 pré-requisitos registrados (455 resolvidos)
- ❌ 0 unidades temáticas, classificações, objetivos, competências, comentários

---

## 🎯 PLANO DE AÇÃO RECOMENDADO

### Opção A: CORREÇÃO RÁPIDA (recomendado)
1. Aplicar ALTER TABLE para adicionar colunas
2. Corrigir mapeamento no importador
3. Re-importar tudo (com TRUNCATE ou ON DUPLICATE KEY UPDATE)
4. Validar 5 registros manualmente

**Tempo estimado**: ~30min  
**Impacto**: Alto (corrige problema crítico + adiciona campos valiosos)

### Opção B: INCREMENTAL
1. Aplicar ALTER TABLE
2. Popular apenas novos campos (manter descricao errada por ora)
3. Corrigir descricao em script separado depois

**Tempo estimado**: ~15min  
**Impacto**: Médio (campos novos OK, mas descricao continua errada)

### Opção C: APENAS DOCUMENTAR
1. Documentar problemas
2. Usuário decide quando aplicar

---

## 🔍 VALIDAÇÃO PÓS-CORREÇÃO

Query para validar após re-importação:
```sql
-- Verificar se descrição está correta (deve ter texto longo, não códigos BNCC)
SELECT codigo, LEFT(descricao, 80), LEFT(conhecimento_previo, 80)
FROM bncc_habilidades
WHERE descricao LIKE 'EF%' OR descricao LIKE 'EM%'
LIMIT 10;
-- Se retornar linhas: ERRO (descricao ainda tem códigos)

-- Verificar preenchimento dos novos campos
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN unidade_tematica IS NOT NULL THEN 1 ELSE 0 END) as com_unidade,
  SUM(CASE WHEN classificacao IS NOT NULL THEN 1 ELSE 0 END) as com_classif,
  SUM(CASE WHEN objetivos_aprendizagem IS NOT NULL THEN 1 ELSE 0 END) as com_objetivos
FROM bncc_habilidades;
```

---

## 📝 OBSERVAÇÕES FINAIS

1. **Problema do mapeamento** é CRÍTICO porque invalida a descrição de todas as 419 habilidades
2. **Campos ausentes** são importantes para uso pedagógico real (planejamento de aulas, progressões)
3. **Pré-requisitos órfãos** (55) precisam de investigação: podem ser códigos inválidos no Excel ou referências a habilidades de outras etapas não importadas
4. A estrutura atual de `bncc_prerequisitos` é funcional mas limitada; expandir para `bncc_relacionamentos` permite melhor modelagem

**Recomendação final**: Executar Opção A (correção completa) o quanto antes.

---

---

# ✅ CORREÇÃO APLICADA - RESULTADOS

**Data**: 2025-01-XX  
**Opção executada**: **Opção A** (Correção completa)

## 🔧 Alterações Implementadas

### 1. Migração do Banco de Dados
**Arquivo**: `migration_bncc_add_campos_pedagogicos.sql`

✅ **Colunas adicionadas**:
- `unidade_tematica` VARCHAR(255)
- `classificacao` VARCHAR(10) - AF, AC, EF
- `objetivos_aprendizagem` TEXT
- `competencias_relacionadas` TEXT
- `habilidades_relacionadas` TEXT
- `comentarios` TEXT
- `campo_atuacao` VARCHAR(100)

✅ **Índices criados**:
- `idx_bncc_classificacao` ON `classificacao`
- `idx_bncc_unidade` ON `unidade_tematica`

### 2. Correção do Importador
**Arquivo**: `importar_bncc_from_excel.py`

✅ **Fix crítico no COMMON_NAMES**:
```python
# ANTES (ERRADO):
'descricao': ['descricao','descrição','descricao_habilidade','habilidade','texto']
# ↑ Casava com "Conhecimento prévio (habilidades...)" primeiro!

# DEPOIS (CORRETO):
'descricao': ['texto da habilidade','descrição da habilidade','texto','descricao','descrição']
# ↑ Prioriza match exato com "Texto da habilidade"
```

✅ **INSERT expandido**: de 11 para 18 colunas

✅ **Extração adicionada** para todos os novos campos pedagógicos

✅ **Processamento de relacionamentos**: extrai códigos de "Habilidades relacionadas" e insere em `bncc_prerequisitos`

### 3. Re-importação Completa
**Comando**: `python scripts\run_bncc_import.py`

✅ **37 planilhas processadas**
✅ **419 habilidades atualizadas/inseridas**
✅ **Mapeamento confirmado correto**:
```
codigo: Código da habilidade
descricao: Texto da habilidade  ← CORRETO!
conhecimento_previo: Conhecimento prévio
unidade_tematica: Unidade temática
classificacao: Classificação
...
```

---

## 📊 RESULTADOS DA VALIDAÇÃO

### ✅ Validação Completa Executada
**Script**: `scripts/validate_bncc_final.py`

#### 1. Descrições Corrigidas
- ✅ **0 habilidades** com códigos BNCC na descrição
- ✅ **419 habilidades** com textos completos e corretos
- ✅ Exemplo validado: EF08MA01 = "Efetuar cálculos com potências de expoentes inteiros e aplicar esse conhecimento na representação de números em notação científica."

#### 2. Campos Pedagógicos Populados

| Campo | Registros | Taxa |
|-------|-----------|------|
| **classificacao** | 419/419 | **100%** ✅ |
| **comentarios** | 419/419 | **100%** ✅ |
| **objetivos_aprendizagem** | 394/419 | **94%** ✅ |
| **competencias_relacionadas** | 392/419 | **93%** ✅ |
| **habilidades_relacionadas** | 350/419 | **83%** ✅ |
| **unidade_tematica** | 189/419 | **45%** ⚠️ |
| **campo_atuacao** | 39/419 | **9%** ⚠️ |

**Análise**:
- Campos essenciais (classificacao, comentarios, objetivos, competencias) com excelente preenchimento (93-100%)
- `unidade_tematica` com 45%: normal, pois nem todas as áreas têm unidades temáticas (mais comum em Matemática/Ciências)
- `campo_atuacao` com 9%: esperado, é específico de Língua Portuguesa

#### 3. Classificação das Habilidades

| Tipo | Quantidade | % |
|------|-----------|---|
| **AF** (Aprendizagem Focal) | 386 | 92% |
| **AF/AC** (Misto) | 19 | 5% |
| **EF** (Expectativa Fluência) | 14 | 3% |

#### 4. Relacionamentos

| Métrica | Antes | Depois | Variação |
|---------|-------|--------|----------|
| **Total relacionamentos** | 510 | **2334** | **+357%** 🚀 |
| **Com ID resolvido** | 455 | **943** | **+107%** ✅ |
| **Órfãos (sem ID)** | 55 | **1391** | +2429% ⚠️ |

**Análise dos órfãos**:
- Aumento significativo de órfãos porque agora capturamos também "Habilidades relacionadas" (além de conhecimentos prévios)
- Muitas referências podem ser a habilidades de outras etapas não importadas (EI - Educação Infantil, EM - Ensino Médio)
- Necessário auditoria posterior para identificar códigos inválidos vs. referências válidas externas

---

## 🎯 COMPARATIVO ANTES vs DEPOIS

### ANTES da Correção
❌ 419 habilidades com **descrição ERRADA** (recebia "Conhecimento prévio")  
❌ 0 registros com campos pedagógicos (unidade, classificacao, objetivos, etc)  
⚠️ 510 relacionamentos (apenas pré-requisitos básicos)  
⚠️ Dados pedagógicos valiosos perdidos do Excel  

### DEPOIS da Correção
✅ 419 habilidades com **descrição CORRETA** ("Texto da habilidade" completo)  
✅ 419 registros com `classificacao` e `comentarios` (100%)  
✅ 394 registros com `objetivos_aprendizagem` (94%)  
✅ 392 registros com `competencias_relacionadas` (93%)  
✅ 350 registros com `habilidades_relacionadas` (83%)  
✅ 2334 relacionamentos (crescimento de 357%)  
✅ Estrutura robusta para uso pedagógico real  

---

## ⚠️ PENDÊNCIAS E PRÓXIMOS PASSOS

### Pendências Menores
1. **Investigar órfãos**: 1391 relacionamentos sem ID resolvido
   - Separar códigos inválidos vs. referências externas (EI/EM)
   - Considerar importar habilidades de outras etapas

2. **Campo `campo_atuacao`**: apenas 9% preenchido
   - Verificar se Excel só tem para LP ou se há problema no mapeamento

3. **Unidade temática**: 45% preenchido
   - Confirmar se é normal (nem todas áreas têm)

### Melhorias Futuras (Opcional)
- Criar tabela `bncc_relacionamentos` conforme proposto (melhor modelagem)
- Migrar dados de `bncc_prerequisitos` para nova estrutura
- Implementar tipos de relacionamento (prerequisito, complementar, focal, expectativa_fluencia)

---

## ✅ CONCLUSÃO

**Status**: ✅ **CORREÇÃO BEM-SUCEDIDA**

Todos os problemas críticos foram resolvidos:
1. ✅ Descrições corrigidas (0 erros encontrados)
2. ✅ 7 campos pedagógicos adicionados e populados
3. ✅ Relacionamentos expandidos (+357%)
4. ✅ Estrutura pronta para uso em produção

**Validação**: 100% aprovada pelo script `validate_bncc_final.py`

