import os
import datetime
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import black, grey
from Lista_atualizada import create_pdf_buffer
from gerarPDF import salvar_e_abrir_pdf


def gerar_termo_responsabilidade(nome_escola: str = "ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES",
                                 inep: str = "21008485",
                                 cnpj_escola: str = "01.394.462/0001-01",
                                 razao_social_empresa: str = "____________________________________________________",
                                 cnpj_empresa: str = "______________________________",
                                 descricao_lista: str = "lista contendo nomes de alunos, responsáveis e telefones"):
    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        f"<b>{nome_escola}</b>",
        f"<b>INEP: {inep}</b>",
        f"<b>CNPJ: {cnpj_escola}</b>"
    ]

    figura_superior = os.path.join(os.path.dirname(__file__), 'logosemed.png')
    figura_inferior = os.path.join(os.path.dirname(__file__), 'logopaco.png')

    doc, buffer = create_pdf_buffer()
    elements = []

    # Cabeçalho
    data = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 0.5 * inch))

    elements.append(Paragraph('<b>TERMO DE RESPONSABILIDADE E CONFIDENCIALIDADE</b>',
                              ParagraphStyle(name='Titulo', fontSize=14, alignment=1)))
    elements.append(Spacer(1, 0.2 * inch))

    corpo = (
        f"Pelo presente instrumento, a empresa <b>{razao_social_empresa}</b>, inscrita no CNPJ sob o nº <b>{cnpj_empresa}</b>, \n"
        f"declara estar ciente e de acordo que os dados pessoais recebidos desta unidade escolar — {descricao_lista} — são \n"
        f"informações protegidas pela legislação aplicável, incluindo a Lei Geral de Proteção de Dados (Lei nº 13.709/2018 - LGPD). \n\n"
        f"A empresa compromete-se a: \n"
        f"1) Utilizar os dados exclusivamente para a finalidade de oferta e execução dos cursos aos alunos indicados; \n"
        f"2) Adotar medidas técnicas e administrativas aptas a proteger os dados contra acessos não autorizados, situações acidentais ou ilícitas \n"
        f"   de destruição, perda, alteração, comunicação ou difusão; \n"
        f"3) Manter a confidencialidade das informações, abstendo-se de compartilhar, ceder, vender ou divulgar os dados a terceiros; \n"
        f"4) Comunicar imediatamente à escola qualquer incidente de segurança que resulte em violação, vazamento ou acesso indevido; \n"
        f"5) Excluir ou devolver integralmente os dados, a pedido da escola, ao término da prestação dos serviços ou quando a sua conservação \n"
        f"   deixar de ser necessária; \n"
        f"6) Responsabilizar-se por quaisquer danos causados por uso inadequado, vazamento, acesso indevido ou tratamento irregular dos dados, \n"
        f"   isentando a escola de qualquer ônus decorrente de tais eventos.\n\n"
        f"Este termo entra em vigor na data de sua assinatura e permanece válido enquanto persistir o tratamento dos dados \n"
        f"decorrente da finalidade acima descrita."
    )

    elements.append(Paragraph(corpo, ParagraphStyle(name='Corpo', fontSize=11, leading=16, alignment=4)))
    elements.append(Spacer(1, 0.4 * inch))

    # Rodapé com data
    hoje = datetime.datetime.now().strftime('%d/%m/%Y')
    elements.append(Paragraph(f"Paco do Lumiar/MA, {hoje}.", ParagraphStyle(name='Data', fontSize=11, alignment=2)))
    elements.append(Spacer(1, 0.8 * inch))

    # Linhas de assinatura
    assinatura_data = [
        [Paragraph('<b>ESCOLA</b>', ParagraphStyle(name='AssTitulo', fontSize=10, alignment=1)),
         Paragraph('<b>EMPRESA</b>', ParagraphStyle(name='AssTitulo', fontSize=10, alignment=1))],
        [Paragraph('__________________________________________', ParagraphStyle(name='Linha', fontSize=10, alignment=1)),
         Paragraph('__________________________________________', ParagraphStyle(name='Linha', fontSize=10, alignment=1))],
        [Paragraph(nome_escola, ParagraphStyle(name='AssNome', fontSize=10, alignment=1)),
         Paragraph(razao_social_empresa, ParagraphStyle(name='AssNome', fontSize=10, alignment=1))],
        [Paragraph(f'CNPJ: {cnpj_escola}', ParagraphStyle(name='AssDoc', fontSize=9, alignment=1)),
         Paragraph(f'CNPJ: {cnpj_empresa}', ParagraphStyle(name='AssDoc', fontSize=9, alignment=1))]
    ]
    assinatura_table = Table(assinatura_data, colWidths=[3.5 * inch, 3.5 * inch])
    assinatura_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])
    assinatura_table.setStyle(assinatura_style)
    elements.append(assinatura_table)

    doc.build(elements)
    buffer.seek(0)
    salvar_e_abrir_pdf(buffer)


if __name__ == '__main__':
    gerar_termo_responsabilidade()


