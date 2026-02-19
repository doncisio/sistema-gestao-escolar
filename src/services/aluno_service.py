"""
Serviço de lógica de negócio para operações relacionadas a alunos.

Este módulo centraliza todas as operações de negócio relacionadas a alunos:
- Verificação de matrículas
- Exclusão de alunos
- Validações e regras de negócio

Extraído do main.py como parte da refatoração do Sprint 2.
Atualizado no Sprint 18 com validação Pydantic.
Refatorado no Sprint 22 — removido acoplamento com tkinter.
"""

from typing import Tuple, List, Dict, Optional
from mysql.connector import Error as MySQLError
from db.connection import get_cursor
from src.core.config_logs import get_logger
from src.core.config import ANO_LETIVO_ATUAL
from src.utils.safe import converter_para_int_seguro
from pydantic import ValidationError

# Import condicional dos modelos Pydantic (para compatibilidade)
try:
    from src.models.aluno import AlunoCreate, AlunoUpdate, AlunoRead
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    logger = get_logger(__name__)
    logger.warning("Modelos Pydantic não disponíveis, validação desabilitada")

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Exceções de negócio (capturadas pela UI para exibir mensagens)
# ---------------------------------------------------------------------------

class AlunoServiceError(Exception):
    """Erro genérico do serviço de alunos."""
    pass


class AlunoIdInvalidoError(AlunoServiceError):
    """ID de aluno inválido."""
    pass


class MatriculaAtivaError(AlunoServiceError):
    """Aluno possui matrícula ativa e não pode ser excluído."""
    pass


class AnoLetivoNaoEncontradoError(AlunoServiceError):
    """Ano letivo não encontrado no sistema."""
    pass


