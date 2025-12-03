"""
Serviço de gerenciamento de turmas

Este módulo encapsula toda a lógica de negócio relacionada a turmas:
- Listagem de turmas por ano letivo, série, turno
- Consulta de turmas individuais
- Criação e atualização de turmas
- Validações de capacidade e horários
"""

from typing import List, Dict, Any, Optional, Tuple
from db.connection import get_connection
from config_logs import get_logger

logger = get_logger(__name__)


def listar_turmas(
    ano_letivo_id: Optional[int] = None,
    serie_id: Optional[int] = None,
    turno: Optional[str] = None,
    escola_id: Optional[int] = None,
    aplicar_filtro_perfil: bool = True
) -> List[Dict[str, Any]]:
    """
    Lista turmas com filtros opcionais.
    
    Args:
        ano_letivo_id: ID do ano letivo (None = todos)
        serie_id: ID da série (None = todas)
        turno: Turno ('Matutino', 'Vespertino', 'Noturno', None = todos)
        escola_id: ID da escola (None = todas)
        aplicar_filtro_perfil: Se True, filtra turmas baseado no perfil do usuário
    
    Returns:
        Lista de dicionários com dados das turmas
    """
    try:
        # Obter filtro de turmas baseado no perfil (se aplicável)
        filtro_perfil_sql = ""
        filtro_perfil_params = []
        
        if aplicar_filtro_perfil:
            try:
                from services.perfil_filter_service import get_sql_filtro_turmas
                filtro_perfil_sql, filtro_perfil_params = get_sql_filtro_turmas("t")
            except ImportError:
                pass  # Módulo não disponível, ignora filtro
        
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Query base
            query = """
                SELECT 
                    t.id,
                    t.nome,
                    t.turno,
                    t.ano_letivo_id,
                    t.serie_id,
                    t.escola_id,
                    s.nome as serie_nome,
                    al.ano_letivo as ano_letivo,
                    COALESCE(COUNT(DISTINCT m.id), 0) as total_alunos
                FROM turmas t
                LEFT JOIN series s ON t.serie_id = s.id
                LEFT JOIN anosletivos al ON t.ano_letivo_id = al.id
                LEFT JOIN Matriculas m ON m.turma_id = t.id AND m.status = 'Ativo'
            """
            
            # Adicionar filtros
            filtros = []
            params = []
            
            if ano_letivo_id is not None:
                filtros.append("t.ano_letivo_id = %s")
                params.append(ano_letivo_id)
            
            if serie_id is not None:
                filtros.append("t.serie_id = %s")
                params.append(serie_id)
            
            if turno is not None:
                filtros.append("t.turno = %s")
                params.append(turno)
            
            if escola_id is not None:
                filtros.append("t.escola_id = %s")
                params.append(escola_id)
            
            # Adicionar filtro base (WHERE 1=1 para facilitar concatenação)
            if filtros:
                query += " WHERE " + " AND ".join(filtros)
            else:
                query += " WHERE 1=1"
            
            # Aplicar filtro de perfil do usuário (professor vê apenas suas turmas)
            if filtro_perfil_sql:
                query += filtro_perfil_sql
                params.extend(filtro_perfil_params)
            
            query += """
                GROUP BY t.id, t.nome, t.turno,
                         t.ano_letivo_id, t.serie_id, t.escola_id,
                         s.nome, al.ano_letivo
                ORDER BY s.nome, t.turno, t.nome
            """
            
            cursor.execute(query, tuple(params))
            turmas = cursor.fetchall()
            
            logger.info(f"Listadas {len(turmas)} turmas (filtros: ano={ano_letivo_id}, serie={serie_id}, turno={turno})")
            return turmas
            
    except Exception as e:
        logger.exception(f"Erro ao listar turmas: {e}")
        raise


