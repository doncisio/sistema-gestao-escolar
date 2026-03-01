"""
Módulo para preencher templates PDF da pasta SMTT com dados do sistema.
Templates preenchidos com: dados da escola, gestor geral (representante) e séries.

Arquivos gerados:
  curso.pdf        → tabela de séries/cursos com tipo de ensino e modalidade
  instituicao.pdf  → ficha de cadastro da instituição de ensino
  representante.pdf → ficha de cadastro do representante da instituição

Coordenadas mapeadas a partir da inspeção dos PDFs originais com pdfplumber.
Sistema de coordenadas do reportlab: origem (0,0) no canto inferior esquerdo da página.
Conversão: reportlab_y = page_height - pdfplumber_y_bot
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black
import io

from src.core.config import ANO_LETIVO_ATUAL, PROJECT_ROOT
from src.core.config_logs import get_logger
from db.connection import get_cursor
from tkinter import messagebox

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Mapeamento de séries → código SMTT de tipo de ensino
# Tipo de Ensino SMTT:  1=Educação Infantil, 2=Fund.I, 3=Fund.II,
#                       4=Ensino Médio,       8=EJA
# Modalidade SMTT:      1=Presencial, 2=Semipresencial, 3=EAD
# ---------------------------------------------------------------------------
_TIPO_ENSINO_SMTT: Dict[str, int] = {
    "berçário": 1, "maternal": 1, "jardim": 1, "pré-escola": 1,
    "pré i": 1, "pré ii": 1, "pré 1": 1, "pré 2": 1,
    "1º ano": 2, "2º ano": 2, "3º ano": 2, "4º ano": 2, "5º ano": 2,
    "1 ano": 2,  "2 ano": 2,  "3 ano": 2,  "4 ano": 2,  "5 ano": 2,
    "6º ano": 3, "7º ano": 3, "8º ano": 3, "9º ano": 3,
    "6 ano": 3,  "7 ano": 3,  "8 ano": 3,  "9 ano": 3,
    "ensino médio": 4, "1º médio": 4, "2º médio": 4, "3º médio": 4,
    "eja": 8, "jovens e adultos": 8,
}

_MODALIDADE_PADRAO = 1  # Presencial

# Complemento do segmento para cada tipo SMTT
_SEGMENTO_SMTT: Dict[int, str] = {
    1: 'da Educação Infantil',
    2: 'do Ensino Fundamental I',
    3: 'do Ensino Fundamental II',
    4: 'do Ensino Médio',
    8: 'da EJA',
}


def _descricao_completa(serie_nome: str, turma_nomes: List[str]) -> str:
    """
    Monta a descrição completa do curso para a tabela de curso.pdf.

    Exemplos:
      ('1º Ano', ['1º Ano A'])          → '1º Ano do Ensino Fundamental I'
      ('7º Ano', ['7º Ano A','7º Ano B']) → '7º Ano do Ensino Fundamental II (A e B)'
    """
    tipo     = _tipo_ensino(serie_nome)
    segmento = _SEGMENTO_SMTT.get(tipo, '')
    desc     = f"{serie_nome} {segmento}".strip()

    # Extrai o identificador de cada turma removendo o nome da série
    ids: List[str] = []
    for tnome in turma_nomes:
        sufixo = tnome.strip()
        # Remove o prefixo igual ao serie_nome (case-insensitive)
        if sufixo.lower().startswith(serie_nome.lower()):
            sufixo = sufixo[len(serie_nome):].strip()
        if sufixo:
            ids.append(sufixo)

    if ids:
        if len(ids) == 1:
            desc = f"{desc} ({ids[0]})"
        else:
            lista = ', '.join(ids[:-1]) + ' e ' + ids[-1]
            desc = f"{desc} ({lista})"

    return desc

# ---------------------------------------------------------------------------
# Posições X (centro de cada célula) para dígitos do CNPJ em instituicao.pdf.
# 14 células, y_bot_pdf=176.50 → reportlab_y_base = 841.9-176.5+3 = 668.4
# (usamos drawCentredString em cada posição)
# ---------------------------------------------------------------------------
_CNPJ_X_CENTERS = [
    51.65, 68.65, 85.90, 102.90, 119.90, 136.90, 153.90,
    170.90, 187.90, 205.15, 222.35, 238.85, 255.35, 271.85,
]
_CNPJ_Y_RL = 668.4   # y no sistema reportlab (centro vertical das células)


def _tipo_ensino(serie_nome: str) -> int:
    """Retorna o código SMTT de tipo de ensino para a série informada."""
    chave = serie_nome.lower().strip()
    for k, v in _TIPO_ENSINO_SMTT.items():
        if k in chave:
            return v
    return 2  # Ensino Fundamental I como padrão


def _val(d: Optional[Dict], chave: str, padrao: str = "") -> str:
    """Lê uma chave do dicionário ou retorna padrao."""
    if not d:
        return padrao
    return str(d.get(chave) or padrao)


# ---------------------------------------------------------------------------
# Funções de consulta ao banco
# ---------------------------------------------------------------------------

def buscar_dados_escola(escola_id: int = 60) -> Optional[Dict[str, Any]]:
    """
    Busca dados cadastrais da escola (nome, endereço, CNPJ, INEP, etc.).

    Args:
        escola_id: ID da escola (padrão: 60)

    Returns:
        Dicionário com campos: id, nome, endereco, inep, cnpj, municipio,
        telefone, cep, bairro — ou None em caso de erro.
    """
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    id, nome, endereco, inep, cnpj, municipio,
                    telefone, cep, bairro
                FROM escolas
                WHERE id = %s
                LIMIT 1
            """, (escola_id,))
            resultado = cursor.fetchone()
            if resultado:
                logger.info(f"Escola encontrada: {resultado.get('nome', 'N/A')}")
                return resultado
            logger.warning(f"Escola id={escola_id} não encontrada")
            return None
    except Exception as e:
        logger.exception(f"Erro ao buscar dados da escola: {e}")
        return None


