from src.core.conexao import conectar_bd
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
import io
import os
import calendar
import sys
import re
import unicodedata
from typing import List
from src.utils.dates import nome_mes_pt
from src.core.config_logs import get_logger

logger = get_logger(__name__)


def listar_colunas_funcionarios(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW COLUMNS FROM Funcionarios")
        cols = {row[0] for row in cursor.fetchall()}
        return cols
    finally:
        cursor.close()


def consultar_profissionais(conn, mes: int, ano: int):
    colunas = listar_colunas_funcionarios(conn)
    campos = []

    def add_if(col, alias):
        if col in colunas:
            campos.append(f"{col} AS {alias}")

    add_if("id", "id")
    add_if("matricula", "matricula")
    add_if("nome", "nome")
    add_if("cargo", "funcao")
    add_if("carga_horaria", "carga_horaria")
    # Situação funcional priorizando a coluna 'vinculo'
    if "vinculo" in colunas:
        campos.append("vinculo AS situacao_funcional")
    elif "situacao_funcional" in colunas:
        campos.append("situacao_funcional AS situacao_funcional")
    elif "situacao" in colunas:
        campos.append("situacao AS situacao_funcional")
    elif "status" in colunas:
        campos.append("status AS situacao_funcional")
    # Turno se existir
    add_if("turno", "turno")

    select_campos = ", ".join(campos) if campos else "id, nome"

    # Carregar profissionais e faltas do mês/ano
    cursor = conn.cursor(dictionary=True)
    try:
        query = f"""
            SELECT {select_campos}
            FROM Funcionarios
            WHERE escola_id = %s
            ORDER BY nome
        """
        cursor.execute(query, (60,))
        resultados = cursor.fetchall()

        # Buscar registros de faltas para o mês/ano
        faltas_cursor = conn.cursor(dictionary=True)
        try:
            faltas_cursor.execute(
                """
                SELECT funcionario_id, p, f, fj, observacao
                FROM funcionario_faltas_mensal
                WHERE ano = %s AND mes = %s
                """,
                (ano, mes),
            )
            faltas_map = {}
            for row in faltas_cursor.fetchall():
                faltas_map[row["funcionario_id"]] = {
                    "p": row.get("p", ""),
                    "f": row.get("f", ""),
                    "fj": row.get("fj", ""),
                    "observacao": row.get("observacao", ""),
                }
        finally:
            faltas_cursor.close()

        # Normaliza chaves esperadas e aplica faltas
        # Total de dias do mês selecionado (1..ultimo-dia)
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        linhas = []
        for r in resultados:
            funcionario_id = r.get("id") or r.get("funcionario_id")
            faltas = faltas_map.get(funcionario_id, {})
            linhas.append({
                "matricula": r.get("matricula", ""),
                "nome": r.get("nome", ""),
                "situacao_funcional": r.get("situacao_funcional", ""),
                "funcao": r.get("funcao", r.get("cargo", "")),
                "carga_horaria": r.get("carga_horaria", r.get("ch", "")),
                "turno": r.get("turno", ""),
                # P padrão = total de dias do mês, se não houver valor salvo
                "p": faltas.get("p") if faltas.get("p") not in (None, "") else ultimo_dia,
                "f": faltas.get("f", ""),
                "fj": faltas.get("fj", ""),
                "observacao": faltas.get("observacao", ""),
            })
        return linhas
    finally:
        cursor.close()


def consultar_escola(conn, escola_id: int = 60):
    colunas = listar_colunas_funcionarios(conn)  # reaproveita conexão; vamos inspecionar tabela Escolas diretamente
    cursor = conn.cursor()
    try:
        # Descobrir colunas da tabela Escolas
        cursor.execute("SHOW COLUMNS FROM escolas")
        cols_escola = {row[0] for row in cursor.fetchall()}

        campos = []
        if "id" in cols_escola:
            campos.append("id")
        if "nome" in cols_escola:
            campos.append("nome")
        if "endereco" in cols_escola:
            campos.append("endereco")
        if "inep" in cols_escola:
            campos.append("inep")
        if "cnpj" in cols_escola:
            campos.append("cnpj")
        if "municipio" in cols_escola:
            campos.append("municipio")

        select_campos = ", ".join(campos) if campos else "id, nome"
        cursor.close()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT {select_campos} FROM escolas WHERE id = %s", (escola_id,))
        row = cursor.fetchone()
        return row or {}
    finally:
        cursor.close()


def desenhar_tabela_profissionais(can, profissionais, largura, altura, offset_y_inicio):
    def mostrar(valor: str) -> str:
        if valor is None:
            return "--"
        txt = str(valor).strip()
        return txt if txt else "--"
    def normalizar_funcao(funcao: str) -> str:
        if not funcao:
            return ""
        texto = funcao.strip()

        def sem_acentos(txt: str) -> str:
            return "".join(ch for ch in unicodedata.normalize("NFD", txt) if unicodedata.category(ch) != "Mn")

        chave = sem_acentos(texto).casefold()
        if chave == "especialista (coordenadora)":
            return "Coord. Pedagógica"
        if chave == "tecnico em administracao escolar":
            return "Tec. Adm. Escolar"
        if chave in ("auxiliar servicos gerais", "auxiliar de servicos gerais"):
            return "Aux. Serv. Gerais"
        return texto

    def normalizar_turno(turno: str) -> str:
        if not turno:
            return ""
        texto = turno.strip()

        def sem_acentos(txt: str) -> str:
            return "".join(ch for ch in unicodedata.normalize("NFD", txt) if unicodedata.category(ch) != "Mn")

        chave = sem_acentos(texto).casefold()
        # Combinações
        if ("matutino" in chave or "manha" in chave) and ("vespertino" in chave or "tarde" in chave):
            return "MAT/VESP"

        mapas = {
            "matutino": "MAT.",
            "manha": "MAT.",
            "vespertino": "VESP.",
            "tarde": "VESP.",
            "noturno": "Not.",
            "noite": "Not.",
            "integral": "Int.",
            "diurno": "Diur.",
            "intermediario": "Interm.",
        }
        return mapas.get(chave, texto)

    def normalizar_ch(valor) -> str:
        txt = str(valor).strip()
        if not txt:
            return ""
        txt = txt.replace(" ", "")
        if txt.lower().endswith("h"):
            return txt[:-1] + "h"
        # se for apenas números, acrescenta 'h'
        if txt.isdigit():
            return txt + "h"
        return txt

    margem_esq = 40
    margem_dir = 40
    fim_x = largura - margem_dir
    header_altura = 18
    row_altura = 16

    # Títulos das colunas
    titulos = [
        "Nº",
        "Matrícula",
        "Nome",
        "Situação Funcional",
        "Função",
        "CH",
        "Turno",
        "P",
        "F",
        "FJ",
        "Observação",
    ]

    # Coleta de valores normalizados para cálculo de largura
    linhas_valores = []
    for i, (idx, prof) in enumerate(profissionais):
        valores = [
            mostrar(idx),
            mostrar(prof.get("matricula", "")),
            mostrar(prof.get("nome", "")),
            mostrar(prof.get("situacao_funcional", "")),
            mostrar(normalizar_funcao(prof.get("funcao", ""))),
            mostrar(normalizar_ch(prof.get("carga_horaria", ""))),
            mostrar(normalizar_turno(prof.get("turno", ""))),
            mostrar(prof.get("p", "")),
            mostrar(prof.get("f", "")),
            mostrar(prof.get("fj", "")),
            mostrar(prof.get("observacao", "")),
        ]
        linhas_valores.append(valores)

    # Cálculo de larguras desejadas por coluna (baseado em cabeçalho e conteúdo)
    can.setFont("Helvetica-Bold", 10)
    header_widths = [can.stringWidth(t, "Helvetica-Bold", 10) for t in titulos]
    can.setFont("Helvetica", 9)
    data_widths = [0] * len(titulos)
    for valores in linhas_valores:
        for c, texto in enumerate(valores):
            w = can.stringWidth(texto, "Helvetica", 9)
            if w > data_widths[c]:
                data_widths[c] = w

    padding = 8  # 4 px de cada lado
    desired_widths = [max(h, d) + padding for h, d in zip(header_widths, data_widths)]

    # Larguras mínimas por coluna para legibilidade
    # Mínimos modestos apenas para garantir legibilidade (todas as colunas são dinâmicas)
    min_widths = [
        24,   # Nº
        60,   # Matrícula
        100,  # Nome
        100,  # Situação Funcional
        100,  # Função
        30,   # CH
        50,   # Turno
        20,   # P
        20,   # F
        24,   # FJ
        80,   # Observação
    ]

    # Largura disponível para a tabela
    available_width = fim_x - margem_esq

    # Aplica mínimos
    desired_widths = [max(dw, mw) for dw, mw in zip(desired_widths, min_widths)]
    total_desired = sum(desired_widths)

    # Se exceder a largura disponível, escala proporcionalmente mantendo mínimos
    if total_desired > 0:
        # Escala proporcional para caber na largura disponível
        scale = min(1.0, available_width / total_desired)
        widths = [max(mw, dw * scale) for dw, mw in zip(desired_widths, min_widths)]
        current_total = sum(widths)
        if current_total < available_width:
            # Distribui o espaço restante proporcionalmente às larguras atuais (sem favorecer nenhuma coluna)
            remaining = available_width - current_total
            weight_sum = sum(widths) or 1.0
            widths = [w + remaining * (w / weight_sum) for w in widths]
        elif current_total > available_width:
            # Pequeno ajuste final proporcional para fechar exatamente
            factor = available_width / current_total
            widths = [w * factor for w in widths]
    else:
        widths = [available_width / len(titulos)] * len(titulos)

    # Constrói as posições X cumulativas (todas as colunas dinâmicas)
    # Garantir que `xs` seja uma lista de floats para evitar misturar int/float
    xs: List[float] = [float(margem_esq)]
    for w in widths:
        xs.append(xs[-1] + float(w))

    # Colunas como pares (titulo, x_left) para compatibilidade com o restante do desenho
    colunas = [(titulos[i], xs[i]) for i in range(len(titulos))]

    # Funções auxiliares de desenho alinhado e truncado
    def draw_in_cell(texto: str, x_left: float, x_right: float, baseline_y: float, align: str = "left", font_name: str = "Helvetica", font_size: int = 9):
        can.setFont(font_name, font_size)
        txt = str(texto) if texto is not None else ""
        max_width = max(0, x_right - x_left - 4)  # 2px padding de cada lado
        # truncar com reticências se necessário
        ellipsis = "…"
        while can.stringWidth(txt, font_name, font_size) > max_width and len(txt) > 1:
            txt = txt[:-1]
        if can.stringWidth(txt, font_name, font_size) > max_width and max_width >= can.stringWidth(ellipsis, font_name, font_size):
            txt = ellipsis
        # Centralizar placeholders "--" independentemente do alinhamento solicitado
        _align = "center" if txt == "--" else align
        # calcular x
        if _align == "center":
            x = x_left + (x_right - x_left) / 2 - can.stringWidth(txt, font_name, font_size) / 2
        elif _align == "right":
            x = x_right - 2 - can.stringWidth(txt, font_name, font_size)
        else:
            x = x_left + 2
        can.drawString(x, baseline_y, txt)

    total_rows = max(1, len(profissionais))
    top_y = offset_y_inicio
    bottom_y = offset_y_inicio - (header_altura + total_rows * row_altura)

    # Cabeçalho com fundo escuro (desenhado ANTES da grade)
    can.setFillColorRGB(0.2, 0.4, 0.7)
    can.rect(margem_esq, top_y - header_altura, fim_x - margem_esq, header_altura, fill=1, stroke=0)
    can.setFillColorRGB(0, 0, 0)

    # Preenche fundos alternados das linhas (desenhado ANTES da grade, para a grade ficar por cima)
    for i in range(total_rows):
        if i % 2 == 0:
            can.setFillColorRGB(0.96, 0.96, 0.96)
            y_top = top_y - header_altura - i * row_altura
            can.rect(margem_esq, y_top - row_altura, fim_x - margem_esq, row_altura, fill=1, stroke=0)
    can.setFillColorRGB(0, 0, 0)

    # Linhas e colunas (grid) - borda externa + linhas internas (desenhadas POR CIMA dos fundos)
    can.setLineWidth(1.0)
    # Borda externa completa
    can.rect(margem_esq, bottom_y, fim_x - margem_esq, (top_y - bottom_y), fill=0, stroke=1)
    # Linhas verticais das colunas (toda a altura do grid)
    for x in xs:
        can.line(x, bottom_y, x, top_y)
    # Linhas horizontais: topo do cabeçalho, base do cabeçalho e cada linha de dados
    # Topo já coberto pela borda externa; base do cabeçalho:
    can.line(margem_esq, top_y - header_altura, fim_x, top_y - header_altura)
    # Linhas de cada linha de dados
    y_line = top_y - header_altura
    for _ in range(total_rows):
        y_line -= row_altura
        can.line(margem_esq, y_line, fim_x, y_line)

    # Desenha títulos do cabeçalho por cima do fundo
    can.setFillColorRGB(1, 1, 1)
    for i, (titulo, x) in enumerate(colunas):
        x_left = xs[i]
        x_right = xs[i + 1]
        draw_in_cell(titulo, x_left, x_right, top_y - header_altura + 4, align="center", font_name="Helvetica-Bold", font_size=10)
    can.setFillColorRGB(0, 0, 0)

    # Linhas de dados
    y = top_y - header_altura
    for i, (idx, prof) in enumerate(profissionais):
        # Alinhamentos por coluna
        valores = [
            (mostrar(idx), "center"),
            (mostrar(prof.get("matricula", "")), "center"),
            (mostrar(prof.get("nome", "")), "left"),
            (mostrar(prof.get("situacao_funcional", "")), "left"),
            (mostrar(normalizar_funcao(prof.get("funcao", ""))), "left"),
            (mostrar(normalizar_ch(prof.get("carga_horaria", ""))), "center"),
            (mostrar(normalizar_turno(prof.get("turno", ""))), "center"),
            (mostrar(prof.get("p", "")), "center"),
            (mostrar(prof.get("f", "")), "center"),
            (mostrar(prof.get("fj", "")), "center"),
            (mostrar(prof.get("observacao", "")), "left"),
        ]
        baseline = y - row_altura + 4
        for col_idx, (texto, align) in enumerate(valores):
            draw_in_cell(texto, xs[col_idx], xs[col_idx + 1], baseline, align=align, font_name="Helvetica", font_size=9)
        y -= row_altura


def abreviar_nome_escola(nome: str) -> str:
    if not nome:
        return ""
    return re.sub(r"escola municipal", "EM", nome, flags=re.IGNORECASE)


def desenhar_bloco_escola(can, escola: dict, largura: float, altura: float, y_top: float, mes: int, ano: int):
    # Estilo e posicionamento semelhante ao usado em preencher_folha_ponto.py, com mapa de posições fixas
    can.setFont("Helvetica-Bold", 10)

    # Dados
    nome = abreviar_nome_escola(escola.get("nome", ""))
    endereco_partes = [escola.get("endereco", ""), escola.get("municipio", "")]
    endereco = ", ".join([p for p in endereco_partes if p])
    inep = escola.get("inep", "")
    cnpj = escola.get("cnpj", "")

    # Posições absolutas (edite aqui para ajustar)
    posicoes = {
        "nome_escola": (180, altura - 162),
        "endereco": (150, altura - 177),
        "inep": (400, altura - 194),
        "cnpj": (150, altura - 194),
        "ato_normativo": (600, altura - 194),
        "contato": (150, altura - 212),
        "email": (450, altura - 212),
        "periodo inicial": (220, altura - 230),
        "periodo final": (320, altura - 230),
    }

    if nome:
        can.drawString(*posicoes["nome_escola"], nome)
    if endereco:
        can.drawString(*posicoes["endereco"], endereco)
    if inep:
        can.drawString(*posicoes["inep"], inep)
    if cnpj:
        can.drawString(*posicoes["cnpj"], cnpj)
    # Texto fixo solicitado
    can.drawString(*posicoes["ato_normativo"], "nº 202/95 de 08/11/1995")
    can.drawString(*posicoes["contato"], "(98)98147-8951")
    can.drawString(*posicoes["email"], "uebnadirnascimento@gmail.com")

    # Datas inicial e final do mês corrente (referência: mes/ano da geração)
    from calendar import monthrange
    ultimo_dia = monthrange(ano, mes)[1]
    periodo_inicial = f"01/{mes:02d}/{ano}"
    periodo_final = f"{ultimo_dia:02d}/{mes:02d}/{ano}"
    can.drawString(*posicoes["periodo inicial"], periodo_inicial)
    can.drawString(*posicoes["periodo final"], periodo_final)

    # Retorna o último y utilizado (mantém assinatura, ainda que não seja usado)
    return min(posicoes["inep"][1] if inep else y_top, posicoes["cnpj"][1] if cnpj else y_top) - 12


def _encontrar_arquivo_base(nome_sem_acento: str, nome_com_acento: str) -> str:
    try:
        from src.services.utils.templates import find_template
    except Exception:
        candidatos = []
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidatos.append(os.path.join(base_dir, nome_sem_acento))
        candidatos.append(os.path.join(base_dir, "Modelos", nome_sem_acento))
        candidatos.append(os.path.join(base_dir, nome_com_acento))
        candidatos.append(os.path.join(base_dir, "Modelos", nome_com_acento))
        candidatos.append(os.path.join(os.getcwd(), "Modelos", nome_sem_acento))
        candidatos.append(os.path.join(os.getcwd(), "Modelos", nome_com_acento))
        for caminho in candidatos:
            if os.path.isfile(caminho):
                return caminho
        raise FileNotFoundError(f"Nenhum arquivo base encontrado. Procurado: {', '.join(candidatos)}")

    try:
        return find_template(nome_sem_acento)
    except FileNotFoundError:
        return find_template(nome_com_acento)


def gerar_resumo_ponto(mes: int, ano: int):
    dir_saida = r"G:\\Meu Drive\\NADIR_2025\\Ficha de Ponto 2025"
    os.makedirs(dir_saida, exist_ok=True)

    base2 = _encontrar_arquivo_base("Resumo de Frequencia2.pdf", "Resumo de Frequência2.pdf")
    base3 = _encontrar_arquivo_base("Resumo de Frequencia3.pdf", "Resumo de Frequência3.pdf")
    base4 = _encontrar_arquivo_base("Resumo de Frequencia4.pdf", "Resumo de Frequência4.pdf")

    conn = conectar_bd()
    if conn is None:
        logger.error("Erro: não foi possível conectar ao banco de dados.")
        return
    try:
        profissionais = consultar_profissionais(conn, mes, ano)
        escola = consultar_escola(conn, 60)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # Período (usado nas páginas 2 e 3)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    periodo = f"1 a {ultimo_dia} de {nome_mes_pt(mes)} de {ano}"

    # Reordena profissionais para colocar nomes específicos no topo
    import unicodedata as _ud
    def _sem_acentos(txt: str) -> str:
        return "".join(ch for ch in _ud.normalize("NFD", txt) if _ud.category(ch) != "Mn")

    prioridade = [
        "Leandro Fonseca Lima",
        "Rosiane de Jesus Santos Melo",
    ]
    prioridade_norm = [ _sem_acentos(n).casefold() for n in prioridade ]

    def _key(p):
        nome = str(p.get("nome", ""))
        nome_norm = _sem_acentos(nome).casefold()
        try:
            idx = prioridade_norm.index(nome_norm)
            return (0, idx)  # prioridade alta, respeita ordem da lista
        except ValueError:
            return (1, nome_norm)  # depois, ordena alfabeticamente pelos demais

    profissionais = sorted(profissionais, key=_key)

    # Divide em três blocos: 1º bloco (como antes), 2º bloco até o item 40, 3º bloco restante
    bloco1 = list(enumerate(profissionais[:17], start=1))
    bloco2 = list(enumerate(profissionais[17:40], start=18))
    bloco3 = list(enumerate(profissionais[40:], start=41))

    # Página base 2
    reader2 = PdfReader(base2)
    p2 = reader2.pages[0]
    largura2 = float(p2.mediabox.width)
    altura2 = float(p2.mediabox.height)

    packet2 = io.BytesIO()
    can2 = canvas.Canvas(packet2, pagesize=(largura2, altura2))
    # Título ou período do mês no topo, se desejar
    # Opcional: imprimir período no topo (desativado)
    IMPRIMIR_PERIODO = False
    if IMPRIMIR_PERIODO:
        can2.setFont("Helvetica", 10)
        can2.drawString(40, altura2 - 80, periodo)
    # Bloco da escola abaixo do período
    y_after_escola = desenhar_bloco_escola(can2, escola, largura2, altura2, altura2 - 98, mes, ano)
    # Tabela (posição original, sem alteração de layout)
    desenhar_tabela_profissionais(can2, bloco1, largura2, altura2, altura2 - 250)
    can2.save()
    packet2.seek(0)
    overlay2 = PdfReader(packet2)
    pagina2 = PdfReader(base2).pages[0]
    pagina2.merge_page(overlay2.pages[0])

    # Página base 3 (para bloco2)
    reader3 = PdfReader(base3)
    p3 = reader3.pages[0]
    largura3 = float(p3.mediabox.width)
    altura3 = float(p3.mediabox.height)

    packet3 = io.BytesIO()
    can3 = canvas.Canvas(packet3, pagesize=(largura3, altura3))
    if IMPRIMIR_PERIODO:
        can3.setFont("Helvetica", 10)
        can3.drawString(40, altura3 - 80, periodo)
    desenhar_tabela_profissionais(can3, bloco2, largura3, altura3, altura3 - 140)
    can3.save()
    packet3.seek(0)
    overlay3 = PdfReader(packet3)
    pagina3 = PdfReader(base3).pages[0]
    pagina3.merge_page(overlay3.pages[0])

    # Página base 4 (reutiliza o template 3 para bloco3)
    pagina4 = None
    if bloco3:
        reader4 = PdfReader(base4)
        p4 = reader4.pages[0]
        largura4 = float(p4.mediabox.width)
        altura4 = float(p4.mediabox.height)

        packet4 = io.BytesIO()
        can4 = canvas.Canvas(packet4, pagesize=(largura4, altura4))
        if IMPRIMIR_PERIODO:
            can4.setFont("Helvetica", 10)
            can4.drawString(40, altura4 - 80, periodo)
        desenhar_tabela_profissionais(can4, bloco3, largura4, altura4, altura4 - 140)
        can4.save()
        packet4.seek(0)
        overlay4 = PdfReader(packet4)
        pagina4 = PdfReader(base4).pages[0]
        pagina4.merge_page(overlay4.pages[0])

    # Grava somente o arquivo final (mesclado)
    final_out = os.path.join(dir_saida, f"resumo_de_ponto_{nome_mes_pt(mes)}_{ano}.pdf")
    wfinal = PdfWriter()
    wfinal.add_page(pagina2)
    if bloco2:
        wfinal.add_page(pagina3)
    if bloco3 and pagina4 is not None:
        wfinal.add_page(pagina4)

    # Normalizar caixas de página para evitar cortes na impressão
    try:
        for pg in wfinal.pages:
            try:
                mb = pg.mediabox
                # Ajusta todas as caixas para a MediaBox
                pg.cropbox = mb
                # Algumas versões aceitam diretamente as atribuições abaixo; se falhar, ignore silenciosamente
                try:
                    pg.trimbox = mb
                except Exception:
                    pass
                try:
                    pg.bleedbox = mb
                except Exception:
                    pass
                try:
                    pg.artbox = mb
                except Exception:
                    pass
            except Exception:
                continue
    except Exception:
        pass
    with open(final_out, "wb") as ff:
        wfinal.write(ff)
    logger.info(f"Resumo de ponto gerado: {final_out}")

    # Tentar registrar no sistema de documentos (upload + registro)
    try:
        from src.utils.utilitarios.gerenciador_documentos import salvar_documento_sistema
        from src.utils.utilitarios.tipos_documentos import TIPO_RESUMO_PONTO
        try:
            sucesso, mensagem, link = salvar_documento_sistema(
                final_out,
                TIPO_RESUMO_PONTO,
                aluno_id=None,
                funcionario_id=1,
                finalidade='Secretaria',
                descricao=f'Resumo de Ponto - {nome_mes_pt(mes)} {ano}',
            )
            if sucesso:
                logger.info('Resumo de ponto registrado no sistema: %s', link)
            else:
                logger.warning('Falha ao registrar resumo de ponto: %s', mensagem)
        except Exception:
            logger.exception('Erro ao tentar registrar resumo de ponto no sistema')
    except Exception:
        # Se o gerenciador de documentos não estiver disponível, apenas continuar
        pass

    # Abrir automaticamente no visualizador padrão de PDF (não crítico)
    try:
        if os.name == 'nt':
            os.startfile(final_out)  # Windows
        else:
            # macOS ou Linux
            import subprocess
            opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
            subprocess.Popen([opener, final_out])
    except Exception:
        # Silenciosamente ignore se não conseguir abrir
        pass


if __name__ == "__main__":
    hoje = datetime.today()
    gerar_resumo_ponto(hoje.month, hoje.year)


