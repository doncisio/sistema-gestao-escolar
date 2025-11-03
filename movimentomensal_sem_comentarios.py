from reportlab.platypus import Image, Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.colors import black, HexColor, Color
import datetime
import os
import pandas as pd
from biblio_editor import create_pdf_buffer, quebra_linha, get_nome_mes
from Lista_atualizada import fetch_student_data
from gerarPDF import salvar_e_abrir_pdf
from conexao import conectar_bd
import pymysql
import re
from reportlab.lib.pagesizes import landscape
from PyPDF2 import PdfReader, PdfWriter
import io


def add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior):
    data = [
        [Image(figura_inferior, width=2.5 * inch, height=0.5 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),    
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 3.75 * inch))
    elements.append(Paragraph(f"<b>MOVIMENTO MENSAL <br/><br/> {get_nome_mes(datetime.datetime.now().month)}</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1, leading=24)))
    elements.append(Spacer(1, 3.75 * inch))
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
    elements.append(PageBreak())

def contar_alunos_por_serie_sexo(df, data_referencia=None, tipo_contagem='atual', series_range='1_5'):
    if series_range == '1_5':
        contagem = {
            '1º Ano': {'M': 0, 'F': 0},
            '2º Ano': {'M': 0, 'F': 0},
            '3º Ano': {'M': 0, 'F': 0}, 
            '4º Ano': {'M': 0, 'F': 0},
            '5º Ano': {'M': 0, 'F': 0}
        }
    else:
        contagem = {
            '6º Ano A': {'M': 0, 'F': 0},
            '6º Ano B': {'M': 0, 'F': 0},
            '7º Ano': {'M': 0, 'F': 0},
            '8º Ano': {'M': 0, 'F': 0},
            '9º Ano': {'M': 0, 'F': 0}
        }
    
    for _, aluno in df.iterrows():
        serie = aluno['NOME_SERIE']
        turma = aluno.get('NOME_TURMA', '')
        sexo = aluno['SEXO']
        data_matricula = pd.to_datetime(aluno['DATA_MATRICULA']).date() if pd.notna(aluno['DATA_MATRICULA']) else None
        status = aluno['SITUAÇÃO']

        if serie == '6º Ano':
            if 'A' in turma:
                serie = '6º Ano A'
            elif 'B' in turma:
                serie = '6º Ano B'

        if serie in contagem and sexo in ['M', 'F']:
            if tipo_contagem == 'inicial':
                if data_matricula and data_matricula < data_referencia:
                    contagem[serie][sexo] += 1
            else:
                if status == 'Ativo':
                    contagem[serie][sexo] += 1
    
    return contagem

def contar_movimentacao_mensal(cursor, ano_letivo_id, mes, serie):
    query = """
    SELECT 
        hm.status_novo as status,
        COUNT(CASE WHEN a.sexo = 'M' THEN 1 END) as total_m,
        COUNT(CASE WHEN a.sexo = 'F' THEN 1 END) as total_f
    FROM historico_matricula hm
    JOIN matriculas m ON hm.matricula_id = m.id
    JOIN alunos a ON m.aluno_id = a.id
    JOIN turmas t ON m.turma_id = t.id
    JOIN serie s ON t.serie_id = s.id
    WHERE 
        m.ano_letivo_id = %s
        AND hm.data_mudanca <= LAST_DAY(DATE(CONCAT(YEAR(CURDATE()), '-', %s, '-01')))
        AND CONCAT(s.nome, ' ', t.nome) = %s
        AND hm.status_novo IN ('Evadido', 'Transferido')
        AND NOT EXISTS (
            SELECT 1 FROM historico_matricula hm2 
            WHERE hm2.matricula_id = hm.matricula_id 
            AND hm2.data_mudanca > hm.data_mudanca
            AND hm2.status_novo = 'Ativo'
        )
    GROUP BY hm.status_novo;
    """
    cursor.execute(query, (ano_letivo_id, mes, serie))
    return cursor.fetchall()

def contar_aprovacoes_reprovacoes(cursor, ano_letivo_id, serie):
    query = """
    WITH medias_alunos AS (
        SELECT 
            a.id as aluno_id,
            a.sexo,
            s.nome as serie,
            AVG(af.nota) as media_final,
            m.id as matricula_id
        FROM alunos a
        JOIN matriculas m ON a.id = m.aluno_id
        JOIN turmas t ON m.turma_id = t.id
        JOIN serie s ON t.serie_id = s.id
        JOIN avaliacao_final af ON a.id = af.aluno_id
        WHERE 
            m.ano_letivo_id = %s
            AND CONCAT(s.nome, ' ', t.nome) = %s
            AND NOT EXISTS (
                SELECT 1 FROM historico_matricula hm 
                WHERE hm.matricula_id = m.id 
                AND hm.status_novo IN ('Transferido', 'Evadido')
            )
        GROUP BY a.id, a.sexo, s.nome, m.id
    )
    SELECT 
        CASE WHEN media_final >= 6 THEN 'Aprovado' ELSE 'Reprovado' END as situacao,
        COUNT(CASE WHEN sexo = 'M' THEN 1 END) as total_m,
        COUNT(CASE WHEN sexo = 'F' THEN 1 END) as total_f
    FROM medias_alunos
    GROUP BY CASE WHEN media_final >= 6 THEN 'Aprovado' ELSE 'Reprovado' END;
    """
    cursor.execute(query, (ano_letivo_id, serie))
    return cursor.fetchall()

def contar_transferencias_recebidas(cursor, ano_letivo_id, mes, series):
    query = """
    SELECT 
        a.nome,
        a.sexo,
        s.nome as serie,
        t.nome as turma,
        m.status,
        m.data_matricula
    FROM matriculas m
    JOIN alunos a ON m.aluno_id = a.id
    JOIN turmas t ON m.turma_id = t.id
    JOIN serie s ON t.serie_id = s.id
    JOIN anosletivos al ON m.ano_letivo_id = al.id
    WHERE 
        m.ano_letivo_id = %s
        AND MONTH(m.data_matricula) = %s
        AND YEAR(m.data_matricula) = YEAR(CURRENT_DATE())
        AND (
            (t.turno = 'Matutino' AND s.nome IN ('1º Ano', '2º Ano', '3º Ano', '4º Ano', '5º Ano'))
            OR 
            (t.turno = 'Vespertino' AND s.nome IN ('6º Ano', '7º Ano', '8º Ano', '9º Ano'))
        )
    """
    
    
    cursor.execute(query, (ano_letivo_id, mes))
    resultados = cursor.fetchall()
    
    
    df = pd.DataFrame(resultados)
    
    transferencias = {serie: {'M': 0, 'F': 0} for serie in series}
    
    for _, row in df.iterrows():
        serie = row['serie']
        turma = row['turma']
        
        if serie == '6º Ano':
            serie_turma = f"{serie} {turma}"
        else:
            serie_turma = serie
            
        if serie_turma in transferencias:
            if row['sexo'] == 'M':
                transferencias[serie_turma]['M'] += 1
            elif row['sexo'] == 'F':
                transferencias[serie_turma]['F'] += 1
    
    
    return transferencias

def buscar_dias_letivos(cursor, ano_letivo, mes):
    query = """
    SELECT dias_letivos
    FROM dias_letivos_mensais
    WHERE ano_letivo = %s AND mes = %s
    """
    cursor.execute(query, (ano_letivo, mes))
    resultado = cursor.fetchone()
    return resultado['dias_letivos'] if resultado else "---"

def buscar_corpo_docente_1_5(cursor, escola_id=60):
    """Busca os professores do 1º ao 5º ano"""
    query = """
    SELECT 
        f.id,
        f.nome,
        f.matricula,
        f.data_admissao,
        f.cargo,
        f.funcao,
        f.turno,
        f.carga_horaria,
        f.vinculo,
        f.polivalente,
        GROUP_CONCAT(DISTINCT d.nome SEPARATOR ', ') as disciplinas,
        CASE 
            WHEN f.polivalente = 'sim' THEN 
                CASE 
                    WHEN f.turma IS NOT NULL THEN 
                        (SELECT CONCAT(s.nome, ' ', t.nome) 
                         FROM turmas t 
                         JOIN serie s ON t.serie_id = s.id 
                         WHERE t.id = f.turma)
                    ELSE 'Volante (Todas as Turmas)'
                END
            ELSE 
                GROUP_CONCAT(DISTINCT CONCAT(s.nome, ' ', t.nome) SEPARATOR ', ')
        END AS turmas,
        (SELECT l.motivo FROM licencas l WHERE l.funcionario_id = f.id 
         AND CURRENT_DATE() BETWEEN l.data_inicio AND l.data_fim LIMIT 1) as licenca_motivo,
        (SELECT CONCAT(DATE_FORMAT(l.data_inicio, '%d/%m/%Y'), ' a ', 
                      DATE_FORMAT(l.data_fim, '%d/%m/%Y')) 
         FROM licencas l WHERE l.funcionario_id = f.id 
         AND CURRENT_DATE() BETWEEN l.data_inicio AND l.data_fim LIMIT 1) as licenca_periodo
    FROM 
        funcionarios f
    LEFT JOIN 
        funcionario_disciplinas fd ON f.id = fd.funcionario_id
    LEFT JOIN 
        disciplinas d ON fd.disciplina_id = d.id
    LEFT JOIN 
        funcionario_disciplinas ft ON f.id = ft.funcionario_id
    LEFT JOIN 
        turmas t ON ft.turma_id = t.id
    LEFT JOIN 
        serie s ON t.serie_id = s.id
    WHERE 
        f.escola_id = %s
        AND f.cargo = 'Professor@'
        AND (
            s.nome IN ('1º Ano', '2º Ano', '3º Ano', '4º Ano', '5º Ano')
            OR (f.polivalente = 'sim' AND s.nome IS NULL)
            OR (
                f.polivalente = 'sim' AND f.turma IS NOT NULL AND EXISTS (
                    SELECT 1 FROM turmas t2 
                    JOIN serie s2 ON t2.serie_id = s2.id 
                    WHERE t2.id = f.turma AND s2.nome IN ('1º Ano', '2º Ano', '3º Ano', '4º Ano', '5º Ano')
                )
            )
        )
    GROUP BY 
        f.id
    ORDER BY 
        f.nome
    """
    cursor.execute(query, (escola_id,))
    return cursor.fetchall()

def buscar_corpo_docente_6_9(cursor, escola_id=60):
    """Busca os professores do 6º ao 9º ano"""
    cursor.execute("""
        SELECT l.*, f.nome 
        FROM licencas l 
        JOIN funcionarios f ON l.funcionario_id = f.id 
        WHERE f.nome LIKE '%Ana Patrícia%'
    """)
    licenca = cursor.fetchone()
    query = """
    SELECT 
        f.id,
        f.nome,
        f.matricula,
        f.data_admissao,
        f.cargo,
        f.funcao,
        f.turno,
        f.carga_horaria,
        f.vinculo,
        f.polivalente,
        GROUP_CONCAT(DISTINCT d.nome SEPARATOR ', ') as disciplinas,
        CASE 
            WHEN f.polivalente = 'sim' THEN 
                CASE 
                    WHEN f.turma IS NOT NULL THEN 
                        (SELECT CONCAT(s.nome, ' ', t.nome) 
                         FROM turmas t 
                         JOIN serie s ON t.serie_id = s.id 
                         WHERE t.id = f.turma)
                    ELSE 'Volante (Todas as Turmas)'
                END
            ELSE 
                GROUP_CONCAT(DISTINCT CONCAT(s.nome, ' ', t.nome) SEPARATOR ', ')
        END AS turmas,
        (SELECT l.motivo FROM licencas l WHERE l.funcionario_id = f.id 
         AND STR_TO_DATE('23/04/2025', '%d/%m/%Y') BETWEEN l.data_inicio AND l.data_fim LIMIT 1) as licenca_motivo,
        (SELECT CONCAT(DATE_FORMAT(l.data_inicio, '%d/%m/%Y'), ' a ', 
                      DATE_FORMAT(l.data_fim, '%d/%m/%Y')) 
         FROM licencas l WHERE l.funcionario_id = f.id 
         AND STR_TO_DATE('23/04/2025', '%d/%m/%Y') BETWEEN l.data_inicio AND l.data_fim LIMIT 1) as licenca_periodo
    FROM 
        funcionarios f
    LEFT JOIN 
        funcionario_disciplinas fd ON f.id = fd.funcionario_id
    LEFT JOIN 
        disciplinas d ON fd.disciplina_id = d.id
    LEFT JOIN 
        funcionario_disciplinas ft ON f.id = ft.funcionario_id
    LEFT JOIN 
        turmas t ON ft.turma_id = t.id
    LEFT JOIN 
        serie s ON t.serie_id = s.id
    WHERE 
        f.escola_id = %s
        AND f.cargo = 'Professor@'
        AND (
            s.nome IN ('6º Ano', '7º Ano', '8º Ano', '9º Ano')
            OR (f.polivalente = 'não' AND s.nome IS NULL)
            OR (
                f.polivalente = 'não' AND f.turma IS NOT NULL AND EXISTS (
                    SELECT 1 FROM turmas t2 
                    JOIN serie s2 ON t2.serie_id = s2.id 
                    WHERE t2.id = f.turma AND s2.nome IN ('6º Ano', '7º Ano', '8º Ano', '9º Ano')
                )
            )
        )
    GROUP BY 
        f.id
    ORDER BY 
        f.nome
    """
    cursor.execute(query, (escola_id,))
    professores = cursor.fetchall()
    
    return professores

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
    funcionarios = cursor.fetchall()
    
    
    return funcionarios

def gerar_tabela_corpo_docente(elements, professores, titulo):
    """Gera uma tabela de corpo docente para incluir no relatório"""
    styles = getSampleStyleSheet()
    style_cell = ParagraphStyle(name='Cell', fontSize=8, alignment=1) 
    style_cell_left = ParagraphStyle(name='CellLeft', fontSize=8, alignment=0) 

    if not professores:
        elements.append(Paragraph("Nenhum professor encontrado.", styles["Normal"]))
        return
    
    if titulo:
        elements.append(Paragraph(titulo, styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))
    
    headers = ["Nº", "NOME DO SERVIDOR", "CARGO", "SITUAÇÃO FUNCIONAL", "HABILITAÇÃO", "CLASSE REGENTE", "LICENÇA"]
    
    data = [headers]
    
    for i, professor in enumerate(professores, 1):
        licenca_info = ""
        if professor.get('licenca_motivo'):
            licenca_info = professor['licenca_motivo']
        
        habilitacao = ""
        classe_regente_obj = Paragraph("---", style_cell) 

        if 'Kevin Anderson' in professor['nome']:
            habilitacao = "INTÉRPRETE DE LIBRAS"
        elif professor['polivalente'] == 'sim':
            habilitacao = "Polivalente"
            classe_regente_str = professor.get('turmas') or "---"
            if "Volante (Todas as Turmas)" in classe_regente_str:
                 classe_regente_str = "1º a 5º Ano"
            classe_regente_obj = Paragraph(classe_regente_str, style_cell)
        else:
            habilitacao = professor.get('disciplinas') or "---"
            turmas_str = professor.get('turmas')
            
            if turmas_str:
                turmas_list = [t.strip() for t in turmas_str.split(',') if t.strip()]
                parsed_turmas = []
                for t_nome in turmas_list:
                    parsed = parse_turma_nome(t_nome)
                    if parsed != (None, None):
                        parsed_turmas.append((t_nome, parsed))
                
                parsed_turmas.sort(key=lambda x: x[1])
                nomes_turmas_ordenadas = [t[0] for t in parsed_turmas]

                if len(nomes_turmas_ordenadas) > 1:
                    is_sequential = True
                    for j in range(len(parsed_turmas) - 1):
                        ano_atual, letra_atual = parsed_turmas[j][1]
                        ano_prox, letra_prox = parsed_turmas[j+1][1]
                        if not ((ano_prox == ano_atual + 1 and letra_prox == -1 and letra_atual == -1) or \
                                (ano_prox == ano_atual and letra_prox == letra_atual + 1)):
                            is_sequential = False
                            break
                            
                    if is_sequential:
                        primeira_turma_nome = nomes_turmas_ordenadas[0]
                        ultima_turma_nome = nomes_turmas_ordenadas[-1]
                        match_ultima = re.match(r'(\d+)º?\s*Ano', ultima_turma_nome.strip(), re.IGNORECASE)
                        if match_ultima:
                             classe_regente_str = f"{primeira_turma_nome.split(' ')[0]} a {match_ultima.group(1)}º Ano"
                        else:
                            classe_regente_str = f"{primeira_turma_nome} a {ultima_turma_nome}"
                        classe_regente_obj = Paragraph(classe_regente_str, style_cell)
                    else:
                        if len(nomes_turmas_ordenadas) > 1:
                            prefixo = ", ".join(nomes_turmas_ordenadas[:-1])
                            lista_completa_str = f"{prefixo} e {nomes_turmas_ordenadas[-1]}"
                        else:
                            lista_completa_str = nomes_turmas_ordenadas[0]

                        partes = re.split(r'(?:, | e )', lista_completa_str)
                        
                        linhas_formatadas = []
                        for k in range(0, len(partes), 2):
                            par = partes[k:k+2]
                            if k + len(par) == len(partes) and len(par) > 1:
                                separador = " e "
                            elif len(par) > 1:
                                separador = ", "
                            else: 
                                separador = ""
                            
                            linhas_formatadas.append(separador.join(par))

                        classe_regente_str = "<br/>".join(linhas_formatadas)
                        classe_regente_obj = Paragraph(classe_regente_str, style_cell)

                elif len(nomes_turmas_ordenadas) == 1:
                     classe_regente_obj = Paragraph(nomes_turmas_ordenadas[0], style_cell)
                else:
                    classe_regente_obj = Paragraph("---", style_cell) 
            else:
                classe_regente_obj = Paragraph("---", style_cell)

        row = [
            Paragraph(str(i), style_cell),
            Paragraph(professor['nome'], style_cell_left), 
            Paragraph(professor['cargo'], style_cell),
            Paragraph(professor['vinculo'], style_cell),
            Paragraph(habilitacao, style_cell),
            classe_regente_obj, 
            Paragraph(licenca_info or "---", style_cell)
        ]
        data.append(row)
    
    col_widths = [0.4*inch, 2.5*inch, 1*inch, 1.5*inch, 1.2*inch, 1.2*inch, 1.4*inch]
    
    table = Table(data, colWidths=col_widths)
    cor_cabecalho = HexColor('#1B4F72')
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), cor_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F0F0F0')]),
        
        ('GRID', (0, 0), (-1, -1), 0.5, black),
        ('BOX', (0, 0), (-1, -1), 1, black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, black),
    ])
    
    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))

