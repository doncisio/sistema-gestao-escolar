import pandas as pd
from conexao import conectar_bd

# Função para buscar ou adicionar aluno
def get_or_add_aluno(cursor, nome_aluno):
    cursor.execute("SELECT id FROM alunos WHERE nome = %s", (nome_aluno,))
    result = cursor.fetchone()
    
    if result:
        return result[0]  # Retorna o aluno_id existente
    else:
        cursor.execute("INSERT INTO alunos (nome) VALUES (%s)", (nome_aluno,))
        return cursor.lastrowid  # Retorna o novo aluno_id

# Função para buscar ou adicionar responsável
def get_or_add_responsavel(cursor, nome_responsavel, telefone):
    cursor.execute("SELECT id, telefone FROM responsaveis WHERE nome = %s", (nome_responsavel,))
    result = cursor.fetchone()
    
    if result:
        responsavel_id, telefone_existente = result
        # Atualiza o telefone se for diferente e não estiver vazio
        if telefone and telefone_existente != telefone:
            cursor.execute("UPDATE responsaveis SET telefone = %s WHERE id = %s", (telefone, responsavel_id))
            print(f"Telefone atualizado para o responsável: {nome_responsavel}")
        return responsavel_id  # Retorna o responsavel_id existente
    else:
        if telefone:  # Insere apenas se o telefone não estiver vazio
            cursor.execute("INSERT INTO responsaveis (nome, telefone) VALUES (%s, %s)", (nome_responsavel, telefone))
            print(f"Responsável adicionado: {nome_responsavel} com telefone {telefone}")
        else:
            cursor.execute("INSERT INTO responsaveis (nome) VALUES (%s)", (nome_responsavel,))
            print(f"Responsável adicionado: {nome_responsavel} sem telefone")
        return cursor.lastrowid  # Retorna o novo responsavel_id

# Função para adicionar relação aluno-responsável
def add_relacao(cursor, aluno_id, responsavel_id):
    cursor.execute("SELECT * FROM responsaveisalunos WHERE aluno_id = %s AND responsavel_id = %s", (aluno_id, responsavel_id))
    
    if cursor.fetchone():
        print("Já existe relação responsável-aluno")
    else:
        cursor.execute("INSERT INTO responsaveisalunos (aluno_id, responsavel_id) VALUES (%s, %s)", (aluno_id, responsavel_id))
        print("Inserida relação responsável-aluno")

# Lendo o arquivo Excel
file_path = 'Alunos_responsaveis.xlsx'
df = pd.read_excel(file_path)

# Conectando ao banco de dados usando a função já existente
conn = conectar_bd()
cursor = conn.cursor()

try:
    for index, row in df.iterrows():
        nome_aluno = row['ALUNO']
        nome_responsavel = row['RESPONSAVEL']
        telefone_responsavel = row['TELEFONE']  # Lê o telefone do responsável
        
        # Processa o aluno
        aluno_id = get_or_add_aluno(cursor, nome_aluno)
        
        # Processa o responsável com telefone
        responsavel_id = get_or_add_responsavel(cursor, nome_responsavel, telefone_responsavel)
        
        # Adiciona a relação entre aluno e responsável
        add_relacao(cursor, aluno_id, responsavel_id)
    
    # Salva as alterações no banco de dados
    conn.commit()
finally:
    # Fecha a conexão com o banco de dados
    cursor.close()
    conn.close()