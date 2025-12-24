import io
import os
import pandas as pd
import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, grey
from src.core.conexao import conectar_bd
from src.relatorios.gerar_pdf import salvar_e_abrir_pdf
from src.relatorios.listas.lista_atualizada import fetch_student_data
from src.core.config import get_image_path

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

def add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior, capa_text=None):
    # Tentar carregar imagem inferior; usar spacer vazio se não existir
    if figura_inferior and os.path.exists(figura_inferior):
        img_elem = Image(figura_inferior, width=3 * inch, height=0.7 * inch)
    else:
        img_elem = Spacer(1, 0.1 * inch)

    data = [
        [img_elem],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')    # Alinhamento horizontal
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 2 * inch))
    # Texto da capa (padrão para livros recebidos)
    if capa_text is None:
        capa_text = "<b>LISTA DE ALUNOS <br/> E <br/>LIVROS RECEBIDOS</b>"
    elements.append(Paragraph(capa_text, ParagraphStyle(name='Capa', fontSize=24, alignment=1, leading=24)))
    elements.append(Spacer(1, 2.5 * inch))
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
    elements.append(PageBreak())

def add_class_table15(elements, turma_df, nome_serie, nome_turma, turno, nome_professor, figura_inferior, cabecalho, desc_text: str = None):
    # Tentar carregar imagem inferior; usar spacer vazio se não existir
    if figura_inferior and os.path.exists(figura_inferior):
        img_elem = Image(figura_inferior, width=3 * inch, height=0.7 * inch)
    else:
        img_elem = Spacer(1, 0.1 * inch)

    data = [
        [img_elem],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')    # Alinhamento horizontal
    ])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.15 * inch))

    # Inserir descrição (após cabeçalho e antes da tabela) quando fornecida
    if desc_text:
        elements.append(Paragraph(desc_text, ParagraphStyle(name='Desc', fontSize=10, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))

    data = [['Nº', 'Nome'] + [f'Disciplinas {nome_serie} {nome_turma}']*7+ ['ASSINATURA DO RESPONSÁVEL'],
            ['Nº', 'Nome'] + ['PRT', 'MTM','CNC', 'HST', 'GEO','ING', 'ART']+ ['ASSINATURA DO RESPONSÁVEL']]
    for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
        nome = row['NOME DO ALUNO']
        # nascimento = row['NASCIMENTO'].strftime('%d/%m/%Y') if row['NASCIMENTO'] else "Data não disponível"
        # transtorno = row['TRANSTORNO']
        data.append([row_num, nome, '', '', '', '', '', '', '', ''])

    table = Table(data, colWidths=[0.282 * inch, 3 * inch] + [0.42 * inch] * 7 + [3.5 * inch])
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 1), grey),  # Pintar as duas primeiras linhas de cinza
        ('TEXTCOLOR', (0, 0), (-1, 1), white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 2), (-1, -1), white),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (9, 0), (9, 1)),
        ('SPAN', (2, 0), (8, 0)),
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(PageBreak())

def add_class_table69(elements, turma_df, nome_serie, nome_turma, turno, nome_professor, figura_inferior, cabecalho, desc_text: str = None):
    # Tentar carregar imagem inferior; usar spacer vazio se não existir
    if figura_inferior and os.path.exists(figura_inferior):
        img_elem = Image(figura_inferior, width=3 * inch, height=0.7 * inch)
    else:
        img_elem = Spacer(1, 0.1 * inch)

    data = [
        [img_elem],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')    # Alinhamento horizontal
    ])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.15 * inch))

    # Inserir descrição (após cabeçalho e antes da tabela) quando fornecida
    if desc_text:
        elements.append(Paragraph(desc_text, ParagraphStyle(name='Desc', fontSize=10, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))

    data = [['Nº', 'Nome'] + [f'Disciplinas {nome_serie} {nome_turma}']*7+ ['ASSINATURA DO RESPONSÁVEL'],
            ['Nº', 'Nome'] + ['PRT', 'MTM','CNC', 'HST', 'GEO','ING', 'ART']+ ['ASSINATURA DO RESPONSÁVEL']]
    for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
        nome = row['NOME DO ALUNO']
        # nascimento = row['NASCIMENTO'].strftime('%d/%m/%Y') if row['NASCIMENTO'] else "Data não disponível"
        # transtorno = row['TRANSTORNO']
        data.append([row_num, nome, '', '', '', '', '', '', '', ''])

    table = Table(data, colWidths=[0.282 * inch, 3 * inch] + [0.42 * inch] * 7 + [3.5 * inch])
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 1), grey),  # Pintar as duas primeiras linhas de cinza
        ('TEXTCOLOR', (0, 0), (-1, 1), white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 2), (-1, -1), white),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (9, 0), (9, 1)),
        ('SPAN', (2, 0), (8, 0)),
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(PageBreak())