def gerar_tabela_tutores(elements, tutores, titulo):
    """Gera uma tabela de tutores/cuidadores para incluir no relatório"""
    styles = getSampleStyleSheet()
    
    if not tutores:
        elements.append(Paragraph("Nenhum tutor/cuidador encontrado.", styles["Normal"]))
        return

    elements.append(Paragraph(titulo, styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))
    
    headers = ["Nome", "Cargo", "Turno", "C.H.", "Vínculo"]
    
    data = [headers]
    
    for tutor in tutores:
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
        data.append(row)
    
    table = Table(data)
    cor_cabecalho = HexColor('#1B4F72')
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), cor_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F0F0F0')]),
        
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

    elements.append(Paragraph(titulo, styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))
    
    headers = ["Nome", "Cargo", "Turno", "C.H.", "Vínculo"]
    
    data = [headers]
    
    for funcionario in funcionarios:
        row = [
            funcionario['nome'],
            funcionario['cargo'],
            funcionario['turno'],
            funcionario['carga_horaria'],
            funcionario['vinculo']
        ]
        data.append(row)
    
    
    table = Table(data)
    cor_cabecalho = HexColor('#1B4F72')
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), cor_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        ('BACKGROUND', (0, 2), (-1, 2), HexColor('#F0F0F0')),
        ('BACKGROUND', (0, 4), (-1, 4), HexColor('#F0F0F0')),
        
        ('GRID', (0, 0), (-1, -1), 0.5, black),
        ('BOX', (0, 0), (-1, -1), 1, black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, black),
    ])
    
    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))

