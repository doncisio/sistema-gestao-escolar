import os
import pandas as pd
import datetime
import mysql.connector as mysql_connector
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white
import platform
from conexao import conectar_bd
from decimal import Decimal, ROUND_HALF_UP
import re


# ============================================================================
# MELHORIA 3: Funções de Validação para Segurança SQL
# Valida inputs antes de interpolação em queries dinâmicas
# ============================================================================

def validar_nome_disciplina(nome):
    """
    Valida que o nome de disciplina contém apenas caracteres seguros.
    Previne SQL Injection em queries dinâmicas.
    
    Args:
        nome (str): Nome da disciplina a validar
        
    Returns:
        str: Nome validado
        
    Raises:
        ValueError: Se o nome contiver caracteres inválidos
    """
    if not nome:
        raise ValueError("Nome de disciplina não pode ser vazio")
    
    # Permite letras (incluindo acentuadas), números, espaços, pontos, hífens e parênteses
    if not re.match(r'^[A-Za-zÀ-ÿ0-9\s\.\-\(\)]+$', nome):
        raise ValueError(f"Nome de disciplina contém caracteres inválidos: {nome}")
    
    # Limita tamanho máximo
    if len(nome) > 100:
        raise ValueError(f"Nome de disciplina muito longo: {nome}")
    
    return nome


def validar_bimestre(bimestre):
    """
    Valida formato do bimestre.
    
    Args:
        bimestre (str): Bimestre a validar
        
    Returns:
        str: Bimestre validado
        
    Raises:
        ValueError: Se o bimestre for inválido
    """
    # Normalizar entrada: aceitar variações como '3º bimestre', '3º Bimestre', '3 bimestre', '3º', '3'
    if not bimestre or not isinstance(bimestre, str):
        raise ValueError(f"Bimestre inválido: {bimestre}")

    # Extrair número do bimestre (1-4)
    m = re.search(r"([1-4])", bimestre)
    if not m:
        raise ValueError(f"Bimestre inválido: {bimestre}")

    n = m.group(1)
    bimestre_normalizado = f"{n}º Bimestre"
    return bimestre_normalizado


def validar_nivel_id(nivel_id):
    """
    Valida e converte nivel_id para inteiro.
    
    Args:
        nivel_id: ID do nível (pode ser int ou str)
        
    Returns:
        int: nivel_id validado
        
    Raises:
        ValueError: Se não puder ser convertido para int
    """
    try:
        nivel_int = int(nivel_id)
        if nivel_int < 1 or nivel_int > 10:  # Assumindo faixa válida
            raise ValueError(f"nivel_id fora da faixa válida: {nivel_int}")
        return nivel_int
    except (ValueError, TypeError):
        raise ValueError(f"nivel_id inválido: {nivel_id}")


def obter_disciplinas_iniciais():
    """Retorna a lista de disciplinas para séries iniciais (1º ao 5º ano)"""
    return [
        {'nome': 'L. PORTUGUESA', 'coluna': 'NOTA_PORTUGUES'},
        {'nome': 'MATEMÁTICA', 'coluna': 'NOTA_MATEMATICA'},
        {'nome': 'HISTÓRIA', 'coluna': 'NOTA_HISTORIA'},
        {'nome': 'GEOGRAFIA', 'coluna': 'NOTA_GEOGRAFIA'},
        {'nome': 'CIÊNCIAS', 'coluna': 'NOTA_CIENCIAS'},
        {'nome': 'ARTE', 'coluna': 'NOTA_ARTES'},
        {'nome': 'ENS. RELIGIOSO', 'coluna': 'NOTA_ENS_RELIGIOSO'},
        {'nome': 'ED. FÍSICA', 'coluna': 'NOTA_ED_FISICA'}
    ]


def obter_disciplinas_finais():
    """Retorna a lista de disciplinas para séries finais (6º ao 9º ano)"""
    return [
        {'nome': 'L. PORTUGUESA', 'coluna': 'NOTA_PORTUGUES'},
        {'nome': 'MATEMÁTICA', 'coluna': 'NOTA_MATEMATICA'},
        {'nome': 'CIÊNCIAS', 'coluna': 'NOTA_CIENCIAS'},
        {'nome': 'HISTÓRIA', 'coluna': 'NOTA_HISTORIA'},
        {'nome': 'GEOGRAFIA', 'coluna': 'NOTA_GEOGRAFIA'},
        {'nome': 'L. INGLESA', 'coluna': 'NOTA_INGLES'},
        {'nome': 'ARTE', 'coluna': 'NOTA_ARTES'},
        {'nome': 'ENS. RELIGIOSO', 'coluna': 'NOTA_ENS_RELIGIOSO'},
        {'nome': 'ED. FÍSICA', 'coluna': 'NOTA_ED_FISICA'},
        {'nome': 'FILOSOFIA', 'coluna': 'NOTA_FILOSOFIA'}
    ]


def formatar_nome_professor(nome_completo):
    """
    Retorna o primeiro e segundo nome do professor
    
    Args:
        nome_completo: Nome completo do professor
    
    Returns:
        str: Primeiro e segundo nome (ou apenas primeiro se houver só um)
    """
    if not nome_completo or nome_completo == 'Sem Professor':
        return nome_completo
    
    partes = nome_completo.strip().split()
    if len(partes) >= 2:
        return f"{partes[0]} {partes[1]}"
    elif len(partes) == 1:
        return partes[0]
    return nome_completo


