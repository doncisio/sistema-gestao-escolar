"""
Serviço para cálculo de estatísticas de alunos.
Extrai lógica de estatísticas do main.py.
"""

from typing import Dict, List, Optional
from mysql.connector import Error as MySQLError
import logging
from db.connection import get_cursor

logger = logging.getLogger(__name__)


def obter_estatisticas_alunos(escola_id: int = 60) -> Optional[Dict]:
    """
    Calcula estatísticas gerais de alunos da escola.
    
    Args:
        escola_id: ID da escola (padrão: 60)
        
    Returns:
        dict: Estatísticas ou None em caso de erro
    """
    try:
        estatisticas = {}
        
        with get_cursor() as cursor:
            # Total de alunos
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM alunos
                WHERE escola_id = %s
            """, (escola_id,))
            resultado = cursor.fetchone()
            estatisticas['total_alunos'] = resultado[0] if resultado else 0
            
            # Alunos com matrícula ativa
            cursor.execute("""
                SELECT COUNT(DISTINCT m.aluno_id) as total
                FROM matriculas m
                INNER JOIN alunos a ON m.aluno_id = a.id
                WHERE a.escola_id = %s AND m.status = 'Ativo'
            """, (escola_id,))
            resultado = cursor.fetchone()
            estatisticas['alunos_ativos'] = resultado[0] if resultado else 0
            
            # Alunos por série
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
            alunos_por_serie = {}
            
            if resultados:
                if isinstance(resultados[0], dict):
                    alunos_por_serie = {r['serie']: r['total'] for r in resultados}
                else:
                    alunos_por_serie = {r[0]: r[1] for r in resultados}
            
            estatisticas['alunos_por_serie'] = alunos_por_serie
            
            # Alunos por turno
            cursor.execute("""
                SELECT t.turno, COUNT(DISTINCT m.aluno_id) as total
                FROM matriculas m
                INNER JOIN turmas t ON m.turma_id = t.id
                INNER JOIN alunos a ON m.aluno_id = a.id
                WHERE a.escola_id = %s AND m.status = 'Ativo'
                GROUP BY t.turno
            """, (escola_id,))
            
            resultados = cursor.fetchall()
            alunos_por_turno = {}
            
            if resultados:
                if isinstance(resultados[0], dict):
                    alunos_por_turno = {r['turno']: r['total'] for r in resultados}
                else:
                    alunos_por_turno = {r[0]: r[1] for r in resultados}
            
            estatisticas['alunos_por_turno'] = alunos_por_turno
            
            # Alunos sem matrícula
            estatisticas['alunos_sem_matricula'] = (
                estatisticas['total_alunos'] - estatisticas['alunos_ativos']
            )
            
            logger.info(f"Estatísticas calculadas: {estatisticas['total_alunos']} alunos total")
            return estatisticas
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao calcular estatísticas de alunos")
        return None
    except Exception as e:
        logger.exception(f"Erro inesperado ao calcular estatísticas de alunos")
        return None


def obter_estatisticas_por_ano_letivo(ano_letivo_id: int, escola_id: int = 60) -> Optional[Dict]:
    """
    Calcula estatísticas de alunos para um ano letivo específico.
    
    Args:
        ano_letivo_id: ID do ano letivo
        escola_id: ID da escola (padrão: 60)
        
    Returns:
        dict: Estatísticas ou None em caso de erro
    """
    try:
        estatisticas = {}
        
        with get_cursor() as cursor:
            # Matrículas no ano
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM matriculas m
                INNER JOIN alunos a ON m.aluno_id = a.id
                WHERE m.ano_letivo_id = %s AND a.escola_id = %s
            """, (ano_letivo_id, escola_id))
            resultado = cursor.fetchone()
            estatisticas['total_matriculas'] = resultado[0] if resultado else 0
            
            # Matrículas por status
            cursor.execute("""
                SELECT m.status, COUNT(*) as total
                FROM matriculas m
                INNER JOIN alunos a ON m.aluno_id = a.id
                WHERE m.ano_letivo_id = %s AND a.escola_id = %s
                GROUP BY m.status
            """, (ano_letivo_id, escola_id))
            
            resultados = cursor.fetchall()
            matriculas_por_status = {}
            
            if resultados:
                if isinstance(resultados[0], dict):
                    matriculas_por_status = {r['status']: r['total'] for r in resultados}
                else:
                    matriculas_por_status = {r[0]: r[1] for r in resultados}
            
            estatisticas['matriculas_por_status'] = matriculas_por_status
            
            # Taxa de conclusão (se houver dados de conclusão)
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM matriculas m
                INNER JOIN alunos a ON m.aluno_id = a.id
                WHERE m.ano_letivo_id = %s 
                AND a.escola_id = %s 
                AND m.status = 'Concluído'
            """, (ano_letivo_id, escola_id))
            resultado = cursor.fetchone()
            concluidos = resultado[0] if resultado else 0
            
            if estatisticas['total_matriculas'] > 0:
                estatisticas['taxa_conclusao'] = (
                    concluidos / estatisticas['total_matriculas'] * 100
                )
            else:
                estatisticas['taxa_conclusao'] = 0
            
            logger.info(f"Estatísticas do ano letivo {ano_letivo_id} calculadas")
            return estatisticas
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao calcular estatísticas do ano letivo {ano_letivo_id}")
        return None
    except Exception as e:
        logger.exception(f"Erro inesperado ao calcular estatísticas do ano letivo {ano_letivo_id}")
        return None


def obter_alunos_por_situacao(situacao: str, escola_id: int = 60) -> List[Dict]:
    """
    Lista alunos em uma determinada situação.
    
    Args:
        situacao: 'com_matricula', 'sem_matricula', 'transferido', 'evadido'
        escola_id: ID da escola (padrão: 60)
        
    Returns:
        list: Lista de alunos
    """
    try:
        with get_cursor() as cursor:
            if situacao == 'sem_matricula':
                cursor.execute("""
                    SELECT DISTINCT a.*
                    FROM alunos a
                    LEFT JOIN matriculas m ON a.id = m.aluno_id AND m.status = 'Ativo'
                    WHERE a.escola_id = %s AND m.id IS NULL
                    ORDER BY a.nome
                """, (escola_id,))
                
            elif situacao == 'com_matricula':
                cursor.execute("""
                    SELECT DISTINCT a.*
                    FROM alunos a
                    INNER JOIN matriculas m ON a.id = m.aluno_id
                    WHERE a.escola_id = %s AND m.status = 'Ativo'
                    ORDER BY a.nome
                """, (escola_id,))
                
            elif situacao in ['transferido', 'evadido', 'cancelado']:
                cursor.execute("""
                    SELECT DISTINCT a.*
                    FROM alunos a
                    INNER JOIN matriculas m ON a.id = m.aluno_id
                    WHERE a.escola_id = %s AND m.status = %s
                    ORDER BY a.nome
                """, (escola_id, situacao.capitalize()))
                
            else:
                logger.warning(f"Situação desconhecida: {situacao}")
                return []
            
            resultados = cursor.fetchall()
            
            if not resultados:
                return []
            
            # Converter para lista de dicts
            if isinstance(resultados[0], dict):
                return resultados
            else:
                colunas = [desc[0] for desc in cursor.description]
                return [dict(zip(colunas, r)) for r in resultados]
                
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao obter alunos por situação '{situacao}'")
        return []
    except Exception as e:
        logger.exception(f"Erro inesperado ao obter alunos por situação '{situacao}'")
        return []


def calcular_media_idade_alunos(escola_id: int = 60) -> Optional[float]:
    """
    Calcula a média de idade dos alunos ativos.
    
    Args:
        escola_id: ID da escola (padrão: 60)
        
    Returns:
        float: Média de idade ou None
    """
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT AVG(TIMESTAMPDIFF(YEAR, a.data_nascimento, CURDATE())) as media_idade
                FROM alunos a
                INNER JOIN matriculas m ON a.id = m.aluno_id
                WHERE a.escola_id = %s 
                AND m.status = 'Ativo'
                AND a.data_nascimento IS NOT NULL
            """, (escola_id,))
            
            resultado = cursor.fetchone()
            
            if resultado and resultado[0] is not None:
                media = float(resultado[0])
                logger.debug(f"Média de idade calculada: {media:.1f} anos")
                return media
            
            return None
            
    except MySQLError as e:
        logger.exception("Erro MySQL ao calcular média de idade")
        return None
    except Exception as e:
        logger.exception("Erro inesperado ao calcular média de idade")
        return None
