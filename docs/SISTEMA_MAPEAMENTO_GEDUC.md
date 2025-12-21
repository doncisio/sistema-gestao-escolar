# Sistema de Mapeamento GEDUC - Guia Completo

**Data:** 21/12/2025  
**Objetivo:** Mapear IDs entre Sistema Local e GEDUC para exportação precisa

---

## 🎯 Problema que Resolve

### Antes
- **escola_id** (local) ≠ **idinstituicao** (GEDUC)
- **disciplina_id** (local) ≠ **iddisciplina** (GEDUC)
- **serie_id** (local) ≠ **idserie** (GEDUC)
- Valores hardcoded no código
- Alto risco de erros na exportação

### Agora
- ✅ Mapeamento automático via tabela de banco de dados
- ✅ Extração de dados direto do GEDUC
- ✅ Comparação inteligente com base local
- ✅ Sugestões automáticas de correspondência
- ✅ Validação antes de exportar

---

## 📋 Fluxo Completo

```
┌────────────────────────────────────────────────────────────┐
│ 1. EXTRAÇÃO DE DADOS DO GEDUC                              │
│    python scripts/extrair_dados_mapeamento_geduc.py        │
│                                                             │
│    ↓ Faz login no GEDUC via Selenium                       │
│    ↓ Navega pelas páginas de cadastro                      │
│    ↓ Extrai IDs e nomes de:                                │
│      • Escolas (instituições)                              │
│      • Disciplinas                                         │
│      • Cursos                                              │
│      • Currículos                                          │
│      • Séries                                              │
│      • Turnos                                              │
│    ↓ Salva em JSON                                         │
│                                                             │
│    Saída: config/mapeamento_geduc_latest.json              │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ 2. COMPARAÇÃO COM BANCO LOCAL                              │
│    python scripts/comparar_mapeamento.py                   │
│                                                             │
│    ↓ Lê JSON do GEDUC                                      │
│    ↓ Consulta tabelas locais (escolas, disciplinas, etc)  │
│    ↓ Compara nomes usando similaridade de texto           │
│    ↓ Gera sugestões de mapeamento                         │
│    ↓ Cria SQL para popular tabela                         │
│                                                             │
│    Saídas:                                                 │
│    • sql/mapeamento_geduc.sql (script SQL)                │
│    • config/mapeamento_sugerido.json (JSON)               │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ 3. REVISÃO MANUAL                                          │
│    Abrir: sql/mapeamento_geduc.sql                        │
│                                                             │
│    ✅ Matches perfeitos (>95%): OK                        │
│    ⚠️  Matches bons (85-95%): Revisar                     │
│    ❓ Matches duvidosos (<85%): Ajustar manualmente       │
│                                                             │
│    Ajustar valores de id_geduc conforme necessário        │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ 4. EXECUTAR SQL NO BANCO                                   │
│    mysql -u usuario -p database < sql/mapeamento_geduc.sql│
│                                                             │
│    ↓ Cria tabela mapeamento_geduc                         │
│    ↓ Insere registros de mapeamento                       │
│    ↓ Cria índices para performance                        │
└────────────────────────────────────────────────────────────┘
                           ↓
┌────────────────────────────────────────────────────────────┐
│ 5. USAR NO EXPORTADOR                                      │
│    O ExportadorGEDUC já usa o MapeadorGEDUC automaticamente│
│                                                             │
│    Ao exportar histórico:                                  │
│    • disciplina_id local → consulta mapeamento            │
│    • escola_id local → consulta mapeamento                │
│    • serie_id local → consulta mapeamento                 │
│    • Envia IDs corretos do GEDUC                          │
└────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Estrutura da Tabela de Mapeamento

```sql
CREATE TABLE mapeamento_geduc (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- Tipo de dado sendo mapeado
    tipo ENUM('escola', 'disciplina', 'curso', 'curriculo', 'serie', 'turno'),
    
    -- ID no sistema local
    id_local INT NOT NULL,
    nome_local VARCHAR(255),
    
    -- ID no GEDUC
    id_geduc INT NOT NULL,
    nome_geduc VARCHAR(255),
    
    -- Qualidade do mapeamento
    similaridade VARCHAR(10),    -- Ex: "95.5%"
    verificado BOOLEAN DEFAULT FALSE,
    observacoes TEXT,
    
    -- Auditoria
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices para performance
    INDEX idx_tipo_local (tipo, id_local),
    INDEX idx_tipo_geduc (tipo, id_geduc),
    UNIQUE KEY unique_tipo_local (tipo, id_local)
);
```

### Exemplo de Dados

| id | tipo | id_local | nome_local | id_geduc | nome_geduc | similaridade |
|----|------|----------|------------|----------|------------|--------------|
| 1 | escola | 1 | ESCOLA MUNICIPAL MARIA | 1318 | ESCOLA MUN MARIA | 98.5% |
| 2 | disciplina | 5 | MATEMÁTICA | 77 | MATEMATICA | 100.0% |
| 3 | disciplina | 8 | LÍNGUA PORTUGUESA | 78 | LINGUA PORTUGUESA | 95.2% |
| 4 | serie | 2 | 2º ANO EF | 4 | 2 ANO FUNDAMENTAL | 92.0% |

---

## 🔧 Uso no Código

### Classe MapeadorGEDUC

```python
from src.exportadores.geduc_exportador import MapeadorGEDUC

