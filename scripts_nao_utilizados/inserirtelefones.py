import pandas as pd
from conexao import conectar_bd  # Importa a função conectar_bd
import mysql.connector
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO)

def atualizar_telefone(cursor, nome_responsavel, telefone_responsavel):
    query = """
    UPDATE responsaveis
    SET telefone = %s
    WHERE nome = %s
    """
    cursor.execute(query, (telefone_responsavel, nome_responsavel))
    logging.info(f"Telefone do responsável '{nome_responsavel}' atualizado para '{telefone_responsavel}'")

def processar_excel(excel_file):
    return pd.ExcelFile(excel_file)

def main():
    conn = conectar_bd()
    if conn is None:
        logging.error("Não foi possível conectar ao banco de dados.")
        return

    try:
        cursor = conn.cursor()
        df = processar_excel('relatorio_alunos.xlsx')

        # Dicionário para armazenar o primeiro telefone válido encontrado para cada responsável
        responsaveis_telefones = {}

        for planilha_nome in df.sheet_names:
            sheet_df = df.parse(planilha_nome, dtype={'Telefone do Responsável': str})

            # Substituir NaN por None no DataFrame
            sheet_df = sheet_df.where(pd.notnull(sheet_df), None)

            for index, row in sheet_df.iterrows():
                nome_responsavel = row['Nome do Responsável']
                telefone_responsavel = row['Telefone do Responsável']
                
                # Verifica se o telefone é válido e se ainda não foi registrado
                if nome_responsavel and telefone_responsavel and nome_responsavel not in responsaveis_telefones:
                    responsaveis_telefones[nome_responsavel] = telefone_responsavel

        # Atualiza todos os responsáveis com seus respectivos telefones válidos
        for nome_responsavel, telefone_responsavel in responsaveis_telefones.items():
            atualizar_telefone(cursor, nome_responsavel, telefone_responsavel)

        conn.commit()
        logging.info("Telefones dos responsáveis atualizados com sucesso!")

    except mysql.connector.Error as erro:
        logging.error(f"Falha ao conectar ao MySQL: {erro}")
    
    except Exception as e:
        logging.error(f"Ocorreu um erro: {e}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            logging.info("Conexão MySQL foi fechada")

if __name__ == "__main__":
    main()
