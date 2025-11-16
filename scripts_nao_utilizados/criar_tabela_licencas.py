from config_logs import get_logger
logger = get_logger(__name__)
import mysql.connector
from conexao import conectar_bd

def criar_tabela_licencas():
    try:
        # Conectar ao banco de dados
        conn = conectar_bd()
        if not conn:
            logger.info("Não foi possível conectar ao banco de dados")
            return False
        
        cursor = conn.cursor()
        
        # Ler o arquivo SQL com codificação UTF-8
        with open('criar_tabela_licencas.sql', 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # Executar o script SQL
        for statement in sql_script.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        # Confirmar as alterações
        conn.commit()
        logger.info("Tabela 'licencas' criada com sucesso!")
        return True
        
    except mysql.connector.Error as err:
        logger.error(f"Erro ao criar tabela: {err}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    criar_tabela_licencas() 