"""
Serviço para cálculo de estatísticas de alunos.
Extrai lógica de estatísticas do main.py.
"""

from typing import Dict, List, Optional
from mysql.connector import Error as MySQLError
import logging
from db.connection import get_cursor
from utils.cache import dashboard_cache

logger = logging.getLogger(__name__)


@dashboard_cache.cached(ttl=600)  # Cache de 10 minutos
def obter_estatisticas_alunos(escola_id: int = 60, ano_letivo: Optional[str] = None) -> Optional[Dict]:
    """
    Calcula estatísticas gerais de alunos da escola (OTIMIZADO + CACHE).
    
    Args:
        escola_id: ID da escola (padrão: 60)
        ano_letivo: Ano letivo para filtrar (ex: '2024'). Se None, usa o ano atual.
        
    Returns:
        dict: Estatísticas ou None em caso de erro
    """
    try:
        logger.debug(f"Iniciando obter_estatisticas_alunos OTIMIZADO para escola_id={escola_id}, ano_letivo={ano_letivo}")
        
        with get_cursor() as cursor:
            if cursor is None:
                logger.error("get_cursor() retornou None")
                return None
            
            # Se ano_letivo não foi especificado, usa o ano atual
            if ano_letivo is None:
                cursor.execute("SELECT ano_letivo FROM AnosLetivos WHERE CURDATE() BETWEEN data_inicio AND data_fim LIMIT 1")
                resultado = cursor.fetchone()
                ano_letivo = resultado['ano_letivo'] if resultado else str(__import__('datetime').datetime.now().year)
                logger.debug(f"Ano letivo: {ano_letivo}")
            
            # QUERY OTIMIZADA: Uma única query com todas as agregações
            logger.debug("Executando query otimizada única...")
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
                    INNER JOIN serie s ON t.serie_id = s.id
                    INNER JOIN alunos a ON m.aluno_id = a.id
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND (m.status = 'Ativo' OR m.status = 'Transferido' OR m.status = 'Transferida')
                )
                SELECT 
                    COUNT(DISTINCT aluno_id) as total_alunos,
                    SUM(CASE WHEN status = 'Ativo' THEN 1 ELSE 0 END) as alunos_ativos,
                    GROUP_CONCAT(DISTINCT CONCAT_WS(':', serie, turma, turno)) as turmas_detalhes
                FROM base_alunos
            """, (ano_letivo, escola_id))
            
            resultado_base = cursor.fetchone()
            
            if not resultado_base:
                return {
                    'total_alunos': 0,
                    'alunos_ativos': 0,
                    'alunos_por_serie': [],
                    'alunos_por_serie_turma': [],
                    'alunos_por_turno': []
                }
            
            # Extrair totais
            estatisticas = {
                'total_alunos': resultado_base['total_alunos'] if isinstance(resultado_base, dict) else resultado_base[0],
                'alunos_ativos': resultado_base['alunos_ativos'] if isinstance(resultado_base, dict) else resultado_base[1]
            }
            
            logger.debug(f"Total: {estatisticas['total_alunos']}, Ativos: {estatisticas['alunos_ativos']}")
            
            # Agora buscar agregações por série e turma (queries menores)
            cursor.execute("""
                SELECT 
                    s.nome as serie, 
                    COUNT(DISTINCT m.aluno_id) as total
                FROM matriculas m
                INNER JOIN turmas t ON m.turma_id = t.id
                INNER JOIN serie s ON t.serie_id = s.id
                INNER JOIN alunos a ON m.aluno_id = a.id
                WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                  AND a.escola_id = %s
                  AND (m.status = 'Ativo' OR m.status = 'Transferido' OR m.status = 'Transferida')
                GROUP BY s.id, s.nome
                ORDER BY s.nome
            """, (ano_letivo, escola_id))
            
            resultados = cursor.fetchall()
            alunos_por_serie = []
            if resultados:
                if isinstance(resultados[0], dict):
                    alunos_por_serie = [{'serie': r['serie'], 'quantidade': r['total']} for r in resultados]
                else:
                    alunos_por_serie = [{'serie': r[0], 'quantidade': r[1]} for r in resultados]
            
            estatisticas['alunos_por_serie'] = alunos_por_serie
            logger.debug(f"Séries: {len(alunos_por_serie)}")
            
            # Alunos por série E turma
            cursor.execute("""
                SELECT 
                    s.nome as serie, 
                    t.nome as turma,
                    COUNT(DISTINCT m.aluno_id) as total
                FROM matriculas m
                INNER JOIN turmas t ON m.turma_id = t.id
                INNER JOIN serie s ON t.serie_id = s.id
                INNER JOIN alunos a ON m.aluno_id = a.id
                WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                  AND a.escola_id = %s
                  AND (m.status = 'Ativo' OR m.status = 'Transferido' OR m.status = 'Transferida')
                GROUP BY s.id, s.nome, t.id, t.nome
                ORDER BY s.nome, t.nome
            """, (ano_letivo, escola_id))
            
            resultados = cursor.fetchall()
            alunos_por_turma = []
            if resultados:
                if isinstance(resultados[0], dict):
                    alunos_por_turma = [{'serie': r['serie'], 'turma': r['turma'], 'quantidade': r['total']} for r in resultados]
                else:
                    alunos_por_turma = [{'serie': r[0], 'turma': r[1], 'quantidade': r[2]} for r in resultados]
            
            estatisticas['alunos_por_serie_turma'] = alunos_por_turma
            logger.debug(f"Turmas: {len(alunos_por_turma)}")
            
            # Alunos por turno (apenas ativos, sem transferidos)
            cursor.execute("""
                SELECT t.turno, COUNT(DISTINCT m.aluno_id) as total
                FROM matriculas m
                INNER JOIN turmas t ON m.turma_id = t.id
                INNER JOIN alunos a ON m.aluno_id = a.id
                WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                  AND a.escola_id = %s
                  AND m.status = 'Ativo'
                GROUP BY t.turno
            """, (ano_letivo, escola_id))
            
            resultados = cursor.fetchall()
            alunos_por_turno = []
            
            if resultados:
                if isinstance(resultados[0], dict):
                    alunos_por_turno = [{'turno': r['turno'], 'quantidade': r['total']} for r in resultados]
                else:
                    alunos_por_turno = [{'turno': r[0], 'quantidade': r[1]} for r in resultados]
            
            estatisticas['alunos_por_turno'] = alunos_por_turno
            
            # Alunos transferidos no ano letivo
            cursor.execute("""
                SELECT COUNT(DISTINCT m.aluno_id) as total
                FROM matriculas m
                INNER JOIN alunos a ON m.aluno_id = a.id
                WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                  AND a.escola_id = %s
                  AND (m.status = 'Transferido' OR m.status = 'Transferida')
            """, (ano_letivo, escola_id))
            resultado = cursor.fetchone()
            estatisticas['alunos_transferidos'] = resultado['total'] if resultado else 0
            
            # Alunos sem matrícula (calculado como diferença)
            # Total no cadastro - Total com matrícula ativa/transferida
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM alunos
                WHERE escola_id = %s
            """, (escola_id,))
            resultado = cursor.fetchone()
            total_cadastrados = resultado['total'] if resultado else 0
            
            estatisticas['alunos_sem_matricula'] = (
                total_cadastrados - estatisticas['total_alunos']
            )
            
            logger.debug(f"Estatísticas calculadas com sucesso: {estatisticas['total_alunos']} alunos total, {len(alunos_por_serie)} séries")
            return estatisticas
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao calcular estatísticas de alunos: {e}")
        return None
    except Exception as e:
        logger.exception(f"Erro inesperado ao calcular estatísticas de alunos: {e}")
        return None


@dashboard_cache.cached(ttl=600)  # Cache de 10 minutos
def obter_estatisticas_por_ano_letivo(ano_letivo_id: int, escola_id: int = 60) -> Optional[Dict]:
    """
    Calcula estatísticas de alunos para um ano letivo específico (CACHE).
    
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


@dashboard_cache.cached(ttl=300)  # Cache de 5 minutos
def calcular_media_idade_alunos(escola_id: int = 60) -> Optional[float]:
    """
    Calcula a média de idade dos alunos ativos (CACHE).
    
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
