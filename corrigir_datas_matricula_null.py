"""
Script para corrigir data_matricula NULL dos alunos rematriculados na transição de ano letivo.
Data da transição: 27/01/2026
"""
from db.connection import get_connection
from src.core.config import ANO_LETIVO_ATUAL

def main():
    escola_id = 60
    ano_letivo = ANO_LETIVO_ATUAL
    data_transicao = '2026-01-27'
    
    print("=== Correção de Datas de Matrícula NULL ===")
    print(f"Data da transição: {data_transicao}")
    print()
    
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        
        # Pegar ano_letivo_id
        cursor.execute("SELECT id FROM AnosLetivos WHERE ano_letivo = %s", (ano_letivo,))
        ano_letivo_id = cursor.fetchone()['id']
        
        # Contar quantos registros serão afetados
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM matriculas m
            INNER JOIN alunos a ON m.aluno_id = a.id
            WHERE m.ano_letivo_id = %s
              AND a.escola_id = %s
              AND m.data_matricula IS NULL
        """, (ano_letivo_id, escola_id))
        
        total_afetados = cursor.fetchone()['total']
        print(f"Registros com data_matricula NULL: {total_afetados}")
        
        if total_afetados == 0:
            print("Nenhum registro para atualizar.")
            cursor.close()
            return
        
        # Mostrar alguns exemplos
        cursor.execute("""
            SELECT 
                m.id as matricula_id,
                a.id as aluno_id,
                a.nome,
                m.status
            FROM matriculas m
            INNER JOIN alunos a ON m.aluno_id = a.id
            WHERE m.ano_letivo_id = %s
              AND a.escola_id = %s
              AND m.data_matricula IS NULL
            LIMIT 5
        """, (ano_letivo_id, escola_id))
        
        exemplos = cursor.fetchall()
        print("\nExemplos de registros que serão atualizados:")
        print("Mat.ID | Aluno ID | Nome                         | Status")
        print("-" * 70)
        for ex in exemplos:
            print(f"{ex['matricula_id']:6} | {ex['aluno_id']:8} | {ex['nome'][:30]:30} | {ex['status']}")
        
        print()
        resposta = input(f"Confirma a atualização de {total_afetados} registros para {data_transicao}? (s/N): ")
        
        if resposta.lower() != 's':
            print("Operação cancelada.")
            cursor.close()
            return
        
        # Executar UPDATE
        cursor.execute("""
            UPDATE matriculas m
            INNER JOIN alunos a ON m.aluno_id = a.id
            SET m.data_matricula = %s
            WHERE m.ano_letivo_id = %s
              AND a.escola_id = %s
              AND m.data_matricula IS NULL
        """, (data_transicao, ano_letivo_id, escola_id))
        
        linhas_afetadas = cursor.rowcount
        
        # COMMIT EXPLÍCITO
        conn.commit()
        print(f"\n✓ {linhas_afetadas} registros atualizados e commitados com sucesso!")
        
        # Verificar
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM matriculas m
            INNER JOIN alunos a ON m.aluno_id = a.id
            WHERE m.ano_letivo_id = %s
              AND a.escola_id = %s
              AND m.data_matricula IS NULL
        """, (ano_letivo_id, escola_id))
        
        restantes = cursor.fetchone()['total']
        print(f"Registros com data_matricula NULL restantes: {restantes}")
        
        cursor.close()

if __name__ == "__main__":
    main()
