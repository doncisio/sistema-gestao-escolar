from conexao import conectar_bd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
import io
import os
from datetime import datetime

# Conexão com o banco de dados
conn = conectar_bd()

def obter_todos_alunos():
    """Obtém todos os alunos que atendem aos critérios especificados e inclui informações da série e turma."""
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
                t.id AS 'ID_TURMA'
            FROM 
                Alunos a
            JOIN 
                Matriculas m ON a.id = m.aluno_id
            JOIN 
                Turmas t ON m.turma_id = t.id
            JOIN 
                Serie s ON t.serie_id = s.id
            LEFT JOIN
                Funcionarios f ON f.turma = t.id AND f.cargo = 'Professor@'
            WHERE 
                m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = 2025)
            AND 
                a.escola_id = 60
            AND
                m.status = 'Ativo'
            AND s.id <=7
            GROUP BY 
                a.id, a.nome, a.sexo, a.data_nascimento, s.nome, t.nome, t.turno, m.status, f.nome, m.data_matricula, s.id, t.id
            ORDER BY
                s.nome, t.nome
        """
        cursor.execute(query_alunos)
        alunos = cursor.fetchall()
        return alunos
    finally:
        cursor.close()

def criar_nis(aluno, responsavel, pdf_base):
    """Cria um NIS em PDF para um aluno e seu responsável, retornando um objeto BytesIO."""
    try:
        pdf_base_reader = PdfReader(pdf_base)
        primeira_pagina = pdf_base_reader.pages[0]
        largura_pagina = float(primeira_pagina.mediabox.width)
        altura_pagina = float(primeira_pagina.mediabox.height)
        
        print(f"Tamanho da página: {largura_pagina}x{altura_pagina}")
        
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(largura_pagina, altura_pagina))
        
        # Configurações de fonte
        fonte_tamanho = 10
        can.setFont("Helvetica-Bold", fonte_tamanho)
        
        # Posições para os textos (ajuste conforme necessário)
        # Coordenadas são em pontos (1 ponto = 1/72 polegada)
        # x aumenta da esquerda para a direita
        # y aumenta de baixo para cima
        
        # Nome do aluno
        x_pos_nome = 100
        y_pos_nome = altura_pagina - 30  # 200 pontos do topo
        
        # Nome do responsável
        x_pos_responsavel = 100
        y_pos_responsavel = altura_pagina - 250  # 250 pontos do topo
        
        # Desenha os textos
        print(f"Desenhando nome do aluno em ({x_pos_nome}, {y_pos_nome}): {aluno['NOME DO ALUNO']}")
        print(f"Desenhando nome do responsável em ({x_pos_responsavel}, {y_pos_responsavel}): {responsavel['responsavel']}")
        
        can.drawString(x_pos_nome, y_pos_nome, aluno['NOME DO ALUNO'])
        can.drawString(x_pos_responsavel, y_pos_responsavel, responsavel['responsavel'])
        
        can.save()
        packet.seek(0)
        overlay = PdfReader(packet)
        writer = PdfWriter()
        for page in pdf_base_reader.pages:
            page.merge_page(overlay.pages[0])
            writer.add_page(page)

        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        print(f"NIS criado para {aluno['NOME DO ALUNO']} - {responsavel['responsavel']}.")
        return output_stream
    except Exception as e:
        print(f"Erro ao criar NIS: {str(e)}")
        raise

def gerar_nis_responsaveis(aluno, pdf_base):
    """Gera NIS para os responsáveis de um aluno, retornando uma lista de objetos BytesIO."""
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
            return []

        nis_streams = []
        for responsavel in responsaveis:
            nis_stream = criar_nis(aluno, responsavel, pdf_base)
            nis_streams.append(nis_stream)

        return nis_streams

    finally:
        cursor.close()

def gerar_nis_para_todos_os_alunos():
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

    # Caminho para o PDF base
    diretorio_atual = os.getcwd()
    caminho_nis = os.path.join(diretorio_atual, "NIS")
    os.makedirs(caminho_nis, exist_ok=True)
    nis_original = "NIS.pdf"

    # Gerar NIS para cada grupo
    for serie_turma, alunos_grupo in grupos.items():
        nome_serie, nome_turma = serie_turma
        nis_streams_grupo = []

        for aluno in alunos_grupo:
            nis_streams_aluno = gerar_nis_responsaveis(aluno, nis_original)
            if nis_streams_aluno:
                nis_streams_grupo.extend(nis_streams_aluno)

        # Criar um único PDF com todos os NIS do grupo
        if nis_streams_grupo:
            writer = PdfWriter()
            for nis_stream in nis_streams_grupo:
                nis_reader = PdfReader(nis_stream)
                for page in nis_reader.pages:
                    writer.add_page(page)

            # Define o nome do arquivo
            nome_arquivo_unico = os.path.join(caminho_nis, f"NIS_{nome_serie}_{nome_turma}_unico.pdf")

            # Escreve todas as páginas no arquivo
            with open(nome_arquivo_unico, "wb") as output_pdf:
                writer.write(output_pdf)

            print(f"NIS da {nome_serie} - Turma {nome_turma} gerados em {nome_arquivo_unico}")
        else:
            print(f"Nenhum NIS gerado para {nome_serie} - Turma {nome_turma}.")

def gerar_nis_para_um_aluno(id_aluno):
    """Gera NIS para um aluno específico, retornando uma lista de objetos BytesIO."""
    cursor = conn.cursor(dictionary=True)
    try:
        query_aluno = """
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
                t.id AS 'ID_TURMA'
            FROM 
                Alunos a
            JOIN 
                Matriculas m ON a.id = m.aluno_id
            JOIN 
                Turmas t ON m.turma_id = t.id
            JOIN 
                Serie s ON t.serie_id = s.id
            LEFT JOIN
                Funcionarios f ON f.turma = t.id AND f.cargo = 'Professor@'
            WHERE 
                a.id = %s
            AND 
                m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = 2025)
            AND 
                a.escola_id = 60
            AND
                m.status = 'Ativo'
            AND s.id <=7
        """
        cursor.execute(query_aluno, (id_aluno,))
        aluno = cursor.fetchone()

        if not aluno:
            print(f"Nenhum aluno encontrado com o ID {id_aluno}.")
            return

        # Caminho para o PDF base
        diretorio_atual = os.getcwd()
        caminho_nis = os.path.join(diretorio_atual, "NIS")
        os.makedirs(caminho_nis, exist_ok=True)
        nis_original = "NIS.pdf"

        # Gerar NIS para o aluno
        nis_streams = gerar_nis_responsaveis(aluno, nis_original)

        if nis_streams:
            writer = PdfWriter()
            for nis_stream in nis_streams:
                nis_reader = PdfReader(nis_stream)
                for page in nis_reader.pages:
                    writer.add_page(page)

            # Define o nome do arquivo
            nome_arquivo = os.path.join(caminho_nis, f"NIS_{aluno['NOME DO ALUNO']}_teste.pdf")

            # Escreve todas as páginas no arquivo
            with open(nome_arquivo, "wb") as output_pdf:
                writer.write(output_pdf)

            print(f"NIS do aluno {aluno['NOME DO ALUNO']} gerado em {nome_arquivo}")
        else:
            print(f"Nenhum NIS gerado para o aluno {aluno['NOME DO ALUNO']}.")

    finally:
        cursor.close()

# Para testar com um único aluno, descomente a linha abaixo e coloque o ID do aluno desejado
gerar_nis_para_um_aluno(492)  # Substitua 456 pelo ID do aluno que deseja testar

# Para gerar para todos os alunos, descomente a linha abaixo
# gerar_nis_para_todos_os_alunos()

# Fechar a conexão com o banco de dados
conn.close() 