def obter_professores_turma(turma_id, ano_letivo=2025):
    """
    Busca todos os professores de uma turma e suas disciplinas, ordenados por quantidade de disciplinas
    
    Args:
        turma_id: ID da turma
        ano_letivo: Ano letivo para filtrar (padrão: 2025)
    
    Returns:
        list: Lista de dicionários com {'professor': nome, 'disciplinas': [lista], 'qtd_disciplinas': int}
    """
    try:
        # Converter para int nativo do Python (caso seja numpy.int64)
        turma_id = int(turma_id)
        
        conn = conectar_bd()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar se existe a tabela funcionario_disciplinas
        cursor.execute("SHOW TABLES LIKE 'funcionario_disciplinas'")
        tem_tabela_disc = cursor.fetchone() is not None
        
        if tem_tabela_disc:
            # Buscar professores pela tabela funcionario_disciplinas
            query = """
                SELECT 
                    f.nome AS professor,
                    GROUP_CONCAT(DISTINCT d.nome ORDER BY d.nome SEPARATOR ', ') AS disciplinas,
                    COUNT(DISTINCT d.id) AS qtd_disciplinas
                FROM Funcionarios f
                LEFT JOIN funcionario_disciplinas fd ON f.id = fd.funcionario_id
                LEFT JOIN Disciplinas d ON fd.disciplina_id = d.id
                WHERE fd.turma_id = %s
                    AND f.cargo = 'Professor@'
                GROUP BY f.id, f.nome
                HAVING qtd_disciplinas > 0
                ORDER BY qtd_disciplinas DESC, f.nome ASC
            """
            cursor.execute(query, (turma_id,))
        else:
            # Fallback: buscar professores pela coluna turma
            query = """
                SELECT 
                    f.nome AS professor,
                    NULL AS disciplinas,
                    0 AS qtd_disciplinas
                FROM Funcionarios f
                WHERE f.turma = %s
                    AND f.cargo = 'Professor@'
                ORDER BY f.nome ASC
            """
            cursor.execute(query, (turma_id,))
        
        professores = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return professores
        
    except Exception as e:
        print(f"Erro ao buscar professores da turma: {e}")
        return []


def formatar_lista_professores(turma_id, ano_letivo=2025):
    """
    Retorna uma string formatada com os nomes dos professores (primeiro e segundo nome)
    ordenados por quantidade de disciplinas
    
    Args:
        turma_id: ID da turma
        ano_letivo: Ano letivo (padrão: 2025)
    
    Returns:
        str: Nomes dos professores formatados e separados por vírgula
    """
    professores = obter_professores_turma(turma_id, ano_letivo)
    
    if not professores:
        return 'Sem Professor'
    
    nomes_formatados = [formatar_nome_professor(p['professor']) for p in professores]
    
    if len(nomes_formatados) == 1:
        return nomes_formatados[0]
    elif len(nomes_formatados) == 2:
        return f"{nomes_formatados[0]} e {nomes_formatados[1]}"
    else:
        # Para 3 ou mais professores: "Nome1, Nome2 e Nome3"
        return ", ".join(nomes_formatados[:-1]) + f" e {nomes_formatados[-1]}"


def construir_consulta_sql(bimestre, filtro_serie, disciplinas, nivel_id, ano_letivo=2025, escola_id=60, status_matricula=None):
    """
    Constrói a consulta SQL com base nos parâmetros fornecidos
    
    Args:
        bimestre: Bimestre para filtrar as notas
        filtro_serie: Condição WHERE para filtrar séries
        disciplinas: Lista de disciplinas a serem incluídas
        nivel_id: Nível de ensino (2 para iniciais, 3 para finais)
        ano_letivo: Ano letivo para o qual gerar o relatório (padrão: 2025)
        escola_id: ID da escola para filtrar alunos (padrão: 60)
        status_matricula: Status de matrícula a filtrar (padrão: None para usar 'Ativo')
    
    Returns:
        str: Consulta SQL formatada
    """
    # Mapeamento de nomes abreviados para nomes completos no banco de dados
    mapeamento_disciplinas = {
        'L. PORTUGUESA': 'LÍNGUA PORTUGUESA',
        'ENS. RELIGIOSO': 'ENSINO RELIGIOSO',
        'ED. FÍSICA': 'EDUCAÇÃO FÍSICA',
        'L. INGLESA': 'LÍNGUA INGLESA',
        # Adicione outros mapeamentos conforme necessário
    }
    
    # Definir status de matrícula a filtrar
    if status_matricula is None:
        status_filtro = "('Ativo')"
    elif isinstance(status_matricula, str):
        status_filtro = f"('{status_matricula}')"
    elif isinstance(status_matricula, (list, tuple)):
        # Converter a lista em string formatada para SQL: ('Ativo', 'Transferido')
        formatted_statuses = []
        for s in status_matricula:
            formatted_statuses.append(f"'{s}'")
        status_filtro = f"({', '.join(formatted_statuses)})"
    else:
        status_filtro = "('Ativo')"  # Valor padrão seguro
    
    # Parte inicial da consulta comum a ambos os níveis
    query = f"""
        SELECT
            a.nome AS 'NOME DO ALUNO',
            a.sexo AS 'SEXO',
            a.data_nascimento AS 'NASCIMENTO',
            s.nome AS 'NOME_SERIE',
            t.id AS 'ID_TURMA',
            t.nome AS 'NOME_TURMA',
            t.turno AS 'TURNO',
            m.status AS 'STATUS',
            m.data_matricula AS 'DATA_MATRICULA',
            f.nome AS 'NOME_PROFESSOR',
    """
    
    # Adicionar as cláusulas CASE para cada disciplina
    for disciplina in disciplinas:
        nome_display = disciplina['nome']
        nome_bd = mapeamento_disciplinas.get(nome_display, nome_display)
        
        # ============================================================================
        # MELHORIA 3: Validar nome da disciplina antes de interpolar na query
        # ============================================================================
        try:
            nome_bd_validado = validar_nome_disciplina(nome_bd)
            bimestre_validado = validar_bimestre(bimestre)
            nivel_id_validado = validar_nivel_id(nivel_id)
        except ValueError as e:
            print(f"ERRO DE VALIDAÇÃO: {e}")
            continue  # Pula disciplina inválida
        
        query += f"""
            MAX(CASE WHEN d.nome = '{nome_bd_validado}' AND d.nivel_id = {nivel_id_validado} AND n.bimestre = '{bimestre_validado}' THEN n.nota END) AS '{disciplina['coluna']}',
        """
    
    # Remover a última vírgula e espaço
    query = query.rstrip(', \n')
    
    # Adicionar o resto da consulta
    query += f"""
        FROM
            Alunos a
        JOIN
            Matriculas m ON a.id = m.aluno_id
        JOIN
            Turmas t ON m.turma_id = t.id
        JOIN
            Serie s ON t.serie_id = s.id
        LEFT JOIN
            Notas n ON a.id = n.aluno_id AND n.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = {ano_letivo})
        LEFT JOIN
            Disciplinas d ON n.disciplina_id = d.id
        LEFT JOIN
            Funcionarios f ON f.turma = t.id AND f.cargo = 'Professor@'
        WHERE
            m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = {ano_letivo})
            AND a.escola_id = {escola_id}
            AND m.status IN {status_filtro}
            AND {filtro_serie if ('<' in filtro_serie or '>' in filtro_serie or 's.nome' in filtro_serie) else f"s.nome = '{filtro_serie}'"}
        GROUP BY
            a.id, a.nome, s.nome, t.id, t.nome, t.turno, m.status, m.data_matricula, f.nome
        ORDER BY
            a.nome ASC;
    """
    
    return query


