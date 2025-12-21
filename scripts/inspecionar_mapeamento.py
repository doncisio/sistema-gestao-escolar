#!/usr/bin/env python3
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
MAP_CURADO = ROOT / 'config' / 'mapeamento_curado_80.json'

data = json.loads(MAP_CURADO.read_text(encoding='utf-8'))
print('Procurando id_local 3,4,6 no mapeamento:')
for e in data.get('escolas', []):
    if e.get('id_local') in (3,4,6):
        print(json.dumps(e, ensure_ascii=False))
