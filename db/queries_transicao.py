"""
Queries SQL centralizadas para Transição de Ano Letivo

Este módulo contém queries reutilizáveis para operações de transição:
- Consultas de turmas e séries
- Consultas de alunos por status
- Consultas de matrículas
- Queries de progressão de série

Benefícios:
- Eliminação de SQL inline duplicado
- Facilita manutenção e auditoria
- Queries otimizadas e testadas
"""

from typing import List, Dict, Any, Optional, Tuple
from db.connection import get_cursor
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# QUERIES DE ANOS LETIVOS
# ============================================================================

QUERY_ANO_LETIVO_ATUAL = """
    SELECT id, ano_letivo, data_inicio, data_fim
    FROM anosletivos 
    WHERE ano_letivo = YEAR(CURDATE())
"""

QUERY_ANO_LETIVO_RECENTE = """
    SELECT id, ano_letivo, data_inicio, data_fim
    FROM anosletivos 
    ORDER BY ano_letivo DESC 
    LIMIT 1
"""

QUERY_ANO_LETIVO_POR_ANO = """
    SELECT id, ano_letivo, data_inicio, data_fim
    FROM anosletivos 
    WHERE ano_letivo = %s
"""

QUERY_CRIAR_ANO_LETIVO = """
    INSERT INTO anosletivos (ano_letivo)
    VALUES (%s)
    ON DUPLICATE KEY UPDATE ano_letivo = ano_letivo
"""

# ============================================================================
# QUERIES DE TURMAS E SÉRIES
# ============================================================================

# ============================================================================
# QUERIES DE TURMAS E SÉRIES
# ============================================================================
# 
# ESTRUTURA DE TURMAS:
# - Uma SÉRIE pode ter uma ou mais TURMAS
# - Se série tem turma única: turma.nome = '' (vazio)
# - Se série tem várias turmas: turma.nome = 'A', 'B', 'C', ...
# - Exemplos:
#   * "1º Ano" (série) + "" (turma) = apenas "1º Ano"
#   * "6º Ano" (série) + "A" (turma) = "6º Ano A"
#   * "6º Ano" (série) + "B" (turma) = "6º Ano B"
#
# PROGRESSÃO:
# - Usa o ID da série para determinar a próxima (serie_id + 1)
# - Mantém o turno (MAT/VESP) e nome da turma (A, B, etc.) quando possível
# ============================================================================

QUERY_TURMAS_9ANO = """
    SELECT t.id
    FROM turmas t
    JOIN series s ON t.serie_id = s.id
    WHERE s.nome LIKE '9%%'
    AND t.escola_id = %s
"""

QUERY_TURMAS_POR_SERIE = """
    SELECT 
        t.id as turma_id,
        t.nome as turma_nome,
        s.id as serie_id,
        s.nome as serie_nome,
        t.turno
    FROM turmas t
    JOIN series s ON t.serie_id = s.id
    WHERE t.escola_id = %s
    ORDER BY s.id, t.nome
"""

# Busca a próxima série baseado no ID (id + 1)
QUERY_PROXIMA_SERIE = """
    SELECT s.id as proxima_serie_id, s.nome as proxima_serie_nome
    FROM series s
    WHERE s.id = (
        SELECT s2.id + 1
        FROM series s2
        WHERE s2.id = %s
    )
    LIMIT 1
"""

# Busca a turma da próxima série, mantendo turno e nome da turma quando possível
# Prioridade: 1) mesmo turno + mesmo nome, 2) mesmo turno + qualquer nome, 3) qualquer turma
# Parâmetros: (turma_atual_id, escola_id, ano_letivo_destino_id, turma_atual_id, turma_atual_id)
QUERY_TURMA_PROXIMA_SERIE = """
    SELECT t.id as turma_id, t.nome as turma_nome, s.nome as serie_nome, t.turno
    FROM turmas t
    JOIN series s ON t.serie_id = s.id
    WHERE s.id = (
        SELECT s2.id + 1
        FROM series s2
        JOIN turmas t2 ON s2.id = t2.serie_id
        WHERE t2.id = %s
    )
    AND t.escola_id = %s
    AND t.ano_letivo_id = %s
    ORDER BY 
        CASE WHEN t.turno = (SELECT turno FROM turmas WHERE id = %s) THEN 0 ELSE 1 END,
        CASE WHEN t.nome = (SELECT nome FROM turmas WHERE id = %s) THEN 0 ELSE 1 END
    LIMIT 1
"""

# ============================================================================
# QUERIES DE MATRÍCULAS
# ============================================================================

QUERY_TOTAL_MATRICULAS_ATIVAS = """
    SELECT COUNT(DISTINCT a.id) as total
    FROM alunos a
    JOIN matriculas m ON a.id = m.aluno_id
    WHERE m.ano_letivo_id = %s
    AND m.status = 'Ativo'
    AND a.escola_id = %s
"""

