"""
services/boletim_service.py

Serviço de negócio para operações relacionadas a boletins escolares.
Extrai e centraliza a lógica de geração de boletins e documentos de transferência.
"""

from typing import Optional, Dict, Tuple
import logging
from db.connection import get_cursor

logger = logging.getLogger(__name__)


def obter_ano_letivo_atual() -> Optional[int]:
    """
    Obtém o ID do ano letivo atual (ano corrente) do banco.
    Se não encontrar, retorna o ID do ano letivo mais recente.
    
    Returns:
        Optional[int]: ID do ano letivo ou None se não encontrar
    """
    try:
        with get_cursor() as cursor:
            # Tentar ano corrente
            cursor.execute("SELECT id FROM anosletivos WHERE YEAR(CURDATE()) = ano_letivo")
            resultado = cursor.fetchone()
            
            if resultado:
                if isinstance(resultado, dict):
                    return resultado.get('id')
                return resultado[0] if resultado else None
            
            # Fallback: ano letivo mais recente
            cursor.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
            resultado = cursor.fetchone()
            
            if resultado:
                if isinstance(resultado, dict):
                    return resultado.get('id')
                return resultado[0] if resultado else None
            
            return None
    
    except Exception as e:
        logger.exception(f"Erro ao obter ano letivo atual: {e}")
        return None


def verificar_status_matricula(aluno_id: int, ano_letivo_id: int, escola_id: int = 60) -> Optional[Dict]:
    """
    Verifica o status da matrícula de um aluno em um ano letivo específico.
    
    Args:
        aluno_id: ID do aluno
        ano_letivo_id: ID do ano letivo
        escola_id: ID da escola (padrão: 60)
        
    Returns:
        Optional[Dict]: Dicionário com status, nome_aluno, ano_letivo ou None se não encontrar
    """
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT m.status, a.nome, al.ano_letivo
                FROM matriculas m
                JOIN turmas t ON m.turma_id = t.id
                JOIN alunos a ON m.aluno_id = a.id
                JOIN anosletivos al ON m.ano_letivo_id = al.id
                WHERE m.aluno_id = %s 
                AND m.ano_letivo_id = %s 
                AND t.escola_id = %s
                AND m.status IN ('Ativo', 'Transferido')
                ORDER BY m.data_matricula DESC
                LIMIT 1
            """, (aluno_id, ano_letivo_id, escola_id))
            
            resultado = cursor.fetchone()
            
            if not resultado:
                return None
            
            # Suportar dict ou tuple
            if isinstance(resultado, dict):
                return {
                    'status': resultado.get('status'),
                    'nome_aluno': resultado.get('nome'),
                    'ano_letivo': resultado.get('ano_letivo')
                }
            else:
                return {
                    'status': resultado[0],
                    'nome_aluno': resultado[1],
                    'ano_letivo': resultado[2]
                }
    
    except Exception as e:
        logger.exception(f"Erro ao verificar status de matrícula: {e}")
        return None


def decidir_tipo_documento(aluno_id: int, ano_letivo_id: Optional[int] = None) -> Tuple[str, Dict]:
    """
    Decide qual tipo de documento gerar (Boletim ou Transferência) baseado no status da matrícula.
    
    Args:
        aluno_id: ID do aluno
        ano_letivo_id: ID do ano letivo (opcional, usa ano atual se None)
        
    Returns:
        Tuple[str, Dict]: ('Boletim'|'Transferência', dados_matricula)
                          ou ('Erro', {'mensagem': str}) em caso de falha
    """
    try:
        # Obter ano letivo se não foi fornecido
        if ano_letivo_id is None:
            ano_letivo_id = obter_ano_letivo_atual()
            if ano_letivo_id is None:
                return ('Erro', {'mensagem': 'Não foi possível determinar o ano letivo atual'})
        
        # Verificar status da matrícula
        dados = verificar_status_matricula(aluno_id, ano_letivo_id)
        
        if not dados:
            return ('Erro', {'mensagem': 'Não foi possível determinar o status da matrícula do aluno'})
        
        # Decidir tipo de documento
        if dados['status'] == 'Transferido':
            return ('Transferência', dados)
        else:
            return ('Boletim', dados)
    
    except Exception as e:
        logger.exception(f"Erro ao decidir tipo de documento: {e}")
        return ('Erro', {'mensagem': str(e)})


def gerar_boletim_ou_transferencia(aluno_id: int, ano_letivo_id: Optional[int] = None) -> Tuple[bool, str]:
    """
    Função unificada que decide e gera o documento apropriado (Boletim ou Transferência).
    
    Args:
        aluno_id: ID do aluno
        ano_letivo_id: ID do ano letivo (opcional)
        
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    try:
        # Decidir tipo de documento
        tipo, dados = decidir_tipo_documento(aluno_id, ano_letivo_id)
        
        if tipo == 'Erro':
            return (False, dados.get('mensagem', 'Erro desconhecido'))
        
        # Importar funções de geração (lazy import para evitar dependências circulares)
        if tipo == 'Transferência':
            from transferencia import gerar_documento_transferencia
            
            gerar_documento_transferencia(aluno_id, ano_letivo_id or obter_ano_letivo_atual())
            
            mensagem = f"Documento de transferência gerado para {dados['nome_aluno']} (Ano Letivo {dados['ano_letivo']})"
            logger.info(mensagem)
            return (True, mensagem)
        
        else:  # tipo == 'Boletim'
            # Importar boletim do main.py ou módulo específico
            try:
                from main import boletim
                resultado = boletim(aluno_id, ano_letivo_id or obter_ano_letivo_atual())
                
                if resultado:
                    mensagem = f"Boletim gerado para {dados['nome_aluno']} (Ano Letivo {dados['ano_letivo']})"
                    logger.info(mensagem)
                    return (True, mensagem)
                else:
                    return (False, "Nenhum dado gerado para o boletim")
            except ImportError:
                # Fallback: tentar importar de boletim.py
                try:
                    import boletim as boletim_module
                    resultado = boletim_module.boletim(aluno_id, ano_letivo_id or obter_ano_letivo_atual())
                    
                    if resultado:
                        mensagem = f"Boletim gerado para {dados['nome_aluno']}"
                        logger.info(mensagem)
                        return (True, mensagem)
                    else:
                        return (False, "Nenhum dado gerado para o boletim")
                except Exception as e:
                    logger.exception(f"Erro ao gerar boletim: {e}")
                    return (False, f"Erro ao gerar boletim: {str(e)}")
    
    except Exception as e:
        logger.exception(f"Erro ao gerar documento: {e}")
        return (False, f"Erro ao gerar documento: {str(e)}")


