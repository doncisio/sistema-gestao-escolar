#!/usr/bin/env python3
"""
Mapeia turmas GEDUC (geduc_turma_id em `horarios_importados`) para turmas locais
da escola 60/ano 2025, usando heurísticas de nome e dados salvos em HTML/JSON.

Se houver correspondência única, atualiza `turmas.geduc_id` e realinha
`horarios_importados.turma_id` para o `turmas.id` local.

NÃO cria turmas locais novas; apenas sugere e aplica mapeamentos para existentes.
"""
from pathlib import Path
import re
import unicodedata
import json
from src.core.conexao import conectar_bd
from src.importers.geduc_horarios import parse_horario_por_turma

BASE = Path(r"c:/gestao/historico_geduc_imports")


def norm(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^A-Za-z0-9]', '', s).upper()
    return s


def extract_name_from_saved(gid: int):
    # procurar JSON salvo horario_turma_{gid}.json
    j = BASE / f"horario_turma_{gid}.json"
    if j.exists():
        try:
            d = json.loads(j.read_text(encoding='utf-8'))
            nome = d.get('turma_nome')
            if nome:
                return nome
        except Exception:
            pass

    # procurar any html/json that contenha turma_id = gid
    for p in BASE.glob('horario_*.json'):
        try:
            d = json.loads(p.read_text(encoding='utf-8'))
            if d.get('turma_id') == gid:
                if d.get('turma_nome'):
                    return d.get('turma_nome')
                # tentar extrair do HTML source
                htmlp = Path(d.get('source_file') or '')
                if htmlp.exists():
                    try:
                        parsed = parse_horario_por_turma(htmlp)
                        tn = parsed.get('turma_nome')
                        if tn:
                            return tn
                    except Exception:
                        pass
        except Exception:
            continue

    # fallback: tentar abrir arquivos html/json e procurar padrão textual
    # procurar htmls genericos
    for h in BASE.glob('*.html'):
        try:
            txt = h.read_text(encoding='utf-8')
            # procurar frase exata usada pela interface GEDUC
            m = re.search(r"Cadastrar Hor.rio semanal para a turma[:\s]*([\w\W]{1,120})", txt, re.IGNORECASE)
            if m:
                candidate = m.group(1).split('\n')[0].strip()
                return candidate
            # fallback: procurar 'Horario de aula por turma: X'
            m2 = re.search(r"Hor.rio de aula por turma[:\s]*([\w\W]{1,120})", txt, re.IGNORECASE)
            if m2:
                return m2.group(1).split('\n')[0].strip()
        except Exception:
            continue

    return None


def main(dry_run=True):
    conn = conectar_bd()
    cur = conn.cursor(dictionary=True)

    # obter anoletivo id para 2025 se existir: detectar dinamicamente coluna texto
    ano_id = None
    cur.execute("SHOW TABLES LIKE 'anosletivos'")
    if cur.fetchall():
        # listar colunas
        cur.execute('SHOW COLUMNS FROM anosletivos')
        cols = [r['Field'] for r in cur.fetchall()]
        text_cols = cols
        for c in text_cols:
            try:
                cur.execute(f"SELECT id FROM anosletivos WHERE `{c}` LIKE %s LIMIT 1", ("2025%",))
                row = cur.fetchone()
                if row:
                    ano_id = row['id']
                    break
            except Exception:
                continue

    # carregar turmas locais da escola 60 e ano 2025
    if ano_id:
        cur.execute('SELECT t.id, t.nome, t.serie_id, t.turno, s.nome as serie_nome FROM turmas t LEFT JOIN series s ON s.id = t.serie_id WHERE t.escola_id = 60 AND t.ano_letivo_id = %s', (ano_id,))
    else:
        cur.execute('SELECT t.id, t.nome, t.serie_id, t.turno, s.nome as serie_nome FROM turmas t LEFT JOIN series s ON s.id = t.serie_id WHERE t.escola_id = 60')
    local_turmas = cur.fetchall()

    # show local turmas loaded
    print('\nLocal turmas carregadas (escola 60, ano 2025 se disponível):')
    for t in local_turmas:
        print('  id=', t['id'], 'serie=', t.get('serie_nome'), 'nome=', t.get('nome'), 'turno=', t.get('turno'))

    # build canonical names for locals
    local_map = {}
    for t in local_turmas:
        serie = (t.get('serie_nome') or '').strip()
        nome = (t.get('nome') or '').strip()
        turno = (t.get('turno') or '').strip()
        # variants for turno
        variants = []
        if turno.upper().startswith('MAT'):
            variants = ['M', 'MAT', 'MATUTINO']
        else:
            variants = ['V', 'VESP', 'VESPERTINO']

        candidates = []
        for tv in variants:
            cand = f"{serie}{nome}{tv}"
            candidates.append(norm(cand))

        local_map[t['id']] = {'raw': t, 'cands': candidates}

    # distinct geduc ids
    cur.execute('SELECT DISTINCT geduc_turma_id FROM horarios_importados WHERE geduc_turma_id IS NOT NULL')
    geducs = [r['geduc_turma_id'] for r in cur.fetchall()]

    report = []
    for gid in geducs:
        gname = extract_name_from_saved(gid)
        gnorm = norm(gname) if gname else None

        # try to match by normalized name
        matches = []
        if gnorm:
            for lid, info in local_map.items():
                if any(gnorm == cand for cand in info['cands']):
                    matches.append(lid)

        # if no gname or no exact match, try fuzzy: match by serie prefix
        if not matches:
            # try match by serie name appearing in any candidate
            for lid, info in local_map.items():
                serie_name = (info['raw'].get('serie_nome') or '')
                if serie_name and gname and serie_name.strip().upper() in gname.strip().upper():
                    matches.append(lid)

        report.append({'geduc_id': gid, 'geduc_name': gname, 'matched_local_ids': matches})

    # show report
    for r in report:
        print('GEDUC', r['geduc_id'], 'name=', r['geduc_name'], '=> matches=', r['matched_local_ids'])

    # apply updates for unique matches
    applied = []
    for r in report:
        gid = r['geduc_id']
        matches = r['matched_local_ids']
        if len(matches) == 1:
            lid = matches[0]
            print(f'Applying mapping GEDUC {gid} -> local {lid}')
            if not dry_run:
                # set turmas.geduc_id
                cur.execute('UPDATE turmas SET geduc_id = %s WHERE id = %s', (gid, lid))
                # update horarios_importados to point to local id where geduc_turma_id = gid
                cur.execute('UPDATE horarios_importados SET turma_id = %s WHERE geduc_turma_id = %s', (lid, gid))
                conn.commit()
            applied.append((gid, lid))

    cur.close()
    conn.close()

    print('\nDone. Applied mappings:', applied)


if __name__ == '__main__':
    main(dry_run=False)
