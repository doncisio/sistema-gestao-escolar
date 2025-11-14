from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
import tempfile
import platform
import os
import io
import time
from config_logs import get_logger

logger = get_logger(__name__)

def salvar_e_abrir_pdf(buffer):
    """
    Salva o PDF gerado em um arquivo temporário e abre no programa padrão do sistema.

    Args:
        buffer (io.BytesIO): Buffer contendo o conteúdo do PDF gerado.
        nome_arquivo (str): Nome do arquivo PDF (opcional, apenas para fins de identificação).
    """
    # Salvar o buffer em um arquivo temporário e medir o tempo de escrita
    start_write = time.time()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(buffer.getvalue())
        temp_pdf_path = temp_pdf.name
    elapsed_write_ms = int((time.time() - start_write) * 1000)
    logger.info(f"event=pdf_save name=salvar_e_abrir_pdf stage=write duration_ms={elapsed_write_ms}")

    # Abrir o arquivo PDF com o programa padrão do sistema
    try:
        if platform.system() == "Windows":
            os.startfile(temp_pdf_path)
        elif platform.system() == "Darwin":  # macOS
            os.system(f"open '{temp_pdf_path}'")
        else:  # Linux e outros sistemas baseados em Unix
            os.system(f"xdg-open '{temp_pdf_path}'")
    except Exception as e:
        logger.exception(f"Erro ao tentar abrir o PDF: {e}")

def salvar(buffer, nome_aluno):
    """
    Salva o conteúdo do buffer em um arquivo PDF na pasta '9 Ano' com o nome baseado no nome do aluno.

    Args:
        buffer (io.BytesIO): Buffer contendo o conteúdo do PDF gerado.
        nome_aluno (str): Nome do aluno usado para nomear o arquivo PDF.
    """
    # Sanitizar o nome do aluno para evitar caracteres inválidos em nomes de arquivos
    nome_aluno = "".join(c for c in nome_aluno if c.isalnum() or c in (" ", "_")).rstrip()
    nome_arquivo = f"{nome_aluno}.pdf"
    
    # Criar a pasta '9 Ano' se não existir
    pasta_destino = "9 Ano"
    os.makedirs(pasta_destino, exist_ok=True)

    # Caminho completo do arquivo
    caminho_arquivo = os.path.join(pasta_destino, nome_arquivo)

    try:
        # Salvar o buffer em um arquivo PDF e medir tempo de escrita
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
        bottomMargin=18
    )
    doc.build(elements)

def create_pdf_buffer():
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
        bottomMargin=bottom_margin
    )
    return doc, buffer

def create_pdf_buffer_letter():
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
        bottomMargin=bottom_margin
    )
    return doc, buffer

