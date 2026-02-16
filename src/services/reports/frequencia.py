"""Relatórios de frequência e listas de frequência."""

import sys
from typing import Optional, Any, cast, Tuple

from src.core.config_logs import get_logger
from src.services.reports._utils import _find_image_in_repo, _ensure_legacy_module

logger = get_logger(__name__)


def gerar_relatorio_frequencia(*args, **kwargs) -> Tuple[bool, Optional[Any]]:
    """Wrapper compatível para geração de relatório de frequência."""
    _mod = sys.modules.get('relatorio_frequencia') or sys.modules.get('gerar_relatorio_frequencia')
    if _mod is not None:
        if hasattr(_mod, 'gerar_relatorio_frequencia'):
            resultado = cast(Any, _mod).gerar_relatorio_frequencia(*args, **kwargs)
            if isinstance(resultado, tuple):
                success = bool(resultado[0]) if len(resultado) > 0 else True
                data = resultado[1] if len(resultado) > 1 else None
                return success, data
            if isinstance(resultado, str):
                return True, resultado
            if isinstance(resultado, bool):
                return resultado, None
            return bool(resultado), None
        raise AttributeError("Módulo injetado não possui 'gerar_relatorio_frequencia'")

    try:
        _leg = _ensure_legacy_module('relatorio_frequencia', candidate_filename='relatorio_frequencia.py')
        if hasattr(_leg, 'gerar_relatorio_frequencia'):
            resultado = cast(Any, _leg).gerar_relatorio_frequencia(*args, **kwargs)
            if isinstance(resultado, tuple):
                success = bool(resultado[0]) if len(resultado) > 0 else True
                data = resultado[1] if len(resultado) > 1 else None
                return success, data
            if isinstance(resultado, str):
                return True, resultado
            if isinstance(resultado, bool):
                return resultado, None
            return bool(resultado), None
    except Exception:
        pass

    return True, None


def gerar_lista_frequencia() -> bool:
    """Encapsula a chamada ao gerador de lista de frequência (``lista_frequencia``)."""
    _mod = sys.modules.get('lista_frequencia')
    if _mod is not None:
        if not hasattr(_mod, 'lista_frequencia'):
            raise AttributeError("Módulo 'lista_frequencia' injetado não possui 'lista_frequencia'")
        _mod.lista_frequencia()
        return True

    try:
        return _impl_lista_frequencia()
    except Exception:
        try:
            _mod = _ensure_legacy_module('lista_frequencia', required=['lista_frequencia'], candidate_filename='lista_frequencia.py')
        except Exception:
            logger.exception("Módulo 'lista_frequencia' não disponível para gerar lista de frequência")
            raise

        if not hasattr(_mod, 'lista_frequencia'):
            raise AttributeError("Módulo 'lista_frequencia' não possui 'lista_frequencia'")

        _mod.lista_frequencia()
        return True


def gerar_tabela_frequencia() -> bool:
    """Encapsula o gerador de tabela/frequência."""
    _mod = sys.modules.get('gerar_tabela_frequencia')
    if _mod is not None:
        if hasattr(_mod, 'lista_frequencia'):
            cast(Any, _mod).lista_frequencia()
            return True
        if hasattr(_mod, 'gerar_tabela_frequencia'):
            cast(Any, _mod).gerar_tabela_frequencia()
            return True

    try:
        return _impl_gerar_tabela_frequencia()
    except Exception:
        try:
            _mod = _ensure_legacy_module('gerar_tabela_frequencia', required=['lista_frequencia', 'gerar_tabela_frequencia'], candidate_filename='gerar_tabela_frequencia.py')
        except Exception:
            logger.exception("Módulo 'gerar_tabela_frequencia' não disponível para gerar tabela de frequência")
            raise

        if hasattr(_mod, 'lista_frequencia'):
            cast(Any, _mod).lista_frequencia()
            return True
        if hasattr(_mod, 'gerar_tabela_frequencia'):
            cast(Any, _mod).gerar_tabela_frequencia()
            return True

        raise AttributeError("Módulo 'gerar_tabela_frequencia' não possui função conhecida para gerar a tabela de frequência")


# ---------------------------------------------------------------------------
# Implementações migradas
# ---------------------------------------------------------------------------


