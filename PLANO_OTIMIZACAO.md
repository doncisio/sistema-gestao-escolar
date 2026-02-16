# Plano de Otimização — Sistema de Gestão Escolar

> **Data:** 16/02/2026  
> **Escopo:** Análise completa do projeto `main.py` e toda a árvore `src/`  
> **Objetivo:** Melhorar manutenibilidade, performance, confiabilidade e organização do código

---

## 📊 Diagnóstico Atual

| Métrica | Valor |
|---------|-------|
| Arquivo de entrada | `main.py` (150 linhas) — **bem estruturado** |
| Maior arquivo | `src/services/report_service.py` — **2.164 linhas** |
| Arquivos >800 linhas | 5 (`report_service`, `detalhes`, `actions`, `dashboard`, `app`) |
| Scripts avulsos na raiz | **20 arquivos** .py (debug, análise, migração) |
| Módulos com mypy `ignore_errors` | **13 módulos** |
| Testes | ~60+ arquivos em `tests/`, mas sem cobertura configurada |
| Gerenciamento de deps | **Inexistente** (sem `requirements.txt` ou `pyproject.toml`) |
| Código morto identificado | `aluno_old.py`, `turma_service.py.bak`, `administrativa.py.bak` |

---

## 🔴 FASE 1 — Higiene e Fundação (Prioridade Crítica)

Impacto imediato, baixo risco. Pode ser feito sem alterar comportamento.

### 1.1 Criar `requirements.txt` / `pyproject.toml`

**Problema:** Sem gerenciamento de dependências, o projeto é irreplicável em outra máquina.

**Ação:**
```
Criar pyproject.toml com:
- mysql-connector-python
- pydantic / pydantic-settings
- Pillow
- reportlab
- pandas
- plotly
- PyPDF2
- python-dotenv
- openpyxl (se usado)
Fixar versões mínimas compatíveis.
```

**Esforço:** ~1 hora

---

### 1.2 Limpar a raiz do projeto

**Problema:** 20 scripts de análise/debug poluem a raiz e dificultam a navegação.

**Ação:**
| Destino | Arquivos |
|---------|----------|
| `scripts/analise/` | `analisar_*.py`, `analise_*.py`, `comparar_*.py`, `detectar_*.py` |
| `scripts/debug/` | `check_*.py`, `debug_*.py` |
| `scripts/migracao/` | `executar_migracao_*.py`, `limpar_*.py`, `importar_geduc.py` |
| `scripts/utilidades/` | `diploma_5ano.py`, `validar_estrutura_interfaces.py` |

Atualizar imports se algum for referenciado por outros módulos.

**Esforço:** ~30 minutos

---

### 1.3 Remover código morto

**Ação:**
- Deletar `src/models/aluno_old.py` (691 linhas, sem uso ativo)
- Deletar `src/services/turma_service.py.bak`
- Deletar `src/interfaces/administrativa.py.bak`
- Migrar dependências de `src/models/funcionario_old.py` para o modelo atual e então removê-lo

**Esforço:** ~2 horas (requer validação de `funcionario_old.py`)

---

### 1.4 Atualizar `REFACTOR_STATUS.json`

**Problema:** Desatualizado desde nov/2025. Tarefas marcadas "pendente" já foram parcialmente feitas.

**Ação:** Reconciliar com estado real do código e manter atualizado como tracker de dívida técnica.

**Esforço:** ~30 minutos

---

## 🟠 FASE 2 — Arquitetura e Separação de Camadas (Prioridade Alta)

Corrige os problemas estruturais mais impactantes.

### 2.1 Unificar módulos de conexão com banco

**Problema:** Dois módulos fazem a mesma coisa com responsabilidades sobrepostas:
- `src/core/conexao.py` — pool MySQL, `conectar_bd()`
- `db/connection.py` — context managers `get_connection()`, `get_cursor()`

**Ação:**
1. Consolidar em `db/connection.py` como ponto único de entrada
2. Mover lógica de pool de `conexao.py` para dentro de `connection.py`
3. Deprecar `conexao.py` com re-exports temporários para compatibilidade
4. Migrar todos os chamadores gradualmente

**Esforço:** ~4 horas

---

### 2.2 Consolidar diretórios de importação

**Problema:** `src/importadores/` (português) e `src/importers/` (inglês) coexistem.

**Ação:**
1. Escolher uma convenção (recomendação: `src/importadores/` — manter consistência em português)
2. Mover `src/importers/geduc_horarios.py` e `src/importers/local_horarios.py` para `src/importadores/`
3. Remover diretório `src/importers/`

