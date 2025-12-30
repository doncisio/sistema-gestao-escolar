"""
Utilitário para mapear valores de horário (texto livre) para IDs de disciplinas e professores.
"""
import unicodedata
import re
from typing import List, Dict, Tuple, Optional


def _norm(s: str) -> str:
    """
    Normaliza string removendo acentos, pontuação, colapsando espaços e convertendo para maiúsculas.
    
    Args:
        s: String a normalizar
        
    Returns:
        String normalizada (uppercase, sem acentos/pontuação, espaços colapsados)
    """
    if not s:
        return ''
    s = s.strip()
    # Remover acentos
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    # Remover pontuação, manter apenas alfanuméricos e espaços
    s = re.sub(r'[^0-9A-Za-z\s]', ' ', s)
    # Colapsar múltiplos espaços
    s = re.sub(r'\s+', ' ', s)
    return s.strip().upper()


def mapear_disc_prof(
    valor: str,
    disciplinas: List[Dict],
    professores: List[Dict],
    mapeamentos: Dict[str, Dict[str, int]]
) -> Tuple[Optional[int], Optional[int]]:
    """
    Mapeia um valor de horário (texto livre) para IDs de disciplina e professor.
    
    Estratégia de mapeamento:
    1. Tenta extrair disciplina e professor do formato "DISCIPLINA (Professor)"
    2. Busca disciplina por nome exato (case-insensitive)
    3. Se não encontrar, usa mapeamentos locais (aliases) para disciplina
    4. Busca professor por nome completo ou primeiro nome
    5. Se não encontrar, usa mapeamentos locais (aliases) para professor
    
    Args:
        valor: Texto do horário (ex: "MATEMÁTICA (Maria Silva)" ou "RECREIO")
        disciplinas: Lista de dicts com 'id' e 'nome' das disciplinas disponíveis
        professores: Lista de dicts com 'id' e 'nome' dos professores disponíveis
        mapeamentos: Dict com chaves 'disciplinas' e 'professores', 
                     cada uma mapeando nome normalizado -> id
    
    Returns:
        Tupla (disciplina_id, professor_id), onde cada valor pode ser None se não mapeado
    """
    valor = (valor or '').strip()
    disc_id = None
    prof_id = None
    
    # Tentar extrair disciplina e professor do texto formatado "DISCIPLINA (Professor)"
    if " (" in valor and ")" in valor:
        disc_text = valor.split(" (", 1)[0].strip()
        prof_text = valor.split(" (", 1)[1].rstrip(')')
    else:
        disc_text = valor
        prof_text = ''
    
    # Procurar disciplina por nome exato (case-insensitive)
    for d in (disciplinas or []):
        if not isinstance(d, dict):
            continue
        nome_disc = d.get('nome')
        if nome_disc and nome_disc.strip().upper() == disc_text.upper():
            disc_id = d.get('id')
            break
    
    # Se não encontrou, usar mapeamentos locais para disciplina
    if not disc_id and mapeamentos:
        keyd = _norm(valor)
        disc_id = mapeamentos.get('disciplinas', {}).get(keyd)
    
    # Procurar professor por nome completo ou primeiro nome
    if prof_text:
        for p in (professores or []):
            if not isinstance(p, dict):
                continue
            nome_prof = p.get('nome') or ''
            # Match exato ou match por prefixo (primeiro nome)
            if nome_prof.strip().upper() == prof_text.strip().upper() or \
               nome_prof.upper().startswith(prof_text.upper()):
                prof_id = p.get('id')
                break
    
    # Se não encontrou, usar mapeamentos locais para professor
    if not prof_id and mapeamentos:
        # Tenta mapear pelo texto do professor ou pelo valor completo
        keyp = _norm(prof_text or valor)
        prof_id = mapeamentos.get('professores', {}).get(keyp)
    
    return disc_id, prof_id
