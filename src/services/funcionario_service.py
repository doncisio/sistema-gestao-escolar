"""
Módulo de serviço para gerenciamento de funcionários.
Extrai lógica de negócio de funcionários do main.py.
"""

from typing import Optional, Dict, List, Tuple
from mysql.connector import Error as MySQLError
import logging
from db.connection import get_cursor

logger = logging.getLogger(__name__)


def criar_funcionario(
    nome: str,
    cpf: str,
    cargo: str,
    data_admissao: str,
    escola_id: int = 60,
    **kwargs
) -> Tuple[bool, str, Optional[int]]:
    """
    Cria um novo funcionário no sistema.
    
    Args:
        nome: Nome completo do funcionário
        cpf: CPF do funcionário
        cargo: Cargo do funcionário
        data_admissao: Data de admissão (formato: YYYY-MM-DD)
        escola_id: ID da escola (padrão: 60)
        **kwargs: Campos opcionais (email, telefone, endereco, etc.)
        
    Returns:
        tuple: (sucesso: bool, mensagem: str, funcionario_id: int ou None)
    """
    try:
        # Validar campos obrigatórios
        if not nome or not cpf or not cargo:
            return False, "Nome, CPF e cargo são obrigatórios", None
        
        # Verificar se CPF já existe
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT id FROM funcionarios WHERE cpf = %s",
                (cpf,)
            )
            if cursor.fetchone():
                return False, f"CPF {cpf} já cadastrado", None
            
            # Preparar campos
            campos = ['nome', 'cpf', 'cargo', 'data_admissao', 'escola_id']
            valores = [nome, cpf, cargo, data_admissao, escola_id]
            
            # Adicionar campos opcionais
            campos_opcionais = ['email', 'telefone', 'endereco', 'cidade', 'estado', 'cep']
            for campo in campos_opcionais:
                if campo in kwargs and kwargs[campo]:
                    campos.append(campo)
                    valores.append(kwargs[campo])
            
            # Construir query
            placeholders = ', '.join(['%s'] * len(valores))
            campos_str = ', '.join(campos)
            
            cursor.execute(f"""
                INSERT INTO funcionarios ({campos_str})
                VALUES ({placeholders})
            """, tuple(valores))
            
            funcionario_id = cursor.lastrowid
            
            logger.info(f"Funcionário '{nome}' cadastrado com ID {funcionario_id}")
            return True, "Funcionário cadastrado com sucesso", funcionario_id
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao criar funcionário: {e}")
        return False, f"Erro ao cadastrar funcionário: {str(e)}", None
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar funcionário: {e}")
        return False, f"Erro inesperado: {str(e)}", None


def atualizar_funcionario(
    funcionario_id: int,
    **campos
) -> Tuple[bool, str]:
    """
    Atualiza dados de um funcionário.
    
    Args:
        funcionario_id: ID do funcionário
        **campos: Campos a atualizar (nome, cargo, email, etc.)
        
    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    try:
        if not campos:
            return False, "Nenhum campo para atualizar"
        
        with get_cursor() as cursor:
            # Verificar se funcionário existe
            cursor.execute(
                "SELECT id FROM funcionarios WHERE id = %s",
                (funcionario_id,)
            )
            if not cursor.fetchone():
                return False, "Funcionário não encontrado"
            
            # Construir query de atualização
            campos_validos = ['nome', 'cpf', 'cargo', 'email', 'telefone', 
                             'endereco', 'cidade', 'estado', 'cep', 'data_admissao']
            
            sets = []
            valores = []
            
            for campo, valor in campos.items():
                if campo in campos_validos:
                    sets.append(f"{campo} = %s")
                    valores.append(valor)
            
            if not sets:
                return False, "Nenhum campo válido para atualizar"
            
            valores.append(funcionario_id)
            
            cursor.execute(f"""
                UPDATE funcionarios 
                SET {', '.join(sets)}
                WHERE id = %s
            """, tuple(valores))
            
            logger.info(f"Funcionário {funcionario_id} atualizado")
            return True, "Funcionário atualizado com sucesso"
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao atualizar funcionário: {e}")
        return False, f"Erro ao atualizar funcionário: {str(e)}"
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar funcionário: {e}")
        return False, f"Erro inesperado: {str(e)}"


def excluir_funcionario(
    funcionario_id: int,
    verificar_vinculos: bool = True
) -> Tuple[bool, str]:
    """
    Exclui um funcionário do sistema.
    
    Args:
        funcionario_id: ID do funcionário
        verificar_vinculos: Se True, verifica vínculos antes de excluir
        
    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    try:
        with get_cursor() as cursor:
            # Verificar se funcionário existe
            cursor.execute(
                "SELECT nome FROM funcionarios WHERE id = %s",
                (funcionario_id,)
            )
            resultado = cursor.fetchone()
            
            if not resultado:
                return False, "Funcionário não encontrado"
            
            nome = resultado['nome'] if isinstance(resultado, dict) else resultado[0]
            
            # Verificar vínculos (se solicitado)
            if verificar_vinculos:
                # Verificar turmas
                cursor.execute(
                    "SELECT COUNT(*) as total FROM turmas WHERE professor_id = %s",
                    (funcionario_id,)
                )
                turmas = cursor.fetchone()
                total_turmas = turmas['total'] if isinstance(turmas, dict) else turmas[0]
                
                if total_turmas > 0:
                    return False, f"Funcionário possui {total_turmas} turma(s) vinculada(s)"
            
            # Excluir funcionário
            cursor.execute(
                "DELETE FROM funcionarios WHERE id = %s",
                (funcionario_id,)
            )
            
            logger.info(f"Funcionário {funcionario_id} ({nome}) excluído")
            return True, f"Funcionário '{nome}' excluído com sucesso"
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao excluir funcionário: {e}")
        return False, f"Erro ao excluir funcionário: {str(e)}"
    except Exception as e:
        logger.exception(f"Erro inesperado ao excluir funcionário: {e}")
        return False, f"Erro inesperado: {str(e)}"


