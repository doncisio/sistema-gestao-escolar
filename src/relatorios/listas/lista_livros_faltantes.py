"""
Gerador de PDF para Lista de Controle de Livros Faltantes por Turma

Gera relatório PDF com a quantidade de livros faltantes por disciplina
para cada turma do 1º ao 9º ano, com layouts diferenciados para
anos iniciais (1º ao 5º) e anos finais (6º ao 9º).
"""

import io
import os
import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, grey, lightgrey
from reportlab.lib import colors

from src.core.conexao import conectar_bd
from src.relatorios.gerar_pdf import salvar_e_abrir_pdf
from src.core.config import get_image_path, ANO_LETIVO_ATUAL
import logging

logger = logging.getLogger(__name__)


def create_pdf_buffer():
    """Cria buffer para o PDF em formato A4 retrato."""
    buffer = io.BytesIO()
    left_margin = 36
    right_margin = 36
    top_margin = 36
    bottom_margin = 36

    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        leftMargin=left_margin, 
        rightMargin=right_margin, 
        topMargin=top_margin, 
        bottomMargin=bottom_margin
    )
    return doc, buffer


def create_pdf_buffer_landscape():
    """Cria buffer para o PDF em formato A4 paisagem (para anos finais)."""
    buffer = io.BytesIO()
    left_margin = 36
    right_margin = 36
    top_margin = 36
    bottom_margin = 36

    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        leftMargin=left_margin, 
        rightMargin=right_margin, 
        topMargin=top_margin, 
        bottomMargin=bottom_margin
    )
    return doc, buffer


def add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior):
    """Adiciona página de capa ao PDF."""
    # Imagem inferior (logo)
    if figura_inferior and os.path.exists(figura_inferior):
        img_elem = Image(figura_inferior, width=3 * inch, height=0.7 * inch)
    else:
        img_elem = Spacer(1, 0.1 * inch)

    data = [
        [img_elem],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    
    table = Table(data, colWidths=[4.5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 2 * inch))
    
    # Título da capa
    capa_text = "<b>CONTROLE DE LIVROS FALTANTES<br/>POR TURMA E DISCIPLINA</b>"
    elements.append(Paragraph(capa_text, ParagraphStyle(name='Capa', fontSize=24, alignment=1, leading=30)))
    elements.append(Spacer(1, 4 * inch))
    elements.append(Paragraph(
        f"<b>{datetime.datetime.now().year}</b>",
        ParagraphStyle(name='Ano', fontSize=18, alignment=1)
    ))
    elements.append(PageBreak())


def add_turma_table(elements, turma_data, nome_serie, nome_turma, figura_inferior, cabecalho, disciplinas):
    """
    Adiciona tabela com livros faltantes para uma turma específica.
    
    Args:
        elements: Lista de elementos do PDF
        turma_data: Dicionário com {disciplina: {'quantidade': int, 'editora': str, 'colecao': str}}
        nome_serie: Nome da série (ex: "1º Ano")
        nome_turma: Nome da turma (ex: "A")
        figura_inferior: Caminho da imagem de rodapé
        cabecalho: Lista com linhas do cabeçalho
        disciplinas: Lista de disciplinas a exibir
    """
    # Cabeçalho com logo
    if figura_inferior and os.path.exists(figura_inferior):
        img_elem = Image(figura_inferior, width=3 * inch, height=0.7 * inch)
    else:
        img_elem = Spacer(1, 0.1 * inch)

    data = [
        [img_elem],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[4.5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 0.15 * inch))

    # Título da turma
    titulo = f"<b>{nome_serie} - Turma {nome_turma}</b>"
    elements.append(Paragraph(titulo, ParagraphStyle(name='Turma', fontSize=14, alignment=1, leading=18)))
    elements.append(Spacer(1, 0.15 * inch))

    # Criar tabela de livros faltantes
    # Cabeçalho da tabela
    table_data = [
        ['DISCIPLINA', 'QTD FALTANTE', 'EDITORA', 'COLEÇÃO']
    ]
    
    # Adicionar dados de cada disciplina
    total_faltantes = 0
    for disciplina in disciplinas:
        dados_disc = turma_data.get(disciplina, {'quantidade': 0, 'editora': '', 'colecao': ''})
        quantidade = dados_disc.get('quantidade', 0)
        editora = dados_disc.get('editora', '')
        colecao = dados_disc.get('colecao', '')
        total_faltantes += quantidade
        
        # Nome completo das disciplinas
        nomes_disciplinas = {
            'PRT': 'Português',
            'MTM': 'Matemática',
            'CNC': 'Ciências',
            'GEO/HIST': 'Geografia/História',
            'ART': 'Arte'
        }
        
        nome_completo = nomes_disciplinas.get(disciplina, disciplina)
        table_data.append([
            nome_completo, 
            str(quantidade),
            editora or '-',
            colecao or '-'
        ])
    
    # Linha de total (span nas colunas de editora/coleção)
    table_data.append(['TOTAL', str(total_faltantes), '', ''])
    
    # Criar tabela com colunas ajustadas para A4 retrato
    table = Table(table_data, colWidths=[1.5 * inch, 1.5 * inch, 1 * inch, 2.5 * inch])
    
    # Estilo da tabela
    table_style = TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Corpo da tabela
        ('BACKGROUND', (0, 1), (-1, -2), white),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),       # Disciplina à esquerda
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),     # Quantidade centralizada
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),       # Editora à esquerda
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),       # Coleção à esquerda
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 9),
        ('GRID', (0, 0), (-1, -2), 1, black),
        
        # Linha de total
        ('BACKGROUND', (0, -1), (-1, -1), lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('ALIGN', (0, -1), (0, -1), 'RIGHT'),
        ('ALIGN', (1, -1), (1, -1), 'CENTER'),
        ('GRID', (0, -1), (-1, -1), 2, black),
        ('SPAN', (2, -1), (3, -1)),  # Merge editora/coleção na linha total
    ])
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Espaço para observações
    elements.append(Spacer(1, 0.3 * inch))
    obs_style = ParagraphStyle(name='Obs', fontSize=9, alignment=0, leading=14)
    elements.append(Paragraph("<b>Observações:</b>", obs_style))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Linhas para observações manuscritas (ajustado para A4 retrato)
    for i in range(3):
        elements.append(Paragraph("_" * 85, obs_style))
        elements.append(Spacer(1, 0.1 * inch))
    
    elements.append(PageBreak())


