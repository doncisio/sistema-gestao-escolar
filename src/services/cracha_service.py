"""
Serviço para geração de crachás individuais e em lote.
Encapsula a lógica de importação do módulo gerar_cracha.
"""

import os
import sys
from typing import List, Dict, Optional

from src.core.config_logs import get_logger

logger = get_logger(__name__)


def _importar_modulo_cracha():
    """Importa o módulo gerar_cracha dinamicamente.
    
    Returns:
        module: Módulo gerar_cracha carregado
        
    Raises:
        ImportError: Se não conseguir importar o módulo
    """
    scripts_dir = os.path.join(os.getcwd(), "scripts_nao_utilizados")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    
    try:
        import gerar_cracha  # type: ignore
        return gerar_cracha
    except ImportError as e:
        logger.exception("Módulo gerar_cracha não disponível")
        raise ImportError(f"Não foi possível importar o módulo de crachás: {e}") from e


def obter_alunos_para_selecao() -> List[Dict]:
    """Obtém lista de alunos ativos para seleção.
    
    Returns:
        List[Dict]: Lista de dicionários com dados dos alunos (id, nome, série, turma, turno)
    """
    modulo = _importar_modulo_cracha()
    return modulo.obter_alunos_para_selecao()


def obter_responsaveis_do_aluno(aluno_id: int) -> List[Dict]:
    """Obtém lista de responsáveis de um aluno específico.
    
    Args:
        aluno_id: ID do aluno
        
    Returns:
        List[Dict]: Lista de dicionários com dados dos responsáveis (id, nome, telefone, grau_parentesco)
    """
    modulo = _importar_modulo_cracha()
    return modulo.obter_responsaveis_do_aluno(aluno_id)


def gerar_cracha_individual(aluno_id: int, responsavel_id: int) -> Optional[str]:
    """Gera um único crachá para um aluno e responsável específicos.
    
    Args:
        aluno_id: ID do aluno
        responsavel_id: ID do responsável
        
    Returns:
        str: Caminho do arquivo PDF gerado, ou None se houver erro
    """
    modulo = _importar_modulo_cracha()
    return modulo.gerar_cracha_individual(aluno_id, responsavel_id)


def gerar_crachas_todos_alunos() -> str:
    """Gera crachás para todos os alunos ativos.
    
    Returns:
        str: Caminho da pasta onde os crachás foram salvos
    """
    modulo = _importar_modulo_cracha()
    modulo.gerar_crachas_para_todos_os_alunos()
    
    from src.core.config import PROJECT_ROOT
    caminho = PROJECT_ROOT / 'assets' / 'crachas'
    return str(caminho)
