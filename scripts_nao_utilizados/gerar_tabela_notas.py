import io
import os
import pandas as pd
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, red
from conexao import conectar_bd
from gerarPDF import salvar_e_abrir_pdf
from Lista_atualizada import fetch_student_data
from biblio_editor import definir_coordenador
from scripts_nao_utilizados.gerar_documentos import PASTAS_TURMAS, criar_pastas_se_nao_existirem, salvar_pdf, adicionar_cabecalho

def criar_pastas_se_nao_existirem():
    """Cria as pastas especificadas no mapeamento, se elas não existirem."""
    for pasta in PASTAS_TURMAS.values():
        if not os.path.exists(pasta):
            os.makedirs(pasta)
            print(f"Pasta criada: {pasta}")

def buscar_disciplinas_nivel_3():
    """Retorna as disciplinas do nível 3 (anos finais) para a escola."""
    disciplinas = [
        {"id": 802, "nome": "PORTUGUÊS"},
        {"id": 803, "nome": "MATEMÁTICA"},
        {"id": 804, "nome": "CIÊNCIAS"},
        {"id": 805, "nome": "HISTÓRIA"},
        {"id": 806, "nome": "GEOGRAFIA"},
        {"id": 807, "nome": "ARTES"},
        {"id": 808, "nome": "ENS. RELIGIOSO"},
        {"id": 809, "nome": "ED. FÍSICA"},
        {"id": 810, "nome": "FILOSOFIA"},
        {"id": 811, "nome": "INGLÊS"},
    ]
    return disciplinas

def adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior):
    """Adiciona o cabeçalho com as imagens e texto."""
    # Criar tabela com imagem e texto do cabeçalho no padrão de Lista_atualizada.py
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
    elements.append(Spacer(1, 0.2*inch))

def adicionar_tabela_turma_anos_finais(elements, cabecalho, figura_superior, figura_inferior, turma_df, nome_serie, nome_turma, turno):
    """Adiciona uma tabela para cada disciplina da turma dos anos finais."""
    nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else ''
    
    disciplinas = buscar_disciplinas_nivel_3()
    
    # Estilo para o texto de transferência
    style_transferencia = ParagraphStyle(
        name='TransferenciaStyle',
        parent=None,
        fontSize=10,
        alignment=1,
        textColor=red,
        wordWrap='CJK',
    )
    
    for disciplina in disciplinas:
        adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior)
        elements.append(Spacer(1, 0.1 * inch))
        
        coordenador = definir_coordenador(turma_df)
        
        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
        elements.append(Paragraph(f"<b>Disciplina: {disciplina['nome']}</b>", ParagraphStyle(name='DisciplinaTitulo', fontSize=12, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))
        adicionar_assinaturas(elements, nome_professor, coordenador)
        
        data = [['Nº', 'Nome do Aluno', 'T1', 'T2', 'T3', 'T4', 'Média', 'Faltas']]
        table_style = []
        for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
            nome = row['NOME DO ALUNO']
            if row['SITUAÇÃO'] in ['Transferido', 'Transferida']:
                # Para alunos transferidos, mesclar as células e mostrar o status
                data_transferencia = row['DATA_TRANSFERENCIA'].strftime('%d/%m/%Y') if row['DATA_TRANSFERENCIA'] else "Data não disponível"
                texto_transferencia = f"{row['SITUAÇÃO']} em {data_transferencia}"
                linha = [row_num, nome] + [''] * 6
                linha[2] = Paragraph(texto_transferencia, style_transferencia)
                table_style.append(('SPAN', (2, row_num), (-1, row_num)))  # Mescla da coluna 2 até a última coluna
            else:
                # Para alunos ativos, manter as células normais
                notas = ['', '', '', '', '', '']
                linha = [row_num, nome] + notas
            data.append(linha)
            
        table = Table(data, colWidths=[0.33 * inch, 3 * inch] + [0.52 * inch] * 6)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), white),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ] + table_style))
        elements.append(table)
        elements.append(PageBreak())

