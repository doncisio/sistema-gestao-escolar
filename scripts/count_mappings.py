from src.core.conexao import conectar_bd

conn = conectar_bd()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM horarios_importados WHERE geduc_turma_id = %s AND turma_id = %s', (353, 28))
cnt = cur.fetchone()[0]
print('Registros horarios_importados com geduc_turma_id=353 e turma_id=28 ->', cnt)
cur.close()
conn.close()