def buscar_gestor_geral(escola_id: int = 60) -> Optional[Dict[str, Any]]:
    """
    Busca dados completos do gestor geral da escola.
    Prioriza quem tem função 'Gestor Geral', senão busca por cargo 'Gestor Escolar'.

    Campos retornados: nome, cpf, rg, orgao_expedidor, data_expedicao_rg,
    cargo, funcao, email, telefone, endereco_logradouro, endereco_numero,
    endereco_bairro, endereco_cidade, endereco_estado, endereco_cep.

    Args:
        escola_id: ID da escola (padrão: 60)

    Returns:
        Dicionário com dados do gestor ou None.
    """
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    nome,
                    cpf,
                    rg,
                    orgao_expedidor,
                    data_expedicao_rg,
                    cargo,
                    funcao,
                    email,
                    telefone,
                    endereco_logradouro,
                    endereco_numero,
                    endereco_bairro,
                    endereco_cidade,
                    endereco_estado,
                    endereco_cep
                FROM funcionarios
                WHERE escola_id = %s
                AND (
                    funcao = 'Gestor Geral'
                    OR (cargo = 'Gestor Escolar' AND (funcao IS NULL OR funcao = ''))
                )
                ORDER BY
                    CASE WHEN funcao = 'Gestor Geral' THEN 1 ELSE 2 END
                LIMIT 1
            """, (escola_id,))

            resultado = cursor.fetchone()
            if resultado:
                logger.info(f"Gestor encontrado: {resultado.get('nome', 'N/A')}")
                return resultado

            logger.warning("Nenhum gestor geral encontrado")
            return None

    except Exception as e:
        logger.exception(f"Erro ao buscar gestor geral: {e}")
        return None


def buscar_dados_ano_letivo(ano_letivo: int = None) -> Optional[Dict[str, Any]]:
    """
    Busca dados do ano letivo.

    Args:
        ano_letivo: Ano letivo a buscar (padrão: ANO_LETIVO_ATUAL)

    Returns:
        Dicionário com dados do ano letivo ou None.
    """
    if ano_letivo is None:
        ano_letivo = ANO_LETIVO_ATUAL

    try:
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT id, ano_letivo, data_inicio, data_fim, numero_dias_aula
                FROM anosletivos
                WHERE ano_letivo = %s
                LIMIT 1
            """, (ano_letivo,))

            resultado = cursor.fetchone()
            if resultado:
                logger.info(f"Ano letivo encontrado: {ano_letivo}")
                return resultado

            logger.warning(f"Ano letivo {ano_letivo} não encontrado")
            return None

    except Exception as e:
        logger.exception(f"Erro ao buscar ano letivo: {e}")
        return None


def buscar_series_escola(escola_id: int = 60, ano_letivo_id: int = None) -> List[Dict[str, Any]]:
    """
    Busca séries distintas da escola no ano letivo para preencher a tabela
    de cursos do formulário SMTT (curso.pdf).

    Cada série distinta representa uma linha da tabela, com o código de
    Tipo de Ensino SMTT calculado automaticamente.

    Args:
        escola_id: ID da escola (padrão: 60)
        ano_letivo_id: ID do ano letivo (padrão: ano atual)

    Returns:
        Lista de dicts com chaves: serie_nome, tipo_ensino, modalidade.
    """
    try:
        with get_cursor() as cursor:
            if ano_letivo_id is None:
                dados_ano = buscar_dados_ano_letivo()
                if dados_ano:
                    ano_letivo_id = dados_ano.get('id')
                else:
                    logger.error("Não foi possível determinar o ano letivo")
                    return []

            cursor.execute("""
                SELECT DISTINCT
                    s.id AS serie_id,
                    s.nome AS serie_nome
                FROM turmas t
                JOIN series s ON t.serie_id = s.id
                WHERE t.escola_id = %s
                  AND t.ano_letivo_id = %s
                ORDER BY s.id
            """, (escola_id, ano_letivo_id))

            rows = cursor.fetchall()
            series = []
            for row in rows:
                serie_nome = row.get('serie_nome', '')
                series.append({
                    'serie_nome': serie_nome,
                    'tipo_ensino': _tipo_ensino(serie_nome),
                    'modalidade': _MODALIDADE_PADRAO,
                })

            logger.info(f"Encontradas {len(series)} séries distintas")
            return series

    except Exception as e:
        logger.exception(f"Erro ao buscar séries da escola: {e}")
        return []


