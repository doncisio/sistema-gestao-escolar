from src.core.conexao import conectar_bd
from src.core.config import ANO_LETIVO_ATUAL, PROJECT_ROOT
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from pathlib import Path
import io
import os
from datetime import datetime

def formatar_telefone(telefone):
    """Formata um número de telefone para o formato (98) XXXXX-XXXX."""
    if not telefone:
        return "Telefone não informado"
    telefone = str(telefone)
    if "." in telefone:
        telefone = telefone.split(".")[0]
    telefone = telefone.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
    if len(telefone) < 10:
        telefone = "98" + telefone
    if len(telefone) < 10:
        return "Telefone Inválido"
    if len(telefone) == 10:
        return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
    elif len(telefone) == 11:
        return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
    else:
        return "Telefone Inválido"
def reduzir_nome(nome_completo):
    """
    Reduz um nome completo para as duas primeiras partes (nome e sobrenome principal).

    Args:
        nome_completo (str): O nome completo da pessoa.

    Returns:
        str: O nome reduzido, consistindo no nome e sobrenome principal.
    """
    nomes = nome_completo.split()
    if len(nomes) >= 2:
        return f"{nomes[0]} {nomes[1]}"  # Retorna o primeiro nome e o sobrenome principal
    elif len(nomes) == 1:
        return nomes[0]  # Se houver apenas um nome, retorna ele mesmo
    else:
        return ""  # Se o nome estiver vazio, retorna uma string vazia

def criar_cracha(aluno, responsavel, pdf_base):
    """Cria um crachá em PDF para um aluno e seu responsável, retornando um objeto BytesIO."""
    try:
        pdf_base_reader = PdfReader(pdf_base)
        primeira_pagina = pdf_base_reader.pages[0]
        largura_pagina = float(primeira_pagina.mediabox.width)
        altura_pagina = float(primeira_pagina.mediabox.height)
    except Exception as e:
        print(f"ERRO ao ler template PDF: {e}")
        raise
    
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(largura_pagina, altura_pagina))
    fonte_tamanho = 7.5
    can.setFont("Helvetica-BoldOblique", fonte_tamanho)
    largura_texto = can.stringWidth(aluno['NOME DO ALUNO'], "Helvetica-BoldOblique", fonte_tamanho)
    largura_maxima = largura_pagina - 50
    while largura_texto > largura_maxima and fonte_tamanho > 10:
        fonte_tamanho -= 1
        can.setFont("Helvetica-BoldOblique", fonte_tamanho)
        largura_texto = can.stringWidth(aluno['NOME DO ALUNO'], "Helvetica-BoldOblique", fonte_tamanho)
    x_pos1 = 68
    y_pos1 = 107
    y_pos2 = 87
    y_pos3 = 67
    y_pos4 = 47
    can.drawString(x_pos1, y_pos1, responsavel['responsavel'])
    can.drawString(x_pos1, y_pos2, formatar_telefone(responsavel['telefone']) if responsavel['telefone'] else "Telefone não informado")
    can.drawString(x_pos1, y_pos3, aluno['NOME DO ALUNO'])
    can.drawString(x_pos1, y_pos4, reduzir_nome(aluno['NOME_PROFESSOR']) if aluno['NOME_PROFESSOR'] else "")
    can.save()
    packet.seek(0)
    
    try:
        overlay = PdfReader(packet)
        writer = PdfWriter()
        
        for page in pdf_base_reader.pages:
            # Cria uma cópia da página original
            new_page = writer.add_page(page)
            # Faz o merge com o overlay
            new_page.merge_page(overlay.pages[0])

        # Prepare um BytesIO para retornar o PDF
        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        print(f"Cracha criado para {aluno['NOME DO ALUNO']} - {responsavel['responsavel']}.")
        return output_stream
    except Exception as e:
        print(f"ERRO ao criar crachá: {e}")
        raise

def gerar_crachas_responsaveis(aluno, pdf_base):
    """Gera crachás para os responsáveis de um aluno, retornando uma lista de objetos BytesIO."""
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    try:
        query_responsaveis = """
            SELECT 
                r.nome AS responsavel,
                r.telefone AS telefone
            FROM 
                Responsaveis r
            JOIN 
                ResponsaveisAlunos ra ON r.id = ra.responsavel_id  
            WHERE 
                ra.aluno_id = %s;
        """
        cursor.execute(query_responsaveis, (aluno['id'],))
        responsaveis = cursor.fetchall()

        if not responsaveis:
            print(f"Nenhum responsável encontrado para o aluno {aluno['NOME DO ALUNO']}.")
            return []  # Retorna uma lista vazia se nenhum responsável for encontrado

        cracha_streams = []
        for responsavel in responsaveis:
            cracha_stream = criar_cracha(aluno, responsavel, pdf_base)
            cracha_streams.append(cracha_stream)

        return cracha_streams  # Retorna a lista de objetos BytesIO

    finally:
        cursor.close()
        conn.close()

