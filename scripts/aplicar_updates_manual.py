#!/usr/bin/env python3
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from db.connection import get_cursor

MAP_CURADO = ROOT / 'config' / 'mapeamento_curado_80.json'

data = json.loads(MAP_CURADO.read_text(encoding='utf-8'))
ids = {3,4,6}
with get_cursor(commit=True) as cur:
    for e in data.get('escolas', []):
        id_local = e.get('id_local')
        if id_local in ids:
            id_geduc = e.get('id_geduc')
            nome_geduc = e.get('nome_geduc')
            det = e.get('detalhes_geduc', {})
            endereco = det.get('ENDERECO')
            telefone = det.get('TELEFONE')
            cep = det.get('CEP')
            bairro = det.get('BAIRRO')
            inep = det.get('CODIGOINEP')
            cur.execute(
                """
                UPDATE escolas SET endereco=%s, telefone=%s, cep=%s, bairro=%s, id_geduc=%s, nome_geduc=%s, inep=%s, municipio=%s
                WHERE id=%s
                """,
                (endereco, telefone, cep, bairro, id_geduc, nome_geduc, inep, 'Paço do Lumiar - MA', id_local),
            )
            print(f'Updated id={id_local}')
print('Done')
