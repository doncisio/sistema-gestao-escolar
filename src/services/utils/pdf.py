"""Módulo centralizado para criação, salvamento e gerenciamento de PDFs.

Todas as funções de geração de PDF do projeto devem usar este módulo.
O módulo legado ``src.relatorios.gerar_pdf`` é um thin-wrapper que
redireciona para cá, mantendo compatibilidade com código existente.

Uso básico::

    from src.services.utils.pdf import create_pdf_buffer, salvar_e_abrir_pdf

    # Margens padrão
    doc, buffer = create_pdf_buffer(pagesize=landscape(letter))

    # Margens personalizadas por relatório
    doc, buffer = create_pdf_buffer(pagesize=letter, topMargin=5, bottomMargin=5)
"""

import io
import inspect
import json
import os
import platform
import shutil
import tempfile
import time
from typing import List, Optional, Tuple

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate

from src.core.config_logs import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Margens padrão (em pontos — 72 pontos = 1 inch)
# ---------------------------------------------------------------------------
DEFAULT_LEFT_MARGIN = 36
DEFAULT_RIGHT_MARGIN = 18
DEFAULT_TOP_MARGIN = 10
DEFAULT_BOTTOM_MARGIN = 18


# ========================== CRIAÇÃO DE PDF ==================================


def _make_doc(
    output,
    pagesize=letter,
    leftMargin: int = DEFAULT_LEFT_MARGIN,
    rightMargin: int = DEFAULT_RIGHT_MARGIN,
    topMargin: int = DEFAULT_TOP_MARGIN,
    bottomMargin: int = DEFAULT_BOTTOM_MARGIN,
) -> SimpleDocTemplate:
    """Cria um ``SimpleDocTemplate`` com margens configuráveis.

    ``output`` pode ser um ``io.BytesIO`` (para PDF em memória) ou uma
    string com caminho de arquivo (para gravar direto em disco).
    """
    return SimpleDocTemplate(
        output,
        pagesize=pagesize,
        leftMargin=leftMargin,
        rightMargin=rightMargin,
        topMargin=topMargin,
        bottomMargin=bottomMargin,
    )


def create_pdf_buffer(
    pagesize=letter,
    leftMargin: int = DEFAULT_LEFT_MARGIN,
    rightMargin: int = DEFAULT_RIGHT_MARGIN,
    topMargin: int = DEFAULT_TOP_MARGIN,
    bottomMargin: int = DEFAULT_BOTTOM_MARGIN,
) -> Tuple[SimpleDocTemplate, io.BytesIO]:
    """Cria e retorna ``(doc, buffer)`` para gerar PDF em memória.

    Aceita margens personalizadas — cada relatório pode fornecer as suas
    sem afetar os demais::

        doc, buf = create_pdf_buffer(topMargin=5, bottomMargin=5)
    """
    buf = io.BytesIO()
    try:
        doc = _make_doc(buf, pagesize, leftMargin, rightMargin, topMargin, bottomMargin)
        return doc, buf
    except Exception as e:
        logger.exception("Falha ao criar buffer de PDF: %s", e)
        raise


def create_pdf_doc(
    output,
    pagesize=letter,
    leftMargin: int = DEFAULT_LEFT_MARGIN,
    rightMargin: int = DEFAULT_RIGHT_MARGIN,
    topMargin: int = DEFAULT_TOP_MARGIN,
    bottomMargin: int = DEFAULT_BOTTOM_MARGIN,
) -> SimpleDocTemplate:
    """Cria um ``SimpleDocTemplate`` para gerar PDF direto em arquivo.

    Útil para relatórios que gravam direto em disco (sem buffer)::

        doc = create_pdf_doc("relatorio.pdf", pagesize=A4, topMargin=36)
        doc.build(elements)
    """
    try:
        return _make_doc(output, pagesize, leftMargin, rightMargin, topMargin, bottomMargin)
    except Exception as e:
        logger.exception("Falha ao criar doc PDF: %s", e)
        raise


