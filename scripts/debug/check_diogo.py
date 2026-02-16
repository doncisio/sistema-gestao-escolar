from db.connection import conectar_bd

conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

cpf_diogo = '63573622399'

cursor.execute("SELECT id, nome, cpf, data_nascimento FROM Alunos WHERE cpf = %s", (cpf_diogo,))
resultado = cursor.fetchall()

print(f"Buscando CPF: {cpf_diogo}")
if resultado:
    print("ENCONTRADO:")
    for r in resultado:
        print(f"  ID: {r['id']}")
        print(f"  Nome: {r['nome']}")
        print(f"  Data Nasc: {r['data_nascimento']}")
else:
    print("NÃO ENCONTRADO - Diogo pode ser importado")
    
cursor.close()
conn.close()