def buscar_turmas_escola(escola_id: int = 60, ano_letivo_id: int = None) -> List[Dict[str, Any]]:
    """
    Busca todas as turmas da escola no ano letivo.

    Args:
        escola_id: ID da escola (padrão: 60)
        ano_letivo_id: ID do ano letivo (padrão: ano atual)

    Returns:
        Lista de dicionários com dados das turmas.
    """
    try:
        with get_cursor() as cursor:
            if ano_letivo_id is None:
                dados_ano = buscar_dados_ano_letivo()
                if dados_ano:
                    ano_letivo_id = dados_ano.get('id')
                else:
                    logger.error("Não foi possível determinar o ano letivo")
                    return []

            cursor.execute("""
                SELECT
                    t.id,
                    t.nome AS turma_nome,
                    t.turno,
                    s.nome AS serie_nome,
                    COUNT(DISTINCT m.aluno_id) AS total_alunos
                FROM turmas t
                JOIN series s ON t.serie_id = s.id
                LEFT JOIN matriculas m ON t.id = m.turma_id
                    AND m.status = 'Ativo'
                    AND m.ano_letivo_id = %s
                WHERE t.escola_id = %s
                  AND t.ano_letivo_id = %s
                GROUP BY t.id, t.nome, t.turno, s.nome
                ORDER BY s.nome, t.nome, t.turno
            """, (ano_letivo_id, escola_id, ano_letivo_id))

            turmas = cursor.fetchall()
            logger.info(f"Encontradas {len(turmas)} turmas")
            return turmas

    except Exception as e:
        logger.exception(f"Erro ao buscar turmas: {e}")
        return []


def buscar_estatisticas_escola(escola_id: int = 60,
                               ano_letivo_id: int = None) -> Dict[str, Any]:
    """
    Busca estatísticas consolidadas da escola para preencher a tabela da
    ficha de cadastro (instituicao.pdf).

    Retorna dicionário com:
      alunos_mat  — alunos matriculados ativos no turno Matutino
      alunos_ves  — alunos matriculados ativos no turno Vespertino
      prof_mat    — professores com turno Matutino (inclui Matutino/Vespertino)
      prof_ves    — professores com turno Vespertino (inclui Matutino/Vespertino)
      func_mat    — outros funcionários com turno Matutino
      func_ves    — outros funcionários com turno Vespertino

    Args:
        escola_id: ID da escola (padrão: 60)
        ano_letivo_id: ID do ano letivo (padrão: ano atual)
    """
    resultado: Dict[str, Any] = {
        'alunos_mat': '', 'alunos_ves': '',
        'prof_mat': '',   'prof_ves': '',
        'func_mat': '',   'func_ves': '',
    }
    try:
        with get_cursor() as cursor:
            if ano_letivo_id is None:
                dados_ano = buscar_dados_ano_letivo()
                ano_letivo_id = dados_ano.get('id') if dados_ano else None
                if not ano_letivo_id:
                    return resultado

            # ── Alunos por turno ──────────────────────────────────────────
            # Turno no campo turmas pode ser 'Matutino', 'MAT', 'Vespertino', 'VESP'
            cursor.execute("""
                SELECT
                    t.turno,
                    COUNT(DISTINCT m.aluno_id) AS total
                FROM matriculas m
                JOIN turmas t ON m.turma_id = t.id
                WHERE t.escola_id = %s
                  AND m.status = 'Ativo'
                  AND m.ano_letivo_id = %s
                GROUP BY t.turno
            """, (escola_id, ano_letivo_id))

            for row in cursor.fetchall():
                turno = (row.get('turno') or '').upper().strip()
                total = row.get('total', 0)
                if turno in ('MATUTINO', 'MAT'):
                    resultado['alunos_mat'] = str(total)
                elif turno in ('VESPERTINO', 'VESP'):
                    resultado['alunos_ves'] = str(total)

            # ── Professores por turno ─────────────────────────────────────
            cursor.execute("""
                SELECT turno, COUNT(*) AS total
                FROM funcionarios
                WHERE escola_id = %s
                  AND cargo = 'Professor@'
                GROUP BY turno
            """, (escola_id,))

            for row in cursor.fetchall():
                turno = (row.get('turno') or '').lower()
                total = row.get('total', 0)
                if turno in ('matutino', 'matutino/vespertino'):
                    prev = int(resultado['prof_mat'] or 0)
                    resultado['prof_mat'] = str(prev + total)
                if turno in ('vespertino', 'matutino/vespertino'):
                    prev = int(resultado['prof_ves'] or 0)
                    resultado['prof_ves'] = str(prev + total)

            # ── Outros funcionários por turno ─────────────────────────────
            cursor.execute("""
                SELECT turno, COUNT(*) AS total
                FROM funcionarios
                WHERE escola_id = %s
                  AND cargo <> 'Professor@'
                GROUP BY turno
            """, (escola_id,))

            for row in cursor.fetchall():
                turno = (row.get('turno') or '').lower()
                total = row.get('total', 0)
                if turno in ('matutino', 'matutino/vespertino'):
                    prev = int(resultado['func_mat'] or 0)
                    resultado['func_mat'] = str(prev + total)
                if turno in ('vespertino', 'matutino/vespertino'):
                    prev = int(resultado['func_ves'] or 0)
                    resultado['func_ves'] = str(prev + total)

        logger.info(f"Estatísticas escola: {resultado}")
        return resultado

    except Exception as e:
        logger.exception(f"Erro ao buscar estatísticas da escola: {e}")
        return resultado


