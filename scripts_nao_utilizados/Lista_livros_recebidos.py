import io
import os
import pandas as pd
import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, grey
from conexao import conectar_bd
from gerarPDF import salvar_e_abrir_pdf
from Lista_atualizada import fetch_student_data

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

def add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior):
    data = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
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
    elements.append(Paragraph("<b>LISTA DE ALUNOS <br/> E <br/>LIVROS RECEBIDOS</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1, leading=24)))
    elements.append(Spacer(1, 2.5 * inch))
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
    elements.append(PageBreak())

def add_class_table15(elements, turma_df, nome_serie, nome_turma, turno, nome_professor, figura_inferior, cabecalho):
    data = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')    # Alinhamento horizontal
    ])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph(f"<b>PROFESSOR@: {nome_professor} </b>", ParagraphStyle(name='ProfessoraTitulo', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.15 * inch))

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

def add_class_table69(elements, turma_df, nome_serie, nome_turma, turno, nome_professor, figura_inferior, cabecalho):
    data = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')    # Alinhamento horizontal
    ])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.25 * inch))
    # elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
    # elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(f"<b>PROFESSOR@: {nome_professor} </b>", ParagraphStyle(name='ProfessoraTitulo', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.15 * inch))

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

    figura_superior = os.path.join(os.path.dirname(__file__), 'logosemed.png')
    figura_inferior = os.path.join(os.path.dirname(__file__), 'logopaco.png')

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
        # Verifica se a coluna 'ID_SERIE' existe no DataFrame
        if 'ID_SERIE' in turma_df.columns:
            # Filtra os alunos com ID_SERIE <= 7
            turma_df_15 = turma_df[turma_df['ID_SERIE'] <= 7]
            # Filtra os alunos com ID_SERIE > 7
            turma_df_69 = turma_df[turma_df['ID_SERIE'] > 7]
        
            # Adiciona a tabela para alunos com ID_SERIE <= 7
            if not turma_df_15.empty:
                add_class_table15(elements, turma_df_15, nome_serie, nome_turma, turno, nome_professor, figura_inferior, cabecalho)
            
            # Adiciona a tabela para alunos com ID_SERIE > 7
            if not turma_df_69.empty:
                add_class_table69(elements, turma_df_69, nome_serie, nome_turma, turno, nome_professor, figura_inferior, cabecalho)
        else:
            print(f"Coluna 'ID_SERIE' não encontrada para a turma: {nome_serie}, {nome_turma}, {turno}")
    # Gera o PDF
    doc.build(elements)
    buffer.seek(0)
    salvar_e_abrir_pdf(buffer)

lista_livros_recebidos()