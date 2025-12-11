"""
Gerador de Certificado de Conclusão do Ensino Fundamental em PDF
Busca dados do aluno no banco de dados e gera o certificado formatado
"""

import os
from datetime import datetime, date
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
import textwrap
from conexao import conectar_bd
from config_logs import get_logger

logger = get_logger(__name__)


def carregar_imagem_local(nome_arquivo):
    """Carrega uma imagem do diretório local de imagens"""
    try:
        caminho = os.path.join("imagens", nome_arquivo)
        if os.path.exists(caminho):
            return ImageReader(caminho)
        else:
            logger.warning(f"Imagem não encontrada: {caminho}")
            return None
    except Exception as e:
        logger.error(f"Erro ao carregar imagem {nome_arquivo}: {e}")
        return None


def buscar_dados_aluno(aluno_id):
    """
    Busca os dados do aluno no banco de dados
    
    Args:
        aluno_id: ID do aluno
        
    Returns:
        dict: Dados do aluno ou None se não encontrado
    """
    conn = None
    cursor = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor(dictionary=True)
        
        # Query para buscar dados do aluno e responsáveis
        query = """
        SELECT 
            a.id,
            a.sexo as sexo,
            a.nome,
            a.data_nascimento,
            a.local_nascimento,
            a.UF_nascimento,
            e.nome as nome_escola,
            m.status as status_matricula,
            al.ano_letivo as ano_letivo,
            (SELECT GROUP_CONCAT(r.nome SEPARATOR ' e ') 
             FROM responsaveisalunos ra
             JOIN responsaveis r ON ra.responsavel_id = r.id
             WHERE ra.aluno_id = a.id
             LIMIT 2) as nomes_responsaveis
        FROM alunos a
        LEFT JOIN matriculas m ON a.id = m.aluno_id
        LEFT JOIN anosletivos al ON m.ano_letivo_id = al.id
        LEFT JOIN turmas t ON m.turma_id = t.id
        LEFT JOIN escolas e ON t.escola_id = e.id OR e.id = a.escola_id
        WHERE a.id = %s
        ORDER BY al.ano_letivo DESC
        LIMIT 1
        """
        
        cursor.execute(query, (aluno_id,))
        resultado = cursor.fetchone()
        
        if resultado:
            logger.info(f"Dados do aluno {aluno_id} encontrados")
            return resultado
        else:
            logger.warning(f"Aluno {aluno_id} não encontrado")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao buscar dados do aluno: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def formatar_data(data):
    """Formata uma data para o padrão brasileiro"""
    if not data:
        return ''

    # Se for string, tentar vários formatos comuns
    if isinstance(data, str):
        for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y'):
            try:
                dt = datetime.strptime(data, fmt)
                return dt.strftime('%d/%m/%Y')
            except Exception:
                continue
        # Se não conseguiu parsear, retornar a string original
        return data

    # Aceitar datetime e date
    if isinstance(data, (datetime, date)):
        return data.strftime('%d/%m/%Y')

    return str(data)


def formatar_data_extenso(data=None):
    """Formata uma data por extenso"""
    if data is None:
        data = datetime.now()
    elif isinstance(data, str):
        try:
            data = datetime.strptime(data, '%Y-%m-%d')
        except:
            data = datetime.now()
    
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    
    return f"{data.day:02d} de {meses[data.month - 1]} de {data.year}"