**Esforço:** ~1 hora

---

### 2.3 Remover dependências de UI na camada de serviço

**Problema:** Serviços importam `tkinter.messagebox`, violando separação de camadas.

**Arquivos afetados:**
- `src/services/aluno_service.py` — `from tkinter import messagebox`
- `src/utils/error_handler.py` — `tkinter.messagebox`

**Ação:**
1. Serviços devem lançar exceções tipadas (ex.: `AlunoValidationError`, `DatabaseError`)
2. A camada de UI captura e exibe as mensagens
3. `error_handler.py` deve aceitar um callback de exibição injetado, não importar tkinter

**Esforço:** ~6 horas

---

### 2.4 Remover acesso direto ao banco na camada UI

**Problema:** `src/ui/detalhes.py` (962 linhas) faz `get_connection()` + SQL raw diretamente.

**Ação:**
1. Extrair queries para serviços dedicados (`detalhes_service.py` ou expandir `aluno_service.py`)
2. `detalhes.py` chama apenas métodos de serviço
3. Aplicar o mesmo padrão ao `dashboard.py` se houver acesso direto

**Esforço:** ~8 horas

---

## ✅ FASE 3 — Divisão de Arquivos Grandes (CONCLUÍDA)

Melhora manutenibilidade e reduz conflitos de merge.

### ✅ 3.1 Dividir `report_service.py` (2.164 → 31 linhas facade)

**Resultado:**
```
src/services/
├── report_service.py        (facade com re-exports — 31 linhas)
├── reports/
│   ├── __init__.py          (re-exports de todos os módulos)
│   ├── _utils.py            (_find_image_in_repo, _ensure_legacy_module)
│   ├── boletim.py           (7 funções de boletim/notas)
│   ├── declaracao.py        (gerar_declaracao)
│   ├── historico.py         (3 funções de histórico)
│   ├── frequencia.py        (5 funções de frequência)
│   ├── folha_ponto.py       (4 funções de folha de ponto)
│   └── outros.py            (6 funções: crachás, pendências, etc.)
```

---

### ✅ 3.2 Dividir `detalhes.py` (796 → pacote com 3 módulos)

**Resultado:**
```
src/ui/
├── detalhes/
│   ├── __init__.py          (re-exports + DetalhesManager)
│   ├── exibir.py            (utils + funções de exibição ~210 linhas)
│   └── acoes.py             (botões + wrappers de ação ~290 linhas)
```

---

### ✅ 3.3 Dividir `actions.py` (967 → pacote com 6 módulos mixin)

**Resultado:**
```
src/ui/
├── actions/
│   ├── __init__.py          (ActionHandler herda todos os mixins)
│   ├── aluno.py             (AlunoActionsMixin — 6 métodos)
│   ├── funcionario.py       (FuncionarioActionsMixin — 6 métodos)
│   ├── matricula.py         (MatriculaActionsMixin — 3 métodos)
│   ├── relatorios.py        (RelatorioActionsMixin — 4 métodos)
│   └── navegacao.py         (NavegacaoActionsMixin — 2 métodos)
```

---

### ⏭️ 3.4 `queries.py` (522 linhas) — SKIP

**Motivo:** Contém apenas constantes SQL e 2 helpers, sem importadores reais. Dividir não traz benefício.

**Esforço:** ~3 horas

---

## 🔵 FASE 4 — Performance e Resiliência (Prioridade Média)

### 4.1 Melhorar sistema de cache

**Problemas atuais:**
- Sem limite de tamanho (possível memory leak)
- `None` cacheado é tratado como miss
- Sem limpeza automática de entradas expiradas

**Ação:**
1. Adicionar `max_size` com política LRU (usar `collections.OrderedDict`)
2. Usar sentinel `_CACHE_MISS = object()` para distinguir `None` de miss
3. Adicionar background thread com `Timer` para cleanup periódico
4. Considerar migrar para `functools.lru_cache` onde possível

**Esforço:** ~4 horas

---

### 4.2 Melhorar `DbService`

**Problema:** Classe wrapper mínima sem valor agregado (14 linhas).

**Ação:** Adicionar funcionalidades úteis:
```python
class DbService:
    def execute(self, query, params=None) -> int:
        """Execute INSERT/UPDATE/DELETE, retorna rowcount."""
    
    def fetchone(self, query, params=None) -> Optional[dict]:
        """Execute SELECT, retorna primeira linha."""
    
    def fetchall(self, query, params=None) -> List[dict]:
        """Execute SELECT, retorna todas as linhas."""
    
    def transaction(self) -> ContextManager:
        """Context manager para transações explícitas."""
```

