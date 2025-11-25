from config_logs import get_logger
logger = get_logger(__name__)
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
from db.connection import get_connection, get_cursor
import pymysql
import re
from reportlab.lib.pagesizes import landscape, letter, letter
from PyPDF2 import PdfReader, PdfWriter
import io
from typing import Any, cast


def add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior, mes=None):
    data = [
        [Image(figura_inferior, width=2.5 * inch, height=0.5 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),    # Alinhamento horizontal
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 3.75 * inch))
    
    # Usar o mês fornecido ou o mês atual
    mes_atual = mes if mes is not None else datetime.datetime.now().month
    elements.append(Paragraph(f"<b>MOVIMENTO MENSAL <br/><br/> {get_nome_mes(mes_atual)}</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1, leading=24)))
    elements.append(Spacer(1, 3.75 * inch))
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
    elements.append(PageBreak())

def add_header(doc, elements, cabecalho, figura_superior, figura_inferior):
    data = [
        [Image(figura_inferior, width=2.5 * inch, height=0.5 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 0.2 * inch))

def contar_alunos_por_serie_sexo(df, data_referencia=None, tipo_contagem='atual', series_range='1_5'):
    # Criar dicionário para armazenar contagens
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
    
    # Contar alunos por série e sexo
    for _, aluno in df.iterrows():
        serie = aluno['NOME_SERIE']
        turma = aluno.get('NOME_TURMA', '')
        sexo = aluno['SEXO']
        data_matricula = pd.to_datetime(aluno['DATA_MATRICULA']).date() if pd.notna(aluno['DATA_MATRICULA']) else None
        status = aluno['SITUAÇÃO']

        # Ajusta a série para incluir a turma se for 6º ano
        if serie == '6º Ano':
            if 'A' in turma:
                serie = '6º Ano A'
            elif 'B' in turma:
                serie = '6º Ano B'

        if serie in contagem and sexo in ['M', 'F']:
            if tipo_contagem == 'inicial':
                # Para matrícula inicial, conta apenas alunos matriculados antes da data_inicio
                # e que não foram transferidos ou evadiram antes da data_inicio
                if data_matricula and data_matricula < data_referencia:
                    contagem[serie][sexo] += 1
            else:
                # Para matrícula atual, conta apenas alunos ativos (não inclui transferidos e evadidos)
                if status == 'Ativo':
                    contagem[serie][sexo] += 1
    
    return contagem

def contar_movimentacao_mensal(cursor, ano_letivo_id, mes, serie):
    # Conta transferências e evasões acumuladas até o fim do mês específico
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
    # Conta aprovações e reprovações baseado nas médias finais e histórico de matrículas
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

def contar_transferencias_recebidas(cursor, ano_letivo_id, data_inicio_ano_letivo, series):
    logger.info("\nDEBUG - Iniciando contar_transferencias_recebidas")
    logger.info("Parâmetros recebidos:")
    logger.info(f"ano_letivo_id: {ano_letivo_id}")
    logger.info(f"data_inicio_ano_letivo: {data_inicio_ano_letivo}")
    logger.info(f"series: {series}")
    
    # Determina o turno com base nas séries
    turno = 'VESP' if any('6º Ano' in serie or '7º Ano' in serie or '8º Ano' in serie or '9º Ano' in serie for serie in series) else 'MAT'
    logger.info(f"\nDEBUG - Turno determinado: {turno}")
    
    logger.info("\nDEBUG - Verificando dados antes da query principal:")
    
    # Verifica turmas disponíveis
    cursor.execute("""
        SELECT t.id, t.nome, s.nome as serie, t.turno
        FROM turmas t
        JOIN serie s ON t.serie_id = s.id
        WHERE t.ano_letivo_id = %s
    """, (ano_letivo_id,))
    turmas = cursor.fetchall()
    logger.info("\nTurmas disponíveis:")
    for turma in turmas:
        logger.info(f"ID: {turma['id']}, Nome: {turma['nome']}, Série: {turma['serie']}, Turno: {turma['turno']}")
    
    # Verifica primeiras matrículas
    cursor.execute("""
        SELECT m.id, m.data_matricula, m.status, t.turno, s.nome as serie, a.sexo
        FROM matriculas m
        JOIN turmas t ON m.turma_id = t.id
        JOIN serie s ON t.serie_id = s.id
        JOIN alunos a ON m.aluno_id = a.id
        WHERE m.ano_letivo_id = %s
        AND m.data_matricula > %s
        ORDER BY m.data_matricula
        LIMIT 5
    """, (ano_letivo_id, data_inicio_ano_letivo))
    matriculas = cursor.fetchall()
    logger.info("\nPrimeiras 5 matrículas após a data de início:")
    for mat in matriculas:
        logger.info(f"ID: {mat['id']}, Data: {mat['data_matricula']}, Status: {mat['status']}, Turno: {mat['turno']}, Série: {mat['serie']}, Sexo: {mat['sexo']}")
    
    # Prepara a lista de séries para a query
    series_placeholders = ','.join(['%s'] * len(series))
    
    # Query principal modificada para incluir matrículas do início do ano
    query = f"""
        SELECT
            CASE
                WHEN s.nome = '6º Ano' THEN CONCAT(s.nome, ' ', t.nome)
                ELSE s.nome
            END as serie,
            a.sexo,
            COUNT(*) as total,
            GROUP_CONCAT(a.nome) as nomes_alunos
        FROM turmas t
        JOIN matriculas m ON t.id = m.turma_id
        JOIN serie s ON t.serie_id = s.id
        JOIN alunos a ON m.aluno_id = a.id
        WHERE m.ano_letivo_id = %s
        AND (
            (m.data_matricula > %s AND m.status IN ('Ativo', 'Transferido'))
            OR 
            (m.data_matricula = %s AND m.status = 'Ativo')
        )
        AND t.turno = %s
        AND (
            CASE
                WHEN s.nome = '6º Ano' THEN CONCAT(s.nome, ' ', t.nome)
                ELSE s.nome
            END IN ({series_placeholders})
        )
        GROUP BY
            CASE
                WHEN s.nome = '6º Ano' THEN CONCAT(s.nome, ' ', t.nome)
                ELSE s.nome
            END,
            a.sexo
    """
    
    logger.info("\nDEBUG - Query SQL:")
    logger.info(query)
    
    # Prepara os parâmetros da query
    params = [ano_letivo_id, data_inicio_ano_letivo, data_inicio_ano_letivo, turno] + series
    
    logger.info("\nDEBUG - Parâmetros da query:")
    logger.info(f"ano_letivo_id: {ano_letivo_id}")
    logger.info(f"data_inicio_ano_letivo: {data_inicio_ano_letivo}")
    logger.info(f"turno: {turno}")
    logger.info(f"series: {series}")
    
    cursor.execute(query, params)
    resultados = cursor.fetchall()
    
    logger.info("\nDEBUG - Resultados da query:")
    logger.info(f"Total de registros encontrados: {len(resultados)}")
    
    if resultados:
        logger.info("\nDetalhes dos resultados:")
        for row in resultados:
            logger.info(f"Série: {row['serie']}, Sexo: {row['sexo']}, Total: {row['total']}")
            logger.info(f"Alunos: {row['nomes_alunos']}")
    
    # Inicializa o dicionário de contagem
    contagem = {serie: {'M': 0, 'F': 0} for serie in series}
    
    # Preenche o dicionário com os resultados
    for row in resultados:
        serie = row['serie']
        sexo = row['sexo']
        total = row['total']
        contagem[serie][sexo] = total
    
    logger.info("\nDEBUG - Contagem final por série e sexo:")
    for serie in series:
        logger.info(f"{serie}: M={contagem[serie]['M']}, F={contagem[serie]['F']}")
    
    return contagem

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
    # Primeiro, vamos verificar diretamente a licença da professora Ana Patrícia
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
    # Definir estilos para os parágrafos
    styles = getSampleStyleSheet()
    style_cell = ParagraphStyle(name='Cell', fontSize=8, alignment=1) # Estilo para célula
    style_cell_left = ParagraphStyle(name='CellLeft', fontSize=8, alignment=0) # Estilo alinhado à esquerda

    if not professores:
        elements.append(Paragraph("Nenhum professor encontrado.", styles["Normal"]))
        return
    
    # Adicionar título apenas se não estiver vazio
    if titulo:
        elements.append(Paragraph(titulo, styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))
    
    # Definir cabeçalhos
    headers = ["Nº", "NOME DO SERVIDOR", "CARGO", "SITUAÇÃO FUNCIONAL", "HABILITAÇÃO", "CLASSE REGENTE", "LICENÇA"]
    
    # Preparar dados (aceita Paragraphs e strings)
    data: list[list[Any]] = [headers]
    
    for i, professor in enumerate(professores, 1):
        licenca_info = ""
        if professor.get('licenca_motivo'):
            licenca_info = professor['licenca_motivo']
        
        habilitacao = ""
        classe_regente_obj = Paragraph("---", style_cell) # Usar Paragraph para permitir <br/>

        # Verificar se é o professor Kevin Anderson
        if 'Kevin Anderson' in professor['nome']:
            habilitacao = "INTÉRPRETE DE LIBRAS"
        elif professor['polivalente'] == 'sim':
            habilitacao = "Polivalente"
            classe_regente_str = professor.get('turmas') or "---"
            if "Volante (Todas as Turmas)" in classe_regente_str:
                 classe_regente_str = "1º a 5º Ano"
            classe_regente_obj = Paragraph(classe_regente_str, style_cell)
        else:
            # Professor não polivalente
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
                        # Não sequencial: Formatar com ", " e " e ", depois quebrar linha a cada 2.
                        if len(nomes_turmas_ordenadas) > 1:
                             # Junta todos menos o último com ", "
                            prefixo = ", ".join(nomes_turmas_ordenadas[:-1])
                            # Adiciona " e " antes do último
                            lista_completa_str = f"{prefixo} e {nomes_turmas_ordenadas[-1]}"
                        else:
                             # Caso tenha só uma turma (embora o if externo já trate > 1, por segurança)
                            lista_completa_str = nomes_turmas_ordenadas[0]

                        # Quebrar linha a cada duas turmas na lista formatada
                        # Re-separar pelos delimitadores originais para agrupar
                        # Usamos regex para separar por ", " ou " e "
                        partes = re.split(r'(?:, | e )', lista_completa_str)
                        
                        linhas_formatadas = []
                        for k in range(0, len(partes), 2):
                            par = partes[k:k+2]
                            # Determinar o separador correto para o par atual
                            # Se este par contém o último elemento geral, usa " e "
                            if k + len(par) == len(partes) and len(par) > 1:
                                separador = " e "
                            elif len(par) > 1:
                                separador = ", "
                            else: # Apenas um elemento no par
                                separador = ""
                            
                            linhas_formatadas.append(separador.join(par))

                        classe_regente_str = "<br/>".join(linhas_formatadas)
                        classe_regente_obj = Paragraph(classe_regente_str, style_cell)

                elif len(nomes_turmas_ordenadas) == 1:
                     classe_regente_obj = Paragraph(nomes_turmas_ordenadas[0], style_cell)
                else:
                    classe_regente_obj = Paragraph("---", style_cell) # Caso não tenha turmas válidas
            else:
                classe_regente_obj = Paragraph("---", style_cell)

        row = [
            Paragraph(str(i), style_cell),
            Paragraph(professor['nome'], style_cell_left), # Nome alinhado à esquerda
            Paragraph(professor['cargo'], style_cell),
            Paragraph(professor['vinculo'], style_cell),
            Paragraph(habilitacao, style_cell),
            classe_regente_obj, # Já é um Paragraph
            Paragraph(licenca_info or "---", style_cell)
        ]
        data.append(row)
    
    # Definir larguras das colunas
    col_widths = [0.4*inch, 2.5*inch, 1*inch, 1.5*inch, 1.2*inch, 1.2*inch, 1.4*inch]
    
    # Criar tabela
    table = Table(data, colWidths=col_widths)
    cor_cabecalho = HexColor('#1B4F72')
    # Definir estilo
    style = TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), cor_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Corpo da tabela
        
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
    data = [headers]
    
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
        data.append(row)
    
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
    
    # Adicionar espaço para assinaturas
    elements.append(Spacer(1, 2 * inch))
    
    # Criar tabela para assinaturas
    assinaturas_data = [
        ['_____________________________', '_____________________________'],
        ['Gestora Geral', 'Gestora Adjunta']
    ]
    assinaturas_table = Table(assinaturas_data, colWidths=[3*inch, 3*inch])
    assinaturas_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
    ])
    assinaturas_table.setStyle(assinaturas_style)
    elements.append(assinaturas_table)

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
    
    # Definir larguras das colunas
    # col_widths = [2.5*inch, 1.5*inch, 0.8*inch, 0.5*inch, 0.8*inch]
    
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