def relatorio_movimentacao_mensal():
    from reportlab.lib.pagesizes import letter, landscape
    from PyPDF2 import PdfReader, PdfWriter
    import io
    
    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    figura_superior = os.path.join(os.path.dirname(__file__), 'logosemed.png')
    figura_inferior = os.path.join(os.path.dirname(__file__), 'logopaco.png')
    
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    
    professores_1_5 = buscar_corpo_docente_1_5(cursor, escola_id=60)
    professores_6_9 = buscar_corpo_docente_6_9(cursor, escola_id=60)
    tutores = buscar_tutores(cursor, escola_id=60)
    funcionarios_admin = buscar_funcionarios_administrativos(cursor, escola_id=60)
    
    cursor.close()
    conn.close()
    
    doc_capa, buffer_capa = create_pdf_buffer()
    elements_capa = []
    add_cover_page(doc_capa, elements_capa, cabecalho, figura_superior, figura_inferior)
    doc_capa.build(elements_capa)
    buffer_capa.seek(0)
    
    doc_relatorio_1_5, buffer_relatorio_1_5 = create_pdf_buffer()
    elements_relatorio_1_5 = []
    gerar_relatorio_1_5(elements_relatorio_1_5, cabecalho, figura_inferior)
    doc_relatorio_1_5.build(elements_relatorio_1_5)
    buffer_relatorio_1_5.seek(0)
    
    doc_docente_1_5, buffer_docente_1_5 = create_pdf_buffer(pagesize=landscape(letter))
    elements_docente_1_5 = []
    
    data = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[7 * inch])  
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements_docente_1_5.append(table)
    elements_docente_1_5.append(Spacer(1, 0.3 * inch))
    
    elements_docente_1_5.append(Paragraph("CORPO DOCENTE - 1º ao 5º ANO - TURNO MATUTINO", ParagraphStyle(name='Heading2')))
    elements_docente_1_5.append(Spacer(1, 0.2 * inch))
    
    gerar_tabela_corpo_docente(elements_docente_1_5, professores_1_5, "")
    
    elements_docente_1_5.append(Spacer(1, 0.5 * inch))
    gerar_tabela_funcionarios_administrativos(elements_docente_1_5, funcionarios_admin, "FUNCIONÁRIOS ADMINISTRATIVOS")
    
    doc_docente_1_5.build(elements_docente_1_5)
    buffer_docente_1_5.seek(0)
    
    doc_relatorio_6_9, buffer_relatorio_6_9 = create_pdf_buffer()
    elements_relatorio_6_9 = []
    gerar_relatorio_6_9(elements_relatorio_6_9, cabecalho, figura_inferior)
    doc_relatorio_6_9.build(elements_relatorio_6_9)
    buffer_relatorio_6_9.seek(0)
    
    doc_docente_6_9, buffer_docente_6_9 = create_pdf_buffer(pagesize=landscape(letter))
    elements_docente_6_9 = []
    
    elements_docente_6_9.append(table)
    elements_docente_6_9.append(Spacer(1, 0.3 * inch))
    
    elements_docente_6_9.append(Paragraph("CORPO DOCENTE - 6º ao 9º ANO - TURNO VESPERTINO", ParagraphStyle(name='Heading2')))
    elements_docente_6_9.append(Spacer(1, 0.2 * inch))
    
    gerar_tabela_corpo_docente(elements_docente_6_9, professores_6_9, "")
    
    elements_docente_6_9.append(Spacer(1, 0.5 * inch))
    gerar_tabela_tutores(elements_docente_6_9, tutores, "TUTORES E CUIDADORES")
    
    doc_docente_6_9.build(elements_docente_6_9)
    buffer_docente_6_9.seek(0)
    
    output = PdfWriter()
    
    capa_reader = PdfReader(buffer_capa)
    for i in range(len(capa_reader.pages)):
        output.add_page(capa_reader.pages[i])
    
    relatorio_1_5_reader = PdfReader(buffer_relatorio_1_5)
    for i in range(len(relatorio_1_5_reader.pages)):
        output.add_page(relatorio_1_5_reader.pages[i])
    
    docente_1_5_reader = PdfReader(buffer_docente_1_5)
    for i in range(len(docente_1_5_reader.pages)):
        output.add_page(docente_1_5_reader.pages[i])
        
    relatorio_6_9_reader = PdfReader(buffer_relatorio_6_9)
    for i in range(len(relatorio_6_9_reader.pages)):
        output.add_page(relatorio_6_9_reader.pages[i])
    
    docente_6_9_reader = PdfReader(buffer_docente_6_9)
    for i in range(len(docente_6_9_reader.pages)):
        output.add_page(docente_6_9_reader.pages[i])
    
    buffer_final = io.BytesIO()
    output.write(buffer_final)
    buffer_final.seek(0)
    
    salvar_e_abrir_pdf(buffer_final)

