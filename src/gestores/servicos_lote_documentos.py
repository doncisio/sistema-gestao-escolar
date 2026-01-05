import os
import io
import datetime
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image, PageBreak
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import TableStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from src.core.conexao import conectar_bd
from src.core.config import get_image_path
from src.core.config_logs import get_logger
from PyPDF2 import PdfMerger

logger = get_logger(__name__)


def formatar_data_extenso(data):
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    return f"{data.day:02d} de {meses[data.month - 1]} de {data.year}"


def obter_data_impressao(cutoff_date=None):
    """Retorna a string a ser impressa na data do documento.
    Se a data atual for igual ou anterior a 30/12/2025, retorna '30 de Dezembro de 2025.'
    Caso contrário, retorna a data atual por extenso com ponto final.
    """
    if cutoff_date is None:
        cutoff_date = datetime.date(2025, 12, 30)
    hoje = datetime.date.today()
    if hoje <= cutoff_date:
        return "30 de Dezembro de 2025."
    # usar formatar_data_extenso para produzir por extenso e acrescentar ponto final
    try:
        return formatar_data_extenso(datetime.datetime.today()) + '.'
    except Exception:
        return hoje.strftime('%d/%m/%Y') + '.'


def normalizar_turno(turno_raw):
    """Normaliza valores de turno (abreviações -> forma por extenso).

    Exemplos: 'VESP' -> 'Vespertino', 'MAT' -> 'Matutino', 'NOT' -> 'Noturno'
    """
    if not turno_raw:
        return 'Vespertino'
    t = str(turno_raw).strip().lower()
    # mapear substrings comuns
    if 'mat' in t or 'manh' in t or 'manhã' in t:
        return 'Matutino'
    if 'vesp' in t or 'tarde' in t:
        return 'Vespertino'
    if 'not' in t or 'noite' in t:
        return 'Noturno'
    if 'integ' in t or 'integral' in t:
        return 'Integral'
    # fallback: capitalizar palavra
    return str(turno_raw).strip().capitalize()


def nome_estado_por_sigla(uf_abrev):
    """Retorna o nome completo do estado dado a sigla (ex: 'MA' -> 'Maranhão').
    Se a sigla não for reconhecida, retorna a versão capitalizada da entrada.
    """
    if not uf_abrev:
        return 'Maranhão'
    u = str(uf_abrev).strip().upper()
    uf_map = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
        'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
        'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
        'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
        'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
        'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
        'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
    }
    return uf_map.get(u, u.capitalize())


