from src.core.conexao import conectar_bd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
import io
import os
from src.core.config_logs import get_logger

logger = get_logger(__name__)

# Conexão com o banco de dados
conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

# Consulta SQL para buscar os alunos do 9º Ano
query = """
    SELECT 
        a.nome AS nome_aluno, 
        a.sexo, 
        a.data_nascimento,
        s.nome AS nome_serie, 
        t.nome AS nome_turma, 
        t.turno, 
        m.status AS situacao,
        f.nome AS nome_professor,
        GROUP_CONCAT(DISTINCT r.telefone ORDER BY r.id SEPARATOR '/') AS telefones
    FROM 
        Alunos a
    JOIN 
        Matriculas m ON a.id = m.aluno_id
    JOIN 
        Turmas t ON m.turma_id = t.id
    JOIN 
        Serie s ON t.serie_id = s.id
    LEFT JOIN 
        ResponsaveisAlunos ra ON a.id = ra.aluno_id
    LEFT JOIN 
        Responsaveis r ON ra.responsavel_id = r.id
    LEFT JOIN
        Funcionarios f ON f.turma = t.id AND f.cargo = 'Professor@'
    WHERE 
        m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = 2024)
    AND 
        a.escola_id = 3
    AND 
        s.nome = '9º Ano'
    AND 
        m.status = 'Ativo' -- Filtro para status ativo
    GROUP BY 
        a.id, a.nome, a.sexo, a.data_nascimento, s.nome, t.nome, t.turno, m.status, f.nome
    ORDER BY
        a.nome ASC;
"""


# Executar a consulta
cursor.execute(query)
dados_alunos = cursor.fetchall()

# Verificar se existem alunos na lista
if not dados_alunos:
    logger.warning("Nenhum aluno encontrado para o 9º Ano.")
else:
    # Caminho para salvar os diplomas e o diploma original
    caminho_diplomas = r"C:\Users\Usuário\Desktop\TARCISIO_2024\Alzilene\Diploma_internet"
    diploma_original = "diploma original.pdf"  # Atualize com o caminho do diploma original
    os.makedirs(caminho_diplomas, exist_ok=True)

    # Função para criar o diploma
    def criar_diploma(aluno, caminho, pdf_base):
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
        fonte_tamanho = 24
        can.setFont("Helvetica-BoldOblique", fonte_tamanho)

        # Verificar largura do texto e ajustar a fonte se necessário
        largura_texto = can.stringWidth(aluno['nome_aluno'], "Helvetica-BoldOblique", fonte_tamanho)
        largura_maxima = largura_pagina - 50  # Deixa uma margem de 25 unidades de cada lado
        while largura_texto > largura_maxima and fonte_tamanho > 10:
            fonte_tamanho -= 1
            can.setFont("Helvetica-BoldOblique", fonte_tamanho)
            largura_texto = can.stringWidth(aluno['nome_aluno'], "Helvetica-BoldOblique", fonte_tamanho)

        # Centralizar o texto horizontalmente e posicioná-lo verticalmente
        x_pos = (largura_pagina - largura_texto) / 2
        y_pos = 285  # Ajuste conforme necessário

        # Adicionar o texto ao PDF
        can.drawString(x_pos, y_pos, aluno['nome_aluno'])  # Nome do aluno
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

    # Criar diplomas para todos os alunos
    for aluno in dados_alunos:
        criar_diploma(aluno, caminho_diplomas, diploma_original)
