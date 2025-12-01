from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import os

def create_custom_pdf(output_path, image_path):
    # Dimensões da página A4
    width, height = A4

    # Criar o canvas
    c = canvas.Canvas(output_path, pagesize=A4)

    # Desenhar a imagem de fundo
    image_margin = 0.5 * inch
    image_width = width - 2 * image_margin
    image_height = height - 2 * image_margin
    c.drawImage(image_path, image_margin, image_margin, image_width, image_height)
    figura_superior = "imagens/logosemed.png"  # Atualize para o caminho correto
    figura_inferior = "imagens/logopaco.png"  # Atualize para o caminho correto
    # Adicionar o cabeçalho sobre a imagem
    cabecalho = [
        "ESTADO DO MARANHÃO",
        "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>UEB PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 06.003.636/0001-73</b>"
    ]

    # Configurar estilo do texto
    style = ParagraphStyle(name="Header", fontSize=12, alignment=1, textColor=colors.black)

    # Criar tabela
    data = [
        [Image(figura_superior, width=1 * inch, height=1 * inch),
         Paragraph('<br/>'.join(cabecalho), style),
         Image(figura_inferior, width=1.5 * inch, height=1 * inch)]
    ]
    table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
    table.setStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black)
    ])

    # Calcular posição para centralizar horizontalmente
    table_width, table_height = table.wrap(0, 0)  # Obter dimensões da tabela
    x_position = (width - table_width) / 2  # Centralizar horizontalmente
    y_position = height - 2 * inch  # Ajustar verticalmente (deslocamento a partir do topo)

    # Renderizar a tabela no canvas
    table.drawOn(c, x_position, y_position)

    # Finalizar a primeira página
    c.showPage()

    # Páginas subsequentes
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, height - 1 * inch, "Página 2: Aqui começa o conteúdo textual.")
    c.showPage()
    c.drawString(1 * inch, height - 1 * inch, "Página 3: Continuando o texto do documento.")

    # Salvar o PDF
    c.save()

# Caminhos das imagens
image_path = "retangulooval.png"  # Atualize para o caminho da imagem de fundo
output_path = "documento.pdf"

create_custom_pdf(output_path, image_path)
