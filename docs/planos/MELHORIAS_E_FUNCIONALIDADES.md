# Análise de Melhorias e Novas Funcionalidades

**Sistema de Gestão Escolar v2.0.0**  
**Gerado em:** 17/02/2026  
**Total do projeto:** 432 arquivos Python | ~117.000 linhas de código

---

## Sumário

1. [Visão Geral do Sistema Atual](#1-visão-geral-do-sistema-atual)
2. [Problemas de Qualidade de Código](#2-problemas-de-qualidade-de-código)
3. [Melhorias de Arquitetura](#3-melhorias-de-arquitetura)
4. [Novas Funcionalidades Propostas](#4-novas-funcionalidades-propostas)
5. [Melhorias de Performance](#5-melhorias-de-performance)
6. [Melhorias de UX/Interface](#6-melhorias-de-uxinterface)
7. [Melhorias de Segurança](#7-melhorias-de-segurança)
8. [Melhorias de Testes](#8-melhorias-de-testes)
9. [Melhorias de DevOps/Deploy](#9-melhorias-de-devopsdeploy)
10. [Melhorias de Documentação](#10-melhorias-de-documentação)
11. [Roadmap Sugerido](#11-roadmap-sugerido)

---

## 1. Visão Geral do Sistema Atual

### 1.1 Módulos Existentes

| Módulo | Descrição | Arquivos-chave |
|--------|-----------|----------------|
| **Alunos** | CRUD completo com validação Pydantic, pesquisa | `src/interfaces/cadastro_aluno.py`, `src/services/aluno_service.py` |
| **Matrículas** | Matrícula unificada, transferência, status | `src/interfaces/matricula_unificada.py`, `src/services/matricula_service.py` |
| **Funcionários** | Cadastro, edição, documentos de funcionários | `src/interfaces/cadastro_funcionario.py`, `src/services/funcionario_service.py` |
| **Notas** | Lançamento por turma/disciplina/bimestre | `src/interfaces/cadastro_notas.py` (4666 linhas) |
| **Frequência** | Lançamento e controle de faltas | `src/interfaces/lancamento_frequencia.py`, `src/interfaces/cadastro_faltas.py` |
| **Horários** | Grade horária escolar completa | `src/interfaces/horarios_escolares.py` (2367 linhas) |
| **Administrativa** | Escolas, disciplinas, turmas, séries | `src/interfaces/administrativa.py` (2574 linhas) |
| **Relatórios** | 20+ relatórios em PDF (ReportLab) | `src/relatorios/` (15 módulos) |
| **Dashboards** | 3 dashboards: Principal, Coordenador, Professor | `src/ui/dashboard*.py` |
| **Banco de Questões** | CRUD de questões BNCC, avaliações, gabaritos | `banco_questoes/` (UI + services + SQL) |
| **Autenticação** | Login, perfis (Admin/Coordenador/Professor), RBAC | `auth/` |
| **Importadores** | GEDUC (Selenium), BNCC Excel, horários locais/CSV | `src/importadores/` |
| **Exportadores** | Exportação para GEDUC | `src/exportadores/` |
| **Backup** | Backup MySQL automático + Google Drive | `src/core/seguranca.py` |
| **Transição Ano** | Migração de ano letivo com re-matrícula | `src/interfaces/transicao_ano_letivo.py` |
| **Crachás** | Geração de crachás individuais | `src/ui/cracha_individual_window.py` |
| **Livros** | Controle de livros faltantes | `src/ui/livros_faltantes_window.py` |
| **Licenças** | Gerenciamento de licenças de funcionários | `src/interfaces/gerenciamento_licencas.py` |

### 1.2 Relatórios Disponíveis

**Listas:** Alfabética, Atualizada, SEMED, Frequência, Reunião, Fardamento, Notas, Contatos, Transtornos, Livros Faltantes, Controle de Livros, Funcionários (Excel)

**Documentos:** Boletim Bimestral, Atas (1º-5º, 6º-9º, Geral, 1º-9º), Declaração (Aluno, Funcionário, Comparecimento), Histórico Escolar, Transferência, Termo de Responsabilidade, Certificados, Termos "Cuidar dos Olhos"

**Análises:** Movimento Mensal, Tabela de Docentes, Folha de Ponto, Resumo de Ponto, Relatório de Análise de Notas, Pendências

### 1.3 Dashboards

- **Principal:** Gráfico de pizza (distribuição por série/turma) + barras empilhadas (movimento mensal)
- **Coordenador:** Visão expandida com mais métricas
- **Professor:** Visão filtrada por turmas do professor logado

---

## 2. Problemas de Qualidade de Código

### 2.1 Arquivos Gigantes (God Objects)

Esses arquivos concentram responsabilidades demais e dificultam manutenção:

| Arquivo | Linhas | Ação Recomendada |
|---------|--------|------------------|
| `src/interfaces/cadastro_notas.py` | **4.666** | Extrair lógica de negócio para service; dividir UI em abas/componentes |
| `src/interfaces/historico_escolar.py` | **3.018** | Separar renderização PDF da lógica de busca de dados |
| `src/interfaces/administrativa.py` | **2.574** | Separar cada aba (escolas, disciplinas, séries, turmas) em módulo próprio |
| `src/interfaces/horarios_escolares.py` | **2.367** | Extrair lógica de persistência para service |
| `src/relatorios/movimento_mensal.py` | **2.043** | Separar geração de dados de formatação PDF |
| `src/importadores/geduc.py` | **1.974** | Separar UI da automação Selenium |
| `src/interfaces/edicao_funcionario.py` | **1.708** | Reutilizar componentes com `cadastro_funcionario.py` |
| `src/ui/button_factory.py` | **1.692** | Gerar menus dinamicamente a partir de configuração |
| `src/gestores/servicos_lote_documentos.py` | **1.666** | Separar por tipo de documento |
| `src/ui/dashboard_coordenador.py` | **1.192** | Extrair componentes visuais reutilizáveis |

### 2.2 `except:` Nus — 38 Ocorrências

O uso de `except:` sem especificar a exceção captura **tudo**, incluindo `KeyboardInterrupt` e `SystemExit`, dificultando diagnóstico de erros:

| Arquivo | Ocorrências |
|---------|-------------|
| `src/importadores/geduc.py` | 8 |
| `src/interfaces/horarios_escolares.py` | 4 |
| `src/interfaces/administrativa.py` | 3 |
| `src/interfaces/edicao_funcionario.py` | 2 |
| `src/interfaces/edicao_aluno.py` | 3 |
| `src/interfaces/matricula_unificada.py` | 2 |
| `src/interfaces/gerenciamento_licencas.py` | 2 |
| `src/interfaces/historico_escolar.py` | 2 |
| `src/interfaces/cadastro_funcionario.py` | 2 |
| `src/interfaces/cadastro_aluno.py` | 1 |
| `src/relatorios/geradores/certificado.py` | 2 |
| `src/relatorios/geradores/folha_ponto.py` | 1 |
| `src/ui/app.py` | 1 |
| `src/ui/button_factory.py` | 1 |
| `src/ui/dashboard_coordenador.py` | 1 |
| `src/ui/dashboard_professor.py` | 1 |
| `src/utils/utilitarios/utils_imagem.py` | 1 |

**Correção:** Substituir `except:` por `except Exception:` ou exceções específicas.

### 2.3 Valores Hard-Coded

| Valor | Local | Risco |
|-------|-------|-------|
| `escola_id = 60` | `src/relatorios/historico_escolar.py`, `src/services/estatistica_service.py`, vários testes | Funciona apenas para a escola específica |
| Paleta `co0`–`co9` inline | 13+ interfaces definem cores localmente | Apesar de existir `src/ui/colors.py` e `src/ui/theme.py` |
| `ANO_LETIVO_ATUAL = 2026` | `src/core/config.py` | Requer atualização manual a cada virada de ano |
| Caminho Google Drive | `src/core/seguranca.py` | Caminho fixo `G:\Meu Drive\NADIR_2025\` |
| Salt de senha fixo | `auth/password_utils.py` | `salt = "gestao_escolar_2025"` — mesmo salt para todos os usuários |

### 2.4 Duplicação de Código

- **Paleta de cores:** Definida separadamente em ~13 interfaces ao invés de importar de `AppColors`
- **Padrão de janela secundária:** `withdraw pai → Toplevel → protocol WM_DELETE_WINDOW → deiconify` repetido em todo callback de `action_callbacks.py`; deveria ser um decorador ou context manager
- **Conexão BD nas interfaces:** 13 interfaces importam `conectar_bd` diretamente e/ou `mysql.connector`, quebrando a separação de camadas
- **Try/except + messagebox.showerror:** Padrão repetido ~50 vezes; deveria ser um decorador `@handle_ui_errors`

### 2.5 Interfaces Acessando Banco Diretamente

13 de 14 interfaces fazem SQL diretamente ao invés de usar services:

| Interface | Importa `conectar_bd` | Importa `mysql.connector` |
|-----------|:----:|:----:|
| `administrativa.py` | ✓ | |
| `cadastro_aluno.py` | ✓ | ✓ |
| `cadastro_faltas.py` | ✓ | |
| `cadastro_funcionario.py` | ✓ | ✓ |
| `cadastro_notas.py` | ✓ | ✓ |
| `edicao_aluno.py` | ✓ | ✓ |
| `edicao_funcionario.py` | ✓ | ✓ |
| `gerenciamento_licencas.py` | ✓ | ✓ |
| `historico_escolar.py` | ✓ | |
| `horarios_escolares.py` | ✓ | ✓ |
| `lancamento_frequencia.py` | ✓ | |
| `matricula_unificada.py` | ✓ | |
| `solicitacao_professores.py` | ✓ | |
| `transicao_ano_letivo.py` | ✓ | ✓ |

**Ideal:** Interfaces devem chamar apenas services; services usam `get_cursor()` do `db/connection.py`.

---

## 3. Melhorias de Arquitetura

### 3.1 Estado Atual da Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│  UI Layer (src/ui/, src/interfaces/)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  dashboard.py │  │  app.py      │  │  menu.py     │ │
│  │  table.py     │  │  actions/    │  │  detalhes/   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘ │
│          │                  │                            │
│          │  ╔═══════════════════════════════╗            │
│          │  ║  QUEBRA DE CAMADA!            ║            │
│          ├──║  13 interfaces acessam BD     ║            │
│          │  ║  diretamente com conectar_bd  ║            │
│          │  ╚═══════════════════════════════╝            │
│          ▼                                               │
├──────────────────────────────────────────────────────────┤
│  Service Layer (src/services/)                           │
│  aluno_service │ matricula_service │ turma_service      │
│  boletim_service │ estatistica_service │ ...            │
├──────────────────────────────────────────────────────────┤
│  Data Access Layer (db/)                                 │
│  connection.py (pool) │ queries.py (SQL constantes)     │
│  + src/core/conexao.py (shim/compat)                    │
├──────────────────────────────────────────────────────────┤
│  MySQL Database                                          │
└──────────────────────────────────────────────────────────┘
```

### 3.2 Propostas de Melhoria

#### A) Eliminar Acesso Direto ao BD nas Interfaces
- Migrar todo SQL inline das 13 interfaces para a camada de services
- Cada interface deve depender apenas de um ou mais services
- Impacto: ~5.000 linhas a mover/refatorar

#### B) Introduzir Repository Pattern (DAO)
```
Interface → Service → Repository → DB
```
- Repositórios encapsulam SQL puro
- Services contêm lógica de negócio
- Facilita troca de banco no futuro e testes com mocks

#### C) Criar WindowManager
- Classe centralizada para gerenciamento de janelas Toplevel
- Controlaria: abertura, fechamento, hide/show do pai, modais
- Eliminaria duplicação do padrão `withdraw → Toplevel → deiconify`

#### D) Unificar Camada de Conexão
- Remover `src/core/conexao.py` (shim de compatibilidade)
- Padronizar uso exclusivo de `db/connection.py` → `get_cursor()` / `get_connection()`

#### E) Mover banco_questoes/ para src/
- Atualmente `banco_questoes/` está na raiz, inconsistente com `src/`
- Mover para `src/banco_questoes/` para padronizar imports

---

## 4. Novas Funcionalidades Propostas

### 4.1 Prioridade Alta

| # | Funcionalidade | Descrição | Justificativa |
|---|---------------|-----------|---------------|
| F1 | **Relatório de Desempenho Comparativo** | Gráficos comparando notas entre turmas/séries/bimestres | Análise pedagógica para coordenadores |
| F2 | **Alertas de Frequência** | Notificação automática quando aluno atinge limiar de faltas (ex: 25%) | Prevenção de evasão escolar |
| F3 | **Importação de Alunos via CSV/Excel** | Upload de planilha para importar alunos em lote | Agilizar migração entre sistemas |
| F4 | **Agenda/Calendário Escolar** | Módulo com eventos, feriados, datas de provas, reuniões | Organização central de datas |
| F5 | **Relatório de Conselho de Classe** | Geração automática com dados consolidados do bimestre | Demanda frequente das escolas |

### 4.2 Prioridade Média

| # | Funcionalidade | Descrição | Justificativa |
|---|---------------|-----------|---------------|
| F6 | **Módulo de Comunicados** | Sistema de comunicados para pais/responsáveis | Comunicação escola-família |
| F7 | **Dashboard de Frequência** | Gráfico de frequência por turma/mês com tendências | Acompanhamento visual |
| F8 | **Controle de Material Escolar** | Registro e controle de materiais entregues/devolvidos | Gestão de recursos |
| F9 | **Histórico de Alterações (Audit Trail)** | Log de quem alterou o quê e quando | Rastreabilidade e compliance |
| F10 | **Relatórios Customizáveis** | Interface para selecionar campos e filtros antes de gerar | Flexibilidade |
| F11 | **Multi-idioma (i18n)** | Preparar strings para tradução | Acessibilidade |
| F12 | **Busca Global** | Campo de busca unificado que pesquisa alunos, funcionários, turmas | Produtividade |

### 4.3 Prioridade Baixa (Longo Prazo)

| # | Funcionalidade | Descrição | Justificativa |
|---|---------------|-----------|---------------|
| F13 | **Versão Web (Portal)** | Acesso via navegador para professores e coordenadores | Acesso remoto |
| F14 | **App Mobile** | Leitura de QR crachás para frequência rápida | Praticidade |
| F15 | **Módulo Financeiro** | Controle de taxas/mensalidades (se aplicável) | Gestão financeira |
| F16 | **Multi-Escola (SaaS)** | Múltiplas escolas em uma instalação | Escalabilidade |
| F17 | **Integração com e-SUS/Educacenso** | Exportação automática para sistemas governamentais | Conformidade |
| F18 | **Auto-Update** | Verificação automática de atualizações no startup | Facilitar deploy |

---

## 5. Melhorias de Performance

### 5.1 Consultas ao Banco

| Problema | Local | Melhoria |
|----------|-------|----------|
| Dashboard faz N queries em loop (uma por mês) para movimento mensal | `src/services/estatistica_service.py` L356-400 | Consolidar em uma única query com `GROUP BY MES` |
| Cache com TTL fixo de 10min | `estatistica_service.py` `@dashboard_cache.cached(ttl=600)` | Adicionar invalidação por evento (ao inserir/editar matrícula) |
| Importador GEDUC é síncrono e trava a UI | `src/importadores/geduc.py` | Usar ThreadPoolExecutor para não bloquear a janela |
| Busca de alunos usa `LIKE '%nome%'` sem índice | `db/queries.py` L82 | Considerar índice FULLTEXT para buscas frequentes |
| Relatórios PDF gerados de forma síncrona em alguns menus | `src/ui/button_factory.py` | Usar padrão `run_report_in_background` já existente em `dashboard.py` |

### 5.2 Proposta: Query Única para Movimento Mensal

Ao invés do loop atual (1 query por mês × 2 = ~24 queries para um ano), usar uma única CTE:

```sql
WITH meses AS (
    SELECT 1 AS mes UNION ALL SELECT 2 UNION ALL ... SELECT 12
)
SELECT 
    meses.mes,
    COUNT(DISTINCT CASE WHEN m.status = 'Ativo' AND m.data_matricula <= LAST_DAY(CONCAT(@ano, '-', meses.mes, '-01')) THEN m.aluno_id END) as ativos,
    COUNT(DISTINCT CASE WHEN m.status IN ('Transferido','Transferida') AND m.data_matricula <= LAST_DAY(CONCAT(@ano, '-', meses.mes, '-01')) THEN m.aluno_id END) as transferidos,
    COUNT(DISTINCT CASE WHEN m.status = 'Evadido' AND m.data_matricula <= LAST_DAY(CONCAT(@ano, '-', meses.mes, '-01')) THEN m.aluno_id END) as evadidos
FROM meses
CROSS JOIN matriculas m
INNER JOIN alunos a ON m.aluno_id = a.id
WHERE m.ano_letivo_id = @ano_letivo_id AND a.escola_id = @escola_id
GROUP BY meses.mes
ORDER BY meses.mes;
```

**Ganho estimado:** redução de ~24 round-trips ao BD para 1 única query.

### 5.3 Lazy Loading de Módulos

O startup carrega todos os módulos de interface no import de menus. Usar lazy imports para reduzir tempo de inicialização:

```python
# Ao invés de:
from src.interfaces.cadastro_notas import InterfaceCadastroNotas

# Usar lazy import no callback:
def abrir_cadastro_notas():
    from src.interfaces.cadastro_notas import InterfaceCadastroNotas
    InterfaceCadastroNotas(...)
```

---

## 6. Melhorias de UX/Interface

### 6.1 Melhorias Visuais

| Melhoria | Descrição | Prioridade |
|----------|-----------|-----------|
| **Dark Mode** | `src/ui/theme.py` já existe; expandir com tema escuro completo | Média |
| **Cores centralizadas** | Migrar as 13+ interfaces com `co0`–`co9` inline para usar `AppColors` de `colors.py` | Alta |
| **Layout responsivo** | Substituir `geometry("950x670")` fixo por layout com `grid` weights que se adapte | Média |
| **Ícones modernos** | Trocar ícones bitmap por SVG/PNG com resolução alta (DPI awareness) | Baixa |
| **Splash Screen** | Adicionar barra de progresso real (não indeterminada) durante carregamento | Baixa |

### 6.2 Melhorias de Usabilidade

| Melhoria | Descrição | Prioridade |
|----------|-----------|-----------|
| **Atalhos de teclado** | `Ctrl+N` (novo), `Ctrl+S` (salvar), `Ctrl+F` (buscar), `F5` (atualizar) | Alta |
| **Paginação na tabela** | Tabela principal com paginação para escolas com muitos alunos | Média |
| **Feedback não-modal** | Substituir `messagebox` de sucesso por toasts/snackbars temporários | Média |
| **Breadcrumbs** | Indicador visual de "onde estou" na navegação (Menu > Alunos > Edição) | Baixa |
| **Desfazer (Undo)** | Ação de desfazer para operações destrutivas com período de grace | Baixa |
| **Auto-completar** | Campo de busca com sugestões ao digitar | Média |
| **Filtros avançados na tabela** | Filtrar por status, série, turma direto na tabela principal | Alta |
| **Exportar tabela para Excel** | Botão para exportar a tabela visível para `.xlsx` | Média |

### 6.3 Melhorias no Dashboard

| Melhoria | Descrição |
|----------|-----------|
| **Seletor de período** | Dropdown para trocar entre meses/bimestres no dashboard |
| **Gráfico de tendência** | Linha temporal mostrando evolução de matrículas |
| **KPIs resumidos** | Cards com: total de alunos, faltas do mês, notas abaixo da média |
| **Dashboard drill-down** | Clicar numa fatia do gráfico para ver lista de alunos |
| **Comparativo ano-a-ano** | Sobrepor dados do ano anterior para comparação |

---

## 7. Melhorias de Segurança

### 7.1 Críticas (Prioridade Imediata)

| Problema | Severidade | Local | Solução |
|----------|-----------|-------|---------|
| Hash SHA-256 com salt fixo | **CRÍTICA** | `auth/password_utils.py` | Migrar para `bcrypt` ou `argon2id` com salt único por usuário |
| Salt hard-coded no código-fonte | **CRÍTICA** | `auth/password_utils.py` L36: `salt = "gestao_escolar_2025"` | Gerar salt aleatório por usuário; armazenar no banco |
| Senha de transição = fallback para senha do BD | **ALTA** | `src/ui/action_callbacks.py` L497-499 | Criar `ADMIN_TRANSICAO_PASSWORD` separado no `.env` |

### 7.2 Médias

| Problema | Local | Solução |
|----------|-------|---------|
| Comparação de senhas em tempo não-constante | `src/ui/action_callbacks.py` L508 | Usar `secrets.compare_digest()` |
| Sessão sem timeout por inatividade | `auth/auth_service.py` | Implementar expiração de sessão (ex: 30 min sem atividade) |
| Logs podem conter dados sensíveis (CPF, nomes) | Global | Adicionar filtro de PII (Personally Identifiable Information) no logger |
| Sem HTTPS entre cliente e banco MySQL | Conexão DB | Habilitar SSL/TLS para conexão MySQL remota |
| Backup sem criptografia | `src/core/seguranca.py` | Criptografar backup SQL antes de enviar ao Google Drive |

### 7.3 Boas Práticas Já Implementadas ✓
- ✅ SQL parametrizado (`%s`) — sem SQL injection
- ✅ Credenciais GEDUC carregadas do `.env`
- ✅ Bloqueio de conta após 5 tentativas (`MAX_TENTATIVAS_LOGIN = 5`)
- ✅ Desbloqueio após 15 minutos (`TEMPO_BLOQUEIO_MINUTOS = 15`)
- ✅ Sistema de perfis RBAC (Admin/Coordenador/Professor)
- ✅ Feature flags para habilitar/desabilitar funcionalidades

---

## 8. Melhorias de Testes

### 8.1 Estado Atual

- **Configuração:** `pytest.ini` configurado, markers `slow` e `integration`
- **Cobertura:** `pyproject.toml` configurado com `pytest-cov`, mas sem report gerado
- **Estimativa de cobertura:** < 15% (432 arquivos, ~25 arquivos de teste)
- **Problema principal:** Maioria dos testes depende de MySQL real (banco de produção)

### 8.2 Propostas

| # | Melhoria | Detalhamento | Prioridade |
|---|----------|-------------|-----------|
| T1 | **conftest.py com fixtures** | Criar `tests/conftest.py` com fixtures de mock de DB, app, cursor | Alta |
| T2 | **Testes unitários de services** | Cobrir 100% dos services com mocks de DB | Alta |
| T3 | **Separar testes por tipo** | `tests/unit/`, `tests/integration/`, `tests/e2e/` | Média |
| T4 | **Test factory para models** | Funções factory para criar objetos de teste (Aluno, Matricula) | Média |
| T5 | **Coverage mínimo 60%** | Adicionar `--cov-fail-under=60` ao `pytest.ini` | Média |
| T6 | **Testes de validação Pydantic** | Testar todos os models com dados válidos e inválidos | Média |
| T7 | **Smoke test automatizado** | Teste que abre e fecha a aplicação sem erros | Baixa |
| T8 | **Testes de regressão** | Para cada bug corrigido, adicionar teste que previne recorrência | Constante |

### 8.3 Exemplo de conftest.py

```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_cursor():
    """Cursor mock que retorna dicts."""
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []
    return cursor

@pytest.fixture
def mock_db(mock_cursor):
    """Patch completo do get_cursor."""
    with patch('db.connection.get_cursor') as mock:
        mock.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock.return_value.__exit__ = MagicMock(return_value=False)
        yield mock_cursor

@pytest.fixture
def sample_aluno():
    """Aluno de exemplo para testes."""
    return {
        'id': 1, 'nome': 'João Silva',
        'data_nascimento': '2015-03-15', 'sexo': 'M',
        'escola_id': 60, 'status': 'Ativo'
    }
```

---

## 9. Melhorias de DevOps/Deploy

### 9.1 Estado Atual
- **Build:** PyInstaller (`GestaoEscolar.spec`) → `GestaoEscolar.exe`
- **Instalador:** Inno Setup (`GestaoEscolar.iss`)
- **Versão:** `"2.0.0"` em `pyproject.toml`, mas `"1.0.0"` em `GestaoEscolar.iss` — **desincronizado!**
- **Sem CI/CD:** Nenhum pipeline automatizado

### 9.2 Propostas

| # | Melhoria | Descrição | Prioridade |
|---|----------|-----------|-----------|
| D1 | **Sincronizar versão** | Single source of truth em `pyproject.toml`; gerar ISS e `version_info.txt` automaticamente | Alta |
| D2 | **GitHub Actions CI** | Pipeline: lint (ruff) → test (pytest) → build (PyInstaller) → release | Alta |
| D3 | **Migrações automatizadas** | Substituir scripts SQL manuais (`db/migrations/`) por Alembic | Média |
| D4 | **Health check no startup** | Verificar conexão DB + integridade de tabelas essenciais ao iniciar | Média |
| D5 | **Auto-update** | Verificar no GitHub se há versão nova → baixar e instalar | Baixa |
| D6 | **Docker para dev** | `docker-compose.yml` com MySQL + phpMyAdmin para desenvolvimento | Baixa |
| D7 | **Lock de dependências** | `pip freeze` ou Poetry lock para builds reprodutíveis | Média |
| D8 | **CHANGELOG.md** | Manter changelog no formato Keep a Changelog | Média |

### 9.3 Exemplo de GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest tests/ --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v4
```

---

## 10. Melhorias de Documentação

### 10.1 Estado Atual
- `README.md` — presente com Quick Start e estrutura
- `docs/` — 40+ arquivos, maioria são análises de sprints/bugs
- Docstrings presentes nas classes de services e models
- `docs/ARCHITECTURE.md` e `docs/DEVELOPMENT.md` existem

### 10.2 Propostas

| Melhoria | Descrição | Prioridade |
|----------|-----------|-----------|
| **Reorganizar docs/** | Criar subpastas: `docs/sprints/`, `docs/analises/`, `docs/guias/` | Alta |
| **Diagrama ER do banco** | Exportar `redeescola3.mwb` para PNG/SVG e incluir no docs | Alta |
| **Documentar permissões RBAC** | Tabela: perfil × funcionalidade → permissão | Média |
| **API dos Services** | Docstrings padronizadas + geração automática com Sphinx/pdoc | Média |
| **CONTRIBUTING.md** | Padrões de código, convenções de commit, processo de PR | Baixa |
| **CHANGELOG.md** | Histórico de mudanças por versão | Média |
| **Documentar Feature Flags** | Lista de todas as flags com descrição e valor padrão | Média |
| **Guia de Troubleshooting** | Problemas comuns e soluções (conexão BD, imports, etc.) | Baixa |

---

## 11. Roadmap Sugerido

### Sprint 1-2: Fundamentos (4 semanas)

- [ ] **Segurança:** Migrar hash de senhas para bcrypt/argon2 
- [ ] **Qualidade:** Corrigir 38 `except:` nus → `except Exception:`
- [ ] **DevOps:** Sincronizar versão entre `pyproject.toml` e `GestaoEscolar.iss`
- [ ] **Testes:** Criar `conftest.py` com fixtures de mock de DB
- [ ] **Docs:** Reorganizar pasta `docs/` em subpastas

### Sprint 3-4: Arquitetura (4 semanas)

- [ ] **Arquitetura:** Remover `src/core/conexao.py` — padronizar `get_cursor()`
- [ ] **Arquitetura:** Migrar SQL inline de `cadastro_notas.py` para services
- [ ] **Arquitetura:** Migrar SQL inline de `administrativa.py` para services
- [ ] **UX:** Centralizar cores — eliminar `co0`-`co9` inline
- [ ] **UX:** Adicionar atalhos de teclado básicos

### Sprint 5-6: Funcionalidades (4 semanas)

- [ ] **F5:** Relatório de Conselho de Classe
- [ ] **F1:** Relatório de Desempenho Comparativo entre turmas
- [ ] **F2:** Alertas de Frequência (limiar de faltas)
- [ ] **UX:** Filtros avançados na tabela principal
- [ ] **Performance:** Consolidar queries do movimento mensal em uma única

### Sprint 7-8: Refatoração de Gigantes (4 semanas)

- [ ] **Refatorar:** `cadastro_notas.py` (4.666 → ~4 módulos)
- [ ] **Refatorar:** `historico_escolar.py` interface (3.018 → dados + PDF)
- [ ] **Refatorar:** `administrativa.py` (2.574 → 4 abas modulares)
- [ ] **Testes:** Cobertura services ≥ 60%

### Sprint 9-10: UX e Modernização (4 semanas)

- [ ] **F3:** Importação de alunos via CSV/Excel
- [ ] **F4:** Agenda/Calendário Escolar
- [ ] **UX:** Dark Mode
- [ ] **UX:** Dashboard drill-down (clicar fatia → lista)
- [ ] **DevOps:** GitHub Actions CI básico

### Longo Prazo (2º semestre)

- [ ] **F13:** Versão Web (portal para professores)
- [ ] **D5:** Auto-update no instalador
- [ ] **F17:** Integração com Educacenso
- [ ] **WindowManager** centralizado para janelas Toplevel
- [ ] Repository/DAO pattern completo

---

> **Nota:** As estimativas de prioridade consideram impacto no uso diário, esforço de implementação e risco de introdução de bugs. Recomenda-se validar com a equipe pedagógica as funcionalidades propostas antes de iniciar cada sprint.