def relatorio_movimentacao_mensal(mes=None):
    # Se nenhum mês for especificado, usa o mês atual
    if mes is None:
        mes = datetime.datetime.now().month
    else:
        # Garante que o mês está entre 1 e 12
        mes = int(mes)
        if mes < 1 or mes > 12:
            raise ValueError("O mês deve estar entre 1 e 12")
    
    # Criar um único PDF para ambos os relatórios
    from reportlab.lib.pagesizes import letter, landscape
    from PyPDF2 import PdfReader, PdfWriter
    import io
    
    # Cabeçalho comum para ambos os relatórios
    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    # Logotipos
    figura_superior = os.path.join(os.path.dirname(__file__), 'logosemed.png')
    figura_inferior = os.path.join(os.path.dirname(__file__), 'logopaco.png')
    
    # Estabelecer conexão com o banco de dados e buscar dados necessários
    with get_connection() as conn:
        cursor = cast(Any, conn).cursor(dictionary=True)

        # Buscar dados dos professores e tutores
        professores_1_5 = buscar_corpo_docente_1_5(cursor, escola_id=60)
        professores_6_9 = buscar_corpo_docente_6_9(cursor, escola_id=60)
        tutores = buscar_tutores(cursor, escola_id=60)
        funcionarios_admin = buscar_funcionarios_administrativos(cursor, escola_id=60)

        # fechar cursor explicitamente (get_connection garante fechamento da conexão)
        try:
            cursor.close()
        except Exception:
            pass
    
    # Criar buffers separados para cada parte do relatório
    # 1. Capa (retrato)
    doc_capa, buffer_capa = create_pdf_buffer()
    elements_capa = []
    add_cover_page(doc_capa, elements_capa, cabecalho, figura_superior, figura_inferior, mes)
    doc_capa.build(elements_capa)
    buffer_capa.seek(0)
    
    # 2. Relatório 1º ao 5º ano (retrato)
    doc_relatorio_1_5, buffer_relatorio_1_5 = create_pdf_buffer()
    elements_relatorio_1_5 = []
    gerar_relatorio_1_5(elements_relatorio_1_5, cabecalho, figura_inferior, mes)
    doc_relatorio_1_5.build(elements_relatorio_1_5)
    buffer_relatorio_1_5.seek(0)
    
    # 3. Corpo docente 1º ao 5º ano (paisagem)
    doc_docente_1_5, buffer_docente_1_5 = create_pdf_buffer(pagesize=landscape(letter))
    elements_docente_1_5 = []
    
    # Adicionar cabeçalho ao documento paisagem
    data = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    table = Table(data, colWidths=[7 * inch])  # Mais largo para paisagem
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements_docente_1_5.append(table)
    elements_docente_1_5.append(Spacer(1, 0.3 * inch))
    
    # Adicionar título 1º ao 5º ano
    elements_docente_1_5.append(Paragraph("CORPO DOCENTE - 1º ao 5º ANO - TURNO MATUTINO", ParagraphStyle(name='Heading2')))
    elements_docente_1_5.append(Spacer(1, 0.2 * inch))
    
    # Adicionar tabela do corpo docente 1º ao 5º ano
    gerar_tabela_corpo_docente(elements_docente_1_5, professores_1_5, "")
    
    elements_docente_1_5.append(Spacer(1, 0.5 * inch))
    gerar_tabela_funcionarios_administrativos(elements_docente_1_5, funcionarios_admin, "FUNCIONÁRIOS ADMINISTRATIVOS")
    
    doc_docente_1_5.build(elements_docente_1_5)
    buffer_docente_1_5.seek(0)
    
    # 4. Relatório 6º ao 9º ano (retrato)
    doc_relatorio_6_9, buffer_relatorio_6_9 = create_pdf_buffer()
    elements_relatorio_6_9 = []
    gerar_relatorio_6_9(elements_relatorio_6_9, cabecalho, figura_inferior, mes)
    doc_relatorio_6_9.build(elements_relatorio_6_9)
    buffer_relatorio_6_9.seek(0)
    
    # 5. Corpo docente 6º ao 9º ano (paisagem)
    doc_docente_6_9, buffer_docente_6_9 = create_pdf_buffer(pagesize=landscape(letter))
    elements_docente_6_9 = []
    
    # Adicionar cabeçalho novamente
    elements_docente_6_9.append(table)
    elements_docente_6_9.append(Spacer(1, 0.3 * inch))
    
    # Adicionar título 6º ao 9º ano
    elements_docente_6_9.append(Paragraph("CORPO DOCENTE - 6º ao 9º ANO - TURNO VESPERTINO", ParagraphStyle(name='Heading2')))
    elements_docente_6_9.append(Spacer(1, 0.2 * inch))
    
    # Adicionar tabela do corpo docente 6º ao 9º ano
    gerar_tabela_corpo_docente(elements_docente_6_9, professores_6_9, "")
    
    elements_docente_6_9.append(Spacer(1, 0.5 * inch))
    gerar_tabela_tutores(elements_docente_6_9, tutores, "TUTORES E CUIDADORES")
    
    doc_docente_6_9.build(elements_docente_6_9)
    buffer_docente_6_9.seek(0)
    
    # Mesclar os documentos na ordem original
    output = PdfWriter()
    
    # Adicionar páginas na ordem original:
    # 1. Capa
    capa_reader = PdfReader(buffer_capa)
    for i in range(len(capa_reader.pages)):
        output.add_page(capa_reader.pages[i])
    
    # 2. Relatório 1º ao 5º ano
    relatorio_1_5_reader = PdfReader(buffer_relatorio_1_5)
    for i in range(len(relatorio_1_5_reader.pages)):
        output.add_page(relatorio_1_5_reader.pages[i])
    
    # 3. Corpo docente 1º ao 5º ano
    docente_1_5_reader = PdfReader(buffer_docente_1_5)
    for i in range(len(docente_1_5_reader.pages)):
        output.add_page(docente_1_5_reader.pages[i])
        
    # 4. Relatório 6º ao 9º ano
    relatorio_6_9_reader = PdfReader(buffer_relatorio_6_9)
    for i in range(len(relatorio_6_9_reader.pages)):
        output.add_page(relatorio_6_9_reader.pages[i])
    
    # 5. Corpo docente 6º ao 9º ano
    docente_6_9_reader = PdfReader(buffer_docente_6_9)
    for i in range(len(docente_6_9_reader.pages)):
        output.add_page(docente_6_9_reader.pages[i])
    
    # Criar buffer de saída final
    buffer_final = io.BytesIO()
    output.write(buffer_final)
    buffer_final.seek(0)
    
    # Salvar e abrir o PDF final
    try:
        from gerarPDF import salvar_e_abrir_pdf as _salvar_helper
    except Exception:
        _salvar_helper = None

    saved_path = None
    try:
        if _salvar_helper:
            try:
                saved_path = _salvar_helper(buffer_final)
            except Exception:
                saved_path = None

        if not saved_path:
            import tempfile
            from utilitarios.gerenciador_documentos import salvar_documento_sistema
            from utilitarios.tipos_documentos import TIPO_MOVIMENTO_MENSAL

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            try:
                tmp.write(buffer_final.getvalue())
                tmp.close()
                descricao = f"Movimento Mensal - {datetime.datetime.now().year}"
                try:
                    salvar_documento_sistema(tmp.name, TIPO_MOVIMENTO_MENSAL, funcionario_id=1, finalidade='Secretaria', descricao=descricao)
                    saved_path = tmp.name
                except Exception:
                    try:
                        if _salvar_helper:
                            buffer_final.seek(0)
                            _salvar_helper(buffer_final)
                    except Exception:
                        pass
            finally:
                pass
    finally:
        try:
            buffer_final.close()
        except Exception:
            pass

