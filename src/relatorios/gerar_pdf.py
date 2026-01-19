from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
import tempfile
import platform
import os
import io
import time
from src.core.config_logs import get_logger

logger = get_logger(__name__)
import shutil
import inspect
import json
from datetime import datetime
import os as _os
from typing import Optional
from src.core.config import ANO_LETIVO_ATUAL

# Local config path (same convention used em main.py)
LOCAL_CONFIG_PATH = _os.path.join(_os.path.dirname(__file__), 'local_config.json')


def _get_documents_root() -> str:
    try:
        root = _os.environ.get('DOCUMENTS_SECRETARIA_ROOT')
        if root:
            return _os.path.abspath(root)
    except Exception:
        pass
    try:
        import config as _app_config
        default = getattr(_app_config, 'DEFAULT_DOCUMENTS_SECRETARIA_ROOT', None)
        if default:
            return _os.path.abspath(default)
    except Exception:
        pass
    return _os.path.abspath(_os.getcwd())


def _read_local_config() -> dict:
    try:
        if _os.path.exists(LOCAL_CONFIG_PATH):
            with open(LOCAL_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _get_drive_folder_id() -> Optional[str]:
    v = _os.environ.get('DOCUMENTS_DRIVE_FOLDER_ID')
    if v:
        return v
    cfg = _read_local_config()
    if cfg and cfg.get('drive_folder_id'):
        return str(cfg.get('drive_folder_id'))
    try:
        import config as _appcfg
        default = getattr(_appcfg, 'DEFAULT_DRIVE_FOLDER_ID', None)
        if default:
            return default
    except Exception:
        pass
    return None


def _ensure_docs_dirs(ano: Optional[int] = None):
    root = _get_documents_root()
    if ano is None:
        ano = ANO_LETIVO_ATUAL
    pasta_ano = _os.path.join(root, f"Documentos Secretaria {int(ano)}")
    subfolders = [
        'Listas', 'Notas', 'Servicos', 'Faltas', 'Pendencias', 'Relatorios Gerais', 'Contatos', 'Outros'
    ]
    try:
        _os.makedirs(pasta_ano, exist_ok=True)
        for s in subfolders:
            _os.makedirs(_os.path.join(pasta_ano, s), exist_ok=True)
    except Exception:
        logger.exception("_ensure_docs_dirs: falha ao criar pastas")
    return pasta_ano


def _categoria_por_contexto(basename: str, caller: Optional[str] = None) -> str:
    d = (basename or '').lower()
    if caller:
        d = d + ' ' + caller.lower()
    if 'pend' in d or 'pendên' in d or 'pendenc' in d:
        return 'Pendencias'
    if 'assinatura' in d or 'nota' in d or 'boletim' in d:
        return 'Notas'
    if 'lista' in d or 'reuniao' in d or 'lista' in d:
        return 'Listas'
    if 'frequência' in d or 'frequencia' in d or 'falt' in d:
        return 'Faltas'
    if 'contato' in d or 'contatos' in d:
        return 'Contatos'
    if 'moviment' in d or 'servico' in d or 'servicos' in d:
        return 'Servicos'
    if 'geral' in d:
        return 'Relatorios Gerais'
    return 'Relatorios Gerais'


def _move_and_upload(saved_path: str) -> str:
    """Move arquivo salvo em temp para a pasta Documentos apropriada e tenta enviar ao Drive.
    Retorna o novo caminho (ou o original em caso de erro).
    """
    try:
        basename = _os.path.basename(saved_path)
        # tentar identificar o caller (módulo/função) para mapear categoria
        caller = None
        try:
            st = inspect.stack()
            for fr in st[2:6]:
                fn = fr.function or ''
                filename = fr.filename or ''
                if 'relatorio' in filename.lower() or 'pendenc' in filename.lower() or 'lista' in filename.lower():
                    caller = filename
                    break
        except Exception:
            caller = None

        ano = ANO_LETIVO_ATUAL
        pasta_ano = _ensure_docs_dirs(ano)
        categoria = _categoria_por_contexto(basename, caller)
        target_dir = _os.path.join(pasta_ano, categoria)
        _os.makedirs(target_dir, exist_ok=True)
        target_path = _os.path.join(target_dir, basename)

        # mover arquivo
        try:
            shutil.move(saved_path, target_path)
            logger.info("PDF movido para: %s", target_path)
        except Exception as e:
            logger.exception("Falha ao mover PDF para pasta destino: %s", e)
            return saved_path

        # tentar upload (silencioso se falhar)
        try:
            from scripts.auxiliares.drive_uploader import upload_file
            drive_folder_id = _get_drive_folder_id()
            fid, web = upload_file(target_path, parent_id=drive_folder_id)
            if fid:
                logger.info("Arquivo enviado ao Drive (após mover): id=%s path=%s", fid, target_path)
            else:
                logger.warning("upload falhou para arquivo movido: %s", target_path)
        except Exception:
            logger.exception("Erro durante upload do arquivo movido para o Drive")

        return target_path
    except Exception:
        logger.exception("_move_and_upload: erro inesperado ao mover/upload")
        return saved_path



# Tentativa de usar o util centralizado se disponível. Caso contrário, manter
# as implementações legadas abaixo como fallback.
_HAS_NEW_PDF_UTIL = False
try:
    from src.services.utils import pdf as _pdf_util  # type: ignore
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

        # mover para a pasta Documentos e tentar upload
        try:
            moved = _move_and_upload(out_path)
            out_path = moved or out_path
        except Exception:
            logger.exception("Erro ao mover/upload após salvar via services.utils.pdf")

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

    # mover para Documentos e tentar upload
    try:
        new_path = _move_and_upload(temp_pdf_path)
    except Exception:
        logger.exception("Erro ao mover/upload do pdf legado")
        new_path = temp_pdf_path

    try:
        if platform.system() == "Windows":
            os.startfile(new_path)
        elif platform.system() == "Darwin":  # macOS
            os.system(f"open '{new_path}'")
        else:  # Linux e outros sistemas baseados em Unix
            os.system(f"xdg-open '{new_path}'")
    except Exception as e:
        logger.exception(f"Erro ao tentar abrir o PDF: {e}")

    return new_path


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


def criar_pdf(buffer, elements, orientacao='retrato'):
    """
    Cria um PDF com os elementos fornecidos.
    
    Args:
        buffer: Buffer de bytes para o PDF
        elements: Lista de elementos do ReportLab
        orientacao: 'retrato' ou 'paisagem' (padrão: 'retrato')
    """
    pagesize = landscape(letter) if orientacao == 'paisagem' else letter
    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesize,
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


def gerar_pdf(dados: Optional[dict] = None, tipo: str = 'documento', **kwargs):
    """Compat wrapper exposto historicamente como `gerar_pdf`.

    - Permite que testes façam `patch('gerarPDF.gerar_pdf')` sem erro de Pylance.
    - Quando executado de verdade (não mockado), tenta gerar um PDF mínimo
      em memória e salvá-lo com `salvar_e_abrir_pdf`, retornando o caminho
      quando possível ou `True` como fallback.
    """
    try:
        # criar buffer e um conteúdo bem simples
        doc, buffer = create_pdf_buffer()
        elements = []
        try:
            from reportlab.platypus import Paragraph
            from reportlab.lib.styles import ParagraphStyle
            elements.append(Paragraph(f"Documento: {tipo}", ParagraphStyle(name='Title', fontSize=14)))
        except Exception:
            # se reportlab não disponível, apenas escrever o buffer vazio
            pass

        try:
            criar_pdf(buffer, elements)
        except Exception:
            # não fatal — alguns ambientes podem não aceitar build completo
            pass

        try:
            saved = salvar_e_abrir_pdf(buffer)
            return saved
        except Exception:
            return True

    except Exception:
        return True

