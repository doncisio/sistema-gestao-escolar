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
from reportlab.lib.colors import black, white
from conexao import conectar_bd  # Certifique-se de que esta importação é necessária aqui
from gerarPDF import salvar_e_abrir_pdf
from Lista_atualizada import fetch_student_data
from biblio_editor import definir_coordenador

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
            ('BACKGROUND', (0, 0), (-1, 0), white),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ])
    return _STYLE_CACHE['common_table']

def lista_notas():
    """Gera um PDF com a lista de notas dos alunos, agrupados por turma."""

    ano_letivo = 2025
    dados_aluno = fetch_student_data(ano_letivo)

    if not dados_aluno:
        logger.info("Nenhum dado de aluno encontrado.")
        return

    df = pd.DataFrame(dados_aluno)

    # 1. Configurações Iniciais
    cabecalho = [
        "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>EM PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 06.003.636/0001-73</b>"
    ]
    figura_superior = os.path.join(os.path.dirname(__file__), 'imagens', 'logosemed.png')
    figura_inferior = os.path.join(os.path.dirname(__file__), 'imagens', 'logopaco.jpg')

    # 2. Configuração do Documento PDF
    buffer = io.BytesIO()
    left_margin = 36
    right_margin = 18
    top_margin = 18
    bottom_margin = 18
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin
    )
    elements = []

    # 3. Capa do Documento
    adicionar_capainicial(elements, cabecalho, figura_superior, figura_inferior)
    capa_final_adicionada = False  # Variável de controle para a capa final

    # Lista de professores volantes com suas turmas específicas
    professores_volantes = [
        {
            "nome": "Sebastiana Santos Silva",
            "disciplinas": ["HST.", "GGF.", "REL."],
            "turmas": ["2º ANO", "4º ANO", "5º ANO"]
        },
        {
            "nome": "Josué Alves Bezerra Júnior",
            "disciplinas": ["HST.", "GGF.", "REL."],
            "turmas": ["1º ANO", "3º ANO"]
        }
    ]

    # 4. Loop Principal: Agrupar por Turma e Adicionar Tabelas
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        logger.info(f"Processando turma: {nome_serie} {nome_turma} {turno}")  # Debug
        
        if turma_df[turma_df['ID_SERIE'] > 7].empty:
            # Tabela regular para anos iniciais
            adicionar_tabela_turma_anos_iniciais(elements, cabecalho, figura_superior, figura_inferior, turma_df, nome_serie, nome_turma, turno)
            
            # Tabelas para professores volantes - apenas para suas turmas específicas
            for professor in professores_volantes:
                logger.info(f"Verificando professor {professor['nome']} para turma {nome_serie}")  # Debug
                logger.info(f"Turmas do professor: {professor['turmas']}")  # Debug
                
                # Normaliza o nome da série para comparação
                serie_normalizada = nome_serie.strip().upper()
                if serie_normalizada in [t.strip().upper() for t in professor["turmas"]]:
                    logger.info(f"Gerando tabela para professor {professor['nome']} na turma {nome_serie}")  # Debug
                    adicionar_tabela_professor_volante(
                        elements, 
                        cabecalho, 
                        figura_superior, 
                        figura_inferior, 
                        turma_df, 
                        nome_serie, 
                        nome_turma, 
                        turno, 
                        professor["nome"], 
                        professor["disciplinas"]
                    )

        if turma_df[turma_df['ID_SERIE'] <= 7].empty:
            if not capa_final_adicionada:
                # 5. Adiciona a capa final se ainda não foi adicionada
                adicionar_capafinal(elements, cabecalho, figura_superior, figura_inferior)
                capa_final_adicionada = True
            adicionar_tabela_turma_anos_finais(elements, cabecalho, figura_superior, figura_inferior, turma_df, nome_serie, nome_turma, turno)

    # 6. Finalização e Salvamento
    doc.build(elements)
    buffer.seek(0)
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
            from utilitarios.tipos_documentos import TIPO_LISTA_NOTAS

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            try:
                tmp.write(buffer.getvalue())
                tmp.close()
                descricao = f"Lista de Notas - {datetime.datetime.now().year}"
                try:
                    salvar_documento_sistema(tmp.name, TIPO_LISTA_NOTAS, funcionario_id=1, finalidade='Secretaria', descricao=descricao)
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

