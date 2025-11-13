# Análise de dados coletados por `historico_escolar(aluno_id)`

Este documento lista os dados que a função `historico_escolar(aluno_id)` (arquivo `historico_escolar.py`) consulta no banco e como esses dados são usados para preencher as tabelas do histórico (PDF) e outras estruturas. Em seguida indico quais desses dados são efetivamente mostrados na interface `interface_historico_escolar.py`.

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
     - `h.serie_id`
     - `a.ano_letivo` -> ano letivo (texto/inteiro)
     - `e.nome` -> escola_nome
     - `e.municipio` -> escola_municipio
     - `situacao_final` -> calculada no SQL ("Promovido(a)" / "Retido(a)" baseado em média/conceito)

   - Uso: preenche a tabela "CAMINHO ESCOLAR" do PDF (ANO LETIVO, ESTABELECIMENTO, LOCAL, RESULTADO FINAL).

6. IDs para observações (consulta `query_anos_letivos`)
   - Retorna linhas com: `h.serie_id`, `h.ano_letivo_id`, `h.escola_id`
   - Uso: para buscar observações específicas na tabela `observacoes_historico` e compor a seção de observações do PDF.

7. Observações adicionais (dentro de `criar_tabela_observacoes`)
   - Consulta: `observacoes_historico` por (`serie_id`, `ano_letivo_id`, `escola_id`)
   - Se encontrada, pré-fixa com o nome da escola.

8. Outros usos internos / cálculos
   - Cálculo de `carga_total_por_serie` agregando `carga_horaria` ou usando `carga_horaria_total` quando valores individuais são nulos.
   - Determinação de `quantitativo_serie_ids` (número de séries distintas presentes).
   - Ajustes de layout/espacamento do PDF com base no número de disciplinas desconhecidas.

---

## 2) Quais desses campos são mostrados na interface `interface_historico_escolar.py`?

A interface exibe e permite filtrar/editar parte dos dados retornados. Abaixo a lista dos campos usados pela interface (visíveis ao usuário) vs usados apenas no PDF ou internamente.

Campos mostrados diretamente na interface (visíveis nos widgets):

- Dados do aluno (labels):
  - `nome_aluno` -> mostrado no label `self.lbl_aluno` (campo "Aluno:")
  - `data_nascimento` (formatado) -> mostrado no label `self.lbl_data_nascimento` ("Data Nascimento:")
  - `sexo` -> mostrado no label `self.lbl_sexo` ("Sexo:")

- Tabela / TreeView de histórico (`self.treeview_historico`) — colunas definidas em `interface_historico_escolar.py`:
  - `ID` -> id do registro em `historico_escolar` (h.id)
  - `Disciplina` -> `d.nome` (nome da disciplina)
  - `Ano Letivo` -> texto do ano letivo (`a.ano_letivo`) ou mapeamento do `ano_letivo_id`
  - `Série` -> série (nome/descrição) correspondente ao `serie_id`
  - `Escola` -> `e.nome` (nome da escola onde o registro foi realizado)
  - `Média` -> `h.media` (formatada, 1 casa decimal no código)
  - `Conceito` -> `h.conceito`

- Comboboxes / filtros (visíveis e editáveis):
  - `Escola` (lista de `escolas` com `id` + nome)
  - `Série` (lista de séries)
  - `Ano Letivo` (lista de anos letivos)
  - `Disciplina` (lista de disciplinas disponíveis)
  - Filtros rápidos: `filtro_ano`, `filtro_disciplina`, `filtro_situacao` — afetam a exibição na treeview

- Outros controles
  - Botões de Inserir/Atualizar/Excluir usam e alteram campos: `disciplina_id`, `media`, `ano_letivo_id`, `escola_id`, `conceito`, `serie_id` (estes campos fazem parte das operações de escrita no banco e aparecem na interface via os widgets acima)

Campos usados no PDF ou internamente, mas NÃO diretamente mostrados na janela principal da interface (ou só aparecem no PDF / janelas específicas):

- `d.carga_horaria` (carga horária por disciplina) — usado para preencher coluna CH no PDF; não aparece no `treeview_historico` padrão.
- `cht.carga_horaria_total` (carga horária total por série/ano/escola) — usado apenas no PDF para calcular totais.
- `resultados` (consulta de `situacao_final`) -> `situacao_final` aparece no PDF na tabela "CAMINHO ESCOLAR" mas não é coluna na treeview padrão.
- `dados_observacoes` e `observacoes_historico` — usados para compor a seção Observações do PDF; não há campo de observações principal visível na tela (há função para gerenciar observações, porém não é mostrado por padrão no grid principal)
- `endereco_escola`, `inep_escola`, `cnpj_escola`, `municipio_escola` — usados no cabeçalho do PDF; não são exibidos na tela principal (exceto dentro de diálogos ou exportações)
- `responsaveis` -> nomes usados no PDF em "FILHO DE:" mas a interface principal não exibe os responsáveis na área do histórico (a menos de diálogo específico no código)

---

## 3) Observações e recomendações rápidas

- A interface exibe os campos essenciais para CRUD do histórico (disciplina, ano letivo, série, escola, média, conceito e id do registro) e informações básicas do aluno (nome, data de nascimento, sexo).
- Dados adicionais usados para compor o PDF (carga horária, situação final por série, observações por escola) não aparecem diretamente no `treeview_historico`, mas são consultados quando se gera o PDF (`historico_escolar(aluno_id)`).
- Se quiser expor carga horária ou situação final na interface, pode-se adicionar colunas na `treeview_historico` ou painéis secundários que mostram esses dados por série.

---

Arquivo gerado automaticamente por análise do código em `c:\gestao` em {data}.