def processar_dados_alunos(dados_aluno, disciplinas, preencher_nulos=False):
    """
    Converte os dados obtidos do banco em DataFrame e faz processamentos necessários
    
    Args:
        dados_aluno: Dados dos alunos obtidos da consulta SQL
        disciplinas: Lista de disciplinas para as quais processar as notas
        preencher_nulos: Se True, preenche valores nulos com 0, caso contrário mantém como nulos
    
    Returns:
        DataFrame: Dados processados
    """
    # Verificar se existem dados para processar
    if not dados_aluno:
        print("Aviso: Nenhum dado de aluno fornecido para processamento")
        return pd.DataFrame()  # Retorna DataFrame vazio
    
    # Convertendo os dados para um DataFrame
    df = pd.DataFrame(dados_aluno)
    
    # Processar as notas (manter como float para arredondamento posterior)
    for disciplina in disciplinas:
        coluna = disciplina['coluna']
        # Verificar se a coluna existe no DataFrame
        if coluna in df.columns:
            if preencher_nulos:
                df[coluna] = df[coluna].fillna(0)  # Preencher NaN com 0
            
            # Converter para float (NÃO para int ainda - o arredondamento será feito na geração do PDF)
            try:
                # Apenas converte valores não nulos para float
                for idx in df.index:
                    if pd.notnull(df.at[idx, coluna]):
                        try:
                            df.at[idx, coluna] = float(df.at[idx, coluna])
                        except:
                            if preencher_nulos:
                                df.at[idx, coluna] = 0.0
            except Exception as e:
                print(f"Erro ao processar coluna {coluna}: {e}")
    
    # Função auxiliar para converter string para data de forma segura
    def converter_para_data(valor):
        if pd.isnull(valor):
            return None
        
        if isinstance(valor, datetime.date):
            return valor
            
        # Se for string, tentar converter para data
        if isinstance(valor, str):
            try:
                # Tentar diferentes formatos de data
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
                    try:
                        return datetime.datetime.strptime(valor, fmt).date()
                    except ValueError:
                        continue
            except Exception:
                pass
        
        # Se não conseguir converter, retornar None
        return None
    
    # Filtrando os dados conforme as regras especificadas
    try:
        # Atualizadas para 2025
        data_cutoff_transferido = datetime.date(2025, 4, 30)
        data_cutoff_ativo = datetime.date(2025, 6, 19)
        
        # Verificar se a coluna DATA_MATRICULA existe
        if 'DATA_MATRICULA' in df.columns:
            # Converter a coluna DATA_MATRICULA para o tipo date
            df['DATA_MATRICULA'] = df['DATA_MATRICULA'].apply(converter_para_data)
            
            # Processar marcações especiais
            for index, row in df.iterrows():
                # Verificar se há data de matrícula antes de comparar
                if pd.notnull(row['DATA_MATRICULA']):
                    if row['STATUS'] == 'Ativo' and row['DATA_MATRICULA'] > data_cutoff_ativo:
                        df.at[index, 'NOME DO ALUNO'] += ' (2025.2)'  # Atualizado para 2025
                    elif row['STATUS'] == 'Transferido' and row['DATA_MATRICULA'] > data_cutoff_transferido:
                        df.at[index, 'NOME DO ALUNO'] += ' (Transf.)'
    except Exception as e:
        print(f"Erro ao processar datas de matrícula: {e}")
    
    return df