# ---------------------------------------------------------------------------
# Helpers de preenchimento por template
# ---------------------------------------------------------------------------

def _txt(can: canvas.Canvas, x: float, y: float, texto: str,
         font: str = "Helvetica", size: float = 8.5) -> None:
    """Desenha texto no canvas na posição (x, y) com a fonte indicada."""
    can.setFont(font, size)
    can.drawString(x, y, str(texto))


def _preencher_curso(can: canvas.Canvas, height: float, dados: Dict[str, Any]) -> None:
    """
    Preenche o template curso.pdf.

    Campos preenchidos:
      - INSTITUIÇÃO (→ nome da escola; CÓDIGO não é preenchido)
      - Tabela de cursos (linhas 1–36):
            Nº  | DESCRIÇÃO DO CURSO | TIPO DE ENSINO | MODALIDADE

    Séries com múltiplas turmas são agrupadas numa única linha, e os
    identificadores das turmas aparecem entre parênteses na descrição.
    Ex.: '7º Ano do Ensino Fundamental II (A e B)'
    """
    escola = dados.get('escola') or {}

    # Cabeçalho — CÓDIGO (INEP) e INSTITUIÇÃO
    _txt(can, 80,  height - 163.7, _val(escola, 'inep'))
    _txt(can, 190, height - 163.7, _val(escola, 'nome'))

    # ------ Tabela de cursos ------
    # Row 1: y_bot_pdf = 212.9  →  reportlab_y = height - 212.9
    # Cada linha seguinte: Δ ≈ 14.55 pts
    turmas   = dados.get('turmas', [])
    y_row1   = height - 212.9
    delta_y  = 14.55

    X_DESCRICAO  = 62.0
    X_TIPO       = 440.0
    X_MODALIDADE = 525.0

    # Agrupa turmas por série mantendo a ordem original
    grupos: Dict[str, List[str]] = {}
    ordem: List[str] = []
    for turma in turmas:
        serie = turma.get('serie_nome', '') if isinstance(turma, dict) else turma[3]
        tnome = turma.get('turma_nome', '') if isinstance(turma, dict) else turma[1]
        if serie not in grupos:
            grupos[serie] = []
            ordem.append(serie)
        grupos[serie].append(tnome)

    MAX_LINHAS = 36
    for i, serie_nome in enumerate(ordem[:MAX_LINHAS]):
        y       = y_row1 - i * delta_y
        descr   = _descricao_completa(serie_nome, grupos[serie_nome])
        _txt(can, X_DESCRICAO,  y, descr)
        _txt(can, X_TIPO,       y, str(_tipo_ensino(serie_nome)))
        _txt(can, X_MODALIDADE, y, str(_MODALIDADE_PADRAO))


# ---------------------------------------------------------------------------
# Parâmetros de posicionamento da tabela de estatísticas em instituicao.pdf.
# Altere apenas estes quatro valores para ajustar toda a tabela de uma vez:
#
#   _ESTAT_X0  — x da coluna Matutino (primeira coluna de dados)
#   _ESTAT_DX  — distância horizontal entre colunas  (Matutino → Vespertino)
#   _ESTAT_Y0  — y_reportlab da primeira linha (Alunos Matriculados)
#   _ESTAT_DY  — distância vertical entre linhas (valor positivo = para baixo)
#
# Ordem das linhas: Alunos, Vagas, Turmas, Professores, Funcionários
# y_reportlab = 841.9 - y_pdfplumber_top
# ---------------------------------------------------------------------------
_ESTAT_X0 = 146.0   # x da coluna Matutino
_ESTAT_DX = 30.0   # distância horizontal entre colunas (Mat → Ves)
_ESTAT_Y0 = 363.0   # y_reportlab da linha 0 (Alunos)
_ESTAT_DY =  15.0   # distância vertical entre linhas

