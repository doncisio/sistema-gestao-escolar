#!/usr/bin/env python3
"""Cria backup da tabela `escolas` e gera CSV de revisão das sincronizações.

Gera:
- sql/backup_escolas_<ts>.sql
- config/revisao_sincronizacao_escolas_<ts>.csv
"""
from pathlib import Path
import csv
import json
import datetime
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from db.connection import get_cursor

DET_PATH = ROOT / 'config' / 'detalhes_escolas_geduc.json'
MAP_CURADO = ROOT / 'config' / 'mapeamento_curado_80.json'

TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
OUT_SQL = ROOT / 'sql' / f'backup_escolas_{TS}.sql'
OUT_CSV = ROOT / 'config' / f'revisao_sincronizacao_escolas_{TS}.csv'


def dump_table(cur):
    # Show create
    cur.execute("SHOW CREATE TABLE escolas")
    row = cur.fetchone()
    # row may be dict or tuple
    if isinstance(row, dict):
        create_sql = row.get('Create Table')
    else:
        create_sql = row[1]
    # fetch all rows
    cur.execute("SELECT * FROM escolas")
    rows = cur.fetchall()

    with OUT_SQL.open('w', encoding='utf-8') as f:
        f.write(f"-- Backup gerado em {TS}\n")
        f.write(create_sql + ";\n\n")
        if rows:
            cols = list(rows[0].keys())
            for r in rows:
                vals = []
                for c in cols:
                    v = r[c]
                    if v is None:
                        vals.append('NULL')
                    else:
                        s = str(v).replace("'", "''")
                        vals.append(f"'{s}'")
                f.write(f"INSERT INTO escolas ({', '.join(cols)}) VALUES ({', '.join(vals)});\n")


def load_mapeamento():
    if not MAP_CURADO.exists():
        return {}
    data = json.loads(MAP_CURADO.read_text(encoding='utf-8'))
    m = {}
    for e in data.get('escolas', []):
        id_geduc = e.get('id_geduc')
        id_local = e.get('id_local')
        if id_geduc and id_local:
            m[int(id_geduc)] = int(id_local)
    return m


def gerar_csv(cur, mapeamento):
    detalhes = json.loads(DET_PATH.read_text(encoding='utf-8'))
    escolas = detalhes.get('escolas', [])

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        header = ['id_geduc','nome_geduc','CODIGOINEP','REGIAO','match_method','local_id','local_nome','local_inep','local_telefone','local_cep','local_bairro','action']
        writer.writerow(header)

        for e in escolas:
            id_geduc = e.get('id_geduc')
            nome_geduc = e.get('nome_geduc') or e.get('NOME')
            inep = e.get('CODIGOINEP')
            regiao = e.get('REGIAO')

            match_method = None
            local = None

            # 1) id_geduc column
            cur.execute("SELECT id,nome,inep,telefone,cep,bairro FROM escolas WHERE id_geduc = %s LIMIT 1", (id_geduc,))
            row = cur.fetchone()
            if row:
                match_method = 'id_geduc'
                local = row
            else:
                # 2) mapping
                if id_geduc in mapeamento:
                    lid = mapeamento[id_geduc]
                    cur.execute("SELECT id,nome,inep,telefone,cep,bairro FROM escolas WHERE id = %s LIMIT 1", (lid,))
                    row = cur.fetchone()
                    if row:
                        match_method = 'mapping'
                        local = row
                # 3) inep
                if local is None and inep:
                    cur.execute("SELECT id,nome,inep,telefone,cep,bairro FROM escolas WHERE inep = %s LIMIT 1", (inep,))
                    row = cur.fetchone()
                    if row:
                        match_method = 'inep'
                        local = row
                # 4) nome exact
                if local is None and nome_geduc:
                    cur.execute("SELECT id,nome,inep,telefone,cep,bairro FROM escolas WHERE nome = %s LIMIT 1", (nome_geduc,))
                    row = cur.fetchone()
                    if row:
                        match_method = 'nome'
                        local = row
                # 5) inserted (post-sync)
                if local is None:
                    cur.execute("SELECT id,nome,inep,telefone,cep,bairro FROM escolas WHERE id_geduc = %s LIMIT 1", (id_geduc,))
                    row = cur.fetchone()
                    if row:
                        match_method = 'inserted'
                        local = row

            action = 'updated' if match_method and match_method != 'inserted' else 'inserted'
            lid = local['id'] if local else ''
            lname = local.get('nome') if local else ''
            line = [id_geduc, nome_geduc, inep, regiao, match_method or '', lid, lname, local.get('inep') if local else '', local.get('telefone') if local else '', local.get('cep') if local else '', local.get('bairro') if local else '', action]
            writer.writerow(line)


def main():
    with get_cursor() as cur:
        dump_table(cur)
        mapeamento = load_mapeamento()
        gerar_csv(cur, mapeamento)

    print(f"Backup SQL salvo em: {OUT_SQL}")
    print(f"CSV de revisão salvo em: {OUT_CSV}")


if __name__ == '__main__':
    main()