def gerar_documento_pdf(df, bimestre, nome_arquivo, disciplinas, nivel_ensino, ano_letivo=None):
    """
    Gera o documento PDF com as notas dos alunos
    
    Args:
        df: DataFrame com os dados dos alunos e suas notas
        bimestre: Bimestre para o título do documento
        nome_arquivo: Nome do arquivo PDF a ser gerado
        disciplinas: Lista de disciplinas para incluir na tabela
        nivel_ensino: Nível de ensino ("fundamental_iniciais" ou "fundamental_finais")
        ano_letivo: Ano letivo para o relatório (padrão: ano atual)
    """
    # Importar Spacer no início da função para garantir que esteja disponível em todo o escopo
    from reportlab.platypus import Spacer
    from reportlab.lib.pagesizes import letter, landscape
    
    # Se o ano letivo não for especificado, usar o ano atual
    if ano_letivo is None:
        ano_letivo = datetime.datetime.now().year
    
    # Função auxiliar para adicionar quebra de linha nos títulos das colunas
    def adicionar_quebra_linha(texto):
        return Paragraph('<br/>'.join(list(texto.upper())), ParagraphStyle(
            'header', 
            fontName='Helvetica-Bold', 
            fontSize=10, 
            textColor=black, 
            alignment=1))  # Centralizado
    
    # Informações do cabeçalho
    cabecalho = [
        "ESTADO DO MARANHÃO",
        "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>UEB PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 06.003.636/0001-73</b>"
    ]
    
    # Caminhos das figuras
    figura_superior_path = os.path.join(os.path.dirname(__file__), 'pacologo.png')
    figura_inferior_path = os.path.join(os.path.dirname(__file__), 'logopaco.jpg')
    
    # Verificar se as imagens existem
    try:
        figura_superior = Image(figura_superior_path, width=1 * inch, height=1 * inch)
    except Exception as e:
        print(f"Aviso: Não foi possível carregar a imagem superior: {e}")
        # Criar um espaço em branco no lugar da imagem
        figura_superior = Spacer(1 * inch, 1 * inch)
    
    try:
        figura_inferior = Image(figura_inferior_path, width=1.5 * inch, height=1 * inch)
    except Exception as e:
        print(f"Aviso: Não foi possível carregar a imagem inferior: {e}")
        # Criar um espaço em branco no lugar da imagem
        figura_inferior = Spacer(1.5 * inch, 1 * inch)
    
    # Define as margens da página (em pontos) para margens estreitas
    left_margin = 36    # Margem esquerda (0,5 polegadas)
    right_margin = 18   # Margem direita (0,5 polegadas)
    top_margin = 18     # Margem superior (0,5 polegadas)
    bottom_margin = 18  # Margem inferior (0,5 polegadas)
    
    # Cria o documento PDF com as margens ajustadas e orientação apropriada
    doc = SimpleDocTemplate(
        nome_arquivo, 
        pagesize=letter,  # Sempre usar orientação retrato
        leftMargin=left_margin, 
        rightMargin=right_margin, 
        topMargin=top_margin, 
        bottomMargin=bottom_margin
    )
    elements = []
    
    # Adicionar a capa
    data = [
        [figura_superior,
         Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1)),
         figura_inferior]
    ]
    # Usar larguras fixas para orientação retrato
    table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 3.3 * inch))
    elements.append(Paragraph(f"<b>NOTAS {bimestre.upper()} {ano_letivo}</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1)))
    elements.append(Spacer(1, 4 * inch))
    elements.append(Paragraph(f"<b>{ano_letivo}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
    elements.append(PageBreak())
    
    # Iniciar a segunda página com a tabela
    elements.append(PageBreak())
    
    pagina_atual = 3
    # Agrupar os dados por nome_serie, nome_turma e turno
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        # Verifique se a página atual é par, se for, insira uma página em branco para garantir que a tabela comece em uma página ímpar
        if pagina_atual == 4:
            elements.append(PageBreak())  # Adicionar uma quebra de página
            pagina_atual += 1
        
        # Obter o ID da turma do primeiro registro
        turma_id = turma_df['ID_TURMA'].iloc[0] if 'ID_TURMA' in turma_df.columns else None
        
        # Buscar professores da turma ordenados por quantidade de disciplinas
        if turma_id:
            professores_turma = obter_professores_turma(turma_id, ano_letivo)
            if professores_turma:
                # Formatar nomes (primeiro e segundo nome) e criar string
                nomes_formatados = [formatar_nome_professor(p['professor']) for p in professores_turma]
                
                # Exceção especial: adicionar "Josué Alves" para o 3º Ano
                if nome_serie == "3º Ano" and "Josué Alves" not in [formatar_nome_professor(p['professor']) for p in professores_turma]:
                    nomes_formatados.append("Josué Alves")
                
                if len(nomes_formatados) == 1:
                    nome_professor = nomes_formatados[0]
                elif len(nomes_formatados) == 2:
                    nome_professor = f"{nomes_formatados[0]} e {nomes_formatados[1]}"
                else:
                    # Para 3 ou mais: "Nome1, Nome2 e Nome3"
                    nome_professor = ", ".join(nomes_formatados[:-1]) + f" e {nomes_formatados[-1]}"
            else:
                # Fallback para o professor do DataFrame
                nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Sem Professor'
                nome_professor = formatar_nome_professor(nome_professor)
        else:
            # Fallback para o professor do DataFrame
            nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Sem Professor'
            nome_professor = formatar_nome_professor(nome_professor)
        
        # Adicionar o cabeçalho antes de cada tabela
        data = [
            [figura_superior,
             Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1)),
             figura_inferior]
        ]
        table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
        table_style = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ])
        table.setStyle(table_style)
        elements.append(table)
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Adicionar o título da turma
        elements.append(Paragraph(f"<b>{bimestre.upper()}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=14, alignment=1)))
        elements.append(Spacer(1, 0.125 * inch))
        # Adicionar o título da turma
        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {ano_letivo}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=14, alignment=0)))
        elements.append(Spacer(1, 0.125 * inch))
        # Estilo para o professor e coordenador
        estilo_esquerda = ParagraphStyle(name='Esquerda', fontSize=12, alignment=0)
        estilo_direita = ParagraphStyle(name='Direita', fontSize=12, alignment=2)
        
        # Determinar o nome do coordenador com base no nível de ensino
        nome_coordenador = "Laise de Laine" if nivel_ensino == "fundamental_iniciais" else "Allanne Leão Sousa"
        
        # Criar parágrafos
        paragrafo_professor = Paragraph(f"<b>Professor(a): {nome_professor}</b>", estilo_esquerda)
        paragrafo_coordenador = Paragraph(f"<b>Coordenadora: {nome_coordenador}</b>", estilo_direita)
        # Criar tabela com os textos alinhados
        dados_tabela = [[paragrafo_professor, paragrafo_coordenador]]
        tabela = Table(dados_tabela)
        table_style = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ])
        tabela.setStyle(table_style)
        
        # Adicionar elementos ao PDF
        elements.append(tabela)
        elements.append(Spacer(1, 0.125 * inch))
        
        # Definir os dados da tabela com as notas
        cabecalho_tabela = ['Nº', 'NOME DO ALUNO'] 
        for disciplina in disciplinas:
            # Usar apenas o nome para o cabeçalho (sem a parte 'NOTA_')
            nome_display = disciplina['nome']
            cabecalho_tabela.append(adicionar_quebra_linha(nome_display))
        
        data = [cabecalho_tabela]
        
        # Adicionar as notas de cada disciplina
        for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
            linha_aluno = [row_num, row['NOME DO ALUNO']]
            
            # Adicionar as notas de cada disciplina
            for disciplina in disciplinas:
                coluna = disciplina['coluna']
                # Acessar coluna de forma segura para evitar KeyError quando a coluna estiver ausente
                valor_nota = row.get(coluna, None) if hasattr(row, 'get') else (row[coluna] if coluna in row.index else None)
                if pd.notnull(valor_nota):
                    # Nota vem multiplicada por 10 (ex: 76.7 representa 7.67)
                    nota_real = float(valor_nota) / 10
                    # Arredondar usando Decimal para garantir arredondamento correto (sempre para cima quando >= 5)
                    nota_decimal = Decimal(str(nota_real))
                    nota_arredondada = float(nota_decimal.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
                    # Multiplicar por 10 novamente para exibir (ex: 7.4 → 74)
                    nota_final = nota_arredondada * 10
                    # Mostrar como inteiro
                    linha_aluno.append(int(nota_final))
                else:
                    linha_aluno.append("")  # Célula vazia para notas nulas
            
            data.append(linha_aluno)
        
        # Criar a tabela de notas - Ajustar larguras para orientação retrato
        col_widths = [0.35 * inch, 3.2 * inch]  # Largura fixa para número e nome
        disciplina_width = 0.45 * inch  # Largura para disciplinas
        for _ in disciplinas:
            col_widths.append(disciplina_width)
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), white),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Manter o alinhamento à esquerda para a coluna 'Nome'
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('ROWHEIGHT', (0, 1), (-1, -1), 20),  # Altura normal das linhas sem espaço para assinatura
        ]))
        elements.append(table)
        elements.append(PageBreak())
        pagina_atual += 1
    
    # Build the PDF
    doc.build(elements)


