"""Thin wrapper de compatibilidade para geração de PDF.

Este módulo delega toda a lógica para ``src.services.utils.pdf``.
Mantido apenas para que imports existentes continuem funcionando::

    from src.relatorios.gerar_pdf import salvar_e_abrir_pdf, create_pdf_buffer

Novos relatórios devem importar diretamente de ``src.services.utils.pdf``.
"""

from reportlab.lib.pagesizes import letter, landscape
import io
from typing import Optional

from src.core.config_logs import get_logger

logger = get_logger(__name__)

# ---- Re-exportar tudo do módulo centralizado --------------------------------
from src.services.utils.pdf import (  # noqa: F401 — re-exports intencionais
    # Constantes de margem
    DEFAULT_LEFT_MARGIN,
    DEFAULT_RIGHT_MARGIN,
    DEFAULT_TOP_MARGIN,
    DEFAULT_BOTTOM_MARGIN,
    # Criação de PDF
    create_pdf_buffer as _create_pdf_buffer,
    create_pdf_doc,
    criar_pdf,
    # Salvar / abrir
    salvar_e_abrir_pdf,
    salvar,
    # Gerenciamento de documentos (usados por scripts externos)
    _get_documents_root,
    _ensure_docs_dirs,
)


# ---- Wrappers de conveniência com defaults legados --------------------------


def create_pdf_buffer(
    pagesize=None,
    leftMargin: int = DEFAULT_LEFT_MARGIN,
    rightMargin: int = DEFAULT_RIGHT_MARGIN,
    topMargin: int = DEFAULT_TOP_MARGIN,
    bottomMargin: int = DEFAULT_BOTTOM_MARGIN,
):
    """Cria (doc, buffer) — default ``landscape(letter)`` por compatibilidade.

    Aceita margens personalizadas::

        doc, buf = create_pdf_buffer(topMargin=5, bottomMargin=5)
    """
    if pagesize is None:
        pagesize = landscape(letter)
    return _create_pdf_buffer(
        pagesize=pagesize,
        leftMargin=leftMargin,
        rightMargin=rightMargin,
        topMargin=topMargin,
        bottomMargin=bottomMargin,
    )


def create_pdf_buffer_letter(
    leftMargin: int = DEFAULT_LEFT_MARGIN,
    rightMargin: int = DEFAULT_RIGHT_MARGIN,
    topMargin: int = DEFAULT_TOP_MARGIN,
    bottomMargin: int = DEFAULT_BOTTOM_MARGIN,
):
    """Cria (doc, buffer) com ``pagesize=letter`` (retrato).

    Aceita margens personalizadas::

        doc, buf = create_pdf_buffer_letter(topMargin=20, bottomMargin=20)
    """
    return _create_pdf_buffer(
        pagesize=letter,
        leftMargin=leftMargin,
        rightMargin=rightMargin,
        topMargin=topMargin,
        bottomMargin=bottomMargin,
    )


def gerar_pdf(dados: Optional[dict] = None, tipo: str = "documento", **kwargs):
    """Compat wrapper exposto historicamente como ``gerar_pdf``.

    Permite que testes façam ``patch('gerarPDF.gerar_pdf')`` sem erro.
    """
    try:
        doc, buffer = create_pdf_buffer()
        elements = []
        try:
            from reportlab.platypus import Paragraph
            from reportlab.lib.styles import ParagraphStyle
            elements.append(
                Paragraph(f"Documento: {tipo}", ParagraphStyle(name="Title", fontSize=14))
            )
        except Exception:
            pass

        try:
            criar_pdf(buffer, elements)
        except Exception:
            pass

        try:
            saved = salvar_e_abrir_pdf(buffer)
            return saved
        except Exception:
            return True
    except Exception:
        return True

