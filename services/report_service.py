import os
import sys
import importlib
from typing import Optional

from config_logs import get_logger
logger = get_logger(__name__)


def gerar_crachas_para_todos_os_alunos() -> str:
    """Executa a geração de crachás usando o módulo `gerar_cracha`.

    Retorna o caminho da pasta onde os crachás foram salvos.

    Levanta ImportError se o módulo não estiver disponível e propaga
    outras exceções para o chamador tratar (UI/worker).
    """
    # Adicionar o diretório scripts_nao_utilizados ao path
    scripts_dir = os.path.join(os.getcwd(), "scripts_nao_utilizados")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    try:
        import gerar_cracha  # type: ignore
    except ImportError:
        logger.exception("Módulo gerar_cracha não disponível")
        raise

    # tentar recarregar o módulo quando possível, mas ignore falhas de reload
    try:
        importlib.reload(gerar_cracha)
    except Exception:
        pass

    # Executa a função principal do gerador (pode demorar)
    gerar_cracha.gerar_crachas_para_todos_os_alunos()

    caminho = os.path.join(os.getcwd(), "Cracha_Anos_Iniciais")
    return caminho


def gerar_relatorio_avancado_com_assinatura(bimestre: str, nivel_ensino: str, ano_letivo: int,
                                            status_matricula, preencher_nulos: bool) -> bool:
    """Encapsula a chamada ao gerador de relatório de notas com assinatura.

    Retorna True se o relatório foi gerado com sucesso, False caso contrário.
    Propaga exceções para o chamador para tratamento de UI.
    """
    # O gerador principal está em NotaAta.py (ou módulo equivalente)
    try:
        from NotaAta import gerar_relatorio_notas_com_assinatura  # type: ignore
    except ImportError:
        logger.exception("Não foi possível importar NotaAta para gerar relatório avançado")
        raise

    resultado = gerar_relatorio_notas_com_assinatura(
        bimestre=bimestre,
        nivel_ensino=nivel_ensino,
        ano_letivo=ano_letivo,
        status_matricula=status_matricula,
        preencher_nulos=preencher_nulos
    )
    return bool(resultado)


def gerar_relatorio_pendencias(bimestre: str, nivel_ensino: str, ano_letivo: int, escola_id: int = 60) -> bool:
    """Encapsula a geração do relatório de pendências.

    Retorna True se gerou, False se não há pendências. Propaga exceções para o chamador.
    """
    try:
        from relatorio_pendencias import gerar_pdf_pendencias  # type: ignore
    except ImportError:
        logger.exception("Não foi possível importar relatorio_pendencias")
        raise

    resultado = gerar_pdf_pendencias(
        bimestre=bimestre,
        nivel_ensino=nivel_ensino,
        ano_letivo=ano_letivo,
        escola_id=escola_id
    )
    return bool(resultado)