# Calculado automaticamente — não editar manualmente
# Linhas (após troca de posição entre Alunos e Turmas):
#   0 → Turmas  |  1 → Vagas  |  2 → Alunos  |  3 → Professores  |  4 → Funcionários
# Colunas: Mat | Ves | traço | traço | Soma
_INST_POS: Dict[str, Tuple[float, float]] = {
    # ── Turmas (linha 0) ──
    'turmas_mat':  (_ESTAT_X0,                _ESTAT_Y0 - 0 * _ESTAT_DY),
    'turmas_ves':  (_ESTAT_X0 + _ESTAT_DX,   _ESTAT_Y0 - 0 * _ESTAT_DY),
    'turmas_c3':   (_ESTAT_X0 + 2 * _ESTAT_DX, _ESTAT_Y0 - 0 * _ESTAT_DY),
    'turmas_c4':   (_ESTAT_X0 + 3 * _ESTAT_DX, _ESTAT_Y0 - 0 * _ESTAT_DY),
    'turmas_soma': (_ESTAT_X0 + 4 * _ESTAT_DX, _ESTAT_Y0 - 0 * _ESTAT_DY),
    # ── Vagas (linha 1) ──
    'vagas_mat':   (_ESTAT_X0,                _ESTAT_Y0 - 1 * _ESTAT_DY),
    'vagas_ves':   (_ESTAT_X0 + _ESTAT_DX,   _ESTAT_Y0 - 1 * _ESTAT_DY),
    'vagas_c3':    (_ESTAT_X0 + 2 * _ESTAT_DX, _ESTAT_Y0 - 1 * _ESTAT_DY),
    'vagas_c4':    (_ESTAT_X0 + 3 * _ESTAT_DX, _ESTAT_Y0 - 1 * _ESTAT_DY),
    'vagas_soma':  (_ESTAT_X0 + 4 * _ESTAT_DX, _ESTAT_Y0 - 1 * _ESTAT_DY),
    # ── Alunos (linha 2) ──
    'alunos_mat':  (_ESTAT_X0,                _ESTAT_Y0 - 2 * _ESTAT_DY),
    'alunos_ves':  (_ESTAT_X0 + _ESTAT_DX,   _ESTAT_Y0 - 2 * _ESTAT_DY),
    'alunos_c3':   (_ESTAT_X0 + 2 * _ESTAT_DX, _ESTAT_Y0 - 2 * _ESTAT_DY),
    'alunos_c4':   (_ESTAT_X0 + 3 * _ESTAT_DX, _ESTAT_Y0 - 2 * _ESTAT_DY),
    'alunos_soma': (_ESTAT_X0 + 4 * _ESTAT_DX, _ESTAT_Y0 - 2 * _ESTAT_DY),
    # ── Professores (linha 3) ──
    'prof_mat':    (_ESTAT_X0,                _ESTAT_Y0 - 3 * _ESTAT_DY),
    'prof_ves':    (_ESTAT_X0 + _ESTAT_DX,   _ESTAT_Y0 - 3 * _ESTAT_DY),
    'prof_c3':     (_ESTAT_X0 + 2 * _ESTAT_DX, _ESTAT_Y0 - 3 * _ESTAT_DY),
    'prof_c4':     (_ESTAT_X0 + 3 * _ESTAT_DX, _ESTAT_Y0 - 3 * _ESTAT_DY),
    'prof_soma':   (_ESTAT_X0 + 4 * _ESTAT_DX, _ESTAT_Y0 - 3 * _ESTAT_DY),
    # ── Funcionários (linha 4) ──
    'func_mat':    (_ESTAT_X0,                _ESTAT_Y0 - 4 * _ESTAT_DY),
    'func_ves':    (_ESTAT_X0 + _ESTAT_DX,   _ESTAT_Y0 - 4 * _ESTAT_DY),
    'func_c3':     (_ESTAT_X0 + 2 * _ESTAT_DX, _ESTAT_Y0 - 4 * _ESTAT_DY),
    'func_c4':     (_ESTAT_X0 + 3 * _ESTAT_DX, _ESTAT_Y0 - 4 * _ESTAT_DY),
    'func_soma':   (_ESTAT_X0 + 4 * _ESTAT_DX, _ESTAT_Y0 - 4 * _ESTAT_DY),
}


def _soma(a: Any, b: Any) -> str:
    """Soma dois valores que podem ser string, int ou vazio; retorna string."""
    try:
        return str(int(a or 0) + int(b or 0))
    except (ValueError, TypeError):
        return ''


def _escrever_valores_estatisticas(
        can: canvas.Canvas, dados: Dict[str, Any]) -> None:
    """
    Escreve os valores das estatísticas escolares em instituicao.pdf.

    Colunas: Matutino | Vespertino | - | - | Soma
    Linhas (ordem atual): Turmas | Vagas | Alunos | Professores | Funcionários

    As posições são definidas em _INST_POS (calculado a partir de _ESTAT_*).
    """
    estat = dados.get('estatisticas') or {}

    alunos_mat = estat.get('alunos_mat', '')
    alunos_ves = estat.get('alunos_ves', '')
    prof_mat   = estat.get('prof_mat',   '')
    prof_ves   = estat.get('prof_ves',   '')
    func_mat   = estat.get('func_mat',   '')
    func_ves   = estat.get('func_ves',   '')
    vagas_mat  = dados.get('vagas_mat',  150)
    vagas_ves  = dados.get('vagas_ves',  180)
    turmas_mat = dados.get('turmas_mat', 5)
    turmas_ves = dados.get('turmas_ves', 5)

    valores = {
        # ── Turmas ──
        'turmas_mat':  str(turmas_mat),
        'turmas_ves':  str(turmas_ves),
        'turmas_c3':   '-',
        'turmas_c4':   '-',
        'turmas_soma': _soma(turmas_mat, turmas_ves),
        # ── Vagas ──
        'vagas_mat':   str(vagas_mat),
        'vagas_ves':   str(vagas_ves),
        'vagas_c3':    '-',
        'vagas_c4':    '-',
        'vagas_soma':  _soma(vagas_mat, vagas_ves),
        # ── Alunos ──
        'alunos_mat':  str(alunos_mat),
        'alunos_ves':  str(alunos_ves),
        'alunos_c3':   '-',
        'alunos_c4':   '-',
        'alunos_soma': _soma(alunos_mat, alunos_ves),
        # ── Professores ──
        'prof_mat':    str(prof_mat),
        'prof_ves':    str(prof_ves),
        'prof_c3':     '-',
        'prof_c4':     '-',
        'prof_soma':   _soma(prof_mat, prof_ves),
        # ── Funcionários ──
        'func_mat':    str(func_mat),
        'func_ves':    str(func_ves),
        'func_c3':     '-',
        'func_c4':     '-',
        'func_soma':   _soma(func_mat, func_ves),
    }

    can.setFillColor(black)
    can.setFont('Helvetica-Bold', 9)
    for chave, valor in valores.items():
        if chave in _INST_POS and valor:
            x, y = _INST_POS[chave]
            can.drawString(x, y, valor)


