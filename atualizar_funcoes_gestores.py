import sys
sys.path.insert(0, 'c:/gestao')

from db.connection import get_connection

# Atualizar funções dos gestores
with get_connection() as conn:
    cursor = conn.cursor()
    
    try:
        # Atualizar Leandro para Gestor Geral
        cursor.execute("""
            UPDATE funcionarios 
            SET funcao = 'Gestor Geral'
            WHERE id = 243
            AND nome = 'Leandro Fonseca Lima'
        """)
        
        # Atualizar Rosiane para Gestora Adjunta
        cursor.execute("""
            UPDATE funcionarios 
            SET funcao = 'Gestora Adjunta'
            WHERE id = 202
            AND nome = 'Rosiane de Jesus Santos Melo'
        """)
        
        conn.commit()
        
        print("✓ Funções atualizadas com sucesso!")
        print()
        
        # Verificar resultado
        cursor.execute("""
            SELECT id, nome, cargo, funcao 
            FROM funcionarios 
            WHERE id IN (202, 243)
            ORDER BY 
                CASE WHEN funcao LIKE '%Geral%' THEN 1 
                     WHEN funcao LIKE '%Adjunt%' THEN 2 
                     ELSE 3 
                END
        """)
        
        print("Gestores atualizados:")
        print("-" * 80)
        print(f"{'ID':<5} {'Nome':<40} {'Cargo':<20} {'Função':<15}")
        print("-" * 80)
        for g in cursor.fetchall():
            funcao = g[3] if g[3] else "Não definida"
            print(f"{g[0]:<5} {g[1]:<40} {g[2]:<20} {funcao:<15}")
        print("-" * 80)
        
        cursor.close()
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Erro ao atualizar: {e}")