def add_turma_table_anos_finais(elements, turma_data, nome_serie, nome_turma, figura_inferior, cabecalho, disciplinas):
    """
    Adiciona tabela com livros faltantes para uma turma dos anos finais (6º ao 9º ano).
    Layout em retrato, padronizado com os anos iniciais.
    
    Args:
        elements: Lista de elementos do PDF
        turma_data: Dicionário com {disciplina: {'quantidade': int, 'editora': str, 'colecao': str}}
        nome_serie: Nome da série (ex: "6º Ano")
        nome_turma: Nome da turma (ex: "A")
        figura_inferior: Caminho da imagem de rodapé
        cabecalho: Lista com linhas do cabeçalho
        disciplinas: Lista de disciplinas a exibir
    """
    # Cabeçalho com logo
    if figura_inferior and os.path.exists(figura_inferior):
        img_elem = Image(figura_inferior, width=3 * inch, height=0.7 * inch)
    else:
        img_elem = Spacer(1, 0.1 * inch)

    data = [
        [img_elem],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[4.5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 0.15 * inch))

    # Título da turma
    titulo = f"<b>{nome_serie} - Turma {nome_turma}</b>"
    elements.append(Paragraph(titulo, ParagraphStyle(name='Turma', fontSize=14, alignment=1, leading=18)))
    elements.append(Spacer(1, 0.15 * inch))

    # Criar tabela de livros faltantes (formato paisagem com mais colunas)
    # Cabeçalho da tabela
    table_data = [
        ['DISCIPLINA', 'QTD FALTANTE', 'EDITORA', 'COLEÇÃO']
    ]
    
    # Adicionar dados de cada disciplina
    total_faltantes = 0
    for disciplina in disciplinas:
        dados_disc = turma_data.get(disciplina, {'quantidade': 0, 'editora': '', 'colecao': ''})
        quantidade = dados_disc.get('quantidade', 0)
        editora = dados_disc.get('editora', '')
        colecao = dados_disc.get('colecao', '')
        total_faltantes += quantidade
        
        # Nome completo das disciplinas
        nomes_disciplinas = {
            'PRT': 'Português',
            'MTM': 'Matemática',
            'CNC': 'Ciências',
            'HST': 'História',
            'GEO': 'Geografia',
            'ING': 'Inglês',
            'ART': 'Arte'
        }
        
        nome_completo = nomes_disciplinas.get(disciplina, disciplina)
        table_data.append([
            nome_completo, 
            str(quantidade),
            editora or '-',
            colecao or '-'
        ])
    
    # Linha de total (span nas colunas de editora/coleção)
    table_data.append(['TOTAL', str(total_faltantes), '', ''])
    
    # Criar tabela com colunas ajustadas para A4 retrato
    table = Table(table_data, colWidths=[1.5 * inch, 1.5 * inch, 1 * inch, 2.5 * inch])
    
    # Estilo da tabela
    table_style = TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Corpo da tabela
        ('BACKGROUND', (0, 1), (-1, -2), white),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),       # Disciplina à esquerda
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),     # Quantidade centralizada
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),       # Editora à esquerda
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),       # Coleção à esquerda
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 9),
        ('GRID', (0, 0), (-1, -2), 1, black),
        
        # Linha de total
        ('BACKGROUND', (0, -1), (-1, -1), lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('ALIGN', (0, -1), (0, -1), 'RIGHT'),
        ('ALIGN', (1, -1), (1, -1), 'CENTER'),
        ('GRID', (0, -1), (-1, -1), 2, black),
        ('SPAN', (2, -1), (3, -1)),  # Merge editora/coleção na linha total
    ])
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Espaço para observações
    elements.append(Spacer(1, 0.3 * inch))
    obs_style = ParagraphStyle(name='Obs', fontSize=9, alignment=0, leading=14)
    elements.append(Paragraph("<b>Observações:</b>", obs_style))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Linhas para observações manuscritas (ajustado para A4 retrato)
    for i in range(3):
        elements.append(Paragraph("_" * 85, obs_style))
        elements.append(Spacer(1, 0.1 * inch))
    
    elements.append(PageBreak())