def adicionar_assinaturas(elements, nome_professor, coordenador):
    """Adiciona as linhas de assinatura do professor e coordenador."""
    paragrafo_professor = Paragraph(f"<b>PROFESSOR@: {nome_professor}</b>", ParagraphStyle(name='ProfessoraTitulo', fontSize=12, alignment=1))
    paragrafo_coordenador = Paragraph(f"<b>Coordenadora: {coordenador}</b>", ParagraphStyle(name='ProfessoraTitulo', fontSize=12, alignment=1))
    
    dados_tabela_assinatura = [[paragrafo_professor, paragrafo_coordenador]]
    tabela_assinatura = Table(dados_tabela_assinatura, colWidths=[4.5 * inch, 3.5 * inch])
    tabela_assinatura.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    elements.append(tabela_assinatura)

def adicionar_tabela_turma_anos_iniciais(elements, cabecalho, figura_superior, figura_inferior, turma_df, nome_serie, nome_turma, turno):
    """Adiciona uma tabela para cada turma dos anos iniciais."""
    nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Sem Professor'

    # Estilo para o texto de transferência
    style_transferencia = ParagraphStyle(
        name='TransferenciaStyle',
        parent=None,
        fontSize=10,
        alignment=1,
        textColor=red,
        wordWrap='CJK',
    )

    adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior)
    elements.append(Spacer(1, 0.1 * inch))

    coordenador = definir_coordenador(turma_df)

    elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.1 * inch))
    adicionar_assinaturas(elements, nome_professor, coordenador)

    data = [['Nº', 'Nome', 'PORT.', 'MTM.', 'CNC.', 'HST.', 'GGF.', 'ART.', 'REL.', 'REC.']]
    table_style = []
    for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
        nome = row['NOME DO ALUNO']
        if row['SITUAÇÃO'] in ['Transferido', 'Transferida']:
            # Para alunos transferidos, mesclar as células e mostrar o status
            data_transferencia = row['DATA_TRANSFERENCIA'].strftime('%d/%m/%Y') if row['DATA_TRANSFERENCIA'] else "Data não disponível"
            texto_transferencia = f"{row['SITUAÇÃO']} em {data_transferencia}"
            linha = [row_num, nome] + [''] * 8
            linha[2] = Paragraph(texto_transferencia, style_transferencia)
            table_style.append(('SPAN', (2, row_num), (-1, row_num)))  # Mescla da coluna 2 até a última coluna
        else:
            # Para alunos ativos, manter as células normais
            notas = ['', '', '', '', '', '', '', '']  # Notas vazias
            linha = [row_num, nome] + notas
        data.append(linha)

    table = Table(data, colWidths=[0.33 * inch, 3 * inch] + [0.52 * inch] * 8)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), white),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ] + table_style))
    elements.append(table)
    elements.append(PageBreak())

def criar_pasta_sebastiana():
    """Cria a pasta específica para a professora Sebastiana."""
    pasta_base = os.path.dirname(list(PASTAS_TURMAS.values())[0])
    pasta_sebastiana = os.path.join(pasta_base, "PROFESSORA SEBASTIANA")
    if not os.path.exists(pasta_sebastiana):
        os.makedirs(pasta_sebastiana)
        print(f"Pasta criada: {pasta_sebastiana}")
    return pasta_sebastiana

def adicionar_tabela_sebastiana(elements, cabecalho, figura_superior, figura_inferior, turma_df, nome_serie, nome_turma, turno):
    """Adiciona uma tabela específica para a professora Sebastiana com as disciplinas de História e Geografia."""
    # Estilo para o texto de transferência
    style_transferencia = ParagraphStyle(
        name='TransferenciaStyle',
        parent=None,
        fontSize=10,
        alignment=1,
        textColor=red,
        wordWrap='CJK',
    )

    adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior)
    elements.append(Spacer(1, 0.1 * inch))

    elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Adicionar informações da professora
    elements.append(Paragraph(f"<b>PROFESSOR(A) VOLANTE: Sebastiana Santos Silva</b>", ParagraphStyle(name='ProfessoraTitulo', fontSize=12, alignment=0)))
    elements.append(Spacer(1, 0.15 * inch))

    data = [['Nº', 'Nome', 'HST.', 'GGF.']]
    table_style = []
    for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
        nome = row['NOME DO ALUNO']
        if row['SITUAÇÃO'] in ['Transferido', 'Transferida']:
            # Para alunos transferidos, mesclar as células e mostrar apenas o status
            texto_transferencia = row['SITUAÇÃO']
            linha = [row_num, nome] + [''] * 2
            linha[2] = Paragraph(texto_transferencia, style_transferencia)
            table_style.append(('SPAN', (2, row_num), (-1, row_num)))  # Mescla da coluna 2 até a última coluna
        else:
            # Para alunos ativos, manter as células normais
            notas = ['', '']  # Notas vazias para História e Geografia
            linha = [row_num, nome] + notas
        data.append(linha)

    table = Table(data, colWidths=[0.33 * inch, 3 * inch] + [0.52 * inch] * 2)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), white),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ] + table_style))
    elements.append(table)
    elements.append(PageBreak())

