import io
import os
import pandas as pd
import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, grey
from Lista_atualizada import fetch_student_data
from gerar_documentos import PASTAS_TURMAS, criar_pastas_se_nao_existirem, salvar_pdf, adicionar_cabecalho

def lista_fardamento():
    """Gera um PDF com a lista de alunos para receberem o fardamento pelos pais/responsaveis, agrupados por turma."""
    ano_letivo = 2025
    dados_aluno = fetch_student_data(ano_letivo)
    
    if not dados_aluno:
        print("Nenhum dado de aluno encontrado.")
        return
        
    df = pd.DataFrame(dados_aluno)
    criar_pastas_se_nao_existirem()
    
    # Definir caminhos das imagens no diretório principal
    diretorio_principal = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    figura_superior = os.path.join(diretorio_principal, "logosemed.png")
    figura_inferior = os.path.join(diretorio_principal, "logopaco.jpg")
    
    cabecalho = [
        "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>EM PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 06.003.636/0001-73</b>"
    ]
    
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        nome_turma_completo = f"{nome_serie} {nome_turma}" if nome_turma else nome_serie
        
        if nome_turma_completo not in PASTAS_TURMAS:
            print(f"Aviso: Turma '{nome_turma_completo}' não está mapeada para uma pasta. Pulando...")
            continue
            
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            leftMargin=36,
            rightMargin=18,
            topMargin=18,
            bottomMargin=18
        )
        elements = []
        
        # Adicionar capa inicial
        adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior)
        elements.append(Spacer(1, 2 * inch))
        elements.append(Paragraph("<b>LISTA DE ALUNOS <br/> E <br/>FARDAMENTOS RECEBIDOS</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1, leading=24)))
        elements.append(Spacer(1, 2.5 * inch))
        elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
        elements.append(PageBreak())
        
        # Extrair nome do professor e filtrar alunos ativos
        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Sem Professor'
        turma_df = turma_df[turma_df['SITUAÇÃO'] == 'Ativo']
        
        # Adicionar cabeçalho da página
        adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior, 11)
        elements.append(Spacer(1, 0.125 * inch))
        # Adicionar título da 
        elements.append(Paragraph("Lista de alunos para receberem o fardamento escolar pelos pais/responsáveis", 
                                ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Adicionar título da turma
        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", 
                                ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Criar tabela de presença com larguras ajustadas para modo paisagem
        data = [['Nº', 'Nome', 'Assinatura do Responsável', 'Parentesco']]
        for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
            nome = row['NOME DO ALUNO']
            assinatura = ''
            parentesco = ''
            data.append([row_num, nome, assinatura, parentesco])
        
        # Ajustando as larguras das colunas para melhor aproveitamento do espaço horizontal
        table = Table(data, colWidths=[0.4 * inch, 3 * inch, 3 * inch, 1.5 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), white),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        elements.append(table)
        elements.append(PageBreak())
        
        doc.build(elements)
        buffer.seek(0)
        salvar_pdf(buffer, nome_turma_completo, "Fardamento")