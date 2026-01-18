from src.core.config_logs import get_logger
logger = get_logger(__name__)
import io
import os
import pandas as pd
from src.core.config import get_image_path, ANO_LETIVO_ATUAL
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, PageTemplate, Frame
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, grey, HexColor
from src.core.conexao import conectar_bd
from src.relatorios.gerar_pdf import salvar_e_abrir_pdf
from scripts.auxiliares.biblio_editor import formatar_telefone, formatar_cpf
from typing import Any, cast

def fetch_students_with_disorders(ano_letivo):
    """Busca alunos que possuem algum tipo de transtorno registrado"""
    conn: Any = conectar_bd()
    if not conn:
        logger.info("Não foi possível conectar ao banco de dados.")
        return None
    cursor: Any = cast(Any, conn).cursor(dictionary=True)

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
            m.status = 'Ativo'
        AND
            a.descricao_transtorno IS NOT NULL
        AND
            a.descricao_transtorno != ''
        AND
            a.descricao_transtorno != 'Nenhum'
        AND
            a.descricao_transtorno != 'ASMÁTICO (MODERADO)'
        GROUP BY 
            a.id, a.nome, a.sexo, a.data_nascimento, a.descricao_transtorno,
            s.nome, s.id, t.nome, t.turno, m.status, f.nome
        ORDER BY
            s.id, t.nome, t.turno, a.nome;
    """
    try:
        cursor.execute(query, (ano_letivo,))
        dados_aluno = cursor.fetchall()
        logger.info(f"Total de alunos com transtornos encontrados: {len(dados_aluno)}")
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

def format_phone_numbers(telefones):
    """Formata os números de telefone"""
    if not telefones:
        return ""
    
    telefones_lista = telefones.split('/')
    telefones_formatados = [formatar_telefone(tel) for tel in telefones_lista]
    
    grupos = []
    for i in range(0, len(telefones_lista), 1):
        grupo = telefones_formatados[i:i+1]
        grupos.append('/'.join(grupo))
    
    return '<br/>'.join(grupos)

def add_class_table_disorders(elements, turma_df, nome_serie, nome_turma, turno, nome_professor, figura_inferior, cabecalho):
    """Adiciona tabela com alunos com transtornos de uma turma específica"""
    
    # Converte a abreviação do turno para o nome completo
    turno_completo = "MATUTINO" if turno == "MAT" else "VESPERTINO"
    
    elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno_completo} - {datetime.datetime.now().year}</b>", 
                             ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(f"<b>PROFESSOR@: {nome_professor} </b>", 
                             ParagraphStyle(name='ProfessoraTitulo', fontSize=12, alignment=0)))
    elements.append(Spacer(1, 0.15 * inch))
    
    # Calcula totais
    total_alunos = len(turma_df)
    total_masculino = turma_df[turma_df['SEXO'] == 'M'].shape[0]
    total_feminino = turma_df[turma_df['SEXO'] == 'F'].shape[0]
    
    elements.append(Paragraph(f"ALUNOS COM TRANSTORNOS: MASCULINO ({total_masculino}) FEMININO ({total_feminino}) - TOTAL: {total_alunos}", 
                             ParagraphStyle(name='TotaisAlunos', fontSize=12, alignment=0)))
    elements.append(Spacer(1, 0.15 * inch))

    # Prepara os dados da tabela
    data = [['Nº', 'Nome', 'Nascimento', 'CPF', 'Transtorno', 'Responsáveis', 'Telefones']]
    
    # Ordena o DataFrame pelo nome do aluno
    turma_df = turma_df.sort_values('NOME DO ALUNO')
    
    for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
        nome = row['NOME DO ALUNO']
        nascimento = row['NASCIMENTO'].strftime('%d/%m/%Y') if row['NASCIMENTO'] else "Data não disponível"
        cpf = formatar_cpf(row['CPF'])
        transtorno = row['TRANSTORNO']
        responsaveis = row['RESPONSAVEIS'] if row['RESPONSAVEIS'] else ""
        telefones_raw = row['TELEFONES'] if row['TELEFONES'] else ""
        
        # Formata telefones
        telefones = format_phone_numbers(telefones_raw)
        
        data.append([
            row_num, 
            nome, 
            nascimento, 
            cpf, 
            transtorno,
            Paragraph(responsaveis, ParagraphStyle(name='Responsavel', fontSize=9, alignment=0)),
            Paragraph(telefones, ParagraphStyle(name='Telefone', fontSize=9, alignment=0))
        ])  # type: ignore[arg-type]

    # Define larguras das colunas
    col_widths = [30, 120, 70, 70, 90, 100, 75]
    
    # Cria a tabela
    table = Table(data, colWidths=col_widths)
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('FONTSIZE', (0, 1), (-1, -1), 8)
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))

def add_summary_table(elements, df, figura_inferior, cabecalho):
    """Adiciona uma tabela resumo com estatísticas dos transtornos"""
    
    elements.append(Paragraph("<b>RESUMO GERAL - ALUNOS COM TRANSTORNOS</b>", 
                             ParagraphStyle(name='ResumoTitulo', fontSize=16, alignment=1)))
    elements.append(Spacer(1, 0.3 * inch))

    # Estatísticas gerais
    total_alunos = len(df)
    total_masculino = len(df[df['SEXO'] == 'M'])
    total_feminino = len(df[df['SEXO'] == 'F'])
    
    # Tabela de estatísticas gerais
    stats_data = [
        ['Categoria', 'Masculino', 'Feminino', 'Total'],
        ['Alunos com Transtornos', str(total_masculino), str(total_feminino), str(total_alunos)]
    ]
    
    stats_table = Table(stats_data, colWidths=[3 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
    stats_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#003452')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#e9edf5')),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ])
    stats_table.setStyle(stats_style)
    elements.append(stats_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Distribuição por tipo de transtorno
    transtornos_count = df['TRANSTORNO'].value_counts()
    
    transtornos_data = [['Tipo de Transtorno', 'Quantidade', 'Percentual']]
    for transtorno, count in transtornos_count.items():
        percentual = (count / total_alunos) * 100
        transtornos_data.append([transtorno, str(count), f"{percentual:.1f}%"])
    
    transtornos_table = Table(transtornos_data, colWidths=[4 * inch, 1.5 * inch, 1.5 * inch])
    transtornos_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#003452')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f0f0f0')),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ])
    transtornos_table.setStyle(transtornos_style)
    elements.append(transtornos_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Distribuição por turma
    turmas_data = [['Série/Turma', 'Turno', 'Quantidade']]
    grupos = df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO'])
    for (serie, turma, turno), grupo in grupos:
        turno_completo = "Matutino" if turno == "MAT" else "Vespertino"
        turmas_data.append([f"{serie} {turma}", turno_completo, str(len(grupo))])
    
    turmas_table = Table(turmas_data, colWidths=[3 * inch, 2 * inch, 2 * inch])
    turmas_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#003452')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f0f0f0')),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ])
    turmas_table.setStyle(turmas_style)
    elements.append(turmas_table)
    elements.append(PageBreak())

def lista_alunos_transtornos():
    """Função principal que gera o relatório de alunos com transtornos"""
    ano_letivo = ANO_LETIVO_ATUAL
    dados_aluno = fetch_students_with_disorders(ano_letivo)
    
    if not dados_aluno:
        logger.info("Nenhum aluno com transtorno encontrado.")
        return

    df = pd.DataFrame(dados_aluno)
    
    if df.empty:
        logger.info("Nenhum aluno com transtorno encontrado.")
        return

    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    figura_inferior = str(get_image_path('logopaco.png'))

    # Cria o documento
    buffer = io.BytesIO()
    left_margin = 36
    right_margin = 18
    top_margin = 10
    bottom_margin = 18

    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        leftMargin=left_margin, 
        rightMargin=right_margin, 
        topMargin=top_margin, 
        bottomMargin=bottom_margin
    )
    
    elements = []

    # Adiciona página de capa
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
    elements.append(Paragraph("<b>RELAÇÃO DE ALUNOS COM TRANSTORNOS</b>", 
                             ParagraphStyle(name='Capa', fontSize=24, alignment=1)))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("Organizado por Turma", 
                             ParagraphStyle(name='Subtitulo', fontSize=16, alignment=1)))
    elements.append(Spacer(1, 4.7 * inch))
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", 
                             ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
    elements.append(PageBreak())

    # Ordena as turmas por série e nome da turma
    turmas_ordenadas = sorted(df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']), 
                            key=lambda x: (x[0][0], x[0][1]))

    # Adiciona as tabelas de alunos por turma
    for (nome_serie, nome_turma, turno), turma_df in turmas_ordenadas:
        logger.info(f"Processando: {nome_serie} {nome_turma} {turno} - {len(turma_df)} alunos com transtorno")
        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Não informado'
        
        add_class_table_disorders(elements, turma_df, nome_serie, nome_turma, turno, 
                                 nome_professor, figura_inferior, cabecalho)

    # Constrói o documento
    doc.build(elements)
    buffer.seek(0)

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
            from src.utils.utilitarios.tipos_documentos import TIPO_LISTA_ATUALIZADA

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            try:
                tmp.write(buffer.getvalue())
                tmp.close()
                descricao = f"Alunos com Transtornos - {datetime.datetime.now().year}"
                try:
                    salvar_documento_sistema(tmp.name, TIPO_LISTA_ATUALIZADA, funcionario_id=1, finalidade='Secretaria', descricao=descricao)
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
    logger.info("Relatório gerado com sucesso!")

# Executar a função
if __name__ == "__main__":
    lista_alunos_transtornos()