def gerar_declaracoes_9ano_combinadas(output_filename=None, ano_letivo=2025):
    """Gera um único PDF com declarações para todos os alunos do 9º ano ativos no ano especificado.
    O texto segue o template exato informado pelo usuário, com adaptação por sexo.
    """
    conn = conectar_bd()
    if conn is None:
        logger.error("Não foi possível conectar ao banco de dados para gerar declarações em lote")
        return None
    cursor = conn.cursor()

    # Resolver ano_letivo: pode ser ano (2025) ou id da tabela AnosLetivos
    ano_id = None
    try:
        if isinstance(ano_letivo, int) and ano_letivo > 1900:
            cursor.execute("SELECT id FROM AnosLetivos WHERE ano_letivo = %s LIMIT 1", (ano_letivo,))
            arow = cursor.fetchone()
            if arow:
                ano_id = arow[0]
        else:
            # tentar interpretar como id
            cursor.execute("SELECT id FROM AnosLetivos WHERE id = %s LIMIT 1", (ano_letivo,))
            arow = cursor.fetchone()
            if arow:
                ano_id = arow[0]
    except Exception:
        ano_id = None

    if ano_id is None:
        # fallback para o último ano letivo disponível
        cursor.execute("SELECT id FROM AnosLetivos ORDER BY ano_letivo DESC LIMIT 1")
        arow = cursor.fetchone()
        ano_id = arow[0] if arow else None

    # Obter series ids que representem 9º ano
    cursor.execute(
        "SELECT id FROM series WHERE nome LIKE %s OR nome LIKE %s OR nome LIKE %s",
        ('9%', '%9º%', '%9º %')
    )
    series_rows = cursor.fetchall()
    series_ids = [r[0] for r in series_rows]

    if series_ids:
        placeholders = ','.join(['%s'] * len(series_ids))
        query = (
            f"SELECT DISTINCT a.id, a.nome, a.data_nascimento, a.local_nascimento, a.UF_nascimento, "
            f"t.nome as turma, t.turno, e.nome as escola, m.status, "
            f"(SELECT GROUP_CONCAT(r.nome SEPARATOR ' e ') FROM responsaveisalunos ra JOIN responsaveis r ON ra.responsavel_id = r.id WHERE ra.aluno_id = a.id LIMIT 2) as responsaveis "
            f"FROM Alunos a "
            f"JOIN Matriculas m ON a.id = m.aluno_id "
            f"JOIN Turmas t ON m.turma_id = t.id "
            f"LEFT JOIN series s ON t.serie_id = s.id "
            f"LEFT JOIN Escolas e ON t.escola_id = e.id OR e.id = a.escola_id "
            f"WHERE m.ano_letivo_id = %s AND m.status = 'Ativo' AND t.serie_id IN ({placeholders})"
        )
        params = [ano_id] + series_ids
        cursor.execute(query, params)
    else:
        # Fallback por nome
        query = (
            "SELECT DISTINCT a.id, a.nome, a.data_nascimento, a.local_nascimento, a.UF_nascimento, "
            "t.nome as turma, t.turno, e.nome as escola, m.status, "
            "(SELECT GROUP_CONCAT(r.nome SEPARATOR ' e ') FROM responsaveisalunos ra JOIN responsaveis r ON ra.responsavel_id = r.id WHERE ra.aluno_id = a.id LIMIT 2) as responsaveis "
            "FROM Alunos a "
            "JOIN Matriculas m ON a.id = m.aluno_id "
            "JOIN Turmas t ON m.turma_id = t.id "
            "LEFT JOIN series s ON t.serie_id = s.id "
            "LEFT JOIN Escolas e ON t.escola_id = e.id OR e.id = a.escola_id "
            "WHERE m.ano_letivo_id = %s AND m.status = 'Ativo' AND (s.nome LIKE '9%%' OR s.nome LIKE '%%9º%%' OR s.nome LIKE '%%9º %')"
        )
        cursor.execute(query, (ano_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        logger.info("Nenhum aluno do 9º ano ativo encontrado para gerar declarações combinadas")
        return None

    # Preparar documento
    os.makedirs('documentos_gerados', exist_ok=True)
    if output_filename is None:
        output_filename = f"documentos_gerados/Declaracoes_9ano_{ano_letivo}.pdf"

    # Diminuir topMargin para subir o cabeçalho na página
    doc = SimpleDocTemplate(output_filename, pagesize=letter, leftMargin=85, rightMargin=56, topMargin=60, bottomMargin=56)
    elements = []

    # Estilos
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle('Titulo', parent=styles['Normal'], fontSize=16, alignment=TA_CENTER)
    estilo_texto = ParagraphStyle('Texto', parent=styles['Normal'], fontSize=12, leading=18, alignment=TA_JUSTIFY)
    estilo_direita = ParagraphStyle('Direita', parent=styles['Normal'], fontSize=12, alignment=2)

    # Data final — decidir entre 30/12/2025 ou data atual
    data_documento = obter_data_impressao()

    for r in rows:
        aluno_id = r[0]
        nome = r[1] or ''
        data_nasc = r[2]
        municipio = (r[3] or '').upper()
        uf = (r[4] or 'MA').upper()
        # Obter nome completo do estado a partir da sigla
        uf_full = nome_estado_por_sigla(uf)
        # Preparar trecho usado no texto: para Distrito Federal não usamos 'Estado do '
        if uf_full == 'Distrito Federal':
            estado_texto = 'DISTRITO FEDERAL'
        else:
            estado_texto = f"Estado do {uf_full}"
        turma = r[5] or ''
        turno = normalizar_turno(r[6])
        escola = r[7] or ''
        responsaveis = r[9] or ''

        # dividir responsaveis
        partes = responsaveis.split(' e ') if responsaveis else [ '', '' ]
        pai = partes[0] if len(partes) > 0 else ''
        mae = partes[1] if len(partes) > 1 else ''

        # obter genero buscando no banco pode ser complexo; tentar consulta rápida
        # Para segurança, buscaremos sexo via outra query
        sexo = None
        try:
            conn = conectar_bd()
            c = conn.cursor()
            c.execute("SELECT sexo FROM Alunos WHERE id = %s", (aluno_id,))
            srow = c.fetchone()
            sexo = srow[0] if srow else None
            c.close()
            conn.close()
        except Exception:
            sexo = None

        genero = 'masculino' if (not sexo or sexo.upper() != 'F') else 'feminino'

        # formatar data nascimento
        try:
            if data_nasc:
                if isinstance(data_nasc, str):
                    data_dt = datetime.datetime.strptime(data_nasc.split(' ')[0], '%Y-%m-%d')
                else:
                    data_dt = data_nasc
                dia = f"{data_dt.day:02d}"
                mes_nome = formatar_data_extenso(data_dt).split(' de ')[1]
                ano = f"{data_dt.year}"
            else:
                dia = ''
                mes_nome = ''
                ano = ''
        except Exception:
            dia = ''
            mes_nome = ''
            ano = ''

        # adaptar palavras por sexo
        nascido_a = 'nascida' if genero == 'feminino' else 'nascido'
        filho_a = 'filha' if genero == 'feminino' else 'filho'
        aprovado_a = 'Aprovada' if genero == 'feminino' else 'Aprovado'
        aprovado_par = 'Aprovada' if genero == 'feminino' else 'Aprovado'

        # Montar parágrafo conforme template exato
        texto = (
            f"Declaro para os devidos fins de direito, que {(nome or '').upper()}, {nascido_a} no dia {dia} de {mes_nome} de {ano}, "
            f"natural de {municipio}, {estado_texto}, {filho_a} de {(pai if pai else '---').upper()}, e de {(mae if mae else '---').upper()}, "
            f"está {aprovado_a.lower()} no 9º ANO do Ensino Fundamental Anos Finais, na {(escola or '').upper()}, no ano letivo de {ano_letivo}, no turno {turno}.<br/><br/>"
            f"Situação Acadêmica: {aprovado_par}<br/><br/>"
            f"Por ser a expressão da verdade dato e assino a presente declaração, para que surta os devidos efeitos legais."     
        )

        # Cabeçalho com logos e nome da escola
        # Cabeçalho simplificado: apenas o brasão da prefeitura à esquerda e
        # as duas linhas de texto centrais solicitadas
        figura_prefeitura = None
        try:
            figura_prefeitura = str(get_image_path('logo_prefeitura.png')) if get_image_path('logo_prefeitura.png') else None
        except Exception:
            figura_prefeitura = None

        # fallback para pasta local 'imagens' caso get_image_path não resolva
        if not figura_prefeitura:
            possivel = os.path.join(os.path.dirname(__file__), '..', 'imagens', 'logo_prefeitura.png')
            possivel = os.path.normpath(possivel)
            if os.path.exists(possivel):
                figura_prefeitura = possivel

        # Centralizar a imagem e colocar as duas linhas de texto abaixo dela
        # Inserir a imagem centralizada (se disponível)
        if figura_prefeitura and os.path.exists(figura_prefeitura):
            try:
                # Preservar proporção original da imagem: calcular altura a partir
                # da largura alvo usando as dimensões reais via Pillow
                from PIL import Image as PILImage
                pil_img = PILImage.open(figura_prefeitura)
                w_px, h_px = pil_img.size
                if w_px and h_px:
                    largura_alvo = 1.2 * inch
                    altura_calc = largura_alvo * (h_px / float(w_px))
                    img = Image(figura_prefeitura, width=largura_alvo, height=altura_calc)
                else:
                    img = Image(figura_prefeitura, width=1.2 * inch, height=1.2 * inch)
            except Exception:
                # fallback simples
                img = Image(figura_prefeitura, width=1.2 * inch, height=1.2 * inch)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 0.1 * inch))

        # Texto centralizado abaixo da imagem
        center = Paragraph('<br/>'.join([
            "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
            "SECRETARIA MUNICIPAL DE EDUCAÇÃO - SEMED"
        ]), ParagraphStyle(name='Header', fontSize=12, alignment=TA_CENTER))
        elements.append(center)
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph('<b>Declaração</b>'.upper(), estilo_titulo))
        elements.append(Spacer(1, 0.7 * inch))

        elements.append(Paragraph(texto, estilo_texto))
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph(f"PACO DO LUMIAR / MA, {data_documento}", estilo_direita))
        elements.append(Spacer(1, 1 * inch))
        elements.append(Paragraph("______________________________________", ParagraphStyle(name='Ass', alignment=TA_CENTER)))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("GESTOR(A)", ParagraphStyle(name='AssNome', alignment=TA_CENTER)))
        elements.append(PageBreak())

    # Remover último PageBreak
    if elements and isinstance(elements[-1], PageBreak):
        elements = elements[:-1]

    doc.build(elements)
    logger.info(f"Arquivo de declarações combinado gerado: {output_filename}")
    return output_filename


