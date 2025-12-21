#!/usr/bin/env python3
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
MAP_CURADO = ROOT / 'config' / 'mapeamento_curado_80.json'
ids = {60,76,77,99}

data = json.loads(MAP_CURADO.read_text(encoding='utf-8'))
for e in data.get('escolas', []):
    if e.get('id_local') in ids:
        print(json.dumps(e, ensure_ascii=False))
