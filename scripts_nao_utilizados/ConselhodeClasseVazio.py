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


def a_preencher_conselho():
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    # Consulta SQL para buscar os dados necessários
    query = """
        SELECT 
        a.nome AS 'NOME DO ALUNO', 
        a.sexo AS 'SEXO', 
        a.data_nascimento AS 'NASCIMENTO',
        s.nome AS 'NOME_SERIE', 
        t.nome AS 'NOME_TURMA', 
        t.turno AS 'TURNO', 
        m.status AS 'SITUAÇÃO',
        f.nome AS 'NOME_PROFESSOR',
        GROUP_CONCAT(DISTINCT r.telefone ORDER BY r.id SEPARATOR '/') AS 'TELEFONES'
    FROM 
        Alunos a
    JOIN 
        Matriculas m ON a.id = m.aluno_id
    JOIN 
        Turmas t ON m.turma_id = t.id
    JOIN 
        Serie s ON t.serie_id = s.id
    LEFT JOIN 
        ResponsaveisAlunos ra ON a.id = ra.aluno_id
    LEFT JOIN 
        Responsaveis r ON ra.responsavel_id = r.id
    LEFT JOIN
        Funcionarios f ON f.turma = t.id AND f.cargo = 'Professor@'
    WHERE 
        m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = 2024)
    AND 
        a.escola_id = 3
        AND s.id <= 7 -- Filtro para séries com ID menor ou igual a 7
    GROUP BY 
        a.id, a.nome, a.sexo, a.data_nascimento, s.nome, t.nome, t.turno, m.status, f.nome
    ORDER BY
        a.nome ASC;
    """

    cursor.execute(query)
    dados_aluno = cursor.fetchall()

    # Convertendo os dados para um DataFrame
    df = pd.DataFrame(dados_aluno)

    # Adicionando a coluna 'OBSERVACAO' com valor padrão vazio
    df['OBSERVACAO'] = ''

    # Ordenar o DataFrame por série, turma e nome do aluno
    df.sort_values(by=['NOME_SERIE', 'NOME_TURMA', 'NOME DO ALUNO'], inplace=True)

    # Informações do cabeçalho
    cabecalho = [
        "ESTADO DO MARANHÃO",
        "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>UEB PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 06.003.636/0001-73</b>"
    ]

    # Caminhos das figuras
    figura_superior = os.path.join(os.path.dirname(__file__), 'pacologo.png')
    figura_inferior = os.path.join(os.path.dirname(__file__), 'logopacobranco.png')

    # Criar o documento PDF
    buffer = io.BytesIO()
    # Define as margens da página (em pontos) para margens estreitas
    left_margin = 45    # Margem esquerda (0,5 polegadas)
    right_margin = 45   # Margem direita (0,5 polegadas)
    top_margin = 36     # Margem superior (0,5 polegadas)
    bottom_margin = 36  # Margem inferior (0,5 polegadas)

    # Cria o documento PDF com as margens ajustadas
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        leftMargin=left_margin, 
        rightMargin=right_margin, 
        topMargin=top_margin, 
        bottomMargin=bottom_margin
    )
    elements = []
    # Passo 1: Definir a data como uma string
    data_string = "16/12/2024"

    # Passo 2: Converter a string em um objeto datetime
    data = datetime.datetime.strptime(data_string, "%d/%m/%Y")

    # Passo 3: Extrair dia, mês e ano
    dia = data.day
    mes = data.month
    ano = data.year
    # Passo 4: Criar listas para os meses e dias por extenso
    dias_extenso = [
        "zero", "um", "dois", "três", "quatro", "cinco",
        "seis", "sete", "oito", "nove", "dez",
        "onze", "doze", "treze", "quatorze", "quinze",
        "dezesseis", "dezessete", "dezoito", "dezenove",
        "vinte", "vinte e um", "vinte e dois", "vinte e três",
        "vinte e quatro", "vinte e cinco", "vinte e seis",
        "vinte e sete", "vinte e oito", "vinte e nove",
        "trinta", "trinta e um"
    ]

    meses_extenso = [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]

    # Passo 5: Formatar a string final
    data_formatada = f"Aos {dias_extenso[dia]} dias do mês de {meses_extenso[mes - 1]} do presente ano"
    # Adicionar a capa
    data = [
        [Image(figura_superior, width=1 * inch, height=1 * inch),
         Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1)),
         Image(figura_inferior, width=1.5 * inch, height=1 * inch)]
    ]
    table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, .5 * inch))
    elements.append(Paragraph("<b>ATA DE CONSELHO DE CLASSE</b>", ParagraphStyle(name='titulo', fontSize=14, alignment=1)))
    elements.append(Spacer(1, .25 * inch))
    elements.append(Paragraph(f"{data_formatada} realizou-se a reunião presencial do Conselho de Classe Final no turno matutino com a presença da coordenação, gestão, professores e administrativo onde finalizamos o último processo avaliativo e na condição de presidente da reunião, lavramos o seguinte resultado.", ParagraphStyle(name='Ano', fontSize=12, alignment=4, leading=18, firstLineIndent=30)))
    # Passo para adicionar a tabela dos alunos no final do PDF

    # Criar tabela com os dados dos alunos
    dados_tabela_alunos = []

    # Contador para a coluna N°
    contador = 1

    for index, row in df.iterrows():
        turma_completa = f"{row['NOME_SERIE']} {row['NOME_TURMA']}"
        # Adiciona uma string vazia para a coluna 'Situação'
        dados_tabela_alunos.append([contador, row['NOME DO ALUNO'].upper(), turma_completa.upper(), ''])  # Situação em branco
        contador += 1  # Incrementa o contador para o próximo aluno

    # Definindo as colunas da tabela
    colunas_tabela_alunos = ['N°', 'ESTUDANTE', 'TURMA', 'SITUAÇÃO FINAL']

    # Criando a tabela dos alunos
    tabela_alunos = Table([colunas_tabela_alunos] + dados_tabela_alunos, colWidths=[.5 * inch]+[3.75 * inch]+[.8 * inch]+[2 * inch], rowHeights=[0.35 * inch] * (len(dados_tabela_alunos) + 1) )

    # Estilo da tabela dos alunos
    estilo_tabela_alunos = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),     # Alinhamento à esquerda para a coluna de Nome do Aluno
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 14),
        ('BACKGROUND', (0, 1), (-1,-1), white),
        ('GRID', (0, 0), (-1,-1), 1.5 , black),
    ])

    # Aplicar estilo à tabela dos alunos
    tabela_alunos.setStyle(estilo_tabela_alunos)

    # Adicionar espaçamento antes da tabela dos alunos e adicionar a tabela aos elementos do PDF.
    elements.append(Spacer(1,.5 * inch))
    elements.append(tabela_alunos)
    # Construindo o PDF
    doc.build(elements)

    # Resetar o buffer para o início
    buffer.seek(0)

    salvar_e_abrir_pdf(buffer)

a_preencher_conselho()