import sys
import time
sys.path.insert(0, 'c:/gestao')

from db.connection import get_connection

print("🔧 Adicionando colunas RG à tabela funcionarios")
print("=" * 70)

comandos = [
    ("rg", "ALTER TABLE funcionarios ADD COLUMN rg VARCHAR(20) DEFAULT NULL"),
    ("orgao_expedidor", "ALTER TABLE funcionarios ADD COLUMN orgao_expedidor VARCHAR(50) DEFAULT NULL"),
    ("data_expedicao_rg", "ALTER TABLE funcionarios ADD COLUMN data_expedicao_rg DATE DEFAULT NULL")
]

try:
    conn = get_connection()
    cursor = conn.cursor()
    
    print("📋 Verificando colunas existentes...")
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
          AND TABLE_NAME = 'funcionarios'
    """)
    colunas_existentes = {row[0] for row in cursor.fetchall()}
    print(f"   Total de colunas na tabela: {len(colunas_existentes)}")
    print()
    
    adicionadas = 0
    ja_existiam = 0
    
    for nome_coluna, sql in comandos:
        if nome_coluna in colunas_existentes:
            print(f"⏭️  Coluna '{nome_coluna}' já existe - pulando")
            ja_existiam += 1
        else:
            try:
                print(f"📝 Adicionando coluna '{nome_coluna}'...", end=" ", flush=True)
                cursor.execute(sql)
                conn.commit()
                print("✓")
                adicionadas += 1
                time.sleep(0.5)  # Pequena pausa entre comandos
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("⏭️  (já existe)")
                    ja_existiam += 1
                else:
                    print(f"❌ ERRO: {e}")
                    raise
    
    print()
    print("=" * 70)
    print(f"✅ Resumo:")
    print(f"   • Colunas adicionadas: {adicionadas}")
    print(f"   • Já existiam: {ja_existiam}")
    print()
    
    # Verificar resultado final
    print("📋 Verificação final:")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'funcionarios'
          AND COLUMN_NAME IN ('cpf', 'rg', 'orgao_expedidor', 'data_expedicao_rg')
        ORDER BY ORDINAL_POSITION
    """)
    
    colunas = cursor.fetchall()
    for col in colunas:
        default = col[3] if col[3] is not None else 'NULL'
        print(f"   • {col[0]:25} | {col[1]:15} | Null: {col[2]:3}")
    
    cursor.close()
    conn.close()
    print()
    print("✅ Processo concluído com sucesso!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