QUERY_ALUNOS_CONTINUAR = """
    SELECT COUNT(DISTINCT a.id) as total
    FROM alunos a
    JOIN matriculas m ON a.id = m.aluno_id
    WHERE m.ano_letivo_id = %s
    AND m.status IN ('Ativo', 'Concluído', 'Concluido', 'Concluída', 'Concluida')
    AND m.status NOT IN ('Transferido', 'Transferida', 'Cancelado', 'Cancelada', 'Evadido', 'Evadida')
    AND a.escola_id = %s
    AND m.turma_id NOT IN ({turmas_placeholder})
"""

QUERY_ALUNOS_EXCLUIR = """
    SELECT COUNT(DISTINCT a.id) as total
    FROM alunos a
    JOIN matriculas m ON a.id = m.aluno_id
    WHERE m.ano_letivo_id = %s
    AND m.status IN ('Transferido', 'Transferida', 'Cancelado', 'Cancelada', 'Evadido', 'Evadida')
    AND a.escola_id = %s
"""

QUERY_ENCERRAR_MATRICULAS = """
    UPDATE matriculas
    SET status = 'Concluído'
    WHERE ano_letivo_id = %s
    AND status = 'Ativo'
"""

QUERY_CRIAR_MATRICULA = """
    INSERT INTO matriculas (aluno_id, turma_id, ano_letivo_id, status)
    VALUES (%s, %s, %s, 'Ativo')
"""

# ============================================================================
# QUERIES DE ALUNOS PARA REMATRICULAR
# ============================================================================

QUERY_ALUNOS_NORMAIS = """
    SELECT DISTINCT 
        a.id as aluno_id,
        m.turma_id,
        t.turno,
        s.id as serie_id,
        s.nome as serie_nome
    FROM alunos a
    JOIN matriculas m ON a.id = m.aluno_id
    JOIN turmas t ON m.turma_id = t.id
    JOIN series s ON t.serie_id = s.id
    WHERE m.ano_letivo_id = %s
    AND m.status IN (
        'Ativo', 'Concluído', 'Concluido', 'Concluída', 'Concluida'
    )
    AND m.status NOT IN (
        'Transferido', 'Transferida', 'Cancelado', 'Cancelada', 'Evadido', 'Evadida'
    )
    AND a.escola_id = %s
    AND m.turma_id NOT IN ({turmas_placeholder})
    AND s.nome NOT LIKE '9%'
"""

QUERY_ALUNOS_REPROVADOS = """
    SELECT DISTINCT 
        a.id as aluno_id,
        m.turma_id,
        t.turno,
        s.id as serie_id,
        s.nome as serie_nome,
        MIN(nf.media_final) as media_final
    FROM alunos a
    JOIN matriculas m ON a.id = m.aluno_id
    JOIN turmas t ON m.turma_id = t.id
    JOIN series s ON t.serie_id = s.id
    LEFT JOIN notas_finais nf ON a.id = nf.aluno_id AND nf.ano_letivo_id = %s
    WHERE m.ano_letivo_id = %s
    AND m.status IN (
        'Ativo', 'Concluído', 'Concluido', 'Concluída', 'Concluida'
    )
    AND m.status NOT IN (
        'Transferido', 'Transferida', 'Cancelado', 'Cancelada', 'Evadido', 'Evadida'
    )
    AND a.escola_id = %s
    AND s.nome NOT LIKE '9%'
    GROUP BY a.id, m.turma_id, t.turno, s.id, s.nome
    HAVING (MIN(nf.media_final) < 60 OR MIN(nf.media_final) IS NULL)
        OR m.status IN ('Reprovado', 'Reprovada')
"""

# ============================================================================
# QUERIES DE AUDITORIA
# ============================================================================