def validar_dados_aluno(dados: Dict, is_update: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Valida dados de aluno usando Pydantic.
    
    Args:
        dados: Dicionário com dados do aluno
        is_update: Se True, usa validação de update (campos opcionais)
        
    Returns:
        tuple: (sucesso: bool, mensagem_erro: Optional[str])
    """
    if not PYDANTIC_AVAILABLE:
        logger.debug("Validação Pydantic pulada (não disponível)")
        return True, None
    
    try:
        if is_update:
            AlunoUpdate(**dados)
        else:
            AlunoCreate(**dados)
        return True, None
    except ValidationError as e:
        # Formata erros de validação de forma amigável
        erros = []
        for erro in e.errors():
            campo = ' -> '.join(str(loc) for loc in erro['loc'])
            mensagem = erro['msg']
            erros.append(f"{campo}: {mensagem}")
        
        mensagem_completa = "Erro de validação:\n" + "\n".join(erros)
        logger.warning(f"Validação falhou: {mensagem_completa}")
        return False, mensagem_completa
    except Exception as e:
        logger.exception(f"Erro inesperado na validação: {e}")
        return False, f"Erro inesperado na validação: {str(e)}"


def verificar_matricula_ativa(aluno_id: int) -> bool:
    """
    Verifica se o aluno possui matrícula ativa ou transferida na escola com ID 60 no ano letivo atual.
    
    Args:
        aluno_id: ID do aluno a ser verificado
        
    Returns:
        bool: True se o aluno possui matrícula ativa ou transferida, False caso contrário
    """
    try:
        aluno_id_int = int(str(aluno_id))
    except (ValueError, TypeError) as e:
        logger.error(f"ID de aluno inválido: {aluno_id} - {e}")
        raise AlunoIdInvalidoError(f"ID de aluno inválido: {aluno_id}")
    
    try:
        with get_cursor() as cursor:
            # Obtém o ID do ano letivo atual configurado no sistema
            cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = %s", (ANO_LETIVO_ATUAL,))
            resultado_ano = cursor.fetchone()

            if not resultado_ano:
                # Se não encontrar o ano letivo atual, tenta obter o ano letivo mais recente
                logger.debug("Ano letivo atual não encontrado, buscando o mais recente")
                cursor.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                resultado_ano = cursor.fetchone()

            if not resultado_ano:
                logger.warning("Nenhum ano letivo encontrado no sistema")
                raise AnoLetivoNaoEncontradoError("Não foi possível determinar o ano letivo atual.")
                return False

            ano_letivo_id = int(str(resultado_ano['id'] if isinstance(resultado_ano, dict) else resultado_ano[0]))
            logger.debug(f"Verificando matrícula para aluno {aluno_id_int} no ano letivo {ano_letivo_id}")

            # Verifica se o aluno possui matrícula ativa ou transferida na escola 60 no ano letivo atual
            cursor.execute("""
                SELECT m.id 
                FROM matriculas m
                JOIN turmas t ON m.turma_id = t.id
                WHERE m.aluno_id = %s 
                AND m.ano_letivo_id = %s 
                AND t.escola_id = 60
                AND m.status IN ('Ativo', 'Transferido')
            """, (aluno_id_int, ano_letivo_id))

            resultado = cursor.fetchone()
            tem_matricula = resultado is not None
            
            logger.debug(f"Aluno {aluno_id_int} {'possui' if tem_matricula else 'não possui'} matrícula ativa")
            return tem_matricula
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao verificar matrícula do aluno {aluno_id}: {e}")
        raise AlunoServiceError(f"Erro ao verificar matrícula: {str(e)}") from e
    except AlunoServiceError:
        raise
    except Exception as e:
        logger.exception(f"Erro inesperado ao verificar matrícula do aluno {aluno_id}: {e}")
        raise AlunoServiceError(f"Erro ao verificar matrícula: {str(e)}") from e


def verificar_historico_matriculas(aluno_id: int) -> Tuple[bool, List[Tuple[int, int]]]:
    """
    Verifica se o aluno já teve alguma matrícula em qualquer escola e em qualquer ano letivo.
    
    Args:
        aluno_id: ID do aluno a ser verificado
        
    Returns:
        tuple: (bool, list) onde:
            - bool: True se o aluno possui histórico de matrícula, False caso contrário
            - list: Lista de tuplas (ano_letivo, ano_letivo_id) com matrícula (vazio se não houver)
    """
    try:
        aluno_id_int = int(str(aluno_id))
    except (ValueError, TypeError) as e:
        logger.error(f"ID de aluno inválido em verificar_historico_matriculas: {aluno_id} - {e}")
        raise AlunoIdInvalidoError(f"ID de aluno inválido: {aluno_id}")
    
    try:
        with get_cursor() as cursor:
            # Verifica se o aluno possui matrícula em qualquer ano letivo
            logger.debug(f"Buscando histórico de matrículas para aluno {aluno_id_int}")
            cursor.execute("""
                SELECT DISTINCT al.ano_letivo, al.id, m.status
                FROM matriculas m
                JOIN turmas t ON m.turma_id = t.id
                JOIN anosletivos al ON m.ano_letivo_id = al.id
                WHERE m.aluno_id = %s 
                AND m.status IN ('Ativo', 'Transferido')
                ORDER BY al.ano_letivo DESC
            """, (aluno_id_int,))

            resultados = cursor.fetchall()

            # Se não houver resultados, verificar diretamente se há o ano letivo 2024 (ID=1)
            if not resultados:
                logger.debug(f"Nenhuma matrícula ativa encontrada para aluno {aluno_id_int}, verificando ano letivo padrão")
                cursor.execute("SELECT ano_letivo, id FROM anosletivos WHERE id = 1")
                ano_2024 = cursor.fetchone()
                if ano_2024:
                    # Verificar se o aluno tem qualquer matrícula para este ano
                    cursor.execute("""
                        SELECT COUNT(*) FROM matriculas 
                        WHERE aluno_id = %s AND ano_letivo_id = 1
                    """, (aluno_id_int,))
                    resultado_count = cursor.fetchone()
                    count_val = resultado_count['COUNT(*)'] if isinstance(resultado_count, dict) else resultado_count[0]
                    tem_matricula = bool(count_val and int(str(count_val)) > 0)

                    if tem_matricula:
                        ano_val = ano_2024['ano_letivo'] if isinstance(ano_2024, dict) else ano_2024[0]
                        id_val = ano_2024['id'] if isinstance(ano_2024, dict) else ano_2024[1]
                        resultados = [(ano_val, id_val, 'Ativo')]
                        logger.debug(f"Encontrada matrícula no ano letivo padrão para aluno {aluno_id_int}")

            # Se encontrou resultados, retorna True e a lista de anos letivos
            if resultados:
                anos_letivos = []
                for row in resultados:
                    if isinstance(row, dict):
                        anos_letivos.append((row['ano_letivo'], row['id']))
                    else:
                        anos_letivos.append((row[0], row[1]))
                logger.info(f"Aluno {aluno_id_int} possui {len(anos_letivos)} matrícula(s) no histórico")
                return True, anos_letivos
            else:
                # Se ainda não encontrou, busca todos os anos letivos disponíveis
                logger.debug("Nenhuma matrícula encontrada, retornando todos os anos letivos disponíveis")
                cursor.execute("SELECT ano_letivo, id FROM anosletivos ORDER BY ano_letivo DESC")
                todos_anos = cursor.fetchall()

                if todos_anos:
                    anos_list = []
                    for row in todos_anos:
                        if isinstance(row, dict):
                            anos_list.append((row['ano_letivo'], row['id']))
                        else:
                            anos_list.append((row[0], row[1]))
                    return True, anos_list
                return False, []
                
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao verificar histórico de matrículas do aluno {aluno_id}: {e}")
        raise AlunoServiceError(f"Erro ao verificar histórico de matrículas: {str(e)}") from e
    except AlunoServiceError:
        raise
    except Exception as e:
        logger.exception(f"Erro inesperado ao verificar histórico de matrículas do aluno {aluno_id}: {e}")
        raise AlunoServiceError(f"Erro ao verificar histórico de matrículas: {str(e)}") from e


def excluir_aluno_com_confirmacao(aluno_id: int, nome_aluno: str, callback_sucesso=None, confirmado: bool = False) -> bool:
    """
    Exclui um aluno após verificações de segurança.
    
    Verifica se o aluno possui matrícula ativa antes de permitir a exclusão.
    Se tiver matrícula ativa, levanta MatriculaAtivaError.
    
    Args:
        aluno_id: ID do aluno a ser excluído
        nome_aluno: Nome do aluno (para logging)
        callback_sucesso: Função opcional a ser chamada após exclusão bem-sucedida
        confirmado: Se True, pula confirmação (a UI já confirmou)
        
    Returns:
        bool: True se o aluno foi excluído
        
    Raises:
        AlunoIdInvalidoError: Se o ID for inválido
        MatriculaAtivaError: Se o aluno possui matrícula ativa
        AlunoServiceError: Em caso de erro de banco
    """
    try:
        aluno_id_int = int(str(aluno_id))
    except (ValueError, TypeError) as e:
        logger.error(f"ID de aluno inválido em excluir_aluno: {aluno_id} - {e}")
        raise AlunoIdInvalidoError(f"ID de aluno inválido: {aluno_id}")
    
    # Verificar se o aluno possui matrícula ativa
    if verificar_matricula_ativa(aluno_id_int):
        logger.warning(f"Tentativa de excluir aluno {aluno_id_int} com matrícula ativa")
        raise MatriculaAtivaError(
            f"O aluno {nome_aluno} possui matrícula ativa e não pode ser excluído.\n\n"
            "Para excluir este aluno, primeiro remova ou transfira a matrícula."
        )
    
    try:
        with get_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM alunos WHERE id = %s", (aluno_id_int,))
            logger.info(f"Aluno {aluno_id_int} ({nome_aluno}) excluído com sucesso")
            
            if callback_sucesso:
                try:
                    callback_sucesso()
                except Exception as e:
                    logger.exception(f"Erro ao executar callback após exclusão: {e}")
            
            return True
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao excluir aluno {aluno_id_int}: {e}")
        raise AlunoServiceError(f"Erro ao excluir aluno: {str(e)}") from e
    except AlunoServiceError:
        raise
    except Exception as e:
        logger.exception(f"Erro inesperado ao excluir aluno {aluno_id_int}: {e}")
        raise AlunoServiceError(f"Erro ao excluir aluno: {str(e)}") from e


def obter_aluno_por_id(aluno_id: int) -> Optional[Dict]:
    """
    Obtém os dados completos de um aluno pelo ID.
    
    Args:
        aluno_id: ID do aluno
        
    Returns:
        dict: Dicionário com os dados do aluno, ou None se não encontrado
    """
    try:
        aluno_id_int = int(str(aluno_id))
    except (ValueError, TypeError) as e:
        logger.error(f"ID de aluno inválido em obter_aluno_por_id: {aluno_id} - {e}")
        return None
    
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT id, nome, data_nascimento, cpf, endereco, escola_id, 
                       sexo, nis, sus, raca, local_nascimento, UF_nascimento, 
                       descricao_transtorno
                FROM alunos 
                WHERE id = %s
            """, (aluno_id_int,))
            
            resultado = cursor.fetchone()
            
            if resultado:
                logger.debug(f"Dados do aluno {aluno_id_int} obtidos com sucesso")
                return resultado if isinstance(resultado, dict) else {
                    'id': resultado[0],
                    'nome': resultado[1],
                    'data_nascimento': resultado[2],
                    'cpf': resultado[3],
                    'endereco': resultado[4],
                    'escola_id': resultado[5],
                    'sexo': resultado[6],
                    'nis': resultado[7],
                    'sus': resultado[8],
                    'raca': resultado[9],
                    'local_nascimento': resultado[10],
                    'UF_nascimento': resultado[11],
                    'descricao_transtorno': resultado[12]
                }
            else:
                logger.warning(f"Aluno {aluno_id_int} não encontrado")
                return None
                
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao obter dados do aluno {aluno_id}: {e}")
        return None
    except Exception as e:
        logger.exception(f"Erro inesperado ao obter dados do aluno {aluno_id}: {e}")
        return None