def gerar_documento_pdf_com_assinatura(df, bimestre, nome_arquivo, disciplinas, nivel_ensino, ano_letivo=None):
    """
    Gera o documento PDF com as notas dos alunos, com coluna para assinatura dos responsáveis e em modo paisagem
    
    Args:
        df: DataFrame com os dados dos alunos e suas notas
        bimestre: Bimestre para o título do documento
        nome_arquivo: Nome do arquivo PDF a ser gerado
        disciplinas: Lista de disciplinas para incluir na tabela
        nivel_ensino: Nível de ensino ("fundamental_iniciais" ou "fundamental_finais")
        ano_letivo: Ano letivo para o relatório (padrão: ano atual)
    """
    # Importar Spacer no início da função para garantir que esteja disponível em todo o escopo
    from reportlab.platypus import Spacer
    
    # Se o ano letivo não for especificado, usar o ano atual
    if ano_letivo is None:
        ano_letivo = datetime.datetime.now().year
    
    # Função auxiliar para adicionar quebra de linha nos títulos das colunas
    def adicionar_quebra_linha(texto):
        return Paragraph('<br/>'.join(list(texto.upper())), ParagraphStyle(
            'header', 
            fontName='Helvetica-Bold', 
            fontSize=10, 
            textColor=black, 
            alignment=1))  # Centralizado
    
    # Informações do cabeçalho
    cabecalho = [
        "ESTADO DO MARANHÃO",
        "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>UEB PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 06.003.636/0001-73</b>"
    ]
    
    # Caminhos das figuras
    figura_superior_path = os.path.join(os.path.dirname(__file__), 'pacologo.png')
    figura_inferior_path = os.path.join(os.path.dirname(__file__), 'logopaco.jpg')
    
    # Verificar se as imagens existem
    try:
        figura_superior = Image(figura_superior_path, width=1 * inch, height=1 * inch)
    except Exception as e:
        print(f"Aviso: Não foi possível carregar a imagem superior: {e}")
        # Criar um espaço em branco no lugar da imagem
        figura_superior = Spacer(1 * inch, 1 * inch)
    
    try:
        figura_inferior = Image(figura_inferior_path, width=1.5 * inch, height=1 * inch)
    except Exception as e:
        print(f"Aviso: Não foi possível carregar a imagem inferior: {e}")
        # Criar um espaço em branco no lugar da imagem
        figura_inferior = Spacer(1.5 * inch, 1 * inch)
    
    # Define as margens da página (em pontos) para margens estreitas
    left_margin = 36    # Margem esquerda (0,5 polegadas)
    right_margin = 18   # Margem direita (0,5 polegadas)
    top_margin = 18     # Margem superior (0,5 polegadas)
    bottom_margin = 18  # Margem inferior (0,5 polegadas)
    
    # Cria o documento PDF com as margens ajustadas e orientação paisagem
    doc = SimpleDocTemplate(
        nome_arquivo, 
        pagesize=landscape(letter), 
        leftMargin=left_margin, 
        rightMargin=right_margin, 
        topMargin=top_margin, 
        bottomMargin=bottom_margin
    )
    elements = []
    
    # Adicionar a capa
    data = [
        [figura_superior,
         Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1)),
         figura_inferior]
    ]
    table = Table(data, colWidths=[1.32 * inch, 6 * inch, 1.32 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 2.5 * inch))
    elements.append(Paragraph(f"<b>NOTAS {bimestre.upper()} {ano_letivo}</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1)))
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph("<b>RELATÓRIO COM ASSINATURA DOS RESPONSÁVEIS</b>", ParagraphStyle(name='Subtitulo', fontSize=16, alignment=1)))
    elements.append(Spacer(1, 3 * inch))
    elements.append(Paragraph(f"<b>{ano_letivo}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
    elements.append(PageBreak())
    
    pagina_atual = 3
    # Agrupar os dados por nome_serie, nome_turma e turno
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        # Verifique se a página atual é par, se for, insira uma página em branco para garantir que a tabela comece em uma página ímpar
        if pagina_atual == 4:
            elements.append(PageBreak())  # Adicionar uma quebra de página
            pagina_atual += 1
        
        # Obter o ID da turma do primeiro registro
        turma_id = turma_df['ID_TURMA'].iloc[0] if 'ID_TURMA' in turma_df.columns else None
        
        # Buscar professores da turma ordenados por quantidade de disciplinas
        if turma_id:
            professores_turma = obter_professores_turma(turma_id, ano_letivo)
            if professores_turma:
                # Formatar nomes (primeiro e segundo nome) e criar string
                nomes_formatados = [formatar_nome_professor(p['professor']) for p in professores_turma]
                
                # Exceção especial: adicionar "Josué Alves" para o 3º Ano
                if nome_serie == "3º Ano" and "Josué Alves" not in [formatar_nome_professor(p['professor']) for p in professores_turma]:
                    nomes_formatados.append("Josué Alves")
                
                if len(nomes_formatados) == 1:
                    nome_professor = nomes_formatados[0]
                elif len(nomes_formatados) == 2:
                    nome_professor = f"{nomes_formatados[0]} e {nomes_formatados[1]}"
                else:
                    # Para 3 ou mais: "Nome1, Nome2 e Nome3"
                    nome_professor = ", ".join(nomes_formatados[:-1]) + f" e {nomes_formatados[-1]}"
            else:
                # Fallback para o professor do DataFrame
                nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Sem Professor'
                nome_professor = formatar_nome_professor(nome_professor)
        else:
            # Fallback para o professor do DataFrame
            nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Sem Professor'
            nome_professor = formatar_nome_professor(nome_professor)
        
        # Adicionar o cabeçalho antes de cada tabela
        data = [
            [figura_superior,
             Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1)),
             figura_inferior]
        ]
        table = Table(data, colWidths=[1.32 * inch, 6 * inch, 1.32 * inch])
        table_style = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ])
        table.setStyle(table_style)
        elements.append(table)
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Adicionar o título da turma
        elements.append(Paragraph(f"<b>{bimestre.upper()}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=14, alignment=1)))
        elements.append(Spacer(1, 0.125 * inch))
        # Adicionar o título da turma
        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {ano_letivo}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=14, alignment=0)))
        elements.append(Spacer(1, 0.125 * inch))
        # Estilo para o professor e coordenador
        estilo_esquerda = ParagraphStyle(name='Esquerda', fontSize=12, alignment=0)
        estilo_direita = ParagraphStyle(name='Direita', fontSize=12, alignment=2)
        
        # Determinar o nome do coordenador com base no nível de ensino
        nome_coordenador = "Laise de Laine" if nivel_ensino == "fundamental_iniciais" else "Allanne Leão Sousa"
        
        # Criar parágrafos
        paragrafo_professor = Paragraph(f"<b>Professor(a): {nome_professor}</b>", estilo_esquerda)
        paragrafo_coordenador = Paragraph(f"<b>Coordenadora: {nome_coordenador}</b>", estilo_direita)
        # Criar tabela com os textos alinhados
        dados_tabela = [[paragrafo_professor, paragrafo_coordenador]]
        tabela = Table(dados_tabela)
        table_style = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ])
        tabela.setStyle(table_style)
        
        # Adicionar elementos ao PDF
        elements.append(tabela)
        elements.append(Spacer(1, 0.125 * inch))
        
        # Definir os dados da tabela com as notas
        cabecalho_tabela = ['Nº', 'NOME DO ALUNO'] 
        for disciplina in disciplinas:
            # Usar apenas o nome para o cabeçalho (sem a parte 'NOTA_')
            nome_display = disciplina['nome']
            cabecalho_tabela.append(adicionar_quebra_linha(nome_display))
        
        # Adicionar coluna de assinatura
        cabecalho_tabela.append('ASSINATURA DO RESPONSÁVEL')  # Horizontal, sem quebra de linha
        
        data = [cabecalho_tabela]
        
        # Adicionar as notas de cada disciplina
        for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
            linha_aluno = [row_num, row['NOME DO ALUNO']]
            
            # Adicionar as notas de cada disciplina
            for disciplina in disciplinas:
                coluna = disciplina['coluna']
                # Acessar coluna de forma segura para evitar KeyError quando a coluna estiver ausente
                valor_nota = row.get(coluna, None) if hasattr(row, 'get') else (row[coluna] if coluna in row.index else None)
                if pd.notnull(valor_nota):
                    # Nota vem multiplicada por 10 (ex: 76.7 representa 7.67)
                    nota_real = float(valor_nota) / 10
                    # Arredondar usando Decimal para garantir arredondamento correto (sempre para cima quando >= 5)
                    nota_decimal = Decimal(str(nota_real))
                    nota_arredondada = float(nota_decimal.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
                    # Multiplicar por 10 novamente para exibir (ex: 7.4 → 74)
                    nota_final = nota_arredondada * 10
                    # Mostrar como inteiro
                    linha_aluno.append(int(nota_final))
                else:
                    linha_aluno.append("")  # Célula vazia para notas nulas
            
            # Adicionar espaço para assinatura
            linha_aluno.append("")
            
            data.append(linha_aluno)
        
        # Criar a tabela de notas - Ajustar larguras para acomodar a assinatura
        if nivel_ensino == "fundamental_finais":
            # Larguras ajustadas para orientação paisagem
            col_widths = [0.35 * inch, 3.2 * inch]  # Largura para número e nome
            disciplina_width = 0.35 * inch  # Largura maior para disciplinas em paisagem
            for _ in disciplinas:
                col_widths.append(disciplina_width)
            col_widths.append(3.15 * inch)  # Largura para assinatura
        else:
            # Larguras originais para orientação retrato
            col_widths = [0.35 * inch, 3.2 * inch]  # Largura fixa para número e nome
            disciplina_width = 0.35 * inch  # Diminuída para 0.35 inch (era 0.65 inch)
            for _ in disciplinas:
                col_widths.append(disciplina_width)
            col_widths.append(3.15 * inch)  # Aumentada para 3 inch (era 2 inch)
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), white),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Manter o alinhamento à esquerda para a coluna 'Nome'
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, black),
            # Altura maior para linhas com espaço para assinatura
            ('ROWHEIGHT', (0, 1), (-1, -1), 30),
        ]))
        elements.append(table)
        elements.append(PageBreak())
        pagina_atual += 1
    
    # Build the PDF
    doc.build(elements)


