import io
import os
import pandas as pd
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, grey
from gerarPDF import salvar_e_abrir_pdf, create_pdf_buffer_letter
from Lista_atualizada import fetch_student_data
from typing import Any
from config import get_image_path
from config_logs import get_logger

logger = get_logger(__name__)

# Cache global para imagens e estilos
_IMAGE_CACHE = {}
_STYLE_CACHE = {}

def _get_cached_image(path, width, height):
    """Retorna uma imagem em cache para evitar recarregamento."""
    key = (path, width, height)
    if key not in _IMAGE_CACHE:
        try:
            if path and os.path.exists(path):
                _IMAGE_CACHE[key] = Image(path, width=width, height=height)
            else:
                _IMAGE_CACHE[key] = Spacer(width, height)
        except Exception as e:
            logger.warning("Não foi possível carregar imagem '%s': %s", path, e)
            _IMAGE_CACHE[key] = Spacer(width, height)
    return _IMAGE_CACHE[key]

def _get_cached_style(name, **kwargs):
    """Retorna um estilo em cache para evitar recriação."""
    key = (name, tuple(sorted(kwargs.items())))
    if key not in _STYLE_CACHE:
        _STYLE_CACHE[key] = ParagraphStyle(name=name, **kwargs)
    return _STYLE_CACHE[key]

def lista_reuniao():
    ano_letivo = 2025
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        return

    df = pd.DataFrame(dados_aluno)
    # print(df[['NOME_SERIE', 'NOME_TURMA', 'TURNO']].isnull().sum())

    # Informações do cabeçalho
    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    # Criar o documento PDF
    doc, buffer = create_pdf_buffer_letter()
    elements = []

    # Caminhos das figuras usando get_image_path
    figura_superior_path = str(get_image_path('logosemed.png'))
    figura_inferior_path = str(get_image_path('logopaco.jpg'))

    # Debug: logar caminhos resolvidos para as imagens
    logger.info("DEBUG imagens - figura_superior_path=%s figura_inferior_path=%s", figura_superior_path, figura_inferior_path)

    # Carregar imagens em cache
    img_sup = _get_cached_image(figura_superior_path, 1 * inch, 1 * inch)
    img_inf = _get_cached_image(figura_inferior_path, 1.5 * inch, 1 * inch)
    header_style = _get_cached_style('Header', fontSize=12, alignment=1)
    capa_style = _get_cached_style('Capa', fontSize=24, alignment=1)
    ano_style = _get_cached_style('Ano', fontSize=18, alignment=1)
    turma_style = _get_cached_style('TurmaTitulo', fontSize=12, alignment=1)
    pauta_style = _get_cached_style('PautaTitulo', fontSize=14, alignment=1)
    item_style = _get_cached_style('PautaItem', fontSize=11, leftIndent=20)

    # Adicionar a capa
    data = [
        [img_sup,
         Paragraph('<br/>'.join(cabecalho), header_style),
         img_inf]
    ]
    table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 3.3 * inch))
    elements.append(Paragraph("<b>LISTA PARA REUNIÃO</b>", capa_style))
    elements.append(Spacer(1, 4 * inch))
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ano_style))
    elements.append(PageBreak())

    # Função para formatar os números de telefone
    def formatar_telefone(telefone):
        return f"{telefone[:5]}-{telefone[5:]}"

    # Lista de itens da pauta
    pauta_items = [
        "Atividades sequenciais do Projeto",
        "Atividades do projeto como atividades avaliadas 2º período",
        "Culminância do Projeto: cada professor(a) deverá levar seu subtema já definido e a proposta metodológica de apresentação",
        "Entrega de nota do 2º período",
        "Encerramento do Período dia 30/06, segunda-feira",
        "Primeira semana de AGOSTO"
    ]

    # Agrupar os dados por nome_serie, nome_turma e turno
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        # Extraindo o nome do professor da turma
        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Sem Professor'
        
        # Filtrar apenas os alunos com a situação "Ativo"
        turma_df = turma_df[turma_df['SITUAÇÃO'] == 'Ativo']

        # Adicionar o cabeçalho antes de cada tabela
        data = [
            [img_sup,
             Paragraph('<br/>'.join(cabecalho), _get_cached_style('Header', fontSize=11, alignment=1)),
             img_inf]
        ]
        table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
        table_style = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ])
        table.setStyle(table_style)
        elements.append(table)

        elements.append(Spacer(1, 0.125 * inch))

        # Adicionar o título da turma
        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", turma_style))
        elements.append(Spacer(1, 0.1 * inch))

        # Adicionar a pauta da reunião
        elements.append(Paragraph("<b>PAUTA DA REUNIÃO</b>", pauta_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        for item in pauta_items:
            elements.append(Paragraph(f"• {item}", item_style))
            elements.append(Spacer(1, 0.1 * inch))
        
        elements.append(Spacer(1, 0.2 * inch))

        # Criar a tabela para a turma
        data: list[list[Any]] = [['Nº', 'Nome', 'Telefone', 'Assinatura do Responsavél']]
        # Função para formatar os dados, garantindo que 'NASCIMENTO' não seja None
        for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
            nome = row['NOME DO ALUNO']
            assinatura = ''
            telefones_str = ''

            data.append([row_num, nome, telefones_str, assinatura])

        table = Table(data, colWidths=[0.33 * inch, 3 * inch, 1.25 * inch, 3 * inch])
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), white),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ])
        table.setStyle(table_style)
        elements.append(table)

        # Adicionar a quebra de página após a última tabela
        elements.append(PageBreak())

    doc.build(elements)

    # Resetar o buffer para o início
    buffer.seek(0)
    try:
        from gerarPDF import salvar_e_abrir_pdf as _salvar_helper
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
            from utilitarios.gerenciador_documentos import salvar_documento_sistema
            from utilitarios.tipos_documentos import TIPO_LISTA_REUNIAO

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            try:
                tmp.write(buffer.getvalue())
                tmp.close()
                descricao = f"Lista para Reunião - {datetime.datetime.now().year}"
                try:
                    salvar_documento_sistema(tmp.name, TIPO_LISTA_REUNIAO, funcionario_id=1, finalidade='Secretaria', descricao=descricao)
                    saved_path = tmp.name
                except Exception:
                    try:
                        if _salvar_helper:
                            buffer.seek(0)
                            _salvar_helper(buffer)
                    except Exception:
                        pass
            finally:
                pass
    finally:
        try:
            buffer.close()
        except Exception:
            pass