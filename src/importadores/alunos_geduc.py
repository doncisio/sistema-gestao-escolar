"""
Interface gráfica para extração, comparação e importação de alunos do GEDUC.

Fluxo:
1. (Etapa 1 — opcional) Usuário informa credenciais do GEDUC;
   o Selenium abre o Chrome, faz login, coleta todas as turmas/alunos
   e salva em 'alunos_geduc.json'. Logs são exibidos em tempo real.
   Ao concluir, a comparação (Etapa 2) é iniciada automaticamente.

2. (Etapa 2) Lê o arquivo JSON (gerado na Etapa 1 ou selecionado manualmente)
   e compara com as matrículas ativas do ano letivo corrente (escola_id=60).

3. Exibe em tabela os alunos presentes no GEDUC mas sem matrícula local,
   com dados de nome, nascimento, sexo, CPF, raça, turma e responsáveis.

4. Usuário seleciona os alunos desejados (individualmente ou todos),
   escolhe a turma de destino e clica em "Inserir Selecionados".
   Os dados são normalizados (capitalização, CPF, datas, raça→enum)
   e os responsáveis são inseridos sem duplicatas (dedup por CPF e nome).

5. Após a inserção, a comparação é refeita automaticamente para
   atualizar a lista (alunos recém-inseridos somem da tabela).

Acesso: Menu Principal → Serviços → 📥 Importar Alunos do GEDUC
"""

import os
import re
import sys
import io
import json
import logging
import unicodedata
import threading
import datetime
import queue as _queue_mod
from pathlib import Path
from typing import Optional, Dict, List

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ─── caminho raiz ──────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import mysql.connector

from db.connection import conectar_bd
from src.core.config_logs import get_logger

logger = get_logger(__name__)

# ─── cores padrão do sistema ──────────────────────────────────────────────────
CO0 = "#F5F5F5"   # fundo
CO1 = "#003A70"   # azul escuro
CO2 = "#77B341"   # verde
CO3 = "#E74C3C"   # vermelho
CO4 = "#4A86E8"   # azul claro
CO_LINHA_PAR  = "#EBF3FA"
CO_LINHA_IMPAR = "#FFFFFF"

# ─── mapeamentos ──────────────────────────────────────────────────────────────
_PREPOSICOES = {'de', 'da', 'das', 'do', 'dos', 'e', 'em', 'a', 'o', 'ao'}

# Mapa de nome completo do estado (conforme GEDUC) → sigla UF (char(2))
_MAPA_NOME_SIGLA: Dict[str, str] = {
    'Acre': 'AC', 'Alagoas': 'AL', 'Amapa': 'AP', 'Amazonas': 'AM',
    'Bahia': 'BA', 'Ceara': 'CE', 'Distrito Federal': 'DF',
    'Espirito Santo': 'ES', 'Goias': 'GO', 'Maranhao': 'MA',
    'Mato Grosso': 'MT', 'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG',
    'Para': 'PA', 'Paraiba': 'PB', 'Parana': 'PR', 'Pernambuco': 'PE',
    'Piaui': 'PI', 'Rio de Janeiro': 'RJ', 'Rio Grande do Norte': 'RN',
    'Rio Grande do Sul': 'RS', 'Rondonia': 'RO', 'Roraima': 'RR',
    'Santa Catarina': 'SC', 'Sao Paulo': 'SP', 'Sergipe': 'SE',
    'Tocantins': 'TO',
}


def _estado_para_sigla(valor) -> Optional[str]:
    """Converte nome completo de estado ou código IBGE para sigla UF de 2 chars."""
    if not valor or str(valor).strip() in ('', 'None', '00', '0'):
        return None
    v = str(valor).strip()
    if len(v) == 2 and v.isalpha():
        return v.upper()  # já é sigla
    # lookup por nome sem acento (uppercase)
    sem_ac = ''.join(
        c for c in unicodedata.normalize('NFD', v)
        if unicodedata.category(c) != 'Mn'
    ).title()
    return _MAPA_NOME_SIGLA.get(sem_ac) or _MAPA_NOME_SIGLA.get(v) or None

MAPA_SEXO = {'1': 'M', '2': 'F', 'M': 'M', 'F': 'F'}

MAPA_RACA_ENUM = {
    'Branca': 'branco', 'Preta': 'preto', 'Parda': 'pardo',
    'Amarela': 'amarelo', 'Indígena': 'indígena', 'Não declarada': 'pardo',
}

JSON_PADRAO = str(ROOT_DIR / 'alunos_geduc.json')


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _normalizar(nome: str) -> str:
    if not nome:
        return ''
    nome = unicodedata.normalize('NFKD', str(nome)).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', nome.strip().upper())


# Dicionário de palavras que precisam de acento/cedilha (chave = sem acento, CAPS)
_PALAVRAS_MUNICIPIO: dict = {
    'DE': 'de', 'DO': 'do', 'DA': 'da', 'DOS': 'dos', 'DAS': 'das', 'E': 'e',
    'SAO': 'São', 'JOSE': 'José', 'JOAO': 'João',
    'LUIS': 'Luís', 'LUIZ': 'Luiz',
    'PACO': 'Paço', 'ACAILANDIA': 'Açailândia',
    'GONCALO': 'Gonçalo', 'MARANHAO': 'Maranhão',
    'BELEM': 'Belém', 'MACAPA': 'Macapá', 'AMAPA': 'Amapá',
    'PARNAIBA': 'Parnaíba',
    'CODO': 'Codó', 'TURIACU': 'Turiaçu', 'ICATU': 'Icatu',
    'ACARA': 'Açará', 'BRASILIA': 'Brasília', 'GOIANIA': 'Goiânia',
    'RIBEIRAO': 'Ribeirão', 'SANTAREM': 'Santarém', 'BRAGANCA': 'Bragança',
    'INES': 'Inês', 'ALCANTARA': 'Alcântara', 'VARZEA': 'Várzea',
    'FLORIANOPOLIS': 'Florianópolis', 'TUCURUI': 'Tucuruí',
    'SERTAOZINHO': 'Sertãozinho', 'PARAUAPEBAS': 'Parauapebas',
}


def _normalizar_municipio(texto) -> Optional[str]:
    """Normaliza nome de município: remove sufixo '- UF', descarta inválidos,
    aplica capitalização correta com acentos/cedilha."""
    if not texto or str(texto).strip() in ('', 'None', '00', '0'):
        return None
    texto = str(texto).strip()
    if ' - ' in texto:
        texto = texto.split(' - ')[0].strip()
    palavras = texto.split()
    resultado = []
    for i, palavra in enumerate(palavras):
        # normaliza para lookup: remove acentos, uppercase
        chave = ''.join(
            c for c in unicodedata.normalize('NFD', palavra)
            if unicodedata.category(c) != 'Mn'
        ).upper()
        if chave in _PALAVRAS_MUNICIPIO:
            forma = _PALAVRAS_MUNICIPIO[chave]
            if i == 0 and forma[0].islower():
                forma = forma[0].upper() + forma[1:]
            resultado.append(forma)
        else:
            resultado.append(palavra.capitalize())
    return ' '.join(resultado)


def _capitalizar(nome: str) -> str:
    if not nome:
        return ''
    return ' '.join(
        p.capitalize() if i == 0 or p.lower() not in _PREPOSICOES else p.lower()
        for i, p in enumerate(nome.strip().split())
    )


def _formatar_cpf(cpf: str) -> Optional[str]:
    if not cpf:
        return None
    d = re.sub(r'\D', '', str(cpf))
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}" if len(d) == 11 else (d or None)


def _formatar_tel(tel: str) -> str:
    if not tel:
        return ''
    d = re.sub(r'\D', '', str(tel))
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return tel


class _LogCapture(logging.Handler):
    """Repassa registros de log para uma Queue — usada para exibir progresso na UI."""

    def __init__(self, q: _queue_mod.Queue):
        super().__init__()
        self._q = q

    def emit(self, record: logging.LogRecord):
        try:
            self._q.put_nowait(self.format(record))
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  LÓGICA DE COMPARAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

