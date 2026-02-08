"""
Script para excluir duplicata de Carlos Matheus de Jesus Santos
ID a excluir: 2807
ID principal a manter: 2808
"""

from db.connection import conectar_bd

def executar_exclusao():
    conn = conectar_bd()
    if not conn:
        print("Erro ao conectar ao banco de dados!")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    id_remover = 2807
    id_manter = 2808
    
    print("="*80)
    print("EXCLUINDO DUPLICATA DE CARLOS MATHEUS DE JESUS SANTOS")
    print("="*80)
    print(f"\nID principal (manter): {id_manter}")
    print(f"ID duplicado (excluir): {id_remover}")
    print()
    
    try:
        # 1. Verificar vínculos
        print("\n[1/5] Verificando matriculas...")
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM Matriculas 
            WHERE aluno_id = %s
        """, (id_remover,))
        total_matriculas = cursor.fetchone()['total']
        print(f"      Matriculas vinculadas ao ID {id_remover}: {total_matriculas}")
        
        # 2. Transferir matrículas se houver
        if total_matriculas > 0:
            print("\n[2/5] Transferindo matriculas para o ID principal...")
            cursor.execute("""
                UPDATE Matriculas 
                SET aluno_id = %s 
                WHERE aluno_id = %s
            """, (id_manter, id_remover))
            print(f"      {cursor.rowcount} matriculas transferidas")
        else:
            print("\n[2/5] Nenhuma matricula para transferir")
        
        # 3. Verificar e transferir responsáveis
        print("\n[3/5] Verificando responsaveis...")
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM ResponsaveisAlunos 
            WHERE aluno_id = %s
        """, (id_remover,))
        total_resp = cursor.fetchone()['total']
        print(f"      Responsaveis vinculados ao ID {id_remover}: {total_resp}")
        
        if total_resp > 0:
            # Primeiro, verificar se já existe vínculo no ID principal
            cursor.execute("""
                SELECT DISTINCT responsavel_id 
                FROM ResponsaveisAlunos 
                WHERE aluno_id = %s
            """, (id_remover,))
            resp_ids = [r['responsavel_id'] for r in cursor.fetchall()]
            
            # Remover vínculos duplicados e transferir
            for resp_id in resp_ids:
                # Verificar se já existe no ID principal
                cursor.execute("""
                    SELECT COUNT(*) as existe 
                    FROM ResponsaveisAlunos 
                    WHERE aluno_id = %s AND responsavel_id = %s
                """, (id_manter, resp_id))
                
                if cursor.fetchone()['existe'] == 0:
                    # Transferir para ID principal
                    cursor.execute("""
                        UPDATE ResponsaveisAlunos 
                        SET aluno_id = %s 
                        WHERE aluno_id = %s AND responsavel_id = %s
                    """, (id_manter, id_remover, resp_id))
                else:
                    # Já existe, apenas remover duplicata
                    cursor.execute("""
                        DELETE FROM ResponsaveisAlunos 
                        WHERE aluno_id = %s AND responsavel_id = %s
                    """, (id_remover, resp_id))
            
            print(f"      Responsaveis processados")
        
        # 4. Excluir outros vínculos (se houver)
        print("\n[4/5] Removendo outros vinculos...")
        
        # Verificar e remover notas (se houver tabela de notas)
        try:
            cursor.execute("""
                DELETE FROM Notas 
                WHERE aluno_id = %s
            """, (id_remover,))
            if cursor.rowcount > 0:
                print(f"      {cursor.rowcount} notas removidas")
        except:
            pass  # Tabela pode não existir ou não ter notas
        
        # 5. Finalmente, excluir o registro duplicado
        print("\n[5/5] Excluindo registro duplicado...")
        cursor.execute("""
            DELETE FROM Alunos 
            WHERE id = %s
        """, (id_remover,))
        registros_excluidos = cursor.rowcount
        print(f"      {registros_excluidos} registro excluido")
        
        # Commit das alterações
        conn.commit()
        
        print("\n" + "="*80)
        print("EXCLUSAO CONCLUIDA COM SUCESSO!")
        print("="*80)
        print(f"\nRegistro excluido: ID {id_remover}")
        print(f"Registro mantido: ID {id_manter}")
        print("\nVerificando resultado final...")
        
        # Verificar resultado
        cursor.execute("""
            SELECT id, nome, cpf, data_nascimento
            FROM Alunos
            WHERE cpf = '07038702386'
        """)
        resultado = cursor.fetchall()
        
        print(f"\nAlunos com CPF 07038702386: {len(resultado)}")
        for r in resultado:
            print(f"  ID {r['id']}: {r['nome']}")
        
        if len(resultado) == 1:
            print("\nOK: Duplicata resolvida! Apenas 1 registro permanece.")
        else:
            print(f"\nAVISO: Ainda existem {len(resultado)} registros com este CPF!")
        
    except Exception as e:
        print(f"\nERRO durante a exclusao: {e}")
        conn.rollback()
        print("Alteracoes revertidas (ROLLBACK)")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("\nATENCAO: Este script vai excluir permanentemente o registro duplicado!")
    print("ID a excluir: 2807")
    print("ID a manter: 2808")
    
    resposta = input("\nDeseja continuar? (sim/nao): ").strip().lower()
    
    if resposta in ['sim', 's', 'yes', 'y']:
        executar_exclusao()
    else:
        print("\nOperacao cancelada pelo usuario.")
