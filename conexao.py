import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error, pooling

load_dotenv()  # Carrega as variáveis do arquivo .env

# ============================================================================
# MELHORIA 4: Connection Pool para Múltiplos Usuários
# Implementa pool de conexões para melhor performance com múltiplos usuários
# ============================================================================

# Variável global para armazenar o pool de conexões
_connection_pool = None

def inicializar_pool():
    """
    Inicializa o pool de conexões MySQL.
    Deve ser chamado uma vez no início da aplicação.
    
    Returns:
        MySQLConnectionPool: Pool de conexões inicializado
    """
    global _connection_pool
    
    if _connection_pool is None:
        try:
            # Configurações do pool
            pool_name = "gestao_escolar_pool"
            pool_size = int(os.getenv('DB_POOL_SIZE', '5'))  # Padrão: 5 conexões
            
            _connection_pool = pooling.MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=pool_size,
                pool_reset_session=True,  # Reseta sessão ao devolver conexão ao pool
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                auth_plugin='mysql_native_password'
            )
            
            print(f"✓ Connection Pool inicializado: {pool_name} (size={pool_size})")
            
        except Error as e:
            print(f"✗ Erro ao criar connection pool: {e}")
            _connection_pool = None
    
    return _connection_pool


def conectar_bd():
    """
    Obtém uma conexão do pool de conexões.
    Se o pool não estiver inicializado, inicializa automaticamente.
    
    Returns:
        MySQLConnection: Conexão do pool ou None em caso de erro
    """
    global _connection_pool
    
    try:
        # Inicializar pool se ainda não foi inicializado
        if _connection_pool is None:
            inicializar_pool()
        
        # Tentar obter conexão do pool
        if _connection_pool is not None:
            conn = _connection_pool.get_connection()
            
            # Verificar se a conexão está ativa
            if conn.is_connected():
                return conn
            else:
                print("⚠ Conexão do pool não está ativa, tentando reconectar...")
                conn.reconnect(attempts=3, delay=1)
                return conn if conn.is_connected() else None
        else:
            # Fallback: criar conexão direta se pool falhou
            print("⚠ Pool não disponível, usando conexão direta (fallback)")
            return _conectar_direto()
            
    except Error as e:
        print(f"✗ Erro ao obter conexão do pool: {e}")
        # Fallback: tentar conexão direta
        return _conectar_direto()


def _conectar_direto():
    """
    Cria uma conexão direta ao banco (fallback quando pool falha).
    Método privado, não deve ser usado diretamente.
    
    Returns:
        MySQLConnection: Conexão direta ou None em caso de erro
    """
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
        print(f"✗ Erro ao conectar diretamente ao banco de dados: {e}")
        return None


def fechar_pool():
    """
    Fecha todas as conexões do pool.
    Deve ser chamado ao encerrar a aplicação.
    """
    global _connection_pool
    
    if _connection_pool is not None:
        try:
            # MySQL Connector não tem método close() no pool
            # As conexões são fechadas automaticamente quando o pool é destruído
            _connection_pool = None
            print("✓ Connection Pool encerrado")
        except Exception as e:
            print(f"⚠ Erro ao fechar pool: {e}")


def obter_info_pool():
    """
    Retorna informações sobre o estado atual do pool.
    Útil para monitoramento e debug.
    
    Returns:
        dict: Dicionário com informações do pool ou None se pool não existir
    """
    global _connection_pool
    
    if _connection_pool is None:
        return None
    
    try:
        # Obter configurações do pool
        pool_config = _connection_pool._cnx_config
        
        return {
            'pool_name': _connection_pool.pool_name,
            'pool_size': _connection_pool._pool_size,
            'host': pool_config.get('host', 'N/A'),
            'database': pool_config.get('database', 'N/A'),
            'user': pool_config.get('user', 'N/A')
        }
    except Exception as e:
        print(f"⚠ Erro ao obter informações do pool: {e}")
        return None