def gerar_pdf_livros_faltantes(ano_letivo=None):
    """
    Gera PDFs com controle de livros faltantes por turma.
    Cria dois PDFs separados: um para anos iniciais (1º ao 5º) e outro para anos finais (6º ao 9º).
    
    Args:
        ano_letivo: Ano letivo (usa o atual se não informado)
    """
    if ano_letivo is None:
        ano_letivo = ANO_LETIVO_ATUAL
        
    try:
        # Conectar ao banco
        conn = conectar_bd()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar ID do ano letivo
        cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = %s", (ano_letivo,))
        result = cursor.fetchone()
        if not result:
            logger.error(f"Ano letivo {ano_letivo} não encontrado")
            return
        ano_letivo_id = result['id']
        
        # Buscar séries do 1º ao 5º ano (anos iniciais)
        cursor.execute("""
            SELECT id, nome
            FROM series 
            WHERE id BETWEEN 3 AND 7
            ORDER BY id
        """)
        series_iniciais = cursor.fetchall()
        
        # Buscar séries do 6º ao 9º ano (anos finais)
        cursor.execute("""
            SELECT id, nome
            FROM series 
            WHERE id BETWEEN 8 AND 11
            ORDER BY id
        """)
        series_finais = cursor.fetchall()
        
        # Definir disciplinas para cada tipo
        disciplinas_iniciais = ['PRT', 'MTM', 'CNC', 'GEO/HIST', 'ART']
        disciplinas_finais = ['PRT', 'MTM', 'CNC', 'HST', 'GEO', 'ING', 'ART']
        
        # Configurar cabeçalho e imagens
        cabecalho = [
            "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
            "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
            "<b>INEP: 21008485</b>",
            "<b>CNPJ: 01.394.462/0001-01</b>"
        ]
        
        figura_superior = str(get_image_path('logosemed.png'))
        figura_inferior = str(get_image_path('logopaco.png'))
        
        # Processar Anos Iniciais (1º ao 5º ano) - Formato Retrato
        if series_iniciais:
            tem_dados_iniciais = _gerar_pdf_anos_iniciais(
                cursor, ano_letivo_id, series_iniciais, disciplinas_iniciais,
                cabecalho, figura_superior, figura_inferior, ano_letivo
            )
        else:
            tem_dados_iniciais = False
        
        # Processar Anos Finais (6º ao 9º ano) - Formato Paisagem
        if series_finais:
            tem_dados_finais = _gerar_pdf_anos_finais(
                cursor, ano_letivo_id, series_finais, disciplinas_finais,
                cabecalho, figura_superior, figura_inferior, ano_letivo
            )
        else:
            tem_dados_finais = False
        
        # Verificar se gerou algum PDF
        if not tem_dados_iniciais and not tem_dados_finais:
            logger.warning("Nenhum dado de livros faltantes cadastrado!")
            from tkinter import messagebox
            messagebox.showwarning(
                "Aviso",
                "Nenhum dado de livros faltantes foi cadastrado ainda!\n\n"
                "Por favor, cadastre os dados primeiro através da opção:\n"
                "Listas > Gerenciar Livros Faltantes"
            )
        
        logger.info(f"PDFs de livros faltantes gerados com sucesso para o ano {ano_letivo}")
        
    except Exception as e:
        logger.error(f"Erro ao gerar PDF de livros faltantes: {e}")
        from tkinter import messagebox
        messagebox.showerror("Erro", f"Erro ao gerar PDF: {e}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _gerar_pdf_anos_iniciais(cursor, ano_letivo_id, series, disciplinas, cabecalho, figura_superior, figura_inferior, ano_letivo):
    """
    Gera PDF para anos iniciais (1º ao 5º ano) em formato retrato.
    
    Returns:
        bool: True se gerou com sucesso, False se não havia dados
    """
    # Criar documento PDF (retrato)
    doc, buffer = create_pdf_buffer()
    elements = []
    
    # Adicionar capa
    add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior)
    
    tem_dados = False
    
    # Para cada série, buscar dados de todas as turmas
    for serie in series:
        serie_id = serie['id']
        serie_nome = serie['nome']
        
        # Buscar turmas existentes para esta série
        query = """
            SELECT DISTINCT turma 
            FROM livros_faltantes 
            WHERE ano_letivo_id = %s AND serie_id = %s
            ORDER BY turma
        """
        cursor.execute(query, (ano_letivo_id, serie_id))
        turmas = cursor.fetchall()
        
        # Se não houver dados, pular esta série
        if not turmas:
            logger.info(f"Nenhum dado de livros faltantes para {serie_nome}")
            continue
        
        tem_dados = True
        
        # Para cada turma da série
        for turma_row in turmas:
            turma = turma_row['turma']
            
            # Definir nome de exibição da turma (se vazio, mostrar "Única")
            turma_display = 'Única' if not turma or turma.strip() == '' else turma
            
            # Buscar dados de livros faltantes
            query = """
                SELECT disciplina, quantidade_faltante, editora, colecao
                FROM livros_faltantes
                WHERE ano_letivo_id = %s 
                AND serie_id = %s 
                AND turma = %s
            """
            cursor.execute(query, (ano_letivo_id, serie_id, turma))
            resultados = cursor.fetchall()
            
            # Organizar dados em dicionário estruturado
            turma_data = {}
            for row in resultados:
                turma_data[row['disciplina']] = {
                    'quantidade': row['quantidade_faltante'],
                    'editora': row.get('editora', ''),
                    'colecao': row.get('colecao', '')
                }
            
            # Adicionar tabela para esta turma
            add_turma_table(
                elements=elements,
                turma_data=turma_data,
                nome_serie=serie_nome,
                nome_turma=turma_display,
                figura_inferior=figura_inferior,
                cabecalho=cabecalho,
                disciplinas=disciplinas
            )
    
    # Se tem dados, gerar PDF
    if tem_dados:
        doc.build(elements)
        buffer.seek(0)
        
        # Salvar e abrir com nome específico
        from tkinter import filedialog
        arquivo_padrao = f"Livros_Faltantes_Anos_Iniciais_{ano_letivo}.pdf"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=arquivo_padrao,
            title="Salvar Lista de Livros Faltantes - Anos Iniciais"
        )
        
        if filepath:
            with open(filepath, 'wb') as f:
                f.write(buffer.getvalue())
            
            # Abrir o arquivo
            import subprocess
            subprocess.Popen([filepath], shell=True)
            logger.info(f"PDF de anos iniciais salvo em: {filepath}")
    
    return tem_dados