# Criar mapeador
mapeador = MapeadorGEDUC()

# Obter ID do GEDUC
id_geduc = mapeador.obter_id_geduc('disciplina', id_local=5)
# Retorna: 77

# Obter nome do GEDUC
nome_geduc = mapeador.obter_nome_geduc('escola', id_local=1)
# Retorna: "ESCOLA MUN MARIA"

# Validar se existe mapeamento
existe = mapeador.validar_mapeamento('serie', id_local=2)
# Retorna: True

# Mapear lista de disciplinas
disciplinas_local = [5, 8, 12]
mapeamento = mapeador.mapear_disciplinas(disciplinas_local)
# Retorna: {5: 77, 8: 78, 12: 83}
```

### Integração com ExportadorGEDUC

```python
from src.exportadores.geduc_exportador import ExportadorGEDUC

# Criar exportador (já inclui mapeador internamente)
exportador = ExportadorGEDUC(headless=False)

# O mapeador está disponível em:
exportador.mapeador.obter_id_geduc('disciplina', 5)

# ANTES (hardcoded):
dados_historico = {
    'idinstituicao': 1318,  # ❌ Hardcoded
    'idcurso': 4,           # ❌ Hardcoded
    'disciplinas': [
        {'id': '5', ...}    # ❌ ID local, não do GEDUC
    ]
}

# AGORA (com mapeamento):
dados_historico = {
    'idinstituicao': exportador.mapeador.obter_id_geduc('escola', escola_id),
    'idcurso': exportador.mapeador.obter_id_geduc('curso', curso_id),
    'disciplinas': [
        {
            'id': str(exportador.mapeador.obter_id_geduc('disciplina', disc_id)),
            ...
        }
        for disc in disciplinas_local
    ]
}
```

---

## 📊 Algoritmo de Comparação

### Normalização de Nomes

```python
def normalizar_nome(nome):
    # 1. Remover acentuação
    nome = ''.join(c for c in unicodedata.normalize('NFD', nome) 
                   if unicodedata.category(c) != 'Mn')
    
    # 2. Converter para maiúsculas
    nome = nome.upper()
    
    # 3. Remover espaços extras
    return nome.strip()
```

**Exemplos:**
- `"Escola Municipal São José"` → `"ESCOLA MUNICIPAL SAO JOSE"`
- `"Língua Portuguesa"` → `"LINGUA PORTUGUESA"`
- `"Matemática - 1º Ano"` → `"MATEMATICA - 1 ANO"`

### Cálculo de Similaridade

Usa `difflib.SequenceMatcher` (algoritmo de Ratcliff/Obershelp):

```python
from difflib import SequenceMatcher

def similaridade(texto1, texto2):
    return SequenceMatcher(None, texto1.upper(), texto2.upper()).ratio()
