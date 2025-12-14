from src.core.config_logs import get_logger
logger = get_logger(__name__)
import os
import datetime
import pandas as pd
from src.core.config import get_image_path
from reportlab.lib.colors import black, white, grey
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from src.core.conexao import conectar_bd
from src.relatorios.listas.lista_atualizada import data_ano_letivo, create_pdf_buffer, add_cover_page, format_phone_numbers
from src.relatorios.gerar_pdf import salvar_e_abrir_pdf
from scripts.auxiliares.biblio_editor import formatar_telefone
from typing import Any, cast


def buscar_contatos_alunos(ano_letivo: int):
    conn: Any = conectar_bd()
    if not conn:
        logger.info("Não foi possível conectar ao banco de dados.")
        return []
    cursor: Any = cast(Any, conn).cursor(dictionary=True)

    # Debug: verificar ano letivo
    logger.info(f"Buscando contatos para ano letivo: {ano_letivo}")
    
    # Verificar se o ano letivo existe
    try:
        cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = %s", (ano_letivo,))
        ano_result = cursor.fetchone()
        if not ano_result:
            logger.warning(f"Ano letivo {ano_letivo} não encontrado na tabela anosletivos")
            return []
        logger.info(f"ID do ano letivo: {ano_result['id']}")
    except Exception as e:
        logger.error(f"Erro ao verificar ano letivo: {e}")
        return []

    query = """
        SELECT 
            a.nome AS ALUNO,
            s.nome AS NOME_SERIE,
            COALESCE(NULLIF(t.nome, ''), t.turno) AS NOME_TURMA,
            t.turno AS TURNO,
            GROUP_CONCAT(DISTINCT r.nome ORDER BY r.id SEPARATOR ', ') AS RESPONSAVEIS,
            GROUP_CONCAT(DISTINCT r.telefone ORDER BY r.id SEPARATOR '/') AS TELEFONES
        FROM alunos a
        JOIN matriculas m ON a.id = m.aluno_id
        JOIN turmas t ON m.turma_id = t.id
        JOIN series s ON t.serie_id = s.id
        LEFT JOIN responsaveisalunos ra ON a.id = ra.aluno_id
        LEFT JOIN responsaveis r ON ra.responsavel_id = r.id
        WHERE m.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = %s)
          AND a.escola_id = 60
        GROUP BY a.id, a.nome, s.nome, t.nome, t.turno
        ORDER BY s.nome, t.nome, a.nome
    """
    try:
        cursor.execute(query, (ano_letivo,))
        registros = cursor.fetchall()
        logger.info(f"Total de registros encontrados: {len(registros)}")
        return registros
    except Exception as e:
        logger.error("Erro ao executar a consulta: %s", str(e))
        return []
    finally:
        try:
            cast(Any, cursor).close()
        except Exception:
            pass
        try:
            cast(Any, conn).close()
        except Exception:
            pass


def formatar_responsaveis_multilinha(responsaveis_concatenados: str) -> str:
    if not responsaveis_concatenados:
        return ''
    nomes = [n.strip() for n in responsaveis_concatenados.split(',') if n and n.strip()]
    return '<br/>'.join(nomes)


def add_contacts_table(elements, turma_df, nome_serie, nome_turma, turno, figura_inferior, cabecalho):
    # Cabeçalho por página/turma no mesmo modelo
    datacabecalho = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
    ]
    tablecabecalho = Table(datacabecalho, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    tablecabecalho.setStyle(table_style)
    elements.append(tablecabecalho)

    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.15 * inch))

    data: list[list[Any]] = [['Nº', 'Nome', 'Responsáveis', 'Telefone']]
    for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
        nome = row['ALUNO']
        responsaveis = formatar_responsaveis_multilinha(row['RESPONSAVEIS'] or '')
        telefones = format_phone_numbers(row['TELEFONES'])
        data.append([
            row_num,
            nome,
            Paragraph(responsaveis, ParagraphStyle(name='Responsaveis', fontSize=10)),
            Paragraph(telefones, ParagraphStyle(name='Telefones', fontSize=10))
        ])

    # Larguras ajustadas para melhor quebra e aproveitamento da página (total ~7.75in)
    table = Table(data, colWidths=[0.35 * inch, 2.8 * inch, 2.95 * inch, 1.65 * inch])
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(PageBreak())


def gerar_pdf_contatos(ano_letivo: int):
    registros = buscar_contatos_alunos(ano_letivo)
    if not registros:
        logger.info('Nenhum dado encontrado.')
        from tkinter import messagebox
        messagebox.showinfo("Info", "Nenhum dado encontrado para gerar o relatório.")
        return None

    df = pd.DataFrame(registros)

    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    figura_superior = str(get_image_path('logosemed.png'))
    figura_inferior = str(get_image_path('logopaco.png'))

    doc, buffer = create_pdf_buffer()
    elements = []

    add_cover_page(doc, elements, cabecalho, figura_superior, figura_inferior)

    # Gera as tabelas por turma
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        add_contacts_table(elements, turma_df, nome_serie, nome_turma, turno, figura_inferior, cabecalho)

    doc.build(elements)
    buffer.seek(0)
    
    # Salvar e abrir o PDF
    try:
        saved_path = salvar_e_abrir_pdf(buffer)
        logger.info(f"PDF de contatos gerado: {saved_path}")
        return saved_path
    except Exception as e:
        logger.exception(f"Erro ao salvar PDF: {e}")
        from tkinter import messagebox
        messagebox.showerror("Erro", f"Erro ao salvar PDF: {e}")
        return None
    finally:
        try:
            buffer.close()
        except Exception:
            pass


if __name__ == '__main__':
    ano = 2025
    gerar_pdf_contatos(ano)

