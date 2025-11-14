# Análise de dados coletados por `historico_escolar(aluno_id)`

Este documento lista os dados que a função `historico_escolar(aluno_id)` (arquivo `historico_escolar.py`) consulta no banco e como esses dados são usados para preencher as tabelas do histórico (PDF) e outras estruturas. Também agrega recomendações da equipe para reduzir consultas redundantes passando dados já carregados pela UI.

## Resumo (contrato)
- Entrada: `aluno_id` (int)
- Saídas/uso: gera PDF do histórico escolar; preenche tabelas internas do PDF; retorna/usa dados para observações e cálculos de carga horária e situação final.
- Erros: retorna/termina sem gerar documento se não houver conexão ou registros.

---

## 1) Consultas feitas e campos retornados (origem: `historico_escolar.py`)

1. Dados da escola (consulta `query_escola`)
   - Tabela: `Escolas`
   - Campos retornados (nomes locais):
     - `e.id` -> escola_id (usado internamente)
     - `e.nome` -> nome_escola
     - `e.endereco` -> endereco_escola
     - `e.inep` -> inep_escola
     - `e.cnpj` -> cnpj_escola
     - `e.municipio` -> municipio_escola

2. Dados do aluno (consulta `query_aluno`)
   - Tabela: `Alunos`
   - Campos retornados:
     - `a.nome` -> nome_aluno
     - `a.data_nascimento` -> nascimento (formatado em `data_nascimento`)
     - `a.sexo` -> sexo
     - `a.local_nascimento` -> localn
     - `a.UF_nascimento` -> uf

3. Responsáveis (consulta `query_responsaveis`)
   - Tabelas: `Responsaveis`, `ResponsaveisAlunos`
   - Campos retornados:
     - `r.nome` -> lista `responsaveis` (pode gerar `filho_de_texto` para o PDF)

4. Histórico por disciplina (consulta `query_historico`)
   - Tabela principal: `historico_escolar` (alias h), com join em `disciplinas` (d) e `carga_horaria_total` (cht)
   - Campos retornados (cada registro do histórico):
     - `d.nome` -> disciplina (nome da disciplina)
     - `d.carga_horaria` -> carga_horaria (hora da disciplina)
     - `h.serie_id` -> série numérica (ex.: 3..11)
     - `h.media` -> média registrada (valor numérico ou NULL)
     - `h.conceito` -> conceito (R, B, O, etc.)
     - `cht.carga_horaria_total` -> carga_horaria_total (total por série/ano/escola)
     - `h.ano_letivo_id` -> id do ano letivo (foreign key)

   - Uso: esses registros preenchem a tabela "ESTUDOS REALIZADOS" do PDF (média/conceito/carga horária por série/disciplina).

