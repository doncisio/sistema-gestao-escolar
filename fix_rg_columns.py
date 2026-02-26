#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'c:/gestao')

import mysql.connector
from db.connection import _get_db_config

print("🔧 Adicionando colunas RG à tabela funcionarios")
print("=" * 70)

try:
    # Obter configuração do banco
    db_config = _get_db_config()
    
    # Conectar diretamente
    conn = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )
    cursor = conn.cursor()
    
    print("✓ Conectado ao banco de dados")
    print()
    
    # Lista de comandos ALTER TABLE
    comandos = [
        ("rg", "ALTER TABLE funcionarios ADD COLUMN rg VARCHAR(20) DEFAULT NULL"),
        ("orgao_expedidor", "ALTER TABLE funcionarios ADD COLUMN orgao_expedidor VARCHAR(50) DEFAULT NULL"),
        ("data_expedicao_rg", "ALTER TABLE funcionarios ADD COLUMN data_expedicao_rg DATE DEFAULT NULL")
    ]
    
    for nome_coluna, sql in comandos:
        try:
            print(f"📝 Adicionando coluna '{nome_coluna}'...", end=" ", flush=True)
            cursor.execute(sql)
            conn.commit()
            print("✓")
        except mysql.connector.Error as e:
            if e.errno == 1060:  # Duplicate column name
                print("⏭️  (já existe)")
            else:
                print(f"\n❌ Erro: {e}")
                raise
    
    print()
    print("=" * 70)
    
    # Verificar
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'funcionarios'
          AND COLUMN_NAME IN ('rg', 'orgao_expedidor', 'data_expedicao_rg')
        ORDER BY ORDINAL_POSITION
    """)
    
    colunas = cursor.fetchall()
    
    if colunas:
        print("✅ Colunas verificadas:")
        for col in colunas:
            print(f"   • {col[0]:25} | {col[1]:15} | Null: {col[2]}")
        print()
        print("✅ Sucesso! As colunas foram adicionadas.")
    else:
        print("⚠️  Aviso: Nenhuma coluna encontrada na verificação")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
