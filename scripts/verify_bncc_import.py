#!/usr/bin/env python3
"""Script rápido para verificar estatísticas da importação BNCC"""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv('.env')

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST','localhost'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME','redeescola')
)

c = conn.cursor()

c.execute('SELECT COUNT(*) FROM bncc_habilidades')
r = c.fetchone()
print(f'Total habilidades: {r[0] if r and r[0] is not None else 0}')

c.execute('SELECT COUNT(*) FROM bncc_prerequisitos')
r = c.fetchone()
print(f'Total pré-requisitos: {r[0] if r and r[0] is not None else 0}')

c.execute('SELECT COUNT(*) FROM bncc_habilidades WHERE conhecimento_previo IS NOT NULL AND conhecimento_previo != ""')
r = c.fetchone()
print(f'Habilidades com conhecimento_previo preenchido: {r[0] if r and r[0] is not None else 0}')

c.execute('''
    SELECT etapa_sigla, componente_codigo, COUNT(*) as cnt 
    FROM bncc_habilidades 
    GROUP BY etapa_sigla, componente_codigo 
    ORDER BY etapa_sigla, componente_codigo
''')
print('\nDistribuição por etapa e componente:')
for row in c.fetchall():
    print(f'  {row[0] or "?"}-{row[1] or "?"}: {row[2]}')

c.execute('''
    SELECT COUNT(*) FROM bncc_prerequisitos WHERE prereq_bncc_id IS NOT NULL
''')
r = c.fetchone()
print(f'\nPré-requisitos com ID resolvido: {r[0] if r and r[0] is not None else 0}')

conn.close()
print('\n✓ Verificação concluída.')