5. Resumo por série / situação final (consulta `query_historia_escolar`)
   - Tabelas: `historico_escolar` (h), `anosletivos` (a), `escolas` (e)
   - Campos retornados por grupo (por série):
     - `h.aluno_id`
    ```markdown
    # Análise do `historico_escolar` (resumo atualizado)

    Este documento descreve os campos, queries e responsabilidades atuais do gerador de PDF `historico_escolar` (`historico_escolar.py`) e como a interface (`interface_historico_escolar.py`) tenta reduzir consultas redundantes via cache. Também resume a instrumentação de desempenho presente e recomenda próximos passos prioritários.

    **Resumo (contrato)**
    - **Entrada**: `aluno_id` (int) — a função aceita parâmetros opcionais (`aluno`, `escola`, `historico`, `resultados`, `dados_observacoes`, `carga_total_por_serie`, `disciplinas`).
    - **Saída/efeito**: gera e salva um PDF em `documentos_gerados/` e registra o documento via `utilitarios.gerenciador_documentos.salvar_documento_sistema`.
    - **Falhas**: aborta quando não há conexão ou dados essenciais; mensagens de erro são logadas e, em parte, exibidas ao usuário.

    ---

    **1) Consultas e campos principais (implementação atual)**

    - **Dados da escola** (`query_escola`)
      - Tabela: `Escolas`
      - Campos usados: `id`, `nome`, `endereco`, `inep`, `cnpj`, `municipio` (montam cabeçalho do PDF).

    - **Dados do aluno** (`query_aluno`)
      - Tabela: `Alunos`
      - Campos usados: `nome`, `data_nascimento`, `sexo`, `local_nascimento`, `UF_nascimento` (formatados para o cabeçalho do PDF).

    - **Responsáveis** (`query_responsaveis`)
      - Tabelas: `Responsaveis`, `ResponsaveisAlunos`
      - Uso: compor o texto "FILHO DE:" no PDF.

    - **Histórico por disciplina** (`query_historico`)
      - Tabelas: `historico_escolar` (h) JOIN `disciplinas` (d) LEFT JOIN `carga_horaria_total` (cht)
      - Campos retornados por registro: `d.nome`, `d.carga_horaria`, `h.serie_id`, `h.media`, `h.conceito`, `cht.carga_horaria_total`, `h.ano_letivo_id`.
      - Uso: preencher tabela "ESTUDOS REALIZADOS" (média, conceito, CH). `carga_total_por_serie` é calculado a partir dessas cargas ou a partir de `carga_horaria_total` quando cargas individuais são nulas.

    - **Resumo por série / situação final** (`query_historia_escolar`)
      - Agrupa por `h.serie_id` e retorna `ano_letivo`, `escola_nome`, `escola_municipio` e a `situacao_final` calculada no SQL (Promovido/Retido).
      - Uso: preencher tabela "CAMINHO ESCOLAR".

    - **IDs para observações** (`query_anos_letivos`)
      - Retorna tuplas `(serie_id, ano_letivo_id, escola_id)` usadas para buscar entradas em `observacoes_historico`.

    - **Observações adicionais** (`observacoes_historico`)
      - Buscadas por `(serie_id, ano_letivo_id, escola_id)` e prefixadas com o nome da escola quando presentes.

    Observação: todas as consultas críticas são medidas com logs de duração: `event=db_query name=<nome_query> duration_ms=<ms>`.

    ---

    **2) O que a interface (`interface_historico_escolar.py`) fornece hoje**

    - **Cache/UI first**: a interface implementa `gerar_historico_com_cache` — ela tenta montar `aluno`, `historico`, `resultados`, `dados_observacoes` e `carga_total_por_serie` a partir de caches locais e apenas consulta o BD quando necessário. Isso reduz consultas repetidas no fluxo de geração do PDF.
    - **Campos exibidos** (treeview e labels): `ID`, `Disciplina`, `Ano Letivo`, `Série`, `Escola`, `Média` (formatada), `Conceito`, além de `nome`, `data_nascimento`, `sexo` do aluno.
    - **Filtros e otimizações**: carregamento otimizado de alunos (`LIMIT 50`), busca incremental com `LIKE` para autocomplete, caches locais para resultados de filtros e disciplinas filtradas.

    ---

    **3) Instrumentação e mudanças recentes**

    - **Conversaões centralizadas**: os helpers `to_safe_int` e `to_safe_float` foram movidos para `utilitarios/conversoes.py` e `historico_escolar.py` importa `from utilitarios.conversoes import to_safe_int, to_safe_float`.
    - **Medição de queries**: já existente — logs com `event=db_query name=... duration_ms=...` para cada consulta relevante (`select_escola`, `select_aluno`, `select_responsaveis`, `select_historico`, `select_resultados_por_serie`, `select_anos_letivos_para_observacoes`, etc.).
    - **PDF render timing**: `historico_escolar` agora mede o tempo de render (envolvendo `doc.build(elements)`) e registra `event=pdf_render name=historico_escolar duration_ms=<ms>`.
    - **PDF save timing**: suporte de logging de escrita/salvamento foi adicionado em `gerarPDF.py` (registra eventos `event=pdf_save ... stage=write duration_ms=<ms>`).

    Exemplo de eventos de log atualmente gerados:
    - `event=db_query name=select_historico aluno_id=... duration_ms=123 rows=...`
    - `event=pdf_render name=historico_escolar duration_ms=456`
    - `event=pdf_save name=salvar stage=write file=Historico_... duration_ms=12`

    ---

    **4) Observações de código relevantes para a análise**

    - O gerador aceita parâmetros opcionais (cache-friendly): quando `aluno`, `historico` ou `resultados` são fornecidos pela interface, evita reconsultas e loga essa condição.
    - `carga_total_por_serie` pode ser passado pelo wrapper (por exemplo, quando a interface montou previamente o mapa) ou é calculado pelo gerador a partir do `historico` retornado do BD.
    - Há mapeamento explícito de nomes de disciplinas (`mapeamento_disciplinas`) para normalizar nomes antes de preencher a tabela.
    - Ajustes de layout (espaçamento) são aplicados dinamicamente com base no número de disciplinas desconhecidas para tentar manter o documento em uma página.

    ---

    **5) Recomendações prioritárias (curto/médio prazo)**

    - **Propagar instrumentação**: adotar `event=pdf_render` e `event=pdf_save` em todos os geradores de PDF (ex.: `transferencia.py`, `tabela_docentes.py`, etc.) para obter métricas comparáveis.
    - **Padronizar utilitários**: consolidar instrumentação e helpers em `utilitarios/` (ex.: utilitário de medição/benchmark que retorna elapsed_ms e faz o log padrão). Isso facilita testes e consistência dos nomes de eventos no log.
    - **Testes**: criar testes unitários que:
      - cubram `historico_escolar` com parâmetros opcionais (mock DB) e sem parâmetros (mock DB);
      - verifiquem geração de eventos de log (`event=db_query`, `event=pdf_render`, `event=pdf_save`) usando captura de logs ou stub do logger;
      - validem a normalização de cargas (`to_safe_int`/`to_safe_float`) e os cálculos de `carga_total_por_serie`.
    - **Interface**: considerar expor `carga_horaria` e `situacao_final` no `treeview` ou em um painel de detalhes para reduzir a necessidade de gerar o PDF apenas para consultar esses valores.
    - **Performance**: analisar índices e planos das queries mais custosas (`query_historico` e `query_historia_escolar`) em produção; considerar materializar agregados por aluno/ano quando geração em lote for necessária.

    ---

    **6) Próximos passos técnicos sugeridos (execução)**

    1. Propagar `event=pdf_render` e `event=pdf_save` para todos os geradores de PDF.
    2. Extrair utilitário de medição/registro (`utilitarios/benchmark.py`) que encapsule `start = time.time(); ...; log(event=..., duration_ms=...)`.
    3. Escrever testes unitários com fixtures de DB (usar sqlite em memória ou mocks) e adicionar verificação de logs.
    4. Atualizar pipeline/CI para garantir que `tests/` sejam descobertos com o `PYTHONPATH` correto (ou transformar o projeto em pacote instalável no ambiente de teste).
    5. (Opcional) Adicionar métricas agregadas (Prometheus / log parser) para acompanhar latências e alertar em picos.

    ---

    **Alterações realizadas automaticamente nesta revisão**

    - Helpers de conversão movidos para: `utilitarios/conversoes.py` (`to_safe_int`, `to_safe_float`).
    - `historico_escolar.py`: passou a importar as conversões e a medir `pdf_render`.
    - `gerarPDF.py`: passou a medir/logar `pdf_save` nas etapas de escrita.
    - `interface_historico_escolar.py`: contém o wrapper `gerar_historico_com_cache` que monta dados a partir do cache/UI e registra queries de apoio com `event=db_query`.

    ---

    Arquivo mesclado e atualizado automaticamente a partir das fontes do código em `c:\gestao` em 2025-11-14.

    ``` 