def gerar_relatorio_1_5(elements, cabecalho, figura_inferior, mes):
    ano_letivo = 2025
    
    # Conectar ao banco para obter as datas do ano letivo
    from db.connection import get_cursor
    with get_cursor() as cursor:
        # Buscar datas do ano letivo
        cursor.execute("SELECT id, data_inicio, data_fim FROM anosletivos WHERE ano_letivo = %s", (ano_letivo,))
        datas_ano_letivo = cursor.fetchone()

    if not datas_ano_letivo:
        logger.info("Ano letivo não encontrado")
        return

    data_inicio = datas_ano_letivo['data_inicio']
    data_fim = datas_ano_letivo['data_fim']
    ano_letivo_id = datas_ano_letivo['id']
    
    logger.info(f"\nDEBUG - Datas do ano letivo:")
    logger.info(f"data_inicio: {data_inicio}")
    logger.info(f"data_fim: {data_fim}")
    logger.info(f"ano_letivo_id: {ano_letivo_id}")
    
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        return

    df = pd.DataFrame(dados_aluno)

    # Adicionar cabeçalho informativo
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
    
    # Informações da escola
    info_data = [
        [Paragraph(f"<b>MÊS:</b> {get_nome_mes(mes)}", estilo_info), 
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
    
    # Buscar dias letivos do mês atual usando uma nova conexão
    with get_cursor() as cursor:
        dias_letivos = buscar_dias_letivos(cursor, ano_letivo, mes)
    
    # Informações sobre salas e dias letivos
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
    
    # Checkboxes para dependência administrativa
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
    
    # Contar alunos - matrícula inicial
    contagem_inicial = contar_alunos_por_serie_sexo(df, data_inicio, 'inicial')
    total_m_inicial = sum(serie['M'] for serie in contagem_inicial.values())
    total_f_inicial = sum(serie['F'] for serie in contagem_inicial.values())
    total_geral_inicial = total_m_inicial + total_f_inicial
    
    # Contar alunos - matrícula atual
    contagem_atual = contar_alunos_por_serie_sexo(df)
    total_m_atual = sum(serie['M'] for serie in contagem_atual.values())
    total_f_atual = sum(serie['F'] for serie in contagem_atual.values())
    total_geral_atual = total_m_atual + total_f_atual
    
    # Preparar dados de movimentação mensal
    series = ['1º Ano', '2º Ano', '3º Ano', '4º Ano', '5º Ano']
    
    # Usar uma nova conexão para buscar dados de movimentação
    with get_cursor() as cursor:
        dados_movimentacao = {serie: contar_movimentacao_mensal(cursor, ano_letivo_id, mes, serie) for serie in series}
        
        # Contar transferências recebidas
        logger.info(f"\nDEBUG - Chamando contar_transferencias_recebidas com:")
        logger.info(f"ano_letivo_id: {ano_letivo_id}")
        logger.info(f"data_inicio: {data_inicio}")
        logger.info(f"series: {series}")
        transferencias_recebidas = contar_transferencias_recebidas(cursor, ano_letivo_id, data_inicio, series)
        
        # Se o ano letivo terminou, buscar aprovações/reprovações
        hoje = datetime.date.today()
        if hoje > data_fim:
            dados_aprovacao = {serie: contar_aprovacoes_reprovacoes(cursor, ano_letivo_id, serie) for serie in series}
    
    # Processar dados de transferências e evasões
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
    
    # Contar transferências por série e sexo usando a função do Dashboard
    transferidos_dashboard = contar_transferencias_por_serie_sexo(df, '1_5', series)
    
    # Atualizar linhas da tabela
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
    
    # Adicionar aprovações/reprovações se o ano letivo terminou
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
        # Se o ano não terminou, manter as linhas com "--"
        data.extend([
            [quebra_linha("ALUNOS APROVADOS")] + ["--"]*13,
            [quebra_linha("ALUNOS REPROVADOS")] + ["--"]*13
        ])
    
    # Adicionar contagem de turmas usando uma nova conexão
    with get_cursor() as cursor:
        query_turmas = """
        SELECT s.nome as serie, COUNT(DISTINCT t.id) as total_turmas
        FROM turmas t
        JOIN serie s ON t.serie_id = s.id
        WHERE t.ano_letivo_id = %s
        GROUP BY s.nome
        """
        cursor.execute(query_turmas, (ano_letivo_id,))
        turmas = {r['serie']: r['total_turmas'] for r in cursor.fetchall()}
    
    # Criar lista com número de turmas por série
    turmas_por_serie = []
    total_turmas = 0
    for serie in series:
        num_turmas = turmas.get(serie, 0)
        turmas_por_serie.extend([num_turmas, num_turmas])  # Mesmo número para M e F
        total_turmas += num_turmas
    
    data.append([quebra_linha("Nº de TURMAS")] + 
                turmas_por_serie +  # Lista com números repetidos para M/F
                [total_turmas, total_turmas, total_turmas])  # Total e Total Geral
    
    # Criar tabela com estilo
    colWidths = [2.5*inch] + [0.35*inch]*12 + [inch]
    table = Table(data, colWidths=colWidths)
    
    # Cores personalizadas
    cor_cabecalho = HexColor('#1B4F72')
    cor_subcabecalho = HexColor('#2874A6')
    cor_texto = black
    cor_linha_clara = Color(0.95, 0.95, 0.95)
    cor_borda = black
    
    table.setStyle(TableStyle([
        # Estilo do cabeçalho
        ('BACKGROUND', (0, 0), (-1, 2), cor_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 2), 'white'),
        ('FONTNAME', (0, 0), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 2), 11),
        
        # Estilo do corpo da tabela
        ('FONTNAME', (0, 3), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 3), (-1, -1), 10),
        ('TEXTCOLOR', (0, 3), (-1, -1), cor_texto),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Linhas alternadas
        ('BACKGROUND', (0, 4), (-1, 4), cor_linha_clara),
        ('BACKGROUND', (0, 6), (-1, 6), cor_linha_clara),
        ('BACKGROUND', (0, 8), (-1, 8), cor_linha_clara),
        ('BACKGROUND', (0, 10), (-1, 10), cor_linha_clara),
        
        # Bordas e grades
        ('GRID', (0, 0), (-1, -1), 0.5, cor_borda),
        ('BOX', (0, 0), (-1, -1), 1, cor_borda),
        ('LINEBELOW', (0, 2), (-1, 2), 1, cor_borda),
        
        # Espaçamento e padding
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        
        # Spans necessários
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
        
        # Destaque para primeira coluna
        ('FONTNAME', (0, 3), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 3), (0, -1), 'LEFT'),
    ]))
    
    elements.append(table)

