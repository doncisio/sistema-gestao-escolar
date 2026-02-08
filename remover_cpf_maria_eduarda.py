"""
Script para remover CPF incorreto de Maria Eduarda Cordeiro dos Santos
ID: 598
CPF incorreto: 63484635320 (pertence a outra pessoa)
"""

from db.connection import conectar_bd

def remover_cpf_incorreto():
    conn = conectar_bd()
    if not conn:
        print("Erro ao conectar ao banco de dados!")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    id_aluno = 598
    cpf_incorreto = '63484635320'
    
    print("="*80)
    print("REMOVENDO CPF INCORRETO DE MARIA EDUARDA CORDEIRO DOS SANTOS")
    print("="*80)
    print(f"\nID do aluno: {id_aluno}")
    print(f"CPF incorreto: {cpf_incorreto}")
    print()
    
    try:
        # 1. Verificar dados atuais
        print("[1/3] Verificando dados atuais...")
        cursor.execute("""
            SELECT id, nome, cpf, data_nascimento, sexo
            FROM Alunos
            WHERE id = %s
        """, (id_aluno,))
        
        aluno = cursor.fetchone()
        
        if not aluno:
            print(f"ERRO: Aluno com ID {id_aluno} nao encontrado!")
            return
        
        print(f"      Nome: {aluno['nome']}")
        print(f"      CPF atual: {aluno['cpf']}")
        print(f"      Nascimento: {aluno['data_nascimento']}")
        print(f"      Sexo: {aluno['sexo']}")
        
        # 2. Verificar quem tem o CPF correto
        print(f"\n[2/3] Verificando quem mais tem o CPF {cpf_incorreto}...")
        cursor.execute("""
            SELECT id, nome, cpf, data_nascimento
            FROM Alunos
            WHERE cpf = %s
            ORDER BY id
        """, (cpf_incorreto,))
        
        alunos_com_cpf = cursor.fetchall()
        print(f"      {len(alunos_com_cpf)} alunos com este CPF:")
        for a in alunos_com_cpf:
            print(f"        ID {a['id']}: {a['nome']} (Nasc: {a['data_nascimento']})")
        
        # 3. Remover CPF do ID 598
        print(f"\n[3/3] Removendo CPF incorreto do ID {id_aluno}...")
        cursor.execute("""
            UPDATE Alunos 
            SET cpf = NULL 
            WHERE id = %s
        """, (id_aluno,))
        
        print(f"      CPF removido ({cursor.rowcount} registro atualizado)")
        
        # Commit das alterações
        conn.commit()
        
        print("\n" + "="*80)
        print("REMOCAO CONCLUIDA COM SUCESSO!")
        print("="*80)
        print(f"\nAluno ID {id_aluno}: CPF removido temporariamente")
        print(f"CPF {cpf_incorreto} agora pertence apenas a:")
        
        # Verificar resultado final
        cursor.execute("""
            SELECT id, nome, cpf
            FROM Alunos
            WHERE cpf = %s
        """, (cpf_incorreto,))
        
        resultado = cursor.fetchall()
        for r in resultado:
            print(f"  ID {r['id']}: {r['nome']}")
        
        # Verificar o aluno que teve o CPF removido
        cursor.execute("""
            SELECT id, nome, cpf
            FROM Alunos
            WHERE id = %s
        """, (id_aluno,))
        
        aluno_atualizado = cursor.fetchone()
        print(f"\nAluno ID {id_aluno}:")
        print(f"  Nome: {aluno_atualizado['nome']}")
        print(f"  CPF: {aluno_atualizado['cpf'] or 'NAO CADASTRADO (aguardando documento correto)'}")
        
        if len(resultado) == 1:
            print(f"\nOK: Conflito de CPF resolvido!")
            print(f"\nVERIFICANDO SE AINDA HA CPFS DUPLICADOS...")
            
            # Verificar se ainda há CPFs duplicados no sistema
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
            
            total_duplicados = cursor.fetchone()['total']
            
            if total_duplicados == 0:
                print("\n" + "="*80)
                print("PARABENS! TODOS OS CPFS DUPLICADOS FORAM RESOLVIDOS!")
                print("="*80)
                print("\nO sistema agora esta pronto para:")
                print("  1. Implementar indice unico no campo CPF")
                print("  2. Importar dados do GEDUC com seguranca")
                print("  3. Validacao automatica de CPF no cadastro")
            else:
                print(f"\nAinda existem {total_duplicados} CPFs duplicados no sistema")
        
    except Exception as e:
        print(f"\nERRO durante a remocao: {e}")
        conn.rollback()
        print("Alteracoes revertidas (ROLLBACK)")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("\nATENCAO: Este script vai remover o CPF incorreto do aluno ID 598")
    print("O CPF ficara NULL ate que o documento correto seja apresentado")
    
    resposta = input("\nDeseja continuar? (sim/nao): ").strip().lower()
    
    if resposta in ['sim', 's', 'yes', 'y']:
        remover_cpf_incorreto()
    else:
        print("\nOperacao cancelada pelo usuario.")
