import sys
import os

# Garantir que a raiz do repositório esteja no path para importar `src`
# Detectar raiz do repositório (procura por main.py)
script_dir = os.path.abspath(os.path.dirname(__file__))
if os.path.exists(os.path.join(script_dir, 'main.py')):
    repo_root = script_dir
else:
    repo_root = os.path.abspath(os.path.join(script_dir, '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.core.config_logs import get_logger
logger = get_logger(__name__)
from src.core.conexao import conectar_bd
import os
from PyPDF2 import PdfReader, PdfWriter
import io
from reportlab.pdfgen import canvas


def gerar_diplomas_5ano():
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT DISTINCT
            a.id AS id,
            a.nome AS nome_aluno
        FROM alunos a
        JOIN matriculas m ON a.id = m.aluno_id
        JOIN turmas t ON m.turma_id = t.id
        JOIN series s ON t.serie_id = s.id
        WHERE s.nome = '5º Ano' AND m.status = 'Ativo'
        ORDER BY a.nome ASC;
    """

    cursor.execute(query)
    alunos = cursor.fetchall()

    if not alunos:
        logger.info("Nenhum aluno ativo encontrado no 5º Ano.")
        cursor.close()
        conn.close()
        return

    diretorio_atual = os.getcwd()
    caminho_diplomas = os.path.join(diretorio_atual, "Diplomas_5ano")
    os.makedirs(caminho_diplomas, exist_ok=True)

    # Tenta localizar pelo helper; se falhar usa o caminho absoluto informado
    try:
        from src.services.utils.templates import find_template
        pdf_base = find_template("Diploma A4 NAO OFICIAL 2025 5 ANO.pdf")
    except Exception:
        pdf_base = r"C:\gestao\Modelos\Diploma A4 NAO OFICIAL 2025 5 ANO.pdf"

    data_fixa = "23/12/2025"

    def criar_diploma(aluno, pdf_base_path):
        """Cria as páginas do diploma para `aluno` e retorna lista de páginas."""
        pdf_base_reader = PdfReader(pdf_base_path)
        primeira_pagina = pdf_base_reader.pages[0]
        largura_pagina = float(primeira_pagina.mediabox.width)
        altura_pagina = float(primeira_pagina.mediabox.height)

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(largura_pagina, altura_pagina))

        # Fonte e posicionamento do nome (centralizado)
        fonte_tamanho = 24
        can.setFont("Helvetica-Bold", fonte_tamanho)
        largura_texto = can.stringWidth(aluno['nome_aluno'], "Helvetica-Bold", fonte_tamanho)
        largura_maxima = largura_pagina - 80
        while largura_texto > largura_maxima and fonte_tamanho > 10:
            fonte_tamanho -= 1
            can.setFont("Helvetica-Bold", fonte_tamanho)
            largura_texto = can.stringWidth(aluno['nome_aluno'], "Helvetica-Bold", fonte_tamanho)

        nome_x_offset = 10  # ajuste em pontos para mover o nome horizontalmente
        x_nome = (largura_pagina - largura_texto) / 2 + nome_x_offset
        # Ajuste: descer o nome do aluno (menor percentual => mais baixo na página)
        y_nome = altura_pagina * 0.5
        can.drawString(x_nome, y_nome, aluno['nome_aluno'])

        # Data fixa (posicionada abaixo do nome)
        fonte_data = 16
        can.setFont("Helvetica", fonte_data)
        largura_data = can.stringWidth(data_fixa, "Helvetica", fonte_data)
        # Deslocamento: mover a data um pouco para a direita e para baixo
        data_x_offset = -10  # ajuste em pontos para mover à direita
        data_y_offset = 195  # ajuste em pontos para descer a data
        x_data = (largura_pagina - largura_data) / 2 + data_x_offset
        y_data = y_nome - data_y_offset
        can.drawString(x_data, y_data, data_fixa)

        can.save()
        packet.seek(0)
        overlay = PdfReader(packet)

        # Mesclar a sobreposição nas páginas base e devolver as páginas resultantes
        result_pages = []
        for page in pdf_base_reader.pages:
            page.merge_page(overlay.pages[0])
            result_pages.append(page)

        return result_pages

    combined_writer = PdfWriter()
    for aluno in alunos:
        try:
            pages = criar_diploma(aluno, pdf_base)
            for p in pages:
                combined_writer.add_page(p)
            logger.info(f"Adicionado diploma de {aluno['nome_aluno']} ao arquivo combinado.")
        except Exception as e:
            logger.exception(f"Erro ao criar diploma para {aluno.get('nome_aluno')}: {e}")

    nome_combinado = os.path.join(caminho_diplomas, "Diplomas_5ano_Todos.pdf")
    with open(nome_combinado, "wb") as out_comb:
        combined_writer.write(out_comb)

    logger.info(f"Arquivo combinado gerado em {nome_combinado}")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    gerar_diplomas_5ano()
