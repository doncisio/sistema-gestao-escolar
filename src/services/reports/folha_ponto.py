"""Relatórios de folha de ponto e resumo de ponto."""

import os
import sys
import io
from typing import Optional, Any, cast

from src.core.config_logs import get_logger
from src.services.reports._utils import _ensure_legacy_module

logger = get_logger(__name__)


def gerar_resumo_ponto(*args, **kwargs) -> bool:
    """Encapsula a chamada ao gerador de resumo de ponto."""
    _mod = sys.modules.get('gerar_resumo_ponto')
    if _mod is not None:
        if hasattr(_mod, 'gerar_resumo_ponto'):
            cast(Any, _mod).gerar_resumo_ponto(*args, **kwargs)
            return True
        raise AttributeError("Módulo 'gerar_resumo_ponto' injetado não possui 'gerar_resumo_ponto'")

    try:
        return _impl_gerar_resumo_ponto(*args, **kwargs)
    except NotImplementedError:
        pass
    except Exception:
        pass

    try:
        _mod = _ensure_legacy_module('gerar_resumo_ponto', required=['gerar_resumo_ponto'], candidate_filename='gerar_resumo_ponto.py')
    except Exception:
        logger.exception("Módulo 'gerar_resumo_ponto' não disponível para gerar resumo de ponto")
        raise

    if not hasattr(_mod, 'gerar_resumo_ponto'):
        raise AttributeError("Módulo 'gerar_resumo_ponto' não possui 'gerar_resumo_ponto'")

    resultado = cast(Any, _mod).gerar_resumo_ponto(*args, **kwargs)
    try:
        return bool(resultado)
    except Exception:
        return True


def gerar_folhas_de_ponto(*args, **kwargs) -> bool:
    """Encapsula a chamada a ``preencher_folha_ponto.gerar_folhas_de_ponto``."""
    try:
        _mod = _ensure_legacy_module('preencher_folha_ponto', required=['gerar_folhas_de_ponto'], candidate_filename='preencher_folha_ponto.py')
    except Exception:
        logger.exception("Módulo 'preencher_folha_ponto' não disponível para gerar folhas de ponto")
        raise

    if not hasattr(_mod, 'gerar_folhas_de_ponto'):
        raise AttributeError("Módulo 'preencher_folha_ponto' não possui 'gerar_folhas_de_ponto'")

    resultado = _mod.gerar_folhas_de_ponto(*args, **kwargs)
    try:
        return bool(resultado)
    except Exception:
        return True


# ---------------------------------------------------------------------------
# Implementações migradas
# ---------------------------------------------------------------------------


