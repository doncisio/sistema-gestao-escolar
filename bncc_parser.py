import re
from typing import Dict, Optional


def parse_bncc_code(code: str) -> Dict[str, Optional[str]]:
    """Parse a BNCC ability code into components.

    Supports formats such as:
    - EI02TS01  (Educação Infantil)
    - EF67EF01  (Ensino Fundamental)
    - EF15LP01  (Língua Portuguesa bloco 1-5)
    - EM13LGG103 (Ensino Médio)

    Returns a dict with keys (may be None if not applicable):
      codigo_raw, etapa_sigla, grupo_faixa, campo_experiencias,
      ano_bloco, componente_codigo, em_competencia, em_sequencia
    """
    if not code or not isinstance(code, str):
        return {k: None for k in ['codigo_raw','etapa_sigla','grupo_faixa','campo_experiencias','ano_bloco','componente_codigo','em_competencia','em_sequencia']}

    c = code.strip().upper()
    parsed = {
        'codigo_raw': c,
        'etapa_sigla': None,
        'grupo_faixa': None,
        'campo_experiencias': None,
        'ano_bloco': None,
        'componente_codigo': None,
        'em_competencia': None,
        'em_sequencia': None
    }

    # Educação Infantil: EI + 2 dígitos (grupo) + 2 letras (campo) + 2 dígitos (posição)
    m = re.match(r'^(EI)(\d{2})([A-Z]{2})(\d{2})$', c)
    if m:
        parsed.update({
            'etapa_sigla': m.group(1),
            'grupo_faixa': m.group(2),
            'campo_experiencias': m.group(3),
            'ano_bloco': None,
            'componente_codigo': None
        })
        return parsed

    # Ensino Fundamental: EF + 2 dígitos (ano/bloco) + 2 letras (componente) + 2 dígitos (posição)
    m = re.match(r'^(EF)(\d{2})([A-Z]{2})(\d{2})$', c)
    if m:
        parsed.update({
            'etapa_sigla': m.group(1),
            'ano_bloco': m.group(2),
            'componente_codigo': m.group(3)
        })
        return parsed

    # Ensino Médio: EM + 2 dígitos (13 = qualquer série do EM) + área/componente (2-3 letras) + 3 dígitos (c + nn)
    m = re.match(r'^(EM)(\d{2})([A-Z]{2,3})(\d{3})$', c)
    if m:
        comp = m.group(3)
        last = m.group(4)
        em_comp = int(last[0])
        em_seq = int(last[1:])
        parsed.update({
            'etapa_sigla': m.group(1),
            'ano_bloco': m.group(2),
            'componente_codigo': comp,
            'em_competencia': em_comp,
            'em_sequencia': em_seq
        })
        return parsed

    # Caso não reconhecido: tentar padrões alternativos
    # Ex.: alguns códigos podem ter 3 letras de componente no EF (raro), ou variações.
    # Tentativa genérica: extrair prefixo de letras, números no meio e sufixo de letras/dígitos
    m = re.match(r'^([A-Z]{2})(\d{2})([A-Z]{2,3})(\d{2,3})$', c)
    if m:
        etapa = m.group(1)
        parsed['etapa_sigla'] = etapa
        parsed['ano_bloco'] = m.group(2)
        parsed['componente_codigo'] = m.group(3)
        last = m.group(4)
        if len(last) == 3:
            try:
                parsed['em_competencia'] = int(last[0])
                parsed['em_sequencia'] = int(last[1:])
            except Exception:
                pass
        return parsed

    return parsed


if __name__ == '__main__':
    samples = [
        'EI02TS01',
        'EF67EF01',
        'EM13LGG103',
        'EF15LP01',
        'EI01EO05',
        'EM13MAT205',
        'XYZ'
    ]
    for s in samples:
        print(f"{s} -> {parse_bncc_code(s)}")
