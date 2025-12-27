from typing import List, Dict, Optional
from src.core.conexao import conectar_bd


def upsert_horarios(dados: List[Dict]) -> int:
    """Insere ou atualiza (upsert) uma lista de horários em `horarios_importados`.
    Retorna o número de linhas processadas.
    Cada item em `dados` deve conter pelo menos: turma_id, dia, horario, valor
    Opcionalmente: disciplina_id, professor_id
    """
    if not dados:
        return 0

    conn = conectar_bd()
    if not conn:
        raise RuntimeError("Não foi possível conectar ao banco de dados")

    cursor = conn.cursor()
    sql = (
        "INSERT INTO horarios_importados (turma_id, dia, horario, valor, disciplina_id, professor_id) "
        "VALUES (%s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE valor=VALUES(valor), disciplina_id=VALUES(disciplina_id), professor_id=VALUES(professor_id)"
    )

    count = 0
    try:
        for item in dados:
            params = (
                item.get('turma_id'),
                item.get('dia'),
                item.get('horario'),
                item.get('valor'),
                item.get('disciplina_id'),
                item.get('professor_id'),
            )
            cursor.execute(sql, params)
            count += 1
        try:
            conn.commit()
        except Exception:
            pass
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

    return count