def gerar_relatorio_6_9(elements, cabecalho, figura_inferior, mes):
    ano_letivo = 2025
    
    # Conectar ao banco para obter as datas do ano letivo
    from db.connection import get_cursor
    with get_cursor() as cursor:
        # Buscar datas do ano letivo
        cursor.execute("SELECT id, data_inicio, data_fim FROM anosletivos WHERE ano_letivo = %s", (ano_letivo,))
        datas_ano_letivo = cursor.fetchone()

    if not datas_ano_letivo:
        logger.info("Ano letivo não encontrado")
        return

    data_inicio = datas_ano_letivo['data_inicio']
    data_fim = datas_ano_letivo['data_fim']
    ano_letivo_id = datas_ano_letivo['id']
    
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        return

    df = pd.DataFrame(dados_aluno)

    # Adicionar cabeçalho informativo
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
    
    # Informações da escola
    info_data = [
        [Paragraph(f"<b>MÊS:</b> {get_nome_mes(mes)}", estilo_info), 
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
    
    # Buscar dias letivos do mês atual usando uma nova conexão
    with get_cursor() as cursor:
        dias_letivos = buscar_dias_letivos(cursor, ano_letivo, mes)
    
    # Informações sobre salas e dias letivos
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
    
    # Checkboxes para dependência administrativa
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
    
    # Séries do 6º ao 9º ano
    series = ['6º Ano A', '6º Ano B', '7º Ano', '8º Ano', '9º Ano']
    
    # Contar alunos - matrícula inicial
    contagem_inicial = contar_alunos_por_serie_sexo(df, data_inicio, 'inicial', '6_9')
    total_m_inicial = sum(serie['M'] for serie in contagem_inicial.values())
    total_f_inicial = sum(serie['F'] for serie in contagem_inicial.values())
    total_geral_inicial = total_m_inicial + total_f_inicial
    
    # Contar alunos - matrícula atual
    contagem_atual = contar_alunos_por_serie_sexo(df, series_range='6_9')
    total_m_atual = sum(serie['M'] for serie in contagem_atual.values())
    total_f_atual = sum(serie['F'] for serie in contagem_atual.values())
    total_geral_atual = total_m_atual + total_f_atual
    
    # Preparar dados de movimentação mensal
    # Usar uma nova conexão para buscar dados de movimentação
    with get_cursor() as cursor:
        dados_movimentacao = {serie: contar_movimentacao_mensal(cursor, ano_letivo_id, mes, serie) for serie in series}
        
        # Contar transferências recebidas
        transferencias_recebidas = contar_transferencias_recebidas(cursor, ano_letivo_id, data_inicio, series)
    
    # Se o ano letivo terminou, buscar aprovações/reprovações
    hoje = datetime.date.today()
    
    # Processar dados de transferências e evasões
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
    
    # Contar transferências por série e sexo usando a função do Dashboard
    transferidos_dashboard = contar_transferencias_por_serie_sexo(df, '6_9', series)
    
    # Atualizar linhas da tabela
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
    
    # Adicionar aprovações/reprovações se o ano letivo terminou
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
        # Se o ano não terminou, manter as linhas com "--"
        data.extend([
            [quebra_linha("ALUNOS APROVADOS")] + ["--"]*11,
            [quebra_linha("ALUNOS REPROVADOS")] + ["--"]*11
        ])
    
    # Adicionar contagem de turmas usando uma nova conexão
    with get_cursor() as cursor:
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
    
    # Criar lista com número de turmas por série
    turmas_por_serie = []
    total_turmas = 0
    for serie in series:
        num_turmas = turmas.get(serie, 0)
        turmas_por_serie.extend([num_turmas, num_turmas])  # Mesmo número para M e F
        total_turmas += num_turmas
    
    data.append([quebra_linha("Nº de TURMAS")] + 
                turmas_por_serie +  # Lista com números repetidos para M/F
                [total_turmas, total_turmas, total_turmas])  # Total e Total Geral
    
    # Criar tabela com estilo
    colWidths = [2.5*inch] + [0.35*inch]*12 + [inch]
    table = Table(data, colWidths=colWidths)
    
    # Cores personalizadas
    cor_cabecalho = HexColor('#1B4F72')
    cor_subcabecalho = HexColor('#2874A6')
    cor_texto = black
    cor_linha_clara = Color(0.95, 0.95, 0.95)
    cor_borda = black
    
    table.setStyle(TableStyle([
        # Estilo do cabeçalho
        ('BACKGROUND', (0, 0), (-1, 2), cor_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 2), 'white'),
        ('FONTNAME', (0, 0), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 2), 11),
        
        # Estilo do corpo da tabela
        ('FONTNAME', (0, 3), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 3), (-1, -1), 10),
        ('TEXTCOLOR', (0, 3), (-1, -1), cor_texto),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Linhas alternadas
        ('BACKGROUND', (0, 4), (-1, 4), cor_linha_clara),
        ('BACKGROUND', (0, 6), (-1, 6), cor_linha_clara),
        ('BACKGROUND', (0, 8), (-1, 8), cor_linha_clara),
        ('BACKGROUND', (0, 10), (-1, 10), cor_linha_clara),
        
        # Bordas e grades
        ('GRID', (0, 0), (-1, -1), 0.5, cor_borda),
        ('BOX', (0, 0), (-1, -1), 1, cor_borda),
        ('LINEBELOW', (0, 2), (-1, 2), 1, cor_borda),
        
        # Espaçamento e padding
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        
        # Spans necessários
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
        
        # Destaque para primeira coluna
        ('FONTNAME', (0, 3), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 3), (0, -1), 'LEFT'),
    ]))
    
    elements.append(table)

