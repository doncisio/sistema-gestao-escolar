from config_logs import get_logger
logger = get_logger(__name__)
from conexao import conectar_bd
import os
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
import io
from reportlab.pdfgen import canvas

def diploma(aluno_id):
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    query = """
            SELECT DISTINCT
                a.id AS id,
                a.nome AS nome_aluno, 
                a.sexo, 
                a.data_nascimento AS nascimento_aluno,
                a.local_nascimento AS local_aluno,
                a.UF_nascimento AS uf_aluno,
                e.nome AS nome_escola,
                al.ano_letivo AS ano_letivo  -- Obtendo o ano letivo da tabela anosletivos
            FROM alunos a
            JOIN historico_escolar h ON a.id = h.aluno_id
            LEFT JOIN Escolas e ON a.escola_id = e.id
            LEFT JOIN anosletivos al ON h.ano_letivo_id = al.id  -- JOIN com anosletivos
            WHERE h.serie_id = 11 AND a.id = %s
            ORDER BY a.nome ASC;
        """
    cursor.execute(query, (aluno_id,))
    aluno = cursor.fetchone()

    meses = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro"
    }
    # Verificar se existem alunos na lista
    if not aluno:
        logger.info("O aluno não cursou o 9º Ano na escola.")
        cursor.close()
        conn.close()
        return
    else:
        # Obter o diretório atual do script
        diretorio_atual = os.getcwd()

        # Criar o caminho para a pasta Diploma_9º_ANO dentro do diretório atual
        caminho_diplomas = os.path.join(diretorio_atual, "Diplomas_2025")

        diploma_original = "MODELO CERTIFICADO 2024.pdf"  # Atualize com o caminho do diploma original
        os.makedirs(caminho_diplomas, exist_ok=True)

        # Função para criar o diploma
        def criar_diploma(aluno, caminho, pdf_base):

            # Consulta SQL para obter os nomes dos responsáveis
            query_responsaveis = """
                SELECT 
                    r.nome AS responsavel
                FROM 
                    Responsaveis r
                JOIN 
                    ResponsaveisAlunos ra ON r.id = ra.responsavel_id  
                WHERE 
                    ra.aluno_id = %s;
            """

            cursor.execute(query_responsaveis, (aluno['id'],))
            responsaveis = cursor.fetchall()

            # Verifica se existem responsáveis e atribui valores
            responsavel1 = responsaveis[0]['responsavel'] if len(responsaveis) > 0 else None
            responsavel2 = responsaveis[1]['responsavel'] if len(responsaveis) > 1 else None

            data_nascimento = aluno['nascimento_aluno'] 

            # Extrair dia, mês e ano
            dia = data_nascimento.day
            mes = meses[data_nascimento.month]
            ano = data_nascimento.year

            #  Extrair dia, mês e ano atual

            data_atual = datetime.now()
            dia_atual = data_atual.day
            mes_atual = meses[data_atual.month]
            ano_atual = data_atual.year

            # Nome do arquivo final
            nome_arquivo = os.path.join(caminho, f"{aluno['nome_aluno']}_diploma.pdf")

            # Ler o diploma original para obter as dimensões da página
            pdf_base_reader = PdfReader(pdf_base)
            primeira_pagina = pdf_base_reader.pages[0]
            # Conversão para float ao calcular dimensões da página
            largura_pagina = float(primeira_pagina.mediabox.width)  # Converte para float
            altura_pagina = float(primeira_pagina.mediabox.height)  # Converte para float

            # Criar sobreposição com o texto do diploma
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(largura_pagina, altura_pagina))

            # Configurar fonte inicial
            fonte_tamanho = 20
            can.setFont("Helvetica-BoldOblique", fonte_tamanho)

            # Verificar largura do texto e ajustar a fonte se necessário
            largura_texto = can.stringWidth(aluno['nome_aluno'], "Helvetica-BoldOblique", fonte_tamanho)
            largura_maxima = largura_pagina - 50  # Deixa uma margem de 25 unidades de cada lado
            while largura_texto > largura_maxima and fonte_tamanho > 10:
                fonte_tamanho -= 1
                can.setFont("Helvetica-BoldOblique", fonte_tamanho)
                largura_texto = can.stringWidth(aluno['nome_aluno'], "Helvetica-BoldOblique", fonte_tamanho)

            # Centralizar o texto horizontalmente e posicioná-lo verticalmente
            x_pos1 = (largura_pagina - largura_texto) / 2
            y_pos1 = 540  # Ajuste conforme necessário

            x_pos2 = (largura_pagina - largura_texto) / 2
            y_pos2 = 495  # Ajuste conforme necessário

            x_pos3 = (largura_pagina - largura_texto) / 2
            y_pos3 = 445  # Ajuste conforme necessário

            x_pos4 = 275
            x_pos5 = x_pos4 + 100
            x_pos6 = 570
            x_pos7 = 820
            x_pos8 = 165
            x_pos9 = 400
            x_pos10 = 1100
            x_pos11 = 855
            x_pos12 = 930
            x_pos13 = 1100
            y_pos4 = 395  # Ajuste conforme necessário
            y_pos5 = 347  # Ajuste conforme necessário
            y_pos6 = 254  # Ajuste conforme necessário

            # Adicionar o texto ao PDF
            can.drawString(x_pos1, y_pos1, aluno['nome_aluno'])  # Nome do aluno
            can.drawString(x_pos2, y_pos2, responsavel1)  # Responsável 1
            # Adicionar verificação antes de desenhar o responsável 2
            if responsavel2 is not None:
                can.drawString(x_pos3, y_pos3, responsavel2)  # Responsável 2

            can.drawString(x_pos4, y_pos4, str(dia))
            can.drawString(x_pos5, y_pos4, mes)
            can.drawString(x_pos6, y_pos4, str(ano))
            can.drawString(x_pos7, y_pos4, aluno['local_aluno'] if aluno['local_aluno'] else "Local não informado")
            can.drawString(x_pos8, y_pos5, aluno['uf_aluno'] if aluno['uf_aluno'] else "UF não informada")
            can.drawString(x_pos9, y_pos5, aluno['nome_escola'] if aluno['nome_escola'] else "Escola não informado")
            can.drawString(x_pos10, y_pos5, str(aluno['ano_letivo']))
            can.drawString(x_pos11, y_pos6, str(dia_atual))
            can.drawString(x_pos12, y_pos6, mes_atual)
            can.drawString(x_pos13, y_pos6, str(ano_atual))
            can.save()

            # Mover para o início
            packet.seek(0)
            overlay = PdfReader(packet)

            # Mesclar sobreposição com o PDF original
            writer = PdfWriter()
            for page in pdf_base_reader.pages:
                page.merge_page(overlay.pages[0])
                writer.add_page(page)

            # Salvar o diploma gerado
            with open(nome_arquivo, "wb") as output_pdf:
                writer.write(output_pdf)

            logger.info(f"Diploma criado para {aluno['nome_aluno']} em {nome_arquivo}.")
            cursor.close()
            conn.close()
    
    criar_diploma(aluno, caminho_diplomas, diploma_original) # Atualize com o caminho do diploma original


# diploma(2624)  # Atualize com o ID do aluno