def gerar_relatorio_notas(bimestre=None, nivel_ensino="iniciais", ano_letivo=None, escola_id=60, status_matricula=None, preencher_nulos=False):
    """
    Função unificada para gerar relatórios de notas bimestrais.
    
    Esta função unifica a lógica das funções nota_bimestre e nota_bimestre2,
    permitindo gerar relatórios para ambos os níveis de ensino (iniciais e finais)
    através de um único ponto de entrada.
    
    Args:
        bimestre (str): Bimestre para gerar o relatório ("1º bimestre", "2º bimestre", etc)
        nivel_ensino (str): Tipo de relatório ("iniciais" para 1º ao 5º ano ou "finais" para 6º ao 9º ano)
        ano_letivo (int): Ano letivo para o relatório (padrão: ano atual)
        escola_id (int): ID da escola para filtrar alunos (padrão: 60)
        status_matricula (str|list): Status de matrícula(s) a incluir no relatório (padrão: None = 'Ativo')
        preencher_nulos (bool): Se True, preenche valores nulos com 0, caso contrário deixa em branco
    
    Returns:
        bool: True se o relatório foi gerado com sucesso, False caso contrário
    """
    try:
        if bimestre is None:
            raise ValueError("É necessário especificar o bimestre para gerar o relatório")
        
        # Inicializar variáveis para conexão com o banco de dados
        conn = None
        cursor = None
        
        # Se o ano letivo não for especificado, usar o ano atual
        if ano_letivo is None:
            ano_letivo = 2025  # Alterado para usar 2025 como padrão
        
        # Configurações baseadas no nível de ensino
        if nivel_ensino == "iniciais":
            filtro_serie = "s.id <= 7"
            disciplinas = obter_disciplinas_iniciais()
            nome_arquivo = f'Notas {bimestre} {ano_letivo}.pdf'
            nivel_id = 2
            tipo_ensino = "fundamental_iniciais"
        elif nivel_ensino == "finais":
            filtro_serie = "s.id > 7"
            disciplinas = obter_disciplinas_finais()
            nome_arquivo = f'Notas {bimestre} {ano_letivo} Series Finais.pdf'
            nivel_id = 3
            tipo_ensino = "fundamental_finais"
        else:
            raise ValueError(f"Nível de ensino '{nivel_ensino}' inválido. Use 'iniciais' ou 'finais'.")
        
        # Se status_matricula incluir transferidos, adicionar ao nome do arquivo
        if status_matricula and ('Transferido' in status_matricula if isinstance(status_matricula, (list, tuple)) else status_matricula == 'Transferido'):
            nome_arquivo = nome_arquivo.replace('.pdf', ' (com Transferidos).pdf')
        
        # Conectar ao banco de dados
        conn = conectar_bd()
        cursor = conn.cursor(dictionary=True)
        
        # Ajustar a consulta SQL para usar todos os parâmetros
        query = construir_consulta_sql(
            bimestre=bimestre, 
            filtro_serie=filtro_serie, 
            disciplinas=disciplinas, 
            nivel_id=nivel_id, 
            ano_letivo=ano_letivo,
            escola_id=escola_id,
            status_matricula=status_matricula
        )
        
        cursor.execute(query)
        dados_aluno = cursor.fetchall()
        
        if not dados_aluno:
            print(f"Nenhum dado encontrado para o bimestre {bimestre} e nível {nivel_ensino} no ano {ano_letivo}")
            return False
        
        # Processar os dados e gerar o PDF
        df = processar_dados_alunos(dados_aluno, disciplinas, preencher_nulos)
        gerar_documento_pdf(df, bimestre, nome_arquivo, disciplinas, tipo_ensino, ano_letivo)
        
        # Fechar recursos
        cursor.close()
        conn.close()
        
        # Abrir o PDF gerado
        abrir_pdf_com_programa_padrao(nome_arquivo)
        
        return True
        
    except Exception as e:
        import traceback
        print(f"Erro ao gerar relatório de notas: {str(e)}")
        traceback.print_exc()
        
        # Garantir que as conexões sejam fechadas em caso de erro
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
            
        return False