def gerar_declaracoes_5ano_combinadas(output_filename=None, ano_letivo=2025):
    """Gera um único PDF com declarações para todos os alunos do 5º ano ativos no ano especificado.
    A lógica é análoga à geração para 9º ano, mas filtra séries do 5º ano e ajusta o texto.
    """
    conn = conectar_bd()
    if conn is None:
        logger.error("Não foi possível conectar ao banco de dados para gerar declarações em lote (5º ano)")
        return None
    cursor = conn.cursor()

    # Resolver ano_letivo: pode ser ano (2025) ou id da tabela AnosLetivos
    ano_id = None
    try:
        if isinstance(ano_letivo, int) and ano_letivo > 1900:
            cursor.execute("SELECT id FROM AnosLetivos WHERE ano_letivo = %s LIMIT 1", (ano_letivo,))
            arow = cursor.fetchone()
            if arow:
                ano_id = arow[0]
        else:
            cursor.execute("SELECT id FROM AnosLetivos WHERE id = %s LIMIT 1", (ano_letivo,))
            arow = cursor.fetchone()
            if arow:
                ano_id = arow[0]
    except Exception:
        ano_id = None

    if ano_id is None:
        # fallback para o último ano letivo disponível
        cursor.execute("SELECT id FROM AnosLetivos ORDER BY ano_letivo DESC LIMIT 1")
        arow = cursor.fetchone()
        ano_id = arow[0] if arow else None

    # Obter series ids que representem 5º ano
    cursor.execute(
        "SELECT id FROM series WHERE nome LIKE %s OR nome LIKE %s OR nome LIKE %s",
        ('5%', '%5º%', '%5º %')
    )
    series_rows = cursor.fetchall()
    series_ids = [r[0] for r in series_rows]

    if series_ids:
        placeholders = ','.join(['%s'] * len(series_ids))
        query = (
            f"SELECT DISTINCT a.id, a.nome, a.data_nascimento, a.local_nascimento, a.UF_nascimento, "
            f"t.nome as turma, t.turno, e.nome as escola, m.status, "
            f"(SELECT GROUP_CONCAT(r.nome SEPARATOR ' e ') FROM responsaveisalunos ra JOIN responsaveis r ON ra.responsavel_id = r.id WHERE ra.aluno_id = a.id LIMIT 2) as responsaveis "
            f"FROM Alunos a "
            f"JOIN Matriculas m ON a.id = m.aluno_id "
            f"JOIN Turmas t ON m.turma_id = t.id "
            f"LEFT JOIN series s ON t.serie_id = s.id "
            f"LEFT JOIN Escolas e ON t.escola_id = e.id OR e.id = a.escola_id "
            f"WHERE m.ano_letivo_id = %s AND m.status = 'Ativo' AND t.serie_id IN ({placeholders})"
        )
        params = [ano_id] + series_ids
        cursor.execute(query, params)
    else:
        # Fallback por nome
        query = (
            "SELECT DISTINCT a.id, a.nome, a.data_nascimento, a.local_nascimento, a.UF_nascimento, "
            "t.nome as turma, t.turno, e.nome as escola, m.status, "
            "(SELECT GROUP_CONCAT(r.nome SEPARATOR ' e ') FROM responsaveisalunos ra JOIN responsaveis r ON ra.responsavel_id = r.id WHERE ra.aluno_id = a.id LIMIT 2) as responsaveis "
            "FROM Alunos a "
            "JOIN Matriculas m ON a.id = m.aluno_id "
            "JOIN Turmas t ON m.turma_id = t.id "
            "LEFT JOIN series s ON t.serie_id = s.id "
            "LEFT JOIN Escolas e ON t.escola_id = e.id OR e.id = a.escola_id "
            "WHERE m.ano_letivo_id = %s AND m.status = 'Ativo' AND (s.nome LIKE '5%%' OR s.nome LIKE '%%5º%%' OR s.nome LIKE '%%5º %')"
        )
        cursor.execute(query, (ano_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        logger.info("Nenhum aluno do 5º ano ativo encontrado para gerar declarações combinadas")
        return None

    # Preparar documento
    os.makedirs('documentos_gerados', exist_ok=True)
    if output_filename is None:
        output_filename = f"documentos_gerados/Declaracoes_5ano_{ano_letivo}.pdf"

    doc = SimpleDocTemplate(output_filename, pagesize=letter, leftMargin=85, rightMargin=56, topMargin=60, bottomMargin=56)
    elements = []

    # Estilos
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle('Titulo', parent=styles['Normal'], fontSize=16, alignment=TA_CENTER)
    estilo_texto = ParagraphStyle('Texto', parent=styles['Normal'], fontSize=12, leading=18, alignment=TA_JUSTIFY)
    estilo_direita = ParagraphStyle('Direita', parent=styles['Normal'], fontSize=12, alignment=2)

    data_documento = obter_data_impressao()

    for r in rows:
        aluno_id = r[0]
        nome = r[1] or ''
        data_nasc = r[2]
        municipio = (r[3] or '').upper()
        uf = (r[4] or 'MA').upper()
        uf_full = nome_estado_por_sigla(uf)
        if uf_full == 'Distrito Federal':
            estado_texto = 'DISTRITO FEDERAL'
        else:
            estado_texto = f"Estado do {uf_full}"
        turma = r[5] or ''
        turno = normalizar_turno(r[6])
        escola = r[7] or ''
        responsaveis = r[9] or ''

        partes = responsaveis.split(' e ') if responsaveis else [ '', '' ]
        pai = partes[0] if len(partes) > 0 else ''
        mae = partes[1] if len(partes) > 1 else ''

        sexo = None
        try:
            conn = conectar_bd()
            c = conn.cursor()
            c.execute("SELECT sexo FROM Alunos WHERE id = %s", (aluno_id,))
            srow = c.fetchone()
            sexo = srow[0] if srow else None
            c.close()
            conn.close()
        except Exception:
            sexo = None

        genero = 'masculino' if (not sexo or sexo.upper() != 'F') else 'feminino'

        try:
            if data_nasc:
                if isinstance(data_nasc, str):
                    data_dt = datetime.datetime.strptime(data_nasc.split(' ')[0], '%Y-%m-%d')
                else:
                    data_dt = data_nasc
                dia = f"{data_dt.day:02d}"
                mes_nome = formatar_data_extenso(data_dt).split(' de ')[1]
                ano = f"{data_dt.year}"
            else:
                dia = ''
                mes_nome = ''
                ano = ''
        except Exception:
            dia = ''
            mes_nome = ''
            ano = ''

        nascido_a = 'nascida' if genero == 'feminino' else 'nascido'
        filho_a = 'filha' if genero == 'feminino' else 'filho'
        aprovado_a = 'Aprovada' if genero == 'feminino' else 'Aprovado'
        aprovado_par = 'Aprovada' if genero == 'feminino' else 'Aprovado'

        texto = (
            f"Declaro para os devidos fins de direito, que {(nome or '').upper()}, {nascido_a} no dia {dia} de {mes_nome} de {ano}, "
            f"natural de {municipio}, {estado_texto}, {filho_a} de {(pai if pai else '---').upper()}, e de {(mae if mae else '---').upper()}, "
            f"está {aprovado_a.lower()} no 5º ANO do Ensino Fundamental, na {(escola or '').upper()}, no ano letivo de {ano_letivo}, no turno {turno}.<br/><br/>"
            f"Situação Acadêmica: {aprovado_par}<br/><br/>"
            f"Por ser a expressão da verdade dato e assino a presente declaração, para que surta os devidos efeitos legais."     
        )

        figura_prefeitura = None
        try:
            figura_prefeitura = str(get_image_path('logo_prefeitura.png')) if get_image_path('logo_prefeitura.png') else None
        except Exception:
            figura_prefeitura = None

        if not figura_prefeitura:
            possivel = os.path.join(os.path.dirname(__file__), '..', 'imagens', 'logo_prefeitura.png')
            possivel = os.path.normpath(possivel)
            if os.path.exists(possivel):
                figura_prefeitura = possivel

        if figura_prefeitura and os.path.exists(figura_prefeitura):
            try:
                from PIL import Image as PILImage
                pil_img = PILImage.open(figura_prefeitura)
                w_px, h_px = pil_img.size
                if w_px and h_px:
                    largura_alvo = 1.2 * inch
                    altura_calc = largura_alvo * (h_px / float(w_px))
                    img = Image(figura_prefeitura, width=largura_alvo, height=altura_calc)
                else:
                    img = Image(figura_prefeitura, width=1.2 * inch, height=1.2 * inch)
            except Exception:
                img = Image(figura_prefeitura, width=1.2 * inch, height=1.2 * inch)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 0.1 * inch))

        center = Paragraph('<br/>'.join([
            "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
            "SECRETARIA MUNICIPAL DE EDUCAÇÃO - SEMED"
        ]), ParagraphStyle(name='Header', fontSize=12, alignment=TA_CENTER))
        elements.append(center)
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph('<b>Declaração</b>'.upper(), estilo_titulo))
        elements.append(Spacer(1, 0.7 * inch))

        elements.append(Paragraph(texto, estilo_texto))
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph(f"PACO DO LUMIAR / MA, {data_documento}", estilo_direita))
        elements.append(Spacer(1, 1 * inch))
        elements.append(Paragraph("______________________________________", ParagraphStyle(name='Ass', alignment=TA_CENTER)))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("GESTOR(A)", ParagraphStyle(name='AssNome', alignment=TA_CENTER)))
        elements.append(PageBreak())

    if elements and isinstance(elements[-1], PageBreak):
        elements = elements[:-1]

    doc.build(elements)
    logger.info(f"Arquivo de declarações combinado gerado: {output_filename}")
    return output_filename


