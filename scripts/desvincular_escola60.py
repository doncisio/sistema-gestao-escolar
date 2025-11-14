#!/usr/bin/env python3
"""Script para desvincular funcionários da `escola_id = 60` mantendo o registro.

Uso:
  - Dry-run (padrão): lista os funcionários afetados, nenhuma alteração feita
    python desvincular_escola60.py

  - Aplicar alterações:
    python desvincular_escola60.py --apply

O script usa a função `conectar_bd()` do projeto para obter a conexão.
"""
import argparse
import sys
from datetime import date

try:
    from conexao import conectar_bd
except Exception as e:
    print(f"Erro ao importar conectar_bd: {e}")
    sys.exit(1)


def tem_coluna(conn, tabela, coluna):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
              AND COLUMN_NAME = %s
            """,
            (tabela, coluna),
        )
        r = cur.fetchone()
        return bool(r and r[0] > 0)
    finally:
        cur.close()


def listar_funcionarios(conn):
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, nome, cargo, vinculo, escola_id FROM Funcionarios WHERE escola_id = 60")
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()


def aplicar_desvinculo(conn, ids):
    # Verificar colunas opcionais
    has_data_saida = tem_coluna(conn, 'Funcionarios', 'data_saida')
    has_ativo = tem_coluna(conn, 'Funcionarios', 'ativo')

    cur = conn.cursor()
    try:
        # Iniciar transação
        for fid in ids:
            parts = ["escola_id = NULL"]
            params = []
            if has_data_saida:
                parts.append("data_saida = COALESCE(data_saida, CURDATE())")
            if has_ativo:
                parts.append("ativo = 0")

            sql = "UPDATE Funcionarios SET " + ", ".join(parts) + " WHERE id = %s"
            params = [fid]
            cur.execute(sql, params)

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def main():
    parser = argparse.ArgumentParser(description='Desvincular funcionários da escola_id=60 (modo dry-run por padrão)')
    parser.add_argument('--apply', action='store_true', help='Aplicar as alterações (padrão: dry-run)')
    args = parser.parse_args()

    conn = conectar_bd()
    if not conn:
        print('Não foi possível conectar ao banco de dados. Verifique as credenciais em `conexao.py`.')
        sys.exit(1)

    try:
        rows = listar_funcionarios(conn)
        if not rows:
            print('Nenhum funcionário encontrado com escola_id = 60.')
            return

        print(f"Foram encontrados {len(rows)} funcionários com escola_id = 60:\n")
        for r in rows:
            print(f"ID: {r['id']:>5} | Nome: {r['nome'][:60]:60} | Cargo: {r.get('cargo')} | Vinculo: {r.get('vinculo')}")

        if not args.apply:
            print('\nMODO DRY-RUN: nenhuma alteração foi feita.')
            print('Rode com `--apply` para realmente alterar os registros (faça backup antes).')
            return

        confirma = input('\nDeseja realmente desvincular estes funcionários (escola_id => NULL)? (sim/nao): ').strip().lower()
        if confirma not in ('sim', 's', 'yes', 'y'):
            print('Operação cancelada pelo usuário.')
            return

        ids = [r['id'] for r in rows]
        aplicar_desvinculo(conn, ids)
        print(f'Operação concluída. {len(ids)} registros atualizados.')

    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()
