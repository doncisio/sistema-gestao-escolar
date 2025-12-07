"""
Gerador de Folha de Ponto em PDF
Cria fichas de ponto para funcionários com cabeçalho personalizado e tabela de registro
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
import calendar
from conexao import conectar_bd
from config_logs import get_logger
import os

logger = get_logger(__name__)


class FolhaPontoGenerator:
    """Gerador de Folha de Ponto em PDF"""
    
    def __init__(self, header_font_size: int = 28):
        self.pagesize = A4
        self.width, self.height = A4
        self.margin = 1.5 * cm
        # Tamanho da fonte do texto central do cabeçalho (configurável)
        self.header_font_size = header_font_size
        
    def _buscar_dados_funcionario(self, funcionario_id):
        """
        Busca os dados do funcionário no banco de dados
        
        Args:
            funcionario_id: ID do funcionário
            
        Returns:
            dict: Dados do funcionário ou None se não encontrado
        """
        conn = conectar_bd()
        if not conn:
            logger.error("Não foi possível conectar ao banco de dados")
            return None
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Buscar dados do funcionário
            query = """
                SELECT 
                    f.id,
                    f.nome,
                    f.matricula,
                    f.cargo,
                    f.data_admissao,
                    f.carga_horaria,
                    f.telefone,
                    f.email,
                    e.nome as escola_nome
                FROM Funcionarios f
                LEFT JOIN escolas e ON f.escola_id = e.id
                WHERE f.id = %s
            """
            
            cursor.execute(query, (funcionario_id,))
            funcionario = cursor.fetchone()
            
            if not funcionario:
                logger.warning(f"Funcionário com ID {funcionario_id} não encontrado")
                return None
                
            # Formatar data de admissão
            if funcionario.get('data_admissao'):
                funcionario['data_admissao_formatada'] = funcionario['data_admissao'].strftime('%d/%m/%Y')
            else:
                funcionario['data_admissao_formatada'] = 'Não informada'
                
            # Valores padrão para campos nulos
            funcionario['matricula'] = funcionario.get('matricula') or 'Não informada'
            funcionario['carga_horaria'] = funcionario.get('carga_horaria') or 'Não informada'
            funcionario['telefone'] = funcionario.get('telefone') or 'Não informado'
            funcionario['email'] = funcionario.get('email') or 'Não informado'
            funcionario['escola_nome'] = funcionario.get('escola_nome') or 'Não informada'
            
            return funcionario
            
        except Exception as e:
            logger.exception(f"Erro ao buscar dados do funcionário: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def _desenhar_borda(self, c):
        """
        Desenha a borda decorativa ao redor da página
        
        Args:
            c: Canvas do PDF
        """
        borda_path = r"imagens\borda.png"
        
        if os.path.exists(borda_path):
            try:
                # Desenhar a borda cobrindo toda a página
                c.drawImage(
                    borda_path, 
                    0, 0,  # Posição x, y (canto inferior esquerdo)
                    width=self.width, 
                    height=self.height,
                    preserveAspectRatio=False,  # Esticar para cobrir toda a página
                    mask='auto'
                )
            except Exception as e:
                logger.warning(f"Erro ao desenhar borda: {e}")
        else:
            logger.warning(f"Imagem de borda não encontrada: {borda_path}")
    
    def _desenhar_cabecalho(self, c, y_position, texto_central="FOLHA DE PONTO", periodo_text: str = None, info_lines: list = None):
        """
        Desenha o cabeçalho com duas imagens nas extremidades e texto no centro
        
        Args:
            c: Canvas do PDF
            y_position: Posição Y inicial
            texto_central: Texto a ser exibido no centro
            
        Returns:
            float: Nova posição Y após o cabeçalho
        """
        # Caminhos das imagens
        img_esquerda_path = r"imagens\logopacosemed.png"
        img_direita_path = r"imagens\pacologo.png"
        
        # Dimensões das imagens (aumentadas para melhor visibilidade)
        img_width = 4 * cm
        img_height = 2.67 * cm
        
        # Posições
        x_esquerda = self.margin
        x_direita = self.width - self.margin - img_width
        y_img = y_position - img_height
        
        # Desenhar imagens se existirem
        if os.path.exists(img_esquerda_path):
            c.drawImage(img_esquerda_path, x_esquerda, y_img, 
                       width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
        else:
            logger.warning(f"Imagem não encontrada: {img_esquerda_path}")
            
        if os.path.exists(img_direita_path):
            c.drawImage(img_direita_path, x_direita, y_img, 
                       width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
        else:
            logger.warning(f"Imagem não encontrada: {img_direita_path}")
        
        # Texto central (usa tamanho configurável)
        fs = int(self.header_font_size)
        c.setFont("Helvetica-Bold", fs)
        texto_width = c.stringWidth(texto_central, "Helvetica-Bold", fs)
        x_texto = (self.width - texto_width) / 2
        # Posicionar o texto em relação ao centro vertical das imagens,
        # mas levemente abaixo para evitar que fique muito alto.
        # y_position corresponde ao topo das imagens; o centro vertical das imagens
        # é y_position - img_height/2. Ajustamos para ficar alguns pontos abaixo.
        y_texto = y_position - img_height / 2 + 8
        c.drawString(x_texto, y_texto, texto_central)

        # Desenhar rótulo "Período" abaixo do texto central e acima do retângulo
        # Aumentado conforme solicitado
        periodo_label_font = 12
        c.setFont("Helvetica-Bold", periodo_label_font)
        periodo_label = "Período"
        y_label = y_texto - (fs * 0.8)
        c.setFillColor(colors.black)
        c.drawCentredString(self.width / 2, y_label, periodo_label)

        # Desenhar período se fornecido (retângulo com texto dentro)
        if periodo_text:
            # Retângulo arredondado claro com o período centralizado
            font_period = 9
            c.setFont("Helvetica", font_period)
            text_w = c.stringWidth(periodo_text, "Helvetica", font_period)
            # aumentar padding horizontal para alargar o retângulo
            pad_x = 12
            # aumentar a largura mínima do retângulo e a altura
            rect_w = max(text_w + pad_x * 2, 6.5 * cm)
            rect_h = 0.8 * cm
            x_rect = (self.width - rect_w) / 2
            # posicionar o retângulo logo abaixo do label "Período"
            y_rect = y_label - rect_h - 4
            # cor cinza um pouco mais escura
            c.setFillColor(colors.HexColor("#e0e0e0"))
            try:
                c.roundRect(x_rect, y_rect, rect_w, rect_h, 6, stroke=0, fill=1)
            except Exception:
                c.rect(x_rect, y_rect, rect_w, rect_h, stroke=0, fill=1)
            # desenhar o texto do período centralizado dentro do retângulo
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", font_period)
            c.drawCentredString(self.width / 2, y_rect + rect_h / 2 - (font_period / 4), periodo_text)
            y_text_below = y_rect - 6
        else:
            y_text_below = y_label - 6

        # Desenhar linhas de informação centralizadas abaixo do período
        if info_lines:
            line_font = 9
            spacing = 12
            y_current = y_text_below
            for text, bold in info_lines:
                if bold:
                    c.setFont("Helvetica-Bold", line_font)
                else:
                    c.setFont("Helvetica", line_font)
                c.setFillColor(colors.black)
                c.drawCentredString(self.width / 2, y_current - spacing, text)
                y_current -= spacing

        # Retornar nova posição Y (abaixo do cabeçalho e informações)
        return y_img - 0.5 * cm
    
    def _criar_secao_dados_funcionario(self, funcionario):
        """
        Cria a seção com dados do funcionário
        
        Args:
            funcionario: Dicionário com dados do funcionário
            
        Returns:
            list: Lista de elementos (Paragraph, Table, etc.)
        """
        elementos = []
        styles = getSampleStyleSheet()
        
        # # Estilo para título da seção
        # style_titulo = ParagraphStyle(
        #     'TituloSecao',
        #     parent=styles['Heading2'],
        #     fontSize=12,
        #     textColor=colors.HexColor('#003452'),
        #     spaceAfter=2,
        #     spaceBefore=6
        # )
        
        # Estilo para dados
        style_dados = ParagraphStyle(
            'Dados',
            parent=styles['Normal'],
            fontSize=10,
            leading=14
        )

        elementos.append(Spacer(1, 0.2 * cm))

        # Título da seção
        elementos.append(Paragraph("<b>Dados do Empregado (a):</b>", style_dados))
        
        # Nome
        elementos.append(Paragraph(f"<b>Nome:</b> {funcionario['nome']}", style_dados))
        
        # Matrícula e Admissão
        texto_mat_adm = f"<b>Matrícula:</b> {funcionario['matricula']} &nbsp;&nbsp;&nbsp;&nbsp; <b>Admissão:</b> {funcionario['data_admissao_formatada']}"
        elementos.append(Paragraph(texto_mat_adm, style_dados))
        
        # Função e Carga Horária
        texto_func_carga = f"<b>Função:</b> {funcionario['cargo']} &nbsp;&nbsp;&nbsp;&nbsp; <b>Carga horária:</b> {funcionario['carga_horaria']}"
        elementos.append(Paragraph(texto_func_carga, style_dados))
        
        # Lotação
        elementos.append(Paragraph(f"<b>Lotação:</b> {funcionario['escola_nome']}", style_dados))
        
        # Contato e E-mail
        texto_contato = f"<b>Contato:</b> {funcionario['telefone']} &nbsp;&nbsp;&nbsp;&nbsp; <b>E-mail:</b> {funcionario['email']}"
        elementos.append(Paragraph(texto_contato, style_dados))
        
        elementos.append(Spacer(1, 0.5 * cm))
        
        return elementos
    
    def _criar_tabela_ponto(self, mes, ano):
        """
        Cria a tabela de registro de ponto para o mês especificado
        
        Args:
            mes: Mês (1-12)
            ano: Ano (ex: 2025)
            
        Returns:
            Table: Tabela formatada
        """
        # Cabeçalho da tabela (texto simples será convertido em Paragraphs para quebra automática)
        header_texts = [
            'Dia',
            'Entrada',
            'Início do Intervalo',
            'Fim do Intervalo',
            'Saída',
            'Hora Extra',
            'Assinatura'
        ]
        
        # Obter número de dias no mês
        _, num_dias = calendar.monthrange(ano, mes)
        
        # Definir larguras das colunas
        colWidths = [
            1.2*cm,  # Dia (reduzido)
            1.8*cm,  # Entrada
            1.8*cm,  # Início do Intervalo
            1.8*cm,  # Fim do Intervalo
            1.8*cm,  # Saída
            1.8*cm,  # Hora Extra
            8*cm   # Assinatura (aumentada)
        ]

        # Definir tamanho da fonte do cabeçalho e estilo para Paragraph
        header_font = 9
        styles = getSampleStyleSheet()
        header_style = ParagraphStyle(
            'table_header',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=header_font,
            alignment=1,  # center
            leading=header_font * 1.2
        )

        # Criar Paragraphs para o cabeçalho e calcular altura máxima necessária
        header_paragraphs = []
        header_heights = []
        for text, width in zip(header_texts, colWidths):
            para = Paragraph(text, header_style)
            w, h = para.wrap(width, 0)
            header_paragraphs.append(para)
            header_heights.append(h)

        header_row_height = max(max(header_heights), 0.45 * cm)

        # Montar dados da tabela com os Paragraphs no cabeçalho
        dados_tabela = [header_paragraphs]

        # Adicionar linhas para cada dia do mês (numeradas com dois dígitos)
        for dia in range(1, num_dias + 1):
            dados_tabela.append([
                f"{dia:02d}",  # Apenas o número do dia, com zero à esquerda
                '',  # Entrada
                '',  # Início do Intervalo
                '',  # Fim do Intervalo
                '',  # Saída
                '',  # Hora Extra
                ''   # Assinatura
            ])

        # Criar tabela com larguras ajustadas e alturas (cabeçalho dinâmico)
        tabela = Table(dados_tabela, colWidths=colWidths, rowHeights=[header_row_height] + [0.49*cm] * num_dias)
        
        # Estilo da tabela
        estilo = TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e0e0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), header_font),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            
            # Corpo da tabela
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Coluna Dia centralizada
            ('ALIGN', (1, 1), (-1, -1), 'LEFT'),  # Demais colunas alinhadas à esquerda
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            
            # Linhas alternadas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ])
        
        tabela.setStyle(estilo)
        
        return tabela
    
    def _adicionar_rodape(self, c, y_position):
        """
        Adiciona rodapé com assinaturas
        
        Args:
            c: Canvas do PDF
            y_position: Posição Y para o rodapé
        """
        # Linha para assinatura do empregado
        y = y_position - 2 * cm
        x_centro = self.width / 2
        
        c.setFont("Helvetica", 9)

        # Linha de assinatura empregado
        linha_width = 6 * cm
        # Aumentar o espaçamento horizontal entre as assinaturas
        horizontal_gap = 2.5 * cm
        x_linha_empregado = x_centro - linha_width - horizontal_gap
        c.line(x_linha_empregado, y, x_linha_empregado + linha_width, y)
        texto_empregado = "Assinatura do Empregado (a)"
        texto_width = c.stringWidth(texto_empregado, "Helvetica", 9)
        c.drawString(x_linha_empregado + (linha_width - texto_width) / 2, y - 20, texto_empregado)

        # Linha de assinatura responsável
        x_linha_responsavel = x_centro + horizontal_gap
        c.line(x_linha_responsavel, y, x_linha_responsavel + linha_width, y)
        texto_responsavel = "Assinatura do Gestor(a)"
        texto_width = c.stringWidth(texto_responsavel, "Helvetica", 9)
        c.drawString(x_linha_responsavel + (linha_width - texto_width) / 2, y - 20, texto_responsavel)
        
        # Texto centralizado entre as assinaturas
        try:
            c.setFont("Helvetica", 8)
            url_text = "www.pacodolumiar.ma.gov.br"
            # Posicionar um pouco abaixo da linha de assinatura, mas acima dos rótulos
            y_url = y - 4
            c.setFillColor(colors.black)
            c.drawCentredString(x_centro, y_url, url_text)
        except Exception:
            # Não interromper caso haja problema ao desenhar o texto
            pass
    
    def gerar_folha_ponto(self, funcionario_id, mes=None, ano=None, output_path=None):
        """
        Gera a folha de ponto em PDF para um funcionário
        
        Args:
            funcionario_id: ID do funcionário
            mes: Mês (1-12). Se None, usa o mês atual
            ano: Ano. Se None, usa o ano atual
            output_path: Caminho do arquivo de saída. Se None, gera automaticamente
            
        Returns:
            str: Caminho do arquivo gerado ou None se houver erro
        """
        # Usar data atual se não especificado
        if mes is None or ano is None:
            hoje = datetime.now()
            mes = mes or hoje.month
            ano = ano or hoje.year
        
        # Buscar dados do funcionário
        funcionario = self._buscar_dados_funcionario(funcionario_id)
        if not funcionario:
            logger.error(f"Não foi possível buscar dados do funcionário ID {funcionario_id}")
            return None
        
        # Definir caminho de saída
        if output_path is None:
            # Criar diretório de saída se não existir
            output_dir = "Modelos"
            os.makedirs(output_dir, exist_ok=True)
            
            # Nome do arquivo
            nome_arquivo = f"folha_ponto_{funcionario['nome'].replace(' ', '_')}_{mes:02d}_{ano}.pdf"
            output_path = os.path.join(output_dir, nome_arquivo)
        
        try:
            # Criar documento PDF com SimpleDocTemplate
            # Aumentar topMargin para empurrar todo o conteúdo para baixo
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.pagesize,
                leftMargin=self.margin,
                rightMargin=self.margin,
                topMargin=6*cm,
                bottomMargin=2.5*cm
            )
            
            # Lista de elementos do documento
            story = []
            
            # Adicionar espaçamento mínimo para o cabeçalho
            story.append(Spacer(1, 0.3*cm))
            
            # Adicionar dados do funcionário
            story.extend(self._criar_secao_dados_funcionario(funcionario))
            
            # Adicionar tabela de ponto
            tabela = self._criar_tabela_ponto(mes, ano)
            story.append(tabela)
            
            # Adicionar espaçamento mínimo antes do rodapé
            story.append(Spacer(1, 0.5*cm))
            
            # Função para desenhar cabeçalho e rodapé em cada página
            nome_mes = calendar.month_name[mes].upper()
            texto_cabecalho = f"Folha de Ponto"
            
            # Preparar texto do período e linhas de informação
            start_day = 1
            end_day = calendar.monthrange(ano, mes)[1]
            periodo_text = f"{start_day:02d} à {end_day:02d}/{mes:02d}/{ano}"
            info_lines = [
                ("Prefeitura de Paço do Lumiar", True),
                ("06.003.636/0001-73", False),
                ("Centro Administrativo - Avenida 13, S/N - Maiobão - Paço do Lumiar", False),
                ("Secretaria Municipal de Educação", True),
                ("19.931.246/0001-05", False),
                ("Avenida 09, 15, quadra 76 - Maiobão -Paço do Lumiar", False),
            ]

            def primeira_pagina(canvas_obj, doc_obj):
                canvas_obj.saveState()
                # Desenhar borda primeiro (fundo)
                self._desenhar_borda(canvas_obj)
                # Subir o cabeçalho na página (mais próximo do topo)
                y_cabecalho = self.height - 1*cm
                self._desenhar_cabecalho(canvas_obj, y_cabecalho, texto_cabecalho, periodo_text, info_lines)
                # Desenhar rodapé (subido)
                self._adicionar_rodape(canvas_obj, 4*cm)
                canvas_obj.restoreState()
            
            def paginas_seguintes(canvas_obj, doc_obj):
                canvas_obj.saveState()
                # Desenhar borda primeiro (fundo)
                self._desenhar_borda(canvas_obj)
                # Subir o cabeçalho na página (mais próximo do topo)
                y_cabecalho = self.height - 1*cm
                self._desenhar_cabecalho(canvas_obj, y_cabecalho, texto_cabecalho, periodo_text, info_lines)
                # Desenhar rodapé (subido)
                self._adicionar_rodape(canvas_obj, 4*cm)
                canvas_obj.restoreState()
            
            # Construir PDF
            doc.build(story, onFirstPage=primeira_pagina, onLaterPages=paginas_seguintes)
            
            logger.info(f"Folha de ponto gerada com sucesso: {output_path}")
            return output_path
            
        except Exception as e:
            logger.exception(f"Erro ao gerar folha de ponto: {e}")
            return None


def gerar_folha_ponto_funcionario(funcionario_id, mes=None, ano=None, output_path=None, header_font_size: int = None):
    """
    Função auxiliar para gerar folha de ponto
    
    Args:
        funcionario_id: ID do funcionário
        mes: Mês (1-12)
        ano: Ano
        output_path: Caminho do arquivo de saída
        
    Returns:
        str: Caminho do arquivo gerado ou None se houver erro
    """
    # Permitir sobrescrever o tamanho da fonte do cabeçalho
    if header_font_size is not None:
        gerador = FolhaPontoGenerator(header_font_size=header_font_size)
    else:
        gerador = FolhaPontoGenerator()
    return gerador.gerar_folha_ponto(funcionario_id, mes, ano, output_path)


def gerar_folhas_para_escola(escola_id, mes=None, ano=None, output_path=None, header_font_size: int = None):
    """
    Gera um único arquivo PDF contendo as folhas de ponto de todos os funcionários
    pertencentes à escola especificada por `escola_id`.

    Args:
        escola_id: ID da escola (campo `escola_id` na tabela Funcionarios)
        mes: mês (1-12). Se None, usa o mês atual.
        ano: ano. Se None, usa o ano atual.
        output_path: caminho do arquivo de saída. Se None, gera em `Modelos/Folhas_Escola_<escola_id>_<mes>_<ano>.pdf`.
        header_font_size: tamanho da fonte do cabeçalho (opcional).

    Returns:
        str: caminho do arquivo gerado ou None em caso de erro.
    """
    # usar data atual se não informado
    if mes is None or ano is None:
        hoje = datetime.now()
        mes = mes or hoje.month
        ano = ano or hoje.year

    conn = conectar_bd()
    if not conn:
        logger.error("Não foi possível conectar ao banco de dados para listar funcionários")
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT f.id, f.nome
            FROM Funcionarios f
            WHERE f.escola_id = %s
            ORDER BY f.nome
        """
        cursor.execute(query, (escola_id,))
        funcionarios = cursor.fetchall()
    except Exception as e:
        logger.exception(f"Erro ao buscar funcionários da escola {escola_id}: {e}")
        return None
    finally:
        conn.close()

    if not funcionarios:
        logger.warning(f"Nenhum funcionário encontrado para a escola_id={escola_id}")
        return None

    # criar gerador com font configurada
    gerador = FolhaPontoGenerator(header_font_size=header_font_size or 24)

    # caminho de saída padrão
    if output_path is None:
        os.makedirs('Modelos', exist_ok=True)
        nome_arquivo = f"Folhas_Escola_{escola_id}_{mes:02d}_{ano}.pdf"
        output_path = os.path.join('Modelos', nome_arquivo)

    try:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=gerador.pagesize,
            leftMargin=gerador.margin,
            rightMargin=gerador.margin,
            topMargin=6*cm,
            bottomMargin=2.5*cm
        )

        story = []

        for idx, f in enumerate(funcionarios):
            # garantir espaçamento similar à geração individual
            story.append(Spacer(1, 0.3*cm))
            funcionario = gerador._buscar_dados_funcionario(f['id'])
            if not funcionario:
                continue

            # seção de dados + tabela
            story.extend(gerador._criar_secao_dados_funcionario(funcionario))
            story.append(gerador._criar_tabela_ponto(mes, ano))

            # adicionar quebra de página entre funcionários, exceto após o último
            if idx < len(funcionarios) - 1:
                story.append(PageBreak())

        # callbacks de página (reusar os mesmos do gerador)
        nome_mes = calendar.month_name[mes].upper()
        texto_cabecalho = f"Folha de Ponto"
        start_day = 1
        end_day = calendar.monthrange(ano, mes)[1]
        periodo_text = f"{start_day:02d} à {end_day:02d}/{mes:02d}/{ano}"
        info_lines = [
            ("Prefeitura de Paço do Lumiar", True),
            ("06.003.636/0001-73", False),
            ("Centro Administrativo - Avenida 13, S/N - Maiobão - Paço do Lumiar", False),
            ("Secretaria Municipal de Educação", True),
            ("19.931.246/0001-05", False),
            ("Avenida 09, 15, quadra 76 - Maiobão -Paço do Lumiar", False),
        ]

        def primeira_pagina(canvas_obj, doc_obj):
            canvas_obj.saveState()
            gerador._desenhar_borda(canvas_obj)
            y_cabecalho = gerador.height - 1*cm
            gerador._desenhar_cabecalho(canvas_obj, y_cabecalho, texto_cabecalho, periodo_text, info_lines)
            gerador._adicionar_rodape(canvas_obj, 4.5*cm)
            canvas_obj.restoreState()

        def paginas_seguintes(canvas_obj, doc_obj):
            canvas_obj.saveState()
            gerador._desenhar_borda(canvas_obj)
            y_cabecalho = gerador.height - 1*cm
            gerador._desenhar_cabecalho(canvas_obj, y_cabecalho, texto_cabecalho, periodo_text, info_lines)
            gerador._adicionar_rodape(canvas_obj, 4.5*cm)
            canvas_obj.restoreState()

        doc.build(story, onFirstPage=primeira_pagina, onLaterPages=paginas_seguintes)
        logger.info(f"Folhas geradas para escola_id={escola_id}: {output_path}")
        return output_path

    except Exception as e:
        logger.exception(f"Erro ao gerar folhas para escola {escola_id}: {e}")
        return None


if __name__ == "__main__":
    # Exemplo de uso
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python gerar_folha_ponto.py <funcionario_id> [mes] [ano]")
        print("Exemplo: python gerar_folha_ponto.py 1 12 2025")
        sys.exit(1)
    
    funcionario_id = int(sys.argv[1])
    mes = int(sys.argv[2]) if len(sys.argv) > 2 else None
    ano = int(sys.argv[3]) if len(sys.argv) > 3 else None
    header_font_size = int(sys.argv[4]) if len(sys.argv) > 4 else None

    resultado = gerar_folha_ponto_funcionario(funcionario_id, mes, ano, None, header_font_size)
    
    if resultado:
        print(f"Folha de ponto gerada com sucesso: {resultado}")
    else:
        print("Erro ao gerar folha de ponto")
        sys.exit(1)
