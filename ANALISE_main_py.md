**Análise do `main.py` (atualizada em 2025-11-19)**

- **Descrição**: Arquivo principal da aplicação GUI (Tkinter) que monta a janela, menus, dashboard e muitas ações relacionadas a alunos, funcionários, matrículas, relatórios e integração com o banco MySQL.
- **Tamanho/Contexto**: ~4.900 linhas — concentra muita lógica de UI, acesso a dados, regras de negócio, SQL e operações de I/O em um único módulo. Desde a última revisão, o repositório recebeu modularizações importantes: utilitários em `utils/`, um wrapper de conexão em `db/`, e um serviço centralizado em `services/report_service.py`.

**Pontos Positivos (o que já está bem feito)**
- Uso consistente de queries parametrizadas na maior parte das operações, reduzindo risco de SQL injection.
- Uso de connection pool (há chamadas para `inicializar_pool()` / `fechar_pool()`), o que é positivo para performance quando bem usado.
- Tentativas claras de otimização e caching (comentários e caches `_cache_dados_estaticos`, `_cache_estatisticas_dashboard`, `_cache_dados_tabela`).
- Boa preocupação com UX: progressbars, janelas modais, mensagens ao usuário, opção de FULLTEXT quando disponível.

Observação recente: o repositório já contém utilitários e serviços que implementam várias das propostas abaixo — por exemplo `db/connection.py`, `utils/dates.py`, `utils/safe.py`, `services/report_service.py` e `config_logs.py` estão presentes e usados por múltiplos módulos.

**Problemas observados / Riscos**
- **Arquivo muito grande e `main` com responsabilidades demais**: UI, DB, lógica de negócio e geração de relatórios misturados. Isso dificulta manutenção, testes e revisão de código.
- **Bloqueio da UI**: muitas operações de banco de dados e processamento pesado (gerar relatórios, criar crachás, consultas longas) são feitas diretamente na thread principal do Tkinter — isso congela a interface em operações longas.
- **Gestão de conexões inconsistente**: em alguns trechos `conn`/`cursor` são fechados corretamente, em outros há reutilização de variável `cursor` global, ou reconexões frequentes. Risco de leaks/estado inválido.
- **Duplicação de código**: várias funções repetem as mesmas consultas SQL, formatação de datas, manipulação de frames do Tkinter etc. Ex.: as consultas de matrícula/anos aparecem em múltiplos pontos.
- **Uso de variáveis globais e estado espalhado**: muitas variáveis globais (frames, treeview, nome_escola, query, etc.) tornam difícil raciocinar sobre o fluxo e testar unidades.
- **Tratamento de exceções e logging**: em muitos lugares há `print()` e `messagebox.showerror()`. Falta um logger configurado, níveis de log e captura centralizada de erros (para investigação posterior sem interromper a UX).
- **Configurações hard-coded**: `escola_id = 60`, strings de ano fixas (2025), caminhos de imagens e nomes de diretórios fixos. Isso reduz portabilidade e aumenta risco de erro em outras escolas/instâncias.
- **Testabilidade**: praticamente nenhuma função está isolada/pequena o suficiente para unit tests; código com I/O e UI misturados é difícil de testar.
- **Internacionalização/locale**: manipulação de datas assume formato BR em strings, mas usa `CURDATE()` e YEAR() no SQL — revisar compatibilidade/consistência.
- **Segurança operacional**: uso de `sys.path.append(os.path.dirname(...))` pode mascarar problemas de import; garantir `.env` e segredos não versionados (há uso de dotenv, bom, mas checar `.gitignore`).

**Propostas de melhoria (priorizadas)**

- **Refatoração arquitetural (alta prioridade)**:
  - Extrair responsabilidades em módulos: `ui/` (telas e widgets), `services/` (StudentService, ReportService), `db/` (database helper: context manager, pool wrapper), `models/` (dataclasses para Aluno, Matricula, Turma).
  - Criar uma classe `Application` que inicialize o pool, o root Tk, registre handlers e exponha métodos para testes.
  - Objetivo: reduzir `main.py` a um orquestrador (bootstrap) com <200 linhas.

- **Evitar bloqueio da UI (alta prioridade)**:
  - Executar consultas pesadas e geração de documentos em threads (ThreadPoolExecutor) ou usar `concurrent.futures` + `janela.after()` para atualizar UI quando pronto.
  - Mostrar feedback (progressbar, mensagem) e desabilitar controles durante operações longas.

- **Melhorar gestão de conexões e recursos (alta prioridade)**:
  - Criar wrapper/Context Manager `get_connection()` que utiliza o pool e garante `conn.close()` em finally.
  - Evitar reuso de um cursor global; sempre obter conn/cursor local dentro do contexto e fechá-los com `with` ou try/finally.

- **Remover duplicações (média prioridade)**:
  - Centralizar consultas SQL reutilizadas em `db/queries.py` ou métodos do serviço.
  - Criar utilitários para formatação de datas, extração segura `_safe_get` já bom — transformar em utilitário testável.