def _impl_gerar_tabela_frequencia() -> bool:
    """Implementação migrada do gerador de tabela/frequência."""
    import pandas as pd
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    import os
    import datetime

    try:
        from src.relatorios.listas.lista_atualizada import fetch_student_data
    except Exception:
        logger.exception('Não foi possível importar fetch_student_data para gerar_tabela_frequencia')
        raise

    try:
        from src.services.utils.pdf import salvar_e_abrir_pdf, create_pdf_buffer
    except Exception:
        try:
            from src.relatorios.gerar_pdf import salvar_e_abrir_pdf, create_pdf_buffer
        except Exception:
            logger.exception('Não foi possível importar helpers de PDF para gerar_tabela_frequencia')
            raise

    ano_letivo = datetime.datetime.now().year
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        logger.info('Nenhum dado de aluno encontrado para gerar_tabela_frequencia')
        return False

    df = pd.DataFrame(dados_aluno)

    figura_superior = _find_image_in_repo('logopacobranco.png') or ''
    figura_inferior = _find_image_in_repo('logopaco.jpg') or ''

    doc, buffer = create_pdf_buffer()
    elements = []

    style_total = ParagraphStyle(name='TotalStyle', parent=None, fontSize=10, alignment=1, wordWrap='CJK')
    style_transferencia = ParagraphStyle(name='TransferenciaStyle', parent=None, fontSize=10, alignment=1, textColor=colors.red, wordWrap='CJK')

    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        if turma_df.empty:
            continue

        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else ''

        data = [
            [Image(figura_inferior, width=1.25 * inch, height=.75 * inch),
             Paragraph('<br/>'.join([
                 "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
                 "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
                 "<b>INEP: 21008485</b>",
                 "<b>CNPJ: 01.394.462/0001-01</b>"
             ]), ParagraphStyle(name='Header', fontSize=12, alignment=1)),
             Image(figura_superior, width=1.5 * inch, height=1 * inch)]
        ]
        table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
        table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        elements.append(table)
        elements.append(Spacer(1, 0.25 * inch))

        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {ano_letivo}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=14, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(f"<b>PROFESSOR(A): {nome_professor} </b>", ParagraphStyle(name='ProfessoraTitulo', fontSize=14, alignment=0)))
        elements.append(Spacer(1, 0.15 * inch))

        total_masculino = turma_df[turma_df['SEXO'] == 'M'].shape[0]
        total_feminino = turma_df[turma_df['SEXO'] == 'F'].shape[0]
        total_transferidos = turma_df[turma_df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])].shape[0]
        elements.append(Paragraph(f"TOTAIS: MASCULINO ({total_masculino}) FEMININO ({total_feminino}) - TRANSFERIDOS: {total_transferidos}", ParagraphStyle(name='TotaisAlunos', fontSize=12, alignment=0)))
        elements.append(Spacer(1, 0.15 * inch))

        texto_total_vertical = '<br/>'.join(list("TOTAL"))
        datas = pd.date_range(start=f'{ano_letivo}-01-01', periods=25).date
        tabela_frequencia = [['Nº', 'Nome'] + ['' for _ in datas] + [Paragraph(texto_total_vertical, style_total)]]

        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]

        for i, (_, row) in enumerate(turma_df.iterrows(), start=1):
            if row.get('SITUAÇÃO') in ['Transferido', 'Transferida']:
                data_transferencia = row.get('DATA_TRANSFERENCIA')
                data_transferencia = data_transferencia.strftime('%d/%m/%Y') if data_transferencia else "Data não disponível"
                texto_transferencia = f"{row.get('SITUAÇÃO')} em {data_transferencia}"
                linha = [i, row.get('NOME DO ALUNO')] + [''] * (len(datas) + 1)
                linha[2] = Paragraph(texto_transferencia, style_transferencia)
                table_style.append(('SPAN', (2, i), (-1, i)))
            else:
                linha = [i, row.get('NOME DO ALUNO')] + [''] * len(datas) + ['']
            tabela_frequencia.append(linha)

        row_heights = [1 * inch]
        row_heights.extend([0.25 * inch] * (len(tabela_frequencia) - 1))
        table = Table(tabela_frequencia, colWidths=[0.282 * inch, 3 * inch] + [0.25 * inch] * len(datas) + [0.35 * inch], rowHeights=row_heights)
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(PageBreak())

    doc.build(elements)
    salvar_e_abrir_pdf(buffer)
    return True


