# Prioridades: melhorias para `historico_escolar` e interface

Este arquivo sumariza e prioriza as tarefas a partir de
`HISTORICO_CAMPOS_ANALISE.md` e `HISTORICO_CAMPOS_ANALISE_ADICIONAL.md`.

Objetivo: reduzir consultas ao banco durante geração de PDF, melhorar a
interface e garantir fallback e testabilidade.

---

**Prioridade Alta**
- **Consolidar parâmetros opcionais**: atualizar `historico_escolar(aluno_id, ...)`
  para aceitar parâmetros opcionais (`aluno`, `escola`, `historico`, `resultados`,
  `dados_observacoes`, `carga_total_por_serie`, `disciplinas`) e usá-los quando
  fornecidos; caso contrário, manter consultas atuais ao BD.
  - Arquivo alvo: `historico_escolar.py`.
  - Risco/benefício: baixo risco, alto ganho de performance quando usado.

- **Criar wrapper `gerar_historico_com_cache`**: função na interface que
  agrega dados já carregados pela UI e chama `historico_escolar(..., aluno=..., ...)`.
  - Arquivo alvo: `interface_historico_escolar.py` (ou módulo de helpers da UI).
  - Resultado esperado: gera PDF sem reconsultas redundantes.

- **Logar origem dos dados (cache vs BD)**: em `historico_escolar` registrar
  no log quando os dados vieram de parâmetros (cache/UI) ou do BD.
  - Ajuda debugging e auditoria.

**Prioridade Média**
- **Reduzir queries ao gerar PDF**: revisar consultas atuais para agrupar
  e buscar apenas campos necessários; usar joins/agg quando possível.
  - Priorizar `query_historico`, `query_historia_escolar` e `query_anos_letivos`.

- **Expor `carga_horaria` e `situacao_final` na interface**: adicionar colunas
  (ou painel secundário) em `self.treeview_historico` para permitir visualização
  rápida e reduzir necessidade de abrir PDF para checar esses valores.
  - Arquivo alvo: `interface_historico_escolar.py`.

- **Fallback completo ao BD**: garantir que, se parâmetros opcionais não
  estiverem presentes, a função faça todas as consultas necessárias e
  retorne comportamento idêntico ao atual.

**Prioridade Baixa / Operacional**
- **Unificar documentos MD**: mesclar conteúdo de
  `HISTORICO_CAMPOS_ANALISE_ADICIONAL.md` em `HISTORICO_CAMPOS_ANALISE.md`
  ou manter referenciado; deixar claro contrato de assinaturas e campos.

- **Testes unitários para `historico_escolar`**: adicionar testes que
  cubram casos com e sem parâmetros opcionais, e geração parcial de dados.
  - Usar fixtures que simulem conexões e retornos do BD.

- **Batch / Connection pool para geração em lote**: quando gerar muitos PDFs
  (rota ou script de lote), usar pool de conexões e limitar concorrência.

- **Medir e logar desempenho**: instrumentar pontos-chave (tempo de query,
  tempo de render de PDF) para priorizar otimizações futuras.

---

Sugestão de pequenas etapas de implementação (sequência recomendada):
1. Alterar `historico_escolar` para aceitar parâmetros opcionais com logs.
2. Implementar `gerar_historico_com_cache` na camada de interface.
3. Ajustar chamadas existentes para usar o wrapper quando possível.
4. Adicionar colunas/painel na interface para `carga_horaria`/`situacao_final`.
5. Escrever testes unitários cobrindo os novos caminhos.
6. Medir performance em geração de PDF e otimizar queries agrupadas.

---

Arquivos sugeridos para alteração rápida:
- `historico_escolar.py` — principal: aceitar dados opcionais e logar origem.
- `interface_historico_escolar.py` — criar wrapper e UI adicional.
- `HISTORICO_CAMPOS_ANALISE.md` — documentar a assinatura atualizada.

Se quiser, posso aplicar um patch inicial que:
- altera a assinatura de `historico_escolar` (compatível com fallback),
- adiciona logs de origem dos dados, e
- cria um stub `gerar_historico_com_cache` em `interface_historico_escolar.py`.

Status das ações (atualizado em 2025-11-13):

- `historico_escolar.py`: assinatura parametrizada e logs implementados (CONCLUIDO).
- `interface_historico_escolar.py`: wrapper `gerar_historico_com_cache` implementado (CONCLUIDO).
- `utilitarios/escola_cache.py`: helper de cache criado para evitar consultas repetidas (CONCLUIDO).
- Substituição de `print()` por `logger` em módulos críticos (CONCLUIDO: `historico_escolar.py`, `interface_historico_escolar.py`, `boletim.py`, `analise_alunos.py`).
- Testes básicos adicionados: `tests/test_conversoes.py` (cobertura inicial para `to_safe_int`) (CONCLUIDO).

Próximos passos recomendados:
- Extrair e centralizar helpers de conversão (`to_safe_int`, `to_safe_float`) em `utilitarios/conversoes.py`.
- Adicionar testes de integração que simulam/conectam a um banco de desenvolvimento para validar comportamento completo do `historico_escolar` com parâmetros precomputados.
- Preparar commit e push das mudanças após revisão.

Arquivo atualizado automaticamente após implementação de mudanças no código.
