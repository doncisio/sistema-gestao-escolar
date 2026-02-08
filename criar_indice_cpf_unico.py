"""
Script para criar índice UNIQUE no campo CPF da tabela Alunos
Previne CPFs duplicados no futuro
"""

from db.connection import conectar_bd

def criar_indice_unico():
    conn = conectar_bd()
    if not conn:
        print("Erro ao conectar ao banco de dados!")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    print("="*80)
    print("CRIANDO INDICE UNIQUE NO CAMPO CPF")
    print("="*80)
    
    try:
        # 1. Verificar se já existe o índice
        print("\n[1/3] Verificando se o indice ja existe...")
        cursor.execute("""
            SHOW INDEX FROM Alunos WHERE Key_name = 'idx_cpf_unico'
        """)
        
        indice_existente = cursor.fetchone()
        
        if indice_existente:
            print("      AVISO: Indice 'idx_cpf_unico' ja existe!")
            print("      Nenhuma acao necessaria.")
            return
        
        print("      Indice nao existe. Prosseguindo...")
        
        # 2. Verificar se há CPFs duplicados
        print("\n[2/3] Verificando CPFs duplicados...")
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM (
                SELECT cpf
                FROM Alunos
                WHERE cpf IS NOT NULL AND cpf != ''
                GROUP BY cpf
                HAVING COUNT(*) > 1
            ) as duplicados
        """)
        
        duplicados = cursor.fetchone()['total']
        
        if duplicados > 0:
            print(f"      ERRO: {duplicados} CPFs duplicados encontrados!")
            print("      Execute primeiro: python detectar_erros_comparacao.py")
            print("      Para resolver as duplicatas antes de criar o indice.")
            return
        
        print("      OK: Nenhum CPF duplicado encontrado")
        
        # 3. Criar o índice
        print("\n[3/3] Criando indice UNIQUE...")
        cursor.execute("""
            CREATE UNIQUE INDEX idx_cpf_unico ON Alunos(cpf)
        """)
        
        print("      Indice criado com sucesso!")
        
        # Verificar criação
        cursor.execute("""
            SHOW INDEX FROM Alunos WHERE Key_name = 'idx_cpf_unico'
        """)
        
        indice = cursor.fetchone()
        
        print("\n" + "="*80)
        print("INDICE UNIQUE CRIADO COM SUCESSO!")
        print("="*80)
        
        print(f"\nDetalhes do indice:")
        print(f"  Nome: {indice['Key_name']}")
        print(f"  Tabela: {indice['Table']}")
        print(f"  Coluna: {indice['Column_name']}")
        print(f"  Tipo: UNIQUE")
        
        print("\n" + "="*80)
        print("PROTECAO ATIVADA!")
        print("="*80)
        
        print("""
A partir de agora:
  - Nao sera possivel cadastrar CPFs duplicados
  - Tentativas de duplicacao retornarao erro
  - Multiplos alunos podem ter cpf = NULL
  - Sistema esta protegido contra erros de digitacao
        """)
        
    except Exception as e:
        print(f"\nERRO ao criar indice: {e}")
        print("\nPossivel causa:")
        print("  - CPFs duplicados ainda existem no banco")
        print("  - String vazia '' ao inves de NULL")
        print("\nSolucao:")
        print("  1. Execute: python corrigir_cpfs_vazios.py")
        print("  2. Execute: python detectar_erros_comparacao.py")
        print("  3. Resolva as duplicatas")
        print("  4. Tente criar o indice novamente")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("\nEste script vai criar um indice UNIQUE no campo CPF")
    print("Isso vai impedir CPFs duplicados no futuro")
    
    resposta = input("\nDeseja continuar? (sim/nao): ").strip().lower()
    
    if resposta in ['sim', 's', 'yes', 'y']:
        criar_indice_unico()
    else:
        print("\nOperacao cancelada pelo usuario.")
