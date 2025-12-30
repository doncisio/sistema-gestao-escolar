from src.core.conexao import conectar_bd

conn = conectar_bd()
cur = conn.cursor(dictionary=True)
cur.execute('SELECT id, nome, serie_id FROM turmas WHERE geduc_id = %s', (353,))
rows = cur.fetchall()
print('turmas with geduc_id=353 ->')
for r in rows:
    print('  id=', r['id'], 'nome=', r.get('nome'), 'serie_id=', r.get('serie_id'))
cur.close()
conn.close()
