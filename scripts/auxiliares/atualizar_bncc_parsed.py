#!/usr/bin/env python3
"""
Atualiza a tabela `bncc_habilidades` populando `codigo_raw` e colunas parsed
usando a função `parse_bncc_code` do arquivo `bncc_parser.py`.

Uso:
  python atualizar_bncc_parsed.py --user doncisio --database redeescola --host localhost

O script pedirá interativamente a senha e fará commit ao final.
"""
import argparse
import getpass
import sys
import mysql.connector
from mysql.connector import errorcode
from bncc_parser import parse_bncc_code


def atualizar(host, port, user, password, database, batch_size=200):
    try:
        conn = mysql.connector.connect(host=host, port=port, user=user, password=password, database=database, charset='utf8mb4')
    except mysql.connector.Error as err:
        print(f"Erro ao conectar: {err}")
        return 1

    cursor = conn.cursor(dictionary=True)
    cursor_update = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS cnt FROM bncc_habilidades")
    total = cursor.fetchone()['cnt']
    print(f"Total de registros em bncc_habilidades: {total}")

    cursor.execute("SELECT id, codigo FROM bncc_habilidades")

    update_sql = '''
    UPDATE bncc_habilidades
    SET codigo_raw=%s,
        etapa_sigla=%s,
        grupo_faixa=%s,
        campo_experiencias=%s,
        ano_bloco=%s,
        componente_codigo=%s,
        em_competencia=%s,
        em_sequencia=%s,
        updated_at=CURRENT_TIMESTAMP
    WHERE id=%s
    '''

    count = 0
    failed = 0
    for row in cursor:
        id_ = row['id']
        codigo = row.get('codigo') or ''
        parsed = parse_bncc_code(codigo)
        values = (
            parsed.get('codigo_raw'),
            parsed.get('etapa_sigla'),
            parsed.get('grupo_faixa'),
            parsed.get('campo_experiencias'),
            parsed.get('ano_bloco'),
            parsed.get('componente_codigo'),
            parsed.get('em_competencia'),
            parsed.get('em_sequencia'),
            id_
        )
        try:
            cursor_update.execute(update_sql, values)
            count += 1
            if count % batch_size == 0:
                conn.commit()
                print(f"Committed {count}/{total}")
        except Exception as e:
            print(f"Erro atualizando id={id_}, codigo={codigo}: {e}")
            failed += 1

    conn.commit()
    cursor.close()
    cursor_update.close()
    conn.close()

    print(f"Atualização concluída. Registros processados: {count}, falhas: {failed}")
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Atualiza campos parsed em bncc_habilidades')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', default=3306, type=int)
    parser.add_argument('--user', required=True)
    parser.add_argument('--database', required=True)
    parser.add_argument('--password', help='Senha MySQL (opcional)')
    args = parser.parse_args()

    pwd = args.password or getpass.getpass(prompt=f"Senha para {args.user}@{args.host}: ")

    rc = atualizar(args.host, args.port, args.user, pwd, args.database)
    sys.exit(rc)
