import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error, pooling
from config_logs import get_logger

# Importar configurações centralizadas
try:
    from config.settings import settings
except ImportError:
    # Fallback se settings não estiver disponível
    settings = None

load_dotenv()  # Carrega as variáveis do arquivo .env

logger = get_logger(__name__)

# ============================================================================
# MELHORIA 4: Connection Pool para Múltiplos Usuários
# Implementa pool de conexões para melhor performance com múltiplos usuários
# ============================================================================

# Variável global para armazenar o pool de conexões
_connection_pool = None

def _validar_configuracao_db() -> tuple[bool, list[str]]:
    """
    Valida que todas as variáveis de ambiente necessárias estão configuradas.
    
    Returns:
        tuple[bool, list[str]]: (is_valid, error_messages)
    """
    errors = []
    
    # Usar settings se disponível, caso contrário ler de env
    if settings:
        db_config = settings.database
        if not db_config.host:
            errors.append("DB_HOST não configurado")
        if not db_config.user:
            errors.append("DB_USER não configurado")
        if not db_config.password:
            errors.append("DB_PASSWORD não configurado")
        if not db_config.name:
            errors.append("DB_NAME não configurado")
    else:
        if not os.getenv('DB_HOST'):
            errors.append("DB_HOST não configurado no .env")
        if not os.getenv('DB_USER'):
            errors.append("DB_USER não configurado no .env")
        if not os.getenv('DB_PASSWORD'):
            errors.append("DB_PASSWORD não configurado no .env")
        if not os.getenv('DB_NAME'):
            errors.append("DB_NAME não configurado no .env")
    
    return len(errors) == 0, errors


def _testar_conexao_db(host: str, user: str, password: str, database: str) -> tuple[bool, str]:
    """
    Testa se é possível conectar ao banco de dados.
    
    Returns:
        tuple[bool, str]: (success, message)
    """
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            auth_plugin='mysql_native_password',
            connection_timeout=5
        )
        if conn.is_connected():
            conn.close()
            return True, "Conexão testada com sucesso"
        return False, "Conexão não está ativa"
    except Error as e:
        return False, f"Erro ao testar conexão: {e}"


def inicializar_pool():
    """
    Inicializa o pool de conexões MySQL com validação robusta.
    Deve ser chamado uma vez no início da aplicação.
    
    Returns:
        MySQLConnectionPool: Pool de conexões inicializado
    
    Raises:
        ValueError: Se a configuração do banco estiver inválida
    """
    global _connection_pool
    
    if _connection_pool is None:
        # Validar configuração primeiro
        is_valid, errors = _validar_configuracao_db()
        if not is_valid:
            error_msg = "Configuração do banco de dados inválida:\n" + "\n".join(f"  - {err}" for err in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Obter configurações
            if settings:
                db_config = settings.database
                host = db_config.host
                user = db_config.user
                password = db_config.password
                database = db_config.name
                pool_size = db_config.pool_size
            else:
                host = os.getenv('DB_HOST')
                user = os.getenv('DB_USER')
                password = os.getenv('DB_PASSWORD')
                database = os.getenv('DB_NAME')
                pool_size = int(os.getenv('DB_POOL_SIZE', '5'))
            
            # Testar conexão antes de criar o pool
            success, message = _testar_conexao_db(host, user, password, database)
            if not success:
                logger.error(f"✗ Teste de conexão falhou: {message}")
                raise ValueError(f"Não foi possível conectar ao banco: {message}")
            
            logger.info(f"✓ {message}")
            
            # Criar pool
            pool_name = "gestao_escolar_pool"
            _connection_pool = pooling.MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=pool_size,
                pool_reset_session=True,
                host=host,
                user=user,
                password=password,
                database=database,
                auth_plugin='mysql_native_password'
            )
            
            logger.info(f"✓ Connection Pool inicializado: {pool_name} (size={pool_size})")
            
        except Error as e:
            logger.exception(f"✗ Erro ao criar connection pool: {e}")
            _connection_pool = None
            raise
    
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
                logger.warning("⚠ Conexão do pool não está ativa, tentando reconectar...")
                conn.reconnect(attempts=3, delay=1)
                return conn if conn.is_connected() else None
        else:
            # Fallback: criar conexão direta se pool falhou
            logger.warning("⚠ Pool não disponível, usando conexão direta (fallback)")
            return _conectar_direto()
            
    except Error as e:
        logger.exception(f"✗ Erro ao obter conexão do pool: {e}")
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
        # Obter configurações
        if settings:
            db_config = settings.database
            host = db_config.host
            user = db_config.user
            password = db_config.password
            database = db_config.name
        else:
            host = os.getenv('DB_HOST')
            user = os.getenv('DB_USER')
            password = os.getenv('DB_PASSWORD')
            database = os.getenv('DB_NAME')
        
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            auth_plugin='mysql_native_password'
        )
        if conn.is_connected():
            return conn
    except Error as e:
        logger.exception(f"✗ Erro ao conectar diretamente ao banco de dados: {e}")
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
            logger.debug("[OK] Connection Pool encerrado")
        except Exception as e:
            logger.exception(f"⚠ Erro ao fechar pool: {e}")


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
        logger.exception(f"⚠ Erro ao obter informações do pool: {e}")
        return None