def _gerar_pdf_anos_finais(cursor, ano_letivo_id, series, disciplinas, cabecalho, figura_superior, figura_inferior, ano_letivo):
    """
    Gera PDF para anos finais (6º ao 9º ano) em formato retrato.
    
    Returns:
        bool: True se gerou com sucesso, False se não havia dados
    """
    # Criar documento PDF (retrato)
    doc, buffer = create_pdf_buffer()
    elements = []
    
    # Adicionar capa
    add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior)
    
    tem_dados = False
    
    # Para cada série, buscar dados de todas as turmas
    for serie in series:
        serie_id = serie['id']
        serie_nome = serie['nome']
        
        # Buscar turmas existentes para esta série
        query = """
            SELECT DISTINCT turma 
            FROM livros_faltantes 
            WHERE ano_letivo_id = %s AND serie_id = %s
            ORDER BY turma
        """
        cursor.execute(query, (ano_letivo_id, serie_id))
        turmas = cursor.fetchall()
        
        # Se não houver dados, pular esta série
        if not turmas:
            logger.info(f"Nenhum dado de livros faltantes para {serie_nome}")
            continue
        
        tem_dados = True
        
        # Para cada turma da série
        for turma_row in turmas:
            turma = turma_row['turma']
            
            # Definir nome de exibição da turma (se vazio, mostrar "Única")
            turma_display = 'Única' if not turma or turma.strip() == '' else turma
            
            # Buscar dados de livros faltantes
            query = """
                SELECT disciplina, quantidade_faltante, editora, colecao
                FROM livros_faltantes
                WHERE ano_letivo_id = %s 
                AND serie_id = %s 
                AND turma = %s
            """
            cursor.execute(query, (ano_letivo_id, serie_id, turma))
            resultados = cursor.fetchall()
            
            # Organizar dados em dicionário estruturado
            turma_data = {}
            for row in resultados:
                turma_data[row['disciplina']] = {
                    'quantidade': row['quantidade_faltante'],
                    'editora': row.get('editora', ''),
                    'colecao': row.get('colecao', '')
                }
            
            # Adicionar tabela para esta turma (versão anos finais)
            add_turma_table_anos_finais(
                elements=elements,
                turma_data=turma_data,
                nome_serie=serie_nome,
                nome_turma=turma_display,
                figura_inferior=figura_inferior,
                cabecalho=cabecalho,
                disciplinas=disciplinas
            )
    
    # Se tem dados, gerar PDF
    if tem_dados:
        doc.build(elements)
        buffer.seek(0)
        
        # Salvar e abrir com nome específico
        from tkinter import filedialog
        arquivo_padrao = f"Livros_Faltantes_Anos_Finais_{ano_letivo}.pdf"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=arquivo_padrao,
            title="Salvar Lista de Livros Faltantes - Anos Finais"
        )
        
        if filepath:
            with open(filepath, 'wb') as f:
                f.write(buffer.getvalue())
            
            # Abrir o arquivo
            import subprocess
            subprocess.Popen([filepath], shell=True)
            logger.info(f"PDF de anos finais salvo em: {filepath}")
    
    return tem_dados


if __name__ == "__main__":
    # Para testes
    gerar_pdf_livros_faltantes()
