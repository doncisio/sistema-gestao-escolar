# Analise e sugestoes (2025-12-08)

## Contexto observado
- Entrypoint `main.py` aciona login opcional via feature flag `perfis_habilitados` e inicia `Application`.
- `Application` em `ui/app.py` gerencia Tk, pega nome da escola via query com id 60 fixo, e inicia backup automatico via `Seguranca`.
- Pool MySQL em `conexao.py` depende de variaveis .env sem validacao ou health check; fallback direto para conexao simples.
- Logs configurados por `config_logs.py` no root logger com rotacao e formato simples.
- Nao ha `requirements.txt`/`pyproject` nem `.env.example` no repo; docs prometem 90+ testes e arquitetura MVC.

## Prioridades (0-2 semanas)
1. Configuracao centralizada e segura
   - Criar `.env.example` e `requirements.txt`/`poetry.lock` alinhados com codigo atual.
   - Extrair settings (DB, backup, test_mode, caminhos) para um objeto unico (`config/settings.py`) com validacao e defaults; ler `GESTAO_TEST_MODE` em `main.py` em vez de constante `TEST_MODE = False`.
2. Robustez do pool de conexao
   - Em `conexao.inicializar_pool`, validar que variaveis `DB_*` estao presentes, falhar com mensagem clara e opcionalmente testar conexao ao subir.
   - Eliminar duplicidade entre `conexao.py` e `db/connection.py` criando um unico entrypoint `get_connection()`/context manager.
3. IDs e configuracao de escola
   - Substituir id fixo 60 em `ui/app.py._get_school_name` por `config.ESCOLA_ID` ou valor lido do .env, com fallback offline (nome default) e aviso suave na UI.
4. Backup e encerramento
   - Tornar opcional `Seguranca` via feature flag/env; registrar falhas no backup e nao interromper fechamento.
   - Evitar agendar backup duas vezes: inicializar scheduler somente uma vez e cancelar no handler de fechamento.
5. Observabilidade
   - Permitir formato JSON e nivel de log via env/feature flag em `config_logs.setup_logging`, com campo de correlacao (request_id/usuario) em `log_with_context`.
   - Adicionar log inicial de versao/ambiente logo no `main()`.

## Qualidade e manutencao (2-6 semanas)
- Atualizar docs (`docs/README.md`, `docs/MELHORIAS_SISTEMA.md`) para refletir tamanho real do `main.py`, estado dos testes e roadmap atual.
- Habilitar CI simples (GitHub Actions) rodando `pytest tests` e `mypy`/`ruff` em Windows e Ubuntu.
- Adicionar `pre-commit` com ruff/black e cheque de formatos (evita divergencias em scripts `.bat`).
- Fortalecer UI contra erros de banco: caso a query de `_get_school_name` falhe, exibir mensagem nao bloqueante e carregar UI em modo somente leitura.
- Mapear lugares que manipulam usuarios/perfis para validar permissoes em um unico decorator/guard de UI.

## Ideias de novas funcionalidades
- Dashboard por perfil: `setup_dashboard` ja aceita `usuario`; ampliar para widgets especificos (coordenador recebe alertas de turmas, secretaria recebe pendencias de documentos).
- Monitoramento de saude: tela ou comando rapido que mostra status do pool (`obter_info_pool()`), ultimo backup, e conectividade com MySQL.
- Exportacoes agendadas: agendar geracao de relatorios frequentes (listas de frequencia/boletins) com envio automatico para pasta do Drive configurada.
- Auditoria de acoes sensiveis: registrar eventos como edicao de aluno/funcionario e restaurar backups, incluindo `usuario` e timestamp, com consulta por data.
