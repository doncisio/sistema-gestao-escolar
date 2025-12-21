#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from db.connection import get_cursor

with get_cursor() as cur:
    cur.execute('SELECT id, nome, inep, telefone, cep, bairro, id_geduc, nome_geduc FROM escolas WHERE id IN (3,4,6)')
    rows = cur.fetchall()
    if not rows:
        print('Nenhum registro encontrado para ids', ids)
    else:
        print('id|nome|inep|telefone|cep|bairro|id_geduc|nome_geduc')
        for r in rows:
            print(f"{r['id']}|{r.get('nome') or ''}|{r.get('inep') or ''}|{r.get('telefone') or ''}|{r.get('cep') or ''}|{r.get('bairro') or ''}|{r.get('id_geduc') or ''}|{r.get('nome_geduc') or ''}")
