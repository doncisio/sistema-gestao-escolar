"""
Módulo de serviço para gerenciamento de declarações.
Extrai lógica de negócio de declarações do main.py.
"""

from typing import Optional, Dict, Tuple
from mysql.connector import Error as MySQLError
import logging
from db.connection import get_cursor

logger = logging.getLogger(__name__)


def identificar_tipo_pessoa(pessoa_id: int) -> Tuple[bool, Optional[str]]:
    """
    Identifica se uma pessoa é aluno ou funcionário.
    
    Args:
        pessoa_id: ID da pessoa
        
    Returns:
        tuple: (sucesso: bool, tipo: 'Aluno'|'Funcionário'|None)
    """
    try:
        with get_cursor() as cursor:
            # Verificar se é aluno
            cursor.execute("SELECT id FROM alunos WHERE id = %s", (pessoa_id,))
            if cursor.fetchone():
                logger.debug(f"Pessoa {pessoa_id} identificada como Aluno")
                return True, 'Aluno'
            
            # Verificar se é funcionário
            cursor.execute("SELECT id FROM funcionarios WHERE id = %s", (pessoa_id,))
            if cursor.fetchone():
                logger.debug(f"Pessoa {pessoa_id} identificada como Funcionário")
                return True, 'Funcionário'
            
            logger.warning(f"Pessoa {pessoa_id} não encontrada")
            return False, None
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao identificar tipo de pessoa {pessoa_id}")
        return False, None
    except Exception as e:
        logger.exception(f"Erro inesperado ao identificar tipo de pessoa {pessoa_id}")
        return False, None


def obter_dados_aluno_para_declaracao(aluno_id: int) -> Optional[Dict]:
    """
    Obtém dados completos do aluno para geração de declaração.
    
    Args:
        aluno_id: ID do aluno
        
    Returns:
        dict: Dados do aluno ou None
    """
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    a.id, a.nome, a.data_nascimento, a.cpf,
                    a.nome_mae, a.nome_pai, a.endereco, a.cidade, a.estado,
                    m.turma_id, t.nome as turma_nome, t.serie_id,
                    s.nome as serie_nome, al.ano as ano_letivo
                FROM alunos a
                LEFT JOIN matriculas m ON a.id = m.aluno_id AND m.status = 'Ativo'
                LEFT JOIN turmas t ON m.turma_id = t.id
                LEFT JOIN series s ON t.serie_id = s.id
                LEFT JOIN anos_letivos al ON m.ano_letivo_id = al.id
                WHERE a.id = %s
            """, (aluno_id,))
            
            resultado = cursor.fetchone()
            
            if not resultado:
                logger.warning(f"Aluno {aluno_id} não encontrado")
                return None
            
            # Converter para dict se necessário
            if isinstance(resultado, dict):
                return resultado
            else:
                colunas = [desc[0] for desc in cursor.description]
                return dict(zip(colunas, resultado))
                
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao obter dados do aluno {aluno_id}")
        return None
    except Exception as e:
        logger.exception(f"Erro inesperado ao obter dados do aluno {aluno_id}")
        return None


def obter_dados_funcionario_para_declaracao(funcionario_id: int) -> Optional[Dict]:
    """
    Obtém dados completos do funcionário para geração de declaração.
    
    Args:
        funcionario_id: ID do funcionário
        
    Returns:
        dict: Dados do funcionário ou None
    """
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, nome, cpf, cargo, data_admissao,
                    email, telefone, endereco, cidade, estado
                FROM funcionarios
                WHERE id = %s
            """, (funcionario_id,))
            
            resultado = cursor.fetchone()
            
            if not resultado:
                logger.warning(f"Funcionário {funcionario_id} não encontrado")
                return None
            
            # Converter para dict se necessário
            if isinstance(resultado, dict):
                return resultado
            else:
                colunas = [desc[0] for desc in cursor.description]
                return dict(zip(colunas, resultado))
                
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao obter dados do funcionário {funcionario_id}")
        return None
    except Exception as e:
        logger.exception(f"Erro inesperado ao obter dados do funcionário {funcionario_id}")
        return None


def validar_dados_declaracao(tipo_pessoa: str, dados: Dict, tipo_declaracao: str) -> Tuple[bool, str]:
    """
    Valida se os dados são suficientes para gerar a declaração.
    
    Args:
        tipo_pessoa: 'Aluno' ou 'Funcionário'
        dados: Dicionário com dados da pessoa
        tipo_declaracao: Tipo de declaração solicitada
        
    Returns:
        tuple: (válido: bool, mensagem_erro: str)
    """
    if not dados:
        return False, "Dados não encontrados"
    
    # Validações comuns
    if not dados.get('nome'):
        return False, "Nome não encontrado"
    
    if tipo_pessoa == 'Aluno':
        # Validações específicas para aluno
        if tipo_declaracao in ['Transferência', 'Bolsa Família']:
            if not dados.get('turma_nome'):
                return False, "Aluno não possui matrícula ativa"
            if not dados.get('serie_nome'):
                return False, "Série não encontrada"
            if not dados.get('ano_letivo'):
                return False, "Ano letivo não encontrado"
    
    elif tipo_pessoa == 'Funcionário':
        # Validações específicas para funcionário
        if not dados.get('cargo'):
            return False, "Cargo não encontrado"
        if not dados.get('data_admissao'):
            return False, "Data de admissão não encontrada"
    
    return True, ""


def registrar_geracao_declaracao(pessoa_id: int, tipo_pessoa: str, tipo_declaracao: str, 
                                 motivo_outros: Optional[str] = None) -> bool:
    """
    Registra a geração de uma declaração no banco para auditoria.
    
    Args:
        pessoa_id: ID da pessoa
        tipo_pessoa: 'Aluno' ou 'Funcionário'
        tipo_declaracao: Tipo de declaração
        motivo_outros: Motivo especificado se tipo_declaracao == 'Outros'
        
    Returns:
        bool: True se registrado com sucesso
    """
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO log_declaracoes (
                    pessoa_id, tipo_pessoa, tipo_declaracao, 
                    motivo_outros, data_geracao
                )
                VALUES (%s, %s, %s, %s, NOW())
            """, (pessoa_id, tipo_pessoa, tipo_declaracao, motivo_outros))
            
            logger.info(f"Geração de declaração registrada: {tipo_pessoa} {pessoa_id}, tipo: {tipo_declaracao}")
            return True
            
    except MySQLError as e:
        # Log mas não falha - registro é opcional
        logger.warning(f"Não foi possível registrar geração de declaração: {e}")
        return False
    except Exception as e:
        logger.warning(f"Erro ao registrar geração de declaração: {e}")
        return False