def buscar_alunos(termo_busca: str, escola_id: int = 60, aplicar_filtro_perfil: bool = True) -> List[Dict]:
    """
    Busca alunos por nome, CPF ou matrícula.
    
    Args:
        termo_busca: Termo para buscar (nome parcial, CPF, etc.)
        escola_id: ID da escola (padrão: 60)
        aplicar_filtro_perfil: Se True, filtra alunos baseado no perfil do usuário
        
    Returns:
        list: Lista de dicionários com dados dos alunos encontrados
    """
    if not termo_busca or not termo_busca.strip():
        logger.debug("Termo de busca vazio")
        return []
    
    try:
        # Obter filtro de turmas baseado no perfil (se aplicável)
        filtro_perfil_sql = ""
        filtro_perfil_params = []
        
        if aplicar_filtro_perfil:
            try:
                from src.services.perfil_filter_service import get_sql_filtro_turmas
                filtro_perfil_sql, filtro_perfil_params = get_sql_filtro_turmas("t")
            except ImportError:
                pass  # Módulo não disponível, ignora filtro
        
        termo_formatado = f"%{termo_busca.strip()}%"
        
        with get_cursor() as cursor:
            # Buscar ano letivo atual configurado
            from src.core.config import ANO_LETIVO_ATUAL
            cursor.execute("SELECT id, data_fim FROM anosletivos WHERE ano_letivo = %s LIMIT 1", (ANO_LETIVO_ATUAL,))
            resultado_ano = cursor.fetchone()
            
            ano_letivo_id = None
            if resultado_ano:
                ano_id = resultado_ano['id'] if isinstance(resultado_ano, dict) else resultado_ano[0]
                data_fim = resultado_ano['data_fim'] if isinstance(resultado_ano, dict) else resultado_ano[1]
                
                if data_fim is None:
                    ano_letivo_id = ano_id
                else:
                    cursor.execute("SELECT CURDATE() <= %s as ainda_ativo", (data_fim,))
                    ainda_ativo = cursor.fetchone()
                    if ainda_ativo and (ainda_ativo['ainda_ativo'] if isinstance(ainda_ativo, dict) else ainda_ativo[0]):
                        ano_letivo_id = ano_id
            
            # Query com ano letivo definido
            query = """
                SELECT DISTINCT a.id, a.nome, a.data_nascimento, 
                       COALESCE(m.status, 'Sem matrícula') as status,
                       COALESCE(s.nome, 'N/A') as serie
                FROM alunos a
                LEFT JOIN matriculas m ON a.id = m.aluno_id AND m.ano_letivo_id = %s
                LEFT JOIN turmas t ON m.turma_id = t.id
                LEFT JOIN series s ON t.serie_id = s.id
                WHERE a.escola_id = %s
                AND (a.nome LIKE %s OR a.cpf LIKE %s)
            """
            
            params = [ano_letivo_id, escola_id, termo_formatado, termo_formatado]
            
            # Aplicar filtro de perfil do usuário (professor vê apenas seus alunos)
            if filtro_perfil_sql:
                query += filtro_perfil_sql
                params.extend(filtro_perfil_params)
            
            query += " ORDER BY a.nome LIMIT 50"
            
            cursor.execute(query, tuple(params))
            
            resultados = cursor.fetchall()
            
            logger.debug(f"Busca por '{termo_busca}' retornou {len(resultados)} resultados")
            
            if isinstance(resultados, list) and len(resultados) > 0:
                if isinstance(resultados[0], dict):
                    return resultados
                else:
                    # Converter tuplas em dicionários
                    return [
                        {
                            'id': r[0],
                            'nome': r[1],
                            'data_nascimento': r[2],
                            'status': r[3],
                            'serie': r[4]
                        }
                        for r in resultados
                    ]
            
            return []
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao buscar alunos: {e}")
        return []
    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar alunos: {e}")
        return []


