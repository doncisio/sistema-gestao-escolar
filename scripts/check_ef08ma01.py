#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar conteúdo da habilidade EF08MA01
"""

import mysql.connector
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Conecta ao banco
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    charset='utf8mb4'
)

cursor = conn.cursor(dictionary=True)

# Busca o registro
cursor.execute('''
    SELECT codigo, descricao, LENGTH(descricao) as len 
    FROM bncc_habilidades 
    WHERE codigo = 'EF08MA01'
''')

row = cursor.fetchone()

if row:
    print(f"Código: {row['codigo']}")
    print(f"Descrição ({row['len']} caracteres):")
    print(row['descricao'])
else:
    print("Registro não encontrado")

cursor.close()
conn.close()
