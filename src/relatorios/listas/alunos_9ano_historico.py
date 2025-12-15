from typing import List, Dict, Any
from src.core.conexao import conectar_bd
from src.core.config_logs import get_logger

logger = get_logger(__name__)


def _obter_ano_id(cursor, ano_letivo: int | None) -> int:
    if ano_letivo is None:
        cursor.execute("SELECT id FROM AnosLetivos ORDER BY ano_letivo DESC LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else 1

    # se foi passado um número de ano (ex: 2025)
    if isinstance(ano_letivo, int) and ano_letivo > 1900:
        cursor.execute("SELECT id FROM AnosLetivos WHERE ano_letivo = %s LIMIT 1", (ano_letivo,))
        row = cursor.fetchone()
        if row:
            return row[0]

    # tentar como id
    try:
        cursor.execute("SELECT id FROM AnosLetivos WHERE id = %s LIMIT 1", (ano_letivo,))
        row = cursor.fetchone()
        if row:
            return row[0]
    except Exception:
        pass

    # fallback
    cursor.execute("SELECT id FROM AnosLetivos ORDER BY ano_letivo DESC LIMIT 1")
    row = cursor.fetchone()
    return row[0] if row else 1


def buscar_alunos_9ano_historico(ano_letivo: int | None = None, escola_id: int = 60) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retorna alunos matriculados e ativos no 9º ano divididos em:
      - 'completo': aqueles que possuem histórico (qualquer escola) para todas as séries 1º ao 8º (serie_id 3..10)
      - 'com_pendencias': aqueles que têm ausência de histórico em pelo menos uma das séries 1..8

    Cada item contém: aluno_id, nome, turma_id, turma_nome, serie_id_atual, series_faltantes (lista de serie_id)
    """
    conn = conectar_bd()
    if conn is None:
        logger.error("Não foi possível conectar ao banco de dados")
        return {'completo': [], 'com_pendencias': []}

    try:
        cursor = conn.cursor()

        ano_id = _obter_ano_id(cursor, ano_letivo)

        # obter ids de séries que representem 9º ano (mesma heurística usada em outros módulos)
        cursor.execute("SELECT id FROM series WHERE nome LIKE %s OR nome LIKE %s OR nome LIKE %s", ('9%', '%9º%', '%9º %'))
        rows = cursor.fetchall()
        series_9_ids = [r[0] for r in rows] if rows else []

        # buscar alunos ativos em turmas de 9º ano
        if series_9_ids:
            placeholders = ','.join(['%s'] * len(series_9_ids))
            query = (
                f"SELECT DISTINCT a.id AS aluno_id, a.nome AS aluno_nome, t.id AS turma_id, t.nome AS turma_nome, t.serie_id "
                f"FROM Alunos a JOIN Matriculas m ON a.id = m.aluno_id JOIN Turmas t ON m.turma_id = t.id "
                f"WHERE m.ano_letivo_id = %s AND m.status = 'Ativo' AND t.serie_id IN ({placeholders}) AND (t.escola_id = %s OR a.escola_id = %s)"
            )
            params = [ano_id] + series_9_ids + [escola_id, escola_id]
            cursor.execute(query, params)
        else:
            # fallback por nome
            cursor.execute(
                """
                SELECT DISTINCT a.id AS aluno_id, a.nome AS aluno_nome, t.id AS turma_id, t.nome AS turma_nome, t.serie_id
                FROM Alunos a
                JOIN Matriculas m ON a.id = m.aluno_id
                JOIN Turmas t ON m.turma_id = t.id
                LEFT JOIN series s ON t.serie_id = s.id
                WHERE m.ano_letivo_id = %s AND m.status = 'Ativo' AND (s.nome LIKE '9%%' OR s.nome LIKE '%%9º%%' OR s.nome LIKE '%%9º %') AND (t.escola_id = %s OR a.escola_id = %s)
                """,
                (ano_id, escola_id, escola_id)
            )

        alunos_rows = cursor.fetchall()
        if not alunos_rows:
            return {'completo': [], 'com_pendencias': []}

        # normalizar lista de ids
        aluno_ids = [r[0] if not isinstance(r, dict) else r.get('aluno_id') for r in alunos_rows]

        # séries que correspondem a 1º ao 8º conforme convenção do sistema: serie_id 3..10
        required_serie_ids = list(range(3, 11))

        # buscar histórico escolar para esses alunos nas séries 3..10
        placeholders = ','.join(['%s'] * len(aluno_ids))
        cursor.execute(
            f"SELECT DISTINCT aluno_id, serie_id FROM historico_escolar WHERE aluno_id IN ({placeholders}) AND serie_id BETWEEN %s AND %s",
            tuple(aluno_ids) + (3, 10)
        )
        historico_rows = cursor.fetchall()

        # mapear aluno_id -> set(serie_id)
        historico_map: Dict[int, set] = {}
        for row in historico_rows:
            aluno_id = row[0]
            serie_id = row[1]
            historico_map.setdefault(aluno_id, set()).add(serie_id)

        completo = []
        com_pendencias = []

        for r in alunos_rows:
            if isinstance(r, dict):
                aluno_id = r.get('aluno_id')
                nome = r.get('aluno_nome')
                turma_id = r.get('turma_id')
                turma_nome = r.get('turma_nome')
                serie_atual = r.get('serie_id')
            else:
                # ordem: aluno_id, aluno_nome, turma_id, turma_nome, serie_id
                aluno_id = r[0]
                nome = r[1]
                turma_id = r[2] if len(r) > 2 else None
                turma_nome = r[3] if len(r) > 3 else None
                serie_atual = r[4] if len(r) > 4 else None

            presentes = historico_map.get(aluno_id, set())
            faltantes = [s for s in required_serie_ids if s not in presentes]

            item = {
                'aluno_id': aluno_id,
                'nome': nome,
                'turma_id': turma_id,
                'turma_nome': turma_nome,
                'serie_id_atual': serie_atual,
                'series_faltantes': faltantes
            }

            if not faltantes:
                completo.append(item)
            else:
                com_pendencias.append(item)

        return {'completo': completo, 'com_pendencias': com_pendencias}

    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    resultado = buscar_alunos_9ano_historico(None, 60)
    print(f"Alunos com histórico completo: {len(resultado['completo'])}")
    print(f"Alunos com pendências: {len(resultado['com_pendencias'])}")