def gerar_relatorio_1_5(elements, cabecalho, figura_inferior):
    ano_letivo = 2025
    
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, data_inicio, data_fim FROM anosletivos WHERE ano_letivo = %s", (ano_letivo,))
    datas_ano_letivo = cursor.fetchone()
    
    if not datas_ano_letivo:
        print("Ano letivo não encontrado")
        return
        
    data_inicio = datas_ano_letivo['data_inicio']
    data_fim = datas_ano_letivo['data_fim']
    ano_letivo_id = datas_ano_letivo['id']
    mes_atual = datetime.datetime.now().month
    
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        return

    df = pd.DataFrame(dados_aluno)


    estilo_titulo = ParagraphStyle(
        name='EstiloTitulo',
        fontSize=12,
        alignment=1,
        spaceAfter=10,
        spaceBefore=10,
        leading=16
    )
    
    estilo_info = ParagraphStyle(
        name='EstiloInfo',
        fontSize=10,
        alignment=0,
        spaceAfter=5,
        leading=14
    )
    
    data = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho), estilo_titulo)]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.2 * inch))
    
    elements.append(Paragraph("<b>MOVIMENTO MENSAL – ENSINO FUNDAMENTAL</b>", estilo_titulo))
    elements.append(Paragraph("<b>1º ao 5º ANO</b>", estilo_titulo))
    elements.append(Spacer(1, 0.2 * inch))
    
    info_data = [
        [Paragraph(f"<b>MÊS:</b> {get_nome_mes(datetime.datetime.now().month)}", estilo_info), 
         Paragraph(f"<b>ANO:</b> {datetime.datetime.now().year}", estilo_info)]
    ]
    info_table = Table(info_data, colWidths=[4*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(info_table)
    
    elements.append(Paragraph("<b>UNIDADE DE ENSINO:</b> E. M. PROFESSORA NADIR NASCIMENTO MORAES.", estilo_info))
    elements.append(Paragraph("<b>ENDEREÇO:</b> RUA 65 QD 12 S/N – Conjunto Maiobão", estilo_info))
    elements.append(Paragraph("<b>MUNICÍPIO:</b> Paço do Lumiar – MA", estilo_info))
    elements.append(Paragraph("<b>TURNO:</b> MATUTINO", estilo_info))
    
    dias_letivos = buscar_dias_letivos(cursor, ano_letivo, mes_atual)
    
    info_salas_data = [
        [Paragraph("<b>Nº DE SALA DE AULA DO PRÉDIO:</b> 5", estilo_info),
         Paragraph(f"<b>Nº DE DIAS LETIVOS:</b> {dias_letivos}", estilo_info)]
    ]
    info_salas_table = Table(info_salas_data, colWidths=[4*inch, 4*inch])
    info_salas_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(info_salas_table)
    
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("<b>DEPENDÊNCIA ADMINISTRATIVA DO PRÉDIO</b>", estilo_info))
    
    checkbox_data = [
        ['( ) Estadual', '(X) Municipal', '( ) Particular', '( ) Alugado']
    ]
    checkbox_table = Table(checkbox_data, colWidths=[2*inch]*4)
    checkbox_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
    ]))
    elements.append(checkbox_table)
    
    elements.append(Spacer(1, 0.5 * inch))
    
    contagem_inicial = contar_alunos_por_serie_sexo(df, data_inicio, 'inicial')
    total_m_inicial = sum(serie['M'] for serie in contagem_inicial.values())
    total_f_inicial = sum(serie['F'] for serie in contagem_inicial.values())
    total_geral_inicial = total_m_inicial + total_f_inicial
    
    contagem_atual = contar_alunos_por_serie_sexo(df)
    total_m_atual = sum(serie['M'] for serie in contagem_atual.values())
    total_f_atual = sum(serie['F'] for serie in contagem_atual.values())
    total_geral_atual = total_m_atual + total_f_atual
    
    series = ['1º Ano', '2º Ano', '3º Ano', '4º Ano', '5º Ano']
    dados_movimentacao = {serie: contar_movimentacao_mensal(cursor, ano_letivo_id, mes_atual, serie) for serie in series}
    
    transferencias_recebidas = contar_transferencias_recebidas(cursor, ano_letivo_id, mes_atual, series)
    
    
    hoje = datetime.date.today()
    if hoje > data_fim:
        dados_aprovacao = {serie: contar_aprovacoes_reprovacoes(cursor, ano_letivo_id, serie) for serie in series}
    
    evadidos = {serie: {'M': 0, 'F': 0} for serie in series}
    transferidos = {serie: {'M': 0, 'F': 0} for serie in series}
    
    for serie, movimentacao in dados_movimentacao.items():
        for registro in movimentacao:
            if registro['status'] == 'Evadido':
                evadidos[serie]['M'] = registro['total_m']
                evadidos[serie]['F'] = registro['total_f']
            elif registro['status'] == 'Transferido':
                transferidos[serie]['M'] = registro['total_m']
                transferidos[serie]['F'] = registro['total_f']
    
    transferidos_dashboard = contar_transferencias_por_serie_sexo(df, series)
    
    
    data = [[quebra_linha("ESPECIFICAÇÃO"), 'Série'] + ['']*9 + ['Total','Total', 'Total Geral'],
            ['', '1º Ano','1º Ano', '2º Ano','2º Ano','3º Ano','3º Ano','4º Ano','4º Ano','5º Ano','5º Ano']+['']*3,
            ['']+['M', 'F']*6+[''],
            [quebra_linha("MATRÍCULA INICIAL")] + 
            [contagem_inicial['1º Ano']['M'], contagem_inicial['1º Ano']['F'],
             contagem_inicial['2º Ano']['M'], contagem_inicial['2º Ano']['F'],
             contagem_inicial['3º Ano']['M'], contagem_inicial['3º Ano']['F'],
             contagem_inicial['4º Ano']['M'], contagem_inicial['4º Ano']['F'],
             contagem_inicial['5º Ano']['M'], contagem_inicial['5º Ano']['F'],
             total_m_inicial, total_f_inicial, total_geral_inicial],
            [quebra_linha("MATRÍCULA ATUAL")] + 
            [contagem_atual['1º Ano']['M'], contagem_atual['1º Ano']['F'],
             contagem_atual['2º Ano']['M'], contagem_atual['2º Ano']['F'],
             contagem_atual['3º Ano']['M'], contagem_atual['3º Ano']['F'],
             contagem_atual['4º Ano']['M'], contagem_atual['4º Ano']['F'],
             contagem_atual['5º Ano']['M'], contagem_atual['5º Ano']['F'],
             total_m_atual, total_f_atual, total_geral_atual],
            [quebra_linha("TRANSFERÊNCIAS RECEBIDAS")] + 
            [transferencias_recebidas['1º Ano']['M'], transferencias_recebidas['1º Ano']['F'],
             transferencias_recebidas['2º Ano']['M'], transferencias_recebidas['2º Ano']['F'],
             transferencias_recebidas['3º Ano']['M'], transferencias_recebidas['3º Ano']['F'],
             transferencias_recebidas['4º Ano']['M'], transferencias_recebidas['4º Ano']['F'],
             transferencias_recebidas['5º Ano']['M'], transferencias_recebidas['5º Ano']['F'],
             sum(serie['M'] for serie in transferencias_recebidas.values()),
             sum(serie['F'] for serie in transferencias_recebidas.values()),
             sum(serie['M'] + serie['F'] for serie in transferencias_recebidas.values())],
            [quebra_linha("TRANSFERÊNCIAS EXPEDIDAS")] + 
            [transferidos_dashboard['1º Ano']['M'], transferidos_dashboard['1º Ano']['F'],
             transferidos_dashboard['2º Ano']['M'], transferidos_dashboard['2º Ano']['F'],
             transferidos_dashboard['3º Ano']['M'], transferidos_dashboard['3º Ano']['F'],
             transferidos_dashboard['4º Ano']['M'], transferidos_dashboard['4º Ano']['F'],
             transferidos_dashboard['5º Ano']['M'], transferidos_dashboard['5º Ano']['F'],
             sum(serie['M'] for serie in transferidos_dashboard.values()),
             sum(serie['F'] for serie in transferidos_dashboard.values()),
             sum(serie['M'] + serie['F'] for serie in transferidos_dashboard.values())],
            [quebra_linha("ALUNOS EVADIDOS")] + 
            [evadidos['1º Ano']['M'], evadidos['1º Ano']['F'],
             evadidos['2º Ano']['M'], evadidos['2º Ano']['F'],
             evadidos['3º Ano']['M'], evadidos['3º Ano']['F'],
             evadidos['4º Ano']['M'], evadidos['4º Ano']['F'],
             evadidos['5º Ano']['M'], evadidos['5º Ano']['F'],
             sum(serie['M'] for serie in evadidos.values()),
             sum(serie['F'] for serie in evadidos.values()),
             sum(serie['M'] + serie['F'] for serie in evadidos.values())],
    ]
    
    if hoje > data_fim and 'dados_aprovacao' in locals():
        aprovados = {serie: {'M': 0, 'F': 0} for serie in series}
        reprovados = {serie: {'M': 0, 'F': 0} for serie in series}
        
        for serie, resultados in dados_aprovacao.items():
            for resultado in resultados:
                if resultado['situacao'] == 'Aprovado':
                    aprovados[serie]['M'] = resultado['total_m']
                    aprovados[serie]['F'] = resultado['total_f']
                else:
                    reprovados[serie]['M'] = resultado['total_m']
                    reprovados[serie]['F'] = resultado['total_f']
        
        data.extend([
            [quebra_linha("ALUNOS APROVADOS")] + 
            [aprovados['1º Ano']['M'], aprovados['1º Ano']['F'],
             aprovados['2º Ano']['M'], aprovados['2º Ano']['F'],
             aprovados['3º Ano']['M'], aprovados['3º Ano']['F'],
             aprovados['4º Ano']['M'], aprovados['4º Ano']['F'],
             aprovados['5º Ano']['M'], aprovados['5º Ano']['F'],
             sum(serie['M'] for serie in aprovados.values()),
             sum(serie['F'] for serie in aprovados.values()),
             sum(serie['M'] + serie['F'] for serie in aprovados.values())],
            [quebra_linha("ALUNOS REPROVADOS")] + 
            [reprovados['1º Ano']['M'], reprovados['1º Ano']['F'],
             reprovados['2º Ano']['M'], reprovados['2º Ano']['F'],
             reprovados['3º Ano']['M'], reprovados['3º Ano']['F'],
             reprovados['4º Ano']['M'], reprovados['4º Ano']['F'],
             reprovados['5º Ano']['M'], reprovados['5º Ano']['F'],
             sum(serie['M'] for serie in reprovados.values()),
             sum(serie['F'] for serie in reprovados.values()),
             sum(serie['M'] + serie['F'] for serie in reprovados.values())]
        ])
    else:
        data.extend([
            [quebra_linha("ALUNOS APROVADOS")] + ["--"]*13,
            [quebra_linha("ALUNOS REPROVADOS")] + ["--"]*13
        ])
    
    query_turmas = """
    SELECT s.nome as serie, COUNT(DISTINCT t.id) as total_turmas
    FROM turmas t
    JOIN serie s ON t.serie_id = s.id
    WHERE t.ano_letivo_id = %s
    GROUP BY s.nome
    """
    cursor.execute(query_turmas, (ano_letivo_id,))
    turmas = {r['serie']: r['total_turmas'] for r in cursor.fetchall()}
    
    turmas_por_serie = []
    total_turmas = 0
    for serie in series:
        num_turmas = turmas.get(serie, 0)
        turmas_por_serie.extend([num_turmas, num_turmas])  
        total_turmas += num_turmas
    
    data.append([quebra_linha("Nº de TURMAS")] + 
                turmas_por_serie +  
                [total_turmas, total_turmas, total_turmas])  
    
    colWidths = [2.5*inch] + [0.35*inch]*12 + [inch]
    table = Table(data, colWidths=colWidths)
    
    cor_cabecalho = HexColor('#1B4F72')
    cor_subcabecalho = HexColor('#2874A6')
    cor_texto = black
    cor_linha_clara = Color(0.95, 0.95, 0.95)
    cor_borda = black
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 2), cor_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 2), 'white'),
        ('FONTNAME', (0, 0), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 2), 11),
        
        ('FONTNAME', (0, 3), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 3), (-1, -1), 10),
        ('TEXTCOLOR', (0, 3), (-1, -1), cor_texto),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        ('BACKGROUND', (0, 4), (-1, 4), cor_linha_clara),
        ('BACKGROUND', (0, 6), (-1, 6), cor_linha_clara),
        ('BACKGROUND', (0, 8), (-1, 8), cor_linha_clara),
        ('BACKGROUND', (0, 10), (-1, 10), cor_linha_clara),
        
        ('GRID', (0, 0), (-1, -1), 0.5, cor_borda),
        ('BOX', (0, 0), (-1, -1), 1, cor_borda),
        ('LINEBELOW', (0, 2), (-1, 2), 1, cor_borda),
        
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        
        ('SPAN', (0, 0), (0, 2)),
        ('SPAN', (1, 0), (10, 0)),
        ('SPAN', (11, 0), (12, 2)),
        ('SPAN', (13, 0), (13, 2)),
        ('SPAN', (1, 1), (2, 1)),
        ('SPAN', (3, 1), (4, 1)),
        ('SPAN', (5, 1), (6, 1)),
        ('SPAN', (7, 1), (8, 1)),
        ('SPAN', (9, 1), (10, 1)),
        ('SPAN', (11, 10), (12, 10)),
        ('SPAN', (1, 10), (2, 10)),
        ('SPAN', (3, 10), (4, 10)),
        ('SPAN', (5, 10), (6, 10)),
        ('SPAN', (7, 10), (8, 10)),
        ('SPAN', (9, 10), (10, 10)),
        ('SPAN', (11, 10), (12, 10)),
        
        ('FONTNAME', (0, 3), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 3), (0, -1), 'LEFT'),
    ]))
    
    elements.append(table)
    
    cursor.close()
    conn.close()