def obter_todos_alunos():
    """Obtém todos os alunos que atendem aos critérios especificados e inclui informações da série e turma."""
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    try:
        query_alunos = """
            SELECT 
                a.id AS id,
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
                m.data_matricula AS 'DATA_MATRICULA',
                t.id AS 'ID_TURMA'  -- Adiciona o ID da turma
            FROM 
                Alunos a
            JOIN 
                Matriculas m ON a.id = m.aluno_id
            JOIN 
                Turmas t ON m.turma_id = t.id
            JOIN 
                series s ON t.serie_id = s.id
            LEFT JOIN
                Funcionarios f ON f.turma = t.id AND f.cargo = 'Professor@'
            WHERE 
                m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
            AND 
                a.escola_id = 60
            AND
                m.status = 'Ativo'
            AND s.id <=7
            GROUP BY 
                a.id, a.nome, a.sexo, a.data_nascimento, s.nome, t.nome, t.turno, m.status, f.nome, m.data_matricula, s.id, t.id  -- Inclui o ID da turma no GROUP BY
            ORDER BY
                s.nome, t.nome  -- Ordena por série e turma
        """
        cursor.execute(query_alunos, (ANO_LETIVO_ATUAL,))
        alunos = cursor.fetchall()
        print(f"Debug: Buscando alunos para ano letivo {ANO_LETIVO_ATUAL}")
        print(f"Debug: {len(alunos)} alunos encontrados")
        return alunos
    finally:
        cursor.close()
        conn.close()

def gerar_crachas_para_todos_os_alunos():
    alunos = obter_todos_alunos()
    if not alunos:
        print("Nenhum aluno encontrado.")
        return

    # Agrupar alunos por série e turma
    grupos = {}
    for aluno in alunos:
        serie_turma = (aluno['NOME_SERIE'], aluno['NOME_TURMA'])
        if serie_turma not in grupos:
            grupos[serie_turma] = []
        grupos[serie_turma].append(aluno)

    # Caminho para o PDF base e saída
    caminho_template = PROJECT_ROOT / 'Modelos' / 'MODELO CRACHA.pdf'
    caminho_cracha = PROJECT_ROOT / 'assets' / 'crachas'
    caminho_cracha.mkdir(parents=True, exist_ok=True)
    diploma_original = str(caminho_template)
    
    # Verificar se o template existe
    if not caminho_template.exists():
        print(f"ERRO: Template não encontrado em {caminho_template}")
        print(f"Verifique se o arquivo existe na pasta 'Modelos'")
        return

    # Gerar crachás para cada grupo
    for serie_turma, alunos_grupo in grupos.items():
        nome_serie, nome_turma = serie_turma
        cracha_streams_grupo = []

        for aluno in alunos_grupo:
            cracha_streams_aluno = gerar_crachas_responsaveis(aluno, diploma_original)
            if cracha_streams_aluno:
                cracha_streams_grupo.extend(cracha_streams_aluno)

        # Criar um único PDF com todos os crachás do grupo
        if cracha_streams_grupo:
            writer = PdfWriter()
            for cracha_stream in cracha_streams_grupo:
                cracha_reader = PdfReader(cracha_stream)
                for page in cracha_reader.pages:
                    writer.add_page(page)

            # Define o nome do arquivo
            nome_arquivo_unico = caminho_cracha / f"Crachas_{nome_serie}_{nome_turma}_unico.pdf"

            # Escreve todas as páginas no arquivo
            with open(nome_arquivo_unico, "wb") as output_pdf:
                writer.write(output_pdf)

            print(f"Crachás da {nome_serie} - Turma {nome_turma} gerados em {nome_arquivo_unico}")
        else:
            print(f"Nenhum crachá gerado para {nome_serie} - Turma {nome_turma}.")