# Modificar as funções existentes para usar a nova função unificada
def nota_bimestre(bimestre=None, preencher_nulos=False):
    """
    Gera relatório de notas bimestrais para séries iniciais (1º ao 5º ano)
    
    Args:
        bimestre: Bimestre para gerar o relatório ("1º bimestre", etc)
        preencher_nulos: Se True, preenche valores nulos com 0
    """
    return gerar_relatorio_notas(bimestre, "iniciais", preencher_nulos=preencher_nulos)


def nota_bimestre2(bimestre=None, preencher_nulos=False):
    """
    Gera relatório de notas bimestrais para séries finais (6º ao 9º ano)
    
    Args:
        bimestre: Bimestre para gerar o relatório ("1º bimestre", etc)
        preencher_nulos: Se True, preenche valores nulos com 0
    """
    return gerar_relatorio_notas(bimestre, "finais", preencher_nulos=preencher_nulos)


def gerar_relatorio_notas_com_assinatura(bimestre=None, nivel_ensino="iniciais", ano_letivo=None, escola_id=60, status_matricula=None, preencher_nulos=False):
    """
    Função para gerar relatórios de notas bimestrais com coluna para assinatura de responsáveis e em modo paisagem.
    
    Args:
        bimestre (str): Bimestre para gerar o relatório ("1º bimestre", "2º bimestre", etc)
        nivel_ensino (str): Tipo de relatório ("iniciais" para 1º ao 5º ano ou "finais" para 6º ao 9º ano)
        ano_letivo (int): Ano letivo para o relatório (padrão: ano atual)
        escola_id (int): ID da escola para filtrar alunos (padrão: 60)
        status_matricula (str|list): Status de matrícula(s) a incluir no relatório (padrão: None = 'Ativo')
        preencher_nulos (bool): Se True, preenche valores nulos com 0, caso contrário deixa em branco
    
    Returns:
        bool: True se o relatório foi gerado com sucesso, False caso contrário
    """
    try:
        if bimestre is None:
            raise ValueError("É necessário especificar o bimestre para gerar o relatório")
        
        # Inicializar variáveis para conexão com o banco de dados
        conn = None
        cursor = None
        
        # Se o ano letivo não for especificado, usar o ano atual
        if ano_letivo is None:
            ano_letivo = 2025  # Alterado para usar 2025 como padrão
        
        # Configurações baseadas no nível de ensino
        if nivel_ensino == "iniciais":
            filtro_serie = "s.id <= 7"
            disciplinas = obter_disciplinas_iniciais()
            nome_arquivo = f'Notas {bimestre} {ano_letivo} (Com Assinatura).pdf'
            nivel_id = 2
            tipo_ensino = "fundamental_iniciais"
        elif nivel_ensino == "finais":
            filtro_serie = "s.id > 7"
            disciplinas = obter_disciplinas_finais()
            nome_arquivo = f'Notas {bimestre} {ano_letivo} Series Finais (Com Assinatura).pdf'
            nivel_id = 3
            tipo_ensino = "fundamental_finais"
        else:
            raise ValueError(f"Nível de ensino '{nivel_ensino}' inválido. Use 'iniciais' ou 'finais'.")
        
        # Se status_matricula incluir transferidos, adicionar ao nome do arquivo
        if status_matricula and ('Transferido' in status_matricula if isinstance(status_matricula, (list, tuple)) else status_matricula == 'Transferido'):
            nome_arquivo = nome_arquivo.replace('.pdf', ' (com Transferidos).pdf')
        
        # Conectar ao banco de dados
        conn = conectar_bd()
        cursor = conn.cursor(dictionary=True)
        
        # Ajustar a consulta SQL para usar todos os parâmetros
        query = construir_consulta_sql(
            bimestre=bimestre, 
            filtro_serie=filtro_serie, 
            disciplinas=disciplinas, 
            nivel_id=nivel_id, 
            ano_letivo=ano_letivo,
            escola_id=escola_id,
            status_matricula=status_matricula
        )
        
        cursor.execute(query)
        dados_aluno = cursor.fetchall()
        
        if not dados_aluno:
            print(f"Nenhum dado encontrado para o bimestre {bimestre} e nível {nivel_ensino} no ano {ano_letivo}")
            return False
        
        # Processar os dados e gerar o PDF
        df = processar_dados_alunos(dados_aluno, disciplinas, preencher_nulos)
        gerar_documento_pdf_com_assinatura(df, bimestre, nome_arquivo, disciplinas, tipo_ensino, ano_letivo)
        
        # Fechar recursos
        cursor.close()
        conn.close()
        
        # Abrir o PDF gerado
        abrir_pdf_com_programa_padrao(nome_arquivo)
        
        return True
        
    except Exception as e:
        import traceback
        print(f"Erro ao gerar relatório de notas com assinatura: {str(e)}")
        traceback.print_exc()
        
        # Garantir que as conexões sejam fechadas em caso de erro
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
            
        return False


