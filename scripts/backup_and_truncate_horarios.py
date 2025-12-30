#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import csv
from src.core.conexao import conectar_bd

OUTDIR = Path(r"c:/gestao/historico_geduc_imports")
OUTDIR.mkdir(parents=True, exist_ok=True)

def backup_and_truncate():
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out = OUTDIR / f'backup_horarios_{ts}.csv'
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute('SELECT * FROM horarios_importados')
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    with out.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow(r)

    print('Backup salvo em', out)
    # truncar tabela
    cur.execute('TRUNCATE TABLE horarios_importados')
    conn.commit()
    cur.close()
    conn.close()
    print('Tabela horarios_importados truncada.')

if __name__ == '__main__':
    backup_and_truncate()
