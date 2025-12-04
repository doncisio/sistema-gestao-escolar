from config_logs import get_logger
from config import get_image_path
logger = get_logger(__name__)
"""
Módulo para gerar relatórios de pendências de notas
Identifica alunos sem notas e disciplinas sem lançamento
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, lightgrey, red, grey
import pandas as pd
import datetime
import os
from conexao import conectar_bd
from NotaAta import abrir_pdf_com_programa_padrao
from typing import Any, cast


def buscar_pendencias_notas(bimestre, nivel_ensino="iniciais", ano_letivo=None, escola_id=60):
    """
    Busca alunos sem notas e disciplinas sem lançamento
    
    Args:
        bimestre: Bimestre para verificar ("1º bimestre", etc)
        nivel_ensino: "iniciais" ou "finais"
        ano_letivo: Ano letivo (padrão: ano atual)
        escola_id: ID da escola
    
    Returns:
        dict: Dicionário com pendências por turma
    """
    if ano_letivo is None:
        ano_letivo = datetime.datetime.now().year
    
    # Definir filtro de série
    if nivel_ensino == "iniciais":
        filtro_serie = "s.id <= 7"
        nivel_id = 2
    else:
        filtro_serie = "s.id > 7"
        nivel_id = 3
    
    conn: Any = conectar_bd()
    cursor = cast(Any, conn).cursor(dictionary=True)
    
    # Query para buscar alunos ativos e suas notas
    query = f"""
        SELECT 
            s.nome AS serie,
            t.nome AS turma,
            t.turno AS turno,
            a.id AS aluno_id,
            a.nome AS aluno_nome,
            d.id AS disciplina_id,
            d.nome AS disciplina,
            n.nota AS nota
        FROM Alunos a
        JOIN Matriculas m ON a.id = m.aluno_id
        JOIN Turmas t ON m.turma_id = t.id
        JOIN series s ON t.serie_id = s.id
        CROSS JOIN Disciplinas d
        LEFT JOIN Notas n ON a.id = n.aluno_id 
            AND d.id = n.disciplina_id 
            AND n.bimestre = '{bimestre}'
            AND n.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = {ano_letivo})
        WHERE 
            m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = {ano_letivo})
            AND a.escola_id = {escola_id}
            AND m.status = 'Ativo'
            AND {filtro_serie}
            AND d.escola_id = {escola_id}
            AND d.nivel_id = {nivel_id}
        ORDER BY s.nome, t.nome, t.turno, a.nome, d.nome
    """
    
    cursor.execute(query)
    dados = cursor.fetchall()
    if cursor:
        cursor.close()
    if conn:
        conn.close()
    
    # Organizar dados por turma
    pendencias = {}
    disciplinas_por_turma = {}  # Para rastrear disciplinas únicas
    
    for registro in dados:
        chave_turma = (registro['serie'], registro['turma'], registro['turno'])
        
        if chave_turma not in pendencias:
            pendencias[chave_turma] = {
                'serie': registro['serie'],
                'turma': registro['turma'],
                'turno': registro['turno'],
                'alunos': {},
                'disciplinas_sem_lancamento': set(),
                'disciplinas_com_nota': set(),
                'todas_disciplinas': set(),
                'total_alunos': 0,
                'total_disciplinas': 0
            }
            disciplinas_por_turma[chave_turma] = set()
        
        aluno_id = registro['aluno_id']
        aluno_nome = registro['aluno_nome']
        disciplina_id = registro['disciplina_id']
        disciplina = registro['disciplina']
        nota = registro['nota']
        
        # Adicionar disciplina única
        disciplinas_por_turma[chave_turma].add((disciplina_id, disciplina))
        pendencias[chave_turma]['todas_disciplinas'].add(disciplina)
        
        # Contar aluno (apenas uma vez)
        if aluno_id not in pendencias[chave_turma]['alunos']:
            pendencias[chave_turma]['alunos'][aluno_id] = {
                'nome': aluno_nome,
                'disciplinas_sem_nota': []
            }
            pendencias[chave_turma]['total_alunos'] += 1
        
        # Verificar se a nota está pendente (evitar duplicatas)
        if nota is None:
            if disciplina not in pendencias[chave_turma]['alunos'][aluno_id]['disciplinas_sem_nota']:
                pendencias[chave_turma]['alunos'][aluno_id]['disciplinas_sem_nota'].append(disciplina)
        else:
            pendencias[chave_turma]['disciplinas_com_nota'].add(disciplina)
    
    # Identificar disciplinas sem nenhum lançamento
    for chave_turma, info in pendencias.items():
        info['total_disciplinas'] = len(disciplinas_por_turma[chave_turma])
        info['disciplinas_sem_lancamento'] = info['todas_disciplinas'] - info['disciplinas_com_nota']
    
    return pendencias


def gerar_pdf_pendencias(bimestre, nivel_ensino="iniciais", ano_letivo=None, escola_id=60):
    """
    Gera PDF com relatório de pendências de notas
    
    Args:
        bimestre: Bimestre para verificar
        nivel_ensino: "iniciais" ou "finais"
        ano_letivo: Ano letivo
        escola_id: ID da escola
    
    Returns:
        bool: True se gerou com sucesso
    """
    if ano_letivo is None:
        ano_letivo = datetime.datetime.now().year
    
    # Buscar pendências
    logger.info(f"Buscando pendências para {bimestre}, nível {nivel_ensino}...")
    pendencias = buscar_pendencias_notas(bimestre, nivel_ensino, ano_letivo, escola_id)
    
    if not pendencias:
        logger.info("Nenhuma pendência encontrada!")
        return False
    
    # Nome do arquivo
    nome_arquivo = f"Pendencias_Notas_{bimestre.replace(' ', '_')}_{nivel_ensino}_{ano_letivo}.pdf"
    
    # Criar documento PDF com margens maiores
    doc = SimpleDocTemplate(
        nome_arquivo,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50
    )
    
    elements = []
    
    # Estilos
    cabecalho_escola_style = ParagraphStyle(
        'CabecalhoEscola',
        fontSize=12,
        alignment=1,
        fontName='Helvetica'
    )
    
    cabecalho_style = ParagraphStyle(
        'Cabecalho',
        fontSize=14,
        alignment=1,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    
    subtitulo_style = ParagraphStyle(
        'Subtitulo',
        fontSize=12,
        alignment=1,
        spaceAfter=8
    )
    
    info_style = ParagraphStyle(
        'Info',
        fontSize=10,
        alignment=1,
        spaceAfter=16
    )
    
    turma_titulo_style = ParagraphStyle(
        'TurmaTitulo',
        fontSize=11,
        spaceAfter=8,
        fontName='Helvetica-Bold',
        spaceBefore=8
    )
    
    alerta_style = ParagraphStyle(
        'Alerta',
        fontSize=10,
        textColor=red,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    disc_sem_lanc_style = ParagraphStyle(
        'DiscSemLanc',
        fontSize=9,
        leftIndent=15,
        spaceAfter=10,
        leading=12
    )
    
    alunos_titulo_style = ParagraphStyle(
        'AlunosTitulo',
        fontSize=10,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    rodape_style = ParagraphStyle(
        'Rodape',
        fontSize=8,
        alignment=1,
        textColor=grey
    )
    
    # ===== CABEÇALHO PADRÃO =====
    # Informações do cabeçalho
    cabecalho_info = [
        "ESTADO DO MARANHÃO",
        "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>UEB PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 06.003.636/0001-73</b>"
    ]
    
    # Caminhos das figuras
    figura_superior_path = str(get_image_path('pacologo.png'))
    figura_inferior_path = str(get_image_path('logopaco.jpg'))
    
    # Carregar as imagens
    try:
        figura_superior = Image(figura_superior_path, width=1*inch, height=1*inch)
    except Exception as e:
        logger.info(f"Aviso: Não foi possível carregar a imagem superior: {e}")
        figura_superior = Spacer(1*inch, 1*inch)
    
    try:
        figura_inferior = Image(figura_inferior_path, width=1.5*inch, height=1*inch)
    except Exception as e:
        logger.info(f"Aviso: Não foi possível carregar a imagem inferior: {e}")
        figura_inferior = Spacer(1.5*inch, 1*inch)
    
    # Criar tabela de cabeçalho com 3 colunas: [imagem esq | texto centro | imagem dir]
    data_cabecalho = [
        [
            figura_superior,
            Paragraph('<br/>'.join(cabecalho_info), ParagraphStyle(name='Header', fontSize=12, alignment=1)),
            figura_inferior
        ]
    ]
    
    tabela_cabecalho = Table(data_cabecalho, colWidths=[1.32*inch, 4*inch, 1.32*inch])
    tabela_cabecalho.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    
    elements.append(tabela_cabecalho)
    elements.append(Spacer(1, 0.25*inch))
    
    # ===== TÍTULO DO RELATÓRIO =====
    elements.append(Paragraph(
        f"<b>RELATÓRIO DE PENDÊNCIAS DE NOTAS</b>",
        cabecalho_style
    ))
    
    elements.append(Paragraph(
        f"<b>{bimestre.upper()} - {ano_letivo}</b>",
        subtitulo_style
    ))
    
    elements.append(Paragraph(
        f"Nível: {'Séries Iniciais (1º ao 5º ano)' if nivel_ensino == 'iniciais' else 'Séries Finais (6º ao 9º ano)'}",
        info_style
    ))
    
    # Estatísticas gerais
    total_turmas_com_pendencia = 0
    total_alunos_com_pendencia = 0
    total_disciplinas_sem_lancamento = 0
    
    for chave_turma, info in pendencias.items():
        alunos_com_pendencia = sum(1 for a in info['alunos'].values() if len(a['disciplinas_sem_nota']) > 0)
        if alunos_com_pendencia > 0 or len(info['disciplinas_sem_lancamento']) > 0:
            total_turmas_com_pendencia += 1
            total_alunos_com_pendencia += alunos_com_pendencia
            total_disciplinas_sem_lancamento += len(info['disciplinas_sem_lancamento'])
    
    # Resumo geral
    resumo_data = [
        ['RESUMO GERAL', ''],
        ['Turmas com pendências:', str(total_turmas_com_pendencia)],
        ['Alunos com notas faltando:', str(total_alunos_com_pendencia)],
        ['Disciplinas sem lançamento:', str(total_disciplinas_sem_lancamento)]
    ]
    
    resumo_table = Table(resumo_data, colWidths=[3.5*inch, 2*inch])
    resumo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, black),
    ]))
    
    elements.append(resumo_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Detalhamento por turma
    turmas_ordenadas = sorted(pendencias.keys())
    
    for idx, chave_turma in enumerate(turmas_ordenadas):
        info = pendencias[chave_turma]
        
        # Filtrar apenas alunos com pendências
        alunos_com_pendencia = {
            aluno_id: aluno_info 
            for aluno_id, aluno_info in info['alunos'].items() 
            if len(aluno_info['disciplinas_sem_nota']) > 0
        }
        
        # Verificar se há pendências nesta turma
        if len(alunos_com_pendencia) == 0 and len(info['disciplinas_sem_lancamento']) == 0:
            continue
        
        # Título da turma
        elements.append(Paragraph(
            f"<b>Turma: {info['serie']} {info['turma']} - Turno: {info['turno']}</b>",
            turma_titulo_style
        ))
        
        # Disciplinas sem lançamento (SEM REPETIÇÃO)
        if len(info['disciplinas_sem_lancamento']) > 0:
            elements.append(Paragraph(
                f"<b>⚠ DISCIPLINAS SEM NENHUM LANÇAMENTO ({len(info['disciplinas_sem_lancamento'])}):</b>",
                alerta_style
            ))
            
            # Ordenar e remover duplicatas
            disciplinas_unicas = sorted(list(set(info['disciplinas_sem_lancamento'])))
            disc_text = ", ".join(disciplinas_unicas)
            
            elements.append(Paragraph(
                disc_text,
                disc_sem_lanc_style
            ))
        
        # Alunos com notas faltando
        if len(alunos_com_pendencia) > 0:
            elements.append(Paragraph(
                f"<b>ALUNOS COM NOTAS FALTANDO ({len(alunos_com_pendencia)}):</b>",
                alunos_titulo_style
            ))
            
            # Estilo para texto dentro da tabela
            celula_style = ParagraphStyle(
                'Celula',
                fontSize=8,
                leading=10,
                wordWrap='CJK'
            )
            
            # Criar tabela de alunos
            aluno_data = [[
                Paragraph('<b>Nº</b>', celula_style),
                Paragraph('<b>ALUNO</b>', celula_style),
                Paragraph('<b>DISCIPLINAS FALTANDO</b>', celula_style)
            ]]
            
            for num, (aluno_id, aluno_info) in enumerate(sorted(alunos_com_pendencia.items(), key=lambda x: x[1]['nome']), 1):
                # Remover duplicatas das disciplinas faltando
                disciplinas_unicas = sorted(list(set(aluno_info['disciplinas_sem_nota'])))
                disciplinas_faltando = ", ".join(disciplinas_unicas)
                
                aluno_data.append([
                    Paragraph(str(num), celula_style),
                    Paragraph(aluno_info['nome'], celula_style),
                    Paragraph(disciplinas_faltando, celula_style)
                ])
            
            aluno_table = Table(aluno_data, colWidths=[0.4*inch, 2.2*inch, 3.2*inch])
            aluno_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), black),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('GRID', (0, 0), (-1, -1), 0.5, black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            elements.append(aluno_table)
        
        # Adicionar espaço entre turmas, mas não após a última
        if idx < len(turmas_ordenadas) - 1:
            elements.append(Spacer(1, 0.2*inch))
    
    # Rodapé
    elements.append(Spacer(1, 0.25*inch))
    elements.append(Paragraph(
        f"Relatório gerado em: {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}",
        rodape_style
    ))
    
    # Gerar PDF
    try:
        doc.build(elements)
        logger.info(f"PDF gerado com sucesso: {nome_arquivo}")
        
        # Abrir PDF
        abrir_pdf_com_programa_padrao(nome_arquivo)
        return True
    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Teste
    logger.info("Testando geração de relatório de pendências...")
    gerar_pdf_pendencias("3º bimestre", "iniciais", 2025, 60)