def listar_funcionarios(
    escola_id: int = 60,
    cargo: Optional[str] = None,
    ativo: Optional[bool] = None
) -> List[Dict]:
    """
    Lista funcionários da escola.
    
    Args:
        escola_id: ID da escola (padrão: 60)
        cargo: Filtrar por cargo (opcional)
        ativo: Filtrar por status ativo (opcional)
        
    Returns:
        list: Lista de dicionários com dados dos funcionários
    """
    try:
        with get_cursor() as cursor:
            # Construir query com filtros
            query = "SELECT * FROM funcionarios WHERE escola_id = %s"
            params: List = [escola_id]
            
            if cargo:
                query += " AND cargo = %s"
                params.append(cargo)
            
            if ativo is not None:
                # Assumindo que existe campo 'ativo' na tabela
                query += " AND ativo = %s"
                params.append(1 if ativo else 0)
            
            query += " ORDER BY nome"
            
            cursor.execute(query, tuple(params))
            resultados = cursor.fetchall()
            
            if isinstance(resultados, list) and len(resultados) > 0:
                if isinstance(resultados[0], dict):
                    return resultados
                else:
                    # Converter tuplas em dicionários
                    colunas = [desc[0] for desc in cursor.description]
                    return [dict(zip(colunas, r)) for r in resultados]
            
            return []
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao listar funcionários: {e}")
        return []
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar funcionários: {e}")
        return []


def buscar_funcionario(
    termo_busca: str,
    escola_id: int = 60
) -> List[Dict]:
    """
    Busca funcionários por nome ou CPF.
    
    Args:
        termo_busca: Termo para buscar (nome parcial ou CPF)
        escola_id: ID da escola (padrão: 60)
        
    Returns:
        list: Lista de dicionários com dados dos funcionários encontrados
    """
    try:
        if not termo_busca or not termo_busca.strip():
            return []
        
        termo_formatado = f"%{termo_busca.strip()}%"
        
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM funcionarios
                WHERE escola_id = %s
                AND (nome LIKE %s OR cpf LIKE %s)
                ORDER BY nome
                LIMIT 50
            """, (escola_id, termo_formatado, termo_formatado))
            
            resultados = cursor.fetchall()
            
            if isinstance(resultados, list) and len(resultados) > 0:
                if isinstance(resultados[0], dict):
                    return resultados
                else:
                    colunas = [desc[0] for desc in cursor.description]
                    return [dict(zip(colunas, r)) for r in resultados]
            
            return []
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao buscar funcionário: {e}")
        return []
    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar funcionário: {e}")
        return []


def obter_funcionario_por_id(funcionario_id: int) -> Optional[Dict]:
    """
    Obtém dados completos de um funcionário.
    
    Args:
        funcionario_id: ID do funcionário
        
    Returns:
        dict: Dados do funcionário ou None
    """
    try:
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM funcionarios WHERE id = %s",
                (funcionario_id,)
            )
            
            resultado = cursor.fetchone()
            
            if resultado:
                if isinstance(resultado, dict):
                    return resultado
                else:
                    colunas = [desc[0] for desc in cursor.description]
                    return dict(zip(colunas, resultado))
            
            return None
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao obter funcionário: {e}")
        return None
    except Exception as e:
        logger.exception(f"Erro inesperado ao obter funcionário: {e}")
        return None


def obter_turmas_professor(funcionario_id: int, ano_letivo_id: Optional[int] = None) -> List[Dict]:
    """
    Obtém turmas de um professor/funcionário.
    
    Args:
        funcionario_id: ID do funcionário
        ano_letivo_id: ID do ano letivo (opcional, usa atual se None)
        
    Returns:
        list: Lista de dicionários com dados das turmas
    """
    try:
        with get_cursor() as cursor:
            query = """
                SELECT t.id, t.nome, s.nome as serie
                FROM turmas t
                JOIN series s ON t.serie_id = s.id
                WHERE t.professor_id = %s
            """
            params = [funcionario_id]
            
            if ano_letivo_id:
                query += " AND t.ano_letivo_id = %s"
                params.append(ano_letivo_id)
            else:
                # Buscar ano letivo configurado
                from src.core.config import ANO_LETIVO_ATUAL
                query += " AND t.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = %s LIMIT 1)"
                params.append(ANO_LETIVO_ATUAL)
            
            query += " ORDER BY s.ordem, t.nome"
            
            cursor.execute(query, tuple(params))
            resultados = cursor.fetchall()
            
            if isinstance(resultados, list) and len(resultados) > 0:
                if isinstance(resultados[0], dict):
                    return resultados
                else:
                    return [
                        {
                            'id': r[0],
                            'nome': r[1],
                            'serie': r[2]
                        }
                        for r in resultados
                    ]
            
            return []
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao obter turmas do professor: {e}")
        return []
    except Exception as e:
        logger.exception(f"Erro inesperado ao obter turmas do professor: {e}")
        return []
