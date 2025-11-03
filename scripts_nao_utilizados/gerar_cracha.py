from conexao import conectar_bd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
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
    pdf_base_reader = PdfReader(pdf_base)
    primeira_pagina = pdf_base_reader.pages[0]
    largura_pagina = float(primeira_pagina.mediabox.width)
    altura_pagina = float(primeira_pagina.mediabox.height)
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
    overlay = PdfReader(packet)
    writer = PdfWriter()
    for page in pdf_base_reader.pages:
        page.merge_page(overlay.pages[0])
        writer.add_page(page)

    # Prepare um BytesIO para retornar o PDF
    output_stream = io.BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    print(f"Cracha criado para {aluno['NOME DO ALUNO']} - {responsavel['responsavel']}.")
    return output_stream

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
                a.id, a.nome, a.sexo, a.data_nascimento, s.nome, t.nome, t.turno, m.status, f.nome, m.data_matricula, s.id, t.id  -- Inclui o ID da turma no GROUP BY
            ORDER BY
                s.nome, t.nome  -- Ordena por série e turma
        """
        cursor.execute(query_alunos)
        alunos = cursor.fetchall()
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

    # Caminho para o PDF base
    diretorio_atual = os.getcwd()
    caminho_cracha = os.path.join(diretorio_atual, "Cracha_Anos_Iniciais")
    os.makedirs(caminho_cracha, exist_ok=True)
    diploma_original = os.path.join(diretorio_atual, "Modelos", "MODELO CRACHA.pdf")

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
            nome_arquivo_unico = os.path.join(caminho_cracha, f"Crachas_{nome_serie}_{nome_turma}_unico.pdf")

            # Escreve todas as páginas no arquivo
            with open(nome_arquivo_unico, "wb") as output_pdf:
                writer.write(output_pdf)

            print(f"Crachás da {nome_serie} - Turma {nome_turma} gerados em {nome_arquivo_unico}")
        else:
            print(f"Nenhum crachá gerado para {nome_serie} - Turma {nome_turma}.")

# Execução standalone (comentada para uso como módulo)
if __name__ == "__main__":
    # Exemplo de uso: Gerar crachás para todos os alunos e criar um arquivo único por série e turma
    gerar_crachas_para_todos_os_alunos()