def listar_alunos_ativos(escola_id: int = 60, ano_letivo_id: Optional[int] = None, aplicar_filtro_perfil: bool = True) -> List[Dict]:
    """
    Lista todos os alunos com matrícula ativa.
    
    Args:
        escola_id: ID da escola (padrão: 60)
        ano_letivo_id: ID do ano letivo (se None, usa ano atual)
        aplicar_filtro_perfil: Se True, filtra alunos baseado no perfil do usuário
        
    Returns:
        list: Lista de dicionários com dados dos alunos ativos
    """
    try:
        # Obter filtro de turmas baseado no perfil (se aplicável)
        filtro_perfil_sql = ""
        filtro_perfil_params = []
        
        if aplicar_filtro_perfil:
            try:
                from src.services.perfil_filter_service import get_sql_filtro_turmas
                filtro_perfil_sql, filtro_perfil_params = get_sql_filtro_turmas("t")
            except ImportError:
                pass  # Módulo não disponível, ignora filtro
        
        with get_cursor() as cursor:
            # Obter ano letivo atual se não especificado
            if ano_letivo_id is None:
                from src.core.config import ANO_LETIVO_ATUAL
                
                # Tentar o ano configurado e verificar se ainda está ativo
                cursor.execute("SELECT id, data_fim FROM anosletivos WHERE ano_letivo = %s LIMIT 1", (ANO_LETIVO_ATUAL,))
                resultado_ano = cursor.fetchone()
                
                if resultado_ano:
                    ano_id = resultado_ano['id'] if isinstance(resultado_ano, dict) else resultado_ano[0]
                    data_fim = resultado_ano['data_fim'] if isinstance(resultado_ano, dict) else resultado_ano[1]
                    
                    # Se não tem data_fim OU ainda não passou, usa este ano
                    if data_fim is None:
                        ano_letivo_id = ano_id
                    else:
                        cursor.execute("SELECT CURDATE() <= %s as ainda_ativo", (data_fim,))
                        ainda_ativo = cursor.fetchone()
                        if ainda_ativo and (ainda_ativo['ainda_ativo'] if isinstance(ainda_ativo, dict) else ainda_ativo[0]):
                            ano_letivo_id = ano_id
                
                # Fallback: busca ano ativo por data
                if ano_letivo_id is None:
                    cursor.execute("""
                        SELECT id FROM anosletivos 
                        WHERE CURDATE() BETWEEN data_inicio AND data_fim
                        ORDER BY ano_letivo DESC 
                        LIMIT 1
                    """)
                    resultado_ano = cursor.fetchone()
                    
                    if resultado_ano:
                        ano_letivo_id = resultado_ano['id'] if isinstance(resultado_ano, dict) else resultado_ano[0]
                
                if ano_letivo_id is None:
                    logger.warning("Ano letivo atual não encontrado")
                    return []
            
            query = """
                SELECT DISTINCT a.id, a.nome, a.data_nascimento, 
                       m.status, s.nome as serie, t.nome as turma
                FROM alunos a
                JOIN matriculas m ON a.id = m.aluno_id
                JOIN turmas t ON m.turma_id = t.id
                JOIN series s ON t.serie_id = s.id
                WHERE a.escola_id = %s
                AND m.ano_letivo_id = %s
                AND m.status = 'Ativo'
            """
            
            params = [escola_id, ano_letivo_id]
            
            # Aplicar filtro de perfil do usuário (professor vê apenas seus alunos)
            if filtro_perfil_sql:
                query += filtro_perfil_sql
                params.extend(filtro_perfil_params)
            
            query += " ORDER BY a.nome"
            
            cursor.execute(query, tuple(params))
            
            resultados = cursor.fetchall()
            
            logger.debug(f"Listados {len(resultados)} alunos ativos")
            
            if isinstance(resultados, list) and len(resultados) > 0:
                if isinstance(resultados[0], dict):
                    return resultados
                else:
                    return [
                        {
                            'id': r[0],
                            'nome': r[1],
                            'data_nascimento': r[2],
                            'status': r[3],
                            'serie': r[4],
                            'turma': r[5]
                        }
                        for r in resultados
                    ]
            
            return []
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao listar alunos ativos: {e}")
        return []
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar alunos ativos: {e}")
        return []