def carregar_json_geduc(caminho: str) -> Dict:
    """Carrega e valida o arquivo JSON do GEDUC."""
    with open(caminho, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    if 'turmas' not in dados:
        raise ValueError("Formato de JSON inválido: chave 'turmas' ausente.")
    return dados


def obter_alunos_locais_ativos(escola_id: int = 60) -> Dict[str, int]:
    """
    Retorna dicionário {nome_normalizado: aluno_id} de todos os alunos
    com matrícula ativa no ano letivo corrente da escola informada.
    """
    conn = conectar_bd()
    cursor = conn.cursor(buffered=True)
    try:
        # Obter ano letivo corrente (maior ano_letivo ativo)
        cursor.execute(
            "SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1"
        )
        row = cursor.fetchone()
        ano_letivo_id = row[0] if row else None

        if not ano_letivo_id:
            return {}

        cursor.execute("""
            SELECT a.id, a.nome
            FROM alunos a
            INNER JOIN matriculas m ON m.aluno_id = a.id
            WHERE m.status = 'Ativo'
              AND m.ano_letivo_id = %s
              AND a.escola_id = %s
        """, (ano_letivo_id, escola_id))
        return {_normalizar(nome): aid for aid, nome in cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


def obter_turmas_alunos_locais(escola_id: int = 60) -> Dict[str, str]:
    """
    Retorna {nome_normalizado: descricao_turma} para todos os alunos
    com matrícula ativa no ano letivo corrente.
    descricao_turma = '{série} {nome_turma}'.strip(), ex: '3º Ano', '7º Ano A'.
    """
    conn = conectar_bd()
    cursor = conn.cursor(buffered=True)
    try:
        cursor.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
        row = cursor.fetchone()
        ano_letivo_id = row[0] if row else None
        if not ano_letivo_id:
            return {}
        cursor.execute("""
            SELECT a.nome,
                   TRIM(CONCAT(s.nome, IF(t.nome != '', CONCAT(' ', t.nome), '')))
            FROM alunos a
            INNER JOIN matriculas m ON m.aluno_id = a.id
            INNER JOIN turmas t    ON t.id = m.turma_id
            INNER JOIN series s    ON s.id = t.serie_id
            WHERE m.status = 'Ativo'
              AND m.ano_letivo_id = %s
              AND a.escola_id = %s
        """, (ano_letivo_id, escola_id))
        return {_normalizar(nome): desc for nome, desc in cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


def obter_dados_locais_completos(escola_id: int = 60) -> Dict[str, Dict]:
    """
    Retorna {nome_normalizado: row_dict} para todos os alunos com matrícula ativa
    no ano letivo corrente, incluindo campos de dados pessoais e endereço.
    """
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        cursor.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
        row = cursor.fetchone()
        ano_letivo_id = row['id'] if row else None
        if not ano_letivo_id:
            return {}
        cursor.execute("""
            SELECT a.id, a.nome, a.data_nascimento, a.sexo, a.cpf, a.raca,
                   a.local_nascimento, a.UF_nascimento,
                   a.endereco, a.descricao_transtorno
            FROM alunos a
            INNER JOIN matriculas m ON m.aluno_id = a.id
            WHERE m.status = 'Ativo' AND m.ano_letivo_id = %s AND a.escola_id = %s
        """, (ano_letivo_id, escola_id))
        return {_normalizar(r['nome']): r for r in cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


def comparar_divergencias_geduc_local(dados_json: Dict, escola_id: int = 60) -> List[Dict]:
    """
    Retorna lista de alunos presentes tanto no GEDUC quanto localmente,
    mas com dados divergentes. Cada item indica quais campos diferem.
    """
    locais = obter_dados_locais_completos(escola_id)
    divergencias = []

    for turma in dados_json.get('turmas', []):
        turma_id_geduc   = turma.get('id', '')
        turma_nome_geduc = turma.get('nome', '')
        for aluno in turma.get('alunos', []):
            nome_norm = _normalizar(aluno.get('nome', ''))
            if not nome_norm or nome_norm not in locais:
                continue  # não existe localmente — tratado por comparar_geduc_local
            local = locais[nome_norm]

            # Valores GEDUC já convertidos para o mesmo formato do banco local
            sexo_raw = aluno.get('sexo')
            geduc_conv = {
                'data_nascimento':    aluno.get('data_nascimento', ''),
                'sexo':               MAPA_SEXO.get(str(sexo_raw), '') if sexo_raw else '',
                'cpf':                _formatar_cpf(aluno.get('cpf', '')),
                'raca':               MAPA_RACA_ENUM.get(aluno.get('raca', 'Não declarada'), 'pardo'),
                'local_nascimento':   _normalizar_municipio(aluno.get('local_nascimento')),
                'descricao_transtorno': aluno.get('descricao_transtorno', 'Nenhum'),
            }

            diffs = []
            for campo, label in [
                ('data_nascimento', 'Nascimento'),
                ('sexo',            'Sexo ⚠️(pend.)'),
                ('cpf',             'CPF'),
                ('raca',            'Raça'),
                ('local_nascimento','Naturalidade'),
                ('descricao_transtorno', 'Transtorno'),
            ]:
                v_geduc = str(geduc_conv.get(campo, '') or '').strip().upper()
                v_local = str(local.get(campo, '') or '').strip().upper()
                if v_geduc and v_local != v_geduc:
                    diffs.append(f"{label}: [{v_local or '—'}] → [{v_geduc}]")
            if diffs:
                divergencias.append({
                    'aluno_id':          local['id'],
                    'nome_fmt':          _capitalizar(aluno.get('nome', '')),
                    'campos_diff':       ' | '.join(diffs),
                    'num_diffs':         len(diffs),
                    'turma_geduc_id':    turma_id_geduc,
                    'turma_geduc_nome':  turma_nome_geduc,
                    # campos GEDUC para atualização
                    # sexo: visível na comparação mas NÃO atualizado no banco (possível erro no GEDUC)
                    'data_nascimento':   aluno.get('data_nascimento', ''),
                    'sexo':              None,  # pendente: não atualizar
                    'cpf_fmt':           _formatar_cpf(aluno.get('cpf', '')),
                    'raca_enum':         MAPA_RACA_ENUM.get(aluno.get('raca', 'Não declarada'), 'pardo'),
                    'local_nascimento':  _normalizar_municipio(aluno.get('local_nascimento')),
                    'codigo_estado':     _estado_para_sigla(aluno.get('codigo_estado')),
                    'logradouro':        aluno.get('logradouro', ''),
                    'numero_end':        aluno.get('numero_end', ''),
                    'bairro':            aluno.get('bairro', ''),
                    'municipio_res':     aluno.get('municipio_res', ''),
                    'uf_res':            aluno.get('uf_res', ''),
                    'cep':               aluno.get('cep', ''),
                    'descricao_transtorno': aluno.get('descricao_transtorno', 'Nenhum'),
                })

    return divergencias


def gerar_pdf_pendencias_geduc(pendencias: List[Dict]) -> None:
    """Gera e abre um PDF com a lista de pendências do GEDUC no padrão das listas do sistema."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.colors import black, white, grey, HexColor
        from src.core.config import get_image_path
    except Exception as e:
        raise RuntimeError(f"ReportLab não disponível: {e}")

    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]
    figura_inferior = str(get_image_path('logopaco.png'))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=36, rightMargin=18, topMargin=10, bottomMargin=18
    )
    elements = []

    # ── Cabeçalho ─────────────────────────────────────────────────────────
    def _header_table():
        import os as _os
        img_cell = Image(figura_inferior, width=3 * inch, height=0.7 * inch) \
            if figura_inferior and _os.path.exists(figura_inferior) else Spacer(1, 0.7 * inch)
        data = [
            [img_cell],
            [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
        ]
        t = Table(data, colWidths=[7.5 * inch])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN',  (0, 0), (-1, -1), 'CENTER')
        ]))
        return t

    # ── Capa ───────────────────────────────────────────────────────────────
    elements.append(_header_table())
    elements.append(Spacer(1, 2 * inch))
    elements.append(Paragraph(
        "<b>PENDÊNCIAS DE DADOS — GEDUC</b>",
        ParagraphStyle(name='Capa', fontSize=22, alignment=1)
    ))
    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph(
        f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}  |  Total: {len(pendencias)} alunos",
        ParagraphStyle(name='Sub', fontSize=11, alignment=1)
    ))
    elements.append(PageBreak())

    # ── Tabela de pendências ───────────────────────────────────────────────
    elements.append(_header_table())
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(
        f"<b>PENDÊNCIAS DE DADOS — GEDUC</b>",
        ParagraphStyle(name='Titulo', fontSize=13, alignment=1, spaceAfter=6)
    ))
    elements.append(Spacer(1, 0.15 * inch))

    # Estilos de célula
    st_hdr = ParagraphStyle('th', fontSize=9,  fontName='Helvetica-Bold', textColor=white, alignment=1)
    st_cel = ParagraphStyle('td', fontSize=8,  fontName='Helvetica', alignment=0, leading=10)
    st_num = ParagraphStyle('tn', fontSize=8,  fontName='Helvetica', alignment=1)

    COL_N   = 0.40 * inch
    COL_NOM = 2.00 * inch
    COL_TRM = 1.20 * inch
    COL_QTD = 0.40 * inch
    COL_CAM = 7.5 * inch - COL_N - COL_NOM - COL_TRM - COL_QTD

    rows = [[
        Paragraph("Nº",              st_hdr),
        Paragraph("Nome do Aluno",   st_hdr),
        Paragraph("Turma",           st_hdr),
        Paragraph("Qtd",             st_hdr),
        Paragraph("Campos Pendentes", st_hdr),
    ]]
    for i, p in enumerate(pendencias, 1):
        rows.append([
            Paragraph(str(i),                   st_num),
            Paragraph(p['nome_fmt'],             st_cel),
            Paragraph(p.get('turma_fmt', '—'),  st_cel),
            Paragraph(str(p['num_pend']),        st_num),
            Paragraph(p['campos_pend'].replace(' | ', '<br/>'), st_cel),
        ])

    tabela = Table(rows, colWidths=[COL_N, COL_NOM, COL_TRM, COL_QTD, COL_CAM], repeatRows=1)
    tabela.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND',   (0, 0), (-1, 0), HexColor('#003A70')),
        ('TEXTCOLOR',    (0, 0), (-1, 0), white),
        ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, 0), 9),
        ('ALIGN',        (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING',(0, 0), (-1, 0), 5),
        ('TOPPADDING',   (0, 0), (-1, 0), 5),
        # Linhas de dados
        ('FONTNAME',     (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',     (0, 1), (-1, -1), 8),
        ('VALIGN',       (0, 1), (-1, -1), 'TOP'),
        ('TOPPADDING',   (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING',(0, 1), (-1, -1), 3),
        # Zebra
        *[('BACKGROUND', (0, r), (-1, r), HexColor('#EBF3FA'))
          for r in range(1, len(rows)) if r % 2 == 0],
        # Grade
        ('GRID',         (0, 0), (-1, -1), 0.25, grey),
        ('BOX',          (0, 0), (-1, -1), 0.5,  black),
    ]))
    elements.append(tabela)
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(
        f"Total de alunos com pendências: <b>{len(pendencias)}</b>",
        ParagraphStyle(name='Rodape', fontSize=9, alignment=2)
    ))

    doc.build(elements)
    buffer.seek(0)

    try:
        from src.relatorios.gerar_pdf import salvar_e_abrir_pdf as _salvar
        _salvar(buffer)
    except Exception:
        import tempfile, subprocess
        fd, path = tempfile.mkstemp(suffix='.pdf', prefix='pendencias_geduc_')
        with open(path, 'wb') as f:
            f.write(buffer.getvalue())
        os.close(fd)
        try:
            os.startfile(path)
        except Exception:
            subprocess.Popen(['start', '', path], shell=True)


def atualizar_aluno_geduc(aluno_id: int, dados: Dict) -> Dict:
    conn = conectar_bd()
    cursor = conn.cursor(buffered=True)
    try:
        logradouro = dados.get('logradouro') or ''
        numero     = dados.get('numero_end') or ''
        endereco   = f"{logradouro}, {numero}" if logradouro and numero else (logradouro or None)
        cursor.execute("""
            UPDATE alunos SET
                data_nascimento      = %s,
                cpf                  = %s,
                raca                 = %s,
                local_nascimento     = %s,
                UF_nascimento        = %s,
                endereco             = %s,
                descricao_transtorno = %s
            WHERE id = %s
        """, (
            dados.get('data_nascimento') or None,
            dados.get('cpf_fmt') or None,
            dados.get('raca_enum'),
            _normalizar_municipio(dados.get('local_nascimento')) or None,
            _estado_para_sigla(dados.get('codigo_estado')) or None,
            endereco,
            dados.get('descricao_transtorno', 'Nenhum'),
            aluno_id,
        ))
        conn.commit()
        return {'sucesso': True, 'mensagem': f'Aluno ID {aluno_id} atualizado com sucesso'}
    except Exception as e:
        conn.rollback()
        return {'sucesso': False, 'mensagem': str(e)}
    finally:
        cursor.close()
        conn.close()


# Campos verificados na aba Pendências
_CAMPOS_PENDENCIA = [
    ('cpf',               'CPF do Aluno'),
    ('data_nascimento',   'Nascimento do Aluno'),
    ('sexo',              'Gênero do Aluno'),
    ('raca',              'Cor do Aluno'),
    ('local_nascimento',  'Naturalidade do Aluno'),
    ('mae',               'Filiação Mãe'),
    ('cpf_mae',           'CPF da Mãe'),
    ('nascimento_mae',    'Nascimento da Mãe'),
    ('celular',           'Celular do Responsável'),
    ('responsavel_tipo',  'Quem é o Responsável'),
    ('cep',               'CEP'),
    ('bairro',            'Bairro'),
    ('logradouro',        'Rua'),
    ('numero_end',        'Número'),
    ('codigo_estado',     'Estado'),
    ('municipio_res',     'Cidade'),
]

# Campos com semântica especial: valor '0','1','2','3' são VÁLIDOS (não são pendentes)
_CAMPOS_VALOR_ZERO_VALIDO = {'responsavel_tipo'}


def verificar_pendencias_geduc(dados_json: Dict, escola_id: int = 60) -> List[Dict]:
    """
    Retorna lista de alunos do GEDUC com campos obrigatórios vazios/não preenchidos.
    Cada item: nome_fmt, turma_fmt (do banco local), num_pend, campos_pend.
    """
    _VAZIOS = {'', '0', 'none', 'null', 'não declarada', 'nao declarada', 'nenhum'}

    turmas_locais = obter_turmas_alunos_locais(escola_id)

    resultado = []
    for turma in dados_json.get('turmas', []):
        turma_nome = str(turma.get('nome', '') or '').strip()
        turma_id   = str(turma.get('id', '') or '').strip()
        for aluno in turma.get('alunos', []):
            pendentes = []
            for campo, label in _CAMPOS_PENDENCIA:
                val = aluno.get(campo)
                val_str = str(val).strip().lower() if val is not None else ''
                if campo in _CAMPOS_VALOR_ZERO_VALIDO:
                    if val is None or val_str == '':
                        pendentes.append(label)
                elif val is None or val_str in _VAZIOS:
                    pendentes.append(label)
            if pendentes:
                nome_norm = _normalizar(aluno.get('nome', ''))
                turma_fmt = turmas_locais.get(nome_norm) or \
                            turma_nome or \
                            (f"ID {turma_id}" if turma_id else '—')
                resultado.append({
                    'nome_fmt':    _capitalizar(aluno.get('nome', '?')),
                    'turma_fmt':   turma_fmt,
                    'num_pend':    len(pendentes),
                    'campos_pend': ' | '.join(pendentes),
                })
    resultado.sort(key=lambda x: (x['turma_fmt'], x['nome_fmt']))
    return resultado


def comparar_geduc_local(dados_json: Dict, escola_id: int = 60) -> List[Dict]:
    """
    Retorna lista de alunos presentes no GEDUC mas sem matrícula ativa local.
    Cada item contém os dados normalizados prontos para exibição e inserção.
    """
    locais = obter_alunos_locais_ativos(escola_id)
    apenas_geduc = []

    for turma in dados_json.get('turmas', []):
        turma_id_geduc = turma.get('id', '')
        turma_nome_geduc = turma.get('nome', '')

        for aluno in turma.get('alunos', []):
            nome_norm = _normalizar(aluno.get('nome', ''))
            if not nome_norm:
                continue
            if nome_norm in locais:
                continue  # já está no sistema

            apenas_geduc.append({
                'nome_geduc':        aluno.get('nome', ''),
                'nome_normalizado':  nome_norm,
                'nome_fmt':          _capitalizar(aluno.get('nome', '')),
                'data_nascimento':   aluno.get('data_nascimento', ''),
                'sexo_raw':          str(aluno.get('sexo', '1')),
                'sexo':              MAPA_SEXO.get(str(aluno.get('sexo', '1')), 'M'),
                'cpf_raw':           aluno.get('cpf', ''),
                'cpf_fmt':           _formatar_cpf(aluno.get('cpf', '')),
                'raca':              aluno.get('raca', 'Não declarada'),
                'raca_enum':         MAPA_RACA_ENUM.get(aluno.get('raca', 'Não declarada'), 'pardo'),
                'celular':           _formatar_tel(aluno.get('celular', '')),
                'email':             aluno.get('email', ''),
                'mae':               aluno.get('mae', ''),
                'cpf_mae':           aluno.get('cpf_mae', ''),
                'profissao_mae':     aluno.get('profissao_mae', ''),
                'pai':               aluno.get('pai', ''),
                'cpf_pai':           aluno.get('cpf_pai', ''),
                'profissao_pai':     aluno.get('profissao_pai', ''),
                'outros_nome':       aluno.get('outros_nome', ''),
                'outros_cpf':        aluno.get('outros_cpf', ''),
                'responsavel_tipo':  aluno.get('responsavel_tipo', ''),
                'cid':               aluno.get('cid', ''),
                'tgd':               aluno.get('tgd', '0'),
                'althab':            aluno.get('althab', '0'),
                'descricao_transtorno': aluno.get('descricao_transtorno', 'Nenhum'),
                'inep_escola':       aluno.get('inep_escola', ''),
                'turma_geduc_id':    turma_id_geduc,
                'turma_geduc_nome':  turma_nome_geduc,
                # Naturalidade (codigo_naturalidade = código IBGE do município de nasc.;
                #               local_nascimento = nome real via <select>;
                #               codigo_estado = nome do estado via <select>)
                'codigo_naturalidade': aluno.get('codigo_naturalidade', ''),
                'local_nascimento':    aluno.get('local_nascimento', ''),
                'codigo_estado':     aluno.get('codigo_estado', ''),                # Endereço de residência
                'cep':               aluno.get('cep', ''),
                'logradouro':        aluno.get('logradouro', ''),
                'numero_end':        aluno.get('numero_end', ''),
                'complemento':       aluno.get('complemento', ''),
                'bairro':            aluno.get('bairro', ''),
                # municipio_res = código IBGE do município de residência
                'municipio_res':     aluno.get('municipio_res', ''),
                # uf_res = sigla UF já convertida
                'uf_res':            aluno.get('uf_res', ''),
            })

    return apenas_geduc


# ══════════════════════════════════════════════════════════════════════════════
#  INSERÇÃO NO BANCO
# ══════════════════════════════════════════════════════════════════════════════

def _inserir_responsavel(cursor, nome: str, cpf: str, telefone: str,
                         parentesco: str) -> Optional[int]:
    cpf_fmt = _formatar_cpf(cpf) if cpf else None
    nome_fmt = _capitalizar(nome) if nome else None
    if not nome_fmt:
        return None

    # Verificar por CPF
    if cpf_fmt:
        cursor.execute("SELECT id FROM responsaveis WHERE cpf = %s", (cpf_fmt,))
        r = cursor.fetchone()
        if r:
            return r[0]

    # Verificar por nome normalizado
    nome_norm = _normalizar(nome_fmt)
    cursor.execute("SELECT id, nome FROM responsaveis")
    for rid, rnome in cursor.fetchall():
        if _normalizar(rnome) == nome_norm:
            return rid

    # Inserir novo
    cursor.execute(
        "INSERT INTO responsaveis (nome, cpf, telefone, grau_parentesco) VALUES (%s,%s,%s,%s)",
        (nome_fmt, cpf_fmt, telefone or '', parentesco)
    )
    return cursor.lastrowid


def inserir_aluno_geduc(dados: Dict, escola_id: int = 60,
                        turma_id_local: Optional[int] = None,
                        ano_letivo_id: Optional[int] = None) -> Dict:
    """
    Insere um aluno GEDUC no banco local.
    Retorna dict com 'sucesso', 'aluno_id', 'mat_id', 'mensagem'.
    """
    conn = conectar_bd()
    cursor = conn.cursor(buffered=True)
    try:
        # Obter ano letivo corrente se não fornecido
        if not ano_letivo_id:
            cursor.execute(
                "SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1"
            )
            row = cursor.fetchone()
            ano_letivo_id = row[0] if row else None
            if not ano_letivo_id:
                return {'sucesso': False, 'mensagem': 'Nenhum ano letivo cadastrado.'}

        # Inserir aluno
        logradouro = dados.get('logradouro') or ''
        numero = dados.get('numero_end') or ''
        endereco = f"{logradouro}, {numero}" if logradouro and numero else (logradouro or None)
        cursor.execute("""
            INSERT INTO alunos
                (nome, data_nascimento, sexo, cpf, raca,
                 descricao_transtorno, escola_id,
                 local_nascimento, UF_nascimento,
                 endereco)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            dados['nome_fmt'],
            dados['data_nascimento'] or None,
            dados['sexo'],
            dados['cpf_fmt'],
            dados['raca_enum'],
            dados.get('descricao_transtorno', 'Nenhum'),
            escola_id,
            dados.get('local_nascimento') or None,   # nome do município de nascimento
            dados.get('codigo_estado') or None,      # nome do estado de nascimento
            endereco,
        ))
        aluno_id = cursor.lastrowid

        # Matricular se turma informada
        mat_id = None
        if turma_id_local and ano_letivo_id:
            cursor.execute("""
                INSERT INTO matriculas
                    (aluno_id, turma_id, data_matricula, ano_letivo_id, status)
                VALUES (%s, %s, CURDATE(), %s, 'Ativo')
            """, (aluno_id, turma_id_local, ano_letivo_id))
            mat_id = cursor.lastrowid

        # Responsáveis
        resp_tipo = dados.get('responsavel_tipo', '0')
        celular = dados.get('celular', '')

        if dados.get('mae'):
            rid = _inserir_responsavel(
                cursor, dados['mae'], dados.get('cpf_mae', ''),
                celular if resp_tipo == '0' else '', 'Mãe'
            )
            if rid:
                cursor.execute(
                    "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s,%s)",
                    (rid, aluno_id)
                )

        if dados.get('pai'):
            rid = _inserir_responsavel(
                cursor, dados['pai'], dados.get('cpf_pai', ''),
                celular if resp_tipo == '1' else '', 'Pai'
            )
            if rid:
                cursor.execute(
                    "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s,%s)",
                    (rid, aluno_id)
                )

        if dados.get('outros_nome'):
            rid = _inserir_responsavel(
                cursor, dados['outros_nome'], dados.get('outros_cpf', ''),
                celular if resp_tipo == '2' else '', 'Outro Responsável'
            )
            if rid:
                cursor.execute(
                    "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s,%s)",
                    (rid, aluno_id)
                )

        conn.commit()
        return {
            'sucesso': True,
            'aluno_id': aluno_id,
            'mat_id': mat_id,
            'mensagem': f"Inserido com ID {aluno_id}" + (f", matrícula {mat_id}" if mat_id else ""),
        }

    except mysql.connector.errors.IntegrityError as e:
        conn.rollback()
        msg = str(e)
        if 'idx_cpf_unico' in msg or 'Duplicate entry' in msg:
            cpf = dados.get('cpf_fmt', '')
            logger.warning(
                "CPF já cadastrado, aluno pulado: %s (CPF: %s)",
                dados.get('nome_geduc', '?'), cpf
            )
            return {
                'sucesso': False,
                'mensagem': f"CPF {cpf} já existe no sistema — aluno não inserido.",
            }
        logger.exception("Erro de integridade ao inserir aluno %s: %s", dados.get('nome_geduc'), e)
        return {'sucesso': False, 'mensagem': msg}
    except Exception as e:
        conn.rollback()
        logger.exception("Erro ao inserir aluno %s: %s", dados.get('nome_geduc'), e)
        return {'sucesso': False, 'mensagem': str(e)}
    finally:
        cursor.close()
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  INTERFACE GRÁFICA
# ══════════════════════════════════════════════════════════════════════════════

class InterfaceImportarAlunosGEDUC:
    """
    Janela que compara o JSON do GEDUC com o sistema local e permite
    selecionar e importar os alunos ausentes.
    """

    def __init__(self, janela_pai=None):
        self.janela_pai = janela_pai

        # Janela principal
        if janela_pai:
            self.janela = tk.Toplevel(janela_pai)
        else:
            self.janela = tk.Tk()

        self.janela.title("Importar Alunos do GEDUC")
        self.janela.geometry("1100x820")
        self.janela.configure(bg=CO0)
        self.janela.protocol("WM_DELETE_WINDOW", self._ao_fechar)

        # Centralizar
        self.janela.update_idletasks()
        w, h = 1100, 820
        x = (self.janela.winfo_screenwidth() - w) // 2
        y = (self.janela.winfo_screenheight() - h) // 2
        self.janela.geometry(f"{w}x{h}+{x}+{y}")

        # Estado interno
        self._alunos: List[Dict] = []
        self._vars_sel: List[tk.BooleanVar] = []
        self._turmas_locais: List[Dict] = []
        self._ano_letivo_id: Optional[int] = None
        self._pendencias: List[Dict] = []
        self._arquivo_json = tk.StringVar(value=JSON_PADRAO)

        self._carregar_turmas_locais()
        self._construir_ui()
        # Inicia polling de log (roda durante toda a vida da janela)
        self.janela.after(300, self._poll_log_queue)

        if janela_pai:
            self.janela.grab_set()
            self.janela.focus_force()

    # ──────────────────────────────── DADOS ──────────────────────────────────

    def _carregar_turmas_locais(self):
        try:
            conn = conectar_bd()
            cursor = conn.cursor(buffered=True)
            cursor.execute(
                "SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1"
            )
            row = cursor.fetchone()
            self._ano_letivo_id = row[0] if row else None

            cursor.execute("""
                SELECT t.id, CONCAT(s.nome, CASE WHEN t.nome != '' THEN CONCAT(' ', t.nome) ELSE '' END,
                       ' - ', t.turno) AS descricao
                FROM turmas t
                JOIN series s ON s.id = t.serie_id
                WHERE t.escola_id = 60
                  AND t.ano_letivo_id = %s
                ORDER BY s.nome, t.nome, t.turno
            """, (self._ano_letivo_id,))
            self._turmas_locais = [{'id': tid, 'desc': desc} for tid, desc in cursor.fetchall()]
            cursor.close()
            conn.close()
        except Exception as e:
            logger.exception(f"Erro ao carregar turmas: {e}")
            self._turmas_locais = []

    # ──────────────────────────────── UI ─────────────────────────────────────

    def _construir_ui(self):
        # ── cabeçalho ──
        frame_cabecalho = tk.Frame(self.janela, bg=CO1, pady=8)
        frame_cabecalho.pack(fill=tk.X)

        tk.Label(
            frame_cabecalho,
            text="📥  Importar Alunos do GEDUC",
            font=("Arial", 15, "bold"),
            bg=CO1, fg="white",
        ).pack(side=tk.LEFT, padx=20)

        # ══ Etapa 1: Extrair do GEDUC ══
        frame_extr = tk.LabelFrame(
            self.janela,
            text=" ① Extrair dados do GEDUC (Selenium) ",
            font=("Arial", 9, "bold"), bg=CO0, fg=CO1, pady=4, padx=8,
        )
        frame_extr.pack(fill=tk.X, padx=15, pady=(6, 2))

        tk.Label(frame_extr, text="Usuário:", font=("Arial", 9), bg=CO0).grid(
            row=0, column=0, sticky="e", padx=(0, 3), pady=2)
        self._var_usuario = tk.StringVar()
        tk.Entry(frame_extr, textvariable=self._var_usuario,
                 font=("Arial", 10), width=20).grid(row=0, column=1, padx=2, pady=2, sticky="w")

        tk.Label(frame_extr, text="Senha:", font=("Arial", 9), bg=CO0).grid(
            row=0, column=2, sticky="e", padx=(12, 3), pady=2)
        self._var_senha = tk.StringVar()
        tk.Entry(frame_extr, textvariable=self._var_senha,
                 font=("Arial", 10), width=20, show="*").grid(row=0, column=3, padx=2, pady=2, sticky="w")

        self._btn_extrair = tk.Button(
            frame_extr, text="▶  Extrair do GEDUC",
            command=self._extrair_do_geduc,
            bg=CO2, fg="white", font=("Arial", 9, "bold"), cursor="hand2", padx=10)
        self._btn_extrair.grid(row=0, column=4, padx=(14, 4), pady=4)

        tk.Label(
            frame_extr,
            text="Abre o Chrome, faz login no GEDUC e coleta todos os alunos → salva em alunos_geduc.json",
            font=("Arial", 8, "italic"), bg=CO0, fg="#666666",
        ).grid(row=1, column=0, columnspan=5, sticky="w", padx=2, pady=(0, 2))

        # ══ Etapa 2: Comparar e Importar ══
        frame_etapa2 = tk.LabelFrame(
            self.janela,
            text=" ② Comparar e importar ",
            font=("Arial", 9, "bold"), bg=CO0, fg=CO1, pady=4, padx=8,
        )
        frame_etapa2.pack(fill=tk.X, padx=15, pady=(2, 0))

        # ── seleção de arquivo ──
        frame_arq = tk.Frame(frame_etapa2, bg=CO0)
        frame_arq.pack(fill=tk.X)

        tk.Label(frame_arq, text="Arquivo JSON:", font=("Arial", 10, "bold"),
                 bg=CO0, fg=CO1).pack(side=tk.LEFT)

        tk.Entry(frame_arq, textvariable=self._arquivo_json,
                 font=("Arial", 10), width=55).pack(side=tk.LEFT, padx=6)

        tk.Button(frame_arq, text="Procurar", command=self._selecionar_arquivo,
                  bg=CO4, fg="white", font=("Arial", 9, "bold"),
                  cursor="hand2").pack(side=tk.LEFT, padx=4)

        tk.Button(frame_arq, text="🔍 Comparar", command=self._comparar,
                  bg=CO1, fg="white", font=("Arial", 10, "bold"),
                  cursor="hand2", height=1, padx=10).pack(side=tk.LEFT, padx=8)

        # ── turma de destino ──
        frame_turma = tk.Frame(frame_etapa2, bg=CO0, pady=2)
        frame_turma.pack(fill=tk.X)

        tk.Label(frame_turma, text="Turma de destino (para matrícula):",
                 font=("Arial", 10, "bold"), bg=CO0, fg=CO1).pack(side=tk.LEFT)

        self._var_turma = tk.StringVar()
        opcoes_turma = ["— Não matricular —"] + [t['desc'] for t in self._turmas_locais]
        self._combo_turma = ttk.Combobox(
            frame_turma, textvariable=self._var_turma,
            values=opcoes_turma, state="readonly", width=45, font=("Arial", 10)
        )
        self._combo_turma.current(0)
        self._combo_turma.pack(side=tk.LEFT, padx=8)

        # ── status ──
        self._var_status = tk.StringVar(value="Preencha as credenciais e clique em ▶ Extrair, ou carregue um JSON existente.")
        self._lbl_status = tk.Label(
            self.janela, textvariable=self._var_status,
            font=("Arial", 9, "italic"), bg=CO0, fg="#555555", anchor="w"
        )
        self._lbl_status.pack(fill=tk.X, padx=15)

        # ── notebook com abas ──
        self._notebook = ttk.Notebook(self.janela)
        self._notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=(4, 0))

        # ── Aba 1: Ausentes no Sistema ──
        frame_aba1 = tk.Frame(self._notebook, bg=CO0)
        self._notebook.add(frame_aba1, text="📋 Ausentes no Sistema (0)")

        colunas  = ("sel", "nome", "nasc", "sexo", "cpf", "raca", "turma_geduc", "mae", "pai", "transtorno")
        larguras = (30, 260, 90, 50, 110, 70, 150, 200, 200, 130)
        titulos  = (" ", "Nome", "Nascimento", "Sexo", "CPF", "Raça",
                    "Turma GEDUC", "Mãe", "Pai", "Transtorno")

        frame_tabela = tk.Frame(frame_aba1, bg=CO0)
        frame_tabela.pack(fill=tk.BOTH, expand=True)

        self._tree = ttk.Treeview(
            frame_tabela, columns=colunas, show="headings",
            selectmode="browse", height=12
        )
        for col, larg, tit in zip(colunas, larguras, titulos):
            self._tree.heading(col, text=tit)
            self._tree.column(col, width=larg, minwidth=larg, anchor="w" if larg > 50 else "center")

        self._tree.tag_configure("par",  background=CO_LINHA_PAR)
        self._tree.tag_configure("impar", background=CO_LINHA_IMPAR)
        self._tree.tag_configure("selecionado", background="#D4EDDA")

        scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self._tree.yview)
        scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        frame_tabela.rowconfigure(0, weight=1)
        frame_tabela.columnconfigure(0, weight=1)

        self._tree.bind("<Button-1>", self._toggle_selecao)

        frame_botoes1 = tk.Frame(frame_aba1, bg=CO0, pady=6)
        frame_botoes1.pack(fill=tk.X)

        self._lbl_contagem = tk.Label(
            frame_botoes1, text="", font=("Arial", 10), bg=CO0, fg=CO1
        )
        self._lbl_contagem.pack(side=tk.LEFT)

        tk.Button(
            frame_botoes1, text="✅ Selecionar Todos", command=self._selecionar_todos,
            bg=CO4, fg="white", font=("Arial", 9, "bold"), cursor="hand2"
        ).pack(side=tk.LEFT, padx=6)

        tk.Button(
            frame_botoes1, text="☐ Desmarcar Todos", command=self._desmarcar_todos,
            bg="#95A5A6", fg="white", font=("Arial", 9, "bold"), cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            frame_botoes1, text="📥 Inserir Selecionados no Sistema",
            command=self._inserir_selecionados,
            bg=CO2, fg="white", font=("Arial", 11, "bold"),
            cursor="hand2", padx=12, pady=4
        ).pack(side=tk.RIGHT, padx=6)

        # ── Aba 2: Divergências ──
        frame_aba2 = tk.Frame(self._notebook, bg=CO0)
        self._notebook.add(frame_aba2, text="⚠️ Divergências (0)")

        colunas_div  = ("sel", "nome", "num", "campos_diff")
        larguras_div = (30, 250, 45, 680)
        titulos_div  = (" ", "Nome", "Qtd", "Campos divergentes (Valor Local → Valor GEDUC)")

        frame_tabela_div = tk.Frame(frame_aba2, bg=CO0)
        frame_tabela_div.pack(fill=tk.BOTH, expand=True)

        self._tree_div = ttk.Treeview(
            frame_tabela_div, columns=colunas_div, show="headings",
            selectmode="browse", height=12
        )
        for col, larg, tit in zip(colunas_div, larguras_div, titulos_div):
            self._tree_div.heading(col, text=tit)
            self._tree_div.column(col, width=larg, minwidth=larg, anchor="w" if larg > 50 else "center")

        self._tree_div.tag_configure("par",  background=CO_LINHA_PAR)
        self._tree_div.tag_configure("impar", background=CO_LINHA_IMPAR)
        self._tree_div.tag_configure("selecionado", background="#D4EDDA")

        scroll_y2 = ttk.Scrollbar(frame_tabela_div, orient="vertical", command=self._tree_div.yview)
        scroll_x2 = ttk.Scrollbar(frame_tabela_div, orient="horizontal", command=self._tree_div.xview)
        self._tree_div.configure(yscrollcommand=scroll_y2.set, xscrollcommand=scroll_x2.set)

        self._tree_div.grid(row=0, column=0, sticky="nsew")
        scroll_y2.grid(row=0, column=1, sticky="ns")
        scroll_x2.grid(row=1, column=0, sticky="ew")
        frame_tabela_div.rowconfigure(0, weight=1)
        frame_tabela_div.columnconfigure(0, weight=1)

        self._tree_div.bind("<Button-1>", self._toggle_sel_div)

        frame_botoes2 = tk.Frame(frame_aba2, bg=CO0, pady=6)
        frame_botoes2.pack(fill=tk.X)

        self._lbl_contagem_div = tk.Label(
            frame_botoes2, text="", font=("Arial", 10), bg=CO0, fg=CO1
        )
        self._lbl_contagem_div.pack(side=tk.LEFT)

        tk.Button(
            frame_botoes2, text="✅ Selecionar Todos", command=self._selecionar_todos_div,
            bg=CO4, fg="white", font=("Arial", 9, "bold"), cursor="hand2"
        ).pack(side=tk.LEFT, padx=6)

        tk.Button(
            frame_botoes2, text="☐ Desmarcar Todos", command=self._desmarcar_todos_div,
            bg="#95A5A6", fg="white", font=("Arial", 9, "bold"), cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            frame_botoes2, text="🔄 Atualizar Selecionados",
            command=self._atualizar_selecionados,
            bg="#2980B9", fg="white", font=("Arial", 11, "bold"),
            cursor="hand2", padx=12, pady=4
        ).pack(side=tk.RIGHT, padx=6)

        # ── Aba 3: Pendências ──
        frame_aba3 = tk.Frame(self._notebook, bg=CO0)
        self._notebook.add(frame_aba3, text="📋 Pendências (0)")

        colunas_pend  = ("nome", "num", "campos_pend")
        larguras_pend = (270, 45, 670)
        titulos_pend  = ("Nome", "Qtd", "Campos pendentes")

        frame_tabela_pend = tk.Frame(frame_aba3, bg=CO0)
        frame_tabela_pend.pack(fill=tk.BOTH, expand=True)

        self._tree_pend = ttk.Treeview(
            frame_tabela_pend, columns=colunas_pend, show="headings",
            selectmode="browse", height=12
        )
        for col, larg, tit in zip(colunas_pend, larguras_pend, titulos_pend):
            self._tree_pend.heading(col, text=tit)
            self._tree_pend.column(col, width=larg, minwidth=larg, anchor="w" if larg > 50 else "center")

        self._tree_pend.tag_configure("par",  background=CO_LINHA_PAR)
        self._tree_pend.tag_configure("impar", background=CO_LINHA_IMPAR)

        scroll_y3 = ttk.Scrollbar(frame_tabela_pend, orient="vertical",  command=self._tree_pend.yview)
        scroll_x3 = ttk.Scrollbar(frame_tabela_pend, orient="horizontal", command=self._tree_pend.xview)
        self._tree_pend.configure(yscrollcommand=scroll_y3.set, xscrollcommand=scroll_x3.set)

        self._tree_pend.grid(row=0, column=0, sticky="nsew")
        scroll_y3.grid(row=0, column=1, sticky="ns")
        scroll_x3.grid(row=1, column=0, sticky="ew")
        frame_tabela_pend.rowconfigure(0, weight=1)
        frame_tabela_pend.columnconfigure(0, weight=1)

        frame_botoes3 = tk.Frame(frame_aba3, bg=CO0, pady=6)
        frame_botoes3.pack(fill=tk.X)

        self._lbl_contagem_pend = tk.Label(
            frame_botoes3, text="", font=("Arial", 10), bg=CO0, fg=CO1
        )
        self._lbl_contagem_pend.pack(side=tk.LEFT)

        tk.Button(
            frame_botoes3, text="🖨️ Imprimir PDF",
            command=self._imprimir_pendencias_pdf,
            bg="#8E44AD", fg="white", font=("Arial", 9, "bold"), cursor="hand2"
        ).pack(side=tk.RIGHT, padx=6)

        # ── botão fechar (fora das abas) ──
        frame_fechar = tk.Frame(self.janela, bg=CO0, pady=4)
        frame_fechar.pack(fill=tk.X, padx=15)

        tk.Button(
            frame_fechar, text="Fechar", command=self._ao_fechar,
            bg=CO3, fg="white", font=("Arial", 10, "bold"), cursor="hand2"
        ).pack(side=tk.RIGHT, padx=4)

        # ── log ──
        frame_log = tk.Frame(self.janela, bg=CO0)
        frame_log.pack(fill=tk.X, padx=15, pady=(0, 6))

        self._txt_log = tk.Text(
            frame_log, height=4, font=("Consolas", 8),
            bg="#F0F0F0", fg="#333333", state=tk.DISABLED, wrap="word"
        )
        log_scroll = ttk.Scrollbar(frame_log, orient="vertical", command=self._txt_log.yview)
        self._txt_log.configure(yscrollcommand=log_scroll.set)
        self._txt_log.pack(side=tk.LEFT, fill=tk.X, expand=True)
        log_scroll.pack(side=tk.LEFT, fill=tk.Y)

    # ──────────────────────────────── AÇÕES ──────────────────────────────────

    def _extrair_do_geduc(self):
        """Inicia extração do GEDUC via Selenium e exibe progresso em tempo real."""
        usuario = self._var_usuario.get().strip()
        senha = self._var_senha.get().strip()
        if not usuario or not senha:
            messagebox.showerror("Credenciais ausentes",
                                 "Informe o usuário e a senha do GEDUC.",
                                 parent=self.janela)
            return

        arquivo_saida = self._arquivo_json.get().strip() or JSON_PADRAO

        self._btn_extrair.config(state=tk.DISABLED, text="Extraindo…")
        self._var_status.set("Extração iniciada — o Chrome será aberto automaticamente. Aguarde.")
        self._log("=" * 60)
        self._log(f"Iniciando extração do GEDUC → {arquivo_saida}")

        # Criar fila + handler para capturar logs do módulo Selenium
        self._log_queue: _queue_mod.Queue = _queue_mod.Queue()
        handler = _LogCapture(self._log_queue)
        handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%H:%M:%S'))
        root_log = logging.getLogger()
        root_log.addHandler(handler)
        self._log_handler = handler

        def _executar():
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "importar_geduc",
                    ROOT_DIR / "scripts" / "migracao" / "importar_geduc.py",
                )
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[arg-type]
                mod.extrair_alunos_geduc(usuario, senha, arquivo_saida=arquivo_saida)
            except Exception as e:
                logger.exception(f"Erro na extração GEDUC: {e}")
            finally:
                root_log.removeHandler(self._log_handler)
                self.janela.after(0, lambda: self._extracao_concluida(arquivo_saida))

        threading.Thread(target=_executar, daemon=True).start()

    def _poll_log_queue(self):
        """Drena a fila de logs gerados por _LogCapture e exibe na área de log."""
        if hasattr(self, '_log_queue'):
            try:
                while True:
                    msg = self._log_queue.get_nowait()
                    self._log(msg)
            except _queue_mod.Empty:
                pass
        # Reagendar enquanto a janela existir
        try:
            self.janela.after(250, self._poll_log_queue)
        except tk.TclError:
            pass  # janela já destruída

    def _extracao_concluida(self, arquivo_saida: str):
        """Chamado quando a thread de extração termina."""
        try:
            self._btn_extrair.config(state=tk.NORMAL, text="▶  Extrair do GEDUC")
            self._arquivo_json.set(arquivo_saida)
            self._log("=" * 60)
            self._log("Extração concluída. Iniciando comparação automática…")
            self._var_status.set("Extração concluída! Comparando com o sistema local…")
            self._comparar()
        except tk.TclError:
            pass  # janela foi fechada antes da thread terminar

    def _selecionar_arquivo(self):
        path = filedialog.askopenfilename(
            title="Selecionar arquivo JSON do GEDUC",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
            parent=self.janela,
        )
        if path:
            self._arquivo_json.set(path)

    def _comparar(self):
        caminho = self._arquivo_json.get().strip()
        if not caminho or not os.path.exists(caminho):
            messagebox.showerror("Erro", f"Arquivo não encontrado:\n{caminho}", parent=self.janela)
            return

        self._var_status.set("Comparando... aguarde.")
        self.janela.update()

        def executar():
            try:
                dados = carregar_json_geduc(caminho)
                alunos = comparar_geduc_local(dados, escola_id=60)
                divergencias = comparar_divergencias_geduc_local(dados, escola_id=60)
                pendencias = verificar_pendencias_geduc(dados)
                self.janela.after(0, lambda a=alunos, d=dados, div=divergencias, pend=pendencias:
                                  self._exibir_resultado(a, d, div, pend))
            except Exception as e:
                self.janela.after(0, lambda: self._var_status.set(f"Erro: {e}"))
                logger.exception(f"Erro na comparação: {e}")

        threading.Thread(target=executar, daemon=True).start()

    def _exibir_resultado(self, alunos: List[Dict], dados_json: Dict, divergencias: List[Dict] = None, pendencias: List[Dict] = None):
        self._alunos = alunos
        self._selecionados = set()

        # Limpar tabela
        for item in self._tree.get_children():
            self._tree.delete(item)

        total_geduc = dados_json.get('total_alunos', 0)
        data_extr   = dados_json.get('data_extracao', '')[:10] if dados_json.get('data_extracao') else ''

        for i, a in enumerate(alunos):
            tag = "par" if i % 2 == 0 else "impar"
            self._tree.insert("", "end", iid=str(i), tags=(tag,), values=(
                "☐",
                a['nome_fmt'],
                a['data_nascimento'],
                a['sexo'],
                a['cpf_fmt'] or '',
                a['raca'],
                f"{a['turma_geduc_nome'] or ''} (ID {a['turma_geduc_id']})".strip(),
                _capitalizar(a['mae']) if a.get('mae') else '',
                _capitalizar(a['pai']) if a.get('pai') else '',
                a.get('descricao_transtorno', 'Nenhum'),
            ))

        n = len(alunos)
        self._notebook.tab(0, text=f"📋 Ausentes no Sistema ({n})")
        self._lbl_contagem.config(
            text=f"{n} aluno{'s' if n != 1 else ''} no GEDUC sem matrícula local"
        )
        self._var_status.set(
            f"JSON: {os.path.basename(caminho := self._arquivo_json.get())} | "
            f"Extração: {data_extr} | Total GEDUC: {total_geduc} | "
            f"Faltando no sistema: {n}"
        )
        self._log(f"Comparação concluída: {n} alunos faltando no sistema local.")

        if divergencias is not None:
            self._exibir_divergencias(divergencias)

        if pendencias is not None:
            self._exibir_pendencias(pendencias)

    def _toggle_selecao(self, event):
        region = self._tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self._tree.identify_row(event.y)
        if not row_id:
            return
        try:
            idx = int(row_id)
        except ValueError:
            return

        if idx in self._selecionados:
            self._selecionados.discard(idx)
            vals = list(self._tree.item(row_id, "values"))
            vals[0] = "☐"
            tag = "par" if idx % 2 == 0 else "impar"
            self._tree.item(row_id, values=vals, tags=(tag,))
        else:
            self._selecionados.add(idx)
            vals = list(self._tree.item(row_id, "values"))
            vals[0] = "☑"
            self._tree.item(row_id, values=vals, tags=("selecionado",))

        self._lbl_contagem.config(
            text=f"{len(self._alunos)} no GEDUC sem matrícula | "
                 f"{len(self._selecionados)} selecionados"
        )

    def _selecionar_todos(self):
        if not hasattr(self, '_selecionados'):
            self._selecionados = set()
        for i in range(len(self._alunos)):
            self._selecionados.add(i)
            vals = list(self._tree.item(str(i), "values"))
            vals[0] = "☑"
            self._tree.item(str(i), values=vals, tags=("selecionado",))
        self._lbl_contagem.config(
            text=f"{len(self._alunos)} no GEDUC | {len(self._selecionados)} selecionados"
        )

    def _desmarcar_todos(self):
        if not hasattr(self, '_selecionados'):
            self._selecionados = set()
            return
        for i in self._selecionados:
            vals = list(self._tree.item(str(i), "values"))
            vals[0] = "☐"
            tag = "par" if i % 2 == 0 else "impar"
            self._tree.item(str(i), values=vals, tags=(tag,))
        self._selecionados.clear()
        self._lbl_contagem.config(
            text=f"{len(self._alunos)} no GEDUC | 0 selecionados"
        )

    def _inserir_selecionados(self):
        if not hasattr(self, '_selecionados') or not self._selecionados:
            messagebox.showwarning("Atenção", "Selecione ao menos um aluno.", parent=self.janela)
            return

        # Turma de destino
        idx_turma = self._combo_turma.current()
        turma_id_local = None
        if idx_turma > 0:
            turma_id_local = self._turmas_locais[idx_turma - 1]['id']

        alunos_sel = [self._alunos[i] for i in sorted(self._selecionados)]
        n = len(alunos_sel)

        confirmacao = messagebox.askyesno(
            "Confirmar Inserção",
            f"Inserir {n} aluno{'s' if n != 1 else ''} no sistema local?\n\n"
            + (f"Turma de matrícula: {self._var_turma.get()}\n" if turma_id_local else "Sem matrícula automática.\n")
            + "\nOs dados serão normalizados antes da inserção.",
            parent=self.janela,
        )
        if not confirmacao:
            return

        self._var_status.set("Inserindo alunos... aguarde.")
        self.janela.update()

        def executar():
            ok, erros = 0, 0
            for dados in alunos_sel:
                resultado = inserir_aluno_geduc(
                    dados,
                    escola_id=60,
                    turma_id_local=turma_id_local,
                    ano_letivo_id=self._ano_letivo_id,
                )
                if resultado['sucesso']:
                    ok += 1
                    self.janela.after(
                        0, lambda d=dados, r=resultado:
                        self._log(f"[OK] {d['nome_fmt']} — {r['mensagem']}")
                    )
                else:
                    erros += 1
                    self.janela.after(
                        0, lambda d=dados, r=resultado:
                        self._log(f"[ERRO] {d['nome_fmt']} — {r['mensagem']}")
                    )

            self.janela.after(0, lambda: self._pos_insercao(ok, erros))

        threading.Thread(target=executar, daemon=True).start()

    def _pos_insercao(self, ok: int, erros: int):
        self._var_status.set(f"Inserção concluída: {ok} inseridos, {erros} erros.")
        msg = f"Inserção concluída!\n\n✅ Inseridos: {ok}\n❌ Erros: {erros}"
        if erros:
            messagebox.showwarning("Resultado", msg, parent=self.janela)
        else:
            messagebox.showinfo("Resultado", msg, parent=self.janela)

        # Recomparar para atualizar a lista
        self._comparar()

    # ─────────────────────── ABA DIVERGÊNCIAS ───────────────────────────────

    def _exibir_divergencias(self, divergencias: List[Dict]):
        self._divergencias = divergencias
        self._selecionados_div: set = set()

        for item in self._tree_div.get_children():
            self._tree_div.delete(item)

        for i, d in enumerate(divergencias):
            tag = "par" if i % 2 == 0 else "impar"
            self._tree_div.insert("", "end", iid=str(i), tags=(tag,), values=(
                "☐",
                d['nome_fmt'],
                str(d['num_diffs']),
                d['campos_diff'],
            ))

        n = len(divergencias)
        self._notebook.tab(1, text=f"⚠️ Divergências ({n})")
        self._lbl_contagem_div.config(
            text=f"{n} aluno{'s' if n != 1 else ''} com dados divergentes"
        )
        self._log(f"Divergências encontradas: {n} alunos com dados diferentes localmente.")

    def _imprimir_pendencias_pdf(self):
        if not hasattr(self, '_pendencias') or not self._pendencias:
            messagebox.showwarning("Atenção", "Nenhuma pendência para imprimir.", parent=self.janela)
            return
        self._var_status.set("Gerando PDF...")
        self.janela.update()
        def executar():
            try:
                gerar_pdf_pendencias_geduc(self._pendencias)
                self.janela.after(0, lambda: self._var_status.set("PDF gerado e aberto com sucesso."))
            except Exception as e:
                logger.exception(f"Erro ao gerar PDF de pendências: {e}")
                self.janela.after(0, lambda: messagebox.showerror("Erro", f"Falha ao gerar PDF:\n{e}", parent=self.janela))
                self.janela.after(0, lambda: self._var_status.set("Erro ao gerar PDF."))
        threading.Thread(target=executar, daemon=True).start()

    def _exibir_pendencias(self, pendencias: List[Dict]):
        self._pendencias = pendencias

        for item in self._tree_pend.get_children():
            self._tree_pend.delete(item)

        for i, p in enumerate(pendencias):
            tag = "par" if i % 2 == 0 else "impar"
            self._tree_pend.insert("", "end", iid=str(i), tags=(tag,), values=(
                p['nome_fmt'],
                str(p['num_pend']),
                p['campos_pend'],
            ))

        n = len(pendencias)
        self._notebook.tab(2, text=f"📋 Pendências ({n})")
        self._lbl_contagem_pend.config(
            text=f"{n} aluno{'s' if n != 1 else ''} com campos pendentes no GEDUC"
        )
        self._log(f"Pendências: {n} alunos com dados incompletos no GEDUC.")

    def _toggle_sel_div(self, event):
        region = self._tree_div.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self._tree_div.identify_row(event.y)
        if not row_id:
            return
        try:
            idx = int(row_id)
        except ValueError:
            return

        if not hasattr(self, '_selecionados_div'):
            self._selecionados_div = set()

        if idx in self._selecionados_div:
            self._selecionados_div.discard(idx)
            vals = list(self._tree_div.item(row_id, "values"))
            vals[0] = "☐"
            tag = "par" if idx % 2 == 0 else "impar"
            self._tree_div.item(row_id, values=vals, tags=(tag,))
        else:
            self._selecionados_div.add(idx)
            vals = list(self._tree_div.item(row_id, "values"))
            vals[0] = "☑"
            self._tree_div.item(row_id, values=vals, tags=("selecionado",))

        self._lbl_contagem_div.config(
            text=f"{len(self._divergencias)} com divergências | "
                 f"{len(self._selecionados_div)} selecionados"
        )

    def _selecionar_todos_div(self):
        if not hasattr(self, '_selecionados_div'):
            self._selecionados_div = set()
        for i in range(len(self._divergencias)):
            self._selecionados_div.add(i)
            vals = list(self._tree_div.item(str(i), "values"))
            vals[0] = "☑"
            self._tree_div.item(str(i), values=vals, tags=("selecionado",))
        self._lbl_contagem_div.config(
            text=f"{len(self._divergencias)} com divergências | "
                 f"{len(self._selecionados_div)} selecionados"
        )

    def _desmarcar_todos_div(self):
        if not hasattr(self, '_selecionados_div'):
            self._selecionados_div = set()
            return
        for i in self._selecionados_div:
            vals = list(self._tree_div.item(str(i), "values"))
            vals[0] = "☐"
            tag = "par" if i % 2 == 0 else "impar"
            self._tree_div.item(str(i), values=vals, tags=(tag,))
        self._selecionados_div.clear()
        self._lbl_contagem_div.config(
            text=f"{len(self._divergencias)} com divergências | 0 selecionados"
        )

    def _atualizar_selecionados(self):
        if not hasattr(self, '_selecionados_div') or not self._selecionados_div:
            messagebox.showwarning("Atenção", "Selecione ao menos um aluno.", parent=self.janela)
            return

        registros_sel = [self._divergencias[i] for i in sorted(self._selecionados_div)]
        n = len(registros_sel)

        confirmacao = messagebox.askyesno(
            "Confirmar Atualização",
            f"Atualizar dados de {n} aluno{'s' if n != 1 else ''} com os dados do GEDUC?\n\n"
            "Os dados locais serão substituídos pelos dados do GEDUC.",
            parent=self.janela,
        )
        if not confirmacao:
            return

        self._var_status.set("Atualizando alunos... aguarde.")
        self.janela.update()

        def executar():
            ok, erros = 0, 0
            for dados in registros_sel:
                resultado = atualizar_aluno_geduc(dados['aluno_id'], dados)
                if resultado['sucesso']:
                    ok += 1
                    self.janela.after(
                        0, lambda d=dados, r=resultado:
                        self._log(f"[OK] {d['nome_fmt']} — {r['mensagem']}")
                    )
                else:
                    erros += 1
                    self.janela.after(
                        0, lambda d=dados, r=resultado:
                        self._log(f"[ERRO] {d['nome_fmt']} — {r['mensagem']}")
                    )
            self.janela.after(0, lambda: self._pos_atualizacao(ok, erros))

        threading.Thread(target=executar, daemon=True).start()

    def _pos_atualizacao(self, ok: int, erros: int):
        self._var_status.set(f"Atualização concluída: {ok} atualizados, {erros} erros.")
        msg = f"Atualização concluída!\n\n✅ Atualizados: {ok}\n❌ Erros: {erros}"
        if erros:
            messagebox.showwarning("Resultado", msg, parent=self.janela)
        else:
            messagebox.showinfo("Resultado", msg, parent=self.janela)
        # Recomparar para atualizar as listas
        self._comparar()

    def _log(self, msg: str):
        self._txt_log.configure(state=tk.NORMAL)
        self._txt_log.insert(tk.END, msg + "\n")
        self._txt_log.see(tk.END)
        self._txt_log.configure(state=tk.DISABLED)

    def _ao_fechar(self):
        if self.janela_pai:
            self.janela_pai.deiconify()
        self.janela.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  PONTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

def abrir_importacao_alunos_geduc(janela_pai=None):
    """
    Abre a interface de importação de alunos do GEDUC.
    Se janela_pai for fornecida, ela será ocultada durante o uso e
    restaurada ao fechar.
    """
    try:
        if janela_pai:
            janela_pai.withdraw()
        InterfaceImportarAlunosGEDUC(janela_pai=janela_pai)
    except Exception as e:
        logger.exception(f"Erro ao abrir importação de alunos GEDUC: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir interface:\n{e}")
        if janela_pai:
            janela_pai.deiconify()


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    InterfaceImportarAlunosGEDUC(janela_pai=root)
    root.mainloop()