def gerar_relatorio_6_9(elements, cabecalho, figura_inferior):
    ano_letivo = 2025
    
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, data_inicio, data_fim FROM anosletivos WHERE ano_letivo = %s", (ano_letivo,))
    datas_ano_letivo = cursor.fetchone()
    
    if not datas_ano_letivo:
        print("Ano letivo não encontrado")
        return
        
    data_inicio = datas_ano_letivo['data_inicio']
    data_fim = datas_ano_letivo['data_fim']
    ano_letivo_id = datas_ano_letivo['id']
    mes_atual = datetime.datetime.now().month
    
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        return

    df = pd.DataFrame(dados_aluno)

    estilo_titulo = ParagraphStyle(
        name='EstiloTitulo',
        fontSize=12,
        alignment=1,
        spaceAfter=10,
        spaceBefore=10,
        leading=16
    )
    
    estilo_info = ParagraphStyle(
        name='EstiloInfo',
        fontSize=10,
        alignment=0,
        spaceAfter=5,
        leading=14
    )
    
    data = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho), estilo_titulo)]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.2 * inch))
    
    elements.append(Paragraph("<b>MOVIMENTO MENSAL – ENSINO FUNDAMENTAL</b>", estilo_titulo))
    elements.append(Paragraph("<b>6º ao 9º ANO</b>", estilo_titulo))
    elements.append(Spacer(1, 0.2 * inch))
    
    info_data = [
        [Paragraph(f"<b>MÊS:</b> {get_nome_mes(datetime.datetime.now().month)}", estilo_info), 
         Paragraph(f"<b>ANO:</b> {datetime.datetime.now().year}", estilo_info)]
    ]
    info_table = Table(info_data, colWidths=[4*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(info_table)
    
    elements.append(Paragraph("<b>UNIDADE DE ENSINO:</b> E. M. PROFESSORA NADIR NASCIMENTO MORAES.", estilo_info))
    elements.append(Paragraph("<b>ENDEREÇO:</b> RUA 65 QD 12 S/N – Conjunto Maiobão", estilo_info))
    elements.append(Paragraph("<b>MUNICÍPIO:</b> Paço do Lumiar – MA", estilo_info))
    elements.append(Paragraph("<b>TURNO:</b> VESPERTINO", estilo_info))
    
    dias_letivos = buscar_dias_letivos(cursor, ano_letivo, mes_atual)
    
    info_salas_data = [
        [Paragraph("<b>Nº DE SALA DE AULA DO PRÉDIO:</b> 5", estilo_info),
         Paragraph(f"<b>Nº DE DIAS LETIVOS:</b> {dias_letivos}", estilo_info)]
    ]
    info_salas_table = Table(info_salas_data, colWidths=[4*inch, 4*inch])
    info_salas_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(info_salas_table)
    
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("<b>DEPENDÊNCIA ADMINISTRATIVA DO PRÉDIO</b>", estilo_info))
    
    checkbox_data = [
        ['( ) Estadual', '(X) Municipal', '( ) Particular', '( ) Alugado']
    ]
    checkbox_table = Table(checkbox_data, colWidths=[2*inch]*4)
    checkbox_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
    ]))
    elements.append(checkbox_table)
    
    elements.append(Spacer(1, 0.5 * inch))
    
    series = ['6º Ano A', '6º Ano B', '7º Ano', '8º Ano', '9º Ano']
    
    contagem_inicial = contar_alunos_por_serie_sexo(df, data_inicio, 'inicial', '6_9')
    total_m_inicial = sum(serie['M'] for serie in contagem_inicial.values())
    total_f_inicial = sum(serie['F'] for serie in contagem_inicial.values())
    total_geral_inicial = total_m_inicial + total_f_inicial
    
    contagem_atual = contar_alunos_por_serie_sexo(df, series_range='6_9')
    total_m_atual = sum(serie['M'] for serie in contagem_atual.values())
    total_f_atual = sum(serie['F'] for serie in contagem_atual.values())
    total_geral_atual = total_m_atual + total_f_atual
    
    dados_movimentacao = {serie: contar_movimentacao_mensal(cursor, ano_letivo_id, mes_atual, serie) for serie in series}
    
    transferencias_recebidas = contar_transferencias_recebidas(cursor, ano_letivo_id, mes_atual, series)
    
    hoje = datetime.date.today()
    
    evadidos = {serie: {'M': 0, 'F': 0} for serie in series}
    transferidos = {serie: {'M': 0, 'F': 0} for serie in series}
    
    for serie, movimentacao in dados_movimentacao.items():
        for registro in movimentacao:
            if registro['status'] == 'Evadido':
                evadidos[serie]['M'] = registro['total_m']
                evadidos[serie]['F'] = registro['total_f']
            elif registro['status'] == 'Transferido':
                transferidos[serie]['M'] = registro['total_m']
                transferidos[serie]['F'] = registro['total_f']
    
    transferidos_dashboard = contar_transferencias_por_serie_sexo(df, series, series_range='6_9')
    
    
    data = [[quebra_linha("ESPECIFICAÇÃO"), 'Série'] + ['']*9 + ['Total','Total', 'Total Geral'],
            ['', '6º Ano A','6º Ano A', '6º Ano B','6º Ano B','7º Ano','7º Ano','8º Ano','8º Ano','9º Ano','9º Ano']+['']*3,
            ['']+['M', 'F']*6+[''],
            [quebra_linha("MATRÍCULA INICIAL")] + 
            [contagem_inicial['6º Ano A']['M'], contagem_inicial['6º Ano A']['F'],
             contagem_inicial['6º Ano B']['M'], contagem_inicial['6º Ano B']['F'],
             contagem_inicial['7º Ano']['M'], contagem_inicial['7º Ano']['F'],
             contagem_inicial['8º Ano']['M'], contagem_inicial['8º Ano']['F'],
             contagem_inicial['9º Ano']['M'], contagem_inicial['9º Ano']['F'],
             total_m_inicial, total_f_inicial, total_geral_inicial],
            [quebra_linha("MATRÍCULA ATUAL")] + 
            [contagem_atual['6º Ano A']['M'], contagem_atual['6º Ano A']['F'],
             contagem_atual['6º Ano B']['M'], contagem_atual['6º Ano B']['F'],
             contagem_atual['7º Ano']['M'], contagem_atual['7º Ano']['F'],
             contagem_atual['8º Ano']['M'], contagem_atual['8º Ano']['F'],
             contagem_atual['9º Ano']['M'], contagem_atual['9º Ano']['F'],
             total_m_atual, total_f_atual, total_geral_atual],
            [quebra_linha("TRANSFERÊNCIAS RECEBIDAS")] + 
            [transferencias_recebidas['6º Ano A']['M'], transferencias_recebidas['6º Ano A']['F'],
             transferencias_recebidas['6º Ano B']['M'], transferencias_recebidas['6º Ano B']['F'],
             transferencias_recebidas['7º Ano']['M'], transferencias_recebidas['7º Ano']['F'],
             transferencias_recebidas['8º Ano']['M'], transferencias_recebidas['8º Ano']['F'],
             transferencias_recebidas['9º Ano']['M'], transferencias_recebidas['9º Ano']['F'],
             sum(serie['M'] for serie in transferencias_recebidas.values()),
             sum(serie['F'] for serie in transferencias_recebidas.values()),
             sum(serie['M'] + serie['F'] for serie in transferencias_recebidas.values())],
            [quebra_linha("TRANSFERÊNCIAS EXPEDIDAS")] + 
            [transferidos_dashboard['6º Ano A']['M'], transferidos_dashboard['6º Ano A']['F'],
             transferidos_dashboard['6º Ano B']['M'], transferidos_dashboard['6º Ano B']['F'],
             transferidos_dashboard['7º Ano']['M'], transferidos_dashboard['7º Ano']['F'],
             transferidos_dashboard['8º Ano']['M'], transferidos_dashboard['8º Ano']['F'],
             transferidos_dashboard['9º Ano']['M'], transferidos_dashboard['9º Ano']['F'],
             sum(serie['M'] for serie in transferidos_dashboard.values()),
             sum(serie['F'] for serie in transferidos_dashboard.values()),
             sum(serie['M'] + serie['F'] for serie in transferidos_dashboard.values())],
            [quebra_linha("ALUNOS EVADIDOS")] + 
            [evadidos['6º Ano A']['M'], evadidos['6º Ano A']['F'],
             evadidos['6º Ano B']['M'], evadidos['6º Ano B']['F'],
             evadidos['7º Ano']['M'], evadidos['7º Ano']['F'],
             evadidos['8º Ano']['M'], evadidos['8º Ano']['F'],
             evadidos['9º Ano']['M'], evadidos['9º Ano']['F'],
             sum(serie['M'] for serie in evadidos.values()),
             sum(serie['F'] for serie in evadidos.values()),
             sum(serie['M'] + serie['F'] for serie in evadidos.values())],
    ]
    
    if hoje > data_fim:
        dados_aprovacao = {serie: contar_aprovacoes_reprovacoes(cursor, ano_letivo_id, serie) for serie in series}
        aprovados = {serie: {'M': 0, 'F': 0} for serie in series}
        reprovados = {serie: {'M': 0, 'F': 0} for serie in series}
        
        for serie, resultados in dados_aprovacao.items():
            for resultado in resultados:
                if resultado['situacao'] == 'Aprovado':
                    aprovados[serie]['M'] = resultado['total_m']
                    aprovados[serie]['F'] = resultado['total_f']
                else:
                    reprovados[serie]['M'] = resultado['total_m']
                    reprovados[serie]['F'] = resultado['total_f']
        
        data.extend([
            [quebra_linha("ALUNOS APROVADOS")] + 
            [aprovados['6º Ano A']['M'], aprovados['6º Ano A']['F'],
             aprovados['6º Ano B']['M'], aprovados['6º Ano B']['F'],
             aprovados['7º Ano']['M'], aprovados['7º Ano']['F'],
             aprovados['8º Ano']['M'], aprovados['8º Ano']['F'],
             aprovados['9º Ano']['M'], aprovados['9º Ano']['F'],
             sum(serie['M'] for serie in aprovados.values()),
             sum(serie['F'] for serie in aprovados.values()),
             sum(serie['M'] + serie['F'] for serie in aprovados.values())],
            [quebra_linha("ALUNOS REPROVADOS")] + 
            [reprovados['6º Ano A']['M'], reprovados['6º Ano A']['F'],
             reprovados['6º Ano B']['M'], reprovados['6º Ano B']['F'],
             reprovados['7º Ano']['M'], reprovados['7º Ano']['F'],
             reprovados['8º Ano']['M'], reprovados['8º Ano']['F'],
             reprovados['9º Ano']['M'], reprovados['9º Ano']['F'],
             sum(serie['M'] for serie in reprovados.values()),
             sum(serie['F'] for serie in reprovados.values()),
             sum(serie['M'] + serie['F'] for serie in reprovados.values())]
        ])
    else:
        data.extend([
            [quebra_linha("ALUNOS APROVADOS")] + ["--"]*11,
            [quebra_linha("ALUNOS REPROVADOS")] + ["--"]*11
        ])
    
    query_turmas = """
    SELECT 
        CASE 
            WHEN s.nome = '6º Ano' THEN CONCAT(s.nome, ' ', t.nome)
            ELSE s.nome 
        END as serie_nome,
        COUNT(DISTINCT t.id) as total_turmas
    FROM turmas t
    JOIN serie s ON t.serie_id = s.id
    WHERE t.ano_letivo_id = %s
    GROUP BY 
        CASE 
            WHEN s.nome = '6º Ano' THEN CONCAT(s.nome, ' ', t.nome)
            ELSE s.nome 
        END;
    """
    cursor.execute(query_turmas, (ano_letivo_id,))
    turmas = {r['serie_nome']: r['total_turmas'] for r in cursor.fetchall()}
    
    turmas_por_serie = []
    total_turmas = 0
    for serie in series:
        num_turmas = turmas.get(serie, 0)
        turmas_por_serie.extend([num_turmas, num_turmas])  
        total_turmas += num_turmas
    
    data.append([quebra_linha("Nº de TURMAS")] + 
                turmas_por_serie +  
                [total_turmas, total_turmas, total_turmas])  
    
    colWidths = [2.5*inch] + [0.35*inch]*12 + [inch]
    table = Table(data, colWidths=colWidths)
    
    cor_cabecalho = HexColor('#1B4F72')
    cor_subcabecalho = HexColor('#2874A6')
    cor_texto = black
    cor_linha_clara = Color(0.95, 0.95, 0.95)
    cor_borda = black
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 2), cor_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 2), 'white'),
        ('FONTNAME', (0, 0), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 2), 11),
        
        ('FONTNAME', (0, 3), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 3), (-1, -1), 10),
        ('TEXTCOLOR', (0, 3), (-1, -1), cor_texto),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        ('BACKGROUND', (0, 4), (-1, 4), cor_linha_clara),
        ('BACKGROUND', (0, 6), (-1, 6), cor_linha_clara),
        ('BACKGROUND', (0, 8), (-1, 8), cor_linha_clara),
        ('BACKGROUND', (0, 10), (-1, 10), cor_linha_clara),
        
        ('GRID', (0, 0), (-1, -1), 0.5, cor_borda),
        ('BOX', (0, 0), (-1, -1), 1, cor_borda),
        ('LINEBELOW', (0, 2), (-1, 2), 1, cor_borda),
        
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        
        ('SPAN', (0, 0), (0, 2)),
        ('SPAN', (1, 0), (10, 0)),
        ('SPAN', (11, 0), (12, 2)),
        ('SPAN', (13, 0), (13, 2)),
        ('SPAN', (1, 1), (2, 1)),
        ('SPAN', (3, 1), (4, 1)),
        ('SPAN', (5, 1), (6, 1)),
        ('SPAN', (7, 1), (8, 1)),
        ('SPAN', (9, 1), (10, 1)),
        ('SPAN', (1, 10), (2, 10)),
        ('SPAN', (3, 10), (4, 10)),
        ('SPAN', (5, 10), (6, 10)),
        ('SPAN', (7, 10), (8, 10)),
        ('SPAN', (9, 10), (10, 10)),
        ('SPAN', (11, 10), (12, 10)),
        
        ('FONTNAME', (0, 3), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 3), (0, -1), 'LEFT'),
    ]))
    
    elements.append(table)
    
    cursor.close()
    conn.close()

