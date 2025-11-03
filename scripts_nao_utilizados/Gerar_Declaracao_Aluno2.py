from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import datetime

def gerar_declaracao_abnt(buffer, marcacoes, dados_aluno, dados_escola, responsaveis):
    # Definir estilo ABNT para parágrafos
    style_abnt = ParagraphStyle(
        name='ABNT',
        fontName='Helvetica',
        fontSize=12,
        leading=18,  # Espaçamento 1.5 entre linhas
        alignment=0,  # Alinhado à esquerda
        leftIndent=0,
        spaceBefore=12,
        spaceAfter=12,
    )

    # Definir estilo para título
    style_titulo = ParagraphStyle(
        name='Titulo',
        fontName='Helvetica-Bold',
        fontSize=14,
        alignment=1,  # Centralizado
        spaceAfter=20,  # Espaçamento após o título
    )

    # Definir margens padrão ABNT
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=2 * inch,
        leftMargin=3 * inch,
        topMargin=3 * inch,
        bottomMargin=2 * inch
    )

    elements = []

    # Cabeçalho com nome da escola
    cabecalho = [
        f"<b>ESTADO DO MARANHÃO</b>",
        f"<b>PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR</b>",
        f"<b>SECRETARIA MUNICIPAL DE EDUCAÇÃO</b>",
        f"<b>{dados_escola['nome']}</b>",
        f"INEP: {dados_escola['inep']}",
        f"CNPJ: {dados_escola['cnpj']}"
    ]

    # Adicionar o cabeçalho ao documento
    elements.append(Paragraph('<br/>'.join(cabecalho), style_abnt))
    elements.append(Spacer(1, 20))

    # Adicionar título da declaração
    elements.append(Paragraph("<b>DECLARAÇÃO ESCOLAR</b>", style_titulo))
    elements.append(Spacer(1, 20))

    # Corpo da declaração
    nome_aluno = dados_aluno['nome']
    turma = dados_aluno['turma']
    data_nascimento = dados_aluno['data_nascimento']

    texto_declaracao = f"""Declaramos, para os devidos fins, que {nome_aluno}, nascido(a) em {data_nascimento}, está regularmente matriculado(a) na escola {dados_escola['nome']} na turma {turma} no ano letivo de {datetime.datetime.now().year}. Nada consta que desabone sua conduta."""
    
    elements.append(Paragraph(texto_declaracao, style_abnt))

    # Observações ou outras informações adicionais
    if marcacoes:
        marcacoes_texto = "<br/>".join(marcacoes)
        elements.append(Paragraph(f"Observações:<br/>{marcacoes_texto}", style_abnt))

    # Assinaturas dos responsáveis
    elements.append(Spacer(1, 30))  # Espaço antes das assinaturas
    elements.append(Paragraph("Por ser verdade, firmamos o presente documento.", style_abnt))

    # Data e local
    data_atual = datetime.datetime.now().strftime("%d de %B de %Y")
    rodape = f"Paço do Lumiar, {data_atual}."
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(rodape, style_abnt))
    elements.append(Spacer(1, 40))

    # Espaço para a assinatura do diretor
    elements.append(Paragraph("______________________________", style_abnt))
    elements.append(Paragraph("Assinatura do(a) Diretor(a)", style_abnt))

    # Adiciona tabelas com as informações dos responsáveis
    if responsaveis:
        elements.append(Spacer(1, 20))
        for idx, responsavel in enumerate(responsaveis, start=1):
            grau_parentesco = 'Pai' if idx == 1 else 'Mãe' if idx == 2 else 'Responsável'
            tabela_responsavel = [
                ['Nome:', responsavel['nome']],
                ['Telefone:', responsavel['telefone']],
                ['Grau de Parentesco:', grau_parentesco]
            ]
            t = Table(tabela_responsavel, hAlign='LEFT')
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 20))

    # Constrói o PDF
    doc.build(elements)