def obter_detalhes_matricula_aluno(aluno_id: int, ano_letivo_id: int) -> Optional[Dict]:
    """
    Retorna detalhes de matrícula, série, turma e responsáveis do aluno para
    exibição no painel de detalhes.

    Args:
        aluno_id: ID do aluno
        ano_letivo_id: ID do ano letivo

    Returns:
        Dict com chaves: status, data_matricula, serie_nome, turma_nome,
        turma_id, data_transferencia, nome_mae, nome_pai.
        None se não encontrar dados.
    """
    try:
        aluno_id_int = converter_para_int_seguro(aluno_id)
        if aluno_id_int is None:
            return None

        with get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    m.status, 
                    m.data_matricula,
                    s.nome as serie_nome,
                    t.nome as turma_nome,
                    t.id as turma_id,
                    (SELECT hm.data_mudanca 
                     FROM historico_matricula hm 
                     WHERE hm.matricula_id = m.id 
                     AND hm.status_novo IN ('Transferido', 'Transferida')
                     ORDER BY hm.data_mudanca DESC 
                     LIMIT 1) as data_transferencia,
                    GROUP_CONCAT(DISTINCT CASE WHEN r.grau_parentesco = 'Mãe' THEN r.nome END) as nome_mae,
                    GROUP_CONCAT(DISTINCT CASE WHEN r.grau_parentesco = 'Pai' THEN r.nome END) as nome_pai
                FROM alunos a
                LEFT JOIN matriculas m ON a.id = m.aluno_id AND m.ano_letivo_id = %s AND m.status IN ('Ativo', 'Transferido')
                LEFT JOIN turmas t ON m.turma_id = t.id AND t.escola_id = 60
                LEFT JOIN series s ON t.serie_id = s.id
                LEFT JOIN responsaveisalunos ra ON a.id = ra.aluno_id
                LEFT JOIN responsaveis r ON ra.responsavel_id = r.id AND r.grau_parentesco IN ('Mãe', 'Pai')
                WHERE a.id = %s
                GROUP BY m.id, m.status, m.data_matricula, s.nome, t.nome, t.id
                ORDER BY m.data_matricula DESC
                LIMIT 1
            """, (ano_letivo_id, aluno_id_int))

            resultado = cursor.fetchone()
            if resultado is None:
                return None

            # Normaliza para dict independente de formato retornado
            if isinstance(resultado, dict):
                return resultado

            keys = [
                'status', 'data_matricula', 'serie_nome', 'turma_nome',
                'turma_id', 'data_transferencia', 'nome_mae', 'nome_pai',
            ]
            return dict(zip(keys, resultado))

    except Exception as e:
        logger.exception(f"Erro ao obter detalhes de matrícula do aluno {aluno_id}: {e}")
        return None
