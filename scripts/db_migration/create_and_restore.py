#!/usr/bin/env python3
"""Cria container MySQL e restaura dump.
Uso: python create_and_restore.py --dump /path/backup.sql --container redeescola_mysql --root-pass secret --db redeescola_test
"""
import argparse
import subprocess
import time
import os
import sys


def run(cmd, check=True, capture=False, stdin=None):
    if capture:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=stdin)
    return subprocess.run(cmd, check=check, stdin=stdin)


def wait_mysql(container, root_pass, timeout=60):
    start = time.time()
    while True:
        try:
            r = run(['docker','exec',container,'mysqladmin','ping','-uroot','-p'+root_pass], check=False, capture=True)
            out = r.stdout.decode('utf-8', errors='ignore') if r.stdout else ''
            if 'mysqld is alive' in out or 'server is alive' in out:
                return True
        except Exception:
            pass
        if time.time() - start > timeout:
            return False
        time.sleep(2)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dump', required=True, help='Caminho local para o dump SQL')
    p.add_argument('--container', default='redeescola_mysql')
    p.add_argument('--root-pass', default='secret')
    p.add_argument('--db', default='redeescola_test')
    p.add_argument('--port', default='3307')
    p.add_argument('--keep', action='store_true', help='Nao remover container se ja existir')
    args = p.parse_args()

    # Se container existe, perguntar ou remover
    existing = subprocess.run(['docker','ps','-a','--filter','name='+args.container,'--format','{{.Names}}'], stdout=subprocess.PIPE)
    if existing.stdout.decode().strip():
        if args.keep:
            print(f"Container {args.container} já existe, seguindo com ele (assume configurado)")
        else:
            print(f"Removendo container existente {args.container}")
            run(['docker','rm','-f',args.container])

    print('Iniciando container MySQL...')
    run(['docker','run','-d','--name',args.container,'-e',f'MYSQL_ROOT_PASSWORD={args.root_pass}','-e',f'MYSQL_DATABASE={args.db}','-p',f'{args.port}:3306','mysql:8.0'])

    print('Aguardando MySQL ficar pronto...')
    if not wait_mysql(args.container, args.root_pass, timeout=120):
        print('Timeout aguardando MySQL. Cheque logs do container.')
        print('Logs:')
        run(['docker','logs',args.container])
        sys.exit(2)

    # Restaurar dump
    if not os.path.exists(args.dump):
        print('Arquivo de dump nao encontrado:', args.dump)
        sys.exit(1)

    print('Copiando dump para container...')
    run(['docker','cp',args.dump,f'{args.container}:/tmp/backup_redeescola.sql'])

    print('Restaurando dump (pode demorar)...')
    with open(args.dump, 'rb') as f:
        r = subprocess.run(['docker','exec','-i',args.container,'mysql','-uroot','-p'+args.root_pass,args.db], stdin=f)
        if r.returncode != 0:
            print('Erro na restauracao, codigo', r.returncode)
            sys.exit(3)

    print('Restauração concluída. Você pode rodar agora os prechecks.')

if __name__ == '__main__':
    main()