def _preencher_instituicao(can: canvas.Canvas, height: float, dados: Dict[str, Any]) -> None:
    """
    Preenche o template instituicao.pdf.

    Campos preenchidos (coordenadas mapeadas do PDF original):
      CNPJ        → 14 células individuais (y_bot_pdf = 176.50)
                    cada dígito centrado em sua célula
      CÓDIGO / DATA RECADASTRO → NÃO preenchidos (área RESERVADO À SMTT)
      INSTITUIÇÃO → x≈87,  y_bot_pdf=221.0
      ENDEREÇO    → x≈88,  y_bot_pdf=239.8
      BAIRRO      → x≈90,  y_bot_pdf=258.7
      MUNICÍPIO   → x≈381, y_bot_pdf=258.7
      CEP         → x≈90,  y_bot_pdf=277.4
      TELEFONE    → x≈381, y_bot_pdf=277.4
      EMAIL       → x≈90,  y_bot_pdf=296.1  (fixo: uebnadirnascimento@gmail.com)
      TABELA      → área y_pdf 297–528 (estatísticas escolares)
      DIRETOR     → x≈102, y_bot_pdf=642.2
    """
    escola = dados.get('escola') or {}
    gestor = dados.get('gestor') or {}

    # ── CNPJ: cada DÍGITO em sua célula individual ──
    cnpj_digitos = ''.join(c for c in _val(escola, 'cnpj') if c.isdigit())
    for idx, digito in enumerate(cnpj_digitos[:14]):
        x_center = _CNPJ_X_CENTERS[idx]
        can.setFont('Helvetica-Bold', 9)
        can.drawCentredString(x_center, _CNPJ_Y_RL, digito)

    # ── CÓDIGO e DATA RECADASTRO são RESERVADOS À SMTT — não preencher ──

    # INSTITUIÇÃO  (y_bot_pdf = 221.0)
    _txt(can, 87,  height - 221.0, _val(escola, 'nome'))

    # ENDEREÇO  (y_bot_pdf = 239.8)
    _txt(can, 88,  height - 239.8, _val(escola, 'endereco'))

    # BAIRRO e MUNICÍPIO  (y_bot_pdf = 258.7)
    _txt(can, 90,  height - 258.7, _val(escola, 'bairro'))
    _txt(can, 381, height - 258.7, _val(escola, 'municipio'))

    # CEP e TELEFONE  (y_bot_pdf = 277.4)
    _txt(can, 90,  height - 277.4, _val(escola, 'cep'))
    _txt(can, 381, height - 277.4, _val(escola, 'telefone'))

    # EMAIL  (fixo — y_bot_pdf = 296.1)
    _txt(can, 90,  height - 296.1, 'uebnadirnascimento@gmail.com')

    # Valores numéricos das estatísticas (posições em _INST_POS)
    _escrever_valores_estatisticas(can, dados)

    # Nome do Diretor/Reitor  (y_bot_pdf = 642.2)
    _txt(can, 102, height - 642.2, _val(gestor, 'nome'))


