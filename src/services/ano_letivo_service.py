"""
Serviço para lógica de ano letivo.

Centraliza queries e regras de negócio relacionadas ao ano letivo,
evitando duplicação entre UI e outros serviços.
"""

from typing import Dict, List, Optional, Tuple
from db.connection import get_cursor
from src.core.config_logs import get_logger

logger = get_logger(__name__)


def obter_ano_letivo_atual_id() -> int:
    """
    Retorna o ID do ano letivo atual.

    Usa a configuração ANO_LETIVO_ATUAL e verifica se ainda está ativo.
    O sistema permanece no ano letivo configurado até sua data_fim.

    Returns:
        int: ID do ano letivo atual (fallback: 1)
    """
    try:
        from src.core.config import ANO_LETIVO_ATUAL

        with get_cursor() as cursor:
            # Busca o ano letivo configurado no sistema
            cursor.execute(
                "SELECT id, data_fim FROM anosletivos WHERE ano_letivo = %s",
                (ANO_LETIVO_ATUAL,),
            )
            resultado = cursor.fetchone()

            if resultado:
                ano_id = resultado["id"] if isinstance(resultado, dict) else resultado[0]
                data_fim = resultado["data_fim"] if isinstance(resultado, dict) else resultado[1]

                if data_fim is None:
                    return int(str(ano_id))

                cursor.execute("SELECT CURDATE() <= %s as ainda_ativo", (data_fim,))
                ainda_ativo = cursor.fetchone()
                if ainda_ativo and (
                    ainda_ativo["ainda_ativo"]
                    if isinstance(ainda_ativo, dict)
                    else ainda_ativo[0]
                ):
                    return int(str(ano_id))

            # Se o ano configurado já encerrou, busca o próximo ano letivo ativo
            cursor.execute(
                """
                SELECT id FROM anosletivos 
                WHERE CURDATE() BETWEEN data_inicio AND data_fim
                ORDER BY ano_letivo DESC 
                LIMIT 1
                """
            )
            resultado = cursor.fetchone()

            # Fallback: ano mais recente
            if not resultado:
                cursor.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                resultado = cursor.fetchone()

            if resultado:
                return int(
                    str(resultado["id"] if isinstance(resultado, dict) else resultado[0])
                )
            return 1

    except Exception as e:
        logger.error(f"Erro ao obter ano letivo atual: {e}")
        return 1


def obter_status_matriculas_por_anos(
    aluno_id: int, anos_letivos: List[Tuple[int, int]]
) -> Dict[str, Tuple[int, str]]:
    """
    Retorna o status da matrícula de um aluno para cada ano letivo informado.

    Args:
        aluno_id: ID do aluno
        anos_letivos: Lista de tuplas (ano_letivo, ano_letivo_id)

    Returns:
        Dict mapeando "ano_letivo - status" -> (ano_letivo_id, status)
    """
    anos_info: Dict[str, Tuple[int, str]] = {}
    try:
        from src.utils.safe import converter_para_int_seguro

        aluno_id_safe = converter_para_int_seguro(aluno_id)
        if aluno_id_safe is None:
            return anos_info

        with get_cursor() as cursor:
            for ano_letivo, ano_letivo_id in anos_letivos:
                cursor.execute(
                    """
                    SELECT m.status
                    FROM matriculas m
                    JOIN turmas t ON m.turma_id = t.id
                    WHERE m.aluno_id = %s 
                    AND m.ano_letivo_id = %s 
                    ORDER BY m.data_matricula DESC
                    LIMIT 1
                    """,
                    (aluno_id_safe, converter_para_int_seguro(ano_letivo_id) or 1),
                )
                status_result = cursor.fetchone()
                status = status_result[0] if status_result else "Desconhecido"
                anos_info[f"{ano_letivo} - {status}"] = (ano_letivo_id, status)

    except Exception as e:
        logger.error(f"Erro ao obter status de matrículas por ano: {e}")

    return anos_info
