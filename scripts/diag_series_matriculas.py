import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from conexao import conectar_bd

def main():
    conn = conectar_bd()
    if conn is None:
        print('ERRO: não foi possível conectar ao banco de dados')
        return
    cursor = conn.cursor()

    # Obter id do ano letivo 2025
    cursor.execute("SELECT id, ano_letivo FROM AnosLetivos WHERE ano_letivo = 2025 LIMIT 1")
    ano_row = cursor.fetchone()
    if ano_row:
        ano_id = ano_row[0]
        print(f'Ano letivo 2025 id = {ano_id}')
    else:
        cursor.execute("SELECT id, ano_letivo FROM AnosLetivos ORDER BY ano_letivo DESC LIMIT 1")
        ano_row = cursor.fetchone()
        if ano_row:
            ano_id = ano_row[0]
            print(f'Ano letivo padrão usado = {ano_row[1]} (id {ano_id})')
        else:
            print('Nenhum ano letivo encontrado')
            return

    print('\nLista de séries (id, nome) e contagem de matrículas no ano selecionado:')
    cursor.execute("SELECT id, nome FROM series ORDER BY nome")
    series = cursor.fetchall()
    for s in series:
        sid = s[0]
        sname = s[1]
        c = conn.cursor()
        try:
            c.execute("SELECT COUNT(*) FROM Matriculas m JOIN Turmas t ON m.turma_id = t.id WHERE m.ano_letivo_id = %s AND t.serie_id = %s", (ano_id, sid))
            cnt = c.fetchone()[0]
        except Exception as e:
            cnt = f'ERRO: {e}'
        finally:
            c.close()
        print(f"{sid}\t{sname}\t{cnt}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