def lista_livros_recebidos():
    ano_letivo = 2025
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        return

    df = pd.DataFrame(dados_aluno)
    # print(df[['NOME_SERIE', 'NOME_TURMA', 'TURNO']].isnull().sum())

    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    figura_superior = str(get_image_path('logosemed.png'))
    figura_inferior = str(get_image_path('logopaco.png'))

    doc, buffer = create_pdf_buffer()
    elements = []

    add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior)

    # Adiciona as tabelas de alunos
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        print(f"{nome_serie}, {nome_turma}, {turno} - {turma_df.shape[0]}")
        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else ' '
        turma_df = turma_df[turma_df['SITUAÇÃO'] == 'Ativo']
        if turma_df.empty:
            print(f"Nenhum aluno ativo encontrado para a turma: {nome_serie}, {nome_turma}, {turno}")
            continue

        # Descrição será inserida pela função de criação de tabela (após cabeçalho)

        # Verifica se a coluna 'ID_SERIE' existe no DataFrame
        if 'ID_SERIE' in turma_df.columns:
            # Filtra os alunos com ID_SERIE <= 7
            turma_df_15 = turma_df[turma_df['ID_SERIE'] <= 7]
            # Filtra os alunos com ID_SERIE > 7
            turma_df_69 = turma_df[turma_df['ID_SERIE'] > 7]

            # Adiciona a tabela para alunos com ID_SERIE <= 7
            if not turma_df_15.empty:
                add_class_table15(
                    elements, turma_df_15, nome_serie, nome_turma, turno, nome_professor,
                    figura_inferior, cabecalho,
                    desc_text=f"Lista de livros devolvidos por alunos do {nome_serie} {nome_turma} {turno}. Registre a assinatura do responsável."
                )

            # Adiciona a tabela para alunos com ID_SERIE > 7
            if not turma_df_69.empty:
                add_class_table69(
                    elements, turma_df_69, nome_serie, nome_turma, turno, nome_professor,
                    figura_inferior, cabecalho,
                    desc_text=f"Lista de livros devolvidos por alunos do {nome_serie} {nome_turma} {turno}. Registre a assinatura do responsável."
                )
        else:
            print(f"Coluna 'ID_SERIE' não encontrada para a turma: {nome_serie}, {nome_turma}, {turno}")
    # Gera o PDF
    doc.build(elements)
    buffer.seek(0)
    salvar_e_abrir_pdf(buffer)

# Não executar automaticamente ao importar. Use `gerar_controle_livros()` ou
# invoque `lista_livros_recebidos()` / `lista_livros_devolvidos()` sob demanda.

def lista_livros_devolvidos():
    """
    Gera um PDF com lista de livros devolvidos por turma.
    Implementação simples que reutiliza os dados de alunos e cria
    uma tabela com coluna para indicar devolução/assinatura.
    """
    ano_letivo = datetime.datetime.now().year
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        return

    df = pd.DataFrame(dados_aluno)

    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    figura_superior = str(get_image_path('logosemed.png'))
    figura_inferior = str(get_image_path('logopaco.png'))

    doc, buffer = create_pdf_buffer()
    elements = []

    # Capa (texto ajustado para devolvidos)
    capa_text = "<b>LISTA DE ALUNOS <br/> E <br/>LIVROS DEVOLVIDOS</b>"
    add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior, capa_text=capa_text)

    # Tabelas por turma (usar mesmas tabelas do relatório de recebidos)
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        print(f"{nome_serie}, {nome_turma}, {turno} - {turma_df.shape[0]}")
        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else ' '
        turma_df = turma_df[turma_df['SITUAÇÃO'] == 'Ativo']
        if turma_df.empty:
            print(f"Nenhum aluno ativo encontrado para a turma: {nome_serie}, {nome_turma}, {turno}")
            continue

        # Descrição será inserida pela função de criação de tabela (após cabeçalho)

        # Verifica se a coluna 'ID_SERIE' existe no DataFrame
        if 'ID_SERIE' in turma_df.columns:
            # Filtra os alunos com ID_SERIE <= 7
            turma_df_15 = turma_df[turma_df['ID_SERIE'] <= 7]
            # Filtra os alunos com ID_SERIE > 7
            turma_df_69 = turma_df[turma_df['ID_SERIE'] > 7]

            # Adiciona a tabela para alunos com ID_SERIE <= 7
            if not turma_df_15.empty:
                add_class_table15(
                    elements, turma_df_15, nome_serie, nome_turma, turno, nome_professor,
                    figura_inferior, cabecalho,
                    desc_text=f"Lista de livros devolvidos por alunos do {nome_serie} {nome_turma} {turno}. Registre a assinatura do responsável."
                )

            # Adiciona a tabela para alunos com ID_SERIE > 7
            if not turma_df_69.empty:
                add_class_table69(
                    elements, turma_df_69, nome_serie, nome_turma, turno, nome_professor,
                    figura_inferior, cabecalho,
                    desc_text=f"Lista de livros devolvidos por alunos do {nome_serie} {nome_turma} {turno}. Registre a assinatura do responsável."
                )
        else:
            print(f"Coluna 'ID_SERIE' não encontrada para a turma: {nome_serie}, {nome_turma}, {turno}")

    # Gera o PDF
    doc.build(elements)
    buffer.seek(0)
    salvar_e_abrir_pdf(buffer)


def gerar_controle_livros():
    """Gera os dois PDFs (recebidos e devolvidos) por turma."""
    try:
        lista_livros_recebidos()
    except Exception as e:
        print(f"Erro ao gerar lista de livros recebidos: {e}")

    try:
        lista_livros_devolvidos()
    except Exception as e:
        print(f"Erro ao gerar lista de livros devolvidos: {e}")