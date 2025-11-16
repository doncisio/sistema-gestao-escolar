from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import tempfile
import os
import platform
from reportlab.lib.colors import HexColor
from GerenciadorDocumentosSistema import GerenciadorDocumentosSistema
import datetime
from config_logs import get_logger

logger = get_logger(__name__)

# Constante para o tipo de documento
TIPO_DIARIO_CLASSE_CAPA = "Capa do Diário de Classe"

def create_custom_pdf():
    try:
        gerenciador = GerenciadorDocumentosSistema()
        nome_documento = f"Capa do Diário de Classe - {datetime.datetime.now().strftime('%Y')}"
        
        # Caminho da imagem de fundo
        image_path = "retangulooval.png"  # Atualize para o caminho da imagem de fundo
        # Dimensões da página A4
        width, height = A4
        arquivo_temp = None

        # Criar um arquivo PDF temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            output_path = temp_file.name
            arquivo_temp = output_path

            # Criar o canvas
            c = canvas.Canvas(output_path, pagesize=A4)

            # Desenhar a imagem de fundo
            draw_background_image(c, image_path, width, height)

            # Adicionar cabeçalho e títulos
            add_header(c)

            # Desenhar as caixas sobre a imagem de fundo na primeira página
            draw_boxes(c)

            # Finalizar a primeira página
            c.showPage()

            # Salvar o PDF
            c.save()

        if arquivo_temp:
            gerenciador.salvar_documento(
                tipo_documento=TIPO_DIARIO_CLASSE_CAPA,
                nome_documento=nome_documento,
                arquivo_origem=arquivo_temp
            )

            # Abrir o PDF no programa padrão do sistema operacional
            open_pdf(arquivo_temp)

    except Exception as e:
        logger.exception("Erro ao gerar a capa do diário de classe: %s", e)
        raise

def draw_background_image(c, image_path, width, height):
    """Desenha a imagem de fundo na página."""
    image_margin = 0.5 * inch
    image_width = width - 2 * image_margin
    image_height = height - 2 * image_margin
    c.drawImage(image_path, image_margin, image_margin, image_width, image_height)

def add_header(c):
    """Adiciona o cabeçalho e títulos ao PDF."""
    cabecalho = [
        "<b>PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR</b>",
        "<b>SECRETARIA MUNICIPAL DE EDUCAÇÃO</b>",
    ]
    
    style_header = ParagraphStyle(name="Header", fontSize=16, alignment=1, textColor=colors.black, leading=24)
    
    # Criar e renderizar a tabela do cabeçalho
    render_table(c, cabecalho, style_header, 2 * inch)

    titulo1 = ["<b>DIÁRIO DE CLASSE</b>"]
    titulo2 = ["<b>ANOS INICIAIS<br/> 1º AO 5º ANO</b>"]
    
    style_title1 = ParagraphStyle(name="Title1", fontSize=50, alignment=1, textColor=HexColor('#00008B'))
    style_title2 = ParagraphStyle(name="Title2", fontSize=40, alignment=1, textColor=HexColor('#00008B'), leading=40)

    # Criar e renderizar as tabelas dos títulos
    render_table(c, titulo1, style_title1, 3.75 * inch)
    render_table(c, titulo2, style_title2, 5.5 * inch)

def render_table(c, data_list, style, y_offset):
    """Renderiza uma tabela no canvas."""
    data = [[Paragraph('<br/>'.join(data_list), style)]]
    
    table = Table(data, colWidths=[8 * inch])
    table.setStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black)
    ])

    # Calcular posição para centralizar horizontalmente
    table_width, table_height = table.wrap(0, 0)
    
    x_position = (A4[0] - table_width) / 2  # Centralizar horizontalmente
    y_position = A4[1] - y_offset  # Ajustar verticalmente

    # Renderizar a tabela no canvas
    table.drawOn(c, x_position, y_position)

def draw_boxes(c):
    """Desenha as caixas com fundo branco e bordas azul escuro na primeira página."""
    
    large_box_width = 6.5 * inch   # Largura das caixas grandes (Escola e Componente Curricular)
    
    large_box_height = 0.5 * inch   # Altura das caixas grandes e pequenas
    
    small_box_width = 1.5 * inch     # Largura das caixas pequenas (Ano Letivo, Série, Turma e Turno)
    
    # Calcular espaço entre as caixas pequenas
    space_between_boxes = (large_box_width - (small_box_width * 4)) / 3
    central = 1 * inch + (large_box_width - small_box_width)/2

    # Posições das caixas na página

    # Primeira linha: "Escola"
    positions = [
        (1 * inch , A4[1] - 6.5 * inch),   # Caixa "Escola"
    ]
    
    # Segunda linha: "Ano Letivo", "Série", "Turma", "Turno"
    positions += [
        (1 * inch , A4[1] - 7.5 * inch),   # Caixa "Ano Letivo"
        (1 * inch + small_box_width + space_between_boxes , A4[1] - 7.5 * inch),   # Caixa "Série"
        (1 * inch + small_box_width*2 + space_between_boxes*2 , A4[1] - 7.5 * inch),   # Caixa "Turma"
        (1 * inch + small_box_width*3 + space_between_boxes*3 , A4[1] - 7.5 * inch)   # Caixa "Turno"
    ]
    
    # Terceira linha: "Componente Curricular"
    positions.append((1 * inch , A4[1] - 8.5 * inch))   # Caixa "Componente Curricular"

    # Quarta linha: "Professor"
    positions.append((1 * inch , A4[1] - 9.5 * inch))   # Caixa "Professor"

    # Última caixa: "Ano" (mesmo tamanho que as menores)
    positions.append((central, A4[1] - 10.5 * inch))   # Caixa "Ano"

    labels = ["Escola", "Ano Letivo", "Série", "Turma", "Turno", "Componente Curricular", "Professor", "Ano"]

    for idx in range(len(positions)):
        x_pos,y_pos = positions[idx]
        label = labels[idx]

        if idx == 0 or idx == 5 or idx == 6:  # Primeira linha e linhas com caixas grandes ("Componente Curricular" e "Professor")
            box_width = large_box_width
            box_height = large_box_height
        else:                     # Segunda linha com caixas pequenas
            box_width = small_box_width
            box_height = large_box_height

        # Desenhar caixa com borda azul escuro e fundo branco
        c.setStrokeColor(HexColor('#00008B'))   # Cor da borda azul escuro
        c.setFillColor(colors.white)             # Cor de fundo branco

        c.roundRect(x_pos , y_pos , box_width , box_height , radius=10 , fill=True)   # Desenha a caixa com cantos arredondados

        # Adicionar texto na caixa centralizado
        text_x_pos = x_pos + box_width / 2      # Centraliza horizontalmente na caixa 
        text_y_pos = - large_box_height + y_pos + box_height / 2     # Centraliza verticalmente na caixa 
        # Definir a fonte como Helvetica, tamanho 12 e em negrito
        c.setFont("Helvetica-Bold", 14)          # Aumenta a fonte e define como negrito

        c.setFillColor(colors.black)             # Cor do texto preta 
        c.drawCentredString(text_x_pos , text_y_pos , label)   # Desenha o texto

def open_pdf(file_path):
    """Abre o arquivo PDF no programa padrão do sistema operacional."""
    
    if platform.system() == 'Windows':
        os.startfile(file_path)
    elif platform.system() == 'Darwin':  # macOS
        os.system(f'open "{file_path}"')
    else:  # Linux e outros sistemas Unix-like
        os.system(f'xdg-open "{file_path}"')


create_custom_pdf()