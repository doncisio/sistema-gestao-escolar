import pandas as pd
from conexao import conectar_bd

# Função para obter o aluno_id a partir do nome do aluno
def get_aluno_id(cursor, nome_aluno):
    cursor.execute("SELECT id FROM alunos WHERE nome = %s", (nome_aluno,))
    result = cursor.fetchone()
    return result[0] if result else None

# Função para verificar se já existe um registro de faltas para o aluno e bimestre
def check_faltas_exist(cursor, aluno_id, bimestre):
    cursor.execute("SELECT * FROM faltas_bimestrais WHERE aluno_id = %s AND bimestre = %s", (aluno_id, bimestre))
    return cursor.fetchone() is not None

# Função principal
def main():
    # Ler o arquivo Excel
    df = pd.read_excel('faltas.xlsx')

    # Conectar ao banco de dados
    conn = conectar_bd()
    cursor = conn.cursor()

    for index, row in df.iterrows():
        nome_aluno = row['nome do aluno']
        faltas = {
            '1º bimestre': row['1º bimestre'],
            '2º bimestre': row['2º bimestre'],
            '3º bimestre': row['3º bimestre'],
            '4º bimestre': row['4º bimestre']
        }

        # Buscar aluno_id
        aluno_id = get_aluno_id(cursor, nome_aluno)

        if aluno_id is not None:
            # Inserir ou atualizar faltas na tabela faltas_bimestrais
            for bimestre, falta in faltas.items():
                if check_faltas_exist(cursor, aluno_id, bimestre):
                    # Atualizar registro existente
                    cursor.execute(
                        "UPDATE faltas_bimestrais SET faltas = %s WHERE aluno_id = %s AND bimestre = %s",
                        (falta, aluno_id, bimestre)
                    )
                    print(f"Faltas atualizadas para: {nome_aluno} no {bimestre}")
                else:
                    # Inserir novo registro
                    cursor.execute(
                        "INSERT INTO faltas_bimestrais (aluno_id, bimestre, ano_letivo_id, faltas) VALUES (%s, %s, %s, %s)",
                        (aluno_id, bimestre, 1, falta)  # Supondo que o ano letivo é 1
                    )
                    print(f"Faltas inseridas para: {nome_aluno} no {bimestre}")
        else:
            print(f"Aluno não encontrado: {nome_aluno}")

    # Commit e fechar a conexão
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