def criar_pdf(
    buffer,
    elements: list,
    orientacao: str = "retrato",
    leftMargin: int = DEFAULT_LEFT_MARGIN,
    rightMargin: int = DEFAULT_RIGHT_MARGIN,
    topMargin: int = DEFAULT_TOP_MARGIN,
    bottomMargin: int = DEFAULT_BOTTOM_MARGIN,
):
    """Constrói o PDF com *elements* e grava no *buffer*.

    Args:
        buffer: ``io.BytesIO`` destino.
        elements: lista de Flowables do ReportLab.
        orientacao: ``'retrato'`` ou ``'paisagem'``.
        leftMargin, rightMargin, topMargin, bottomMargin: margens em pontos.
    """
    pagesize = landscape(letter) if orientacao == "paisagem" else letter
    doc = _make_doc(buffer, pagesize, leftMargin, rightMargin, topMargin, bottomMargin)
    doc.build(elements)


# =================== GERENCIAMENTO DE DOCUMENTOS ===========================
# Funções privadas que organizam o PDF salvo em pastas e fazem upload ao Drive.


def _get_ano_letivo_atual() -> int:
    """Importa ANO_LETIVO_ATUAL de forma lazy para evitar import circular."""
    try:
        from src.core.config import ANO_LETIVO_ATUAL
        return ANO_LETIVO_ATUAL
    except Exception:
        from datetime import datetime
        return datetime.now().year


def _get_documents_root() -> str:
    """Retorna a raiz da pasta de documentos da secretaria."""
    try:
        root = os.environ.get("DOCUMENTS_SECRETARIA_ROOT")
        if root:
            return os.path.abspath(root)
    except Exception:
        pass
    try:
        import config as _app_config
        default = getattr(_app_config, "DEFAULT_DOCUMENTS_SECRETARIA_ROOT", None)
        if default:
            return os.path.abspath(default)
    except Exception:
        pass
    return os.path.abspath(os.getcwd())


# Local config path (mesma convenção de main.py)
_LOCAL_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "local_config.json")


def _read_local_config() -> dict:
    try:
        if os.path.exists(_LOCAL_CONFIG_PATH):
            with open(_LOCAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _get_drive_folder_id() -> Optional[str]:
    v = os.environ.get("DOCUMENTS_DRIVE_FOLDER_ID")
    if v:
        return v
    cfg = _read_local_config()
    if cfg and cfg.get("drive_folder_id"):
        return str(cfg["drive_folder_id"])
    try:
        import config as _appcfg
        default = getattr(_appcfg, "DEFAULT_DRIVE_FOLDER_ID", None)
        if default:
            return default
    except Exception:
        pass
    return None


def _ensure_docs_dirs(ano: Optional[int] = None) -> str:
    """Cria a árvore de pastas de documentos e retorna o caminho-raiz do ano."""
    root = _get_documents_root()
    if ano is None:
        ano = _get_ano_letivo_atual()
    pasta_ano = os.path.join(root, f"Documentos Secretaria {int(ano)}")
    subfolders = [
        "Listas", "Notas", "Servicos", "Faltas",
        "Pendencias", "Relatorios Gerais", "Contatos", "Outros",
    ]
    try:
        os.makedirs(pasta_ano, exist_ok=True)
        for s in subfolders:
            os.makedirs(os.path.join(pasta_ano, s), exist_ok=True)
    except Exception:
        logger.exception("_ensure_docs_dirs: falha ao criar pastas")
    return pasta_ano


def _categoria_por_contexto(basename: str, caller: Optional[str] = None) -> str:
    d = (basename or "").lower()
    if caller:
        d = d + " " + caller.lower()
    if "pend" in d or "pendên" in d or "pendenc" in d:
        return "Pendencias"
    if "assinatura" in d or "nota" in d or "boletim" in d:
        return "Notas"
    if "lista" in d or "reuniao" in d:
        return "Listas"
    if "frequência" in d or "frequencia" in d or "falt" in d:
        return "Faltas"
    if "contato" in d or "contatos" in d:
        return "Contatos"
    if "moviment" in d or "servico" in d or "servicos" in d:
        return "Servicos"
    if "geral" in d:
        return "Relatorios Gerais"
    return "Relatorios Gerais"


def _move_to_organized_folder(saved_path: str) -> str:
    """Move arquivo para a pasta Documentos organizada por categoria.

    Retorna o novo caminho (ou o original em caso de erro).
    """
    try:
        basename = os.path.basename(saved_path)
        caller = None
        try:
            st = inspect.stack()
            for fr in st[2:6]:
                filename = fr.filename or ""
                if any(k in filename.lower() for k in ("relatorio", "pendenc", "lista")):
                    caller = filename
                    break
        except Exception:
            caller = None

        ano = _get_ano_letivo_atual()
        pasta_ano = _ensure_docs_dirs(ano)
        categoria = _categoria_por_contexto(basename, caller)
        target_dir = os.path.join(pasta_ano, categoria)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, basename)

        try:
            shutil.move(saved_path, target_path)
            logger.info("PDF movido para: %s", target_path)
        except Exception as e:
            logger.exception("Falha ao mover PDF para pasta destino: %s", e)
            return saved_path

        return target_path
    except Exception:
        logger.exception("_move_to_organized_folder: erro inesperado")
        return saved_path


