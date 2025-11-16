from config_logs import get_logger
logger = get_logger(__name__)
import io
import os
import pandas as pd
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, grey
from conexao import conectar_bd
from gerarPDF import salvar_e_abrir_pdf
from biblio_editor import formatar_telefone
import unicodedata
from typing import Any, cast

def fetch_student_data(ano_letivo):
    conn: Any = conectar_bd()
    if not conn:
        logger.info("Não foi possível conectar ao banco de dados.")
        return None
    cursor: Any = cast(Any, conn).cursor(dictionary=True)

    # Busca as datas de início e fim do ano letivo
    data_ano = data_ano_letivo(ano_letivo)
    if not data_ano:
        logger.info("Ano letivo não encontrado.")
        try:
            cast(Any, cursor).close()
        except Exception:
            pass
        try:
            cast(Any, conn).close()
        except Exception:
            pass
        return None

    data_inicio = data_ano['data_inicio']

    # Consulta SQL para buscar os dados dos alunos, incluindo a data de matrícula
    query = """
        SELECT 
            a.nome AS 'NOME DO ALUNO', 
            a.sexo AS 'SEXO', 
            a.data_nascimento AS 'NASCIMENTO',
            a.descricao_transtorno AS 'TRANSTORNO',
            s.nome AS 'NOME_SERIE',
            s.id AS 'ID_SERIE',
            t.nome AS 'NOME_TURMA', 
            t.turno AS 'TURNO', 
            m.status AS 'SITUAÇÃO',
            f.nome AS 'NOME_PROFESSOR',
            COALESCE(
                (
                    SELECT MAX(hm.data_mudanca)
                    FROM historico_matricula hm
                    WHERE hm.matricula_id = m.id
                    AND hm.status_novo = 'Ativo'
                ),
                (
                    SELECT MAX(hm2.data_mudanca)
                    FROM historico_matricula hm2
                    WHERE hm2.matricula_id = m.id
                    AND hm2.status_novo NOT IN ('Transferido', 'Transferida', 'Cancelado', 'Cancelada')
                ),
                m.data_matricula
            ) AS 'DATA_MATRICULA',
            (
                SELECT hm.data_mudanca 
                FROM historico_matricula hm 
                WHERE hm.matricula_id = m.id 
                AND hm.status_novo IN ('Transferido', 'Transferida')
                ORDER BY hm.data_mudanca DESC 
                LIMIT 1
            ) AS 'DATA_TRANSFERENCIA',
            GROUP_CONCAT(DISTINCT r.telefone ORDER BY r.id SEPARATOR '/') AS 'TELEFONES'
        FROM 
            Alunos a
        JOIN 
            Matriculas m ON a.id = m.aluno_id
        JOIN 
            Turmas t ON m.turma_id = t.id
        JOIN 
            Serie s ON t.serie_id = s.id
        LEFT JOIN 
            ResponsaveisAlunos ra ON a.id = ra.aluno_id
        LEFT JOIN 
            Responsaveis r ON ra.responsavel_id = r.id
        LEFT JOIN
            Funcionarios f ON f.turma = t.id AND f.cargo = 'Professor@'
        WHERE 
            m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
        AND 
            a.escola_id = 60
        AND
            (m.status = 'Ativo' OR m.status = 'Transferido' OR m.status = 'Transferida')
        GROUP BY 
            a.id, a.nome, a.sexo, a.data_nascimento, a.descricao_transtorno,
            s.nome, s.id, t.nome, t.turno, m.status, f.nome, m.data_matricula, m.id
        ORDER BY
            a.nome;
    """
    
    try:
        cursor.execute(query, (ano_letivo,))
        dados_aluno = cursor.fetchall()
        logger.info("Total de alunos encontrados:", len(dados_aluno))
        return dados_aluno
    except Exception as e:
        logger.error("Erro ao executar a consulta:", str(e))
        return None
    finally:
        try:
            cast(Any, cursor).close()
        except Exception:
            pass
        try:
            cast(Any, conn).close()
        except Exception:
            pass

def data_ano_letivo(ano_letivo):
    conn: Any = conectar_bd()
    if not conn:
        return None
    cursor: Any = cast(Any, conn).cursor(dictionary=True)

    query = """
        SELECT 
            data_inicio, data_fim
        FROM 
            anosletivos
        WHERE 
            id=(SELECT id FROM anosletivos WHERE ano_letivo = %s);
    """
    try:
        cursor.execute(query, (ano_letivo,))
        data = cursor.fetchone()
        return data
    except Exception as e:
        logger.error("Erro ao executar a consulta:", str(e))
        return None
    finally:
        try:
            cast(Any, cursor).close()
        except Exception:
            pass
        try:
            cast(Any, conn).close()
        except Exception:
            pass