def adicionar_tabela_turma_anos_finais(elements, cabecalho, figura_superior, figura_inferior, turma_df, nome_serie, nome_turma, turno):
    """Adiciona uma tabela para cada disciplina da turma dos anos finais, incluindo cabeçalho e informações."""

    # 1. Preparação dos Dados da Turma
    nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else ''
    turma_df = turma_df[turma_df['SITUAÇÃO'] == 'Ativo']

    # 2. Buscar as disciplinas do nível 3 (anos finais) para a escola
    # Supondo que você tenha uma função que retorne as disciplinas do nível 3
    disciplinas = buscar_disciplinas_nivel_3()  # Retorna uma lista de disciplinas

    # 3. Loop sobre as disciplinas
    for disciplina in disciplinas:
        # 4. Cabeçalho da Turma e Disciplina
        data = [
            [Image(figura_superior, width=.75 * inch, height=.75 * inch),
             Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=10, alignment=1)),
             Image(figura_inferior, width=1.125 * inch, height=.75 * inch)]
        ]
        table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
        table_style = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ])
        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 0.1 * inch))

        # 5. Determinação do Coordenador
        coordenador = definir_coordenador(turma_df)

        # 6. Título e Informações da Turma e Disciplina
        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
        elements.append(Paragraph(f"<b>Disciplina: {disciplina['nome']}</b>", ParagraphStyle(name='DisciplinaTitulo', fontSize=12, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))
        adicionar_assinaturas(elements, nome_professor, coordenador)

        # 7. Tabela de Alunos para a Disciplina
        # Colunas: Número, Nome do Aluno, T1, T2, T3, T4, Média, Faltas
        data = [['Nº', 'Nome do Aluno', 'T1', 'T2', 'T3', 'T4', 'Média', 'Faltas']]
        for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
            nome = row['NOME DO ALUNO']
            # Inicializa as notas e faltas como vazias
            notas = ['', '', '', '', '', '']  # T1, T2, T3, T4, Média, Faltas
            data.append([row_num, nome] + notas)

        table = Table(data, colWidths=[0.33 * inch, 3 * inch] + [0.52 * inch] * 6)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), white),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
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

def buscar_disciplinas_nivel_3():
    """Retorna as disciplinas do nível 3 (anos finais) para a escola."""
    # Exemplo de disciplinas (substitua por uma consulta ao banco de dados)
    disciplinas = [
        {"id": 802, "nome": "L. PORTUGUESA"},
        {"id": 803, "nome": "MATEMÁTICA"},
        {"id": 804, "nome": "CIÊNCIAS"},
        {"id": 805, "nome": "HISTÓRIA"},
        {"id": 806, "nome": "GEOGRAFIA"},
        {"id": 807, "nome": "ARTE"},
        {"id": 808, "nome": "ENS. RELIGIOSO"},
        {"id": 809, "nome": "ED. FÍSICA"},
        {"id": 810, "nome": "FILOSOFIA"},
        {"id": 811, "nome": "L. INGLESA"},
    ]
    return disciplinas

def adicionar_capainicial(elements, cabecalho, figura_superior, figura_inferior):
    """Adiciona a capa ao início do documento."""
    img_sup = _get_cached_image(figura_superior, 1 * inch, 1 * inch)
    img_inf = _get_cached_image(figura_inferior, 1.5 * inch, 1 * inch)
    header_style = _get_cached_style('Header', fontSize=12, alignment=1)
    
    data = [
        [img_sup,
         Paragraph('<br/>'.join(cabecalho), header_style),
         img_inf]
    ]
    table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
    table_style = TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 3.3 * inch))
    capa_style = _get_cached_style('Capa', fontSize=24, alignment=1)
    elements.append(Paragraph("<b>TABELA DE NOTAS ANOS INICIAIS</b>", capa_style))
    elements.append(Spacer(1, 4 * inch))
    ano_style = _get_cached_style('Ano', fontSize=18, alignment=1)
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ano_style))
    elements.append(PageBreak())

def adicionar_capafinal(elements, cabecalho, figura_superior, figura_inferior):
    """Adiciona a capa ao início do documento."""
    img_sup = _get_cached_image(figura_superior, 1 * inch, 1 * inch)
    img_inf = _get_cached_image(figura_inferior, 1.5 * inch, 1 * inch)
    header_style = _get_cached_style('Header', fontSize=12, alignment=1)
    
    data = [
        [img_sup,
         Paragraph('<br/>'.join(cabecalho), header_style),
         img_inf]
    ]
    table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
    table_style = TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 3.3 * inch))
    capa_style = _get_cached_style('Capa', fontSize=24, alignment=1)
    elements.append(Paragraph("<b>TABELA DE NOTAS ANOS FINAIS</b>", capa_style))
    elements.append(Spacer(1, 4 * inch))
    ano_style = _get_cached_style('Ano', fontSize=18, alignment=1)
    elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ano_style))
    elements.append(PageBreak())

