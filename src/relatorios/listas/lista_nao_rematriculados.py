"""
Módulo para gerar lista de alunos que não fizeram rematrícula no ano atual
Lista alunos matriculados no ano anterior mas que não se matricularam no ano atual
"""

from src.core.config_logs import get_logger
logger = get_logger(__name__)

import io
import os
from datetime import date
from typing import List, Dict, Optional, Any, cast
import pandas as pd

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, grey, HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from src.core.config import get_image_path, ANO_LETIVO_ATUAL, ESCOLA_ID
from src.core.conexao import conectar_bd
from src.relatorios.gerar_pdf import salvar_e_abrir_pdf


def obter_alunos_nao_rematriculados(ano_anterior: int, ano_atual: int, escola_id: int = ESCOLA_ID) -> List[Dict]:
    """
    Busca alunos que estavam matriculados no ano anterior mas não estão matriculados no ano atual.
    
    Args:
        ano_anterior: Ano letivo anterior (ex: 2025)
        ano_atual: Ano letivo atual (ex: 2026)
        escola_id: ID da escola
        
    Returns:
        Lista de dicionários com dados dos alunos
    """
    conn = conectar_bd()
    if not conn:
        logger.error("Erro ao conectar ao banco de dados")
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Buscar IDs dos anos letivos
        cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = %s", (ano_anterior,))
        ano_anterior_row = cursor.fetchone()
        
        cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = %s", (ano_atual,))
        ano_atual_row = cursor.fetchone()
        
        if not ano_anterior_row or not ano_atual_row:
            logger.error("Anos letivos não encontrados no banco de dados")
            return []
        
        ano_anterior_id = ano_anterior_row['id']
        ano_atual_id = ano_atual_row['id']
        
        # Query para buscar alunos não rematriculados
        query = """
            SELECT DISTINCT
                a.id,
                a.nome,
                a.cpf,
                a.data_nascimento,
                a.sexo,
                s_anterior.nome as serie_anterior,
                t_anterior.nome as turma_anterior,
                t_anterior.turno as turno_anterior,
                m_anterior.status as status_anterior,
                m_anterior.data_matricula as data_matricula_anterior,
                GROUP_CONCAT(DISTINCT r.nome SEPARATOR ' / ') as responsaveis,
                GROUP_CONCAT(DISTINCT r.telefone SEPARATOR ' / ') as telefones_responsaveis,
                GROUP_CONCAT(DISTINCT r.grau_parentesco SEPARATOR ' / ') as graus_parentesco
            FROM Alunos a
            INNER JOIN Matriculas m_anterior ON a.id = m_anterior.aluno_id
            INNER JOIN Turmas t_anterior ON m_anterior.turma_id = t_anterior.id
            INNER JOIN series s_anterior ON t_anterior.serie_id = s_anterior.id
            LEFT JOIN ResponsaveisAlunos ra ON a.id = ra.aluno_id
            LEFT JOIN Responsaveis r ON ra.responsavel_id = r.id
            WHERE m_anterior.ano_letivo_id = %s
                AND a.escola_id = %s
                AND m_anterior.status = 'Concluído'
                AND s_anterior.nome NOT LIKE '%9%ano%'
                AND s_anterior.nome NOT LIKE '%9º%ano%'
                AND NOT EXISTS (
                    SELECT 1 FROM Matriculas m_atual
                    WHERE m_atual.aluno_id = a.id
                    AND m_atual.ano_letivo_id = %s
                )
            GROUP BY a.id, a.nome, a.cpf, a.data_nascimento, a.sexo,
                     s_anterior.nome, t_anterior.nome, t_anterior.turno,
                     m_anterior.status, m_anterior.data_matricula
            ORDER BY a.nome
        """
        
        cursor.execute(query, (ano_anterior_id, escola_id, ano_atual_id))
        alunos = cursor.fetchall()
        
        logger.info(f"Total de alunos não rematriculados: {len(alunos)}")
        
        return alunos
        
    except Exception as e:
        logger.error(f"Erro ao buscar alunos não rematriculados: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def calcular_idade(data_nascimento: date) -> int:
    """Calcula a idade atual do aluno"""
    if not data_nascimento:
        return 0
    hoje = date.today()
    idade = hoje.year - data_nascimento.year
    if (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day):
        idade -= 1
    return idade


def gerar_pdf_nao_rematriculados(ano_anterior: int, ano_atual: int, escola_id: int = ESCOLA_ID):
    """
    Gera PDF com lista de alunos que não fizeram rematrícula
    
    Args:
        ano_anterior: Ano letivo anterior
        ano_atual: Ano letivo atual
        escola_id: ID da escola
    """
    # Buscar dados
    alunos = obter_alunos_nao_rematriculados(ano_anterior, ano_atual, escola_id)
    
    if not alunos:
        logger.warning("Nenhum aluno não rematriculado encontrado")
        return None
    
    # Criar buffer para o PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.25*inch,
        bottomMargin=0.25*inch
    )
    
    # Preparar elementos do documento
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilo para título
    titulo_style = ParagraphStyle(
        'TituloCustom',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=black,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulo
    subtitulo_style = ParagraphStyle(
        'SubtituloCustom',
        parent=styles['Normal'],
        fontSize=11,
        textColor=black,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    # Logo da escola
    logo_path = str(get_image_path('logopaco.png'))
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=2*inch, height=1*inch)
            elements.append(logo)
            elements.append(Spacer(1, 0.1*inch))
        except Exception as e:
            logger.warning(f"Erro ao carregar logo: {e}")
    
    # Título
    elements.append(Paragraph(
        f"LISTA DE ALUNOS NÃO REMATRICULADOS EM {ano_atual}",
        titulo_style
    ))
    
    elements.append(Paragraph(
        f"Alunos matriculados em {ano_anterior} que não se matricularam em {ano_atual}",
        subtitulo_style
    ))
    
    elements.append(Paragraph(
        f"Total: {len(alunos)} alunos | Data: {date.today().strftime('%d/%m/%Y')}",
        subtitulo_style
    ))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Estilo para nomes (permite quebra de linha)
    nome_style = ParagraphStyle(
        'NomeStyle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        alignment=TA_LEFT
    )
    
    # Estilo para texto geral (responsáveis, telefones)
    texto_style = ParagraphStyle(
        'TextoStyle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        alignment=TA_LEFT
    )
    
    # Preparar dados da tabela
    data = [['Nº', 'Nome', 'CPF', 'Idade', 'Turma\nAnterior', 
             'Status\nAnterior', 'Responsáveis', 'Telefones']]
    
    for idx, aluno in enumerate(alunos, 1):
        idade = calcular_idade(aluno['data_nascimento']) if aluno['data_nascimento'] else '-'
        cpf = aluno['cpf'] if aluno['cpf'] else 'SEM CPF'
        responsaveis = aluno['responsaveis'] if aluno['responsaveis'] else '-'
        telefones = aluno['telefones_responsaveis'] if aluno['telefones_responsaveis'] else '-'
        
        # Nome completo com Paragraph para permitir quebra de linha
        nome_paragraph = Paragraph(aluno['nome'], nome_style)
        
        # Responsáveis e telefones com Paragraph
        responsaveis_paragraph = Paragraph(responsaveis, texto_style)
        telefones_paragraph = Paragraph(telefones, texto_style)
        
        # Combinar série, turma e turno anterior
        serie = aluno['serie_anterior'] or '-'
        turma = aluno['turma_anterior']
        if not turma or turma.strip() == '':
            turma = 'única'
        turno = aluno['turno_anterior'] or '-'
        turma_completa = f"{serie} - {turma} - {turno}"
        
        data.append([
            str(idx),
            nome_paragraph,
            cpf,
            str(idade),
            turma_completa,
            aluno['status_anterior'] or '-',
            responsaveis_paragraph,
            telefones_paragraph
        ])
    
    # Criar tabela
    table = Table(data, colWidths=[
        0.3*inch,   # Nº
        2.3*inch,   # Nome
        1.0*inch,   # CPF
        0.5*inch,   # Idade
        1.3*inch,   # Turma Anterior (série + turma + turno)
        0.8*inch,   # Status
        3.0*inch,   # Responsáveis
        0.8*inch    # Telefones
    ])
    
    # Estilo da tabela
    table.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Corpo da tabela
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('TEXTCOLOR', (0, 1), (-1, -1), black),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Nº centralizado
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Idade centralizada
        ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # Status centralizado
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        
        # Linhas da grade
        ('GRID', (0, 0), (-1, -1), 0.5, grey),
        
        # Linhas zebradas
        *[('BACKGROUND', (0, i), (-1, i), HexColor('#E7E6E6'))
          for i in range(2, len(data), 2)]
    ]))
    
    elements.append(table)
    
    # Construir PDF
    doc.build(elements)
    
    # Salvar e abrir
    buffer.seek(0)
    nome_arquivo = f"Lista_Nao_Rematriculados_{ano_anterior}_para_{ano_atual}.pdf"
    
    return salvar_e_abrir_pdf(buffer, nome_arquivo)


