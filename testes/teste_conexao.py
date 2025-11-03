"""
Script para testar a conexão com o banco de dados
"""
import mysql.connector
import traceback
import os
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

def testar_conexao_dotenv():
    """Testa a conexão usando diretamente as variáveis do .env"""
    print("=== TESTE DE CONEXÃO USANDO DOTENV ===")
    
    try:
        # Obter configurações do .env
        config = {
            "host": os.getenv('DB_HOST', 'localhost'),
            "user": os.getenv('DB_USER', 'root'),
            "password": os.getenv('DB_PASSWORD', 'password'),
            "database": os.getenv('DB_NAME', 'gestao_escolar'),
            "auth_plugin": 'mysql_native_password'
        }
        
        print(f"Configurações: Host={config['host']}, DB={config['database']}, User={config['user']}")
        
        # Tentar conectar
        print("Tentando conectar...")
        conexao = mysql.connector.connect(**config)
        
        if conexao.is_connected():
            print("Conexão bem-sucedida!")
            cursor = conexao.cursor()
            cursor.execute("SELECT VERSION()")
            versao = cursor.fetchone()
            print(f"Versão do servidor: {versao[0]}")
            cursor.close()
            conexao.close()
            print("Conexão fechada.")
        else:
            print("Falha: conexao.is_connected() retornou False")
    except Exception as e:
        print(f"Erro ao conectar: {str(e)}")
        traceback.print_exc()
        
def testar_conexao_original():
    """Testa a conexão usando o método do arquivo conexao.py original"""
    print("\n=== TESTE DE CONEXÃO USANDO MÉTODO ORIGINAL ===")
    
    try:
        from conexao import conectar_bd
        
        print("Tentando conectar usando conexao.conectar_bd()...")
        conn = conectar_bd()
        
        if conn and conn.is_connected():
            print("Conexão bem-sucedida!")
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            versao = cursor.fetchone()
            print(f"Versão do servidor: {versao[0]}")
            cursor.close()
            conn.close()
            print("Conexão fechada.")
        else:
            print("Falha: conexão retornou None ou não está conectada")
    except Exception as e:
        print(f"Erro ao conectar: {str(e)}")
        traceback.print_exc()

def testar_conexao_mvc():
    """Testa a conexão usando o método do novo sistema MVC"""
    print("\n=== TESTE DE CONEXÃO USANDO MVC ===")
    
    try:
        from utils.db_utils import conectar_bd
        
        print("Tentando conectar usando utils.db_utils.conectar_bd()...")
        conn = conectar_bd()
        
        if conn and conn.is_connected():
            print("Conexão bem-sucedida!")
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            versao = cursor.fetchone()
            print(f"Versão do servidor: {versao[0]}")
            cursor.close()
            conn.close()
            print("Conexão fechada.")
        else:
            print("Falha: conexão retornou None ou não está conectada")
    except Exception as e:
        print(f"Erro ao conectar: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    testar_conexao_dotenv()
    testar_conexao_original()
    testar_conexao_mvc() 