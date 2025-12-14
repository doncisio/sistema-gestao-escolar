import os
import datetime
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import black, grey
from src.relatorios.listas.lista_atualizada import create_pdf_buffer
from src.relatorios.gerar_pdf import salvar_e_abrir_pdf
from src.core.config import get_image_path

# Cache global para imagens e estilos
_IMAGE_CACHE = {}
_STYLE_CACHE = {}

def _get_cached_image(path, width, height):
    """Retorna uma imagem em cache para evitar recarregamento."""
    key = (path, width, height)
    if key not in _IMAGE_CACHE:
        _IMAGE_CACHE[key] = Image(path, width=width, height=height)
    return _IMAGE_CACHE[key]

def _get_cached_style(name, **kwargs):
    """Retorna um estilo em cache para evitar recriação."""
    key = (name, tuple(sorted(kwargs.items())))
    if key not in _STYLE_CACHE:
        _STYLE_CACHE[key] = ParagraphStyle(name=name, **kwargs)
    return _STYLE_CACHE[key]


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

    figura_superior = str(get_image_path('logosemed.png'))
    figura_inferior = str(get_image_path('logopaco.png'))

    doc, buffer = create_pdf_buffer()
    elements = []

    # Cabeçalho com cache
    img_inf = _get_cached_image(figura_inferior, 3 * inch, 0.7 * inch)
    header_style = _get_cached_style('Header', fontSize=12, alignment=1)
    
    data = [
        [img_inf],
        [Paragraph('<br/>'.join(cabecalho), header_style)]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 0.5 * inch))

    titulo_style = _get_cached_style('Titulo', fontSize=14, alignment=1)
    elements.append(Paragraph('<b>TERMO DE RESPONSABILIDADE E CONFIDENCIALIDADE</b>', titulo_style))
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

    corpo_style = _get_cached_style('Corpo', fontSize=11, leading=16, alignment=4)
    elements.append(Paragraph(corpo, corpo_style))
    elements.append(Spacer(1, 0.4 * inch))

    # Rodapé com data
    hoje = datetime.datetime.now().strftime('%d/%m/%Y')
    data_style = _get_cached_style('Data', fontSize=11, alignment=2)
    elements.append(Paragraph(f"Paco do Lumiar/MA, {hoje}.", data_style))
    elements.append(Spacer(1, 0.8 * inch))

    # Linhas de assinatura usando estilos em cache
    ass_titulo_style = _get_cached_style('AssTitulo', fontSize=10, alignment=1)
    linha_style = _get_cached_style('Linha', fontSize=10, alignment=1)
    ass_nome_style = _get_cached_style('AssNome', fontSize=10, alignment=1)
    ass_doc_style = _get_cached_style('AssDoc', fontSize=9, alignment=1)
    
    assinatura_data = [
        [Paragraph('<b>ESCOLA</b>', ass_titulo_style),
         Paragraph('<b>EMPRESA</b>', ass_titulo_style)],
        [Paragraph('__________________________________________', linha_style),
         Paragraph('__________________________________________', linha_style)],
        [Paragraph(nome_escola, ass_nome_style),
         Paragraph(razao_social_empresa, ass_nome_style)],
        [Paragraph(f'CNPJ: {cnpj_escola}', ass_doc_style),
         Paragraph(f'CNPJ: {cnpj_empresa}', ass_doc_style)]
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