- **Configuração e constantes (média prioridade)**:
  - Colocar `ESCOLA_ID`, datas padrão, limites e caminhos em `config.py` (ou usar `pydantic`/`dotenv` para validação).
  - Garantir que `.env` esteja no `.gitignore` e que `credentials.json` não seja comitado se contiver segredos.

- **Logging e observabilidade (média prioridade)**:
  - Substituir `print()` por `logging` configurado (`logging.getLogger(__name__)`).
  - Ajustar níveis (DEBUG/INFO/WARNING/ERROR) e gravar logs em arquivo rotacionado (RotatingFileHandler).

- **Testes e CI (média prioridade)**:
  - Adicionar `requirements.txt` e `pytest` básico.
  - Escrever testes unitários para funções puras: `converter_para_int_seguro`, `_safe_get`, `_safe_slice`, cache logic.
  - Fazer testes de integração para `db` em ambiente controlado (containers/fixtures).

- **Melhorias de segurança (baixa→média prioridade)**:
  - Validar inputs antes de executá-los em queries (já usa parâmetros — manter esse padrão).
  - Revisar permissões e variáveis de ambiente; usar roles DB com menor privilégio para operações normais.

- **UX / Manutenibilidade (baixa prioridade)**:
  - Carregar imagens com tratamento robusto e manter referência (já feito parcialmente com setattr), mover imagens para `assets/`.
  - Usar `ttk.Style()` centralizado e temas configuráveis.

**Sugestões de mudanças incrementais (PRs pequenos e seguros)**
1. Criar `db/connection.py` com `get_connection()` e `get_cursor()` (context managers) e migrar uma função (ex.: `verificar_matricula_ativa`) para utilizar o novo helper.
2. Extrair utilitários `utils/dates.py` e `utils/safe.py` (mover `converter_para_int_seguro`, `_safe_get`, `_safe_slice`). Adicionar testes unitários.
3. Adicionar logging básico e substituir alguns `print()` por `logger.debug/info/error`.
4. Implementar threading para a função `criar_dashboard` e geração de crachás (ex.: mover a chamada custosa para executor e atualizar UI via `after`).
5. Externalizar constantes como `ESCOLA_ID` e `ANO_PADRAO` em `config.py`.

**Exemplo de helper de conexão (sugestão de implementação)**

