Scripts para preparar e testar as melhorias do banco `redeescola` em um ambiente isolado (Docker).

Pré-requisitos:
- Docker CLI instalado e em execução
- Python 3.8+

Arquivos:
- `create_and_restore.py` : sobe um container MySQL e restaura um dump SQL.
- `run_precheck.py` : executa o SQL de precheck `db/migrations/20251225_precheck_melhorias.sql` e salva resultados em `precheck_resultados.txt`.
- `generate_saneamento_sql.py` : gera scripts SQL de saneamento em `db/migrations/` (backup + updates + deletes).
- `apply_saneamento.py` : aplica os scripts de saneamento no container (faz backup antes, opcional `--dry-run`).

Uso rápido (exemplo):

```bash
python create_and_restore.py --dump ../../backups/backup_redeescola.sql --container redeescola_mysql --root-pass secret --db redeescola_test
python run_precheck.py --container redeescola_mysql --root-pass secret --db redeescola_test --sql ../../db/migrations/20251225_precheck_melhorias.sql
python generate_saneamento_sql.py
# revisar os arquivos gerados em db/migrations antes de aplicar
python apply_saneamento.py --container redeescola_mysql --root-pass secret --db redeescola_test
```

Cuidado: estes scripts executam alterações no banco; use primeiro em staging/VM e revise os SQL gerados antes de aplicar em produção.
