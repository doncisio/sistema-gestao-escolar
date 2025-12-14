import pandas as pd
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
import datetime
from src.core.config import get_image_path
from src.relatorios.gerar_pdf import salvar_e_abrir_pdf
from src.relatorios.listas.lista_atualizada import fetch_student_data
from src.relatorios.gerar_pdf import create_pdf_buffer

# Cache global para imagens e estilos
_IMAGE_CACHE = {}
_STYLE_CACHE = {}

def _get_cached_image(path, width, height):
    """Retorna uma imagem em cache para evitar recarregamento."""
    key = (path, width, height)
    if key not in _IMAGE_CACHE:
        _IMAGE_CACHE[key] = Image(path, width=width, height=height)
    return _IMAGE_CACHE[key]

def _get_cached_style(name, **kwargs):
    """Retorna um estilo em cache para evitar recriação."""
    key = (name, tuple(sorted(kwargs.items())))
    if key not in _STYLE_CACHE:
        _STYLE_CACHE[key] = ParagraphStyle(name=name, **kwargs)
    return _STYLE_CACHE[key]
def lista_frequencia():
    ano_letivo = 2025
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        return

    df = pd.DataFrame(dados_aluno)
    # print(df[['NOME_SERIE', 'NOME_TURMA', 'TURNO']].isnull().sum())

    # Informações do cabeçalho
    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    # Caminhos das figuras
    figura_superior = str(get_image_path('logopacobranco.png'))
    figura_inferior = str(get_image_path('logopaco.jpg'))

    # Criar o documento PDF
    doc, buffer = create_pdf_buffer()
    elements = []
    # Estilo para o texto "TOTAL" com quebra de linha
    style_total = _get_cached_style('TotalStyle', fontSize=10, alignment=1, wordWrap='CJK')
    style_transferencia = _get_cached_style('TransferenciaStyle', fontSize=10, alignment=1, textColor=colors.red, wordWrap='CJK')
    header_style = _get_cached_style('Header', fontSize=12, alignment=1)
    turma_style = _get_cached_style('TurmaTitulo', fontSize=14, alignment=1)
    prof_style = _get_cached_style('ProfessoraTitulo', fontSize=14, alignment=0)
    totais_style = _get_cached_style('TotaisAlunos', fontSize=12, alignment=0)

    # Carregar imagens em cache
    img_sup = _get_cached_image(figura_superior, 1.5 * inch, 1 * inch)
    img_inf = _get_cached_image(figura_inferior, 1.25 * inch, .75 * inch)

    # Agrupar os dados por nome_serie, nome_turma e turno
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else ''
        # Removido o filtro de alunos ativos para incluir os transferidos
        if turma_df.empty:
            continue

        # Adicionar o cabeçalho
        data = [
            [img_inf,
             Paragraph('<br/>'.join(cabecalho), header_style),
             img_sup]
        ]
        table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
        table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        elements.append(table)
        elements.append(Spacer(1, 0.25 * inch))

        # Adicionar o título da turma
        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", turma_style))
        elements.append(Spacer(1, 0.1 * inch))

        # Adicionar informações sobre a professora e totais de alunos por sexo
        elements.append(Paragraph(f"<b>PROFESSOR(A): {nome_professor} </b>", prof_style))
        elements.append(Spacer(1, 0.15 * inch))

        # Usar máscaras booleanas para cálculos mais eficientes
        mask_masculino = turma_df['SEXO'] == 'M'
        mask_feminino = turma_df['SEXO'] == 'F'
        mask_transferidos = turma_df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])
        
        total_masculino = mask_masculino.sum()
        total_feminino = mask_feminino.sum()
        total_transferidos = mask_transferidos.sum()
        elements.append(Paragraph(f"TOTAIS: MASCULINO ({total_masculino}) FEMININO ({total_feminino}) - TRANSFERIDOS: {total_transferidos}", totais_style))
        elements.append(Spacer(1, 0.15 * inch))

        # Criar a tabela de frequência
        texto_total_vertical = '<br/>'.join(list("TOTAL"))
        datas = pd.date_range(start='2025-01-01', periods=25).date
        tabela_frequencia = [['Nº', 'Nome'] + ['' for data in datas] + [Paragraph(texto_total_vertical, style_total)]]
        
        # Lista para armazenar os estilos da tabela
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
            if row['SITUAÇÃO'] in ['Transferido', 'Transferida']:
                # Para alunos transferidos, mesclar as células e mostrar o status
                data_transferencia = row['DATA_TRANSFERENCIA'].strftime('%d/%m/%Y') if row['DATA_TRANSFERENCIA'] else "Data não disponível"
                texto_transferencia = f"{row['SITUAÇÃO']} em {data_transferencia}"
                # Mesclar todas as células das colunas de datas e a coluna TOTAL
                linha = [i, row['NOME DO ALUNO']] + [''] * (len(datas) + 1)
                # Adicionar o texto de transferência na primeira célula mesclada
                linha[2] = Paragraph(texto_transferencia, style_transferencia)
                # Adicionar estilo para mesclar as células
                table_style.append(('SPAN', (2, i), (-1, i)))  # Mescla da coluna 2 até a última coluna
            else:
                # Para alunos ativos, manter as células normais
                linha = [i, row['NOME DO ALUNO']] + [''] * len(datas) + ['']
            tabela_frequencia.append(linha)

        row_heights = [1 * inch]  # Altura da primeira linha (cabeçalho)
        row_heights.extend([0.25 * inch] * (len(tabela_frequencia) - 1))  # Altura das demais linhas
        table = Table(tabela_frequencia, colWidths=[0.282 * inch, 3 * inch] + [0.25 * inch] * len(datas)+ [0.35 * inch], rowHeights=row_heights)
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(PageBreak())

    # Finalizar o documento
    doc.build(elements)
    buffer.seek(0)
    try:
        from src.relatorios.gerar_pdf import salvar_e_abrir_pdf as _salvar_helper
    except Exception:
        _salvar_helper = None

    saved_path = None
    try:
        if _salvar_helper:
            try:
                saved_path = _salvar_helper(buffer)
            except Exception:
                saved_path = None

        if not saved_path:
            import tempfile
            from src.utils.utilitarios.gerenciador_documentos import salvar_documento_sistema
            from src.utils.utilitarios.tipos_documentos import TIPO_LISTA_FREQUENCIA

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            try:
                tmp.write(buffer.getvalue())
                tmp.close()
                descricao = f"Lista de Frequência - {datetime.datetime.now().year}"
                try:
                    salvar_documento_sistema(tmp.name, TIPO_LISTA_FREQUENCIA, funcionario_id=1, finalidade='Secretaria', descricao=descricao)
                    saved_path = tmp.name
                except Exception:
                    try:
                        if _salvar_helper:
                            buffer.seek(0)
                            _salvar_helper(buffer)
                    except Exception:
                        pass
            finally:
                pass
    finally:
        try:
            buffer.close()
        except Exception:
            pass

# lista_frequencia()