def parse_turma_nome(turma_nome):
    """Extrai o número do ano e a letra da turma (se houver) para ordenação.
       Retorna uma tupla (ano, letra_ordinal) ou (None, None) se não encontrar."""
    if not isinstance(turma_nome, str):
        return (None, None)
    
    match = re.match(r'(\d+)º?\s*Ano\s*([A-Z])?', turma_nome.strip(), re.IGNORECASE)
    if match:
        ano = int(match.group(1))
        letra = match.group(2)
        letra_ordinal = ord(letra) - ord('A') if letra else -1 # -1 para turmas sem letra
        return (ano, letra_ordinal)
    return (None, None)

def contar_transferencias_por_serie_sexo(df, series_range, series):
    logger.info("\n=== Iniciando contagem de transferências por série e sexo ===")
    logger.info(f"Series range: {series_range}")
    logger.info(f"Series: {series}")
    
    # Inicializa o dicionário de contagem
    contagem = {}
    
    # Filtra apenas os alunos transferidos
    df_transferidos = df[
        (df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])) & 
        (df['DATA_TRANSFERENCIA'].notna())
    ]
    
    logger.info(f"\nTotal de alunos no DataFrame: {len(df)}")
    logger.info(f"Total de alunos transferidos encontrados: {len(df_transferidos)}")
    
    if len(df_transferidos) > 0:
        logger.info("\nExemplo de dados dos alunos transferidos:")
        logger.info(df_transferidos[['NOME DO ALUNO', 'SEXO', 'NOME_SERIE', 'SITUAÇÃO', 'DATA_TRANSFERENCIA', 'HISTORICO_TRANSFERENCIA']].head())
    
    # Processa cada série
    for serie in series:
        # Filtra alunos da série atual
        if series_range == '6_9' and '6º Ano' in serie:
            # Para 6º ano, precisa considerar a turma (A ou B)
            df_serie = df_transferidos[
                (df_transferidos['NOME_SERIE'] == '6º Ano') & 
                (df_transferidos['NOME_TURMA'] == serie.split()[-1])
            ]
        else:
            # Para outras séries, filtra apenas pelo nome da série
            df_serie = df_transferidos[df_transferidos['NOME_SERIE'] == serie]
        
        # Conta por sexo
        masculino = len(df_serie[df_serie['SEXO'] == 'M'])
        feminino = len(df_serie[df_serie['SEXO'] == 'F'])
        
        logger.info(f"\nSérie {serie}:")
        logger.info(f"Total de transferidos: {len(df_serie)}")
        logger.info(f"Masculino: {masculino}")
        logger.info(f"Feminino: {feminino}")
        
        # Armazena a contagem
        contagem[serie] = {'M': masculino, 'F': feminino}
    
    logger.info("\nContagem final de transferências por série e sexo:")
    for serie, counts in contagem.items():
        logger.info(f"{serie}: M={counts['M']}, F={counts['F']}")
    
    return contagem

