import re
from typing import List

PREREQ_PATTERN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z]{2,3}\d{2,3}\b")

def normalize_code(s: str) -> str:
    if not s:
        return ''
    return s.strip().upper().replace('\u00A0', ' ')

def extract_bncc_codes(text: str) -> List[str]:
    """Extrai códigos BNCC de um texto e retorna lista sem duplicatas na ordem."""
    if not text:
        return []
    s = normalize_code(str(text))
    codes = PREREQ_PATTERN.findall(s)
    seen = set()
    out = []
    for c in codes:
        c = c.strip()
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out
