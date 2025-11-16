import io
import os
import tempfile
import logging
from typing import Tuple

from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter, landscape

from config_logs import get_logger

logger = get_logger(__name__)


def create_pdf_buffer(pagesize=letter) -> Tuple[SimpleDocTemplate, io.BytesIO]:
    """Cria e retorna um par (doc, buffer) para gerar PDF em memória.

    Essa função tenta replicar a API usada pelo código legado. O `pagesize`
    pode ser um objeto de reportlab (e.g., `letter`) ou `landscape(letter)`.
    """
    buf = io.BytesIO()
    try:
        doc = SimpleDocTemplate(buf, pagesize=pagesize)
        return doc, buf
    except Exception as e:
        logger.exception(f"Falha ao criar buffer de PDF: {e}")
        raise


def salvar_e_abrir_pdf(buffer: io.BytesIO, filename: str = None) -> str:
    """Salva o buffer em disco e retorna o caminho do arquivo.

    Se `filename` não for informado, cria um arquivo temporário em
    `tempfile.gettempdir()` com sufixo `.pdf` e retorna o caminho.
    Não tenta abrir o PDF automaticamente (evita efeitos colaterais em CI);
    apenas grava o arquivo e loga a ação.
    """
    try:
        if filename:
            out_path = os.path.abspath(filename)
        else:
            fd, out_path = tempfile.mkstemp(suffix='.pdf', prefix='relatorio_')
            os.close(fd)

        # Garantir que buffer esteja posicionado no início
        try:
            buffer.seek(0)
        except Exception:
            pass

        with open(out_path, 'wb') as f:
            f.write(buffer.getvalue())

        logger.info(f"PDF salvo em: {out_path}")
        return out_path
    except Exception as e:
        logger.exception(f"Falha ao salvar PDF: {e}")
        raise
