import pandas as pd
from conexao import conectar_bd

def atualizar_ou_inserir_funcionario(nome_arquivo_excel):
    """
    Atualiza os dados de funcionários existentes ou insere novos registros
    a partir de um arquivo Excel.
    """
    try:
        # Ler o arquivo Excel usando pandas, tratando células vazias como NaN
        df = pd.read_excel(nome_arquivo_excel, na_values=['', '#N/A', '#NA', 'N/A', 'NA', 'NaN', 'nan', None])

        # Estabelecer conexão com o banco de dados
        conn = conectar_bd()
        cursor = conn.cursor()

        for index, row in df.iterrows():
            nome = row['nome']
            carga_horaria = row['carga_horaria'] if pd.notna(row['carga_horaria']) else None
            cpf = row['cpf'] if pd.notna(row['cpf']) else None
            telefone = row['telefone'] if pd.notna(row['telefone']) else None

            # Verificar se o funcionário já existe pelo nome
            query = "SELECT id FROM funcionarios WHERE nome = %s"
            cursor.execute(query, (nome,))
            result = cursor.fetchone()

            if result:
                funcionario_id = result[0]
                # Atualizar o registro existente (permitindo NULLs)
                update_query = """
                    UPDATE funcionarios
                    SET carga_horaria = %s,
                        cpf = %s,
                        telefone = %s
                    WHERE id = %s
                """
                values = (carga_horaria, cpf, telefone, funcionario_id)
                cursor.execute(update_query, values)
                print(f"Funcionário {nome} atualizado.")
            else:
                # Inserir um novo registro (permitindo NULLs)
                insert_query = """
                    INSERT INTO funcionarios (nome, carga_horaria, cpf, telefone)
                    VALUES (%s, %s, %s, %s)
                """
                values = (nome, carga_horaria, cpf, telefone)
                cursor.execute(insert_query, values)
                print(f"Funcionário {nome} inserido.")

        # Commitar as mudanças e fechar a conexão
        conn.commit()
        cursor.close()
        conn.close()
        print("Processo concluído com sucesso!")

    except FileNotFoundError:
        print(f"Arquivo {nome_arquivo_excel} não encontrado.")
    except KeyError as err:
        print(f"Coluna '{err}' não encontrada no arquivo Excel.")
    except Exception as err:
        print(f"Ocorreu um erro inesperado: {err}")

# Exemplo de uso
nome_arquivo = 'Funcionario.xlsx'  # Substitua pelo nome do seu arquivo Excel
atualizar_ou_inserir_funcionario(nome_arquivo)
