#!/usr/bin/env python3
"""Fluxo completo para aplicar saneamento + migrations de integridade em ambiente isolado.
Uso: python apply_all_changes.py --container redeescola_mysql --root-pass secret --db redeescola_test [--apply] [--run-tests]

O script:
 - cria backup do DB atual (mysqldump) e copia para ./backups/
 - executa precheck (db/migrations/20251225_precheck_melhorias.sql)
 - gera scripts de saneamento (chama generate_saneamento_sql.py)
 - aplica saneamento (chama apply_saneamento.py). Sem --apply roda em dry-run.
 - aplica migração de integridade (`db/migrations/20251225_melhorias_integridade.sql`) se --apply usado
 - (opcional) roda testes com `pytest`

ATENCAO: este script modifica dados se executado com --apply. Use primeiro em staging.
"""
import argparse
import subprocess
import os
import time
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
BACKUPS_DIR = os.path.join(ROOT, 'backups')
if not os.path.exists(BACKUPS_DIR):
    os.makedirs(BACKUPS_DIR, exist_ok=True)

SCRIPT_DIR = os.path.dirname(__file__)
MIGR_DIR = os.path.normpath(os.path.join(ROOT, 'db', 'migrations'))
PRECHECK_SQL = os.path.join(MIGR_DIR, '20251225_precheck_melhorias.sql')
INTEGRITY_SQL = os.path.join(MIGR_DIR, '20251225_melhorias_integridade.sql')


def run(cmd, check=True, capture=False, **kwargs):
    print('CMD>', ' '.join(cmd))
    if capture:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs)
    return subprocess.run(cmd, check=check, **kwargs)


def docker_exec(container, cmd_list, capture=False):
    return run(['docker', 'exec', '-i', container] + cmd_list, check=not capture, capture=capture)


def backup_db(container, root_pass, db_name):
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    tmp_path = f'/tmp/backup_pre_migration_{timestamp}.sql'
    host_path = os.path.join(BACKUPS_DIR, f'backup_pre_migration_{timestamp}.sql')
    print('Criando dump no container em', tmp_path)
    # usar sh -c para redirecionamento
    cmd = ['sh', '-c', f"exec mysqldump -uroot -p{root_pass} {db_name} > {tmp_path}"]
    rc = docker_exec(container, cmd)
    if rc.returncode != 0:
        print('Erro ao criar dump no container. Abortando.')
        sys.exit(1)
    print('Copiando dump para host em', host_path)
    run(['docker', 'cp', f'{container}:{tmp_path}', host_path])
    print('Backup salvo em', host_path)
    return host_path


def run_precheck(container, root_pass, db_name, out_file='precheck_resultados.txt'):
    print('Executando precheck...')
    rc = run(['python', os.path.join(SCRIPT_DIR, 'run_precheck.py'), '--container', container, '--root-pass', root_pass, '--db', db_name, '--sql', PRECHECK_SQL, '--out', out_file], check=False)
    if rc.returncode != 0:
        print('Precheck terminou com erro (veja', out_file, '). Continue com cautela.')
    else:
        print('Precheck concluido. Resultado em', out_file)


def generate_saneamento():
    print('Gerando scripts de saneamento...')
    run(['python', os.path.join(SCRIPT_DIR, 'generate_saneamento_sql.py')])


def apply_saneamento(container, root_pass, db_name, apply=False):
    print('Aplicando saneamento (dry-run if not --apply)')
    args = ['python', os.path.join(SCRIPT_DIR, 'apply_saneamento.py'), '--container', container, '--root-pass', root_pass, '--db', db_name]
    if not apply:
        args.append('--dry-run')
    rc = run(args, check=False)
    if rc.returncode != 0:
        print('Erro ao aplicar saneamento. Abortando.')
        sys.exit(1)


def apply_integrity_sql(container, root_pass, db_name, sql_path):
    if not os.path.exists(sql_path):
        print('Arquivo de integridade nao encontrado:', sql_path)
        return False
    print('Aplicando migration de integridade:', sql_path)
    with open(sql_path, 'rb') as f:
        proc = subprocess.run(['docker','exec','-i',container,'mysql','-uroot','-p'+root_pass,db_name], stdin=f)
        return proc.returncode == 0


def run_tests():
    print('Executando pytest...')
    rc = run(['pytest', '-q'], check=False)
    if rc.returncode != 0:
        print('Testes falharam. Veja o output acima.')
    else:
        print('Testes OK')
    return rc.returncode


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--container', default='redeescola_mysql')
    p.add_argument('--root-pass', default='secret')
    p.add_argument('--db', default='redeescola_test')
    p.add_argument('--apply', action='store_true', help='Aplica realmente alteracoes (sem este: dry-run)')
    p.add_argument('--run-tests', action='store_true', help='Roda pytest ao final')
    p.add_argument('--yes', action='store_true', help='Nao pedir confirmacao interativa')
    args = p.parse_args()

    print('\n1) Criar backup do banco (pre-migration)')
    backup_path = backup_db(args.container, args.root_pass, args.db)

    print('\n2) Rodar precheck SQL e salvar resultado')
    run_precheck(args.container, args.root_pass, args.db)

    print('\n3) Gerar scripts de saneamento (sao criados em db/migrations)')
    generate_saneamento()

    print('\nArquivos de saneamento gerados em db/migrations. Revise-os antes de aplicar.')
    if not args.apply and not args.yes:
        print('\nRodando em modo DRY RUN. Use --apply para aplicar as modificacoes.')
    if args.apply and not args.yes:
        ans = input('Voce confirmou que revisou os arquivos e deseja aplicar as alteracoes? (yes/no) ')
        if ans.strip().lower() not in ('yes','y'):
            print('Aborting by user')
            sys.exit(0)

    print('\n4) Aplicar saneamento (vai executar backup scripts e updates)')
    apply_saneamento(args.container, args.root_pass, args.db, apply=args.apply)

    if args.apply:
        print('\n5) Aplicando migrations de integridade (pode falhar se dados invalidos remain)')
        ok = apply_integrity_sql(args.container, args.root_pass, args.db, INTEGRITY_SQL)
        if not ok:
            print('Falha ao aplicar migrations de integridade. Recomendado restaurar backup e analisar precheck. Backup em:', backup_path)
            sys.exit(1)
        print('Migrations de integridade aplicadas com sucesso.')

    if args.run_tests:
        rc = run_tests()
        if rc != 0:
            print('Erros nos testes encontrados. Recomendado reverter e investigar. Backup em:', backup_path)
            sys.exit(rc)

    print('\nFluxo concluido. Backup original em:', backup_path)
    print('Revise o banco e os logs antes de aplicar em ambiente de producao.')

if __name__ == '__main__':
    main()
