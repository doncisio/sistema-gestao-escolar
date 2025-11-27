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
from bncc_utils import extract_bncc_codes, normalize_code

COMMON_NAMES = {
    'codigo': ['código da habilidade','codigo da habilidade','código','codigo','cod','code'],
    'descricao': ['texto da habilidade','descrição da habilidade','texto','descricao','descrição'],
    'conhecimento_previo': ['conhecimento prévio','conhecimento previo'],
    'unidade_tematica': ['unidade temática','unidade tematica','unidade'],
    'classificacao': ['classificação','classificacao'],
    'objetivos_aprendizagem': ['objetivos de aprendizagem','objetivos'],
    'competencias_relacionadas': ['competências relacionadas','competencias relacionadas'],
    'habilidades_relacionadas': ['habilidades relacionadas'],
    'comentarios': ['comentários','comentarios'],
    'campo_atuacao': ['campo de atuação','campo de atuacao'],
    'area': ['area','área'],
    'competencia': ['competencia','competência'],
    'etapa': ['etapa','fase'],
    'componente': ['componente','disciplina'],
    'ano': ['ano','ano_referencia'],
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
        (codigo, descricao, conhecimento_previo, unidade_tematica, classificacao, objetivos_aprendizagem,
         competencias_relacionadas, habilidades_relacionadas, comentarios, campo_atuacao,
         codigo_raw, etapa_sigla, grupo_faixa, campo_experiencias, ano_bloco, componente_codigo, em_competencia, em_sequencia)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            descricao=VALUES(descricao), conhecimento_previo=VALUES(conhecimento_previo),
            unidade_tematica=VALUES(unidade_tematica), classificacao=VALUES(classificacao),
            objetivos_aprendizagem=VALUES(objetivos_aprendizagem), competencias_relacionadas=VALUES(competencias_relacionadas),
            habilidades_relacionadas=VALUES(habilidades_relacionadas), comentarios=VALUES(comentarios),
            campo_atuacao=VALUES(campo_atuacao), codigo_raw=VALUES(codigo_raw), etapa_sigla=VALUES(etapa_sigla),
            grupo_faixa=VALUES(grupo_faixa), campo_experiencias=VALUES(campo_experiencias), ano_bloco=VALUES(ano_bloco),
            componente_codigo=VALUES(componente_codigo), em_competencia=VALUES(em_competencia), em_sequencia=VALUES(em_sequencia), updated_at=CURRENT_TIMESTAMP
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

        # Extrair todos os campos pedagógicos
        conhecimento_previo = None
        if mapping.get('conhecimento_previo'):
            conhecimento_previo = row.get(mapping['conhecimento_previo'])
            conhecimento_previo = str(conhecimento_previo).strip() if conhecimento_previo is not None and not pd.isna(conhecimento_previo) else None
        
        unidade_tematica = None
        if mapping.get('unidade_tematica'):
            unidade_tematica = row.get(mapping['unidade_tematica'])
            unidade_tematica = str(unidade_tematica).strip() if unidade_tematica is not None and not pd.isna(unidade_tematica) else None
        
        classificacao = None
        if mapping.get('classificacao'):
            classificacao = row.get(mapping['classificacao'])
            classificacao = str(classificacao).strip() if classificacao is not None and not pd.isna(classificacao) else None
        
        objetivos_aprendizagem = None
        if mapping.get('objetivos_aprendizagem'):
            objetivos_aprendizagem = row.get(mapping['objetivos_aprendizagem'])
            objetivos_aprendizagem = str(objetivos_aprendizagem).strip() if objetivos_aprendizagem is not None and not pd.isna(objetivos_aprendizagem) else None
        
        competencias_relacionadas = None
        if mapping.get('competencias_relacionadas'):
            competencias_relacionadas = row.get(mapping['competencias_relacionadas'])
            competencias_relacionadas = str(competencias_relacionadas).strip() if competencias_relacionadas is not None and not pd.isna(competencias_relacionadas) else None
        
        habilidades_relacionadas_texto = None
        if mapping.get('habilidades_relacionadas'):
            habilidades_relacionadas_texto = row.get(mapping['habilidades_relacionadas'])
            habilidades_relacionadas_texto = str(habilidades_relacionadas_texto).strip() if habilidades_relacionadas_texto is not None and not pd.isna(habilidades_relacionadas_texto) else None
        
        comentarios = None
        if mapping.get('comentarios'):
            comentarios = row.get(mapping['comentarios'])
            comentarios = str(comentarios).strip() if comentarios is not None and not pd.isna(comentarios) else None
        
        campo_atuacao = None
        if mapping.get('campo_atuacao'):
            campo_atuacao = row.get(mapping['campo_atuacao'])
            campo_atuacao = str(campo_atuacao).strip() if campo_atuacao is not None and not pd.isna(campo_atuacao) else None

        # valores para inserção: todos os campos
        values = (
            codigo,
            descricao,
            conhecimento_previo,
            unidade_tematica,
            classificacao,
            objetivos_aprendizagem,
            competencias_relacionadas,
            habilidades_relacionadas_texto,
            comentarios,
            campo_atuacao,
            parsed.get('codigo_raw'),
            parsed.get('etapa_sigla'),
            parsed.get('grupo_faixa'),
            parsed.get('campo_experiencias'),
            parsed.get('ano_bloco'),
            parsed.get('componente_codigo'),
            parsed.get('em_competencia'),
            parsed.get('em_sequencia')
        )
        try:
            cursor.execute(insert_sql, values)
            count += 1
            # obter id da habilidade inserida/atualizada
            conn.commit()
            cursor.execute("SELECT id FROM bncc_habilidades WHERE codigo = %s", (codigo,))
            rowid = cursor.fetchone()
            bncc_id = rowid[0] if rowid else None

            # processar pré-requisitos: extrair códigos do texto e inserir na tabela bncc_prerequisitos
            if conhecimento_previo and bncc_id:
                prereq_codes = extract_bncc_codes(conhecimento_previo)
                for pc in prereq_codes:
                    # tentar resolver o id do prereq se já estiver importado
                    cursor.execute("SELECT id FROM bncc_habilidades WHERE codigo = %s", (pc,))
                    found = cursor.fetchone()
                    prereq_bncc_id = found[0] if found else None
                    try:
                        cursor.execute(
                            "INSERT INTO bncc_prerequisitos (bncc_id, prereq_codigo, prereq_bncc_id) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE prereq_bncc_id=VALUES(prereq_bncc_id)",
                            (bncc_id, pc, prereq_bncc_id)
                        )
                    except Exception as e:
                        print(f"Erro inserindo prereq {pc} para {codigo}: {e}")
            
            # processar habilidades relacionadas (complementares/focais)
            if habilidades_relacionadas_texto and bncc_id:
                related_codes = extract_bncc_codes(habilidades_relacionadas_texto)
                for rc in related_codes:
                    cursor.execute("SELECT id FROM bncc_habilidades WHERE codigo = %s", (rc,))
                    found = cursor.fetchone()
                    related_bncc_id = found[0] if found else None
                    try:
                        # usar mesma tabela por ora; futuramente migrar para bncc_relacionamentos
                        cursor.execute(
                            "INSERT IGNORE INTO bncc_prerequisitos (bncc_id, prereq_codigo, prereq_bncc_id) VALUES (%s,%s,%s)",
                            (bncc_id, rc, related_bncc_id)
                        )
                    except Exception as e:
                        print(f"Erro inserindo related {rc} para {codigo}: {e}")

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
        df_obj = pd.read_excel(args.file, sheet_name=args.sheet)
    except Exception as e:
        print(f"Erro lendo Excel: {e}")
        sys.exit(1)

    # se foi lido múltiplas sheets, df_obj será um dict
    pwd = args.password or getpass.getpass(prompt=f"Senha para {args.user}@{args.host}: ")

    try:
        conn = mysql.connector.connect(host=args.host, port=args.port, user=args.user, password=pwd, database=args.database, charset='utf8mb4')
    except mysql.connector.Error as err:
        print(f"Erro conectando ao banco: {err}")
        sys.exit(1)

    if isinstance(df_obj, dict):
        for sheet_name, df in df_obj.items():
            print(f"Processing sheet: {sheet_name} -> {len(df)} rows")
            mapping = map_columns(list(df.columns))
            print("Mapeamento automático proposto:")
            for k,v in mapping.items():
                print(f"  {k}: {v}")
            if not mapping['codigo'] or not mapping['descricao']:
                print(f"Skipping sheet {sheet_name}: não detectou 'codigo' ou 'descricao'.")
                continue
            insert_rows(df, mapping, conn)
    else:
        df = df_obj
        print(f"Colunas detectadas: {list(df.columns)}")
        mapping = map_columns(list(df.columns))
        print("Mapeamento automático proposto:")
        for k,v in mapping.items():
            print(f"  {k}: {v}")
        if not mapping['codigo'] or not mapping['descricao']:
            print("Não foi possível detectar automaticamente as colunas 'codigo' ou 'descricao'. Revise as colunas do arquivo e renomeie-as ou informe mapping manualmente.")
            sys.exit(1)
        insert_rows(df, mapping, conn)
    conn.close()

    print("Importação finalizada.")
