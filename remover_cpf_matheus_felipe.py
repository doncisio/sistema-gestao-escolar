"""
Script para remover CPF incorreto de Matheus Felipe Vale Araujo
ID: 601
CPF incorreto: 63257966326 (pertence a outra pessoa)
"""

from db.connection import conectar_bd

def remover_cpf_incorreto():
    conn = conectar_bd()
    if not conn:
        print("Erro ao conectar ao banco de dados!")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    id_aluno = 601
    cpf_incorreto = '63257966326'
    
    print("="*80)
    print("REMOVENDO CPF INCORRETO DE MATHEUS FELIPE VALE ARAUJO")
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
        
        # 3. Remover CPF do ID 601
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
        
    except Exception as e:
        print(f"\nERRO durante a remocao: {e}")
        conn.rollback()
        print("Alteracoes revertidas (ROLLBACK)")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("\nATENCAO: Este script vai remover o CPF incorreto do aluno ID 601")
    print("O CPF ficara NULL ate que o documento correto seja apresentado")
    
    resposta = input("\nDeseja continuar? (sim/nao): ").strip().lower()
    
    if resposta in ['sim', 's', 'yes', 'y']:
        remover_cpf_incorreto()
    else:
        print("\nOperacao cancelada pelo usuario.")
