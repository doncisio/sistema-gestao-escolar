"""
Script para verificar contagem de 342 alunos
"""
from src.core.conexao import inicializar_pool
from db.connection import get_cursor

inicializar_pool()

escola_id = 60
ano_letivo = '2025'

print("=" * 80)
print("VERIFICAÇÃO: Contagem de Alunos")
print("=" * 80)

with get_cursor() as cursor:
    # 1. Buscar ID do ano letivo
    cursor.execute("SELECT id FROM AnosLetivos WHERE ano_letivo = %s", (ano_letivo,))
    ano_result = cursor.fetchone()
    ano_id = ano_result['id'] if ano_result else None
    print(f"\nAno Letivo: {ano_letivo}, ID: {ano_id}")
    
    if not ano_id:
        print("ERRO: Ano letivo não encontrado!")
        exit(1)
    
    # 2. Contar alunos com matrícula (Ativo + Transferido)
    cursor.execute("""
        SELECT COUNT(DISTINCT m.aluno_id) as total
        FROM matriculas m
        INNER JOIN alunos a ON m.aluno_id = a.id
        WHERE m.ano_letivo_id = %s
          AND a.escola_id = %s
          AND (m.status = 'Ativo' OR m.status = 'Transferido' OR m.status = 'Transferida')
    """, (ano_id, escola_id))
    result = cursor.fetchone()
    total_com_transferidos = result['total'] if result else 0
    print(f"\n1. Total alunos (Ativo + Transferido): {total_com_transferidos}")
    
    # 3. Contar apenas alunos ativos
    cursor.execute("""
        SELECT COUNT(DISTINCT m.aluno_id) as total
        FROM matriculas m
        INNER JOIN alunos a ON m.aluno_id = a.id
        WHERE m.ano_letivo_id = %s
          AND a.escola_id = %s
          AND m.status = 'Ativo'
    """, (ano_id, escola_id))
    result = cursor.fetchone()
    total_ativos = result['total'] if result else 0
    print(f"2. Total alunos (Apenas Ativo): {total_ativos}")
    
    # 4. Contar transferidos
    cursor.execute("""
        SELECT COUNT(DISTINCT m.aluno_id) as total
        FROM matriculas m
        INNER JOIN alunos a ON m.aluno_id = a.id
        WHERE m.ano_letivo_id = %s
          AND a.escola_id = %s
          AND (m.status = 'Transferido' OR m.status = 'Transferida')
    """, (ano_id, escola_id))
    result = cursor.fetchone()
    total_transferidos = result['total'] if result else 0
    print(f"3. Total transferidos: {total_transferidos}")
    
    # 5. Contar TODAS as matrículas (não distintas)
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM matriculas m
        INNER JOIN alunos a ON m.aluno_id = a.id
        WHERE m.ano_letivo_id = %s
          AND a.escola_id = %s
          AND (m.status = 'Ativo' OR m.status = 'Transferido' OR m.status = 'Transferida')
    """, (ano_id, escola_id))
    result = cursor.fetchone()
    total_matriculas = result['total'] if result else 0
    print(f"4. Total matrículas (pode ter duplicadas): {total_matriculas}")
    
    # 6. Verificar se há alunos com múltiplas matrículas
    cursor.execute("""
        SELECT m.aluno_id, a.nome, COUNT(*) as num_matriculas
        FROM matriculas m
        INNER JOIN alunos a ON m.aluno_id = a.id
        WHERE m.ano_letivo_id = %s
          AND a.escola_id = %s
          AND (m.status = 'Ativo' OR m.status = 'Transferido' OR m.status = 'Transferida')
        GROUP BY m.aluno_id, a.nome
        HAVING COUNT(*) > 1
    """, (ano_id, escola_id))
    duplicados = cursor.fetchall()
    print(f"\n5. Alunos com múltiplas matrículas: {len(duplicados)}")
    if duplicados:
        for d in duplicados[:5]:  # Mostrar apenas 5
            print(f"   - ID {d['aluno_id']}: {d['nome']} ({d['num_matriculas']} matrículas)")
    
    # 7. Query usada no dashboard (WITH)
    print("\n" + "=" * 80)
    print("QUERY DO DASHBOARD (com CTE)")
    print("=" * 80)
    cursor.execute("""
        WITH base_alunos AS (
            SELECT 
                m.aluno_id,
                m.status,
                s.nome as serie,
                t.nome as turma,
                t.turno
            FROM matriculas m
            INNER JOIN turmas t ON m.turma_id = t.id
            INNER JOIN series s ON t.serie_id = s.id
            INNER JOIN alunos a ON m.aluno_id = a.id
            WHERE m.ano_letivo_id = %s
              AND a.escola_id = %s
              AND (m.status = 'Ativo' OR m.status = 'Transferido' OR m.status = 'Transferida')
        )
        SELECT 
            COUNT(DISTINCT aluno_id) as total_alunos,
            SUM(CASE WHEN status = 'Ativo' THEN 1 ELSE 0 END) as alunos_ativos
        FROM base_alunos
    """, (ano_id, escola_id))
    result = cursor.fetchone()
    print(f"Total alunos (dashboard): {result['total_alunos']}")
    print(f"Alunos ativos (dashboard): {result['alunos_ativos']}")
    
    print("\n" + "=" * 80)
    print("ANÁLISE")
    print("=" * 80)
    print(f"Diferença esperada: 342 - {total_com_transferidos} = {342 - total_com_transferidos}")
    
    if total_com_transferidos == 342:
        print("✓ Contagem CORRETA!")
    elif total_com_transferidos == 341:
        print("✗ Falta 1 aluno - investigando...")
        # Verificar se é problema de status
        cursor.execute("""
            SELECT DISTINCT m.status, COUNT(DISTINCT m.aluno_id) as total
            FROM matriculas m
            INNER JOIN alunos a ON m.aluno_id = a.id
            WHERE m.ano_letivo_id = %s
              AND a.escola_id = %s
            GROUP BY m.status
        """, (ano_id, escola_id))
        status_list = cursor.fetchall()
        print("\nMatrículas por status:")
        for s in status_list:
            print(f"  - {s['status']}: {s['total']} alunos")