def obter_turma_por_id(turma_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtém dados completos de uma turma pelo ID.
    
    Args:
        turma_id: ID da turma
    
    Returns:
        Dicionário com dados da turma ou None se não encontrada
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    t.id,
                    t.nome,
                    t.turno,
                    t.ano_letivo_id,
                    t.serie_id,
                    t.escola_id,
                    s.nome as serie_nome,
                    al.ano_letivo as ano_letivo,
                    COALESCE(COUNT(DISTINCT m.id), 0) as total_alunos
                FROM turmas t
                LEFT JOIN series s ON t.serie_id = s.id
                LEFT JOIN anosletivos al ON t.ano_letivo_id = al.id
                LEFT JOIN Matriculas m ON m.turma_id = t.id AND m.status = 'Ativo'
                WHERE t.id = %s
                GROUP BY t.id, t.nome, t.turno,
                         t.ano_letivo_id, t.serie_id, t.escola_id,
                         s.nome, al.ano_letivo
            """, (turma_id,))
            
            turma = cursor.fetchone()
            
            if turma:
                logger.debug(f"Turma {turma_id} encontrada: {turma['nome']}")
            else:
                logger.warning(f"Turma {turma_id} não encontrada")
            
            return turma
            
    except Exception as e:
        logger.exception(f"Erro ao obter turma {turma_id}: {e}")
        raise


def obter_turmas_por_serie(serie_id: int, ano_letivo_id: int) -> List[Dict[str, Any]]:
    """
    Obtém todas as turmas de uma série em um ano letivo.
    
    Args:
        serie_id: ID da série
        ano_letivo_id: ID do ano letivo
    
    Returns:
        Lista de turmas da série
    """
    return listar_turmas(ano_letivo_id=ano_letivo_id, serie_id=serie_id)


def obter_turmas_por_turno(turno: str, ano_letivo_id: int) -> List[Dict[str, Any]]:
    """
    Obtém todas as turmas de um turno em um ano letivo.
    
    Args:
        turno: Turno ('Matutino', 'Vespertino', 'Noturno')
        ano_letivo_id: ID do ano letivo
    
    Returns:
        Lista de turmas do turno
    """
    return listar_turmas(ano_letivo_id=ano_letivo_id, turno=turno)


def verificar_capacidade_turma(turma_id: int) -> Tuple[bool, int, int]:
    """
    Verifica se a turma tem vagas disponíveis.
    
    NOTA: A tabela turmas não tem coluna capacidade_maxima.
    Esta função retorna sempre True (vaga disponível) e capacidade ilimitada.
    
    Args:
        turma_id: ID da turma
    
    Returns:
        Tupla (tem_vaga, total_alunos, capacidade_maxima)
    """
    try:
        turma = obter_turma_por_id(turma_id)
        
        if not turma:
            logger.warning(f"Turma {turma_id} não encontrada para verificação de capacidade")
            return False, 0, 0
        
        total_alunos = turma.get('total_alunos', 0)
        # A tabela turmas não tem coluna capacidade_maxima
        # Consideramos capacidade ilimitada (sempre tem vaga)
        capacidade_maxima = 999
        tem_vaga = True
        
        logger.debug(f"Capacidade turma {turma_id}: {total_alunos} alunos (capacidade ilimitada)")
        
        return tem_vaga, total_alunos, capacidade_maxima
        
    except Exception as e:
        logger.exception(f"Erro ao verificar capacidade da turma {turma_id}: {e}")
        raise


def criar_turma(
    nome: str,
    turno: str,
    ano_letivo_id: int,
    serie_id: int,
    escola_id: int,
    capacidade_maxima: int = 999,  # Ignorado - coluna não existe
) -> Tuple[bool, str, Optional[int]]:
    """
    Cria uma nova turma.
    
    Args:
        nome: Nome da turma (ex: "A", "B", "Turma 1")
        turno: Turno ('Matutino', 'Vespertino', 'Noturno', 'MAT', 'VESP')
        ano_letivo_id: ID do ano letivo
        serie_id: ID da série
        escola_id: ID da escola
        capacidade_maxima: Ignorado (coluna não existe na tabela)
    
    Returns:
        Tupla (sucesso, mensagem, id_turma)
    """
    try:
        # Validações
        if not nome or not nome.strip():
            return False, "Nome da turma é obrigatório", None
        
        valid_turnos = ['Matutino', 'Vespertino', 'Noturno', 'MAT', 'VESP', 'NOT']
        if turno not in valid_turnos:
            return False, f"Turno inválido: {turno}", None
        
        # Verificar se já existe turma com mesmo nome, série e turno
        turmas_existentes = listar_turmas(
            ano_letivo_id=ano_letivo_id,
            serie_id=serie_id,
            turno=turno,
            escola_id=escola_id,
            aplicar_filtro_perfil=False
        )
        
        if turmas_existentes:
            for turma in turmas_existentes:
                if turma['nome'] and turma['nome'].strip().upper() == nome.strip().upper():
                    return False, f"Já existe uma turma '{nome}' nesta série e turno", None
        
        # Criar turma
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO turmas 
                (nome, turno, ano_letivo_id, serie_id, escola_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (nome.strip(), turno, ano_letivo_id, serie_id, escola_id))
            
            conn.commit()
            turma_id = cursor.lastrowid
            
            logger.info(f"Turma criada: ID={turma_id}, Nome={nome}, Série={serie_id}, Turno={turno}")
            
            return True, f"Turma '{nome}' criada com sucesso", turma_id
            
    except Exception as e:
        logger.exception(f"Erro ao criar turma: {e}")
        return False, f"Erro ao criar turma: {str(e)}", None


def atualizar_turma(
    turma_id: int,
    nome: Optional[str] = None,
    turno: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Atualiza dados de uma turma existente.
    
    Args:
        turma_id: ID da turma
        nome: Novo nome (None = manter)
        turno: Novo turno (None = manter)
    
    Returns:
        Tupla (sucesso, mensagem)
    """
    try:
        # Verificar se turma existe
        turma = obter_turma_por_id(turma_id)
        if not turma:
            return False, f"Turma {turma_id} não encontrada"
        
        # Validações
        valid_turnos = ['Matutino', 'Vespertino', 'Noturno', 'MAT', 'VESP', 'NOT']
        if turno and turno not in valid_turnos:
            return False, f"Turno inválido: {turno}"
        
        # Construir query de atualização
        campos = []
        valores = []
        
        if nome is not None:
            campos.append("nome = %s")
            valores.append(nome.strip())
        
        if turno is not None:
            campos.append("turno = %s")
            valores.append(turno)
        
        if not campos:
            return True, "Nenhuma alteração foi solicitada"
        
        # Executar atualização
        with get_connection() as conn:
            cursor = conn.cursor()
            
            query = f"UPDATE turmas SET {', '.join(campos)} WHERE id = %s"
            valores.append(turma_id)
            
            cursor.execute(query, tuple(valores))
            conn.commit()
            
            logger.info(f"Turma {turma_id} atualizada: {campos}")
            
            return True, "Turma atualizada com sucesso"
            
    except Exception as e:
        logger.exception(f"Erro ao atualizar turma {turma_id}: {e}")
        return False, f"Erro ao atualizar turma: {str(e)}"


def excluir_turma(turma_id: int, verificar_matriculas: bool = True) -> Tuple[bool, str]:
    """
    Exclui uma turma.
    
    Args:
        turma_id: ID da turma
        verificar_matriculas: Se True, impede exclusão se houver matrículas ativas
    
    Returns:
        Tupla (sucesso, mensagem)
    """
    try:
        turma = obter_turma_por_id(turma_id)
        if not turma:
            return False, f"Turma {turma_id} não encontrada"
        
        # Verificar matrículas
        if verificar_matriculas:
            total_alunos = turma.get('total_alunos', 0)
            if total_alunos > 0:
                return False, f"Não é possível excluir: turma possui {total_alunos} aluno(s) matriculado(s)"
        
        # Excluir turma
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM turmas WHERE id = %s", (turma_id,))
            conn.commit()
            
            logger.info(f"Turma {turma_id} excluída: {turma['nome']}")
            
            return True, f"Turma '{turma['nome']}' excluída com sucesso"
            
    except Exception as e:
        logger.exception(f"Erro ao excluir turma {turma_id}: {e}")
        return False, f"Erro ao excluir turma: {str(e)}"


def buscar_turmas(termo: str, ano_letivo_id: Optional[int] = None, aplicar_filtro_perfil: bool = True) -> List[Dict[str, Any]]:
    """
    Busca turmas por nome, série ou turno.
    
    Args:
        termo: Termo de busca
        ano_letivo_id: ID do ano letivo (None = todos)
        aplicar_filtro_perfil: Se True, filtra turmas baseado no perfil do usuário
    
    Returns:
        Lista de turmas encontradas
    """
    try:
        # Obter filtro de turmas baseado no perfil (se aplicável)
        filtro_perfil_sql = ""
        filtro_perfil_params = []
        
        if aplicar_filtro_perfil:
            try:
                from services.perfil_filter_service import get_sql_filtro_turmas
                filtro_perfil_sql, filtro_perfil_params = get_sql_filtro_turmas("t")
            except ImportError:
                pass  # Módulo não disponível, ignora filtro
        
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    t.id,
                    t.nome,
                    t.turno,
                    t.ano_letivo_id,
                    t.serie_id,
                    s.nome as serie_nome,
                    al.ano_letivo as ano_letivo,
                    COALESCE(COUNT(DISTINCT m.id), 0) as total_alunos
                FROM turmas t
                LEFT JOIN series s ON t.serie_id = s.id
                LEFT JOIN anosletivos al ON t.ano_letivo_id = al.id
                LEFT JOIN Matriculas m ON m.turma_id = t.id AND m.status = 'Ativo'
                WHERE (t.nome LIKE %s OR s.nome LIKE %s OR t.turno LIKE %s)
            """
            
            params: List[Any] = [f"%{termo}%", f"%{termo}%", f"%{termo}%"]
            
            if ano_letivo_id is not None:
                query += " AND t.ano_letivo_id = %s"
                params.append(ano_letivo_id)
            
            # Aplicar filtro de perfil do usuário (professor vê apenas suas turmas)
            if filtro_perfil_sql:
                query += filtro_perfil_sql
                params.extend(filtro_perfil_params)
            
            query += """
                GROUP BY t.id, t.nome, t.turno, 
                         t.ano_letivo_id, t.serie_id, s.nome, al.ano_letivo
                ORDER BY s.nome, t.turno, t.nome
            """
            
            cursor.execute(query, tuple(params))
            turmas = cursor.fetchall()
            
            logger.info(f"Busca '{termo}' encontrou {len(turmas)} turmas")
            return turmas
            
    except Exception as e:
        logger.exception(f"Erro ao buscar turmas: {e}")
        raise
