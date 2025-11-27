#!/usr/bin/env python3
"""
Importa habilidades BNCC a partir do arquivo Excel `MapasDeFocoBncc_Unificados.xlsx`
para a tabela `bncc_habilidades`.

O script tenta mapear colunas comuns automaticamente (codigo, descricao, area,
competencia, etapa, componente, ano, nivel, origem). Se não encontrar colunas
compatíveis, lista as colunas detectadas e encerra.

Uso:
  python importar_bncc_from_excel.py --file C:\gestao\MapasDeFocoBncc_Unificados.xlsx --user doncisio --database redeescola

O script pedirá a senha MySQL.
"""
import argparse
import getpass
import os
import sys
import pandas as pd
import mysql.connector
from mysql.connector import errorcode
from bncc_parser import parse_bncc_code

COMMON_NAMES = {
    'codigo': ['codigo','código','cod','code','id_habilidade','id'],
    'descricao': ['descricao','descrição','descricao_habilidade','habilidade','texto'],
    'area': ['area','área','dominio','domínio'],
    'competencia': ['competencia','competência','competência_nome','competência_codigo','competencia_nome'],
    'etapa': ['etapa','fase','nivel','etapa_sigla'],
    'componente': ['componente','disciplina','componente_curricular','componente_codigo'],
    'ano': ['ano','ano_referencia','ano_bloco'],
    'nivel': ['nivel','nível'],
    'origem': ['origem','fonte']
}


def find_column(columns, candidates):
    cols_lower = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    # try contains
    for cand in candidates:
        for c in columns:
            if cand.lower() in c.lower():
                return c
    return None


def map_columns(df_columns):
    mapping = {}
    for key, candidates in COMMON_NAMES.items():
        col = find_column(df_columns, candidates)
        mapping[key] = col
    return mapping


def insert_rows(df, mapping, conn, batch_size=200):
    cursor = conn.cursor()
    insert_sql = '''
    INSERT INTO bncc_habilidades
    (codigo, descricao, area, competencia, etapa, componente, ano, nivel, origem,
     codigo_raw, etapa_sigla, grupo_faixa, campo_experiencias, ano_bloco, componente_codigo, em_competencia, em_sequencia)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
      descricao=VALUES(descricao), area=VALUES(area), competencia=VALUES(competencia), etapa=VALUES(etapa),
      componente=VALUES(componente), ano=VALUES(ano), nivel=VALUES(nivel), origem=VALUES(origem),
      codigo_raw=VALUES(codigo_raw), etapa_sigla=VALUES(etapa_sigla), grupo_faixa=VALUES(grupo_faixa),
      campo_experiencias=VALUES(campo_experiencias), ano_bloco=VALUES(ano_bloco), componente_codigo=VALUES(componente_codigo),
      em_competencia=VALUES(em_competencia), em_sequencia=VALUES(em_sequencia), updated_at=CURRENT_TIMESTAMP
    '''

    total = len(df)
    count = 0
    for idx, row in df.iterrows():
        codigo = row.get(mapping['codigo']) if mapping['codigo'] else None
        if pd.isna(codigo) or not str(codigo).strip():
            # skip empty codes
            continue
        codigo = str(codigo).strip()
        descricao = row.get(mapping['descricao']) if mapping['descricao'] else None
        area = row.get(mapping['area']) if mapping['area'] else None
        competencia = row.get(mapping['competencia']) if mapping['competencia'] else None
        etapa = row.get(mapping['etapa']) if mapping['etapa'] else None
        componente = row.get(mapping['componente']) if mapping['componente'] else None
        ano = row.get(mapping['ano']) if mapping['ano'] else None
        nivel = row.get(mapping['nivel']) if mapping['nivel'] else None
        origem = row.get(mapping['origem']) if mapping['origem'] else None

        # ensure strings
        descricao = str(descricao).strip() if descricao is not None and not pd.isna(descricao) else None
        area = str(area).strip() if area is not None and not pd.isna(area) else None
        competencia = str(competencia).strip() if competencia is not None and not pd.isna(competencia) else None
        etapa = str(etapa).strip() if etapa is not None and not pd.isna(etapa) else None
        componente = str(componente).strip() if componente is not None and not pd.isna(componente) else None
        ano = str(ano).strip() if ano is not None and not pd.isna(ano) else None
        nivel = str(nivel).strip() if nivel is not None and not pd.isna(nivel) else None
        origem = str(origem).strip() if origem is not None and not pd.isna(origem) else None

        parsed = parse_bncc_code(codigo)

        values = (
            codigo, descricao, area, competencia, etapa, componente, ano, nivel, origem,
            parsed.get('codigo_raw'), parsed.get('etapa_sigla'), parsed.get('grupo_faixa'),
            parsed.get('campo_experiencias'), parsed.get('ano_bloco'), parsed.get('componente_codigo'),
            parsed.get('em_competencia'), parsed.get('em_sequencia')
        )
        try:
            cursor.execute(insert_sql, values)
            count += 1
            if count % batch_size == 0:
                conn.commit()
                print(f"Committed {count}/{total}")
        except Exception as e:
            print(f"Erro inserindo codigo={codigo}: {e}")

    conn.commit()
    cursor.close()
    print(f"Import completed. Total inserted/updated: {count}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Importar BNCC do Excel para MySQL')
    parser.add_argument('--file', default=r'C:\gestao\MapasDeFocoBncc_Unificados.xlsx')
    parser.add_argument('--sheet', default=None, help='Nome da planilha (opcional)')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', default=3306, type=int)
    parser.add_argument('--user', required=True)
    parser.add_argument('--database', required=True)
    parser.add_argument('--password', help='Senha (opcional)')
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Arquivo não encontrado: {args.file}")
        sys.exit(1)

    print("Lendo Excel...")
    try:
        df = pd.read_excel(args.file, sheet_name=args.sheet)
    except Exception as e:
        print(f"Erro lendo Excel: {e}")
        sys.exit(1)

    print(f"Colunas detectadas: {list(df.columns)}")
    mapping = map_columns(list(df.columns))
    print("Mapeamento automático proposto:")
    for k,v in mapping.items():
        print(f"  {k}: {v}")

    # if key columns missing, abort and ask user to inspect
    if not mapping['codigo'] or not mapping['descricao']:
        print("Não foi possível detectar automaticamente as colunas 'codigo' ou 'descricao'. Revise as colunas do arquivo e renomeie-as ou informe mapping manualmente.")
        sys.exit(1)

    pwd = args.password or getpass.getpass(prompt=f"Senha para {args.user}@{args.host}: ")

    try:
        conn = mysql.connector.connect(host=args.host, port=args.port, user=args.user, password=pwd, database=args.database, charset='utf8mb4')
    except mysql.connector.Error as err:
        print(f"Erro conectando ao banco: {err}")
        sys.exit(1)

    insert_rows(df, mapping, conn)
    conn.close()

    print("Importação finalizada.")
