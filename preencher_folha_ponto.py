from config_logs import get_logger
logger = get_logger(__name__)
from conexao import conectar_bd
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
from utils.dates import formatar_data, nome_mes_pt
import calendar
import io
import os
import re
import unicodedata
from typing import Any, cast




def formatar_telefone(telefone):
    if not telefone:
        return ""
    telefone = str(telefone)
    telefone = telefone.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
    if len(telefone) < 10:
        return telefone
    if len(telefone) == 10:
        return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
    if len(telefone) >= 11:
        return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:11]}"
    return telefone


def consultar_funcionarios(conn: Any):
    cursor = cast(Any, conn).cursor(dictionary=True)
    try:
        query = (
            """
            SELECT 
                f.nome AS nome,
                f.matricula AS matricula,
                f.data_admissao AS data_admissao,
                f.funcao AS funcao,
                f.carga_horaria AS carga_horaria,
                f.telefone AS telefone,
                f.email AS email,
                e.nome AS nome_escola
            FROM Funcionarios f
            JOIN Escolas e ON e.id = f.escola_id
            WHERE f.escola_id = %s
            ORDER BY f.nome
            """
        )
        cursor.execute(query, (60,))
        return cursor.fetchall()
    finally:
        cursor.close()


def desenhar_funcionario_no_canvas(c, dados, largura_pagina, altura_pagina, mes_referencia: int, ano_referencia: int):
    def limpar_str(valor):
        if valor is None:
            return ""
        try:
            s = str(valor).strip()
        except Exception:
            return ""
        return "" if s.lower() == "none" else s

    def abreviar_nome_escola(nome: str) -> str:
        if not nome:
            return ""
        # Substitui qualquer variação de "Escola Municipal" por "EM" (case-insensitive)
        return re.sub(r"escola municipal", "EM", nome, flags=re.IGNORECASE)

    def normalizar_funcao(funcao: str) -> str:
        if not funcao:
            return ""
        f = funcao.strip()

        def sem_acentos(txt: str) -> str:
            return "".join(ch for ch in unicodedata.normalize("NFD", txt) if unicodedata.category(ch) != "Mn")

        chave = sem_acentos(f).casefold()

        # Mapeamentos desejados
        if chave == "especialista (coordenadora)":
            return "Coord. Pedagógica"
        if chave == "coordenadora pedagogica":
            return "Coord. Pedagógica"
        if chave == "tecnico em administracao escolar":
            return "Tec. Adm. Escolar"
        if chave in ("auxiliar servicos gerais", "auxiliar de servicos gerais"):
            return "Aux. Serv. Gerais"

        return f

    # Ajuste estas coordenadas conforme o layout do seu arquivo "folha de ponto.pdf"
    # Origem (0,0) fica no canto inferior esquerdo da página
    c.setFont("Helvetica", 10)

    posicoes = {
        "nome": (90, altura_pagina - 210),
        "matricula": (95, altura_pagina - 230),
        "data_admissao": (400, altura_pagina - 230),
        "funcao": (85, altura_pagina - 245),
        "carga_horaria": (300, altura_pagina - 245),
        "nome_escola": (393, altura_pagina - 245),
        "telefone": (90, altura_pagina - 263),
        "email": (300, altura_pagina - 263),
        "periodo_mes": (230, altura_pagina - 97),
    }

    c.drawString(*posicoes["nome"], limpar_str(dados.get('nome')))
    c.drawString(*posicoes["matricula"], limpar_str(dados.get('matricula')))
    c.drawString(*posicoes["data_admissao"], limpar_str(formatar_data(dados.get('data_admissao'))))
    c.drawString(*posicoes["funcao"], limpar_str(normalizar_funcao(dados.get('funcao'))))
    c.drawString(*posicoes["carga_horaria"], limpar_str(dados.get('carga_horaria')))
    c.drawString(*posicoes["nome_escola"], limpar_str(abreviar_nome_escola(dados.get('nome_escola'))))

    # Período do mês de referência (1º dia até o último dia)
    ultimo_dia = calendar.monthrange(ano_referencia, mes_referencia)[1]
    periodo_str = f"1 a {ultimo_dia} de {nome_mes_pt(mes_referencia)} de {ano_referencia}"
    if "periodo_mes" in posicoes:
        c.drawString(*posicoes["periodo_mes"], periodo_str)
    c.drawString(*posicoes["telefone"], limpar_str(formatar_telefone(dados.get('telefone'))))
    c.drawString(*posicoes["email"], limpar_str(dados.get('email')))


def gerar_folhas_de_ponto(template_pdf: str, saida_pdf: str, mes_referencia: int | None = None, ano_referencia: int | None = None):
    if not os.path.isfile(template_pdf):
        raise FileNotFoundError(f"Arquivo base não encontrado: {template_pdf}")

    conn: Any = conectar_bd()
    try:
        funcionarios = consultar_funcionarios(conn)
        if not funcionarios:
            logger.info("Nenhum funcionário encontrado para escola_id=60.")
            return

        hoje = datetime.today()
        if mes_referencia is None:
            mes_referencia = hoje.month
        if ano_referencia is None:
            ano_referencia = hoje.year

        base_reader = PdfReader(template_pdf)
        primeira_pagina = base_reader.pages[0]
        largura = float(primeira_pagina.mediabox.width)
        altura = float(primeira_pagina.mediabox.height)

        writer = PdfWriter()

        for func in funcionarios:
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(largura, altura))
            desenhar_funcionario_no_canvas(can, func, largura, altura, mes_referencia, ano_referencia)
            can.save()
            packet.seek(0)

            overlay_reader = PdfReader(packet)
            # Carrega uma nova página base do template para cada funcionário (evita mutação)
            pagina_base = PdfReader(template_pdf).pages[0]
            pagina_base.merge_page(overlay_reader.pages[0])
            writer.add_page(pagina_base)

        os.makedirs(os.path.dirname(saida_pdf), exist_ok=True)
        with open(saida_pdf, "wb") as f:
            writer.write(f)

        logger.info(f"Folhas de ponto geradas em: {saida_pdf}")
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


# `formatar_data` e `nome_mes_pt` importados de `utils.dates`


def localizar_template_folha() -> str:
    """Tenta localizar o arquivo base "folha de ponto.pdf" em locais comuns.

    Ordem de busca:
      1) mesma pasta deste script
      2) pasta atual de execução (os.getcwd())
    """
    nome_arquivo = "folha de ponto.pdf"
    candidatos = [
        os.path.join(os.path.dirname(__file__), nome_arquivo),
        os.path.join(os.getcwd(), nome_arquivo),
    ]

    for caminho in candidatos:
        if os.path.isfile(caminho):
            return caminho

    raise FileNotFoundError(
        f"Arquivo base não encontrado. Procurado em: {', '.join(candidatos)}"
    )


if __name__ == "__main__":
    base = localizar_template_folha()

    # Diretório de saída solicitado
    dir_saida = r"G:\\Meu Drive\\NADIR_2025\\Ficha de Ponto 2025"
    os.makedirs(dir_saida, exist_ok=True)

    hoje = datetime.today()
    ano_alvo = 2025  # conforme solicitado no nome do arquivo

    # Mês atual + próximos meses do ano atual
    meses_restantes = list(range(hoje.month, 13))

    for mes in meses_restantes:
        nome_mes = nome_mes_pt(mes)
        arquivo_saida = os.path.join(dir_saida, f"Folhas_de_Ponto_{nome_mes}_{ano_alvo}.pdf")
        gerar_folhas_de_ponto(base, arquivo_saida, mes_referencia=mes, ano_referencia=ano_alvo)

