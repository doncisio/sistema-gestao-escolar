**Análise do `main.py`**

- **Descrição**: Arquivo principal da aplicação GUI (Tkinter) que monta a janela, menus, dashboard e muitas ações relacionadas a alunos, funcionários, matrículas, relatórios e integração com o banco MySQL.
- **Tamanho/Contexto**: ~4.900 linhas — concentra muita lógica de UI, acesso a dados, regras de negócio, SQL e operações de I/O em um único módulo.

**Pontos Positivos (o que já está bem feito)**
- Uso consistente de queries parametrizadas na maior parte das operações, reduzindo risco de SQL injection.
- Uso de connection pool (há chamadas para `inicializar_pool()` / `fechar_pool()`), o que é positivo para performance quando bem usado.
- Tentativas claras de otimização e caching (comentários e caches `_cache_dados_estaticos`, `_cache_estatisticas_dashboard`, `_cache_dados_tabela`).
- Boa preocupação com UX: progressbars, janelas modais, mensagens ao usuário, opção de FULLTEXT quando disponível.

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
def get_connection():
    conn = conectar_bd()
    try:
        yield conn
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass

# Uso:
# with get_connection() as conn:
#     cursor = conn.cursor()
#     cursor.execute(...)
#     cursor.close()
```

**Checklist de ações recomendadas (curto prazo)**
- **(Imediato)**: Adicionar logging, mover `escola_id` e caminhos para `config.py`.
- **(Curto prazo)**: Implementar `db/connection.py` e refatorar 3–5 funções críticas para usar o context manager.
- **(Médio prazo)**: Refatorar `main.py` em módulos menores (`ui/`, `services/`, `db/`, `models/`).
- **(Médio prazo)**: Implementar execução assíncrona (threads) para evitar bloqueio do Tkinter.
- **(Longo prazo)**: Escrever testes automatizados e configurar CI (GitHub Actions) para lint + pytest.

**Próximos passos que posso executar para ajudar**
- Extrair automaticamente funções utilitárias para `utils/` com testes (faço em PRs pequenos).
- Implementar `db/connection.py` e atualizar 2 funções como exemplo (ex.: `verificar_matricula_ativa`, `obter_estatisticas_alunos`).
- Adicionar `requirements.txt` e um `pyproject.toml` / `setup.cfg` mínimo e uma pipeline de CI sugerida.

Arquivo criado: `ANALISE_main_py.md` (raiz do projeto).

Se quiser, começo pelo PR: "db: add connection context manager + refactor verificar_matricula_ativa" — confirma que faço isso agora?

**Status das Propostas (controle rápido)**

<!-- REFSTATUS:START -->
- [x] Criar db/connection.py (get_connection)  
- [ ] Extrair utilitários em utils/ (dates.py, safe.py)
- [ ] Adicionar logging básico e substituir print() por logger
- [ ] Implementar threading/executor para operações que bloqueiam a UI
- [ ] Externalizar constantes em config.py (ESCOLA_ID, ANO_PADRAO)
- [ ] Refatorar main.py em ui/, services/, db/, models/
- [x] Centralização _ensure_legacy_module e refactor report_service.py  
- [x] Suíte local de testes passou (26 passed)  

Observações:
- Marquei apenas as ações que já foram realizadas no repositório e validadas localmente.
- Posso manter esse bloco atualizado conforme formos concluindo outras propostas.
<!-- REFSTATUS:END -->