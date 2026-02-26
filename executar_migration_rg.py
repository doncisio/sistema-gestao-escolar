import sys
sys.path.insert(0, 'c:/gestao')

from db.connection import get_connection

print("🔧 Executando migration: Adicionar campos RG na tabela funcionarios")
print("=" * 70)

migration_sql = """
-- Adicionar coluna rg
ALTER TABLE funcionarios 
ADD COLUMN IF NOT EXISTS rg VARCHAR(20) DEFAULT NULL AFTER cpf;

-- Adicionar coluna orgao_expedidor
ALTER TABLE funcionarios 
ADD COLUMN IF NOT EXISTS orgao_expedidor VARCHAR(50) DEFAULT NULL AFTER rg;

-- Adicionar coluna data_expedicao_rg
ALTER TABLE funcionarios 
ADD COLUMN IF NOT EXISTS data_expedicao_rg DATE DEFAULT NULL AFTER orgao_expedidor;
"""

try:
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Executar cada comando separadamente
        for statement in migration_sql.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    print(f"✓ Executado: {statement[:50]}...")
                except Exception as e:
                    # Se der erro porque já existe, continuar
                    if "Duplicate column name" in str(e) or "duplicate" in str(e).lower():
                        print(f"⏭️  Coluna já existe")
                    else:
                        print(f"❌ Erro: {e}")
                        raise
        
        conn.commit()
        print("\n" + "=" * 70)
        print("✅ Migration executada com sucesso!")
        print()
        
        # Verificar resultado
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'funcionarios'
                AND COLUMN_NAME IN ('rg', 'orgao_expedidor', 'data_expedicao_rg')
            ORDER BY ORDINAL_POSITION
        """)
        
        colunas = cursor.fetchall()
        
        if colunas:
            print("📋 Colunas adicionadas:")
            print("-" * 70)
            for col in colunas:
                print(f"   • {col[0]:25} | Tipo: {col[1]:15} | Null: {col[2]:3} | Default: {col[3]}")
            print("-" * 70)
        else:
            print("⚠️  Nenhuma coluna encontrada - pode já existir com outro nome")
        
except Exception as e:
    print(f"\n❌ ERRO ao executar migration: {e}")
    sys.exit(1)

print("\n✅ Processo concluído!")
