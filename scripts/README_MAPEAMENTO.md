# Scripts de Mapeamento GEDUC

Scripts para extrair e mapear dados entre Sistema Local e GEDUC.

## 🎯 Objetivo

Evitar erros na exportação mapeando IDs locais para IDs do GEDUC automaticamente.

## 📁 Arquivos

### 1. `extrair_dados_mapeamento_geduc.py`
Extrai IDs e nomes do GEDUC via Selenium.

**Uso:**
```bash
python scripts/extrair_dados_mapeamento_geduc.py
```

**Saída:**
- `config/mapeamento_geduc_YYYYMMDD_HHMMSS.json` (com timestamp)
- `config/mapeamento_geduc_latest.json` (sempre atualizado)

**Dados extraídos:**
- ✅ Escolas (instituições)
- ✅ Disciplinas
- ✅ Cursos
- ✅ Currículos
- ✅ Séries
- ✅ Turnos

---

### 2. `comparar_mapeamento.py`
Compara dados do GEDUC com banco local e gera SQL.

**Uso:**
```bash
python scripts/comparar_mapeamento.py
```

**Pré-requisito:**
- Arquivo `config/mapeamento_geduc_latest.json` deve existir
- Rodar `extrair_dados_mapeamento_geduc.py` primeiro

**Saída:**
- `sql/mapeamento_geduc.sql` - Script SQL para criar tabela
- `config/mapeamento_sugerido.json` - Mapeamentos sugeridos

**Algoritmo:**
1. Normaliza nomes (remove acentos, maiúsculas)
2. Calcula similaridade (0-100%)
3. Sugere melhor match para cada registro
4. Gera SQL com INSERTs

**Qualidade dos matches:**
- ✅ >95% - Match perfeito
- ⚠️ 85-95% - Revisar
- ❓ <85% - Ajustar manualmente

---

## 🚀 Fluxo Completo

```bash
# Passo 1: Extrair dados do GEDUC
python scripts/extrair_dados_mapeamento_geduc.py
# → Fornece usuário/senha
# → Aguarda login e extração
# → Gera config/mapeamento_geduc_latest.json

# Passo 2: Comparar com banco local
python scripts/comparar_mapeamento.py
# → Compara automaticamente
# → Gera sql/mapeamento_geduc.sql

# Passo 3: Revisar SQL gerado
# Abrir sql/mapeamento_geduc.sql
# Ajustar matches ⚠️ e ❓

# Passo 4: Executar SQL no banco
mysql -u usuario -p database < sql/mapeamento_geduc.sql

# Passo 5: Usar no exportador
# O ExportadorGEDUC já usa automaticamente!
```

---

## 📊 Exemplo de Output

### Extração
```
🔍 EXTRAÇÃO DE DADOS DE MAPEAMENTO DO GEDUC
============================================
📚 Extraindo escolas...
  ✓ Encontrou 8 escolas no select 'IDINSTITUICAO'
📖 Extraindo disciplinas...
  ✓ Encontrou 15 disciplinas no select 'IDDISCIPLINA'
🎓 Extraindo cursos...
  ✓ Encontrou 3 cursos no select 'IDCURSO'

📊 RESUMO DA EXTRAÇÃO
====================
  Escolas:      8
  Disciplinas:  15
  Cursos:       3
  Currículos:   2
  Séries:       9
  Turnos:       3

💾 Dados salvos em: config/mapeamento_geduc_20251221_143052.json
💾 Cópia salva em: config/mapeamento_geduc_latest.json
```

### Comparação
```
🔄 COMPARADOR DE MAPEAMENTO - GEDUC vs Sistema Local
=====================================================
✅ Dados do GEDUC carregados
✅ Conectado ao banco de dados local

🏫 COMPARAÇÃO DE ESCOLAS
========================
📊 Total no sistema local: 5
📊 Total no GEDUC: 8

🔍 Sugestões de mapeamento:

✅   1 → 1318  [98.5%]  ESCOLA MUNICIPAL MARIA       → ESCOLA MUN MARIA
✅   2 → 1319  [100.0%] ESCOLA MUNICIPAL JOSE        → ESCOLA MUNICIPAL JOSE
⚠️    3 → 1320  [87.2%]  ESCOLA ESTADUAL SAO PEDRO    → ESCOLA EST S PEDRO

📖 COMPARAÇÃO DE DISCIPLINAS
=============================
✅   5 → 77   [100.0%] MATEMÁTICA                   → MATEMATICA
✅   8 → 78   [95.2%]  LÍNGUA PORTUGUESA            → LINGUA PORTUGUESA
⚠️   12 → 83   [88.0%]  CIÊNCIAS NATURAIS            → CIENCIAS

💾 GERANDO SCRIPTS SQL
======================
✅ Script SQL gerado: sql/mapeamento_geduc.sql
✅ Mapeamento JSON salvo: config/mapeamento_sugerido.json

📊 ESTATÍSTICAS FINAIS
======================
  Escolas mapeadas:      5
  Disciplinas mapeadas:  15
  Séries mapeadas:       9
```

---

## 🗄️ Tabela Criada

```sql
CREATE TABLE mapeamento_geduc (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tipo ENUM('escola', 'disciplina', 'curso', 'curriculo', 'serie', 'turno'),
    id_local INT NOT NULL,
    nome_local VARCHAR(255),
    id_geduc INT NOT NULL,
    nome_geduc VARCHAR(255),
    similaridade VARCHAR(10),
    verificado BOOLEAN DEFAULT FALSE,
    observacoes TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tipo_local (tipo, id_local),
    UNIQUE KEY unique_tipo_local (tipo, id_local)
);
```

---

## 🔧 Uso no Código

```python
from src.exportadores.geduc_exportador import MapeadorGEDUC

# Criar mapeador
mapeador = MapeadorGEDUC()

# Obter ID do GEDUC
id_geduc_escola = mapeador.obter_id_geduc('escola', escola_id_local)
id_geduc_disciplina = mapeador.obter_id_geduc('disciplina', disciplina_id_local)

# Mapear lista de disciplinas
disciplinas_local = [5, 8, 12]
mapeamento = mapeador.mapear_disciplinas(disciplinas_local)
# Retorna: {5: 77, 8: 78, 12: 83}
```

---

## ⚠️ Problemas Comuns

### "Campo de busca não encontrado"
- GEDUC mudou estrutura da página
- Ajustar nomes de campos em `extrair_dados_mapeamento_geduc.py`

### "Arquivo não encontrado: config/mapeamento_geduc_latest.json"
- Executar primeiro: `python scripts/extrair_dados_mapeamento_geduc.py`

### Muitos matches com baixa similaridade
- Nomes muito diferentes entre sistemas
- Ajustar manualmente no SQL gerado

---

## 📖 Documentação Completa

Ver: [docs/SISTEMA_MAPEAMENTO_GEDUC.md](../docs/SISTEMA_MAPEAMENTO_GEDUC.md)

---

**Última atualização:** 21/12/2025
