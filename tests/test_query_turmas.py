"""Teste da query de listar_turmas."""
import sys
sys.path.insert(0, '.')

from db.connection import get_connection

with get_connection() as conn:
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT 
            t.id,
            t.nome,
            t.turno,
            t.capacidade_maxima,
            t.ano_letivo_id,
            t.serie_id,
            t.escola_id,
            t.professor_id,
            s.nome as serie_nome,
            s.ciclo as serie_ciclo,
            al.ano_letivo as ano_letivo,
            COALESCE(COUNT(DISTINCT m.id), 0) as total_alunos
        FROM turmas t
        LEFT JOIN serie s ON t.serie_id = s.id
        LEFT JOIN anosletivos al ON t.ano_letivo_id = al.id
        LEFT JOIN Matriculas m ON m.turma_id = t.id AND m.status = 'Ativo'
        WHERE 1=1
        GROUP BY t.id, t.nome, t.turno, t.capacidade_maxima, 
                 t.ano_letivo_id, t.serie_id, t.escola_id, t.professor_id,
                 s.nome, s.ciclo, al.ano_letivo
        ORDER BY s.ciclo, s.nome, t.turno, t.nome
    """
    
    cursor.execute(query)
    turmas = cursor.fetchall()
    
    print(f"Total turmas: {len(turmas)}")
    for t in turmas[:5]:
        print(f"  {t['id']}: {t.get('serie_nome', 'N/A')} {t.get('nome', '').strip() or '(única)'} - {t.get('turno', 'N/A')}")
