import io
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
import datetime
from config import get_image_path
from Lista_atualizada import fetch_student_data
from scripts_nao_utilizados.gerar_documentos import PASTAS_TURMAS, criar_pastas_se_nao_existirem, salvar_pdf, adicionar_cabecalho

def lista_frequencia():
    """Gera um PDF com a lista de frequência dos alunos, agrupados por turma."""
    # Observação: os dados dos alunos são obtidos via `fetch_student_data` (importado)
    # Esta função não abre/fecha conexões diretamente; qualquer acesso ao BD
    # deve ser feito pelo provedor `fetch_student_data` ou service layer.
    ano_letivo = 2025
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        from config_logs import get_logger
        logger = get_logger(__name__)
        logger.warning("Nenhum dado de aluno encontrado.")
        return

    df = pd.DataFrame(dados_aluno)
    criar_pastas_se_nao_existirem()

    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    figura_superior = str(get_image_path('logopacobranco.png'))
    figura_inferior = str(get_image_path('logopaco.jpg'))

    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        nome_turma_completo = f"{nome_serie} {nome_turma}" if nome_turma else nome_serie

        if nome_turma_completo not in PASTAS_TURMAS:
            from config_logs import get_logger
            logger = get_logger(__name__)
            logger.warning(f"Aviso: Turma '{nome_turma_completo}' não está mapeada para uma pasta. Pulando...")
            continue

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

        # Adicionar o cabeçalho
        adicionar_cabecalho(elements, cabecalho, figura_inferior, figura_superior, 12)
        elements.append(Spacer(1, 0.25 * inch))

        # Adicionar o título da turma
        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=14, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))

        # Adicionar informações sobre a professora e totais de alunos por sexo
        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else ''
        elements.append(Paragraph(f"<b>PROFESSOR(A): {nome_professor} </b>", ParagraphStyle(name='ProfessoraTitulo', fontSize=14, alignment=0)))
        elements.append(Spacer(1, 0.15 * inch))

        total_masculino = turma_df[turma_df['SEXO'] == 'M'].shape[0]
        total_feminino = turma_df[turma_df['SEXO'] == 'F'].shape[0]
        elements.append(Paragraph(f"TOTAIS: MASCULINO ({total_masculino}) FEMININO ({total_feminino})", ParagraphStyle(name='TotaisAlunos', fontSize=12, alignment=0)))
        elements.append(Spacer(1, 0.15 * inch))

        # Criar a tabela de frequência
        texto_total_vertical = '<br/>'.join(list("TOTAL"))
        datas = pd.date_range(start='2025-01-01', periods=25).date
        tabela_frequencia = [['Nº', 'Nome'] + [''] * len(datas) + [Paragraph(texto_total_vertical, ParagraphStyle(name='TotalStyle', fontSize=10, alignment=1, wordWrap='CJK'))]]
        
        # Estilo para o texto de transferência
        style_transferencia = ParagraphStyle(
            name='TransferenciaStyle',
            parent=None,
            fontSize=10,
            alignment=1,
            textColor=colors.red,
            wordWrap='CJK',
        )
        
        # Lista para armazenar os estilos da tabela
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]
        
        for i, (_, row) in enumerate(turma_df.iterrows(), start=1):
            if row['SITUAÇÃO'] in ['Transferido', 'Transferida']:
                # Para alunos transferidos, mesclar as células e mostrar o status
                data_transferencia = row['DATA_TRANSFERENCIA'].strftime('%d/%m/%Y') if row['DATA_TRANSFERENCIA'] else "Data não disponível"
                texto_transferencia = f"{row['SITUAÇÃO']} em {data_transferencia}"
                # Mesclar todas as células das colunas de datas e a coluna TOTAL
                linha = [i, row['NOME DO ALUNO']] + [''] * (len(datas) + 1)
                # Adicionar o texto de transferência na primeira célula mesclada
                linha[2] = Paragraph(texto_transferencia, style_transferencia)
                # Adicionar estilo para mesclar as células
                table_style.append(('SPAN', (2, i), (-1, i)))  # Mescla da coluna 2 até a última coluna
            else:
                # Para alunos ativos, manter as células normais
                linha = [i, row['NOME DO ALUNO']] + [''] * len(datas) + ['']
            tabela_frequencia.append(linha)
        row_heights = [1 * inch]  # Altura da primeira linha (cabeçalho)
        row_heights.extend([0.25 * inch] * (len(tabela_frequencia) - 1))  # Altura das demais linhas
        table = Table(tabela_frequencia, colWidths=[0.282 * inch, 3 * inch] + [0.25 * inch] * len(datas) + [0.35 * inch], rowHeights=row_heights)
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(PageBreak())

        doc.build(elements)
        buffer.seek(0)
        salvar_pdf(buffer, nome_turma_completo, "Frequencia")

if __name__ == "__main__":
    lista_frequencia()