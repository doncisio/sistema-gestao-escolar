#!/usr/bin/env python3
"""Sincroniza detalhes de escolas extraídos do GEDUC para a tabela local `escolas`.

Fluxo:
- Garante colunas adicionais na tabela `escolas` (telefone, cep, bairro, id_geduc, nome_geduc)
- Para cada escola em `config/detalhes_escolas_geduc.json` tenta atualizar na ordem:
  1) por mapeamento em `config/mapeamento_curado_80.json` (id_local)
  2) por `inep` (CODIGOINEP)
  3) por `nome` exato == `NOME` do GEDUC
  4) senão, insere novo registro usando `nome` = `nome_geduc` (padrão solicitado)

Uso: python scripts/sincronizar_escolas_geduc.py
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from db.connection import get_cursor
DET_PATH = ROOT / 'config' / 'detalhes_escolas_geduc.json'
MAP_CURADO = ROOT / 'config' / 'mapeamento_curado_80.json'

MUNICIPIO_PADRAO = 'Paço do Lumiar - MA'


def normalize_name(nome: str) -> str:
    if not nome:
        return nome
    # tokens que devem ficar em caixa baixa quando não são a primeira palavra
    small_words = {'da', 'de', 'do', 'dos', 'das', 'e'}
    # siglas que queremos preservar em maiúsculas
    acronyms = {'EM', 'UEB', 'UI', 'EE', 'IES', 'EEB'}

    parts = nome.strip().split()
    out = []
    for i, tok in enumerate(parts):
        up = tok.upper()
        if up in acronyms:
            out.append(up)
            continue
        t = tok.capitalize()
        if i != 0 and t.lower() in small_words:
            out.append(t.lower())
        else:
            out.append(t)
    return ' '.join(out)


def _match_name_ci(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return a.strip().lower() == b.strip().lower()


def ensure_columns(cur):
    # verificar colunas existentes
    cur.execute("SHOW COLUMNS FROM escolas")
    cols = {r['Field'] for r in cur.fetchall()}
    to_add = []
    if 'telefone' not in cols:
        to_add.append("ADD COLUMN telefone VARCHAR(32)")
    if 'cep' not in cols:
        to_add.append("ADD COLUMN cep VARCHAR(16)")
    if 'bairro' not in cols:
        to_add.append("ADD COLUMN bairro VARCHAR(128)")
    if 'id_geduc' not in cols:
        to_add.append("ADD COLUMN id_geduc INT")
    if 'nome_geduc' not in cols:
        to_add.append("ADD COLUMN nome_geduc VARCHAR(255)")

    if to_add:
        sql = "ALTER TABLE escolas " + ", ".join(to_add)
        cur.execute(sql)
        print("Colunas adicionadas:", to_add)
    else:
        print("Colunas já presentes, nenhum ALTER necessário")


def load_mapeamento():
    if not MAP_CURADO.exists():
        return {}
    data = json.loads(MAP_CURADO.read_text(encoding='utf-8'))
    m = {}
    for e in data.get('escolas', []):
        id_geduc = e.get('id_geduc')
        id_local = e.get('id_local')
        if id_geduc and id_local:
            m.setdefault(int(id_geduc), []).append(int(id_local))
    return m


def sincronizar():
    detalhes = json.loads(DET_PATH.read_text(encoding='utf-8'))
    escolas = detalhes.get('escolas', [])
    mapeamento = load_mapeamento()

    updated = 0
    inserted = 0
    skipped = 0

    with get_cursor(commit=True) as cur:
        ensure_columns(cur)

        for e in escolas:
            id_geduc = e.get('id_geduc')
            nome_geduc = e.get('nome_geduc') or e.get('NOME')
            inep = e.get('CODIGOINEP') or e.get('CODIGOINEP')
            endereco = e.get('ENDERECO')
            telefone = e.get('TELEFONE')
            cep = e.get('CEP')
            bairro = e.get('BAIRRO')


            # 1) tenta por mapeamento curado (pode mapear para múltiplos ids locais)
            rows = []
            if id_geduc in mapeamento:
                for lid in mapeamento[id_geduc]:
                    cur.execute("SELECT * FROM escolas WHERE id = %s", (lid,))
                    fetched = cur.fetchall()
                    if fetched:
                        rows.extend(fetched)

            # 2) por inep (ATUALIZAR TODAS AS ESCOLAS COM MESMO INEP)
            if not rows and inep:
                cur.execute("SELECT * FROM escolas WHERE inep = %s", (inep,))
                rows = cur.fetchall()

            # 3) por nome exato
            if not rows and nome_geduc:
                cur.execute("SELECT * FROM escolas WHERE nome = %s", (nome_geduc,))
                rows = cur.fetchall()

            # regras especiais de nomes
            # permite atualizar o campo `nome` apenas para este registro
            allow_nome_update_whitelist = {
                'Escola Municipal Profª Nadir Nascimento Moraes'
            }
            # nomes cujo `nome` não pode ser alterado; em caso de 'UEB Monteiro Lobato' inserir também novo registro
            protect_name_prefixes = [
                'ueb monteiro lobato',
                'ueb profª nadir nascimento moraes',
                'ui profª nadir nascimento moraes',
            ]

            inserted_for_this = False

            if rows:
                for row in rows:
                    local_id = row['id']
                    local_name = row.get('nome') or ''

                    # decidir se atualiza o nome
                    allow_update_name = False
                    if _match_name_ci(local_name, list(allow_nome_update_whitelist)[0]):
                        allow_update_name = True

                    # proteger prefixos/nomes específicos
                    need_insert_also = False
                    ln_low = local_name.strip().lower()
                    for p in protect_name_prefixes:
                        if ln_low.startswith(p):
                            # nunca atualiza o campo `nome` para esses
                            allow_update_name = False
                            if p == 'ueb monteiro lobato':
                                need_insert_also = True
                            break

                    # montar update dinâmico (não sobrescrever nome quando não permitido)
                    fields = ['endereco=%s', 'telefone=%s', 'cep=%s', 'bairro=%s', 'id_geduc=%s', 'nome_geduc=%s', 'inep=%s', 'municipio=%s']
                    params = [endereco, telefone, cep, bairro, id_geduc, nome_geduc, inep, MUNICIPIO_PADRAO]
                    if allow_update_name:
                        fields.insert(0, 'nome=%s')
                        params.insert(0, nome_geduc)

                    sql = f"UPDATE escolas SET {', '.join(fields)} WHERE id=%s"
                    params.append(local_id)
                    cur.execute(sql, tuple(params))
                    updated += 1

                    # regra: para UEB Monteiro Lobato, além do update (sem trocar nome), insere um novo registro com nome atual
                    if need_insert_also and not inserted_for_this:
                        new_nome = normalize_name(nome_geduc)
                        # evitar inserir se já existe escola com o mesmo nome exato
                        cur.execute("SELECT id FROM escolas WHERE nome = %s LIMIT 1", (new_nome,))
                        if not cur.fetchone():
                            cur.execute(
                                """
                                INSERT INTO escolas (nome, endereco, inep, cnpj, municipio, telefone, cep, bairro, id_geduc, nome_geduc)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                (new_nome, endereco, inep, None, MUNICIPIO_PADRAO, telefone, cep, bairro, id_geduc, nome_geduc),
                            )
                            inserted += 1
                            inserted_for_this = True

            else:
                # insert (nome normalizado para inserção)
                new_nome = normalize_name(nome_geduc)
                cur.execute("SELECT id FROM escolas WHERE nome = %s LIMIT 1", (new_nome,))
                if cur.fetchone():
                    # já existe um registro com esse nome normalizado: só atualiza esse registro (sem alterar nome)
                    cur.execute("SELECT * FROM escolas WHERE nome = %s LIMIT 1", (new_nome,))
                    existing = cur.fetchone()
                    if existing:
                        cur.execute(
                            """
                            UPDATE escolas SET endereco=%s, telefone=%s, cep=%s, bairro=%s, id_geduc=%s, nome_geduc=%s, inep=%s, municipio=%s
                            WHERE id=%s
                            """,
                            (endereco, telefone, cep, bairro, id_geduc, nome_geduc, inep, MUNICIPIO_PADRAO, existing['id']),
                        )
                        updated += 1
                else:
                    cur.execute(
                        """
                        INSERT INTO escolas (nome, endereco, inep, cnpj, municipio, telefone, cep, bairro, id_geduc, nome_geduc)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (new_nome, endereco, inep, None, MUNICIPIO_PADRAO, telefone, cep, bairro, id_geduc, nome_geduc),
                    )
                    inserted += 1

    print(f"Sincronização completa. Atualizadas: {updated}, Inseridas: {inserted}, Ignoradas: {skipped}")


if __name__ == '__main__':
    sincronizar()
