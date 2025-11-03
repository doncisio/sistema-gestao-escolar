import io
import os
import pandas as pd
import datetime
from reportlab.lib.pagesizes import letter
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
        pagesize=letter,
        leftMargin=left_margin, 
        rightMargin=right_margin, 
        topMargin=top_margin, 
        bottomMargin=bottom_margin
    )
    return doc, buffer

def add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior):
    data = [
        [Image(figura_inferior, width=2.5 * inch, height=0.5 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')    # Alinhamento horizontal
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 3.75 * inch))
    elements.append(Paragraph("<b>LISTA DE ALUNOS <br/> E <br/>FARDAMENTOS RECEBIDOS</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1, leading=24)))
    elements.append(Spacer(1, 3.75 * inch))
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
    elements.append(PageBreak())

def add_class_table(elements, turma_df, nome_serie, nome_turma, turno, nome_professor, figura_inferior, cabecalho):
    data = [
        [Image(figura_inferior, width=2.5 * inch, height=0.5 * inch)],
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
    elements.append(Paragraph("<b>Lista de Assinaturas - Recebimento de Fardamento Escolar</b>", ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(f"<b>PROFESSOR@: {nome_professor} </b>", ParagraphStyle(name='ProfessoraTitulo', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.15 * inch))

    data = [['Nº', 'Nome','ASSINATURA DO RESPONSÁVEL']]
    for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
        nome = row['NOME DO ALUNO']
        data.append([row_num, nome, ''])

    table = Table(data, colWidths=[0.282 * inch, 3 * inch] + [3.5 * inch])
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),  # Pintar as duas primeiras linhas de cinza
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('GRID', (0, 0), (-1, -1), 1, black),
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(PageBreak())

def lista_fardamentos_recebidos():
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
        add_class_table(elements, turma_df, nome_serie, nome_turma, turno, nome_professor, figura_inferior, cabecalho)
            
    # Gera o PDF
    doc.build(elements)
    buffer.seek(0)
    salvar_e_abrir_pdf(buffer)

lista_fardamentos_recebidos()