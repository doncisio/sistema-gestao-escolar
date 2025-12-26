#!/usr/bin/env python3
"""Executa um arquivo SQL de precheck dentro do container MySQL e salva output.
Uso: python run_precheck.py --container redeescola_mysql --root-pass secret --db redeescola_test --sql ../../db/migrations/20251225_precheck_melhorias.sql
"""
import argparse
import subprocess
import sys


def run_sql_in_container(container, root_pass, db, sql_path, out_path):
    with open(sql_path,'rb') as f, open(out_path,'wb') as out:
        proc = subprocess.run(['docker','exec','-i',container,'mysql','-uroot','-p'+root_pass,db], stdin=f, stdout=out, stderr=subprocess.STDOUT)
        return proc.returncode


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--container', default='redeescola_mysql')
    p.add_argument('--root-pass', default='secret')
    p.add_argument('--db', default='redeescola_test')
    p.add_argument('--sql', required=True)
    p.add_argument('--out', default='precheck_resultados.txt')
    args = p.parse_args()

    print('Executando precheck...')
    rc = run_sql_in_container(args.container, args.root_pass, args.db, args.sql, args.out)
    if rc == 0:
        print('Precheck executado, resultado em', args.out)
    else:
        print('Erro (code', rc, ') ao executar precheck. Ver', args.out)
        sys.exit(rc)

if __name__ == '__main__':
    main()