def _preencher_representante(can: canvas.Canvas, height: float, dados: Dict[str, Any]) -> None:
    """
    Preenche o template representante.pdf.

    Campos preenchidos (coordenadas mapeadas do PDF original):
      CÓDIGO          → x≈72,  y≈637  (INEP da escola)
      INSTITUIÇÃO     → x≈180, y≈637  (nome da escola)
      CPF             → x≈59,  y≈586
      RG              → x≈200, y≈586
      ÓRG. EXP.       → x≈366, y≈586
      DT. EXPEDIÇÃO   → x≈483, y≈586
      REPRESENTANTE   → x≈100, y≈566  (nome do gestor)
      CARGO/FUNÇÃO    → x≈99,  y≈546
      ENDEREÇO        → x≈79,  y≈513
      BAIRRO          → x≈77,  y≈493
      CEP             → x≈275, y≈493
      MUNICÍPIO       → x≈406, y≈493
      TELEFONE        → x≈79,  y≈473
      E-MAIL          → x≈197, y≈473
    """
    escola = dados.get('escola') or {}
    gestor = dados.get('gestor') or {}

    # Seção Instituição de Ensino  (y_bot_pdf = 204.8)
    _txt(can, 72,  height - 204.8, _val(escola, 'inep'))
    _txt(can, 180, height - 204.8, _val(escola, 'nome'))

    # Dados do representante  (y_bot_pdf = 255.7)
    _txt(can, 59,  height - 255.7, _val(gestor, 'cpf'))
    _txt(can, 200, height - 255.7, _val(gestor, 'rg'))
    _txt(can, 366, height - 255.7, _val(gestor, 'orgao_expedidor'))

    # Data de expedição  (formata data se disponível)
    data_exp = gestor.get('data_expedicao_rg')
    if data_exp:
        try:
            data_exp_str = data_exp.strftime('%d/%m/%Y') if hasattr(data_exp, 'strftime') else str(data_exp)
        except Exception:
            data_exp_str = str(data_exp)
    else:
        data_exp_str = ''
    _txt(can, 483, height - 255.7, data_exp_str)

    # Nome do representante  (y_bot_pdf = 275.6)
    _txt(can, 100, height - 275.6, _val(gestor, 'nome'))

    # Cargo / Função  (y_bot_pdf = 295.5)
    cargo_funcao = _val(gestor, 'cargo')
    funcao = _val(gestor, 'funcao')
    if funcao:
        cargo_funcao = f"{cargo_funcao} / {funcao}" if cargo_funcao else funcao
    _txt(can, 99,  height - 295.5, cargo_funcao)

    # Endereço do representante  (y_bot_pdf = 329.4)
    endereco_rep = _val(gestor, 'endereco_logradouro')
    num = _val(gestor, 'endereco_numero')
    if num:
        endereco_rep = f"{endereco_rep}, {num}" if endereco_rep else num
    _txt(can, 79,  height - 329.4, endereco_rep)

    # Bairro, CEP, Município  (y_bot_pdf = 349.3)
    _txt(can, 77,  height - 349.3, _val(gestor, 'endereco_bairro'))
    _txt(can, 275, height - 349.3, _val(gestor, 'endereco_cep'))
    municipio = _val(gestor, 'endereco_cidade') or _val(escola, 'municipio')
    _txt(can, 406, height - 349.3, municipio)

    # Telefone e E-mail  (y_bot_pdf = 369.2)
    _txt(can, 79,  height - 369.2, _val(gestor, 'telefone'))
    _txt(can, 197, height - 369.2, _val(gestor, 'email'))


# ---------------------------------------------------------------------------
# Overlay genérico
# ---------------------------------------------------------------------------

def criar_overlay_preenchido(template_path: str, dados: Dict[str, Any]) -> io.BytesIO:
    """
    Cria um overlay PDF com os dados preenchidos sobre o template.

    Args:
        template_path: Caminho do template PDF original
        dados: Dicionário com dados para preencher

    Returns:
        BytesIO com o PDF do overlay.
    """
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    _, height = A4  # 595.3 x 841.9 pts

    nome_arquivo = os.path.basename(template_path).lower()
    can.setFillColor(black)

    if 'curso' in nome_arquivo:
        _preencher_curso(can, height, dados)
    elif 'instituicao' in nome_arquivo:
        _preencher_instituicao(can, height, dados)
    elif 'representante' in nome_arquivo:
        _preencher_representante(can, height, dados)

    can.save()
    packet.seek(0)
    return packet


def preencher_pdf(template_path: str, output_path: str, dados: Dict[str, Any]) -> bool:
    """
    Mescla o overlay de dados sobre o template PDF e salva o resultado.

    Args:
        template_path: Caminho do template PDF original
        output_path:   Caminho onde salvar o PDF preenchido
        dados:         Dicionário com dados para preencher

    Returns:
        True se sucesso, False caso contrário.
    """
    try:
        if not os.path.exists(template_path):
            logger.error(f"Template não encontrado: {template_path}")
            return False

        template_pdf = PdfReader(template_path)
        overlay_packet = criar_overlay_preenchido(template_path, dados)
        overlay_pdf = PdfReader(overlay_packet)

        output_pdf = PdfWriter()
        for page_num in range(len(template_pdf.pages)):
            page = template_pdf.pages[page_num]
            if page_num < len(overlay_pdf.pages):
                page.merge_page(overlay_pdf.pages[page_num])
            output_pdf.add_page(page)

        with open(output_path, 'wb') as f:
            output_pdf.write(f)

        logger.info(f"PDF preenchido salvo: {output_path}")
        return True

    except Exception as e:
        logger.exception(f"Erro ao preencher PDF: {e}")
        return False