def gerar_certificado_pdf(aluno_id, arquivo_saida=None):
    """
    Gera o certificado em PDF para um aluno
    
    Args:
        aluno_id: ID do aluno
        arquivo_saida: Nome do arquivo de saída (opcional)
        
    Returns:
        str: Caminho do arquivo gerado ou None em caso de erro
    """
    # Buscar dados do aluno
    dados = buscar_dados_aluno(aluno_id)
    
    if not dados:
        logger.error(f"Não foi possível gerar certificado: aluno {aluno_id} não encontrado")
        return None
    
    # Definir nome do arquivo de saída
    if arquivo_saida is None:
        pasta_certificados = "certificados"
        os.makedirs(pasta_certificados, exist_ok=True)
        nome_arquivo = f"certificado_aluno_{aluno_id}.pdf"
        arquivo_saida = os.path.join(pasta_certificados, nome_arquivo)
    
    try:
        # Registrar fontes (usando fontes padrão do sistema)
        # Century Gothic pode não estar disponível, usar alternativas
        try:
            pdfmetrics.registerFont(TTFont('CenturyGothic', 'GOTHIC.TTF'))
            pdfmetrics.registerFont(TTFont('CenturyGothic-Bold', 'GOTHICB.TTF'))
            fonte_titulo = 'CenturyGothic-Bold'
            fonte_texto = 'CenturyGothic'
        except:
            logger.info("Fonte Century Gothic não encontrada, usando Helvetica")
            fonte_titulo = 'Helvetica-Bold'
            fonte_texto = 'Helvetica'
        
        # Criar o PDF em formato paisagem
        largura, altura = landscape(A4)
        c = canvas.Canvas(arquivo_saida, pagesize=landscape(A4))
        
        # Carregar e adicionar imagem de fundo
        bg_image = carregar_imagem_local("fcertificado3.png")
        if bg_image:
            # Forçar a imagem de fundo a preencher toda a página A4
            # evitando bordas deixadas pela preservação de proporção
            c.drawImage(bg_image, 0, 0, width=largura, height=altura, preserveAspectRatio=False, mask='auto')
        
        # Definir margens com bordas respeitadas
        margem_esquerda = 75
        margem_direita = 75
        margem_superior = 70
        margem_inferior = 70
        largura_util = largura - margem_esquerda - margem_direita
        
        # Posição Y inicial (do topo com margem)
        y = altura - margem_superior
        
        # Adicionar brasões/logos (carregando localmente)
        # Logo esquerda
        logo_esq = carregar_imagem_local("logo_prefeitura.png")
        if logo_esq:
            c.drawImage(logo_esq, margem_esquerda, y - 80, width=90, height=90, preserveAspectRatio=True, mask='auto')
        
        # Logo direita
        logo_dir = carregar_imagem_local("Daco_5738580.png")
        if logo_dir:
            c.drawImage(logo_dir, largura - margem_direita - 90, y - 80, width=90, height=90, preserveAspectRatio=True, mask='auto')
        
        # Cabeçalho
        
        # Cabeçalho
        c.setFont(fonte_texto, 13)
        c.drawCentredString(largura / 2, y - 15, "ESTADO DO MARANHÃO")
        c.drawCentredString(largura / 2, y - 32, "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR")
        c.drawCentredString(largura / 2, y - 49, "SECRETARIA MUNICIPAL DE EDUCAÇÃO")
        
        y -= 100
        
        # Título CERTIFICADO
        c.setFont(fonte_titulo, 28)
        c.drawCentredString(largura / 2, y-30, "CERTIFICADO")
        
        y -= 50
        
        # Preparar o texto
        escola = dados.get('nome_escola', 'EM PROFª NADIR NASCIMENTO MORAES')
        nome_aluno = dados.get('nome', '').upper()
        nomes_responsaveis = dados.get('nomes_responsaveis', '')
        
        # Separar responsáveis (formato: "Nome1 e Nome2")
        if nomes_responsaveis:
            partes = nomes_responsaveis.split(' e ')
            nome_pai = partes[0].upper() if len(partes) > 0 else ''
            nome_mae = partes[1].upper() if len(partes) > 1 else ''
        else:
            nome_pai = ''
            nome_mae = ''
        
        data_nasc = formatar_data(dados.get('data_nascimento', ''))
        municipio = dados.get('local_nascimento', 'PAÇO DO LUMIAR').upper()
        uf = (dados.get('UF_nascimento') or 'MA').upper()

        # Mapear sigla UF para nome completo do estado
        uf_map = {
            'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
            'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
            'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
            'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
            'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
            'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
            'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
        }
        uf_full = uf_map.get(uf, uf)
        
        # Ajustar gênero conforme campo 'sexo' (M/F)
        sexo_aluno = (dados.get('sexo') or '').upper()
        if sexo_aluno == 'F':
            aluno_label = 'a Aluna'
            filho_label = 'filha'
            nascido_label = 'nascida'
        else:
            aluno_label = 'o Aluno'
            filho_label = 'filho'
            nascido_label = 'nascido'

        # Criar texto completo justificado usando Paragraph
        texto_completo = textwrap.dedent(f"""
            A {escola} no uso de suas atribuições legais, confere o presente
            Certificado de Conclusão do Ensino Fundamental para {aluno_label}
            <b>{nome_aluno}</b>, {filho_label} de {nome_pai} e de {nome_mae},
            {nascido_label} em {data_nasc} no município de {municipio} do
            {('Distrito Federal' if uf_full == 'Distrito Federal' else 'Estado do ' + uf_full)} por ter concluído no ano de 2025. Reconhecido pela Resolução Nº 19/2023-CME de 07/05/2024, do Conselho Municipal de Educação.
        """).strip()
        
        # Criar estilo para texto justificado
        styles = getSampleStyleSheet()
        estilo_justificado = ParagraphStyle(
            'Justificado',
            parent=styles['Normal'],
            fontSize=15,
            leading=22,
            alignment=TA_JUSTIFY,
            fontName=fonte_texto,
            spaceBefore=0,
            spaceAfter=0,
            leftIndent=0,
            rightIndent=0
        )
        
        # Criar parágrafo justificado
        paragrafo = Paragraph(texto_completo, estilo_justificado)
        
        # Calcular largura e altura disponível para o parágrafo
        largura_paragrafo = largura_util
        altura_disponivel = 150
        
        # Desenhar o parágrafo
        w, h = paragrafo.wrap(largura_paragrafo, altura_disponivel)
        paragrafo.drawOn(c, margem_esquerda, y - h)
        
        y -= h + 40
        
        # Data por extenso
        data_atual = formatar_data_extenso()
        c.setFont(fonte_texto, 13)
        texto_data = f"PAÇO DO LUMIAR - MA, {data_atual}."
        c.drawRightString(largura - margem_direita, y, texto_data)
        
        # Verificar se há espaço suficiente para assinaturas
        y -= 60
        if y < margem_inferior + 60:
            y = margem_inferior + 60
        
        # Linhas para assinaturas (centralizadas e espaçadas)
        linha_y = y
        espacamento_total = largura_util
        largura_assinatura = 220
        espaco_entre = (espacamento_total - (2 * largura_assinatura)) / 3
        
        pos_assinatura1 = margem_esquerda + espaco_entre
        pos_assinatura2 = margem_esquerda + espaco_entre + largura_assinatura + espaco_entre
        
        # Desenhar linhas de assinatura
        c.line(pos_assinatura1, linha_y, pos_assinatura1 + largura_assinatura, linha_y)
        c.line(pos_assinatura2, linha_y, pos_assinatura2 + largura_assinatura, linha_y)
        
        # Texto das assinaturas (já desenhado acima, espaço reservado)
        c.setFont(fonte_texto, 10)
        c.drawCentredString(pos_assinatura1 + largura_assinatura/2, linha_y - 18, "SECRETÁRIO(A) MUNICIPAL DE EDUCAÇÃO")
        c.drawCentredString(pos_assinatura2 + largura_assinatura/2, linha_y - 18, "GESTOR ESCOLAR")
        
        # Finalizar o PDF
        c.save()
        
        logger.info(f"Certificado gerado com sucesso: {arquivo_saida}")
        print(f"✓ Certificado gerado: {arquivo_saida}")
        return arquivo_saida
        
    except Exception as e:
        logger.error(f"Erro ao gerar certificado PDF: {e}")
        print(f"✗ Erro ao gerar certificado: {e}")
        return None


def main():
    """Função principal para teste"""
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python gerar_certificado_pdf.py <aluno_id> [arquivo_saida.pdf]")
        print("Exemplo: python gerar_certificado_pdf.py 235500")
        sys.exit(1)
    
    aluno_id = sys.argv[1]
    arquivo_saida = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Gerando certificado para aluno ID: {aluno_id}")
    resultado = gerar_certificado_pdf(aluno_id, arquivo_saida)
    
    if resultado:
        print(f"Certificado salvo em: {resultado}")
        sys.exit(0)
    else:
        print("Falha ao gerar certificado")
        sys.exit(1)


if __name__ == "__main__":
    main()