QUERY_CRIAR_TABELA_AUDITORIA = """
    CREATE TABLE IF NOT EXISTS auditoria_transicao (
        id INT AUTO_INCREMENT PRIMARY KEY,
        data_execucao DATETIME DEFAULT CURRENT_TIMESTAMP,
        ano_origem INT NOT NULL,
        ano_destino INT NOT NULL,
        escola_id INT NOT NULL,
        usuario VARCHAR(100),
        matriculas_encerradas INT DEFAULT 0,
        matriculas_criadas INT DEFAULT 0,
        alunos_promovidos INT DEFAULT 0,
        alunos_retidos INT DEFAULT 0,
        alunos_concluintes INT DEFAULT 0,
        status ENUM('sucesso', 'erro', 'rollback') DEFAULT 'sucesso',
        detalhes TEXT,
        INDEX idx_ano_origem (ano_origem),
        INDEX idx_escola (escola_id),
        INDEX idx_data (data_execucao)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

QUERY_REGISTRAR_AUDITORIA = """
    INSERT INTO auditoria_transicao (
        ano_origem, ano_destino, escola_id, usuario,
        matriculas_encerradas, matriculas_criadas,
        alunos_promovidos, alunos_retidos, alunos_concluintes,
        status, detalhes
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

QUERY_BUSCAR_AUDITORIA = """
    SELECT * FROM auditoria_transicao
    WHERE escola_id = %s
    ORDER BY data_execucao DESC
    LIMIT %s
"""

# ============================================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================================

class QueriesTransicao:
    """Classe com métodos utilitários para queries de transição"""
    
    @staticmethod
    def get_turmas_9ano(escola_id: int) -> List[int]:
        """Retorna IDs das turmas do 9º ano.
        
        Args:
            escola_id: ID da escola
            
        Returns:
            Lista de IDs das turmas do 9º ano
        """
        with get_cursor() as cursor:
            cursor.execute(QUERY_TURMAS_9ANO, (escola_id,))
            rows = cursor.fetchall()
            return [row['id'] for row in rows] if rows else []
    
    @staticmethod
    def get_ano_letivo_atual() -> Optional[Dict]:
        """Retorna dados do ano letivo atual.
        
        Returns:
            Dict com id, ano_letivo, data_inicio, data_fim ou None
        """
        with get_cursor() as cursor:
            cursor.execute(QUERY_ANO_LETIVO_ATUAL)
            resultado = cursor.fetchone()
            
            if not resultado:
                cursor.execute(QUERY_ANO_LETIVO_RECENTE)
                resultado = cursor.fetchone()
            
            return resultado
    
    @staticmethod
    def get_ano_letivo_por_ano(ano: int) -> Optional[Dict]:
        """Busca ano letivo pelo número do ano.
        
        Args:
            ano: Ano a buscar (ex: 2025)
            
        Returns:
            Dict com dados do ano letivo ou None
        """
        with get_cursor() as cursor:
            cursor.execute(QUERY_ANO_LETIVO_POR_ANO, (ano,))
            return cursor.fetchone()
    
    @staticmethod
    def get_total_matriculas_ativas(ano_letivo_id: int, escola_id: int) -> int:
        """Retorna total de matrículas ativas.
        
        Args:
            ano_letivo_id: ID do ano letivo
            escola_id: ID da escola
            
        Returns:
            Total de matrículas ativas
        """
        with get_cursor() as cursor:
            cursor.execute(QUERY_TOTAL_MATRICULAS_ATIVAS, (ano_letivo_id, escola_id))
            resultado = cursor.fetchone()
            return resultado['total'] if resultado else 0
    
    @staticmethod
    def get_alunos_a_excluir(ano_letivo_id: int, escola_id: int) -> int:
        """Retorna contagem de alunos com status de exclusão.
        
        Args:
            ano_letivo_id: ID do ano letivo
            escola_id: ID da escola
            
        Returns:
            Total de alunos transferidos/cancelados/evadidos
        """
        with get_cursor() as cursor:
            cursor.execute(QUERY_ALUNOS_EXCLUIR, (ano_letivo_id, escola_id))
            resultado = cursor.fetchone()
            return resultado['total'] if resultado else 0
    
    @staticmethod
    def get_alunos_para_rematricular(
        ano_letivo_id: int, 
        escola_id: int, 
        turmas_9ano: List[int]
    ) -> Tuple[List[Dict], List[Dict]]:
        """Retorna alunos normais e reprovados para rematricular.
        
        Args:
            ano_letivo_id: ID do ano letivo
            escola_id: ID da escola
            turmas_9ano: Lista de IDs das turmas do 9º ano
            
        Returns:
            Tuple (alunos_normais, alunos_reprovados)
        """
        alunos_normais = []
        alunos_reprovados = []
        
        with get_cursor() as cursor:
            # Alunos normais (exceto 9º ano)
            if turmas_9ano:
                placeholder = ','.join(['%s'] * len(turmas_9ano))
                query = QUERY_ALUNOS_NORMAIS.format(turmas_placeholder=placeholder)
                cursor.execute(query, (ano_letivo_id, escola_id) + tuple(turmas_9ano))
            else:
                query = QUERY_ALUNOS_NORMAIS.format(turmas_placeholder="0")
                cursor.execute(query, (ano_letivo_id, escola_id))

            alunos_normais = cursor.fetchall() or []

            # Fallback defensivo: se nada vier, tentar sem o filtro de NOT IN (pode haver diferença de IDs de turmas do 9º)
            if not alunos_normais:
                try:
                    query_sem_not_in = QUERY_ALUNOS_NORMAIS.format(turmas_placeholder="0")
                    cursor.execute(query_sem_not_in, (ano_letivo_id, escola_id))
                    alunos_normais = cursor.fetchall() or []
                except Exception:
                    pass
            
            # Alunos reprovados
            cursor.execute(QUERY_ALUNOS_REPROVADOS, (ano_letivo_id, ano_letivo_id, escola_id))
            alunos_reprovados = cursor.fetchall() or []
        
        return alunos_normais, alunos_reprovados
    
    @staticmethod
    def get_mapa_turmas(escola_id: int) -> Dict[int, Dict]:
        """Retorna mapa de turmas com informações de série.
        
        Args:
            escola_id: ID da escola
            
        Returns:
            Dict mapeando turma_id para dados da turma/série
        """
        with get_cursor() as cursor:
            cursor.execute(QUERY_TURMAS_POR_SERIE, (escola_id,))
            rows = cursor.fetchall() or []
            return {row['turma_id']: row for row in rows}
    
    @staticmethod
    def get_proxima_turma(turma_atual_id: int, escola_id: int, ano_letivo_destino_id: int = None) -> Optional[int]:
        """Obtém a turma da próxima série mantendo o turno.
        
        Args:
            turma_atual_id: ID da turma atual
            escola_id: ID da escola
            ano_letivo_destino_id: ID do ano letivo de destino (opcional, para compatibilidade)
            
        Returns:
            ID da turma da próxima série ou None se não encontrar
        """
        # Se não especificar ano destino, usa o mesmo ano da turma atual (compatibilidade)
        if ano_letivo_destino_id is None:
            with get_cursor() as cursor:
                cursor.execute("SELECT ano_letivo_id FROM turmas WHERE id = %s", (turma_atual_id,))
                result = cursor.fetchone()
                ano_letivo_destino_id = result['ano_letivo_id'] if result else None
        
        if not ano_letivo_destino_id:
            return None
            
        with get_cursor() as cursor:
            cursor.execute(
                QUERY_TURMA_PROXIMA_SERIE,
                (turma_atual_id, escola_id, ano_letivo_destino_id, turma_atual_id, turma_atual_id)
            )
            resultado = cursor.fetchone()
            return resultado['turma_id'] if resultado else None
    
    @staticmethod
    def criar_tabela_auditoria() -> bool:
        """Cria tabela de auditoria se não existir.
        
        Returns:
            True se criada/existe, False em caso de erro
        """
        try:
            with get_cursor() as cursor:
                cursor.execute(QUERY_CRIAR_TABELA_AUDITORIA)
            logger.info("Tabela de auditoria verificada/criada")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar tabela de auditoria: {e}")
            return False
    
    @staticmethod
    def registrar_auditoria(
        ano_origem: int,
        ano_destino: int,
        escola_id: int,
        usuario: str = None,
        matriculas_encerradas: int = 0,
        matriculas_criadas: int = 0,
        alunos_promovidos: int = 0,
        alunos_retidos: int = 0,
        alunos_concluintes: int = 0,
        status: str = 'sucesso',
        detalhes: str = None
    ) -> bool:
        """Registra uma transição na tabela de auditoria.
        
        Returns:
            True se registrado com sucesso, False caso contrário
        """
        try:
            # Garantir que a tabela existe
            QueriesTransicao.criar_tabela_auditoria()
            
            with get_cursor() as cursor:
                cursor.execute(QUERY_REGISTRAR_AUDITORIA, (
                    ano_origem, ano_destino, escola_id, usuario,
                    matriculas_encerradas, matriculas_criadas,
                    alunos_promovidos, alunos_retidos, alunos_concluintes,
                    status, detalhes
                ))
            logger.info(f"Auditoria registrada: {ano_origem} → {ano_destino}")
            return True
        except Exception as e:
            logger.error(f"Erro ao registrar auditoria: {e}")
            return False
    
    @staticmethod
    def buscar_historico_auditoria(escola_id: int, limite: int = 10) -> List[Dict]:
        """Busca histórico de transições realizadas.
        
        Args:
            escola_id: ID da escola
            limite: Número máximo de registros
            
        Returns:
            Lista de registros de auditoria
        """
        try:
            with get_cursor() as cursor:
                cursor.execute(QUERY_BUSCAR_AUDITORIA, (escola_id, limite))
                return cursor.fetchall() or []
        except Exception as e:
            logger.warning(f"Erro ao buscar auditoria: {e}")
            return []


# Funções de conveniência para uso direto
get_turmas_9ano = QueriesTransicao.get_turmas_9ano
get_ano_letivo_atual = QueriesTransicao.get_ano_letivo_atual
get_total_matriculas_ativas = QueriesTransicao.get_total_matriculas_ativas
get_alunos_para_rematricular = QueriesTransicao.get_alunos_para_rematricular
get_proxima_turma = QueriesTransicao.get_proxima_turma
registrar_auditoria = QueriesTransicao.registrar_auditoria
