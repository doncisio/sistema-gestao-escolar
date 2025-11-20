"""
Teste para verificar turmas do 6º Ano
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.connection import get_cursor

def main():
    print("=" * 80)
    print("VERIFICANDO TURMAS DO 6º ANO - 2025")
    print("=" * 80)
    
    with get_cursor() as cursor:
        # Verificar turmas por série
        cursor.execute("""
            SELECT 
                s.nome as serie, 
                t.nome as turma, 
                COUNT(DISTINCT m.aluno_id) as total
            FROM matriculas m
            INNER JOIN turmas t ON m.turma_id = t.id
            INNER JOIN serie s ON t.serie_id = s.id
            INNER JOIN alunos a ON m.aluno_id = a.id
            WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = '2025')
              AND a.escola_id = 60
              AND (m.status = 'Ativo' OR m.status = 'Transferido' OR m.status = 'Transferida')
            GROUP BY s.id, s.nome, t.id, t.nome
            ORDER BY s.nome, t.nome
        """)
        
        resultados = cursor.fetchall()
        
        print(f"\n✓ Total de turmas encontradas: {len(resultados)}\n")
        
        serie_atual = None
        total_serie = 0
        
        for r in resultados:
            if r['serie'] != serie_atual:
                if serie_atual is not None:
                    print(f"  └─ TOTAL {serie_atual}: {total_serie} alunos\n")
                serie_atual = r['serie']
                total_serie = 0
                print(f"{r['serie']}:")
            
            print(f"  ├─ Turma {r['turma']}: {r['total']} alunos")
            total_serie += r['total']
        
        if serie_atual is not None:
            print(f"  └─ TOTAL {serie_atual}: {total_serie} alunos\n")
        
        # Verificar especificamente o 6º Ano
        print("=" * 80)
        print("DETALHAMENTO 6º ANO")
        print("=" * 80)
        
        cursor.execute("""
            SELECT 
                t.nome as turma,
                t.turno,
                COUNT(DISTINCT m.aluno_id) as total,
                GROUP_CONCAT(a.nome ORDER BY a.nome SEPARATOR ', ') as alunos
            FROM matriculas m
            INNER JOIN turmas t ON m.turma_id = t.id
            INNER JOIN serie s ON t.serie_id = s.id
            INNER JOIN alunos a ON m.aluno_id = a.id
            WHERE s.nome = '6º Ano'
              AND m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = '2025')
              AND a.escola_id = 60
              AND (m.status = 'Ativo' OR m.status = 'Transferido' OR m.status = 'Transferida')
            GROUP BY t.id, t.nome, t.turno
            ORDER BY t.nome
        """)
        
        turmas_6ano = cursor.fetchall()
        
        for turma in turmas_6ano:
            print(f"\nTurma {turma['turma']} - Turno: {turma['turno']}")
            print(f"Total: {turma['total']} alunos")
            if turma['total'] <= 10:
                print(f"Alunos: {turma['alunos']}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
