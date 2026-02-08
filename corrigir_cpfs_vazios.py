"""
Script para corrigir CPFs vazios (string vazia) convertendo para NULL
Necessário antes de criar o índice UNIQUE
"""

from db.connection import conectar_bd

def corrigir_cpfs_vazios():
    conn = conectar_bd()
    if not conn:
        print("Erro ao conectar ao banco de dados!")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    print("="*80)
    print("CORRIGINDO CPFs COM STRING VAZIA PARA NULL")
    print("="*80)
    
    try:
        # 1. Verificar quantos registros têm cpf = ''
        print("\n[1/3] Verificando registros com cpf = '' (string vazia)...")
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Alunos
            WHERE cpf = ''
        """)
        total_vazios = cursor.fetchone()['total']
        
        print(f"      {total_vazios} registros com cpf = '' (string vazia)")
        
        if total_vazios == 0:
            print("\n      Nenhum registro para corrigir!")
            print("      Pode criar o indice UNIQUE diretamente.")
            return
        
        # 2. Mostrar alguns exemplos
        print("\n[2/3] Exemplos de registros afetados:")
        cursor.execute("""
            SELECT id, nome
            FROM Alunos
            WHERE cpf = ''
            LIMIT 5
        """)
        
        exemplos = cursor.fetchall()
        for ex in exemplos:
            print(f"      ID {ex['id']}: {ex['nome']}")
        
        if total_vazios > 5:
            print(f"      ... e mais {total_vazios - 5} registros")
        
        # 3. Converter '' para NULL
        print(f"\n[3/3] Convertendo cpf = '' para cpf = NULL...")
        cursor.execute("""
            UPDATE Alunos
            SET cpf = NULL
            WHERE cpf = ''
        """)
        
        registros_atualizados = cursor.rowcount
        print(f"      {registros_atualizados} registros atualizados")
        
        # Commit
        conn.commit()
        
        print("\n" + "="*80)
        print("CORRECAO CONCLUIDA COM SUCESSO!")
        print("="*80)
        
        # Verificar resultado
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Alunos
            WHERE cpf = ''
        """)
        ainda_vazios = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Alunos
            WHERE cpf IS NULL
        """)
        agora_null = cursor.fetchone()['total']
        
        print(f"\nRegistros com cpf = '': {ainda_vazios}")
        print(f"Registros com cpf = NULL: {agora_null}")
        
        if ainda_vazios == 0:
            print("\n" + "="*80)
            print("AGORA PODE CRIAR O INDICE UNIQUE COM SEGURANCA!")
            print("="*80)
            print("\nComando:")
            print("  CREATE UNIQUE INDEX idx_cpf_unico ON Alunos(cpf);")
            print("\nOu execute o script: criar_indice_cpf_unico.py")
        
    except Exception as e:
        print(f"\nERRO durante a correcao: {e}")
        conn.rollback()
        print("Alteracoes revertidas (ROLLBACK)")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("\nEste script vai converter todos os CPFs vazios (string vazia) para NULL")
    print("Isso e necessario para criar o indice UNIQUE no campo CPF")
    
    resposta = input("\nDeseja continuar? (sim/nao): ").strip().lower()
    
    if resposta in ['sim', 's', 'yes', 'y']:
        corrigir_cpfs_vazios()
    else:
        print("\nOperacao cancelada pelo usuario.")