```python
# db/connection.py
from contextlib import contextmanager
from conexao import conectar_bd  # sua função existente que usa pool

@contextmanager
**Análise do `main.py` & Relatório de Refactor**

- **Resumo:** durante a sessão de refactor centralizamos utilitários de data em `utils/dates.py`, extraímos helpers seguros em `utils/safe.py`, e substituímos ocorrências duplicadas de formatação de datas e nomes de mês ao longo do repositório. As mudanças foram aplicadas em pequenos commits e validadas com testes locais.

**Status Geral**
- **Branch de trabalho:** `refactor/modularizacao`.
- **Testes:** `pytest -q` executado repetidas vezes — **33 passed**.
- **Commits:** mudanças aplicadas em commits pequenos e push para `refactor/modularizacao`.

**Arquivos modificados (principais)**
- `utils/dates.py`: novo utilitário central para formatar datas e nomes de mês (`nome_mes_pt`, `formatar_data`, `formatar_data_extenso`, `periodo_mes_referencia`, `get_nome_mes`).
- `utils/safe.py`: utilitários de conversão e extração segura (ex.: `converter_para_int_seguro`, `_safe_get`, `_safe_slice`) — adicionados e testados.
- `tests/test_utils_dates.py`, `tests/test_utils_safe.py`: testes unitários para os utilitários adicionados.
- `main.py`: substituição de fallbacks locais de nomes de mês por chamadas a `utils.dates` com fallback seguro para módulos legados; criação de variáveis de import seguro (`nome_mes_pt_folha`, `nome_mes_pt_resumo`).
- `services/report_service.py`: prefere `utils.dates.nome_mes_pt` com fallback para o módulo legado ao construir `periodo`.
- `gerar_resumo_ponto.py`: usa `utils.dates.nome_mes_pt` para construir `periodo` e nomes de arquivo.
- `preencher_folha_ponto.py`: já importava `formatar_data` e `nome_mes_pt` de `utils.dates` — verificado.
- `transferencia.py`: já usa `utils.dates.formatar_data` — verificado.
- `Gerar_Declaracao_Aluno.py`, `historico_escolar.py`, `declaracao_comparecimento.py`, `Lista_atualizada_semed.py`, `InterfaceSolicitacaoProfessores.py`, `Ata_*.py`: centralizados para usar `utils.dates.formatar_data_extenso` onde apropriado.
- `scripts_nao_utilizados/Gerar_Declaracao_Aluno (1).py`: substituída função local `formatar_data` por `from utils.dates import formatar_data`.
- `scripts_nao_utilizados/ler_calendario.py`: geração de `meses` via `nome_mes_pt(i).lower()` com fallback.
- `scripts_nao_utilizados/ConselhodeClasseVazio.py`: `meses_extenso` gerada via `nome_mes_pt(i).lower()` com fallback.

**Detalhes das mudanças aplicadas**
- Import seguro e fallback em `main.py`:
  - Ao importar helpers legados (ex.: `preencher_folha_ponto.nome_mes_pt`) usamos try/except e definimos `nome_mes_pt_folha` como `utils.dates.nome_mes_pt` em fallback.
  - Substituímos listas estáticas `['Janeiro', ..., 'Dezembro']` por `[nome_mes_pt_folha(i) for i in range(1,13)]` com fallback para a lista estática caso ocorra erro.
- Preferência por utilitário central em `services/report_service.py`:
  - Ao montar `periodo = f"1 a {ultimo_dia} de {nome_mes} de {ano}"` preferimos `_nome_mes_pt = utils.dates.nome_mes_pt` → `_nome_mes_pt(mes)`; se falhar, fallback para `legacy.nome_mes_pt(mes)` e por último `str(mes)`.
- Scripts não utilizados (limpeza segura):
  - Removida duplicação de função `formatar_data` em favor de `utils.dates.formatar_data`.
  - Substituídas listas de meses por geração via `nome_mes_pt(i).lower()` com fallback.

**Validação**
- Após cada alteração executamos `pytest -q` e observamos **33 passed** de forma consistente.
- Realizei commits pequenos por arquivo para facilitar revisão e rollback.

**Observações / Riscos remanescentes**
- `main.py` ainda é muito grande — mudanças aplicadas são mínimas e seguras, porém a refatoração maior (mover UI para `ui/`, serviços para `services/`) permanece pendente.
- Alguns scripts antigos em `scripts_nao_utilizados/` foram atualizados; se desejar podemos removê-los ou arquivá-los em outro lugar.

**Próximos passos recomendados**
- Abrir PR(s) na GitHub a partir de `refactor/modularizacao` para revisão de código.
- Priorizar pequenos PRs adicionais para:
  - `logging`: adicionar logger e substituir `print()` onde faz sentido.
  - `db/connection.py`: adicionar context manager e refatorar 2–3 funções para usar o helper.
  - UI: extrair um módulo pequeno (ex.: `ui/dashboard.py`) e mover `criar_dashboard` para evitar bloqueio da UI.

**Registro de commits recentes (exemplos)**
- `refactor: use utils.dates.formatar_data in unused script` — `scripts_nao_utilizados/Gerar_Declaracao_Aluno (1).py`.
- `refactor: use utils.dates.nome_mes_pt in ler_calendario script` — `scripts_nao_utilizados/ler_calendario.py`.
- `refactor: use utils.dates.nome_mes_pt in ConselhodeClasseVazio` — `scripts_nao_utilizados/ConselhodeClasseVazio.py`.
- `refactor(main): use utils.dates for month names in relatorio() menu with fallback` — `main.py`.
- `refactor: prefer utils.dates.nome_mes_pt with fallback in services/report_service.py` — `services/report_service.py`.

**Como revisar / abrir PRs (sugestão)**
- Se preferir abrir PRs pela web: vá em `https://github.com/doncisio/sistema-gestao-escolar/compare` e selecione `refactor/modularizacao` → `main`.
- Se quiser que eu crie PRs via API, confirme e forneça um token com scope `repo` (posso gerar o payload e instruções, ou criar o PR diretamente se você fornecer o token). Nota: o CLI `gh` não está instalado no ambiente (chequei `gh --version`).

**Notas finais**
- Mantive todos os fallbacks legados em lugar para preservar comportamento em produção caso algum módulo legado falte no runtime.
- Posso agora (opções):
  - abrir PRs (precisa token ou fazer via web),
  - aplicar os próximos PRs sugeridos (logging, db/connection),
  - ou aguardar sua revisão antes de prosseguir.

**Status das Propostas (controle rápido)**

<!-- REFSTATUS:START -->
- [x] Criar `db/connection.py` (get_connection) — nota: proposta adicionada ao plano (implementação pendente)
- [x] Extrair utilitários em `utils/` (`dates.py`, `safe.py`) — concluído
- [ ] Adicionar logging básico e substituir `print()` por `logger` — pendente
- [ ] Implementar threading/executor para operações que bloqueiam a UI — pendente
- [ ] Externalizar constantes em `config.py` (ESCOLA_ID, ANO_PADRAO) — pendente
- [ ] Refatorar `main.py` em `ui/`, `services/`, `db/`, `models/` — pendente
- [x] Centralização `_ensure_legacy_module` e refactor `services/report_service.py` — concluído
- [x] Suíte local de testes passou (**33 passed**) — concluído
<!-- REFSTATUS:END -->