def parse_turma_nome(turma_nome):
    """Extrai o número do ano e a letra da turma (se houver) para ordenação.
       Retorna uma tupla (ano, letra_ordinal) ou (None, None) se não encontrar."""
    if not isinstance(turma_nome, str):
        return (None, None)
    
    match = re.match(r'(\d+)º?\s*Ano\s*([A-Z])?', turma_nome.strip(), re.IGNORECASE)
    if match:
        ano = int(match.group(1))
        letra = match.group(2)
        letra_ordinal = ord(letra) - ord('A') if letra else -1 
        return (ano, letra_ordinal)
    return (None, None)

def contar_transferencias_por_serie_sexo(df, series, series_range='1_5'):
    """
    Conta alunos transferidos por série e sexo.
    
    Args:
        df: DataFrame com os dados dos alunos
        series: Lista de séries a serem contadas
        series_range: Intervalo de séries ('1_5' ou '6_9')
        
    Returns:
        Dicionário com contagens por série e sexo de alunos transferidos
    """
    contagem = {serie: {'M': 0, 'F': 0} for serie in series}
    
    df_transferidos = df[df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])]
    
    for serie in series:
        if series_range == '1_5':
            serie_df = df_transferidos[df_transferidos['NOME_SERIE'] == serie]
        else:
            if ' ' in serie:  
                serie_df = df_transferidos[(df_transferidos['NOME_SERIE'] + ' ' + df_transferidos['NOME_TURMA']) == serie]
            else:  
                serie_df = df_transferidos[df_transferidos['NOME_SERIE'] == serie]
                
        contagem[serie]['M'] = len(serie_df[serie_df['SEXO'] == 'M'])
        contagem[serie]['F'] = len(serie_df[serie_df['SEXO'] == 'F'])
    
    return contagem

relatorio_movimentacao_mensal()