import sys
sys.path.insert(0, 'c:/gestao')

from db.connection import get_connection

print("🔍 Verificando estrutura da tabela funcionarios")
print("=" * 70)

try:
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar se as colunas já existem
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'funcionarios'
                AND COLUMN_NAME IN ('rg', 'orgao_expedidor', 'data_expedicao_rg')
            ORDER BY ORDINAL_POSITION
        """)
        
        colunas_existentes = [row[0] for row in cursor.fetchall()]
        
        print(f"Colunas existentes: {colunas_existentes if colunas_existentes else 'Nenhuma'}")
        print()
        
        # Adicionar colunas que não existem
        colunas_para_adicionar = []
        
        if 'rg' not in colunas_existentes:
            colunas_para_adicionar.append(('rg', "ADD COLUMN rg VARCHAR(20) DEFAULT NULL AFTER cpf"))
        
        if 'orgao_expedidor' not in colunas_existentes:
            pos = "AFTER rg" if 'rg' in colunas_existentes or 'rg' in [c[0] for c in colunas_para_adicionar] else "AFTER cpf"
            colunas_para_adicionar.append(('orgao_expedidor', f"ADD COLUMN orgao_expedidor VARCHAR(50) DEFAULT NULL {pos}"))
        
        if 'data_expedicao_rg' not in colunas_existentes:
            pos = "AFTER orgao_expedidor" if 'orgao_expedidor' in colunas_existentes or 'orgao_expedidor' in [c[0] for c in colunas_para_adicionar] else "AFTER cpf"
            colunas_para_adicionar.append(('data_expedicao_rg', f"ADD COLUMN data_expedicao_rg DATE DEFAULT NULL {pos}"))
        
        if colunas_para_adicionar:
            print(f"📝 Adicionando {len(colunas_para_adicionar)} colunas...")
            print()
            
            for nome_coluna, alter_statement in colunas_para_adicionar:
                try:
                    sql = f"ALTER TABLE funcionarios {alter_statement}"
                    print(f"Executando: {sql}")
                    cursor.execute(sql)
                    conn.commit()
                    print(f"✓ Coluna '{nome_coluna}' adicionada com sucesso!")
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        print(f"⏭️  Coluna '{nome_coluna}' já existe")
                    else:
                        print(f"❌ Erro ao adicionar '{nome_coluna}': {e}")
                        raise
            
            print()
        else:
            print("✓ Todas as colunas já existem!")
            print()
        
        # Verificar resultado final
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'funcionarios'
                AND COLUMN_NAME IN ('cpf', 'rg', 'orgao_expedidor', 'data_expedicao_rg')
            ORDER BY ORDINAL_POSITION
        """)
        
        colunas = cursor.fetchall()
        
        print("=" * 70)
        print("📋 Estrutura final das colunas relacionadas a documentos:")
        print("-" * 70)
        for col in colunas:
            default = col[3] if col[3] is not None else 'NULL'
            print(f"   • {col[0]:25} | {col[1]:15} | Null: {col[2]:3} | Default: {default}")
        print("-" * 70)
        
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ Verificação concluída!")
