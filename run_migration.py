#!/usr/bin/env python3
"""
Run a SQL migration file against a MySQL database.

Usage examples:
  python run_migration.py --host localhost --user doncisio --database redeescola 
  (you will be interactively prompted for the password)

  python run_migration.py --file C:\gestao\migration_bncc_parsed_fields.sql --user doncisio --database redeescola

The script will execute the SQL file using mysql-connector-python with multi statement support.
"""
import argparse
import getpass
import os
import sys
import mysql.connector
from mysql.connector import errorcode


def run_sql_file(host, user, password, database, file_path, port=3306):
    if not os.path.exists(file_path):
        print(f"Arquivo SQL não encontrado: {file_path}")
        return 1

    with open(file_path, 'r', encoding='utf8') as f:
        sql = f.read()

    try:
        conn = mysql.connector.connect(host=host, user=user, password=password, database=database, port=port, charset='utf8mb4')
    except mysql.connector.Error as err:
        print(f"Erro conectando ao banco: {err}")
        return 2

    try:
        cursor = conn.cursor()
        print("Iniciando execução do arquivo SQL (multi statements)...")
        for result in cursor.execute(sql, multi=True):
            try:
                if result.with_rows:
                    _ = result.fetchall()
                print(f"Executado: {result.statement[:80]}{'...' if len(result.statement) > 80 else ''} -> OK")
            except mysql.connector.Error as e:
                print(f"Erro ao executar statement: {e}")
                conn.rollback()
                cursor.close()
                conn.close()
                return 3

        conn.commit()
        cursor.close()
        conn.close()
        print("Migration executada com sucesso.")
        return 0

    except mysql.connector.Error as err:
        print(f"Erro durante execução: {err}")
        try:
            conn.rollback()
        except Exception:
            pass
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass
        return 4


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Executa um arquivo SQL de migration no MySQL')
    parser.add_argument('--host', default='localhost', help='Host MySQL')
    parser.add_argument('--port', type=int, default=3306, help='Porta MySQL')
    parser.add_argument('--user', required=True, help='Usuário MySQL')
    parser.add_argument('--database', required=True, help='Banco de dados alvo')
    parser.add_argument('--file', default=r'C:\gestao\migration_bncc_parsed_fields.sql', help='Caminho do arquivo SQL')
    parser.add_argument('--password', help='Senha MySQL (não recomendado em CLI)')

    args = parser.parse_args()

    pwd = args.password
    if not pwd:
        pwd = getpass.getpass(prompt=f"Senha para {args.user}@{args.host}: ")

    print(f"Arquivo SQL: {args.file}")
    print("Recomendado: faça backup do banco antes de prosseguir. Deseja continuar? [y/N]", end=' ')
    confirm = input().strip().lower()
    if confirm not in ('y', 'yes'):
        print("Abortando. Faça um backup e execute novamente quando pronto.")
        sys.exit(1)

    rc = run_sql_file(args.host, args.user, pwd, args.database, args.file, port=args.port)
    sys.exit(rc)
