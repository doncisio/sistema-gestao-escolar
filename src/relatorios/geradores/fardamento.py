from src.core.config_logs import get_logger
from src.core.config import get_image_path
logger = get_logger(__name__)
import io
import os
import pandas as pd
import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, grey
from src.relatorios.listas.lista_atualizada import fetch_student_data
from src.relatorios.gerar_pdf import salvar_e_abrir_pdf
try:
    from src.services.report_service import _find_image_in_repo
except Exception:
    _find_image_in_repo = None

def adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior, tamanho_fonte=12):
    """Adiciona o cabeçalho padrão ao documento."""
    data = [
        [Image(figura_superior, width=2 * inch, height=0.8 * inch),
         Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=tamanho_fonte, alignment=1)),
         Image(figura_inferior, width=2 * inch, height=0.8 * inch)]
    ]
    table = Table(data, colWidths=[2.2 * inch, 4 * inch, 2.2 * inch])
    table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    elements.append(table)

def gerar_lista_fardamento():
    """Gera um único PDF com a lista de alunos para receberem o fardamento pelos pais/responsáveis, agrupados por turma."""
    ano_letivo = 2025
    dados_aluno = fetch_student_data(ano_letivo)
    
    if not dados_aluno:
        logger.info("Nenhum dado de aluno encontrado.")
        return
        
    df = pd.DataFrame(dados_aluno)
    # Definir caminhos das imagens usando get_image_path
    figura_superior = str(get_image_path('logopacosemed.png'))
    figura_inferior = str(get_image_path('logopacobranco.png'))
    
    cabecalho = [
        "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>EM PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 06.003.636/0001-73</b>"
    ]
    
    # Criar um único buffer e documento para todas as turmas
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=18,
        topMargin=18,
        bottomMargin=18
    )
    elements = []
    
    # Adicionar capa inicial (apenas uma vez)
    adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior)
    elements.append(Spacer(1, 2 * inch))
    elements.append(Paragraph("<b>LISTA DE ALUNOS <br/> E <br/>FARDAMENTOS RECEBIDOS</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1, leading=24)))
    elements.append(Spacer(1, 2.5 * inch))
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
    elements.append(PageBreak())
    
    # Iterar por todas as turmas e adicionar ao mesmo documento
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        # Extrair nome do professor e filtrar alunos ativos
        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Sem Professor'
        turma_df = turma_df[turma_df['SITUAÇÃO'] == 'Ativo']
        
        # Adicionar cabeçalho da página
        adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior, 11)
        elements.append(Spacer(1, 0.125 * inch))
        
        # Adicionar descrição
        elements.append(Paragraph("Lista de alunos para receberem o fardamento escolar pelos pais/responsáveis", 
                                ParagraphStyle(name='Descricao', fontSize=12, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Adicionar título da turma
        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", 
                                ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Criar tabela de presença com larguras ajustadas para modo paisagem
        # Cabeçalho com duas linhas para sub-colunas
        data = [
            ['Nº', 'Nome', 'TAMANHO/PONTUAÇÃO', '', 'Assinatura do Responsável', 'Parentesco'],
            ['', '', 'Fardamento', 'Calçados', '', '']
        ]
        for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
            nome = row['NOME DO ALUNO']
            # Garantir que valores adicionados à tabela sejam strings
            nome_str = str(nome) if pd.notnull(nome) else ""
            fardamento = ''
            calcados = ''
            assinatura = ''
            parentesco = ''
            data.append([str(row_num), nome_str, fardamento, calcados, assinatura, parentesco])
        
        # Ajustando as larguras das colunas para melhor aproveitamento do espaço horizontal
        table = Table(data, colWidths=[0.4 * inch, 3.2 * inch, 1 * inch, 1 * inch, 3.2 * inch, 1.2 * inch])
        table.setStyle(TableStyle([
            # Cabeçalho principal (linha 0)
            ('BACKGROUND', (0, 0), (-1, 0), white),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Sub-cabeçalho (linha 1)
            ('BACKGROUND', (0, 1), (-1, 1), white),
            ('TEXTCOLOR', (0, 1), (-1, 1), black),
            ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
            
            # Mesclar células do cabeçalho principal
            ('SPAN', (0, 0), (0, 1)),  # Nº
            ('SPAN', (1, 0), (1, 1)),  # Nome
            ('SPAN', (2, 0), (3, 0)),  # TAMANHO/PONTUAÇÃO
            ('SPAN', (4, 0), (4, 1)),  # Assinatura do Responsável
            ('SPAN', (5, 0), (5, 1)),  # Parentesco
            
            # Dados (a partir da linha 2)
            ('ALIGN', (1, 2), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 2), (-1, -1), 10),
            ('BACKGROUND', (0, 2), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        elements.append(table)
        elements.append(PageBreak())
    
    # Construir o documento uma única vez com todas as turmas
    doc.build(elements)
    buffer.seek(0)
    
    # Usar o util central de PDF para salvar/mover/upload via API
    try:
        from src.relatorios.gerar_pdf import salvar_e_abrir_pdf as _salvar_helper
    except Exception:
        _salvar_helper = None

    saved_path = None
    try:
        if _salvar_helper:
            try:
                saved_path = _salvar_helper(buffer)
            except Exception:
                saved_path = None

        if not saved_path:
            import tempfile
            from src.utils.utilitarios.gerenciador_documentos import salvar_documento_sistema
            from src.utils.utilitarios.tipos_documentos import TIPO_LISTA_FARDAMENTO

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            tmp.write(buffer.read())
            tmp.close()
            
            saved_path = salvar_documento_sistema(
                caminho_arquivo=tmp.name,
                tipo_documento=TIPO_LISTA_FARDAMENTO,
                nome_original=f"Lista_Fardamento_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    except Exception as e:
        logger.exception(f"Erro ao salvar PDF de fardamento: {e}")
            
    logger.info("Lista de fardamento gerada com sucesso!")