def _impl_gerar_folhas_de_ponto(*args, **kwargs) -> bool:
    """Implementação migrada (in-process) para ``preencher_folha_ponto.gerar_folhas_de_ponto``."""
    import datetime

    if len(args) >= 2:
        mes = args[0]
        ano = args[1]
    else:
        mes = kwargs.get('mes', datetime.datetime.now().month)
        ano = kwargs.get('ano', datetime.datetime.now().year)

    profissionais = kwargs.get('profissionais')
    out_dir = kwargs.get('out_dir')

    if profissionais is None:
        raise NotImplementedError("_impl_gerar_folhas_de_ponto requer 'profissionais' injetados")

    try:
        from src.services.utils.pdf import create_pdf_buffer, salvar_e_abrir_pdf
    except Exception:
        try:
            from src.relatorios.gerar_pdf import create_pdf_buffer, salvar_e_abrir_pdf
        except Exception:
            logger.exception('Não foi possível importar helpers de PDF para gerar_folhas_de_ponto')
            raise

    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    doc, buffer = create_pdf_buffer()
    elements = []
    elements.append(Paragraph(f"FOLHAS DE PONTO - {mes}/{ano}", ParagraphStyle(name='Title', fontSize=16, alignment=1)))
    elements.append(Spacer(1, 0.2 * inch))

    table_data = [['Nº', 'Nome', 'Função']]
    for i, p in enumerate(profissionais, start=1):
        if isinstance(p, dict):
            nome = p.get('nome') or p.get('nome_profissional') or p.get('Nome') or ''
            func = p.get('funcao') or p.get('cargo') or ''
        else:
            nome = str(p)
            func = ''
        table_data.append([str(i), str(nome), str(func)])

    table = Table(table_data, colWidths=[0.5 * inch, 4 * inch, 2 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(table)

    doc.build(elements)
    try:
        salvar_e_abrir_pdf(buffer)
    except Exception:
        try:
            if out_dir:
                filename = os.path.join(out_dir, f"folhas_ponto_{mes}_{ano}_{int(datetime.datetime.now().timestamp())}.pdf")
                buffer.seek(0)
                with open(filename, 'wb') as f:
                    f.write(buffer.getvalue())
                logger.info(f"PDF salvo em (fallback): {filename}")
            else:
                logger.exception('Falha ao salvar PDF e sem out_dir para fallback')
        except Exception:
            logger.exception('Falha final ao salvar PDF em fallback')

    return True


def _impl_gerar_resumo_ponto(*args, **kwargs) -> bool:
    """Implementação migrada do gerador ``gerar_resumo_ponto``."""
    import importlib
    import calendar

    if len(args) < 2:
        raise TypeError("_impl_gerar_resumo_ponto espera pelo menos (mes, ano)")
    mes = args[0]
    ano = args[1]

    profissionais = kwargs.get('profissionais')
    escola = kwargs.get('escola')
    base2_path = kwargs.get('base2_path')
    base3_path = kwargs.get('base3_path')
    base4_path = kwargs.get('base4_path')

    try:
        from src.services.utils.pdf import salvar_e_abrir_pdf
    except Exception:
        try:
            from src.relatorios.gerar_pdf import salvar_e_abrir_pdf
        except Exception:
            raise

    legacy = _ensure_legacy_module('gerar_resumo_ponto', required=[
        'nome_mes_pt',
        'desenhar_bloco_escola',
        'desenhar_tabela_profissionais',
        'consultar_profissionais',
        'consultar_escola',
        '_encontrar_arquivo_base',
    ], candidate_filename='gerar_resumo_ponto.py')

    conn_provided = kwargs.get('conn')
    conn = None
    try:
        if profissionais is None or escola is None:
            if conn_provided is not None:
                conn = conn_provided
            else:
                try:
                    from src.core.conexao import conectar_bd
                    conn = conectar_bd()
                except Exception:
                    conn = None

            if profissionais is None:
                profissionais = legacy.consultar_profissionais(conn, mes, ano)
            if escola is None:
                escola = legacy.consultar_escola(conn, 60)

    finally:
        if conn is not None and conn_provided is None:
            try:
                conn.close()
            except Exception:
                pass

    ultimo_dia = calendar.monthrange(ano, mes)[1]
    try:
        from src.utils.dates import nome_mes_pt as _nome_mes_pt
        nome_mes = _nome_mes_pt(mes)
    except Exception:
        try:
            nome_mes = legacy.nome_mes_pt(mes)
        except Exception:
            nome_mes = str(mes)

    periodo = f"1 a {ultimo_dia} de {nome_mes} de {ano}"

    import unicodedata as _ud

    def _sem_acentos(txt: str) -> str:
        return "".join(ch for ch in _ud.normalize("NFD", txt) if _ud.category(ch) != "Mn")

    prioridade = [
        "Leandro Fonseca Lima",
        "Rosiane de Jesus Santos Melo",
    ]
    prioridade_norm = [_sem_acentos(n).casefold() for n in prioridade]

    def _key(p):
        nome = str(p.get("nome", ""))
        nome_norm = _sem_acentos(nome).casefold()
        try:
            idx = prioridade_norm.index(nome_norm)
            return (0, idx)
        except ValueError:
            return (1, nome_norm)

    profissionais = sorted(profissionais, key=_key)

    bloco1 = list(enumerate(profissionais[:17], start=1))
    bloco2 = list(enumerate(profissionais[17:40], start=18))
    bloco3 = list(enumerate(profissionais[40:], start=41))

    if base2_path is None:
        base2_path = legacy._encontrar_arquivo_base("Resumo de Frequencia2.pdf", "Resumo de Frequência2.pdf")
    if base3_path is None:
        base3_path = legacy._encontrar_arquivo_base("Resumo de Frequencia3.pdf", "Resumo de Frequência3.pdf")
    if base4_path is None:
        base4_path = legacy._encontrar_arquivo_base("Resumo de Frequencia4.pdf", "Resumo de Frequência4.pdf")

    from reportlab.pdfgen import canvas
    from PyPDF2 import PdfReader, PdfWriter

    reader2 = PdfReader(base2_path)
    p2 = reader2.pages[0]
    largura2 = float(p2.mediabox.width)
    altura2 = float(p2.mediabox.height)

    packet2 = io.BytesIO()
    can2 = canvas.Canvas(packet2, pagesize=(largura2, altura2))
    y_after_escola = legacy.desenhar_bloco_escola(can2, escola, largura2, altura2, altura2 - 98, mes, ano)
    legacy.desenhar_tabela_profissionais(can2, bloco1, largura2, altura2, altura2 - 250)
    can2.save()
    packet2.seek(0)
    overlay2 = PdfReader(packet2)
    pagina2 = PdfReader(base2_path).pages[0]
    pagina2.merge_page(overlay2.pages[0])

    reader3 = PdfReader(base3_path)
    p3 = reader3.pages[0]
    largura3 = float(p3.mediabox.width)
    altura3 = float(p3.mediabox.height)

    packet3 = io.BytesIO()
    can3 = canvas.Canvas(packet3, pagesize=(largura3, altura3))
    legacy.desenhar_tabela_profissionais(can3, bloco2, largura3, altura3, altura3 - 140)
    can3.save()
    packet3.seek(0)
    overlay3 = PdfReader(packet3)
    pagina3 = PdfReader(base3_path).pages[0]
    pagina3.merge_page(overlay3.pages[0])

    pagina4 = None
    if bloco3:
        reader4 = PdfReader(base4_path)
        p4 = reader4.pages[0]
        largura4 = float(p4.mediabox.width)
        altura4 = float(p4.mediabox.height)

        packet4 = io.BytesIO()
        can4 = canvas.Canvas(packet4, pagesize=(largura4, altura4))
        legacy.desenhar_tabela_profissionais(can4, bloco3, largura4, altura4, altura4 - 140)
        can4.save()
        packet4.seek(0)
        overlay4 = PdfReader(packet4)
        pagina4 = PdfReader(base4_path).pages[0]
        pagina4.merge_page(overlay4.pages[0])

    wfinal = PdfWriter()
    wfinal.add_page(pagina2)
    if bloco2:
        wfinal.add_page(pagina3)
    if bloco3 and pagina4 is not None:
        wfinal.add_page(pagina4)

    out_buf = io.BytesIO()
    wfinal.write(out_buf)
    out_buf.seek(0)

    salvar_e_abrir_pdf(out_buf)
    return True
