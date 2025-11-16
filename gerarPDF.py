from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
import tempfile
import platform
import os
import io
import time
from config_logs import get_logger

logger = get_logger(__name__)


# Tentativa de usar o util centralizado se disponível. Caso contrário, manter
# as implementações legadas abaixo como fallback.
_HAS_NEW_PDF_UTIL = False
try:
    from services.utils import pdf as _pdf_util  # type: ignore
    _HAS_NEW_PDF_UTIL = True
except Exception:
    _HAS_NEW_PDF_UTIL = False


def salvar_e_abrir_pdf(buffer):
    """Salva o buffer em disco (delegando para `services.utils.pdf` quando
    disponível) e tenta abrir o arquivo no visualizador padrão do sistema.

    Retorna o caminho do arquivo salvo.
    """
    if _HAS_NEW_PDF_UTIL:
        try:
            out_path = _pdf_util.salvar_e_abrir_pdf(buffer)
        except Exception:
            logger.exception("Falha ao salvar via services.utils.pdf, tentando fallback legada")
            return _salvar_e_abrir_pdf_legacy(buffer)

        # Comportamento legado: tentar abrir o arquivo no SO quando possível.
        try:
            if platform.system() == "Windows":
                os.startfile(out_path)
            elif platform.system() == "Darwin":
                os.system(f"open '{out_path}'")
            else:
                os.system(f"xdg-open '{out_path}'")
        except Exception:
            logger.exception("Erro ao tentar abrir o PDF após salvar pelo util centralizado")

        return out_path

    return _salvar_e_abrir_pdf_legacy(buffer)


def _salvar_e_abrir_pdf_legacy(buffer):
    start_write = time.time()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(buffer.getvalue())
        temp_pdf_path = temp_pdf.name
    elapsed_write_ms = int((time.time() - start_write) * 1000)
    logger.info(f"event=pdf_save name=salvar_e_abrir_pdf stage=write duration_ms={elapsed_write_ms}")

    try:
        if platform.system() == "Windows":
            os.startfile(temp_pdf_path)
        elif platform.system() == "Darwin":  # macOS
            os.system(f"open '{temp_pdf_path}'")
        else:  # Linux e outros sistemas baseados em Unix
            os.system(f"xdg-open '{temp_pdf_path}'")
    except Exception as e:
        logger.exception(f"Erro ao tentar abrir o PDF: {e}")

    return temp_pdf_path


def salvar(buffer, nome_aluno):
    """
    Salva o conteúdo do buffer em um arquivo PDF na pasta '9 Ano' com o nome baseado no nome do aluno.
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
        elapsed_write_ms = int((time.time() - start_write) * 1000)
        logger.info(f"event=pdf_save name=salvar stage=write file={caminho_arquivo} duration_ms={elapsed_write_ms}")
    except Exception as e:
        logger.exception(f"Erro ao salvar o arquivo: {e}")


def criar_pdf(buffer, elements):
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=18,
        topMargin=18,
        bottomMargin=18,
    )
    doc.build(elements)


def create_pdf_buffer():
    """Compat shim: retorna (doc, buffer) com orientação `landscape(letter)`.

    Quando disponível, delega para `services.utils.pdf.create_pdf_buffer`.
    """
    if _HAS_NEW_PDF_UTIL:
        try:
            return _pdf_util.create_pdf_buffer(pagesize=landscape(letter))
        except Exception:
            logger.exception("Falha ao criar buffer via services.utils.pdf, usando fallback legada")

    buffer = io.BytesIO()
    left_margin = 36
    right_margin = 18
    top_margin = 10
    bottom_margin = 18

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )
    return doc, buffer


def create_pdf_buffer_letter():
    """Compat shim: retorna (doc, buffer) com `pagesize=letter`.

    Quando disponível, delega para `services.utils.pdf.create_pdf_buffer`.
    """
    if _HAS_NEW_PDF_UTIL:
        try:
            return _pdf_util.create_pdf_buffer(pagesize=letter)
        except Exception:
            logger.exception("Falha ao criar buffer (letter) via services.utils.pdf, usando fallback legada")

    buffer = io.BytesIO()
    left_margin = 36
    right_margin = 18
    top_margin = 10
    bottom_margin = 18

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )
    return doc, buffer

