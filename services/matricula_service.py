"""
Módulo de serviço para gerenciamento de matrículas.
Extrai lógica de negócio de matrícula do main.py.
"""

from typing import Optional, Dict, List, Tuple
from mysql.connector import Error as MySQLError
import logging
from db.connection import get_cursor

logger = logging.getLogger(__name__)


def obter_ano_letivo_atual() -> Optional[int]:
    """
    Obtém o ID do ano letivo atual.
    
    Returns:
        int: ID do ano letivo atual ou None se não encontrado
    """
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT id FROM anosletivos WHERE YEAR(CURDATE()) = ano_letivo LIMIT 1"
            )
            resultado = cursor.fetchone()
            
            if resultado:
                ano_id = resultado['id'] if isinstance(resultado, dict) else resultado[0]
                logger.debug(f"Ano letivo atual encontrado: {ano_id}")
                return ano_id
            
            logger.warning("Ano letivo atual não encontrado no banco de dados")
            return None
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao obter ano letivo atual: {e}")
        return None
    except Exception as e:
        logger.exception(f"Erro inesperado ao obter ano letivo atual: {e}")
        return None


def obter_series_disponiveis() -> List[Dict]:
    """
    Obtém lista de séries disponíveis para matrícula.
    
    Returns:
        list: Lista de dicionários com id e nome das séries
    """
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT id, nome 
                FROM serie 
                ORDER BY ordem
            """)
            
            resultados = cursor.fetchall()
            
            if isinstance(resultados, list) and len(resultados) > 0:
                if isinstance(resultados[0], dict):
                    return resultados
                else:
                    return [{'id': r[0], 'nome': r[1]} for r in resultados]
            
            return []
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao obter séries: {e}")
        return []
    except Exception as e:
        logger.exception(f"Erro inesperado ao obter séries: {e}")
        return []


def obter_turmas_por_serie(serie_id: int, ano_letivo_id: int) -> List[Dict]:
    """
    Obtém lista de turmas disponíveis para uma série e ano letivo.
    
    Args:
        serie_id: ID da série
        ano_letivo_id: ID do ano letivo
        
    Returns:
        list: Lista de dicionários com id e nome das turmas
    """
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT id, nome 
                FROM turmas 
                WHERE serie_id = %s AND ano_letivo_id = %s
                ORDER BY nome
            """, (serie_id, ano_letivo_id))
            
            resultados = cursor.fetchall()
            
            if isinstance(resultados, list) and len(resultados) > 0:
                if isinstance(resultados[0], dict):
                    return resultados
                else:
                    return [{'id': r[0], 'nome': r[1]} for r in resultados]
            
            return []
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao obter turmas: {e}")
        return []
    except Exception as e:
        logger.exception(f"Erro inesperado ao obter turmas: {e}")
        return []


def verificar_matricula_existente(aluno_id: int, ano_letivo_id: int) -> Optional[Dict]:
    """
    Verifica se aluno já possui matrícula no ano letivo.
    
    Args:
        aluno_id: ID do aluno
        ano_letivo_id: ID do ano letivo
        
    Returns:
        dict: Dados da matrícula existente ou None
    """
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT m.id, m.status, t.nome as turma, s.nome as serie
                FROM matriculas m
                JOIN turmas t ON m.turma_id = t.id
                JOIN serie s ON t.serie_id = s.id
                WHERE m.aluno_id = %s AND m.ano_letivo_id = %s
                LIMIT 1
            """, (aluno_id, ano_letivo_id))
            
            resultado = cursor.fetchone()
            
            if resultado:
                if isinstance(resultado, dict):
                    return resultado
                else:
                    return {
                        'id': resultado[0],
                        'status': resultado[1],
                        'turma': resultado[2],
                        'serie': resultado[3]
                    }
            
            return None
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao verificar matrícula existente: {e}")
        return None
    except Exception as e:
        logger.exception(f"Erro inesperado ao verificar matrícula existente: {e}")
        return None


def matricular_aluno(
    aluno_id: int,
    turma_id: int,
    ano_letivo_id: Optional[int] = None,
    status: str = 'Ativo'
) -> Tuple[bool, str]:
    """
    Matricula um aluno em uma turma.
    
    Args:
        aluno_id: ID do aluno
        turma_id: ID da turma
        ano_letivo_id: ID do ano letivo (se None, usa ano atual)
        status: Status da matrícula (padrão: 'Ativo')
        
    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    try:
        # Obter ano letivo se não especificado
        if ano_letivo_id is None:
            ano_letivo_id = obter_ano_letivo_atual()
            if ano_letivo_id is None:
                return False, "Ano letivo atual não encontrado"
        
        # Verificar se já existe matrícula ativa
        matricula_existente = verificar_matricula_existente(aluno_id, ano_letivo_id)
        if matricula_existente and matricula_existente['status'] == 'Ativo':
            return False, f"Aluno já possui matrícula ativa na turma {matricula_existente['turma']}"
        
        with get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO matriculas (aluno_id, turma_id, ano_letivo_id, status)
                VALUES (%s, %s, %s, %s)
            """, (aluno_id, turma_id, ano_letivo_id, status))
            
            logger.info(f"Aluno {aluno_id} matriculado na turma {turma_id} com sucesso")
            return True, "Matrícula realizada com sucesso"
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao matricular aluno: {e}")
        return False, f"Erro ao matricular aluno: {str(e)}"
    except Exception as e:
        logger.exception(f"Erro inesperado ao matricular aluno: {e}")
        return False, f"Erro inesperado: {str(e)}"


def transferir_aluno(
    matricula_id: int,
    nova_turma_id: int
) -> Tuple[bool, str]:
    """
    Transfere um aluno de uma turma para outra.
    
    Args:
        matricula_id: ID da matrícula atual
        nova_turma_id: ID da nova turma
        
    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    try:
        with get_cursor() as cursor:
            # Verificar se matrícula existe
            cursor.execute(
                "SELECT id FROM matriculas WHERE id = %s",
                (matricula_id,)
            )
            if not cursor.fetchone():
                return False, "Matrícula não encontrada"
            
            # Atualizar turma
            cursor.execute("""
                UPDATE matriculas 
                SET turma_id = %s 
                WHERE id = %s
            """, (nova_turma_id, matricula_id))
            
            logger.info(f"Matrícula {matricula_id} transferida para turma {nova_turma_id}")
            return True, "Transferência realizada com sucesso"
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao transferir aluno: {e}")
        return False, f"Erro ao transferir aluno: {str(e)}"
    except Exception as e:
        logger.exception(f"Erro inesperado ao transferir aluno: {e}")
        return False, f"Erro inesperado: {str(e)}"


