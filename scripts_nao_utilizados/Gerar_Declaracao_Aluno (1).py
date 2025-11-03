import os
import io
import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import TableStyle
from conexao import conectar_bd
from extrairdados import obter_dados_aluno, obter_dados_responsaveis, obter_dados_escola
from gerarPDF import salvar_e_abrir_pdf

def gerar_declaracao_aluno(aluno_id, marcacoes):
    conn = conectar_bd()
    cursor = conn.cursor()

    # Exemplo de uso
    escola_id = 3  # Aqui você pode receber o ID dinamicamente, por exemplo, via input ou outra lógica
    dados_escola = obter_dados_escola(cursor, escola_id)

    if not dados_escola:
        print(f"Escola com ID {escola_id} não encontrada.")
    else:
        nome_escola, inep_escola, cnpj_escola, endereco_escola, municipio_escola = dados_escola[1], dados_escola[3], dados_escola[4], dados_escola[2], dados_escola[5]
        # Informações do cabeçalho com os dados da escola
        cabecalho = [
            "ESTADO DO MARANHÃO",
            "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
            "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
            f"<b>{nome_escola}</b>",  # Substitua pelo nome da escola
            f"<b>INEP: {inep_escola}</b>",  # Substitua pelo INEP da escola
            f"<b>CNPJ: {cnpj_escola}</b>"  # Substitua pelo CNPJ da escola
        ]
        rodape_texto = [
            f"{endereco_escola} - {municipio_escola}."
        ]

    dados_aluno = obter_dados_aluno(cursor, aluno_id)
    if not dados_aluno:
        print("Aluno não encontrado.")
        return

    # Extrair informações do dicionário
    nome_aluno = dados_aluno["nome_aluno"]
    nascimento = dados_aluno["nascimento"]
    sexo = dados_aluno["sexo"]
    nome_serie = dados_aluno["nome_serie"]
    nome_turma = dados_aluno["nome_turma"]
    turno = dados_aluno["turno"]
    nivel_ensino = dados_aluno["nivel_ensino"]
    status = dados_aluno["status"]

    # Obter dados dos responsáveis
    responsaveis = obter_dados_responsaveis(cursor, aluno_id)
    responsavel1 = responsaveis[0] if len(responsaveis) > 0 else None
    responsavel2 = responsaveis[1] if len(responsaveis) > 1 else None

    cursor.close()
    conn.close()

    turma = f"{nome_serie} {nome_turma}"

    def formatar_data(data):
        meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro',
                 'Novembro', 'Dezembro']
        return f"{data.day} de {meses[data.month - 1]} de {data.year}"

    # Formatar a data de nascimento
    data_nascimento = pd.to_datetime(nascimento).strftime("%d/%m/%Y") if pd.notnull(nascimento) else ""

    # Formatar a data atual no formato "DIA de MÊS de ANO"
    data_documento = formatar_data(datetime.datetime.now()) 

    # Caminhos das figuras
    figura_superior = os.path.join(os.path.dirname(__file__), 'pacologo.png')
    figura_inferior = os.path.join(os.path.dirname(__file__), 'logopacobranco.png')

    # Determinar o gênero do aluno com base na coluna "SEXO"
    genero_aluno = 'feminino' if sexo == 'F' else 'masculino'

    # Criar o PDF em memória
    buffer = io.BytesIO()
    # Define as margens da página (em pontos) para margens conforme ABNT
    left_margin = 85    # Margem esquerda (3 cm)
    right_margin = 56   # Margem direita (2 cm)
    top_margin = 85     # Margem superior (3 cm)
    bottom_margin = 56  # Margem inferior (2 cm)

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

    # Criar uma tabela para alinhar horizontalmente
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

    # Adicionar conteúdo ao PDF
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("<b>Declaração Escolar</b>", ParagraphStyle(name='DeclaracaoTitulo', fontSize=16, alignment=1)))
    elements.append(Spacer(1, 0.5 * inch))

    # Definindo o estilo do parágrafo com espaçamento entre linhas
    style_declaracao = ParagraphStyle(
        name='DeclaracaoTexto',
        fontSize=12,
        alignment=4,
        leading=18  # Ajusta o espaçamento entre linhas (1.5 vezes o tamanho da fonte padrão de 12pt)
    )

    if pd.isna(responsavel1):
        if pd.isna(responsavel2):
            elements.append(Paragraph(
                f"Declaramos, para os devidos fins, que <b>{nome_aluno}</b>, nascid{'o' if genero_aluno == 'masculino' else 'a'} em <b>{data_nascimento}</b>, filh{'o' if genero_aluno == 'masculino' else 'a'} de, está regularmente matriculad{'o' if genero_aluno == 'masculino' else 'a'} na <b>{nome_escola}</b> no <b>{turma} </b> do {nivel_ensino} no ano de <b>{datetime.datetime.now().year}</b>, {'no turno <b>matutino</b>' if turno == 'MAT' else 'no turno <b>vespertino</b>'}.",
                style_declaracao))
        else:
            elements.append(Paragraph(
                f"Declaramos, para os devidos fins, que <b>{nome_aluno}</b>, nascid{'o' if genero_aluno == 'masculino' else 'a'} em <b>{data_nascimento}</b>, filh{'o' if genero_aluno == 'masculino' else 'a'} de <b>{responsavel2}</b>, está regularmente matriculad{'o' if genero_aluno == 'masculino' else 'a'} no <b>{nome_escola}</b> na <b>{turma}</b> do {nivel_ensino} no ano de <b>{datetime.datetime.now().year}</b>, {'no turno <b>matutino</b>' if turno == 'MAT' else 'no turno <b>vespertino</b>'}.",
                style_declaracao))
    elif pd.isna(responsavel2):
        elements.append(Paragraph(
            f"Declaramos, para os devidos fins, que <b>{nome_aluno}</b>, nascid{'o' if genero_aluno == 'masculino' else 'a'} em <b>{data_nascimento}</b>, filh{'o' if genero_aluno == 'masculino' else 'a'} de <b>{responsavel1}</b>, está regularmente matriculad{'o' if genero_aluno == 'masculino' else 'a'} no <b>{nome_escola}</b> na <b>{turma} </b> do {nivel_ensino} no ano de <b>{datetime.datetime.now().year}</b>, {'no turno <b>matutino</b>' if turno == 'MAT' else 'no turno <b>vespertino</b>'}.",
            style_declaracao))
    else:
        elements.append(Paragraph(
            f"Declaramos, para os devidos fins, que <b>{nome_aluno}</b>, nascid{'o' if genero_aluno == 'masculino' else 'a'} em <b>{data_nascimento}</b>, filh{'o' if genero_aluno == 'masculino' else 'a'} de <b>{responsavel1}</b> e <b>{responsavel2}</b>, está regularmente matriculad{'o' if genero_aluno == 'masculino' else 'a'} na <b>{nome_escola}</b> no <b>{turma}</b> do {nivel_ensino} no ano de <b>{datetime.datetime.now().year}</b>, {'no turno <b>matutino</b>' if turno == 'MAT' else 'no turno <b>vespertino</b>'}.",
            style_declaracao))

    elements.append(Spacer(1, 0.5 * inch))
    #elements.append(
    #    Paragraph(f"{'O Aluno' if genero_aluno == 'masculino' else 'A Aluna'} irá cursar o ____ ano no ano de 202__.",
    #              style_declaracao))
    elements.append(Paragraph("Nada consta que desabone sua conduta.",  ParagraphStyle(name='texto direita', fontSize=12, alignment=2)))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("Por ser verdade, firmo o presente documento.", ParagraphStyle(name='texto direita', fontSize=12, alignment=2)))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("<b>Declaração para fim de:</b>", style_declaracao))
    elements.append(Spacer(1, 0.1 * inch))

    # Segunda tabela 3x5
    data2 = [
    [f"{'(X)' if marcacoes[0][0] else '(   )'} Transferência", 
     f"{'(X)' if marcacoes[0][1] else '(   )'} Bolsa Família", 
     f"{'(X)' if marcacoes[0][2] else '(   )'} Trabalho",
     f"{'(X)' if marcacoes[0][3] else '(   )'} Outros:_____________________________"]
]
    table2 = Table(data2, hAlign='LEFT')
    table2.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Adiciona esta linha para alinhar verticalmente ao topo
        ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Adiciona esta linha para adicionar espaço à esquerda
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),  # Adiciona esta linha para adicionar espaço à direita
        ('TOPPADDING', (0, 0), (-1, -1), 5),  # Adiciona esta linha para adicionar espaço no topo
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),  # Adiciona esta linha para adicionar espaço na parte inferior
    ]))
    elements.append(table2)

    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("Paço do Lumiar – MA, " + data_documento + ".",
                              ParagraphStyle(name='DeclaracaoTexto', fontSize=12, alignment=2)))

    # Adicionar espaço para assinatura do Diretor Geral
    elements.append(Spacer(1, 1 * inch))
    elements.append(Paragraph("______________________________________",
                              ParagraphStyle(name='DeclaracaoTexto', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("GESTOR(A)", ParagraphStyle(name='DeclaracaoTexto', fontSize=12, alignment=1)))
    # Adicionar o rodapé centralizado
    rodape_texto = f"{endereco_escola} - {municipio_escola}."

    def rodape(canvas, doc):
        width, height = letter
        canvas.saveState()
        canvas.setFont('Helvetica', 10)

        # Concatenar endereço e município
        rodape_texto = f"{endereco_escola} - {municipio_escola}"

        # Centralizar o texto no rodapé
        canvas.drawCentredString(width / 2, 0.75 * inch, rodape_texto)

        canvas.restoreState()
    

    # Build the PDF
    doc.build(elements, onFirstPage=rodape, onLaterPages=rodape)
    buffer.seek(0)

    salvar_e_abrir_pdf(buffer)