**Esforço:** ~3 horas

---

### 4.3 Corrigir `fechar_pool()` para liberação real de recursos

**Problema:** `fechar_pool()` apenas seta `None` sem fechar conexões.

**Ação:** Iterar sobre conexões ativas do pool e chamar `.close()` antes de descartar.

**Esforço:** ~1 hora

---

### 4.4 Eliminar `SELECT *` em queries críticas

**Problema:** `QUERY_BUSCAR_ALUNO_POR_ID` usa `SELECT a.*`, que é frágil e lento.

**Ação:** Substituir por colunas explícitas em todas as queries que usam `*`.

**Esforço:** ~2 horas

---

## 🟢 FASE 5 — Qualidade e Observabilidade (Prioridade Baixa)

### 5.1 Fortalecer mypy

**Problema:** 13 módulos com `ignore_errors = True`.

**Ação progressiva (1 módulo por sprint):**
1. Remover `ignore_errors` de um módulo por vez
2. Corrigir erros de tipo
3. Priorizar módulos de serviço antes de UI

**Esforço:** ~2 horas por módulo

---

### 5.2 Configurar cobertura de testes

**Problema:** `pytest.ini` sem configuração de coverage. Testes existem mas sem visibilidade de cobertura.

**Ação:**
```ini
# pytest.ini
[pytest]
testpaths = tests
addopts = --cov=src --cov-report=html --cov-report=term-missing
```

**Esforço:** ~1 hora

---

### 5.3 Validar settings automaticamente no boot

**Problema:** `Settings()` não chama `validate_all()` no momento da criação.

**Ação:** Chamar `validate_all()` no `__post_init__` da classe `Settings`.

**Esforço:** ~30 minutos

---

### 5.4 Otimizar logging

**Problemas:**
- `get_logger()` chama `setup_logging()` a cada invocação
- `rotation_type='both'` gera dois arquivos de log confusos
- Console handler desnecessário em app empacotada

**Ação:**
1. Remover chamada de `setup_logging()` de dentro de `get_logger()`
2. Usar apenas `TimedRotatingFileHandler` (rotação diária)
3. Console handler condicional (`if __debug__` ou flag ENV)

**Esforço:** ~2 horas

---

### 5.5 Considerar Pydantic Settings

**Problema:** Settings usa dataclasses manuais, mas projeto já tem Pydantic nos models.

**Ação:** Migrar `Settings` para `pydantic-settings.BaseSettings` — unifica validação, suporta `.env` nativamente, tipagem estrita.

**Esforço:** ~3 horas

---

## 📋 Resumo Executivo

| Fase | Foco | Esforço Estimado | Risco |
|------|------|-----------------|-------|
| **1 — Higiene** | Deps, limpeza raiz, código morto | ~4 horas | Mínimo |
| **2 — Arquitetura** | Conexão unificada, separação de camadas | ~19 horas | Médio |
| **3 — Divisão de arquivos** | Split de 4 arquivos monolíticos | ~19 horas | Médio |
| **4 — Performance** | Cache, DB service, pool, queries | ~10 horas | Baixo |
| **5 — Qualidade** | mypy, testes, logging, settings | ~10+ horas | Baixo |
| **Total estimado** | | **~62 horas** | |

---

## ✅ Ordem de Execução Recomendada

```
Semana 1 → Fase 1 completa (higiene)
Semana 2 → 2.1 (unificar conexão) + 2.2 (consolidar importadores)
Semana 3 → 2.3 (remover tkinter dos serviços) + 5.3 (settings auto-validate)
Semana 4 → 3.1 (split report_service.py)
Semana 5 → 2.4 (banco fora da UI) + 3.2 (split detalhes.py)
Semana 6 → 3.3 (split actions.py) + 3.4 (split queries.py)
Semana 7 → Fase 4 (performance)
Semana 8 → Fase 5 (qualidade contínua)
```

---

## 🏗️ Pontos Positivos do Projeto Atual

- **`main.py` bem organizado** — fluxo claro com validação, login e inicialização
- **Models com Pydantic** — validação robusta de CPF, telefone, UF
- **Sistema de cache existente** — precisa ajustes mas a fundação é boa
- **Lazy imports implementados** — melhora tempo de startup
- **Feature flags** — permitem deploy seguro de funcionalidades
- **Logging estruturado** — já suporta JSON e key=value
- **60+ testes** — base de testes substancial
- **Connection pool** — gerenciamento de conexões com fallback
- **Separação em managers** — `TableManager`, `ButtonFactory`, `MenuManager` indicam boa direção