def create_header(cabecalho, figura_inferior):
    """Cria o cabeçalho padrão para todas as páginas"""
    data = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    return table

def create_pdf_buffer():
    buffer = io.BytesIO()
    left_margin = 36
    right_margin = 18
    top_margin = 10
    bottom_margin = 18

    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        leftMargin=left_margin, 
        rightMargin=right_margin, 
        topMargin=top_margin, 
        bottomMargin=bottom_margin
    )
    return doc, buffer

def add_cover_page(elements, cabecalho, figura_inferior):
    data = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 3.3 * inch))
    elements.append(Paragraph("<b>RELAÇÃO GERAL DE ALUNOS</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1)))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("<b>LISTA ALFABÉTICA</b>", ParagraphStyle(name='SubCapa', fontSize=18, alignment=1)))
    elements.append(Spacer(1, 4.7 * inch))
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
    elements.append(PageBreak())

def add_dashboard(elements, df, figura_inferior, cabecalho):
    """
    Adiciona um dashboard com estatísticas dos alunos ao PDF.
    """
    elements.append(create_header(cabecalho, figura_inferior))
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph("<b>DASHBOARD - ESTATÍSTICAS DOS ALUNOS</b>", ParagraphStyle(name='DashboardTitulo', fontSize=16, alignment=1)))
    elements.append(Spacer(1, 0.15 * inch))

    # Calcula as estatísticas
    total_alunos = len(df)
    total_masculino = len(df[df['SEXO'] == 'M'])
    total_feminino = len(df[df['SEXO'] == 'F'])
    total_transferidos = len(df[df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])])
    transferidos_masculino = len(df[(df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])) & (df['SEXO'] == 'M')])
    transferidos_feminino = len(df[(df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])) & (df['SEXO'] == 'F')])
    
    # Filtra apenas alunos ativos para as distribuições
    df_ativos = df[~df['SITUAÇÃO'].isin(['Transferido', 'Transferida', 'Cancelado'])]
    ativos_masculino = len(df_ativos[df_ativos['SEXO'] == 'M'])
    ativos_feminino = len(df_ativos[df_ativos['SEXO'] == 'F'])
    
    # Tabela de estatísticas gerais
    stats_data = [
        ['Categoria', 'Masculino', 'Feminino', 'Total'],
        ['Total de Alunos', str(total_masculino), str(total_feminino), str(total_alunos)],
        ['Alunos Ativos', str(ativos_masculino), str(ativos_feminino), str(len(df_ativos))],
        ['Alunos Transferidos', str(transferidos_masculino), str(transferidos_feminino), str(total_transferidos)]
    ]
    
    stats_table = Table(stats_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1 * inch])
    stats_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ])
    stats_table.setStyle(stats_style)
    elements.append(stats_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Distribuição por série e turma
    series_data = []
    grupos = df_ativos.groupby(['NOME_SERIE', 'NOME_TURMA'])
    for (serie, turma), grupo in grupos:
        masculino = len(grupo[grupo['SEXO'] == 'M'])
        feminino = len(grupo[grupo['SEXO'] == 'F'])
        total = len(grupo)
        nome_serie_turma = f"{serie} {turma}"
        series_data.append([nome_serie_turma, str(masculino), str(feminino), str(total)])
    
    series_data.sort(key=lambda x: (x[0].split()[0], x[0].split()[1]))
    
    series_header = [['Série/Turma', 'Masculino', 'Feminino', 'Total']]
    series_table = Table(series_header + series_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1 * inch])
    series_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ])
    series_table.setStyle(series_style)
    elements.append(series_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Distribuição por turno
    turnos_data = []
    for turno in df_ativos['TURNO'].unique():
        turno_df = df_ativos[df_ativos['TURNO'] == turno]
        masculino = len(turno_df[turno_df['SEXO'] == 'M'])
        feminino = len(turno_df[turno_df['SEXO'] == 'F'])
        total = len(turno_df)
        turnos_data.append([turno, str(masculino), str(feminino), str(total)])

    turnos_header = [['Turno', 'Masculino', 'Feminino', 'Total']]
    turnos_table = Table(turnos_header + turnos_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1 * inch])
    turnos_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ])
    turnos_table.setStyle(turnos_style)
    elements.append(turnos_table)
    elements.append(PageBreak())

def remover_acentos(texto):
    """
    Remove acentos de uma string.
    """
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

