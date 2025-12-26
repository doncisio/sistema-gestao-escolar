#!/usr/bin/env python3
"""Aplica os scripts de saneamento gerados em db/migrations no container MySQL.
Uso: python apply_saneamento.py --container redeescola_mysql --root-pass secret --db redeescola_test [--dry-run]
"""
import argparse
import glob
import subprocess
import os
import sys

MIGR_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'migrations'))
SANE_FILES = [
    'saneamento_backup_turmas.sql',
    'saneamento_turmas.sql',
    'saneamento_backup_notas_duplicadas.sql',
    'saneamento_notas_duplicadas.sql',
    'saneamento_backup_matriculas.sql',
    'saneamento_matriculas_data.sql'
]


def run_file_in_container(container, root_pass, db, file_path):
    with open(file_path, 'rb') as f:
        proc = subprocess.run(['docker','exec','-i',container,'mysql','-uroot','-p'+root_pass,db], stdin=f)
        return proc.returncode


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--container', default='redeescola_mysql')
    p.add_argument('--root-pass', default='secret')
    p.add_argument('--db', default='redeescola_test')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    for fname in SANE_FILES:
        path = os.path.join(MIGR_DIR, fname)
        if not os.path.exists(path):
            print('Aviso: arquivo nao encontrado, pulando', path)
            continue
        print('\n-- Aplicando', fname)
        if args.dry_run:
            print('DRY RUN: mostrar primeiras linhas do arquivo:')
            with open(path,'r',encoding='utf-8') as f:
                for i,l in enumerate(f):
                    if i>20:
                        break
                    print(l.rstrip())
            continue
        rc = run_file_in_container(args.container, args.root_pass, args.db, path)
        if rc != 0:
            print('Erro ao aplicar', fname, 'codigo', rc)
            sys.exit(rc)
        print('Concluido', fname)

    print('\nSaneamento finalizado. Verifique se os prechecks agora retornam resultados limpos e tente aplicar as migrations de integridade.')

if __name__ == '__main__':
    main()
