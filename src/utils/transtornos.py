"""
Utilitário para normalizar descrições de transtornos/necessidades especiais.

Converte valores brutos vindos do GEDUC (com códigos CID misturados, espaços,
siglas, prefixos "CID10", "CID 10", etc.) para um formato padronizado e legível.

Exemplos de entrada → saída:
  'CID: F91.3'                   → 'TDO'
  'CID: F90.0'                   → 'TDAH'
  'TEA - CID: F84.0'             → 'TEA'
  'TEA - CID: CID10 F84.0'       → 'TEA'
  'TEA - CID: CID 10 F 84.0'     → 'TEA'
  'CID: CID 11 F6A05'            → 'TDAH'
  'TEA, ALTAS HABILIDADES'       → 'TEA / Altas Habilidades'
  'TEA'                          → 'TEA'
  'Nenhum' / '' / None           → 'Nenhum'
"""

import re
from typing import Optional

# ── Mapeamento código CID (normalizado) → sigla do transtorno ────────────────
_CID_MAP: dict[str, str] = {
    # CID-10
    'F84.0': 'TEA',    # Autismo infantil / Transtorno do Espectro Autista
    'F840':  'TEA',
    'F90.0': 'TDAH',   # Distúrbio de atividade e atenção
    'F900':  'TDAH',
    'F90.1': 'TDAH',
    'F901':  'TDAH',
    'F91.3': 'TDO',    # Transtorno desafiador de oposição
    'F913':  'TDO',
    # CID-11
    'F6A05': 'TDAH',
}

# ── Siglas / palavras-chave conhecidas → label normalizado ───────────────────
# A ordem importa: siglas principais primeiro, complementares depois
_SIGLAS: list[tuple[str, str]] = [
    ('TDAH',              'TDAH'),
    ('TDA',               'TDAH'),
    ('TEA',               'TEA'),
    ('TGD',               'TEA'),   # TGD geralmente = TEA neste contexto
    ('TDO',               'TDO'),
    ('TOD',               'TDO'),
    ('ALTAS HABILIDADES', 'Altas Habilidades'),
    ('SUPERDOTAÇÃO',      'Altas Habilidades'),
    ('SUPERDOTACAO',      'Altas Habilidades'),
]

# Regex para extrair código CID do tipo Fxx.x ou F6A05 (permite espaço entre F e dígito)
_RE_CID = re.compile(
    r'\bF\s*([0-9][0-9A-Z]*(?:\.[0-9]+)?)\b',
    re.IGNORECASE,
)


def _extrair_cids(texto: str) -> list[str]:
    """Retorna lista de códigos CID encontrados no texto, normalizados (sem espaços)."""
    # Remover prefixos "CID10", "CID 10", "CID11", "CID 11" antes de buscar
    t = re.sub(r'\bCID\s*\d+\s*', '', texto.upper())
    # Colapsar espaço entre F e o número: "F 84.0" → "F84.0"
    t = re.sub(r'\bF\s+([0-9])', r'F\1', t)
    return [m.group(0).strip() for m in _RE_CID.finditer(t)]


def normalizar_descricao_transtorno(texto: Optional[str]) -> str:
    """
    Normaliza o campo *descricao_transtorno* para um label padronizado e legível.

    Prioridade de detecção:
      1. Siglas/palavras-chave conhecidas no texto (TEA, TDAH, TDO …)
      2. Código CID extraído e mapeado para a sigla correspondente
      3. Se nada reconhecido, mantém o valor original sem alteração

    Múltiplos transtornos são separados por ' / '.
    """
    if not texto:
        return 'Nenhum'
    t = str(texto).strip()
    if not t or t.upper() in ('NENHUM', 'NONE', 'NULL', '0', ''):
        return 'Nenhum'

    t_upper = t.upper()
    encontrados: list[str] = []

    # ── 1) Buscar siglas/palavras-chave ──────────────────────────────────────
    for chave, label in _SIGLAS:
        # word-boundary para siglas curtas; substring simples para frases
        padrao = r'\b' + re.escape(chave) + r'\b' if ' ' not in chave else re.escape(chave)
        if re.search(padrao, t_upper) and label not in encontrados:
            encontrados.append(label)

    # ── 2) Extrair e mapear códigos CID ──────────────────────────────────────
    for codigo in _extrair_cids(t):
        cod_norm = codigo.upper().replace(' ', '')
        mapped = _CID_MAP.get(cod_norm) or _CID_MAP.get(cod_norm.replace('.', ''))
        if mapped and mapped not in encontrados:
            encontrados.append(mapped)

    if not encontrados:
        # Valor não reconhecido: retornar capitalizado sem código CID
        return t.strip()

    return ' / '.join(encontrados)


def montar_transtorno_geduc(aluno: dict) -> str:
    """
    Constrói o valor normalizado de *descricao_transtorno* a partir dos campos
    brutos do GEDUC:  descricao_transtorno, cid, tgd, althab.

    Usa o campo textual como fonte principal; complementa com as flags tgd/althab
    quando o campo textual não oferece informação suficiente.
    """
    desc = aluno.get('descricao_transtorno', '') or ''
    cid  = aluno.get('cid', '') or ''
    tgd  = str(aluno.get('tgd', '0')).strip()
    althab = str(aluno.get('althab', '0')).strip()

    # Combinar descricao_transtorno + cid em um único texto para análise
    texto_combinado = ' '.join(filter(None, [desc, cid])).strip()

    resultado = normalizar_descricao_transtorno(texto_combinado or None)

    # Complementar com flags quando o texto não trouxe informação
    partes = [p.strip() for p in resultado.split('/') if p.strip() != 'Nenhum']

    if tgd == '1' and 'TEA' not in partes:
        partes.insert(0, 'TEA')

    if althab == '1' and 'Altas Habilidades' not in partes:
        partes.append('Altas Habilidades')

    return ' / '.join(partes) if partes else 'Nenhum'
