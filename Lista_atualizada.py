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
from typing import Any, cast

# Cache global para imagens e estilos
_IMAGE_CACHE = {}
_STYLE_CACHE = {}

def _get_cached_image(path, width, height):
    """Retorna uma imagem em cache para evitar recarregamento."""
    key = (path, width, height)
    if key not in _IMAGE_CACHE:
        _IMAGE_CACHE[key] = Image(path, width=width, height=height)
    return _IMAGE_CACHE[key]

def _get_cached_style(name, **kwargs):
    """Retorna um estilo em cache para evitar recriação."""
    key = (name, tuple(sorted(kwargs.items())))
    if key not in _STYLE_CACHE:
        _STYLE_CACHE[key] = ParagraphStyle(name=name, **kwargs)
    return _STYLE_CACHE[key]

def _get_common_table_style():
    """Retorna o estilo de tabela comum usado em múltiplos lugares."""
    if 'common_table' not in _STYLE_CACHE:
        _STYLE_CACHE['common_table'] = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ])
    return _STYLE_CACHE['common_table']

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
            (
                SELECT GROUP_CONCAT(
                    CONCAT(hm.status_novo, ' em ', DATE_FORMAT(hm.data_mudanca, '%d/%m/%Y'))
                    ORDER BY hm.data_mudanca DESC
                    SEPARATOR ' | '
                )
                FROM historico_matricula hm 
                WHERE hm.matricula_id = m.id 
                AND hm.status_novo IN ('Transferido', 'Transferida')
            ) AS 'HISTORICO_TRANSFERENCIA',
            e_origem.nome AS 'ESCOLA_ORIGEM',
            e_destino.nome AS 'ESCOLA_DESTINO',
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
        LEFT JOIN
            escolas e_origem ON m.escola_origem_id = e_origem.id
        LEFT JOIN
            escolas e_destino ON m.escola_destino_id = e_destino.id
        WHERE 
            m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
        AND 
            a.escola_id = 60
        AND
            (m.status = 'Ativo' OR m.status = 'Transferido' OR m.status = 'Transferida')
        GROUP BY 
            a.id, a.nome, a.sexo, a.data_nascimento, a.descricao_transtorno,
            s.nome, s.id, t.nome, t.turno, m.status, f.nome, m.data_matricula, m.id,
            e_origem.nome, e_destino.nome
        ORDER BY
            CASE 
                WHEN m.data_matricula < %s THEN 1  -- Alunos matriculados antes da data_inicio
                ELSE 2  -- Alunos matriculados após a data_inicio
            END,
            CASE 
                WHEN m.data_matricula < %s THEN a.nome  -- Ordena alfabeticamente para o primeiro grupo
                ELSE m.data_matricula  -- Ordena cronologicamente para o segundo grupo
            END;
    """
    
    try:
        cursor.execute(query, (ano_letivo, data_inicio, data_inicio))
        dados_aluno = cursor.fetchall()
        logger.info("Total de alunos encontrados: %d", len(dados_aluno))
        logger.info("Total de alunos matriculados: %d", len([aluno for aluno in dados_aluno if aluno['SITUAÇÃO'] == 'Ativo']))
        return dados_aluno
    except Exception as e:
        logger.error("Erro ao executar a consulta: %s", str(e))
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

def data_funcionario(escola_id):
    conn: Any = conectar_bd()
    if not conn:
        logger.info("Não foi possível conectar ao banco de dados.")
        return None
    cursor: Any = cast(Any, conn).cursor(dictionary=True)

    query = """
        SELECT 
            f.nome AS Funcionario,
            f.cargo AS Cargo,
            CASE
                WHEN f.cargo = 'Professor@' AND d.nome IS NOT NULL THEN d.nome
                WHEN f.cargo = 'Professor@' AND d.nome IS NULL THEN 'Polivalente'
                ELSE 'Não é professor'
            END AS Disciplina
        FROM 
            funcionarios f
        LEFT JOIN 
            funcionario_disciplinas fd ON f.id = fd.funcionario_id
        LEFT JOIN 
            disciplinas d ON fd.disciplina_id = d.id
        WHERE 
            f.escola_id = %s
        ORDER BY
            f.nome, f.cargo;
    """
    try:
        cursor.execute(query, (escola_id,))
        data = cursor.fetchall()  # Retorna todos os registros
        return data
    except Exception as e:
        logger.error("Erro ao executar a consulta: %s", str(e))
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
        logger.info("Não foi possível conectar ao banco de dados.")
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
        logger.error("Erro ao executar a consulta: %s", str(e))
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

def add_employee_table(elements, funcionarios_df, figura_inferior, cabecalho):
    """
    Adiciona uma tabela de funcionários ao PDF.
    """
    # Cabeçalho da página com imagem em cache
    img = _get_cached_image(figura_inferior, 3 * inch, 0.7 * inch)
    header_style = _get_cached_style('Header', fontSize=12, alignment=1)
    data = [
        [img],
        [Paragraph('<br/>'.join(cabecalho), header_style)]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.25 * inch))
    titulo_style = _get_cached_style('FuncionariosTitulo', fontSize=16, alignment=1)
    elements.append(Paragraph("<b>RELATÓRIO DE FUNCIONÁRIOS</b>", titulo_style))
    elements.append(Spacer(1, 0.15 * inch))

    # Cabeçalho da tabela de funcionários
    data: list[list[Any]] = [['Nº', 'Nome', 'Cargo', 'Disciplina']]
    for row_num, (index, row) in enumerate(funcionarios_df.iterrows(), start=1):
        data.append([row_num, row['Funcionario'], row['Cargo'], row['Disciplina']])

    # Cria a tabela
    table = Table(data)
    table.setStyle(_get_common_table_style())
    # Adiciona alinhamento específico
    table_style_extra = TableStyle([('ALIGN', (1, 1), (1, -1), 'LEFT')])
    table.setStyle(table_style_extra)
    elements.append(table)
    elements.append(PageBreak())

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

def add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior):
    img = _get_cached_image(figura_inferior, 3 * inch, 0.7 * inch)
    header_style = _get_cached_style('Header', fontSize=12, alignment=1)
    data = [
        [img],
        [Paragraph('<br/>'.join(cabecalho), header_style)]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 3.3 * inch))
    capa_style = _get_cached_style('Capa', fontSize=24, alignment=1)
    elements.append(Paragraph("<b>RELAÇÃO DE ALUNOS</b>", capa_style))
    elements.append(Spacer(1, 5 * inch))
    ano_style = _get_cached_style('Ano', fontSize=18, alignment=1)
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ano_style))
    elements.append(PageBreak())

def format_phone_numbers(telefones):
    """
    Formata os números de telefone, adicionando uma quebra de linha após cada número.
    """
    if not telefones:
        return ""
    
    # Divide os telefones pela barra (/) e formata
    telefones_lista = telefones.split('/')
    telefones_formatados = [formatar_telefone(tel) for tel in telefones_lista]
    
    # Retorna com quebras de linha entre os telefones
    return '<br/>'.join(telefones_formatados)

def add_class_table(elements, turma_df, nome_serie, nome_turma, turno, nome_professor, figura_inferior, cabecalho):
    # Cabeçalho com cache
    img = _get_cached_image(figura_inferior, 3 * inch, 0.7 * inch)
    header_style = _get_cached_style('Header', fontSize=12, alignment=1)
    datacabecalho = [
        [img],
        [Paragraph('<br/>'.join(cabecalho), header_style)]
    ]
    tablecabecalho = Table(datacabecalho, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    tablecabecalho.setStyle(table_style)
    elements.append(tablecabecalho)

    elements.append(Spacer(1, 0.25 * inch))
    turma_style = _get_cached_style('TurmaTitulo', fontSize=12, alignment=1)
    elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", turma_style))
    elements.append(Spacer(1, 0.1 * inch))
    prof_style = _get_cached_style('ProfessoraTitulo', fontSize=12, alignment=0)
    elements.append(Paragraph(f"<b>PROFESSOR@: {nome_professor} </b>", prof_style))
    elements.append(Spacer(1, 0.15 * inch))
    
    # Calcula totais usando máscaras booleanas (mais eficiente)
    mask_masculino = turma_df['SEXO'] == 'M'
    mask_feminino = turma_df['SEXO'] == 'F'
    mask_transferidos = turma_df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])
    
    total_masculino = mask_masculino.sum()
    total_feminino = mask_feminino.sum()
    total_transferidos = mask_transferidos.sum()
    
    totais_style = _get_cached_style('TotaisAlunos', fontSize=12, alignment=0)
    elements.append(Paragraph(f"TOTAIS: MASCULINO ({total_masculino}) FEMININO ({total_feminino}) - TRANSFERIDOS: {total_transferidos}", totais_style))
    elements.append(Spacer(1, 0.15 * inch))

    # Estilos reutilizáveis para a tabela
    tel_style = _get_cached_style('Telefones', fontSize=10)
    sit_style = _get_cached_style('Situacao', fontSize=10)
    
    data: list[list[Any]] = [['Nº', 'Nome', 'Nascimento', 'Telefones', 'Transtorno', 'Situação']]
    for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
        nascimento = row['NASCIMENTO'].strftime('%d/%m/%Y') if row['NASCIMENTO'] else "Data não disponível"
        telefones = format_phone_numbers(row['TELEFONES'])
        
        # Formata a situação do aluno
        situacao = row['SITUAÇÃO']
        if situacao in ['Transferido', 'Transferida']:
            data_transferencia = row['DATA_TRANSFERENCIA'].strftime('%d/%m/%Y') if row['DATA_TRANSFERENCIA'] else "Data não disponível"
            situacao = f"<b><font color='red'>{situacao} em {data_transferencia}</font></b>"
        elif situacao == 'Cancelado':
            situacao = "<b><font color='red'>Cancelado</font></b>"
        elif row['DATA_MATRICULA']:
            data_matricula = row['DATA_MATRICULA'].strftime('%d/%m/%Y')
            situacao = f"<b><font color='blue'>Matriculado em {data_matricula}</font></b>"
        
        data.append([row_num, row['NOME DO ALUNO'], nascimento, Paragraph(telefones, tel_style), row['TRANSTORNO'], Paragraph(situacao, sit_style)])

    table = Table(data, colWidths=[0.275 * inch, 3.1 * inch, 1. * inch, 1.2* inch, 1.2 * inch, 1.2 * inch])
    table.setStyle(_get_common_table_style())
    # Adiciona estilos específicos desta tabela
    extra_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT')
    ])
    table.setStyle(extra_style)
    elements.append(table)
    elements.append(PageBreak())

def add_transtornos_detalhados(elements, df, figura_inferior, cabecalho):
    """
    Adiciona uma tabela detalhada de transtornos por série, sexo e turno.
    """
    # Cabeçalho da página com cache
    img = _get_cached_image(figura_inferior, 3 * inch, 0.7 * inch)
    header_style = _get_cached_style('Header', fontSize=12, alignment=1)
    data = [
        [img],
        [Paragraph('<br/>'.join(cabecalho), header_style)]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.25 * inch))
    titulo_style = _get_cached_style('TranstornosDetalhadosTitulo', fontSize=16, alignment=1)
    elements.append(Paragraph("<b>DISTRIBUIÇÃO DE TRANSTORNOS POR SÉRIE, SEXO E TURNO</b>", titulo_style))
    elements.append(Spacer(1, 0.15 * inch))

    # Filtra os dados para excluir transtornos nulos e o transtorno 'Nenhum'
    df_filtrado = df[(df['TRANSTORNO'].notna()) & (df['TRANSTORNO'] != 'Nenhum')]
    
    # Agrupa os dados por série, turma, turno, sexo e transtorno
    df_agrupado = df_filtrado.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO', 'SEXO', 'TRANSTORNO']).size().reset_index(name='TOTAL')
    
    # Ordena os dados
    df_agrupado = df_agrupado.sort_values(['NOME_SERIE', 'NOME_TURMA', 'TURNO', 'SEXO'])
    
    # Prepara os dados para a tabela
    dados_tabela = [['Série', 'Turma', 'Turno', 'Sexo', 'Transtorno', 'Total']]
    
    for _, row in df_agrupado.iterrows():
        serie = row['NOME_SERIE']
        turma = row['NOME_TURMA']
        turno = row['TURNO']
        sexo = 'Masculino' if row['SEXO'] == 'M' else 'Feminino'
        transtorno = row['TRANSTORNO']
        total = row['TOTAL']
        
        dados_tabela.append([serie, turma, turno, sexo, transtorno, str(total)])

    # Cria a tabela usando estilo comum
    table = Table(dados_tabela, colWidths=[1 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 1.2 * inch, 0.6 * inch])
    table.setStyle(_get_common_table_style())
    elements.append(table)
    elements.append(PageBreak())

def add_dashboard(elements, df, figura_inferior, cabecalho):
    """
    Adiciona um dashboard com estatísticas dos alunos ao PDF.
    """
    # Cabeçalho da página com cache
    img = _get_cached_image(figura_inferior, 3 * inch, 0.7 * inch)
    header_style = _get_cached_style('Header', fontSize=12, alignment=1)
    data = [
        [img],
        [Paragraph('<br/>'.join(cabecalho), header_style)]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.25 * inch))
    dash_style = _get_cached_style('DashboardTitulo', fontSize=16, alignment=1)
    elements.append(Paragraph("<b>DASHBOARD - ESTATÍSTICAS DOS ALUNOS</b>", dash_style))
    elements.append(Spacer(1, 0.15 * inch))

    # Calcula as estatísticas usando máscaras booleanas (mais eficiente)
    total_alunos = len(df)
    mask_masculino = df['SEXO'] == 'M'
    mask_feminino = df['SEXO'] == 'F'
    mask_transferidos = df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])
    
    total_masculino = mask_masculino.sum()
    total_feminino = mask_feminino.sum()
    total_transferidos = mask_transferidos.sum()
    transferidos_masculino = (mask_transferidos & mask_masculino).sum()
    transferidos_feminino = (mask_transferidos & mask_feminino).sum()
    
    # Filtra apenas alunos ativos para as distribuições (exclui Transferidos e Cancelados)
    df_ativos = df[~df['SITUAÇÃO'].isin(['Transferido', 'Transferida', 'Cancelado'])]
    ativos_masculino = (df_ativos['SEXO'] == 'M').sum()
    ativos_feminino = (df_ativos['SEXO'] == 'F').sum()
    
    # Tabela de estatísticas gerais
    stats_data = [
        ['Categoria', 'Masculino', 'Feminino', 'Total'],
        ['Total de Alunos', str(total_masculino), str(total_feminino), str(total_alunos)],
        ['Alunos Ativos', str(ativos_masculino), str(ativos_feminino), str(len(df_ativos))],
        ['Alunos Transferidos', str(transferidos_masculino), str(transferidos_feminino), str(total_transferidos)]
    ]
    
    stats_table = Table(stats_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1 * inch])
    stats_table.setStyle(_get_common_table_style())
    elements.append(stats_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Distribuição por série e turma usando máscaras booleanas
    series_data = []
    grupos = df_ativos.groupby(['NOME_SERIE', 'NOME_TURMA'])
    for (serie, turma), grupo in grupos:
        masculino = (grupo['SEXO'] == 'M').sum()
        feminino = (grupo['SEXO'] == 'F').sum()
        total = len(grupo)
        # Formata o nome da série e turma
        nome_serie_turma = f"{serie} {turma}"
        series_data.append([nome_serie_turma, str(masculino), str(feminino), str(total)])
    
    # Ordena os dados por série e turma
    series_data.sort(key=lambda x: (x[0].split()[0], x[0].split()[1]))
    
    # Tabela de distribuição por série e turma
    series_header = [['Série/Turma', 'Masculino', 'Feminino', 'Total']]
    series_table = Table(series_header + series_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1 * inch])
    series_table.setStyle(_get_common_table_style())
    elements.append(series_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Distribuição por turno usando máscaras
    turnos_data = []
    for turno in df_ativos['TURNO'].unique():
        turno_df = df_ativos[df_ativos['TURNO'] == turno]
        masculino = (turno_df['SEXO'] == 'M').sum()
        feminino = (turno_df['SEXO'] == 'F').sum()
        total = len(turno_df)
        turnos_data.append([turno, str(masculino), str(feminino), str(total)])

    # Tabela de distribuição por turno
    turnos_header = [['Turno', 'Masculino', 'Feminino', 'Total']]
    turnos_table = Table(turnos_header + turnos_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1 * inch])
    turnos_table.setStyle(_get_common_table_style())
    elements.append(turnos_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Tabela de total de alunos com transtorno por turno
    trans_titulo_style = _get_cached_style('TranstornosTurnoTitulo', fontSize=14, alignment=1)
    elements.append(Paragraph("<b>TOTAL DE ALUNOS COM TRANSTORNO POR TURNO</b>", trans_titulo_style))
    elements.append(Spacer(1, 0.15 * inch))

    # Filtra alunos com transtorno (excluindo 'Nenhum' e nulos)
    df_transtornos = df_ativos[(df_ativos['TRANSTORNO'].notna()) & (df_ativos['TRANSTORNO'] != 'Nenhum')]
    
    # Agrupa por turno e sexo usando máscaras
    turnos_transtorno_data = []
    for turno in df_transtornos['TURNO'].unique():
        turno_df = df_transtornos[df_transtornos['TURNO'] == turno]
        masculino = (turno_df['SEXO'] == 'M').sum()
        feminino = (turno_df['SEXO'] == 'F').sum()
        total = len(turno_df)
        turnos_transtorno_data.append([turno, str(masculino), str(feminino), str(total)])

    # Tabela de total de alunos com transtorno por turno
    turnos_transtorno_header = [['Turno', 'Masculino', 'Feminino', 'Total']]
    turnos_transtorno_table = Table(turnos_transtorno_header + turnos_transtorno_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1 * inch])
    turnos_transtorno_table.setStyle(_get_common_table_style())
    elements.append(turnos_transtorno_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Distribuição por transtorno usando máscaras
    transtornos_data = []
    sem_transtorno = None
    com_transtorno = []
    
    for transtorno in df_ativos['TRANSTORNO'].unique():
        transtorno_df = df_ativos[df_ativos['TRANSTORNO'] == transtorno]
        masculino = (transtorno_df['SEXO'] == 'M').sum()
        feminino = (transtorno_df['SEXO'] == 'F').sum()
        total = len(transtorno_df)
        
        if not transtorno:
            sem_transtorno = ['Nenhum', str(masculino), str(feminino), str(total)]
        else:
            com_transtorno.append([transtorno, str(masculino), str(feminino), str(total)])
    
    # Ordena os transtornos pelo comprimento da string do transtorno em ordem crescente
    com_transtorno.sort(key=lambda x: len(x[0]))
    
    # Monta a lista final garantindo que 'Nenhum' seja o primeiro
    if sem_transtorno:
        transtornos_data = [sem_transtorno] + com_transtorno
    else:
        transtornos_data = com_transtorno

    # Tabela de distribuição por transtorno
    transtornos_header = [['Transtorno', 'Masculino', 'Feminino', 'Total']]
    transtornos_table = Table(transtornos_header + transtornos_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1 * inch])
    transtornos_table.setStyle(_get_common_table_style())
    elements.append(transtornos_table)
    elements.append(PageBreak())

    # Adiciona a tabela detalhada de transtornos
    add_transtornos_detalhados(elements, df_ativos, figura_inferior, cabecalho)

def lista_atualizada():
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
            # Opcional: remover data de transferência para não conflitar com exibição
            if 'DATA_TRANSFERENCIA' in df.columns:
                df.loc[filtro_aluna, 'DATA_TRANSFERENCIA'] = None
    # print(df[['NOME_SERIE', 'NOME_TURMA', 'TURNO']].isnull().sum())

    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    figura_superior = os.path.join(os.path.dirname(__file__), 'imagens', 'logosemed.png')
    figura_inferior = os.path.join(os.path.dirname(__file__), 'imagens', 'logopaco.png')

    doc, buffer = create_pdf_buffer()
    elements = []

    add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior)
    
    # Adiciona o dashboard antes das tabelas
    add_dashboard(elements, df, figura_inferior, cabecalho)

    # Adiciona as tabelas de alunos
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        logger.info(f"{nome_serie}, {nome_turma}, {turno} - {turma_df.shape[0]}")
        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else ' '
        if turma_df.empty:
            logger.info(f"Nenhum aluno encontrado para a turma: {nome_serie}, {nome_turma}, {turno}")
            continue
        add_class_table(elements, turma_df, nome_serie, nome_turma, turno, nome_professor, figura_inferior, cabecalho)

    # # Busca os dados dos funcionários
    # escola_id = 60
    # funcionarios = data_funcionario(escola_id)
    # if funcionarios:
    #     funcionarios_df = pd.DataFrame(funcionarios)
    #     add_employee_table(elements, funcionarios_df, figura_inferior, cabecalho)
    # else:
    #     print("Nenhum funcionário encontrado.")

    # Gera o PDF
    doc.build(elements)
    buffer.seek(0)
    # Preferir o helper de PDF (mantém compatibilidade com testes que o mockam).
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
            # Gravamos temporário e delegamos ao gerenciador de documentos para upload+registro
            import tempfile
            from utilitarios.gerenciador_documentos import salvar_documento_sistema
            from utilitarios.tipos_documentos import TIPO_LISTA_ATUALIZADA

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            try:
                tmp.write(buffer.getvalue())
                tmp.close()
                descricao = f"Lista Atualizada - {datetime.datetime.now().year}"
                try:
                    salvar_documento_sistema(tmp.name, TIPO_LISTA_ATUALIZADA, funcionario_id=1, finalidade='Secretaria', descricao=descricao)
                    saved_path = tmp.name
                except Exception:
                    # fallback: tentar abrir localmente via helper (se disponível)
                    try:
                        if _salvar_helper:
                            buffer.seek(0)
                            _salvar_helper(buffer)
                    except Exception:
                        pass
            finally:
                # não remover aqui o arquivo temporário: o gerenciador pode precisar dele
                pass
    finally:
        try:
            buffer.close()
        except Exception:
            pass

def lista_matriculados_apos_inicio():
    """
    Gera uma lista de alunos matriculados após o início do ano letivo,
    incluindo alunos transferidos.
    """
    ano_letivo = 2025
    
    # Busca os dados dos alunos
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        logger.info("Nenhum dado de aluno encontrado.")
        return

    # Busca a data de início do ano letivo
    data_ano = data_ano_letivo(ano_letivo)
    if not data_ano:
        logger.info("Ano letivo não encontrado.")
        return
    
    data_inicio = data_ano['data_inicio']
    logger.info(f"Data de início do ano letivo: {data_inicio}")

    # Converte para DataFrame
    df = pd.DataFrame(dados_aluno)
    
    # Filtra apenas alunos matriculados após a data de início
    # Inclui alunos com status Ativo, Transferido ou Transferida
    df_filtrado = df[
        (df['DATA_MATRICULA'] > data_inicio) & 
        (df['SITUAÇÃO'].isin(['Ativo', 'Transferido', 'Transferida']))
    ].copy()
    
    if df_filtrado.empty:
        logger.info("Nenhum aluno matriculado após o início do ano letivo.")
        return
    
    logger.info(f"Total de alunos matriculados após o início: {len(df_filtrado)}")

    # Configuração do PDF
    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    figura_inferior = os.path.join(os.path.dirname(__file__), 'imagens', 'logopaco.png')
    doc, buffer = create_pdf_buffer()
    elements = []

    # Cabeçalho
    img = _get_cached_image(figura_inferior, 3 * inch, 0.7 * inch)
    header_style = _get_cached_style('Header', fontSize=12, alignment=1)
    data = [
        [img],
        [Paragraph('<br/>'.join(cabecalho), header_style)]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.25 * inch))
    
    # Título
    titulo_style = _get_cached_style('TituloMatriculados', fontSize=16, alignment=1)
    elements.append(Paragraph(
        f"<b>ALUNOS MATRICULADOS APÓS {data_inicio.strftime('%d/%m/%Y')}</b>",
        titulo_style
    ))
    elements.append(Spacer(1, 0.1 * inch))
    
    subtitulo_style = _get_cached_style('SubtituloMatriculados', fontSize=14, alignment=1)
    elements.append(Paragraph(
        f"<b>Ano Letivo: {ano_letivo}</b>",
        subtitulo_style
    ))
    elements.append(Spacer(1, 0.15 * inch))

    # Estatísticas
    total = len(df_filtrado)
    masculino = (df_filtrado['SEXO'] == 'M').sum()
    feminino = (df_filtrado['SEXO'] == 'F').sum()
    ativos = (df_filtrado['SITUAÇÃO'] == 'Ativo').sum()
    transferidos = (df_filtrado['SITUAÇÃO'].isin(['Transferido', 'Transferida'])).sum()
    
    stats_style = _get_cached_style('StatsMatriculados', fontSize=12, alignment=0)
    elements.append(Paragraph(
        f"<b>TOTAL: {total} alunos | Masculino: {masculino} | Feminino: {feminino} | "
        f"Ativos: {ativos} | Transferidos: {transferidos}</b>",
        stats_style
    ))
    elements.append(Spacer(1, 0.2 * inch))

    # Ordena por data de matrícula (mais recente primeiro) e depois por nome
    df_filtrado = df_filtrado.sort_values(['DATA_MATRICULA', 'NOME DO ALUNO'], ascending=[False, True])

    # Tabela de alunos
    tel_style = _get_cached_style('Telefones', fontSize=9)
    sit_style = _get_cached_style('Situacao', fontSize=9)
    
    data_table: list[list[Any]] = [
        ['Nº', 'Nome', 'Série/Turma', 'Turno', 'Data Matrícula', 'Situação', 'Telefones']
    ]
    
    for row_num, (index, row) in enumerate(df_filtrado.iterrows(), start=1):
        nome = row['NOME DO ALUNO']
        serie_turma = f"{row['NOME_SERIE']} {row['NOME_TURMA']}"
        turno = row['TURNO']
        data_matricula = row['DATA_MATRICULA'].strftime('%d/%m/%Y') if row['DATA_MATRICULA'] else "N/D"
        
        # Formata a situação
        situacao = row['SITUAÇÃO']
        if situacao in ['Transferido', 'Transferida']:
            data_transf = row['DATA_TRANSFERENCIA'].strftime('%d/%m/%Y') if row['DATA_TRANSFERENCIA'] else "N/D"
            situacao_texto = f"<font color='red'><b>{situacao}</b><br/>{data_transf}</font>"
        else:
            situacao_texto = f"<font color='green'><b>{situacao}</b></font>"
        
        # Formata telefones
        telefones = format_phone_numbers(row['TELEFONES'])
        
        data_table.append([
            row_num,
            nome,
            serie_turma,
            turno,
            data_matricula,
            Paragraph(situacao_texto, sit_style),
            Paragraph(telefones, tel_style)
        ])

    # Cria a tabela
    table = Table(data_table, colWidths=[
        0.3 * inch,  # Nº
        2.2 * inch,  # Nome
        0.8 * inch,  # Série/Turma
        0.6 * inch,  # Turno
        0.8 * inch,  # Data Matrícula
        0.8 * inch,  # Situação
        1.2 * inch   # Telefones
    ])
    table.setStyle(_get_common_table_style())
    extra_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Nome alinhado à esquerda
        ('FONTSIZE', (0, 1), (-1, -1), 9),   # Fonte menor para o conteúdo
    ])
    table.setStyle(extra_style)
    elements.append(table)

    # Gera o PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Salva o PDF
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
            from utilitarios.tipos_documentos import TIPO_LISTA_ATUALIZADA

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            try:
                tmp.write(buffer.getvalue())
                tmp.close()
                descricao = f"Alunos Matriculados Após Início - {ano_letivo}"
                try:
                    salvar_documento_sistema(
                        tmp.name, 
                        TIPO_LISTA_ATUALIZADA, 
                        funcionario_id=1, 
                        finalidade='Secretaria', 
                        descricao=descricao
                    )
                    saved_path = tmp.name
                    logger.info(f"PDF salvo com sucesso: {saved_path}")
                except Exception as e:
                    logger.error(f"Erro ao salvar documento: {e}")
                    if _salvar_helper:
                        buffer.seek(0)
                        _salvar_helper(buffer)
            finally:
                pass
    finally:
        try:
            buffer.close()
        except Exception:
            pass

    logger.info("Relatório de alunos matriculados após o início gerado com sucesso!")

# lista_atualizada()
# lista_matriculados_apos_inicio()