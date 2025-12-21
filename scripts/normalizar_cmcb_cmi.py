#!/usr/bin/env python3
from pathlib import Path
import re
import json
ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from db.connection import get_cursor

DET_PATH = ROOT / 'config' / 'detalhes_escolas_geduc.json'

pattern_cmcb = re.compile(r'cmcb', re.IGNORECASE)
pattern_cmi = re.compile(r'cmi', re.IGNORECASE)

updated_db = 0
updated_json = 0

with get_cursor(commit=True) as cur:
    cur.execute("SELECT id, nome FROM escolas WHERE LOWER(nome) LIKE '%cmcb%' OR LOWER(nome) LIKE '%cmi%'")
    rows = cur.fetchall()
    for r in rows:
        lid = r['id']
        nome = r['nome'] or ''
        novo = pattern_cmcb.sub('CMCB', nome)
        novo = pattern_cmi.sub('CMI', novo)
        if novo != nome:
            cur.execute('UPDATE escolas SET nome=%s WHERE id=%s', (novo, lid))
            updated_db += 1

# atualizar detalhes JSON
if DET_PATH.exists():
    data = json.loads(DET_PATH.read_text(encoding='utf-8'))
    changed = False
    for e in data.get('escolas', []):
        nome = e.get('NOME') or e.get('nome') or ''
        novo = pattern_cmcb.sub('CMCB', nome)
        novo = pattern_cmi.sub('CMI', novo)
        if novo != nome:
            e['NOME'] = novo
            changed = True
            updated_json += 1
    if changed:
        bak = DET_PATH.with_suffix('.json.bak')
        DET_PATH.replace(bak)
        DET_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

print(f'Registros do DB atualizados: {updated_db}')
print(f'Entradas no JSON atualizadas: {updated_json}')
