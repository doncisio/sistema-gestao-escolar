"""
Teste das queries de estatísticas
"""
import logging
logging.basicConfig(level=logging.DEBUG)

from src.core.conexao import inicializar_pool
from db.connection import get_cursor

print("Inicializando pool...")
inicializar_pool()

escola_id = 60

print(f"\n1. Testando query: Total de alunos (escola_id={escola_id})")
try:
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM alunos
            WHERE escola_id = %s
        """, (escola_id,))
        resultado = cursor.fetchone()
        print(f"   Resultado: {resultado}")
        total = resultado['total'] if resultado else 0
        print(f"   Total de alunos: {total}")
except Exception as e:
    print(f"   ✗ ERRO: {e}")
    import traceback
    traceback.print_exc()

print(f"\n2. Testando query: Alunos ativos (escola_id={escola_id})")
try:
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(DISTINCT m.aluno_id) as total
            FROM matriculas m
            INNER JOIN alunos a ON m.aluno_id = a.id
            WHERE a.escola_id = %s AND m.status = 'Ativo'
        """, (escola_id,))
        resultado = cursor.fetchone()
        print(f"   Resultado: {resultado}")
except Exception as e:
    print(f"   ✗ ERRO: {e}")
    import traceback
    traceback.print_exc()

print(f"\n3. Testando query: Alunos por série (escola_id={escola_id})")
try:
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT s.nome as serie, COUNT(DISTINCT m.aluno_id) as total
            FROM matriculas m
            INNER JOIN turmas t ON m.turma_id = t.id
            INNER JOIN series s ON t.serie_id = s.id
            INNER JOIN alunos a ON m.aluno_id = a.id
            WHERE a.escola_id = %s AND m.status = 'Ativo'
            GROUP BY s.id, s.nome
            ORDER BY s.ordem
        """, (escola_id,))
        resultados = cursor.fetchall()
        print(f"   Número de resultados: {len(resultados)}")
        for r in resultados[:3]:  # Primeiras 3 linhas
            print(f"   - {r}")
except Exception as e:
    print(f"   ✗ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\nFIM DO TESTE")
