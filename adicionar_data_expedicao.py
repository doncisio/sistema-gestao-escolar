import sys
sys.path.insert(0, 'c:/gestao')

import mysql.connector
from db.connection import _get_db_config

print("🔧 Adicionando coluna data_expedicao_rg")

try:
    db_config = _get_db_config()
    conn = mysql.connector.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )
    cursor = conn.cursor()
    
    print("✓ Conectado")
    
    try:
        cursor.execute("ALTER TABLE funcionarios ADD COLUMN data_expedicao_rg DATE DEFAULT NULL")
        conn.commit()
        print("✅ Coluna 'data_expedicao_rg' adicionada com sucesso!")
    except mysql.connector.Error as e:
        if e.errno == 1060:
            print("⏭️  Coluna já existe")
        else:
            print(f"❌ Erro: {e}")
            raise
    
    # Verificar
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
          AND TABLE_NAME = 'funcionarios' 
          AND COLUMN_NAME IN ('rg', 'orgao_expedidor', 'data_expedicao_rg')
    """)
    
    print("\n✅ Colunas RG na tabela:")
    for col in cursor.fetchall():
        print(f"   • {col[0]:25} | {col[1]}")
    
    cursor.close()
    conn.close()
    print("\n✅ Concluído!")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    sys.exit(1)