def adicionar_tabela_turma_anos_iniciais(elements, cabecalho, figura_superior, figura_inferior, turma_df, nome_serie, nome_turma, turno):
    """Adiciona uma tabela para cada turma, incluindo cabeçalho e informações."""

    # 1. Preparação dos Dados da Turma
    nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Sem Professor'
    turma_df = turma_df[turma_df['SITUAÇÃO'] == 'Ativo']

    # 2. Cabeçalho da Turma com cache
    img_sup = _get_cached_image(figura_superior, .75 * inch, .75 * inch)
    img_inf = _get_cached_image(figura_inferior, 1.125 * inch, .75 * inch)
    header_style = _get_cached_style('Header', fontSize=10, alignment=1)
    
    data = [
        [img_sup,
         Paragraph('<br/>'.join(cabecalho), header_style),
         img_inf]
    ]
    table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
    table_style = TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 0.1 * inch))

    # 3. Determinação do Coordenador
    coordenador = definir_coordenador(turma_df)

    # 4. Título e Informações da Turma
    turma_style = _get_cached_style('TurmaTitulo', fontSize=12, alignment=1)
    elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", turma_style))
    elements.append(Spacer(1, 0.1 * inch))
    adicionar_assinaturas(elements, nome_professor, coordenador)

    # 5. Tabela de Alunos - Removidas as disciplinas HST., GGF. e REL.
    data = [['Nº', 'Nome', 'PORT.', 'MTM.', 'CNC.', 'ART.', 'REC.']]
    for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
        notas = ['', '', '', '', '']  # Notas vazias para as disciplinas restantes
        data.append([row_num, row['NOME DO ALUNO']] + notas)

    table = Table(data, colWidths=[0.33 * inch, 3 * inch] + [0.52 * inch] * 5)
    table.setStyle(_get_common_table_style())
    elements.append(table)
    elements.append(PageBreak())

def adicionar_assinaturas(elements, nome_professor, coordenador):
    """Adiciona as linhas de assinatura do professor e coordenador."""
    prof_style = _get_cached_style('ProfessoraTitulo', fontSize=12, alignment=1)
    paragrafo_professor = Paragraph(f"<b>PROFESSOR@: {nome_professor}</b>", prof_style)
    paragrafo_coordenador = Paragraph(f"<b>Coordenadora: {coordenador}</b>", prof_style)

    dados_tabela_assinatura = [[paragrafo_professor, paragrafo_coordenador]]
    tabela_assinatura = Table(dados_tabela_assinatura, colWidths=[4.5 * inch, 3.5 * inch])
    tabela_assinatura.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),      # Alinha a primeira coluna à esquerda
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),     # Alinha a segunda coluna à direita
    ]))
    elements.append(tabela_assinatura)

def adicionar_tabela_professor_volante(elements, cabecalho, figura_superior, figura_inferior, turma_df, nome_serie, nome_turma, turno, nome_professor, disciplinas):
    """Adiciona uma tabela para cada professor volante, incluindo cabeçalho e informações."""

    # 1. Preparação dos Dados da Turma
    turma_df = turma_df[turma_df['SITUAÇÃO'] == 'Ativo']

    # 2. Cabeçalho da Turma
    data = [
        [Image(figura_superior, width=.75 * inch, height=.75 * inch),
         Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=10, alignment=1)),
         Image(figura_inferior, width=1.125 * inch, height=.75 * inch)]
    ]
    table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 0.1 * inch))

    # 3. Determinação do Coordenador
    coordenador = definir_coordenador(turma_df)

    # 4. Título e Informações da Turma
    elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
    elements.append(Paragraph(f"<b>Professor Volante: {nome_professor}</b>", ParagraphStyle(name='ProfessorTitulo', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.1 * inch))
    adicionar_assinaturas(elements, nome_professor, coordenador)

    # 5. Tabela de Alunos
    data = [['Nº', 'Nome'] + disciplinas]
    for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
        nome = row['NOME DO ALUNO']
        notas = [''] * len(disciplinas)  # Notas vazias para cada disciplina
        data.append([row_num, nome] + notas)

    table = Table(data, colWidths=[0.33 * inch, 3 * inch] + [0.52 * inch] * len(disciplinas))
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), white),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
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

# Execução
# lista_notas()