def lista_notas():
    """Gera um PDF com as notas dos alunos agrupadas por turma."""
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
    figura_inferior = os.path.join(diretorio_principal, "logopaco.png")
    
    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]
    
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        nome_turma_completo = f"{nome_serie} {nome_turma}" if nome_turma else nome_serie
        
        if nome_turma_completo not in PASTAS_TURMAS:
            print(f"Aviso: Turma '{nome_turma_completo}' não está mapeada para uma pasta. Pulando...")
            continue
            
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=18,
            topMargin=18,
            bottomMargin=18
        )
        elements = []
        
        # Adicionar capa inicial
        adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior)
        elements.append(Spacer(1, 3.3 * inch))
        elements.append(Paragraph(f"<b>{'TABELA DE NOTAS ANOS INICIAIS' if turma_df[turma_df['ID_SERIE'] > 7].empty else 'TABELA DE NOTAS ANOS FINAIS'}</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1)))
        elements.append(Spacer(1, 4 * inch))
        elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
        elements.append(PageBreak())
        
        # Adicionar tabelas de notas
        if turma_df[turma_df['ID_SERIE'] > 7].empty:
            adicionar_tabela_turma_anos_iniciais(elements, cabecalho, figura_superior, figura_inferior, turma_df, nome_serie, nome_turma, turno)
        else:
            adicionar_tabela_turma_anos_finais(elements, cabecalho, figura_superior, figura_inferior, turma_df, nome_serie, nome_turma, turno)
            
        doc.build(elements)
        buffer.seek(0)
        salvar_pdf(buffer, nome_turma_completo, "Notas")

def lista_sebastiana():
    """Gera um PDF com a lista de notas dos alunos para a professora Sebastiana, agrupados por turma."""
    ano_letivo = 2025
    dados_aluno = fetch_student_data(ano_letivo)
    
    if not dados_aluno:
        print("Nenhum dado de aluno encontrado.")
        return
        
    df = pd.DataFrame(dados_aluno)
    criar_pastas_se_nao_existirem()
    pasta_sebastiana = criar_pasta_sebastiana()
    
    # Definir caminhos das imagens no diretório principal
    diretorio_principal = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    figura_superior = os.path.join(diretorio_principal, "logosemed.png")
    figura_inferior = os.path.join(diretorio_principal, "logopaco.png")
    
    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]
    
    # Filtrar apenas as turmas do 1º ao 5º ano
    df = df[df['ID_SERIE'] > 7]  # ID_SERIE > 7 corresponde aos anos iniciais
    
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        nome_turma_completo = f"{nome_serie} {nome_turma}" if nome_turma else nome_serie
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=18,
            topMargin=18,
            bottomMargin=18
        )
        elements = []
        
        # Adicionar capa inicial
        adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior)
        elements.append(Spacer(1, 3.3 * inch))
        elements.append(Paragraph(f"<b>TABELA DE NOTAS - HISTÓRIA E GEOGRAFIA</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1)))
        elements.append(Spacer(1, 4 * inch))
        elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
        elements.append(PageBreak())
        
        # Adicionar tabela específica para a professora Sebastiana
        adicionar_tabela_sebastiana(elements, cabecalho, figura_superior, figura_inferior, turma_df, nome_serie, nome_turma, turno)
            
        doc.build(elements)
        buffer.seek(0)
        
        # Salvar na pasta específica da professora
        nome_arquivo = f"Notas_{nome_turma_completo}.pdf"
        caminho_arquivo = os.path.join(pasta_sebastiana, nome_arquivo)
        with open(caminho_arquivo, 'wb') as f:
            f.write(buffer.getvalue())
        print(f"PDF salvo em: {caminho_arquivo}")

if __name__ == "__main__":
    lista_notas()
    lista_sebastiana()