```

**Escala:**
- `1.0` = 100% idêntico
- `0.95+` = ✅ Match perfeito (provavelmente correto)
- `0.85-0.95` = ⚠️ Match bom (revisar)
- `0.70-0.85` = ⚠️ Match razoável (verificar)
- `<0.70` = ❓ Match duvidoso (ajustar manualmente)

**Exemplos:**
| Local | GEDUC | Similaridade |
|-------|-------|--------------|
| `ESCOLA MUNICIPAL JOSE` | `ESCOLA MUN JOSE` | 95.2% ✅ |
| `MATEMATICA` | `MATEMATICA` | 100.0% ✅ |
| `LINGUA PORTUGUESA` | `PORT PORTUGUESA` | 72.5% ⚠️ |
| `CIENCIAS` | `BIOLOGIA` | 30.0% ❓ |

---

## 🚀 Scripts Disponíveis

### 1. extrair_dados_mapeamento_geduc.py

**Função:** Extrai dados do GEDUC

**Uso:**
```bash
python scripts/extrair_dados_mapeamento_geduc.py
```

**Interativo:**
- Solicita usuário e senha do GEDUC
- Pergunta se quer modo headless
- Faz login (reCAPTCHA manual se necessário)
- Navega pelas páginas
- Salva JSON

**Saída:**
```
config/mapeamento_geduc_20251221_143052.json
config/mapeamento_geduc_latest.json
```

**JSON gerado:**
```json
{
  "data_extracao": "2025-12-21T14:30:52.123456",
  "escolas": [
    {"id_geduc": 1318, "nome": "ESCOLA MUN MARIA"},
    {"id_geduc": 1319, "nome": "ESCOLA MUN JOSE"}
  ],
  "disciplinas": [
    {"id_geduc": 77, "nome": "MATEMATICA"},
    {"id_geduc": 78, "nome": "LINGUA PORTUGUESA"}
  ],
  "cursos": [...],
  "curriculos": [...],
  "series": [...],
  "turnos": [...]
}
```

---

### 2. comparar_mapeamento.py

**Função:** Compara GEDUC com banco local

**Uso:**
```bash
python scripts/comparar_mapeamento.py
```

**Pré-requisito:**
- Arquivo `config/mapeamento_geduc_latest.json` deve existir

**Processo:**
1. Lê JSON do GEDUC
2. Consulta tabelas locais
3. Para cada registro local:
   - Normaliza nome
   - Compara com todos do GEDUC
   - Encontra melhor match
   - Calcula similaridade
4. Gera SQL e JSON

**Saída visual:**
```
🏫 COMPARAÇÃO DE ESCOLAS
========================================
📊 Total no sistema local: 5
📊 Total no GEDUC: 8

🔍 Sugestões de mapeamento:

✅   1 → 1318  [98.5%]  ESCOLA MUNICIPAL MARIA           → ESCOLA MUN MARIA
✅   2 → 1319  [100.0%] ESCOLA MUNICIPAL JOSE            → ESCOLA MUNICIPAL JOSE
⚠️    3 → 1320  [87.2%]  ESCOLA ESTADUAL SAO PEDRO        → ESCOLA EST S PEDRO
❓   4 → 1321  [72.5%]  CENTRO EDUCACIONAL INFANTIL      → CEI MODELO

📖 COMPARAÇÃO DE DISCIPLINAS
========================================
...
```

**Arquivos gerados:**
- `sql/mapeamento_geduc.sql` - Script SQL completo
- `config/mapeamento_sugerido.json` - Mapeamentos em JSON

---

## 📝 Exemplo de SQL Gerado

```sql
-- Tabela de mapeamento entre IDs locais e IDs do GEDUC
CREATE TABLE IF NOT EXISTS mapeamento_geduc (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tipo ENUM('escola', 'disciplina', 'curso', 'curriculo', 'serie', 'turno') NOT NULL,
    id_local INT NOT NULL,
    nome_local VARCHAR(255),
    id_geduc INT NOT NULL,
    nome_geduc VARCHAR(255),
    similaridade VARCHAR(10),
    verificado BOOLEAN DEFAULT FALSE,
    observacoes TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tipo_local (tipo, id_local),
    INDEX idx_tipo_geduc (tipo, id_geduc),
    UNIQUE KEY unique_tipo_local (tipo, id_local)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Mapeamento de Escolas
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) 
VALUES ('escola', 1, 'ESCOLA MUNICIPAL MARIA', 1318, 'ESCOLA MUN MARIA', '98.5%');

INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) 
VALUES ('escola', 2, 'ESCOLA MUNICIPAL JOSE', 1319, 'ESCOLA MUNICIPAL JOSE', '100.0%');

-- Mapeamento de Disciplinas
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) 
VALUES ('disciplina', 5, 'MATEMÁTICA', 77, 'MATEMATICA', '100.0%');

INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) 
VALUES ('disciplina', 8, 'LÍNGUA PORTUGUESA', 78, 'LINGUA PORTUGUESA', '95.2%');

-- Mapeamento de Séries
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) 
VALUES ('serie', 2, '2º ANO EF', 4, '2 ANO FUNDAMENTAL', '92.0%');
```

---

## ✅ Checklist de Implementação

### Fase 1: Extração
- [ ] Executar `extrair_dados_mapeamento_geduc.py`
- [ ] Fornecer credenciais válidas do GEDUC
- [ ] Resolver reCAPTCHA manualmente (se aparecer)
- [ ] Verificar arquivo JSON gerado
- [ ] Confirmar que tem dados em todas as seções

### Fase 2: Comparação
- [ ] Executar `comparar_mapeamento.py`
- [ ] Revisar output no console
- [ ] Verificar SQL gerado em `sql/mapeamento_geduc.sql`
- [ ] Verificar JSON gerado em `config/mapeamento_sugerido.json`

### Fase 3: Ajustes Manuais
- [ ] Abrir `sql/mapeamento_geduc.sql`
- [ ] Revisar todos os matches ⚠️ (85-95%)
- [ ] Corrigir todos os matches ❓ (<85%)
- [ ] Adicionar observações nos casos duvidosos
- [ ] Marcar `verificado = TRUE` nos corretos

### Fase 4: Aplicação
- [ ] Executar SQL no banco de dados
- [ ] Verificar tabela criada: `SELECT * FROM mapeamento_geduc`
- [ ] Testar queries de mapeamento
- [ ] Validar que todos os IDs necessários estão mapeados

### Fase 5: Testes
- [ ] Executar teste de exportação
- [ ] Verificar logs do exportador
- [ ] Confirmar que IDs corretos foram enviados
- [ ] Validar no GEDUC se dados foram salvos corretamente

---

## 🔍 Troubleshooting

### Problema: "Campo de busca não encontrado" durante extração

**Causa:** Nome do campo mudou no GEDUC

**Solução:**
1. Abrir navegador manualmente no GEDUC
2. Acessar página de escolas/disciplinas
3. Inspecionar elemento (F12)
4. Verificar nome do campo `<select name="...">` ou `<input name="...">`
5. Ajustar em `extrair_dados_mapeamento_geduc.py`:
```python
selects_possiveis = ['IDDISCIPLINA', 'IDTURMASDISP', 'disciplina_id', 'NOVO_NOME']
```

### Problema: Muitos matches com baixa similaridade

**Causa:** Nomes muito diferentes entre sistemas

**Solução:**
1. Revisar manualmente o SQL gerado
2. Para cada match ❓:
   - Acessar GEDUC
   - Encontrar ID correto
   - Ajustar manualmente no SQL

### Problema: "Tabela mapeamento_geduc não existe"

**Causa:** SQL não foi executado

**Solução:**
```bash
# Opção 1: Linha de comando
mysql -u usuario -p nome_database < sql/mapeamento_geduc.sql

# Opção 2: MySQL Workbench
# File → Open SQL Script → sql/mapeamento_geduc.sql → Execute

# Opção 3: phpMyAdmin
# Import → Choose File → sql/mapeamento_geduc.sql → Go
```

### Problema: Exportador ainda usa valores hardcoded

**Causa:** Código não atualizado para usar mapeador

**Solução:** Atualizar código em `historico_escolar.py`:
```python
# ANTES
dados_historico = {
    'idinstituicao': 1318,  # ❌
}

# DEPOIS
from src.exportadores.geduc_exportador import MapeadorGEDUC
mapeador = MapeadorGEDUC()
dados_historico = {
    'idinstituicao': mapeador.obter_id_geduc('escola', escola_id),  # ✅
}
```

---

## 📖 Referências

- [BUSCA_ALUNO_GEDUC.md](BUSCA_ALUNO_GEDUC.md) - Como funciona busca de aluno
- [EXPORTACAO_GEDUC_SELENIUM.md](EXPORTACAO_GEDUC_SELENIUM.md) - Fluxo de exportação
- [FASE1_MAPEAMENTO_FORMULARIOS_GEDUC.md](FASE1_MAPEAMENTO_FORMULARIOS_GEDUC.md) - Análise de formulários

---

**Última atualização:** 21/12/2025  
**Status:** ✅ Sistema implementado e testável  
**Próximo passo:** Executar extração com credenciais reais
