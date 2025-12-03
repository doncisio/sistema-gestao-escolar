from config_logs import get_logger
logger = get_logger(__name__)
import io
import os
import pandas as pd
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, grey
from conexao import conectar_bd
from gerarPDF import salvar_e_abrir_pdf
from biblio_editor import formatar_telefone, formatar_cpf
from typing import Any, cast
from tabela_docentes import gerar_tabela_docentes
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet

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
            a.cpf AS 'CPF',
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
            GROUP_CONCAT(DISTINCT r.telefone ORDER BY r.id SEPARATOR '/') AS 'TELEFONES',
            GROUP_CONCAT(DISTINCT CONCAT(r.nome, ' (', r.grau_parentesco, ')') ORDER BY r.id SEPARATOR ' | ') AS 'RESPONSAVEIS'
        FROM 
            Alunos a
        JOIN 
            Matriculas m ON a.id = m.aluno_id
        JOIN 
            Turmas t ON m.turma_id = t.id
        JOIN 
            series s ON t.serie_id = s.id
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
        logger.info("Total de alunos encontrados: %s", len(dados_aluno))
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
        WITH professores_disciplinas AS (
            SELECT DISTINCT
                f.id,
                f.nome AS Funcionario,
                f.cargo AS Cargo,
                CASE
                    WHEN f.cargo = 'Professor@' AND d.nome IS NOT NULL THEN d.nome
                    WHEN f.cargo = 'Professor@' AND d.nome IS NULL THEN 'Polivalente'
                    ELSE NULL
                END AS Disciplina,
                GROUP_CONCAT(DISTINCT CONCAT(s.nome, ' ', t.nome, ' - ', t.turno) 
                           ORDER BY s.nome, t.nome 
                           SEPARATOR ' | ') AS Turmas
            FROM 
                funcionarios f
            LEFT JOIN 
                funcionario_disciplinas fd ON f.id = fd.funcionario_id
            LEFT JOIN 
                disciplinas d ON fd.disciplina_id = d.id
            LEFT JOIN
                Turmas t ON fd.turma_id = t.id
            LEFT JOIN
                series s ON t.serie_id = s.id
            WHERE 
                f.escola_id = %s
                AND f.cargo = 'Professor@'
                AND d.nome IS NOT NULL
                AND f.id != 227  -- Exclui o professor volante
            GROUP BY
                f.id, f.nome, f.cargo, d.nome
        ),
        professores_polivalentes AS (
            SELECT DISTINCT
                f.id,
                f.nome AS Funcionario,
                f.cargo AS Cargo,
                'Polivalente' AS Disciplina,
                GROUP_CONCAT(DISTINCT CONCAT(s.nome, ' ', t.nome, ' - ', t.turno) 
                           ORDER BY s.nome, t.nome 
                           SEPARATOR ' | ') AS Turmas
            FROM 
                funcionarios f
            LEFT JOIN
                Turmas t ON f.turma = t.id
            LEFT JOIN
                series s ON t.serie_id = s.id
            WHERE 
                f.escola_id = %s
                AND f.cargo = 'Professor@'
                AND f.turma IS NOT NULL
                AND f.id != 227  -- Exclui o professor volante
                AND NOT EXISTS (
                    SELECT 1 
                    FROM funcionario_disciplinas fd 
                    WHERE fd.funcionario_id = f.id
                )
            GROUP BY
                f.id, f.nome, f.cargo
        ),
        professor_volante AS (
            SELECT DISTINCT
                f.id,
                f.nome AS Funcionario,
                f.cargo AS Cargo,
                f.funcao AS Disciplina,
                GROUP_CONCAT(DISTINCT CONCAT(s.nome, ' ', t.nome, ' - ', t.turno) 
                           ORDER BY s.nome, t.nome 
                           SEPARATOR ' | ') AS Turmas
            FROM 
                funcionarios f
            CROSS JOIN
                Serie s
            LEFT JOIN
                Turmas t ON t.serie_id = s.id AND t.turno = 'Matutino'
            WHERE 
                f.escola_id = %s
                AND f.id = 227  -- ID do professor volante
                AND s.id IN (3, 4, 5, 6, 7)  -- Séries do professor volante
            GROUP BY
                f.id, f.nome, f.cargo, f.funcao
        )
        SELECT * FROM professores_disciplinas
        UNION ALL
        SELECT * FROM professores_polivalentes
        UNION ALL
        SELECT * FROM professor_volante
        ORDER BY Funcionario;
    """
    try:
        cursor.execute(query, (escola_id, escola_id, escola_id))
        data = cursor.fetchall()

        # Debug: Imprimir todos os funcionários retornados
        logger.info("\nTodos os funcionários retornados:")
        for funcionario in data:
            logger.info(f"ID: {funcionario['id']}, Nome: {funcionario['Funcionario']}, Cargo: {funcionario['Cargo']}, Disciplina: {funcionario['Disciplina']}, Turmas: {funcionario['Turmas']}")

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

def create_header(cabecalho, figura_inferior):
    """Cria o cabeçalho padrão para todas as páginas"""
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
    return table

def add_employee_cover_page(elements, figura_inferior, cabecalho):
    """
    Adiciona uma capa para a seção de professores.
    """
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
    elements.append(Paragraph("<b>RELAÇÃO DE PROFESSORES</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1)))
    elements.append(Spacer(1, 5 * inch))
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
    elements.append(PageBreak())

def add_employee_table(elements, funcionarios_df, figura_inferior, cabecalho):
    """
    Adiciona uma tabela de funcionários ao PDF.
    """
    # Cabeçalho da página
    elements.append(create_header(cabecalho, figura_inferior))
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph("<b>RELATÓRIO DE FUNCIONÁRIOS</b>", ParagraphStyle(name='FuncionariosTitulo', fontSize=16, alignment=1)))
    elements.append(Spacer(1, 0.15 * inch))

    # Cabeçalho da tabela de funcionários
    data: list[list[Any]] = [['Nº', 'Nome', 'Cargo', 'Disciplina']]
    for row_num, (index, row) in enumerate(funcionarios_df.iterrows(), start=1):
        nome = row['Funcionario']
        cargo = row['Cargo']
        disciplina = row['Disciplina']
        data.append([row_num, nome, cargo, disciplina])  # type: ignore[arg-type]

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

    # Cria o documento em modo retrato
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
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

def calcular_larguras_colunas(data, max_width):
    """
    Calcula as larguras das colunas dinamicamente com base no conteúdo.
    max_width é a largura total disponível em pontos (1 inch = 72 pontos)
    """
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.lib.styles import getSampleStyleSheet
    
    styles = getSampleStyleSheet()
    style = styles['Normal']
    
    # Larguras mínimas para cada coluna
    min_widths = {
        0: 30,  # Nº
        1: 150, # Nome
        2: 80,  # Nascimento
        3: 80,  # CPF
        4: 100  # Transtorno
    }
    
    # Calcula a largura necessária para cada coluna
    col_widths = [0.0] * len(data[0])
    for row in data:
        for i, cell in enumerate(row):
            if isinstance(cell, str):
                width = stringWidth(cell, style.fontName, style.fontSize)
            elif isinstance(cell, Paragraph):
                width = stringWidth(cell.text, style.fontName, style.fontSize)
            else:
                width = stringWidth(str(cell), style.fontName, style.fontSize)
            
            # Adiciona um pequeno padding
            width += 20
            col_widths[i] = max(col_widths[i], width, float(min_widths[i]))
    
    # Ajusta as larguras para caber na página
    total_width = sum(col_widths)
    if total_width > max_width:
        # Calcula o fator de redução
        factor = max_width / total_width
        # Aplica o fator mantendo as proporções
        col_widths = [width * factor for width in col_widths]
    
    return col_widths

def add_class_table(elements, turma_df, nome_serie, nome_turma, turno, nome_professor, figura_inferior, cabecalho, adicionar_cabecalho=True):
    # Adiciona o cabeçalho apenas se solicitado
    if adicionar_cabecalho:
        elements.append(create_header(cabecalho, figura_inferior))
        elements.append(Spacer(1, 0.25 * inch))
    
    # Converte a abreviação do turno para o nome completo
    turno_completo = "MATUTINO" if turno == "MAT" else "VESPERTINO"
    
    elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno_completo} - {datetime.datetime.now().year}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(f"<b>PROFESSOR@: {nome_professor} </b>", ParagraphStyle(name='ProfessoraTitulo', fontSize=12, alignment=0)))
    elements.append(Spacer(1, 0.15 * inch))
    
    # Filtra alunos ativos para os totais
    alunos_ativos = turma_df[turma_df['SITUAÇÃO'] == 'Ativo']
    
    # Calcula totais apenas para alunos ativos
    total_masculino = alunos_ativos[alunos_ativos['SEXO'] == 'M'].shape[0]
    total_feminino = alunos_ativos[alunos_ativos['SEXO'] == 'F'].shape[0]
    total_transferidos = turma_df[turma_df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])].shape[0]
    total_matriculados = len(alunos_ativos)
    
    elements.append(Paragraph(f"TOTAIS: MASCULINO ({total_masculino}) FEMININO ({total_feminino}) - TRANSFERIDOS: {total_transferidos} - TOTAL MATRICULADOS: {total_matriculados}", ParagraphStyle(name='TotaisAlunos', fontSize=12, alignment=0)))
    elements.append(Spacer(1, 0.15 * inch))

    # Filtra apenas alunos ativos para a listagem
    turma_df = alunos_ativos

    # Prepara os dados da tabela
    data: list[list[Any]] = [['Nº', 'Nome', 'Nascimento', 'CPF', 'Transtorno']]
    
    # Ordena o DataFrame pelo nome do aluno
    turma_df = turma_df.sort_values('NOME DO ALUNO')
    
    for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
        nome = row['NOME DO ALUNO']
        nascimento = row['NASCIMENTO'].strftime('%d/%m/%Y') if row['NASCIMENTO'] else "Data não disponível"
        cpf = formatar_cpf(row['CPF'])
        transtorno = row['TRANSTORNO']
        
        data.append([
            row_num, 
            nome, 
            nascimento, 
            cpf, 
            transtorno
        ])  # type: ignore[arg-type]

    # Calcula as larguras das colunas dinamicamente
    max_width = 595.27 - 54
    col_widths = calcular_larguras_colunas(data, max_width)
    
    # Cria a tabela com as larguras calculadas
    table = Table(data, colWidths=col_widths)
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), white),
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

    # Distribuição por transtorno
    transtornos_data = []
    for transtorno in df['TRANSTORNO'].unique():
        transtorno_df = df[df['TRANSTORNO'] == transtorno]
        masculino = len(transtorno_df[transtorno_df['SEXO'] == 'M'])
        feminino = len(transtorno_df[transtorno_df['SEXO'] == 'F'])
        total = len(transtorno_df)
        transtornos_data.append([transtorno if transtorno else 'Sem transtorno', str(masculino), str(feminino), str(total)])

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

def buscar_tutores(cursor, escola_id=60):
    """Busca os tutores/cuidadores e demais funcionários da escola"""
    query = """
    SELECT 
        f.nome,
        f.cargo,
        f.turno,
        f.carga_horaria,
        f.vinculo
    FROM 
        funcionarios f
    WHERE 
        f.escola_id = %s
        AND f.cargo = 'Tutor/Cuidador'
    ORDER BY 
        f.nome
    """
    cursor.execute(query, (escola_id,))
    return cursor.fetchall()

def buscar_funcionarios_administrativos(cursor, escola_id=60):
    """Busca os funcionários administrativos da escola"""
    query = """
    SELECT 
        f.nome,
        f.cargo,
        f.turno,
        f.carga_horaria,
        f.vinculo
    FROM 
        funcionarios f
    WHERE 
        f.escola_id = %s
        AND f.cargo NOT IN ('Professor@', 'Tutor/Cuidador')
    ORDER BY 
        f.cargo, f.nome
    """
    cursor.execute(query, (escola_id,))
    return cursor.fetchall()

def gerar_tabela_tutores(elements, tutores, titulo):
    """Gera uma tabela de tutores/cuidadores para incluir no relatório"""
    styles = getSampleStyleSheet()
    
    if not tutores:
        elements.append(Paragraph("Nenhum tutor/cuidador encontrado.", styles["Normal"]))
        return

    # Adicionar título
    elements.append(Paragraph(titulo, styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Definir cabeçalhos
    headers = ["Nome", "Cargo", "Turno", "C.H.", "Vínculo"]
    
    # Preparar dados
    data: list[list[Any]] = [headers]
    
    for tutor in tutores:
        # Ajustar o cargo para mostrar "Tutor/Cuidador" corretamente
        cargo = tutor['cargo']
        if cargo == 'Tutor/Cuidador':
            cargo = 'Tutor/Cuidador'
        
        row = [
            tutor['nome'],
            cargo,
            tutor['turno'],
            tutor['carga_horaria'],
            tutor['vinculo']
        ]
        data.append(row)  # type: ignore[arg-type]
    
    # Criar tabela
    table = Table(data)
    cor_cabecalho = HexColor('#1B4F72')
    # Definir estilo
    style = TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), cor_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Corpo da tabela
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        
        # Linhas alternadas
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F0F0F0')]),
        
        # Bordas
        ('GRID', (0, 0), (-1, -1), 0.5, black),
        ('BOX', (0, 0), (-1, -1), 1, black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, black),
    ])
    
    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))

def gerar_tabela_funcionarios_administrativos(elements, funcionarios, titulo):
    """Gera uma tabela de funcionários administrativos para incluir no relatório"""
    styles = getSampleStyleSheet()
    
    if not funcionarios:
        elements.append(Paragraph("Nenhum funcionário administrativo encontrado.", styles["Normal"]))
        return

    # Adicionar título
    elements.append(Paragraph(titulo, styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Definir cabeçalhos
    headers = ["Nome", "Cargo", "Turno", "C.H.", "Vínculo"]
    
    # Preparar dados
    data: list[list[Any]] = [headers]
    
    for funcionario in funcionarios:
        row = [
            funcionario['nome'],
            funcionario['cargo'],
            funcionario['turno'],
            funcionario['carga_horaria'],
            funcionario['vinculo']
        ]
        data.append(row)  # type: ignore[arg-type]
    
    # Criar tabela
    table = Table(data)
    cor_cabecalho = HexColor('#1B4F72')
    
    # Definir estilo
    style = TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), cor_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Corpo da tabela
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Linhas alternadas
        ('BACKGROUND', (0, 2), (-1, 2), HexColor('#F0F0F0')),
        ('BACKGROUND', (0, 4), (-1, 4), HexColor('#F0F0F0')),
        
        # Bordas e grades
        ('GRID', (0, 0), (-1, -1), 0.5, black),
        ('BOX', (0, 0), (-1, -1), 1, black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, black),
    ])
    
    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))

def create_oficio_header(elements, cabecalho, figura_inferior, numero_oficio, ano):
    """Cria o cabeçalho do ofício no formato padrão"""
    # Adiciona o cabeçalho padrão
    elements.append(create_header(cabecalho, figura_inferior))
    elements.append(Spacer(1, 0.5 * inch))
    
    # Adiciona o número do ofício
    elements.append(Paragraph(f"Ofício nº {numero_oficio}/{ano}", ParagraphStyle(name='OficioNumero', fontSize=14, alignment=1)))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Adiciona a data em português usando util consolidado
    from utils.dates import formatar_data_extenso
    data_atual = datetime.datetime.now()
    data_formatada = formatar_data_extenso(data_atual)
    elements.append(Paragraph(f"Paço do Lumiar - MA, {data_formatada}", ParagraphStyle(name='Data', fontSize=12, alignment=2)))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Adiciona o destinatário
    elements.append(Paragraph("À", ParagraphStyle(name='Destinatario', fontSize=12, alignment=0)))
    elements.append(Paragraph("Secretaria Municipal de Educação – SEMED", ParagraphStyle(name='Destinatario', fontSize=12, alignment=0)))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Adiciona o assunto
    elements.append(Paragraph("Assunto: Atualização das informações da unidade escolar para o Mapeamento da Rede Municipal de Ensino 2025", 
                            ParagraphStyle(name='Assunto', fontSize=12, alignment=0)))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Adiciona o texto introdutório
    texto_intro = """
    Em atendimento à solicitação do setor de Mapeamento da SEMED, apresentamos as informações atualizadas 
    referentes à estrutura e funcionamento desta unidade escolar, contendo as seguintes informações por turma:
    """
    elements.append(Paragraph(texto_intro, ParagraphStyle(name='TextoIntro', fontSize=12, alignment=4)))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Adiciona os tópicos
    topicos = [
        "Turno;",
        "Nome do professor da turma;",
        "Quantitativo de alunos com a lista de matriculados por turma;",
        "Relação dos demais profissionais lotados na unidade escolar e seus devidos cargos."
    ]
    
    for topico in topicos:
        elements.append(Paragraph(f"• {topico}", ParagraphStyle(name='Topico', fontSize=12, alignment=4, leftIndent=20)))
    
    elements.append(Spacer(1, 0.2 * inch))
    
    # Adiciona o texto final
    texto_final = """
    Ressaltamos que todas as informações apresentadas foram verificadas e atualizadas, garantindo a precisão 
    e completude dos dados necessários para o atendimento pleno das necessidades da rede de ensino.
    """
    elements.append(Paragraph(texto_final, ParagraphStyle(name='TextoFinal', fontSize=12, alignment=4)))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Adiciona nota sobre os anexos
    nota_anexos = """
    As informações detalhadas solicitadas encontram-se nos documentos anexados a este ofício.
    """
    elements.append(Paragraph(nota_anexos, ParagraphStyle(name='NotaAnexos', fontSize=12, alignment=4)))
    elements.append(Spacer(1, 0.5 * inch))
    
    # Adiciona espaço para assinatura
    elements.append(Paragraph("Atenciosamente,", ParagraphStyle(name='Atenciosamente', fontSize=12, alignment=4)))
    elements.append(Spacer(1, 1.5 * inch))
    elements.append(Paragraph("________________________________________", ParagraphStyle(name='LinhaAssinatura', fontSize=12, alignment=1)))
    elements.append(Paragraph("Gestora Geral", ParagraphStyle(name='Cargo', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(PageBreak())

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
            if 'DATA_TRANSFERENCIA' in df.columns:
                df.loc[filtro_aluna, 'DATA_TRANSFERENCIA'] = None

    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    figura_superior = os.path.join(os.path.dirname(__file__), 'imagens', 'logosemed.png')
    figura_inferior = os.path.join(os.path.dirname(__file__), 'imagens', 'logopaco.png')

    # Cria o documento em modo retrato
    doc, buffer = create_pdf_buffer()
    elements = []

    # Adiciona o cabeçalho do ofício
    create_oficio_header(elements, cabecalho, figura_inferior, "049", "2025")
    
    # Adiciona o cabeçalho e título do primeiro anexo
    elements.append(create_header(cabecalho, figura_inferior))
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph("<b>ANEXO I - RELAÇÃO DE ALUNOS MATRICULADOS POR TURMA</b>", ParagraphStyle(name='AnexoTitulo', fontSize=14, alignment=1)))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Ordena as turmas por série e nome da turma
    turmas_ordenadas = sorted(df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']), 
                            key=lambda x: (x[0][0], x[0][1]))

    # Adiciona as tabelas de alunos
    primeira_tabela = True
    for (nome_serie, nome_turma, turno), turma_df in turmas_ordenadas:
        logger.info(f"{nome_serie}, {nome_turma}, {turno} - {turma_df.shape[0]}")
        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else ' '
        if turma_df.empty:
            logger.info(f"Nenhum aluno encontrado para a turma: {nome_serie}, {nome_turma}, {turno}")
            continue
        add_class_table(elements, turma_df, nome_serie, nome_turma, turno, nome_professor, figura_inferior, cabecalho, adicionar_cabecalho=not primeira_tabela)
        primeira_tabela = False

    # Busca os dados dos tutores e funcionários administrativos
    conn: Any = conectar_bd()
    escola_id = 60
    tutores = None
    funcionarios_admin = None
    if conn:
        cursor: Any = cast(Any, conn).cursor(dictionary=True)
        try:
            tutores = buscar_tutores(cursor, escola_id)
            funcionarios_admin = buscar_funcionarios_administrativos(cursor, escola_id)
        finally:
            try:
                cast(Any, cursor).close()
            except Exception:
                pass
            try:
                cast(Any, conn).close()
            except Exception:
                pass

    # Adiciona as tabelas de tutores e funcionários administrativos
    if tutores or funcionarios_admin:
        # Adiciona o cabeçalho antes das tabelas
        elements.append(create_header(cabecalho, figura_inferior))
        elements.append(Spacer(1, 0.25 * inch))
        elements.append(Paragraph("<b>ANEXO II - RELAÇÃO DE PROFISSIONAIS LOTADOS NA UNIDADE ESCOLAR</b>", ParagraphStyle(name='AnexoTitulo', fontSize=14, alignment=1)))
        elements.append(Spacer(1, 0.3 * inch))
        
        if tutores:
            gerar_tabela_tutores(elements, tutores, "TUTORES E CUIDADORES")
            elements.append(Spacer(1, 0.3 * inch))
        
        if funcionarios_admin:
            gerar_tabela_funcionarios_administrativos(elements, funcionarios_admin, "FUNCIONÁRIOS ADMINISTRATIVOS")
    
    # conexões já fechadas acima

    # Constrói o documento principal
    doc.build(elements)
    buffer.seek(0)

    # Gera o PDF da tabela de docentes
    buffer_docentes = gerar_tabela_docentes()
    buffer_docentes.seek(0)
    
    # Combina os PDFs
    from PyPDF2 import PdfReader, PdfWriter
    
    # Lê os PDFs
    conteudo_pdf = PdfReader(buffer)
    docentes_pdf = PdfReader(buffer_docentes)
    
    # Cria um novo PDF
    output = PdfWriter()
    
    # Adiciona o conteúdo em modo retrato
    for page in conteudo_pdf.pages:
        output.add_page(page)
    
    # Adiciona a tabela de docentes
    for page in docentes_pdf.pages:
        output.add_page(page)
    
    # Salva o PDF combinado
    output_buffer = io.BytesIO()
    output.write(output_buffer)
    output_buffer.seek(0)

    try:
        from gerarPDF import salvar_e_abrir_pdf as _salvar_helper
    except Exception:
        _salvar_helper = None

    saved_path = None
    try:
        if _salvar_helper:
            try:
                saved_path = _salvar_helper(output_buffer)
            except Exception:
                saved_path = None

        if not saved_path:
            import tempfile
            from utilitarios.gerenciador_documentos import salvar_documento_sistema
            from utilitarios.tipos_documentos import TIPO_LISTA_ATUALIZADA

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            try:
                tmp.write(output_buffer.getvalue())
                tmp.close()
                descricao = f"Lista Atualizada SEMED - {datetime.datetime.now().year}"
                try:
                    salvar_documento_sistema(tmp.name, TIPO_LISTA_ATUALIZADA, funcionario_id=1, finalidade='Secretaria', descricao=descricao)
                    saved_path = tmp.name
                except Exception:
                    try:
                        if _salvar_helper:
                            output_buffer.seek(0)
                            _salvar_helper(output_buffer)
                    except Exception:
                        pass
            finally:
                pass
    finally:
        try:
            output_buffer.close()
        except Exception:
            pass

# lista_atualizada()