def _impl_lista_frequencia() -> bool:
    """Implementação migrada de ``lista_frequencia``."""
    import pandas as pd
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    import os
    import datetime

    try:
        from src.relatorios.listas.lista_atualizada import fetch_student_data
    except Exception:
        logger.exception('Não foi possível importar fetch_student_data para lista_frequencia')
        raise

    try:
        from src.services.utils.pdf import salvar_e_abrir_pdf, create_pdf_buffer
    except Exception:
        try:
            from src.relatorios.gerar_pdf import salvar_e_abrir_pdf, create_pdf_buffer
        except Exception:
            logger.exception('Não foi possível importar helpers de PDF para lista_frequencia')
            raise

    ano_letivo = datetime.datetime.now().year
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        logger.info('Nenhum dado de aluno encontrado para lista_frequencia')
        return False

    df = pd.DataFrame(dados_aluno)

    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    figura_superior = _find_image_in_repo('logopacobranco.png') or ''
    figura_inferior = _find_image_in_repo('logopaco.jpg') or ''

    doc, buffer = create_pdf_buffer()
    elements = []

    style_total = ParagraphStyle(name='TotalStyle', parent=None, fontSize=10, alignment=1, wordWrap='CJK')
    style_transferencia = ParagraphStyle(name='TransferenciaStyle', parent=None, fontSize=10, alignment=1, textColor=colors.red, wordWrap='CJK')

    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        if turma_df.empty:
            continue

        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else ''

        data = [
            [Image(figura_inferior, width=1.25 * inch, height=.75 * inch),
             Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1)),
             Image(figura_superior, width=1.5 * inch, height=1 * inch)]
        ]
        table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
        table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        elements.append(table)
        elements.append(Spacer(1, 0.25 * inch))

        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=14, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(f"<b>PROFESSOR(A): {nome_professor} </b>", ParagraphStyle(name='ProfessoraTitulo', fontSize=14, alignment=0)))
        elements.append(Spacer(1, 0.15 * inch))

        total_masculino = turma_df[turma_df['SEXO'] == 'M'].shape[0]
        total_feminino = turma_df[turma_df['SEXO'] == 'F'].shape[0]
        total_transferidos = turma_df[turma_df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])].shape[0]
        elements.append(Paragraph(f"TOTAIS: MASCULINO ({total_masculino}) FEMININO ({total_feminino}) - TRANSFERIDOS: {total_transferidos}", ParagraphStyle(name='TotaisAlunos', fontSize=12, alignment=0)))
        elements.append(Spacer(1, 0.15 * inch))

        texto_total_vertical = '<br/>'.join(list("TOTAL"))
        datas = pd.date_range(start=f'{ano_letivo}-01-01', periods=25).date
        tabela_frequencia = [['Nº', 'Nome'] + ['' for _ in datas] + [Paragraph(texto_total_vertical, style_total)]]

        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]

        for i, (_, row) in enumerate(turma_df.iterrows(), start=1):
            if row.get('SITUAÇÃO') in ['Transferido', 'Transferida']:
                data_transferencia = row.get('DATA_TRANSFERENCIA')
                data_transferencia = data_transferencia.strftime('%d/%m/%Y') if data_transferencia else "Data não disponível"
                texto_transferencia = f"{row.get('SITUAÇÃO')} em {data_transferencia}"
                linha = [i, row.get('NOME DO ALUNO')] + [''] * (len(datas) + 1)
                linha[2] = Paragraph(texto_transferencia, style_transferencia)
                table_style.append(('SPAN', (2, i), (-1, i)))
            else:
                linha = [i, row.get('NOME DO ALUNO')] + [''] * len(datas) + ['']
            tabela_frequencia.append(linha)

        row_heights = [1 * inch]
        row_heights.extend([0.25 * inch] * (len(tabela_frequencia) - 1))
        table = Table(tabela_frequencia, colWidths=[0.282 * inch, 3 * inch] + [0.25 * inch] * len(datas) + [0.35 * inch], rowHeights=row_heights)
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(PageBreak())

    doc.build(elements)
    salvar_e_abrir_pdf(buffer)
    return True
