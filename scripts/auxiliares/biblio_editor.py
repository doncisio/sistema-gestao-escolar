import io
from reportlab.platypus import Paragraph, Image, Table, TableStyle, SimpleDocTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import black
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

def adicionar_quebra_linha(texto):
    return Paragraph('<br/>'.join(list(texto.upper())), ParagraphStyle(
        'header', 
        fontName='Helvetica-Bold', 
        fontSize=10, 
        textColor=black, 
        alignment=1))  # Centralizado

def quebra_linha(texto):
    linhas = texto.upper().split('\n')
    return Paragraph('<br/>'.join(linhas), ParagraphStyle(
        'header', 
        fontName='Helvetica-Bold', 
        fontSize=10, 
        textColor=black, 
        alignment=1))  # Centralizado

def criar_cabecalho_pdf(figura_superior, figura_inferior, cabecalho):
    data = [
        [Image(figura_superior, width=0.8 * inch, height=0.8 * inch),
         Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1)),
         Image(figura_inferior, width=1.2 * inch, height=0.8 * inch)]
    ]
    table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])
    table.setStyle(table_style)
    return table
def arredondar_personalizado(n):
    """
    Arredonda a nota e retorna multiplicada por 10 (formato inteiro)
    
    A nota no sistema está multiplicada por 10 (ex: 76.7 representa 7.67)
    Divide por 10, arredonda e multiplica por 10 novamente para exibir como inteiro
    
    Exemplos:
        81.6 / 10 = 8.16 -> 8.2 -> 82
        73.3 / 10 = 7.33 -> 7.3 -> 73
        76.7 / 10 = 7.67 -> 7.7 -> 77
        73.5 / 10 = 7.35 -> 7.4 -> 74
    
    Args:
        n: Valor numérico da nota (multiplicado por 10)
        
    Returns:
        int: Nota arredondada e multiplicada por 10
    """
    from decimal import Decimal

    # A função recebe a nota multiplicada por 10 (ex: 63.7 representa 6.37)
    # Vamos dividir por 10 para trabalhar com o valor real
    nota_real = Decimal(str(n)) / Decimal('10')

    # Separar parte inteira e a fração
    parte_inteira = int(nota_real // 1)
    fracao = nota_real - Decimal(parte_inteira)

    # Limiares escolhidos com base no exemplo fornecido:
    # - fracao < 0.3125  -> arredonda para baixo (x.00)
    # - 0.3125 <= fracao < 0.8125 -> arredonda para x.5
    # - fracao >= 0.8125 -> arredonda para cima (x+1.0)
    t1 = Decimal('0.3125')
    t2 = Decimal('0.8125')

    if fracao < t1:
        resultado = Decimal(parte_inteira)
    elif fracao < t2:
        resultado = Decimal(parte_inteira) + Decimal('0.5')
    else:
        resultado = Decimal(parte_inteira + 1)

    # Retornar no formato do sistema (multiplicado por 10, inteiro)
    return int((resultado * Decimal('10')).to_integral_value())

def arredondamento_ata(n):
    """
    Realiza arredondamento específico para atas:
    - Se o número for divisível por 5, retorna o mesmo valor
    - Caso contrário, divide por 10, arredonda e multiplica por 10
    """
    if n % 5 == 0:
        return n
    else:
        return round(n / 10) * 10

def quebra_linha_menor(texto):
# Divide o texto em linhas e aplica a formatação desejada
    linhas = texto.upper().split('\n')
    return Paragraph('<br/>'.join(linhas), ParagraphStyle(
        'header', 
        fontName='Helvetica-Bold', 
        fontSize=9,
        alignment=1))  # Centralizado

def definir_coordenador(turma_df):
    """Determina o coordenador com base nos IDs das séries."""
    coordenador = ''
    if 'ID_SERIE' in turma_df.columns:
        turma_df_15 = turma_df[turma_df['ID_SERIE'] <= 7]
        turma_df_69 = turma_df[turma_df['ID_SERIE'] > 7]

        if not turma_df_15.empty:
            coordenador = 'Laise Laine'
        if not turma_df_69.empty:
            coordenador = 'Allanne Leão'
    return coordenador
def formatar_telefone(telefone):
    """Formata um número de telefone para o formato (98)XXXXX-XXXX."""
    if not telefone:
        return "Telefone não informado"
    telefone = str(telefone)
    if "." in telefone:
        telefone = telefone.split(".")[0]
    telefone = telefone.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
    if len(telefone) < 10:
        telefone = "98" + telefone
    if len(telefone) < 10:
        return "Telefone Inválido"
    if len(telefone) == 10:
        return f"({telefone[:2]}){telefone[2:6]}-{telefone[6:]}"
    elif len(telefone) == 11:
        return f"({telefone[:2]}){telefone[2:7]}-{telefone[7:]}"
    else:
        return "Telefone Inválido"
def reduzir_nome(nome_completo):
    """
    Reduz um nome completo para as duas primeiras partes (nome e sobrenome principal).

    Args:
        nome_completo (str): O nome completo da pessoa.

    Returns:
        str: O nome reduzido, consistindo no nome e sobrenome principal.
    """
    nomes = nome_completo.split()
    if len(nomes) >= 2:
        return f"{nomes[0]} {nomes[1]}"  # Retorna o primeiro nome e o sobrenome principal
    elif len(nomes) == 1:
        return nomes[0]  # Se houver apenas um nome, retorna ele mesmo
    else:
        return ""  # Se o nome estiver vazio, retorna uma string vazia
    
def create_pdf_buffer(pagesize=letter):
    buffer = io.BytesIO()
    left_margin = 36
    right_margin = 18
    top_margin = 10
    bottom_margin = 18

    doc = SimpleDocTemplate(
        buffer, 
        pagesize=pagesize,
        leftMargin=left_margin, 
        rightMargin=right_margin, 
        topMargin=top_margin, 
        bottomMargin=bottom_margin
    )
    return doc, buffer

# Importar get_nome_mes do módulo utils.dates (já tem suporte a uppercase)
from src.utils.dates import get_nome_mes

def formatar_cpf(cpf):
    """Formata um CPF para o formato 000.000.000-00."""
    if not cpf:
        return ""
    cpf = str(cpf)
    cpf = cpf.replace(" ", "").replace(".", "").replace("-", "")
    
    # Adiciona zeros à esquerda se o CPF tiver menos de 11 dígitos
    cpf = cpf.zfill(11)
    
    if len(cpf) != 11:
        return ""
    
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"