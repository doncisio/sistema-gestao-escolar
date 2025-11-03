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

def fetch_student_data(ano_letivo):
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    # Busca as datas de início e fim do ano letivo
    data_ano = data_ano_letivo(ano_letivo)
    if not data_ano:
        print("Ano letivo não encontrado.")
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
        print("Total de alunos encontrados:", len(dados_aluno))
        print("Total de alunos matriculados:", len([aluno for aluno in dados_aluno if aluno['SITUAÇÃO'] == 'Ativo']))
        return dados_aluno
    except Exception as e:
        print("Erro ao executar a consulta:", str(e))
        return None

def data_funcionario(escola_id):
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

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
        print("Erro ao executar a consulta:", str(e))
        return None

def data_ano_letivo(ano_letivo):
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

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
        print("Erro ao executar a consulta:", str(e))
        return None

def add_employee_table(elements, funcionarios_df, figura_inferior, cabecalho):
    """
    Adiciona uma tabela de funcionários ao PDF.
    """
    # Cabeçalho da página
    data = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')    # Alinhamento horizontal
    ])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph("<b>RELATÓRIO DE FUNCIONÁRIOS</b>", ParagraphStyle(name='FuncionariosTitulo', fontSize=16, alignment=1)))
    elements.append(Spacer(1, 0.15 * inch))

    # Cabeçalho da tabela de funcionários
    data = [['Nº', 'Nome', 'Cargo', 'Disciplina']]
    for row_num, (index, row) in enumerate(funcionarios_df.iterrows(), start=1):
        nome = row['Funcionario']
        cargo = row['Cargo']
        disciplina = row['Disciplina']
        data.append([row_num, nome, cargo, disciplina])

    # Cria a tabela
    table = Table(data)
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ])
    table.setStyle(table_style)
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
    data = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')    # Alinhamento horizontal
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 3.3 * inch))
    elements.append(Paragraph("<b>RELAÇÃO DE ALUNOS</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1)))
    elements.append(Spacer(1, 5 * inch))
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
    elements.append(PageBreak())

def format_phone_numbers(telefones):
    """
    Formata os números de telefone, adicionando uma quebra de linha após cada dois números.
    """
    if not telefones:
        return ""
    
    # Divide os telefones pela barra (/)
    telefones_lista = telefones.split('/')

    # Formata cada número de telefone
    telefones_formatados = [formatar_telefone(tel) for tel in telefones_lista]
    
    # Agrupa os telefones de dois em dois
    grupos = []
    for i in range(0, len(telefones_lista), 1):
        grupo = telefones_formatados[i:i+1]  # Pega um telefones por vez
        grupos.append('/'.join(grupo))  # Junta os dois telefones com uma barra
    
    # Adiciona uma quebra de linha após cada grupo
    return '<br/>'.join(grupos)

def add_class_table(elements, turma_df, nome_serie, nome_turma, turno, nome_professor, figura_inferior, cabecalho):
    datacabecalho = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    tablecabecalho = Table(datacabecalho, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')    # Alinhamento horizontal
    ])
    tablecabecalho.setStyle(table_style)
    elements.append(tablecabecalho)

    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(f"<b>PROFESSOR@: {nome_professor} </b>", ParagraphStyle(name='ProfessoraTitulo', fontSize=12, alignment=0)))
    elements.append(Spacer(1, 0.15 * inch))
    
    # Calcula totais incluindo alunos transferidos
    total_masculino = turma_df[turma_df['SEXO'] == 'M'].shape[0]
    total_feminino = turma_df[turma_df['SEXO'] == 'F'].shape[0]
    total_transferidos = turma_df[turma_df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])].shape[0]
    
    elements.append(Paragraph(f"TOTAIS: MASCULINO ({total_masculino}) FEMININO ({total_feminino}) - TRANSFERIDOS: {total_transferidos}", ParagraphStyle(name='TotaisAlunos', fontSize=12, alignment=0)))
    elements.append(Spacer(1, 0.15 * inch))

    data = [['Nº', 'Nome', 'Nascimento', 'Telefones', 'Transtorno', 'Situação']]
    for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
        nome = row['NOME DO ALUNO']
        nascimento = row['NASCIMENTO'].strftime('%d/%m/%Y') if row['NASCIMENTO'] else "Data não disponível"
        transtorno = row['TRANSTORNO']
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
        
        data.append([row_num, nome, nascimento, Paragraph(telefones, ParagraphStyle(name='Telefones', fontSize=10)), transtorno, Paragraph(situacao, ParagraphStyle(name='Situacao', fontSize=10))])

    table = Table(data, colWidths=[0.275 * inch, 3.1 * inch, 1. * inch, 1.2* inch, 1.2 * inch, 1.2 * inch])
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
    elements.append(PageBreak())