def obter_alunos_para_selecao():
    """Obtém lista de alunos ativos para seleção em interface.
    
    Returns:
        list: Lista de dicionários com id, nome, série e turma dos alunos
    """
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                a.id,
                a.nome,
                s.nome AS serie,
                t.nome AS turma,
                t.turno
            FROM 
                Alunos a
            JOIN 
                Matriculas m ON a.id = m.aluno_id
            JOIN 
                Turmas t ON m.turma_id = t.id
            JOIN 
                series s ON t.serie_id = s.id
            WHERE 
                m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
            AND 
                a.escola_id = 60
            AND
                m.status = 'Ativo'
            ORDER BY
                a.nome
        """
        cursor.execute(query, (ANO_LETIVO_ATUAL,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obter_responsaveis_do_aluno(aluno_id):
    """Obtém lista de responsáveis de um aluno específico.
    
    Args:
        aluno_id: ID do aluno
        
    Returns:
        list: Lista de dicionários com id, nome e telefone dos responsáveis
    """
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                r.id,
                r.nome,
                r.telefone,
                r.grau_parentesco
            FROM 
                Responsaveis r
            JOIN 
                ResponsaveisAlunos ra ON r.id = ra.responsavel_id  
            WHERE 
                ra.aluno_id = %s
            ORDER BY
                r.nome
        """
        cursor.execute(query, (aluno_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def gerar_cracha_individual(aluno_id, responsavel_id):
    """Gera um único crachá para um aluno e responsável específicos.
    
    Args:
        aluno_id: ID do aluno
        responsavel_id: ID do responsável
        
    Returns:
        str: Caminho do arquivo PDF gerado, ou None se houver erro
    """
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    try:
        # Buscar dados do aluno
        query_aluno = """
            SELECT 
                a.id,
                a.nome AS 'NOME DO ALUNO',
                s.nome AS 'NOME_SERIE',
                t.nome AS 'NOME_TURMA',
                f.nome AS 'NOME_PROFESSOR'
            FROM 
                Alunos a
            JOIN 
                Matriculas m ON a.id = m.aluno_id
            JOIN 
                Turmas t ON m.turma_id = t.id
            JOIN 
                series s ON t.serie_id = s.id
            LEFT JOIN
                Funcionarios f ON f.turma = t.id AND f.cargo = 'Professor@'
            WHERE 
                a.id = %s
                AND m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                AND m.status = 'Ativo'
            LIMIT 1
        """
        cursor.execute(query_aluno, (aluno_id, ANO_LETIVO_ATUAL))
        aluno = cursor.fetchone()
        
        if not aluno:
            print(f"Aluno {aluno_id} não encontrado ou não está ativo.")
            return None
        
        # Buscar dados do responsável
        query_resp = """
            SELECT 
                r.nome AS responsavel,
                r.telefone AS telefone
            FROM 
                Responsaveis r
            WHERE 
                r.id = %s
        """
        cursor.execute(query_resp, (responsavel_id,))
        responsavel = cursor.fetchone()
        
        if not responsavel:
            print(f"Responsável {responsavel_id} não encontrado.")
            return None
        
        # Caminhos
        caminho_template = PROJECT_ROOT / 'Modelos' / 'MODELO CRACHA.pdf'
        caminho_saida = PROJECT_ROOT / 'assets' / 'crachas'
        caminho_saida.mkdir(parents=True, exist_ok=True)
        
        # Verificar template
        if not caminho_template.exists():
            print(f"ERRO: Template não encontrado em {caminho_template}")
            print(f"Verifique se o arquivo existe na pasta 'Modelos'")
            return None
        
        # Gerar o crachá
        cracha_stream = criar_cracha(aluno, responsavel, str(caminho_template))
        
        # Sanitizar nome do arquivo
        nome_aluno_limpo = aluno['NOME DO ALUNO'].replace(' ', '_').replace('/', '-')
        nome_resp_limpo = responsavel['responsavel'].replace(' ', '_').replace('/', '-')
        nome_arquivo = f"Cracha_{nome_aluno_limpo}_{nome_resp_limpo}.pdf"
        caminho_completo = caminho_saida / nome_arquivo
        
        # Salvar o PDF
        with open(caminho_completo, 'wb') as f:
            f.write(cracha_stream.read())
        
        print(f"Crachá individual gerado: {caminho_completo}")
        return str(caminho_completo)
        
    finally:
        cursor.close()
        conn.close()


# Execução standalone (comentada para uso como módulo)
if __name__ == "__main__":
    # Exemplo de uso: Gerar crachás para todos os alunos e criar um arquivo único por série e turma
    gerar_crachas_para_todos_os_alunos()

