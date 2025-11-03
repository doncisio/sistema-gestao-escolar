import pandas as pd
from conexao import conectar_bd

def inserir_notas(arquivo_excel):
    # Conectar ao banco de dados
    conn = conectar_bd()
    cursor = conn.cursor()

    # Ler o arquivo Excel
    df = pd.read_excel(arquivo_excel)

    # Definir a ordem dos disciplina_ids
    ordem_disciplinas = [1, 2, 5, 3, 4, 6, 7, 8]

    # Iterar sobre cada linha do DataFrame
    for index, row in df.iterrows():
        nome_aluno = row['NOME DO ALUNO']
        
        # Buscar aluno_id pelo nome do aluno
        cursor.execute("SELECT id FROM alunos WHERE nome = %s", (nome_aluno,))
        resultado = cursor.fetchone()
        
        if resultado:
            aluno_id = resultado[0]
            # Inserir notas para cada disciplina na ordem especificada
            for disciplina_id in ordem_disciplinas:
                nota_coluna = f'disciplina_id ={disciplina_id}'
                nota = row.get(nota_coluna)  # Usando get para evitar KeyError
                
                if pd.notna(nota):  # Verifica se a nota não é NaN
                    cursor.execute("""
                        INSERT INTO notas (aluno_id, disciplina_id, bimestre, nota) 
                        VALUES (%s, %s, %s, %s)
                    """, (aluno_id, disciplina_id, '4º bimestre', nota))
        else:
            print(f"Aluno {nome_aluno} não encontrado.")

    # Commit das alterações e fechamento da conexão
    conn.commit()
    cursor.close()
    conn.close()

# Chamada da função com o caminho do arquivo Excel
inserir_notas('nota.xlsx')