def gerar_relatorio_mensal(mes, ano, cabecalho, figura_superior, figura_inferior):
    # Criar documento PDF
    doc, buffer = create_pdf_buffer()
    elements = []
    
    # Adicionar capa
    add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior, mes)
    
    # Adicionar cabeçalho em todas as páginas
    add_header(doc, elements, cabecalho, figura_superior, figura_inferior)

def gerar_lista_alunos_transferidos():
    """
    Gera uma lista detalhada dos alunos transferidos (TRANSFERÊNCIAS EXPEDIDAS)
    """
    ano_letivo = 2025
    
    # Busca os dados dos alunos
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        logger.info("Nenhum dado de aluno encontrado.")
        return

    # Converte para DataFrame
    df = pd.DataFrame(dados_aluno)
    
    # Filtra apenas alunos transferidos usando a mesma lógica do movimento mensal
    # Status Transferido/Transferida E DATA_TRANSFERENCIA não nula
    df_transferidos = df[
        (df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])) &
        (df['DATA_TRANSFERENCIA'].notna())
    ].copy()
    
    if df_transferidos.empty:
        logger.info("Nenhum aluno transferido encontrado.")
        return
    
    logger.info(f"Total de alunos transferidos: {len(df_transferidos)}")

    # Configuração do PDF
    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    figura_inferior = os.path.join(os.path.dirname(__file__), 'logopaco.png')
    doc, buffer = create_pdf_buffer(pagesize=landscape(letter))
    elements = []

    # Cabeçalho
    img = Image(figura_inferior, width=3 * inch, height=0.7 * inch)
    header_style = ParagraphStyle(name='Header', fontSize=12, alignment=1)
    data = [
        [img],
        [Paragraph('<br/>'.join(cabecalho), header_style)]
    ]
    table = Table(data, colWidths=[7 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.25 * inch))
    
    # Título
    titulo_style = ParagraphStyle(name='TituloTransferidos', fontSize=16, alignment=1)
    elements.append(Paragraph(
        f"<b>TRANSFERÊNCIAS EXPEDIDAS - {ano_letivo}</b>",
        titulo_style
    ))
    elements.append(Spacer(1, 0.1 * inch))
    
    subtitulo_style = ParagraphStyle(name='SubtituloTransferidos', fontSize=14, alignment=1)
    elements.append(Paragraph(
        "<b>Lista de Alunos Transferidos</b>",
        subtitulo_style
    ))
    elements.append(Spacer(1, 0.15 * inch))

    # Estatísticas
    total = len(df_transferidos)
    masculino = (df_transferidos['SEXO'] == 'M').sum()
    feminino = (df_transferidos['SEXO'] == 'F').sum()
    
    stats_style = ParagraphStyle(name='StatsTransferidos', fontSize=12, alignment=0)
    elements.append(Paragraph(
        f"<b>TOTAL: {total} alunos | Masculino: {masculino} | Feminino: {feminino}</b>",
        stats_style
    ))
    elements.append(Spacer(1, 0.2 * inch))

    # Ordena por data de transferência (mais recente primeiro) e depois por nome
    df_transferidos = df_transferidos.sort_values(['DATA_TRANSFERENCIA', 'NOME DO ALUNO'], ascending=[False, True])

    # Tabela de alunos
    from biblio_editor import formatar_telefone
    tel_style = ParagraphStyle(name='Telefones', fontSize=9)
    escola_style = ParagraphStyle(name='Escola', fontSize=8)
    
    data_table: list[list[Any]] = [
        ['Nº', 'Nome', 'Série/Turma', 'Turno', 'Data Transferência', 'Escola Destino', 'Telefones']
    ]
    
    for row_num, (index, row) in enumerate(df_transferidos.iterrows(), start=1):
        nome = row['NOME DO ALUNO']
        serie_turma = f"{row['NOME_SERIE']} {row['NOME_TURMA']}"
        turno = row['TURNO']
        data_transf = row['DATA_TRANSFERENCIA'].strftime('%d/%m/%Y') if row['DATA_TRANSFERENCIA'] else "N/D"
        
        # Escola destino
        escola_destino = row.get('ESCOLA_DESTINO', None)
        escola_destino_texto = escola_destino if escola_destino else "N/I"
        
        # Formata telefones
        telefones = ""
        if row['TELEFONES']:
            telefones_lista = row['TELEFONES'].split('/')
            telefones_formatados = [formatar_telefone(tel) for tel in telefones_lista]
            telefones = '<br/>'.join(telefones_formatados)
        
        data_table.append([
            row_num,
            nome,
            serie_turma,
            turno,
            data_transf,
            Paragraph(escola_destino_texto, escola_style),
            Paragraph(telefones, tel_style)
        ])

    # Cria a tabela
    table = Table(data_table, colWidths=[
        0.4 * inch,  # Nº
        2.5 * inch,  # Nome
        1.0 * inch,  # Série/Turma
        0.7 * inch,  # Turno
        1.1 * inch,  # Data Transferência
        2.2 * inch,  # Escola Destino
        1.8 * inch   # Telefones
    ])
    
    cor_cabecalho = HexColor('#1B4F72')
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), cor_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Nome alinhado à esquerda
        ('FONTSIZE', (0, 1), (-1, -1), 9),   # Fonte menor para o conteúdo
    ])
    table.setStyle(table_style)
    elements.append(table)

    # Gera o PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Salva o PDF
    salvar_e_abrir_pdf(buffer)
    logger.info("Relatório de alunos transferidos gerado com sucesso!")

