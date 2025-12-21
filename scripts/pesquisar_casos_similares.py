#!/usr/bin/env python3
from pathlib import Path
import csv
import json
from datetime import datetime
ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from db.connection import get_cursor

DET_PATH = ROOT / 'config' / 'detalhes_escolas_geduc.json'
MAP_PATH = ROOT / 'config' / 'mapeamento_curado_80.json'
OUT_DIR = ROOT / 'config'

def load_detalhes():
    if not DET_PATH.exists():
        return {}
    d = json.loads(DET_PATH.read_text(encoding='utf-8'))
    by_inep = {}
    by_id = {}
    for e in d.get('escolas', []):
        inep = e.get('CODIGOINEP')
        idg = e.get('id_geduc') or e.get('IDINSTITUICAO')
        if inep:
            by_inep[str(inep)] = e
        if idg:
            by_id[int(idg)] = e
    return by_inep, by_id


def load_map():
    if not MAP_PATH.exists():
        return {}
    mdata = json.loads(MAP_PATH.read_text(encoding='utf-8'))
    by_local = {e.get('id_local'): e for e in mdata.get('escolas', []) if e.get('id_local')}
    by_geduc = {}
    for e in mdata.get('escolas', []):
        idg = e.get('id_geduc')
        if idg:
            by_geduc.setdefault(int(idg), []).append(e)
    return by_local, by_geduc


def find_missing():
    by_inep, by_id = load_detalhes()
    by_local_map, by_geduc_map = load_map()

    out = []
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, nome, inep, telefone, cep, bairro, id_geduc, nome_geduc
            FROM escolas
            WHERE (telefone IS NULL OR telefone = '' OR cep IS NULL OR cep = '' OR bairro IS NULL OR bairro = '' OR id_geduc IS NULL OR nome_geduc IS NULL OR nome_geduc = '')
            """
        )
        rows = cur.fetchall()
        for r in rows:
            rec = dict(r)
            # tentar enriquecer com GEDUC por id_geduc, por inep, por mapping
            geduc_from_id = None
            geduc_from_inep = None
            geduc_from_map = None
            if rec.get('id_geduc'):
                geduc_from_id = by_id.get(int(rec['id_geduc']))
            if rec.get('inep'):
                geduc_from_inep = by_inep.get(str(rec['inep']))
            # tentar encontrar mapping por local id
            mapped = by_local_map.get(rec['id'])
            if mapped:
                geduc_from_map = mapped
            # também tentar mapear por nome_geduc via by_geduc_map if nome_geduc exists
            suggestions = []
            if geduc_from_id:
                suggestions.append(('by_id', geduc_from_id))
            if geduc_from_inep:
                suggestions.append(('by_inep', geduc_from_inep))
            if geduc_from_map:
                suggestions.append(('by_map', geduc_from_map))

            out.append((rec, suggestions))
    return out


def write_csv(results):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = OUT_DIR / f'casos_similares_{ts}.csv'
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['local_id','local_nome','local_inep','local_telefone','local_cep','local_bairro','local_id_geduc','local_nome_geduc','suggestions'])
        for rec, suggestions in results:
            sug_text = '|'.join([f"{k}:{json.dumps(v, ensure_ascii=False)}" for k,v in suggestions]) if suggestions else ''
            w.writerow([
                rec.get('id'), rec.get('nome'), rec.get('inep'), rec.get('telefone'), rec.get('cep'), rec.get('bairro'), rec.get('id_geduc'), rec.get('nome_geduc'), sug_text
            ])
    return out_path


if __name__ == '__main__':
    results = find_missing()
    print('Casos encontrados:', len(results))
    if results:
        p = write_csv(results)
        print('CSV salvo em:', p)
    else:
        print('Nenhum caso semelhante encontrado')
