# Recomendações: Dados que a interface deve enviar para `historico_escolar` (reduzir consultas SQL)

Este arquivo contém a mesma recomendação adicionada ao relatório principal, em formato independente, caso a atualização direta de `HISTORICO_CAMPOS_ANALISE.md` tenha falhado.

## Objetivo
Enviar dados já carregados pela interface ao gerar o PDF para evitar reconsultas ao banco de dados e reduzir latência e carga.

## Dados prioritários a enviar (resumo rápido)

1) aluno: {"id", "nome", "data_nascimento", "sexo", "local_nascimento", "UF_nascimento"}
2) escola: {"id", "nome", "endereco", "inep", "cnpj", "municipio"}
3) responsaveis: ["Nome A", "Nome B"]
4) historico: [(disciplina, carga_horaria, serie_id, media, conceito, carga_horaria_total, ano_letivo_id), ...]
5) resultados: [(aluno_id, serie_id, ano_letivo, escola_nome, escola_municipio, situacao_final), ...]
6) dados_observacoes: [(serie_id, ano_letivo_id, escola_id), ...] ou observacoes já resolvidas
7) carga_total_por_serie: {serie_id: {'carga_total': X, 'todas_null': bool, 'carga_horaria_total': Y}}
8) disciplinas (lista completa) ou disciplinas_desconhecidas (lista)

## Sugestão de assinatura opcional da função

```python
def historico_escolar(aluno_id,
                      aluno=None,
                      escola=None,
                      responsaveis=None,
                      historico=None,
                      resultados=None,
                      dados_observacoes=None,
                      carga_total_por_serie=None,
                      disciplinas=None):
    """Usar parâmetros opcionais quando fornecidos; caso contrário, consultar o BD."""
```

## Recomendações pratiques

- Criar um wrapper na interface `gerar_historico_com_cache(aluno_id)` que reúna os dados do cache/UI e chame `historico_escolar(..., aluno=..., historico=..., ...)`.
- Logar a origem dos dados (cache vs BD) dentro de `historico_escolar` para facilitar debugging.
- Manter fallback completo ao BD quando parâmetros não forem fornecidos para compatibilidade.

## Impacto esperado
- Menor número de queries por geração de PDF.
- Geração de PDF mais rápida e previsível.
- Possibilidade de gerar lotes sem abrir muitas conexões simultâneas.

---

Arquivo criado automaticamente como fallback da edição principal em `HISTORICO_CAMPOS_ANALISE.md`.