def _upload_to_drive(file_path: str) -> Optional[str]:
    """Faz upload do arquivo ao Google Drive (silencioso se falhar)."""
    try:
        from scripts.auxiliares.drive_uploader import upload_file
        drive_folder_id = _get_drive_folder_id()
        fid, _web = upload_file(file_path, parent_id=drive_folder_id)
        if fid:
            logger.info("Arquivo enviado ao Drive: id=%s path=%s", fid, file_path)
            return fid
        logger.warning("Upload falhou para: %s", file_path)
    except Exception:
        logger.exception("Erro durante upload ao Drive")
    return None


def _open_in_os(file_path: str):
    """Abre o arquivo no visualizador padrão do sistema operacional."""
    try:
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":
            os.system(f"open '{file_path}'")
        else:
            os.system(f"xdg-open '{file_path}'")
    except Exception:
        logger.exception("Erro ao tentar abrir o PDF: %s", file_path)


# ========================== SALVAR / ABRIR ==================================


def salvar_e_abrir_pdf(
    buffer: io.BytesIO,
    filename: Optional[str] = None,
    abrir: bool = True,
    mover: bool = True,
    upload: bool = True,
) -> str:
    """Salva o buffer em disco, move para pasta organizada, faz upload e abre.

    Cada comportamento pode ser desativado individualmente::

        # Apenas salvar, sem abrir nem upload
        salvar_e_abrir_pdf(buffer, abrir=False, upload=False)

    Args:
        buffer: ``io.BytesIO`` com o conteúdo do PDF.
        filename: caminho de destino (opcional; gera temporário se omitido).
        abrir: se ``True``, abre o PDF no visualizador padrão do SO.
        mover: se ``True``, move para a pasta Documentos organizada.
        upload: se ``True``, faz upload ao Google Drive.

    Returns:
        Caminho final do arquivo salvo.
    """
    start_write = time.time()
    try:
        if filename:
            out_path = os.path.abspath(filename)
        else:
            fd, out_path = tempfile.mkstemp(suffix=".pdf", prefix="relatorio_")
            os.close(fd)

        try:
            buffer.seek(0)
        except Exception:
            pass

        with open(out_path, "wb") as f:
            f.write(buffer.getvalue())

        elapsed_ms = int((time.time() - start_write) * 1000)
        logger.info("event=pdf_save stage=write path=%s duration_ms=%d", out_path, elapsed_ms)

    except Exception as e:
        logger.exception("Falha ao salvar PDF: %s", e)
        raise

    # Mover para pasta organizada
    if mover:
        try:
            moved = _move_to_organized_folder(out_path)
            out_path = moved or out_path
        except Exception:
            logger.exception("Erro ao mover PDF para pasta organizada")

    # Upload ao Drive
    if upload:
        _upload_to_drive(out_path)

    # Abrir no SO
    if abrir:
        _open_in_os(out_path)

    return out_path


def salvar(buffer: io.BytesIO, nome_aluno: str):
    """Salva PDF na pasta '9 Ano' com nome baseado no aluno.

    Função legada mantida por compatibilidade.
    """
    nome_aluno = "".join(c for c in nome_aluno if c.isalnum() or c in (" ", "_")).rstrip()
    nome_arquivo = f"{nome_aluno}.pdf"

    pasta_destino = "9 Ano"
    os.makedirs(pasta_destino, exist_ok=True)
    caminho_arquivo = os.path.join(pasta_destino, nome_arquivo)

    try:
        start_write = time.time()
        with open(caminho_arquivo, "wb") as pdf_file:
            pdf_file.write(buffer.getvalue())
        elapsed_ms = int((time.time() - start_write) * 1000)
        logger.info("event=pdf_save name=salvar file=%s duration_ms=%d", caminho_arquivo, elapsed_ms)
    except Exception as e:
        logger.exception("Erro ao salvar o arquivo: %s", e)