def add_alphabetical_list(elements, df, figura_inferior, cabecalho):
    """
    Adiciona uma lista alfabética de alunos agrupada por letra inicial.
    """
    # Ordena o DataFrame pelo nome do aluno
    df = df.sort_values('NOME DO ALUNO')
    
    # Agrupa os alunos por letra inicial (sem acentos)
    df['LETRA_INICIAL'] = df['NOME DO ALUNO'].apply(lambda x: remover_acentos(x[0]).upper())
    
    for letra in sorted(df['LETRA_INICIAL'].unique()):
        # Filtra os alunos pela letra inicial
        alunos_letra = df[df['LETRA_INICIAL'] == letra]
        
        # Cabeçalho da página
        elements.append(create_header(cabecalho, figura_inferior))
        elements.append(Spacer(1, 0.25 * inch))
        elements.append(Paragraph(f"<b>LETRA: {letra}</b>", ParagraphStyle(name='LetraTitulo', fontSize=16, alignment=1)))
        elements.append(Spacer(1, 0.15 * inch))
        
        # Prepara os dados da tabela
        data = [['Nº', 'Nome', 'Série/Turma', 'Turno', 'Sexo', 'Situação']]
        
        for row_num, (index, row) in enumerate(alunos_letra.iterrows(), start=1):
            nome = row['NOME DO ALUNO']
            serie_turma = f"{row['NOME_SERIE']} {row['NOME_TURMA']}"
            turno = row['TURNO']
            sexo = 'M' if row['SEXO'] == 'M' else 'F'
            
            # Formata a situação do aluno
            situacao = row['SITUAÇÃO']
            if situacao in ['Transferido', 'Transferida']:
                data_transferencia = row['DATA_TRANSFERENCIA'].strftime('%d/%m/%Y') if row['DATA_TRANSFERENCIA'] else "Data não disponível"
                situacao = f"<font color='red'>{situacao} em {data_transferencia}</font>"
            elif situacao == 'Cancelado':
                situacao = "<font color='red'>Cancelado</font>"
            else:
                situacao = "Ativo"
            
            data.append([
                row_num, 
                nome, 
                serie_turma, 
                turno, 
                sexo, 
                Paragraph(situacao, ParagraphStyle(name='Situacao', fontSize=10))
            ])  # type: ignore[arg-type]
        
        # Cria a tabela
        table = Table(data, colWidths=[0.4 * inch, 2.5 * inch, 1 * inch, 0.8 * inch, 0.5 * inch, 1.5 * inch])
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ])
        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Adiciona totais para esta letra
        total_letra = len(alunos_letra)
        total_ativos = len(alunos_letra[alunos_letra['SITUAÇÃO'] == 'Ativo'])
        total_transferidos = len(alunos_letra[alunos_letra['SITUAÇÃO'].isin(['Transferido', 'Transferida'])])
        
        elements.append(Paragraph(
            f"<b>Total de alunos com letra {letra}: {total_letra} (Ativos: {total_ativos}, Transferidos: {total_transferidos})</b>",
            ParagraphStyle(name='TotalLetra', fontSize=11, alignment=0)
        ))
        elements.append(PageBreak())

def lista_alfabetica():
    ano_letivo = 2025
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        return

    df = pd.DataFrame(dados_aluno)
    
    # Ajuste específico: marcar aluna como "Cancelado"
    nome_aluna_cancelada = "Lorena Evellyn Ataíde de Oliveira"
    if 'NOME DO ALUNO' in df.columns and 'SITUAÇÃO' in df.columns:
        filtro_aluna = df['NOME DO ALUNO'] == nome_aluna_cancelada
        if filtro_aluna.any():
            df.loc[filtro_aluna, 'SITUAÇÃO'] = 'Cancelado'
            if 'DATA_TRANSFERENCIA' in df.columns:
                df.loc[filtro_aluna, 'DATA_TRANSFERENCIA'] = None

    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    figura_inferior = os.path.join(os.path.dirname(__file__), 'logopaco.png')

    doc, buffer = create_pdf_buffer()
    elements = []

    # Adiciona a capa
    add_cover_page(elements, cabecalho, figura_inferior)
    
    # Adiciona o dashboard
    add_dashboard(elements, df, figura_inferior, cabecalho)
    
    # Adiciona a lista alfabética
    add_alphabetical_list(elements, df, figura_inferior, cabecalho)

    # Gera o PDF
    doc.build(elements)
    buffer.seek(0)
    salvar_e_abrir_pdf(buffer)

if __name__ == "__main__":
    lista_alfabetica()