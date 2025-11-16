import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()  # Carrega as variáveis do arquivo .env
from config_logs import get_logger

logger = get_logger(__name__)

def conectar_bd():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            auth_plugin='mysql_native_password'
        )
        if conn.is_connected():
            return conn
    except Error as e:
        logger.exception("Erro ao conectar ao banco de dados: %s", e)
        return None

