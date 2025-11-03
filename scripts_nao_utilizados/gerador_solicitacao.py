import os
import mysql.connector as mysql_connector
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

def gerar_autorizacoes():
    def connecting(user_var, passwd, host, database):
        return mysql_connector.connect(
            user=user_var,
            password=passwd,
            host=host,
            database=database,
            auth_plugin='mysql_native_password'
        )

    try:
        conn = connecting('doncisio', '987412365', 'localhost', 'redeescola')
    except mysql_connector.Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        return

    cursor = conn.cursor(dictionary=True)

    # Consulta SQL para buscar os alunos e suas turmas, ordenados por série (1º, 2º, 3º, ...)
    query = """
        SELECT 
            a.nome AS 'NOME_DO_ALUNO', 
            s.nome AS 'NOME_DA_SERIE',
            a.sexo AS 'GENERO'
        FROM 
            Alunos a
        JOIN 
            Matriculas m ON a.id = m.aluno_id
        JOIN 
            Turmas t ON m.turma_id = t.id
        JOIN 
            Serie s ON t.serie_id = s.id
        WHERE 
            m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = 2024)
        AND 
            a.escola_id = 3
        AND 
            m.status = 'Ativo'
        ORDER BY s.nome;
    """

    cursor.execute(query)
    alunos = cursor.fetchall()

    # Estilos do texto
    estilo_texto = ParagraphStyle(
        name='Texto', 
        fontSize=12, 
        alignment=0, 
        leading=15  # Define o espaçamento entre linhas
    )

    # Nome do arquivo PDF
    nome_arquivo = os.path.join(os.getcwd(), f"Autorizacoes_passeio_tracoa.pdf")
    doc = SimpleDocTemplate(
        nome_arquivo, 
        pagesize=A4, 
        leftMargin=20,  # Define margens estreitas
        rightMargin=20, 
        topMargin=20, 
        bottomMargin=20
    )
    
    elements = []

    # Cabeçalhos da tabela
    tabela_dados = []
    turma_atual = None  # Variável para controlar a turma atual

    # Criar uma célula para cada aluno com o texto de autorização
    for aluno in alunos:
        nome_aluno = aluno['NOME_DO_ALUNO']
        nome_serie = aluno['NOME_DA_SERIE']
        nome_genero = aluno['GENERO']

        # Detectar se a turma mudou e adicionar uma quebra de página
        if turma_atual is not None and nome_serie != turma_atual:
            # Adicionar a tabela para a turma atual
            tabela = Table(tabela_dados, colWidths=[7.5 * inch])  # largura de coluna fixa para uma única coluna
            tabela.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Linha horizontal superior
                ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),  # Linha horizontal inferior
                ('LINEBELOW', (0, 0), (-1, -1), 1, colors.black),  # Linhas horizontais internas
            ]))
            elements.append(tabela)
            elements.append(PageBreak())
            tabela_dados = []  # Resetar os dados da tabela para a nova turma

        turma_atual = nome_serie

        # Texto da autorização com espaçamento entre linhas e quebras de linha ajustadas
        texto_autorizacao = f"""
            <b>TERMO DE AUTORIZAÇÃO</b><br/>
            SEMANA DAS CRIANÇAS<br/>
            Autorizo {'o aluno' if nome_genero == 'M' else 'a aluna'} <b>{nome_aluno}</b> do {nome_serie} a participar de um passeio no Viveiro do Tracoá localizado na Estrada de São José de Ribamar, Km 12, Nº 200.<br/>
            Data: <b>11/10/2024 (Sexta-feira)</b>.<br/>
            Horário: <b>7:30h às 10:30h</b>.<br/>
            Assinatura do responsável: ______________________________________________________<br/>
            <b>Obs.: ENTRADA NORMAL DOS ALUNOS.</b>
        """
        autorizacao_paragraph = Paragraph(texto_autorizacao, estilo_texto)
        
        # Adicionar a autorização como uma célula na tabela
        tabela_dados.append([autorizacao_paragraph])

    # Adicionar a última tabela ao documento
    if tabela_dados:
        tabela = Table(tabela_dados, colWidths=[7.5 * inch])  # largura de coluna fixa para uma única coluna
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Linha horizontal superior
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),  # Linha horizontal inferior
            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.black),  # Linhas horizontais internas
        ]))
        elements.append(tabela)

    # Gerar o PDF
    try:
        doc.build(elements)
        print(f"Arquivo '{nome_arquivo}' criado com sucesso.")
    except Exception as e:
        print(f"Erro ao gerar o arquivo PDF: {e}")

    conn.close()

gerar_autorizacoes()