def validar_aluno_para_boletim(aluno_id: int, ano_letivo_id: Optional[int] = None) -> Tuple[bool, str]:
    """
    Valida se um aluno está apto para geração de boletim/transferência.
    
    Args:
        aluno_id: ID do aluno
        ano_letivo_id: ID do ano letivo (opcional)
        
    Returns:
        Tuple[bool, str]: (válido, mensagem_erro)
    """
    try:
        # Obter ano letivo se não foi fornecido
        if ano_letivo_id is None:
            ano_letivo_id = obter_ano_letivo_atual()
            if ano_letivo_id is None:
                return (False, 'Não foi possível determinar o ano letivo atual')
        
        # Verificar se aluno existe
        with get_cursor() as cursor:
            cursor.execute("SELECT id FROM alunos WHERE id = %s", (aluno_id,))
            if not cursor.fetchone():
                return (False, f'Aluno com ID {aluno_id} não encontrado')
        
        # Verificar se tem matrícula no ano letivo
        dados = verificar_status_matricula(aluno_id, ano_letivo_id)
        if not dados:
            return (False, 'Aluno não possui matrícula ativa ou transferida no ano letivo selecionado')
        
        return (True, '')
    
    except Exception as e:
        logger.exception(f"Erro ao validar aluno para boletim: {e}")
        return (False, f'Erro ao validar aluno: {str(e)}')
