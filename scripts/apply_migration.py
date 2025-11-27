#!/usr/bin/env python3
"""
Script para aplicar migration SQL usando credenciais do .env
"""
import sys
from pathlib import Path
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv('.env')

if len(sys.argv) < 2:
    print("Uso: python apply_migration.py <arquivo.sql>")
    sys.exit(1)

sql_file = Path(sys.argv[1])
if not sql_file.exists():
    print(f"Arquivo não encontrado: {sql_file}")
    sys.exit(1)

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST','localhost'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME','redeescola')
)

cursor = conn.cursor()

print(f"Executando migration: {sql_file.name}")
print("=" * 60)

with open(sql_file, 'r', encoding='utf8') as f:
    sql_content = f.read()

# Executar em blocos separados por ';'
statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

for i, stmt in enumerate(statements, 1):
    if stmt.upper().startswith('USE'):
        continue
    try:
        print(f"[{i}/{len(statements)}] Executando: {stmt[:60]}...")
        cursor.execute(stmt)
        conn.commit()
        print(f"  ✓ OK")
    except Exception as e:
        print(f"  ✗ ERRO: {e}")
        conn.rollback()

cursor.close()
conn.close()
print("=" * 60)
print("Migration concluída.")