def gerar_excel_nao_rematriculados(ano_anterior: int, ano_atual: int, escola_id: int = ESCOLA_ID):
    """
    Gera arquivo Excel com lista de alunos que não fizeram rematrícula
    
    Args:
        ano_anterior: Ano letivo anterior
        ano_atual: Ano letivo atual
        escola_id: ID da escola
    """
    # Buscar dados
    alunos = obter_alunos_nao_rematriculados(ano_anterior, ano_atual, escola_id)
    
    if not alunos:
        logger.warning("Nenhum aluno não rematriculado encontrado")
        return None
    
    # Preparar dados para DataFrame
    dados_excel = []
    for idx, aluno in enumerate(alunos, 1):
        idade = calcular_idade(aluno['data_nascimento']) if aluno['data_nascimento'] else '-'
        
        # Combinar série, turma e turno anterior
        serie = aluno['serie_anterior'] or '-'
        turma = aluno['turma_anterior']
        if not turma or turma.strip() == '':
            turma = 'única'
        turno = aluno['turno_anterior'] or '-'
        turma_completa = f"{serie} - {turma} - {turno}"
        
        dados_excel.append({
            'Nº': idx,
            'Nome': aluno['nome'],
            'CPF': aluno['cpf'] if aluno['cpf'] else 'SEM CPF',
            'Data Nascimento': aluno['data_nascimento'].strftime('%d/%m/%Y') if aluno['data_nascimento'] else '-',
            'Idade': idade,
            'Sexo': aluno['sexo'],
            'Turma Anterior': turma_completa,
            'Status Anterior': aluno['status_anterior'] or '-',
            'Data Matrícula Anterior': aluno['data_matricula_anterior'].strftime('%d/%m/%Y') if aluno['data_matricula_anterior'] else '-',
            'Responsáveis': aluno['responsaveis'] or '-',
            'Grau Parentesco': aluno['graus_parentesco'] or '-',
            'Telefones': aluno['telefones_responsaveis'] or '-'
        })
    
    # Criar DataFrame
    df = pd.DataFrame(dados_excel)
    
    # Criar arquivo Excel
    nome_arquivo = f"Lista_Nao_Rematriculados_{ano_anterior}_para_{ano_atual}.xlsx"
    caminho = os.path.join(os.path.expanduser("~"), "Desktop", nome_arquivo)
    
    try:
        with pd.ExcelWriter(caminho, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Não Rematriculados')
            
            # Ajustar largura das colunas
            worksheet = writer.sheets['Não Rematriculados']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        
        logger.info(f"Excel salvo em: {caminho}")
        
        # Abrir arquivo
        os.startfile(caminho)
        
        return caminho
        
    except Exception as e:
        logger.error(f"Erro ao gerar Excel: {e}")
        return None


if __name__ == "__main__":
    # Teste do módulo
    ano_anterior = ANO_LETIVO_ATUAL - 1
    ano_atual = ANO_LETIVO_ATUAL
    
    print(f"Gerando lista de não rematriculados: {ano_anterior} → {ano_atual}")
    
    # Gerar PDF
    pdf_path = gerar_pdf_nao_rematriculados(ano_anterior, ano_atual)
    if pdf_path:
        print(f"PDF gerado: {pdf_path}")
    
    # Gerar Excel
    excel_path = gerar_excel_nao_rematriculados(ano_anterior, ano_atual)
    if excel_path:
        print(f"Excel gerado: {excel_path}")