def gerar_lista_alunos_matriculados_depois():
    """
    Gera uma lista detalhada dos alunos matriculados após o início do ano letivo (TRANSFERÊNCIAS RECEBIDAS)
    Usa a MESMA query SQL do movimento mensal para garantir números exatos.
    """
    ano_letivo = 2025
    
    # Busca a data de início do ano letivo e o ID
    with get_cursor() as cursor:
        cursor.execute("SELECT id, data_inicio FROM anosletivos WHERE ano_letivo = %s", (ano_letivo,))
        resultado = cursor.fetchone()
        if not resultado:
            logger.info("Ano letivo não encontrado.")
            return
        data_inicio = resultado['data_inicio']
        ano_letivo_id = resultado['id']
    
    logger.info(f"Data de início do ano letivo: {data_inicio}")

    # Usa a MESMA query do movimento mensal para buscar os dados
    with get_cursor() as cursor:
        query = """
            SELECT
                a.nome AS nome_aluno,
                a.sexo,
                s.nome AS serie,
                t.nome AS turma,
                t.turno,
                m.data_matricula,
                m.status,
                e_origem.nome AS escola_origem,
                GROUP_CONCAT(DISTINCT r.telefone ORDER BY r.id SEPARATOR '/') AS telefones,
                CASE
                    WHEN s.nome = '6º Ano' THEN CONCAT(s.nome, ' ', t.nome)
                    ELSE s.nome
                END as serie_completa
            FROM turmas t
            JOIN matriculas m ON t.id = m.turma_id
            JOIN serie s ON t.serie_id = s.id
            JOIN alunos a ON m.aluno_id = a.id
            LEFT JOIN ResponsaveisAlunos ra ON a.id = ra.aluno_id
            LEFT JOIN Responsaveis r ON ra.responsavel_id = r.id
            LEFT JOIN escolas e_origem ON m.escola_origem_id = e_origem.id
            WHERE m.ano_letivo_id = %s
            AND a.escola_id = 60
            AND (
                (m.data_matricula > %s AND m.status IN ('Ativo', 'Transferido', 'Transferida'))
                OR 
                (m.data_matricula = %s AND m.status = 'Ativo')
            )
            GROUP BY a.id, a.nome, a.sexo, s.nome, t.nome, t.turno, m.data_matricula, m.status, e_origem.nome
            ORDER BY m.data_matricula DESC, a.nome
        """
        cursor.execute(query, (ano_letivo_id, data_inicio, data_inicio))
        alunos = cursor.fetchall()
    
    if not alunos:
        logger.info("Nenhum aluno matriculado após o início do ano letivo.")
        return
    
    # Converte para DataFrame
    df_filtrado = pd.DataFrame(alunos)
    
    logger.info(f"Total de alunos matriculados após o início: {len(df_filtrado)}")
    logger.info(f"Por turno - MAT: {len(df_filtrado[df_filtrado['turno'] == 'MAT'])}, VESP: {len(df_filtrado[df_filtrado['turno'] == 'VESP'])}")

    # Configuração do PDF
    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    figura_inferior = os.path.join(os.path.dirname(__file__), 'logopaco.png')
    doc, buffer = create_pdf_buffer(pagesize=landscape(letter))
    elements = []

    # Cabeçalho
    img = Image(figura_inferior, width=3 * inch, height=0.7 * inch)
    header_style = ParagraphStyle(name='Header', fontSize=12, alignment=1)
    data = [
        [img],
        [Paragraph('<br/>'.join(cabecalho), header_style)]
    ]
    table = Table(data, colWidths=[7 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.25 * inch))
    
    # Título
    titulo_style = ParagraphStyle(name='TituloMatriculados', fontSize=16, alignment=1)
    elements.append(Paragraph(
        f"<b>TRANSFERÊNCIAS RECEBIDAS - {ano_letivo}</b>",
        titulo_style
    ))
    elements.append(Spacer(1, 0.1 * inch))
    
    subtitulo_style = ParagraphStyle(name='SubtituloMatriculados', fontSize=14, alignment=1)
    elements.append(Paragraph(
        f"<b>Alunos Matriculados Após {data_inicio.strftime('%d/%m/%Y')}</b>",
        subtitulo_style
    ))
    elements.append(Spacer(1, 0.15 * inch))

    # Estatísticas
    total = len(df_filtrado)
    masculino = (df_filtrado['sexo'] == 'M').sum()
    feminino = (df_filtrado['sexo'] == 'F').sum()
    ativos = (df_filtrado['status'] == 'Ativo').sum()
    transferidos = (df_filtrado['status'].isin(['Transferido', 'Transferida'])).sum()
    
    stats_style = ParagraphStyle(name='StatsMatriculados', fontSize=12, alignment=0)
    elements.append(Paragraph(
        f"<b>TOTAL: {total} alunos | Masculino: {masculino} | Feminino: {feminino} | "
        f"Ativos: {ativos} | Transferidos: {transferidos}</b>",
        stats_style
    ))
    elements.append(Spacer(1, 0.2 * inch))

    # Ordena por data de matrícula (mais recente primeiro) e depois por nome
    df_filtrado = df_filtrado.sort_values(['data_matricula', 'nome_aluno'], ascending=[False, True])

    # Tabela de alunos
    from biblio_editor import formatar_telefone
    tel_style = ParagraphStyle(name='Telefones', fontSize=9)
    sit_style = ParagraphStyle(name='Situacao', fontSize=9)
    escola_style = ParagraphStyle(name='Escola', fontSize=8)
    
    data_table: list[list[Any]] = [
        ['Nº', 'Nome', 'Série/Turma', 'Turno', 'Data Matrícula', 'Escola Origem', 'Situação', 'Telefones']
    ]
    
    for row_num, (index, row) in enumerate(df_filtrado.iterrows(), start=1):
        nome = row['nome_aluno']
        serie_turma = f"{row['serie']} {row['turma']}"
        turno = row['turno']
        data_matricula = row['data_matricula'].strftime('%d/%m/%Y') if row['data_matricula'] else "N/D"
        
        # Escola origem
        escola_origem = row.get('escola_origem', None)
        escola_origem_texto = escola_origem if escola_origem else "N/I"
        
        # Formata a situação
        situacao = row['status']
        if situacao in ['Transferido', 'Transferida']:
            situacao_texto = f"<font color='red'><b>{situacao}</b></font>"
        else:
            situacao_texto = f"<font color='green'><b>{situacao}</b></font>"
        
        # Formata telefones
        telefones = ""
        if row['telefones']:
            telefones_lista = row['telefones'].split('/')
            telefones_formatados = [formatar_telefone(tel) for tel in telefones_lista]
            telefones = '<br/>'.join(telefones_formatados)
        
        data_table.append([
            row_num,
            nome,
            serie_turma,
            turno,
            data_matricula,
            Paragraph(escola_origem_texto, escola_style),
            Paragraph(situacao_texto, sit_style),
            Paragraph(telefones, tel_style)
        ])

    # Cria a tabela
    table = Table(data_table, colWidths=[
        0.4 * inch,  # Nº
        2.2 * inch,  # Nome
        0.9 * inch,  # Série/Turma
        0.7 * inch,  # Turno
        1.0 * inch,  # Data Matrícula
        2.0 * inch,  # Escola Origem
        0.8 * inch,  # Situação
        1.6 * inch   # Telefones
    ])
    
    cor_cabecalho = HexColor('#1B4F72')
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), cor_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Nome alinhado à esquerda
        ('FONTSIZE', (0, 1), (-1, -1), 9),   # Fonte menor para o conteúdo
    ])
    table.setStyle(table_style)
    elements.append(table)

    # Gera o PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Salva o PDF
    salvar_e_abrir_pdf(buffer)
    logger.info("Relatório de alunos matriculados após o início gerado com sucesso!")

# relatorio_movimentacao_mensal()
# gerar_lista_alunos_transferidos()
# gerar_lista_alunos_matriculados_depois()