def add_transtornos_detalhados(elements, df, figura_inferior, cabecalho):
    """
    Adiciona uma tabela detalhada de transtornos por série, sexo e turno.
    """
    # Cabeçalho da página
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

    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph("<b>DISTRIBUIÇÃO DE TRANSTORNOS POR SÉRIE, SEXO E TURNO</b>", ParagraphStyle(name='TranstornosDetalhadosTitulo', fontSize=16, alignment=1)))
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

    # Cria a tabela
    table = Table(dados_tabela, colWidths=[1 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 1.2 * inch, 0.6 * inch])
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(PageBreak())

def add_dashboard(elements, df, figura_inferior, cabecalho):
    """
    Adiciona um dashboard com estatísticas dos alunos ao PDF.
    """
    # Cabeçalho da página
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
    
    # Filtra apenas alunos ativos para as distribuições (exclui Transferidos e Cancelados)
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
    # Agrupa por série e turma
    grupos = df_ativos.groupby(['NOME_SERIE', 'NOME_TURMA'])
    for (serie, turma), grupo in grupos:
        masculino = len(grupo[grupo['SEXO'] == 'M'])
        feminino = len(grupo[grupo['SEXO'] == 'F'])
        total = len(grupo)
        # Formata o nome da série e turma
        nome_serie_turma = f"{serie} {turma}"
        series_data.append([nome_serie_turma, str(masculino), str(feminino), str(total)])
    
    # Ordena os dados por série e turma
    series_data.sort(key=lambda x: (x[0].split()[0], x[0].split()[1]))
    
    # Tabela de distribuição por série e turma
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

    # Tabela de distribuição por turno
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
    elements.append(Spacer(1, 0.25 * inch))

    # Tabela de total de alunos com transtorno por turno
    elements.append(Paragraph("<b>TOTAL DE ALUNOS COM TRANSTORNO POR TURNO</b>", ParagraphStyle(name='TranstornosTurnoTitulo', fontSize=14, alignment=1)))
    elements.append(Spacer(1, 0.15 * inch))

    # Filtra alunos com transtorno (excluindo 'Nenhum' e nulos)
    df_transtornos = df_ativos[(df_ativos['TRANSTORNO'].notna()) & (df_ativos['TRANSTORNO'] != 'Nenhum')]
    
    # Agrupa por turno e sexo
    turnos_transtorno_data = []
    for turno in df_transtornos['TURNO'].unique():
        turno_df = df_transtornos[df_transtornos['TURNO'] == turno]
        masculino = len(turno_df[turno_df['SEXO'] == 'M'])
        feminino = len(turno_df[turno_df['SEXO'] == 'F'])
        total = len(turno_df)
        turnos_transtorno_data.append([turno, str(masculino), str(feminino), str(total)])

    # Tabela de total de alunos com transtorno por turno
    turnos_transtorno_header = [['Turno', 'Masculino', 'Feminino', 'Total']]
    turnos_transtorno_table = Table(turnos_transtorno_header + turnos_transtorno_data, colWidths=[2 * inch, 1 * inch, 1 * inch, 1 * inch])
    turnos_transtorno_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ])
    turnos_transtorno_table.setStyle(turnos_transtorno_style)
    elements.append(turnos_transtorno_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Distribuição por transtorno
    transtornos_data = []
    # Primeiro, vamos separar os dados em dois grupos: sem transtorno e com transtorno
    sem_transtorno = None
    com_transtorno = []
    
    for transtorno in df_ativos['TRANSTORNO'].unique():
        transtorno_df = df_ativos[df_ativos['TRANSTORNO'] == transtorno]
        masculino = len(transtorno_df[transtorno_df['SEXO'] == 'M'])
        feminino = len(transtorno_df[transtorno_df['SEXO'] == 'F'])
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
    transtornos_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ])
    transtornos_table.setStyle(transtornos_style)
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

    figura_superior = os.path.join(os.path.dirname(__file__), 'logosemed.png')
    figura_inferior = os.path.join(os.path.dirname(__file__), 'logopaco.png')

    doc, buffer = create_pdf_buffer()
    elements = []

    add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior)
    
    # Adiciona o dashboard antes das tabelas
    add_dashboard(elements, df, figura_inferior, cabecalho)

    # Adiciona as tabelas de alunos
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        print(f"{nome_serie}, {nome_turma}, {turno} - {turma_df.shape[0]}")
        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else ' '
        if turma_df.empty:
            print(f"Nenhum aluno encontrado para a turma: {nome_serie}, {nome_turma}, {turno}")
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
    salvar_e_abrir_pdf(buffer)

# lista_atualizada()