def gerar_documentos_smtt(escola_id: int = 60) -> Tuple[int, int]:
    """
    Gera todos os documentos SMTT preenchidos.

    Dados coletados do banco:
      - dados da escola  (nome, endereço, CNPJ, INEP, etc.)
      - dados do gestor geral  (nome, CPF, RG, e-mail, cargo, endereço, etc.)
      - séries da escola no ano letivo atual  (para tabela de cursos)

    Args:
        escola_id: ID da escola (padrão: 60)

    Returns:
        Tupla (sucesso, total) com quantidade de arquivos gerados e total.
    """
    try:
        logger.info("Buscando dados do sistema para SMTT...")

        dados_ano = buscar_dados_ano_letivo()
        if not dados_ano:
            messagebox.showerror("Erro", "Ano letivo atual não encontrado no sistema.")
            return (0, 0)

        escola = buscar_dados_escola(escola_id)
        if not escola:
            messagebox.showwarning("Aviso", "Dados da escola não encontrados. Os documentos serão gerados sem essas informações.")

        gestor = buscar_gestor_geral(escola_id)
        if not gestor:
            messagebox.showwarning("Aviso", "Gestor geral não encontrado. Os documentos serão gerados sem essas informações.")

        ano_letivo_id = dados_ano.get('id') if dados_ano else None

        turmas = buscar_turmas_escola(escola_id, ano_letivo_id)
        if not turmas:
            messagebox.showwarning("Aviso", "Nenhuma turma encontrada para o ano letivo atual.")

        estatisticas = buscar_estatisticas_escola(escola_id, ano_letivo_id)

        ano_letivo = dados_ano.get('ano_letivo', ANO_LETIVO_ATUAL) if dados_ano else ANO_LETIVO_ATUAL

        dados = {
            'ano_letivo':    ano_letivo,
            'escola':        escola,
            'gestor':        gestor,
            'turmas':        turmas,          # usado em curso.pdf (1 linha por turma)
            'estatisticas':  estatisticas,    # usado em instituicao.pdf
            # Valores fixos para a tabela de instituicao.pdf
            'vagas_mat':     150,
            'vagas_ves':     180,
            'turmas_mat':    5,
            'turmas_ves':    5,
            'data_geracao':  datetime.now().strftime('%d/%m/%Y'),
        }

        pasta_smtt  = os.path.join(PROJECT_ROOT, 'SMTT')
        pasta_saida = os.path.join(PROJECT_ROOT, 'documentos_gerados', 'SMTT')
        os.makedirs(pasta_saida, exist_ok=True)

        templates = ['curso.pdf', 'instituicao.pdf', 'representante.pdf']
        sucesso = 0
        total = len(templates)

        for template_nome in templates:
            template_path = os.path.join(pasta_smtt, template_nome)
            if not os.path.exists(template_path):
                logger.warning(f"Template não encontrado: {template_path}")
                continue

            nome_base   = template_nome.replace('.pdf', '')
            output_nome = f"{nome_base}_preenchido_{ano_letivo}.pdf"
            output_path = os.path.join(pasta_saida, output_nome)

            logger.info(f"Processando {template_nome}...")
            if preencher_pdf(template_path, output_path, dados):
                sucesso += 1
                logger.info(f"✓ {template_nome} processado com sucesso")
            else:
                logger.error(f"✗ Erro ao processar {template_nome}")

        if sucesso > 0:
            messagebox.showinfo(
                "Sucesso",
                f"Documentos SMTT gerados com sucesso!\n\n"
                f"Processados: {sucesso} de {total}\n"
                f"Pasta: {pasta_saida}"
            )
            import webbrowser
            webbrowser.open(pasta_saida)
        else:
            messagebox.showerror(
                "Erro",
                "Nenhum documento foi gerado com sucesso.\n"
                "Verifique os logs para mais detalhes."
            )

        return (sucesso, total)

    except Exception as e:
        logger.exception(f"Erro ao gerar documentos SMTT: {e}")
        messagebox.showerror("Erro", f"Erro ao gerar documentos SMTT:\n{str(e)}")
        return (0, 0)


def abrir_interface_smtt():
    """
    Interface simples para gerar documentos SMTT.
    Pode ser expandida futuramente para permitir seleções.
    """
    try:
        from tkinter import Toplevel, Label, Button, Frame
        import tkinter as tk
        
        # Criar janela
        janela = Toplevel()
        janela.title("Gerar Documentos SMTT")
        janela.geometry("450x250")
        janela.resizable(False, False)
        
        # Centralizar janela
        janela.update_idletasks()
        width = janela.winfo_width()
        height = janela.winfo_height()
        x = (janela.winfo_screenwidth() // 2) - (width // 2)
        y = (janela.winfo_screenheight() // 2) - (height // 2)
        janela.geometry(f'{width}x{height}+{x}+{y}')
        
        # Frame principal
        frame = Frame(janela, padx=20, pady=20)
        frame.pack(expand=True, fill='both')
        
        # Título
        titulo = Label(
            frame,
            text="Gerar Documentos SMTT",
            font=('Arial', 14, 'bold')
        )
        titulo.pack(pady=(0, 15))
        
        # Descrição
        descricao = Label(
            frame,
            text="Os documentos serão preenchidos com:\n\n"
                 f"• Ano Letivo: {ANO_LETIVO_ATUAL}\n"
                 "• Dados da Escola (CNPJ, endereço, etc.)\n"
                 "• Dados do Gestor Geral (CPF, RG, e-mail, etc.)\n"
                 "• Séries / Cursos da Escola",
            font=('Arial', 10),
            justify='left'
        )
        descricao.pack(pady=10)
        
        # Função para gerar
        def gerar():
            janela.destroy()
            gerar_documentos_smtt()
        
        # Botões
        frame_botoes = Frame(frame)
        frame_botoes.pack(pady=20)
        
        btn_gerar = Button(
            frame_botoes,
            text="Gerar Documentos",
            command=gerar,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=10
        )
        btn_gerar.pack(side='left', padx=5)
        
        btn_cancelar = Button(
            frame_botoes,
            text="Cancelar",
            command=janela.destroy,
            bg='#f44336',
            fg='white',
            font=('Arial', 10),
            padx=20,
            pady=10
        )
        btn_cancelar.pack(side='left', padx=5)
        
    except Exception as e:
        logger.exception(f"Erro ao abrir interface SMTT: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir interface:\n{str(e)}")


if __name__ == "__main__":
    # Teste
    gerar_documentos_smtt()