def cancelar_matricula(
    matricula_id: int,
    motivo: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Cancela uma matrícula.
    
    Args:
        matricula_id: ID da matrícula
        motivo: Motivo do cancelamento (opcional)
        
    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    try:
        with get_cursor() as cursor:
            # Verificar se matrícula existe
            cursor.execute(
                "SELECT id, status FROM matriculas WHERE id = %s",
                (matricula_id,)
            )
            resultado = cursor.fetchone()
            
            if not resultado:
                return False, "Matrícula não encontrada"
            
            status_atual = resultado['status'] if isinstance(resultado, dict) else resultado[1]
            
            if status_atual == 'Cancelado':
                return False, "Matrícula já está cancelada"
            
            # Atualizar status
            cursor.execute("""
                UPDATE matriculas 
                SET status = 'Cancelado'
                WHERE id = %s
            """, (matricula_id,))
            
            logger.info(f"Matrícula {matricula_id} cancelada. Motivo: {motivo or 'Não informado'}")
            return True, "Matrícula cancelada com sucesso"
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao cancelar matrícula: {e}")
        return False, f"Erro ao cancelar matrícula: {str(e)}"
    except Exception as e:
        logger.exception(f"Erro inesperado ao cancelar matrícula: {e}")
        return False, f"Erro inesperado: {str(e)}"


def atualizar_status_matricula(
    matricula_id: int,
    novo_status: str
) -> Tuple[bool, str]:
    """
    Atualiza o status de uma matrícula.
    
    Args:
        matricula_id: ID da matrícula
        novo_status: Novo status ('Ativo', 'Cancelado', 'Transferido', etc.)
        
    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    try:
        # Validar status
        status_validos = ['Ativo', 'Cancelado', 'Transferido', 'Concluído', 'Trancado']
        if novo_status not in status_validos:
            return False, f"Status inválido. Use um dos seguintes: {', '.join(status_validos)}"
        
        with get_cursor() as cursor:
            # Verificar se matrícula existe
            cursor.execute(
                "SELECT id FROM matriculas WHERE id = %s",
                (matricula_id,)
            )
            if not cursor.fetchone():
                return False, "Matrícula não encontrada"
            
            # Atualizar status
            cursor.execute("""
                UPDATE matriculas 
                SET status = %s 
                WHERE id = %s
            """, (novo_status, matricula_id))
            
            logger.info(f"Status da matrícula {matricula_id} atualizado para '{novo_status}'")
            return True, f"Status atualizado para '{novo_status}' com sucesso"
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao atualizar status: {e}")
        return False, f"Erro ao atualizar status: {str(e)}"
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar status: {e}")
        return False, f"Erro inesperado: {str(e)}"


def obter_matricula_por_id(matricula_id: int) -> Optional[Dict]:
    """
    Obtém dados completos de uma matrícula.
    
    Args:
        matricula_id: ID da matrícula
        
    Returns:
        dict: Dados da matrícula ou None
    """
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    m.id, m.aluno_id, m.turma_id, m.ano_letivo_id, m.status,
                    a.nome as aluno_nome,
                    t.nome as turma_nome,
                    s.nome as serie_nome,
                    al.ano_letivo
                FROM matriculas m
                JOIN alunos a ON m.aluno_id = a.id
                JOIN turmas t ON m.turma_id = t.id
                JOIN serie s ON t.serie_id = s.id
                JOIN anosletivos al ON m.ano_letivo_id = al.id
                WHERE m.id = %s
            """, (matricula_id,))
            
            resultado = cursor.fetchone()
            
            if resultado:
                if isinstance(resultado, dict):
                    return resultado
                else:
                    return {
                        'id': resultado[0],
                        'aluno_id': resultado[1],
                        'turma_id': resultado[2],
                        'ano_letivo_id': resultado[3],
                        'status': resultado[4],
                        'aluno_nome': resultado[5],
                        'turma_nome': resultado[6],
                        'serie_nome': resultado[7],
                        'ano_letivo': resultado[8]
                    }
            
            return None
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao obter matrícula: {e}")
        return None
    except Exception as e:
        logger.exception(f"Erro inesperado ao obter matrícula: {e}")
        return None