def nota_bimestre_com_assinatura(bimestre=None, preencher_nulos=False):
    """
    Gera relatório de notas bimestrais para séries iniciais (1º ao 5º ano) com coluna para assinatura dos responsáveis
    
    Args:
        bimestre: Bimestre para gerar o relatório ("1º bimestre", etc)
        preencher_nulos: Se True, preenche valores nulos com 0
    """
    return gerar_relatorio_notas_com_assinatura(bimestre, "iniciais", preencher_nulos=preencher_nulos)


def nota_bimestre2_com_assinatura(bimestre=None, preencher_nulos=False):
    """
    Gera relatório de notas bimestrais para séries finais (6º ao 9º ano) com coluna para assinatura dos responsáveis
    
    Args:
        bimestre: Bimestre para gerar o relatório ("1º bimestre", etc)
        preencher_nulos: Se True, preenche valores nulos com 0
    """
    return gerar_relatorio_notas_com_assinatura(bimestre, "finais", preencher_nulos=preencher_nulos)


def abrir_pdf_com_programa_padrao(pdf_path):
    """
    Abre o arquivo PDF gerado com o programa padrão do sistema operacional
    
    Args:
        pdf_path: Caminho do arquivo PDF a ser aberto
    """
    if platform.system() == "Windows":
        os.startfile(pdf_path)
    elif platform.system() == "Darwin":  # macOS
        os.system(f"open '{pdf_path}'")
    else:  # Linux e outros sistemas
        os.system(f"xdg-open '{pdf_path}'")