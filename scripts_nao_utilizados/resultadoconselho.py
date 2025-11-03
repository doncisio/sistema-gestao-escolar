import os
import pandas as pd
import datetime
import mysql.connector as mysql_connector
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, grey
import platform
from conexao import conectar_bd

def lista_atualizada():
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
    figura_superior = os.path.join(os.path.dirname(__file__), 'logosemed.png')
    figura_inferior = os.path.join(os.path.dirname(__file__), 'logopaco.png')

    # Criar o documento PDF
    nome_arquivo = 'Lista de Alunos 2024.pdf'
    # Define as margens da página (em pontos) para margens estreitas
    left_margin = 36    # Margem esquerda (0,5 polegadas)
    right_margin = 18   # Margem direita (0,5 polegadas)
    top_margin = 18     # Margem superior (0,5 polegadas)
    bottom_margin = 18  # Margem inferior (0,5 polegadas)

    # Cria o documento PDF com as margens ajustadas
    doc = SimpleDocTemplate(
        nome_arquivo, 
        pagesize=letter, 
        leftMargin=left_margin, 
        rightMargin=right_margin, 
        topMargin=top_margin, 
        bottomMargin=bottom_margin
    )
    elements = []

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
    elements.append(Spacer(1, 3.3 * inch))
    elements.append(Paragraph("<b>RELAÇÃO DE ALUNOS</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1)))
    elements.append(Spacer(1, 4 * inch))
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
    elements.append(PageBreak())

    # Função para formatar os números de telefone
    def formatar_telefone(telefone):
        return f"{telefone[:5]}-{telefone[5:]}"

    # Agrupar os dados por nome_serie, nome_turma e turno
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        # Extraindo o nome do professor da turma
        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Sem Professor'
        
        # Filtrar apenas os alunos com a situação "Ativo"
        turma_df = turma_df[turma_df['SITUAÇÃO'] == 'Ativo']

        # Adicionar o cabeçalho antes de cada tabela
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

        elements.append(Spacer(1, 0.5 * inch))

        # Adicionar o título da turma
        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=14, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))
        # Adicionar informações sobre a professora e totais de alunos por sexo
        elements.append(Paragraph(f"<b>PROFESSOR@: {nome_professor} </b>", ParagraphStyle(name='ProfessoraTitulo', fontSize=14, alignment=0)))
        elements.append(Spacer(1, 0.15 * inch))
        total_masculino = turma_df[turma_df['SEXO'] == 'M'].shape[0]
        total_feminino = turma_df[turma_df['SEXO'] == 'F'].shape[0]
        elements.append(Paragraph(f"TOTAIS: MASCULINO ({total_masculino}) FEMININO ({total_feminino})", ParagraphStyle(name='TotaisAlunos', fontSize=12, alignment=0)))
        elements.append(Spacer(1, 0.15 * inch))

        # Criar a tabela para a turma
        data = [['Nº', 'Nome', 'Nascimento', 'Telefones', 'Observação']]
        # Função para formatar os dados, garantindo que 'NASCIMENTO' não seja None
        for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
            nome = row['NOME DO ALUNO']
            sexo = 'M' if row['SEXO'] == 'M' else 'F'
            
            # Verifica se a data de nascimento é None, e atribui uma string padrão se for o caso
            if row['NASCIMENTO']:
                nascimento = row['NASCIMENTO'].strftime('%d/%m/%Y')
            else:
                nascimento = "Data não disponível"
            
            # Obter os telefones, remover duplicatas e formatar
            telefones = row['TELEFONES']
            if telefones:
                telefones = list(set(telefones.split('/')))
            else:
                telefones = []
            telefones = [formatar_telefone(telefone) for telefone in telefones if telefone]
            telefones_str = ' / '.join(telefones) if telefones else 'N/A'

            # Adicionar a observação (vazia)
            observacao = ''  # Mantém a célula vazia para anotação

            data.append([row_num, nome, nascimento, telefones_str, observacao])


        table = Table(data)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ])
        table.setStyle(table_style)
        elements.append(table)

        # Adicionar a quebra de página após a última tabela
        elements.append(PageBreak())

    doc.build(elements)

    # Abrir o PDF no programa padrão do sistema operacional
    abrir_pdf_com_programa_padrao(nome_arquivo)

def abrir_pdf_com_programa_padrao(pdf_path):
    if platform.system() == "Windows":
        os.startfile(pdf_path)
    elif platform.system() == "Darwin":  # macOS
        os.system(f"open '{pdf_path}'")
    else:  # Linux e outros sistemas
        os.system(f"xdg-open '{pdf_path}'")