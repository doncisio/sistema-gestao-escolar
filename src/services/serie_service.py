"""
Serviço de gerenciamento de séries escolares

Este módulo encapsula toda a lógica de negócio relacionada a séries:
- Listagem de séries por ciclo
- Consulta de séries individuais
- Validação de progressão entre séries
- Informações de séries do sistema educacional brasileiro
"""

from typing import List, Dict, Any, Optional
from db.connection import get_connection
from src.core.config_logs import get_logger

logger = get_logger(__name__)


def listar_series(ciclo: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lista todas as séries ou filtra por ciclo.
    
    Args:
        ciclo: Filtro por ciclo ('Ensino Infantil', 'Ensino Fundamental I',
               'Ensino Fundamental II', 'Ensino Médio', None = todas)
    
    Returns:
        Lista de dicionários com dados das séries
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            if ciclo:
                cursor.execute("""
                    SELECT id, nome, ciclo, ordem
                    FROM series
                    WHERE ciclo = %s
                    ORDER BY ordem, nome
                """, (ciclo,))
            else:
                cursor.execute("""
                    SELECT id, nome, ciclo, ordem
                    FROM series
                    ORDER BY ordem, nome
                """)
            
            series = cursor.fetchall()
            
            logger.debug(f"Listadas {len(series)} séries (ciclo={ciclo})")
            return series
            
    except Exception as e:
        logger.exception(f"Erro ao listar séries: {e}")
        raise


def obter_serie_por_id(serie_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtém dados de uma série pelo ID.
    
    Args:
        serie_id: ID da série
    
    Returns:
        Dicionário com dados da série ou None se não encontrada
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, nome, ciclo, ordem
                FROM series
                WHERE id = %s
            """, (serie_id,))
            
            serie = cursor.fetchone()
            
            if serie:
                logger.debug(f"Série {serie_id} encontrada: {serie['nome']}")
            else:
                logger.warning(f"Série {serie_id} não encontrada")
            
            return serie
            
    except Exception as e:
        logger.exception(f"Erro ao obter série {serie_id}: {e}")
        raise


def obter_serie_por_nome(nome: str) -> Optional[Dict[str, Any]]:
    """
    Obtém dados de uma série pelo nome.
    
    Args:
        nome: Nome da série (ex: "1º Ano", "5ª Série")
    
    Returns:
        Dicionário com dados da série ou None se não encontrada
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, nome, ciclo, ordem
                FROM series
                WHERE nome = %s
            """, (nome,))
            
            serie = cursor.fetchone()
            
            if serie:
                logger.debug(f"Série '{nome}' encontrada: ID={serie['id']}")
            else:
                logger.warning(f"Série '{nome}' não encontrada")
            
            return serie
            
    except Exception as e:
        logger.exception(f"Erro ao obter série por nome '{nome}': {e}")
        raise


def listar_series_por_ciclo(ciclo: str) -> List[Dict[str, Any]]:
    """
    Lista séries de um ciclo específico.
    
    Args:
        ciclo: Nome do ciclo ('Ensino Infantil', 'Ensino Fundamental I', etc.)
    
    Returns:
        Lista de séries do ciclo ordenadas
    """
    return listar_series(ciclo=ciclo)


def obter_proxima_serie(serie_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtém a próxima série na sequência educacional.
    Útil para progressão automática de alunos.
    
    Args:
        serie_id: ID da série atual
    
    Returns:
        Dicionário com dados da próxima série ou None se for a última
    """
    try:
        serie_atual = obter_serie_por_id(serie_id)
        if not serie_atual:
            return None
        
        ordem_atual = serie_atual.get('ordem', 0)
        
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Buscar série com ordem imediatamente superior
            cursor.execute("""
                SELECT id, nome, ciclo, ordem
                FROM series
                WHERE ordem > %s
                ORDER BY ordem
                LIMIT 1
            """, (ordem_atual,))
            
            proxima_serie = cursor.fetchone()
            
            if proxima_serie:
                logger.debug(f"Próxima série após {serie_atual['nome']}: {proxima_serie['nome']}")
            else:
                logger.debug(f"Série {serie_atual['nome']} é a última do sistema")
            
            return proxima_serie
            
    except Exception as e:
        logger.exception(f"Erro ao obter próxima série de {serie_id}: {e}")
        raise


def obter_serie_anterior(serie_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtém a série anterior na sequência educacional.
    
    Args:
        serie_id: ID da série atual
    
    Returns:
        Dicionário com dados da série anterior ou None se for a primeira
    """
    try:
        serie_atual = obter_serie_por_id(serie_id)
        if not serie_atual:
            return None
        
        ordem_atual = serie_atual.get('ordem', 0)
        
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Buscar série com ordem imediatamente inferior
            cursor.execute("""
                SELECT id, nome, ciclo, ordem
                FROM series
                WHERE ordem < %s
                ORDER BY ordem DESC
                LIMIT 1
            """, (ordem_atual,))
            
            serie_anterior = cursor.fetchone()
            
            if serie_anterior:
                logger.debug(f"Série anterior a {serie_atual['nome']}: {serie_anterior['nome']}")
            else:
                logger.debug(f"Série {serie_atual['nome']} é a primeira do sistema")
            
            return serie_anterior
            
    except Exception as e:
        logger.exception(f"Erro ao obter série anterior de {serie_id}: {e}")
        raise


def validar_progressao_serie(serie_origem_id: int, serie_destino_id: int) -> tuple[bool, str]:
    """
    Valida se a progressão entre duas séries é válida.
    
    Args:
        serie_origem_id: ID da série de origem
        serie_destino_id: ID da série de destino
    
    Returns:
        Tupla (é_valido, mensagem)
    """
    try:
        serie_origem = obter_serie_por_id(serie_origem_id)
        serie_destino = obter_serie_por_id(serie_destino_id)
        
        if not serie_origem:
            return False, f"Série de origem {serie_origem_id} não encontrada"
        
        if not serie_destino:
            return False, f"Série de destino {serie_destino_id} não encontrada"
        
        ordem_origem = serie_origem.get('ordem', 0)
        ordem_destino = serie_destino.get('ordem', 0)
        
        # Progressão válida: ordem destino deve ser maior que origem
        if ordem_destino <= ordem_origem:
            return False, f"Progressão inválida: {serie_destino['nome']} não é posterior a {serie_origem['nome']}"
        
        # Verificar se há séries intermediárias (progressão deve ser sequencial)
        diff_ordem = ordem_destino - ordem_origem
        if diff_ordem > 1:
            # Permitir pulo de série apenas se justificado (pode ser configurado)
            logger.warning(f"Progressão pulando {diff_ordem-1} série(s): {serie_origem['nome']} -> {serie_destino['nome']}")
            return True, f"Atenção: progressão pulando série(s). Verificar se é intencional."
        
        logger.debug(f"Progressão válida: {serie_origem['nome']} -> {serie_destino['nome']}")
        return True, "Progressão válida"
        
    except Exception as e:
        logger.exception(f"Erro ao validar progressão: {e}")
        return False, f"Erro ao validar progressão: {str(e)}"


def obter_estatisticas_serie(serie_id: int, ano_letivo_id: int) -> Dict[str, Any]:
    """
    Obtém estatísticas de uma série em um ano letivo.
    
    Args:
        serie_id: ID da série
        ano_letivo_id: ID do ano letivo
    
    Returns:
        Dicionário com estatísticas (total_turmas, total_alunos, etc.)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    s.id,
                    s.nome,
                    s.ciclo,
                    COUNT(DISTINCT t.id) as total_turmas,
                    COALESCE(SUM(t.capacidade_maxima), 0) as capacidade_total,
                    COUNT(DISTINCT m.id) as total_alunos,
                    COUNT(DISTINCT CASE WHEN m.status = 'Ativo' THEN m.id END) as alunos_ativos,
                    COUNT(DISTINCT CASE WHEN m.status IN ('Transferido', 'Transferida') THEN m.id END) as alunos_transferidos
                FROM series s
                LEFT JOIN turmas t ON s.id = t.serie_id AND t.ano_letivo_id = %s
                LEFT JOIN Matriculas m ON t.id = m.turma_id
                WHERE s.id = %s
                GROUP BY s.id, s.nome, s.ciclo
            """, (ano_letivo_id, serie_id))
            
            stats = cursor.fetchone()
            
            if stats:
                # Calcular taxa de ocupação
                capacidade = stats.get('capacidade_total', 0)
                alunos = stats.get('alunos_ativos', 0)
                
                if capacidade > 0:
                    stats['taxa_ocupacao'] = round((alunos / capacidade) * 100, 2)
                else:
                    stats['taxa_ocupacao'] = 0.0
                
                logger.debug(f"Estatísticas série {serie_id}: {alunos} alunos, {stats['total_turmas']} turmas")
            else:
                logger.warning(f"Nenhuma estatística encontrada para série {serie_id}")
                stats = {
                    'id': serie_id,
                    'total_turmas': 0,
                    'total_alunos': 0,
                    'alunos_ativos': 0,
                    'alunos_transferidos': 0,
                    'capacidade_total': 0,
                    'taxa_ocupacao': 0.0
                }
            
            return stats
            
    except Exception as e:
        logger.exception(f"Erro ao obter estatísticas da série {serie_id}: {e}")
        raise


def buscar_series(termo: str) -> List[Dict[str, Any]]:
    """
    Busca séries por nome ou ciclo.
    
    Args:
        termo: Termo de busca
    
    Returns:
        Lista de séries encontradas
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, nome, ciclo, ordem
                FROM series
                WHERE nome LIKE %s OR ciclo LIKE %s
                ORDER BY ordem, nome
            """, (f"%{termo}%", f"%{termo}%"))
            
            series = cursor.fetchall()
            
            logger.info(f"Busca '{termo}' encontrou {len(series)} séries")
            return series
            
    except Exception as e:
        logger.exception(f"Erro ao buscar séries: {e}")
        raise


def obter_ciclos() -> List[str]:
    """
    Obtém lista de todos os ciclos educacionais disponíveis.
    
    Returns:
        Lista de nomes de ciclos
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT ciclo
                FROM series
                ORDER BY MIN(ordem)
            """)
            
            resultados = cursor.fetchall()
            ciclos = [r[0] for r in resultados if r[0]]
            
            logger.debug(f"Ciclos encontrados: {ciclos}")
            return ciclos
            
    except Exception as e:
        logger.exception(f"Erro ao obter ciclos: {e}")
        raise