def gerar_certificados_9ano_combinados(output_filename=None, ano_letivo=2025):
    """Gera um PDF combinado com páginas de certificados usando a função centralizada.
    """
    conn = conectar_bd()
    if conn is None:
        logger.error("Não foi possível conectar ao banco de dados para gerar certificados em lote")
        return None
    cursor = conn.cursor()

    # Resolver ano_letivo para id (aceita ano numérico 2025 ou id da tabela)
    ano_id = None
    try:
        if isinstance(ano_letivo, int) and ano_letivo > 1900:
            cursor.execute("SELECT id FROM AnosLetivos WHERE ano_letivo = %s LIMIT 1", (ano_letivo,))
            arow = cursor.fetchone()
            if arow:
                ano_id = arow[0]
        else:
            cursor.execute("SELECT id FROM AnosLetivos WHERE id = %s LIMIT 1", (ano_letivo,))
            arow = cursor.fetchone()
            if arow:
                ano_id = arow[0]
    except Exception:
        ano_id = None

    if ano_id is None:
        cursor.execute("SELECT id FROM AnosLetivos ORDER BY ano_letivo DESC LIMIT 1")
        arow = cursor.fetchone()
        ano_id = arow[0] if arow else None

    cursor.execute(
        "SELECT id FROM series WHERE nome LIKE %s OR nome LIKE %s OR nome LIKE %s",
        ('9%', '%9º%', '%9º %')
    )
    series_rows = cursor.fetchall()
    series_ids = [r[0] for r in series_rows]

    if series_ids:
        placeholders = ','.join(['%s'] * len(series_ids))
        query = (
            f"SELECT DISTINCT a.id, a.nome, a.data_nascimento, a.local_nascimento, a.UF_nascimento, "
            f"t.nome as turma, t.turno, e.nome as escola, m.status, a.sexo, "
            f"(SELECT GROUP_CONCAT(r.nome SEPARATOR ' e ') FROM responsaveisalunos ra JOIN responsaveis r ON ra.responsavel_id = r.id WHERE ra.aluno_id = a.id LIMIT 2) as responsaveis "
            f"FROM Alunos a "
            f"JOIN Matriculas m ON a.id = m.aluno_id "
            f"JOIN Turmas t ON m.turma_id = t.id "
            f"LEFT JOIN series s ON t.serie_id = s.id "
            f"LEFT JOIN Escolas e ON t.escola_id = e.id OR e.id = a.escola_id "
            f"WHERE m.ano_letivo_id = %s AND m.status = 'Ativo' AND t.serie_id IN ({placeholders})"
        )
        params = [ano_id] + series_ids
        cursor.execute(query, params)
    else:
        query = (
            "SELECT DISTINCT a.id, a.nome, a.data_nascimento, a.local_nascimento, a.UF_nascimento, "
            "t.nome as turma, t.turno, e.nome as escola, m.status, a.sexo, "
            "(SELECT GROUP_CONCAT(r.nome SEPARATOR ' e ') FROM responsaveisalunos ra JOIN responsaveis r ON ra.responsavel_id = r.id WHERE ra.aluno_id = a.id LIMIT 2) as responsaveis "
            "FROM Alunos a "
            "JOIN Matriculas m ON a.id = m.aluno_id "
            "JOIN Turmas t ON m.turma_id = t.id "
            "LEFT JOIN series s ON t.serie_id = s.id "
            "LEFT JOIN Escolas e ON t.escola_id = e.id OR e.id = a.escola_id "
            "WHERE m.ano_letivo_id = %s AND m.status = 'Ativo' AND (s.nome LIKE '9%%' OR s.nome LIKE '%%9º%%' OR s.nome LIKE '%%9º %')"
        )
        cursor.execute(query, (ano_id,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        logger.info("Nenhum aluno do 9º ano ativo encontrado para gerar certificados combinados")
        return None

    os.makedirs('documentos_gerados', exist_ok=True)
    if output_filename is None:
        output_filename = f"documentos_gerados/Certificados_9ano_{ano_letivo}.pdf"
    
    # Importar função centralizada para renderizar certificados
    try:
        from src.relatorios.geradores.certificado import renderizar_pagina_certificado
    except ImportError:
        logger.error("Não foi possível importar renderizar_pagina_certificado de gerar_certificado_pdf.py")
        return None

    from reportlab.pdfgen import canvas as rl_canvas

    largura, altura = landscape(A4)
    # Se o arquivo alvo existir e estiver bloqueado, tentamos removê-lo antes de criar o canvas.
    final_output = output_filename
    if os.path.exists(final_output):
        try:
            os.remove(final_output)
        except Exception:
            ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            final_output = final_output.replace('.pdf', f'_{ts}.pdf')
            logger.warning(f"Arquivo de saída original bloqueado, gravando em: {final_output}")

    c = rl_canvas.Canvas(final_output, pagesize=landscape(A4))

    # Iterar alunos e desenhar cada certificado em uma página
    for r in rows:
        # Montar dicionário de dados no formato esperado por renderizar_pagina_certificado
        dados = {
            'id': r[0],
            'nome': r[1],
            'data_nascimento': r[2],
            'local_nascimento': r[3],
            'UF_nascimento': r[4],
            'nome_escola': r[7],
            'sexo': r[9] if len(r) > 9 else '',
            'nomes_responsaveis': r[10] if len(r) > 10 else ''
        }
        
        # Renderizar a página usando a função centralizada
        renderizar_pagina_certificado(c, dados, ano_letivo)
        c.showPage()

    try:
        c.save()
        logger.info(f"Arquivo de certificados combinado gerado: {final_output}")
        return final_output
    except Exception as e:
        logger.exception(f"Erro ao salvar PDF combinado: {e}")
        return None
