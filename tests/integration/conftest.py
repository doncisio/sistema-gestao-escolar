"""
Configuração e fixtures compartilhadas para testes de integração.

Este módulo contém configurações globais, fixtures reutilizáveis e
utilitários para todos os testes de integração.
"""

import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.config_logs import get_logger
from db.connection import get_connection

logger = get_logger(__name__)


# =============================================================================
# CONFIGURAÇÃO DE TESTES
# =============================================================================

# Marcar testes lentos
def pytest_configure(config):
    """Configuração inicial do pytest."""
    config.addinivalue_line("markers", "slow: marca testes como lentos")
    config.addinivalue_line("markers", "integration: marca testes de integração")
    config.addinivalue_line("markers", "database: marca testes que usam banco de dados")


# Opção para pular testes de integração
def pytest_addoption(parser):
    """Adiciona opções customizadas ao pytest."""
    parser.addoption(
        "--skip-integration",
        action="store_true",
        default=False,
        help="Pula testes de integração"
    )
    parser.addoption(
        "--skip-slow",
        action="store_true",
        default=False,
        help="Pula testes marcados como lentos"
    )


def pytest_collection_modifyitems(config, items):
    """Modifica coleção de testes baseado em opções."""
    skip_integration = pytest.mark.skip(reason="--skip-integration option given")
    skip_slow = pytest.mark.skip(reason="--skip-slow option given")
    
    for item in items:
        if config.getoption("--skip-integration"):
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
        
        if config.getoption("--skip-slow"):
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


# =============================================================================
# FIXTURES GLOBAIS
# =============================================================================

@pytest.fixture(scope="session")
def db_session_connection():
    """
    Conexão com banco de dados para toda a sessão de testes.
    
    Yields:
        Connection: Conexão MySQL reutilizável
    """
    # `get_connection()` é um context manager (decorado com @contextmanager).
    # Entramos explicitamente no context manager para obter o proxy de
    # conexão e garantimos o __exit__ no teardown.
    ctx = get_connection()
    conn = ctx.__enter__()
    logger.info("Conexão de sessão criada")
    try:
        yield conn
    finally:
        try:
            ctx.__exit__(None, None, None)
        except Exception:
            logger.exception("Erro ao fechar conexão de sessão")


@pytest.fixture(scope="function")
def db_connection():
    """
    Conexão com banco de dados para cada teste.
    
    Yields:
        Connection: Conexão MySQL isolada
    """
    # Suportar tanto retorno direto de conexão quanto context manager.
    ctx = get_connection()
    conn = ctx.__enter__()
    try:
        yield conn
    finally:
        try:
            ctx.__exit__(None, None, None)
        except Exception:
            logger.exception("Erro ao fechar conexão de teste")


@pytest.fixture(scope="function")
def db_transaction(db_connection):
    """
    Transação de banco de dados com rollback automático.
    
    Útil para testes que modificam dados mas devem reverter mudanças.
    
    Yields:
        Connection: Conexão com transação ativa
    """
    # Iniciar transação
    db_connection.start_transaction()
    
    yield db_connection
    
    # Rollback ao final
    db_connection.rollback()
    logger.info("Transação revertida")


@pytest.fixture
def limpar_dados_teste(db_connection):
    """
    Limpa dados de teste do banco após execução.
    
    Remove registros com IDs >= 900000 (reservados para testes).
    """
    yield
    
    cursor = db_connection.cursor()
    try:
        # Ordem correta por foreign keys
        tabelas = [
            "historico_escolar",
            "notas",
            "faltas",
            "matriculas",
            "responsaveis",
            "alunos",
            "funcionarios"
        ]
        
        for tabela in tabelas:
            cursor.execute(f"DELETE FROM {tabela} WHERE id >= 900000")
        
        db_connection.commit()
        logger.info("Dados de teste removidos")
        
    except Exception as e:
        logger.error(f"Erro ao limpar dados de teste: {e}")
        db_connection.rollback()
    finally:
        cursor.close()


@pytest.fixture
def dados_teste_aluno() -> Dict[str, Any]:
    """
    Dados padrão para criar aluno de teste.
    
    Returns:
        Dict com dados válidos de aluno
    """
    return {
        'nome': 'Aluno de Teste Silva',
        'data_nascimento': '2010-05-15',
        'sexo': 'M',
        'cpf': '12345678901',
        'cartao_sus': '123456789012345',
        'nis': '12345678901',
        'endereco': 'Rua de Teste, 123',
        'bairro': 'Centro',
        'cidade': 'Cidade Teste',
        'estado': 'TS',
        'cep': '12345-678',
        'escola_id': 60,
        'status': 'Ativo',
        'local_nascimento': 'Cidade Teste',
        'telefone': '(99) 99999-9999'
    }


@pytest.fixture
def dados_teste_funcionario() -> Dict[str, Any]:
    """
    Dados padrão para criar funcionário de teste.
    
    Returns:
        Dict com dados válidos de funcionário
    """
    return {
        'nome': 'Funcionário de Teste Santos',
        'cargo': 'Professor@',
        'data_nascimento': '1985-03-20',
        'cpf': '98765432109',
        'telefone': '(99) 98888-8888',
        'polivalente': 'não',
        'escola_id': 60
    }


@pytest.fixture
def mock_app():
    """
    Mock da classe Application para testes de UI.
    
    Returns:
        Mock: Objeto Mock configurado como Application
    """
    import tkinter as tk
    
    app = Mock()
    app.janela = tk.Tk()
    app.colors = {
        'co0': '#F5F5F5', 'co1': '#003A70', 'co2': '#77B341',
        'co3': '#E2418E', 'co4': '#4A86E8', 'co5': '#F26A25',
        'co6': '#F7B731', 'co7': '#333333', 'co8': '#BF3036',
        'co9': '#6FA8DC'
    }
    app.table_manager = Mock()
    app.dashboard_manager = Mock()
    app.update_status = Mock()
    
    yield app
    
    # Cleanup
    if app.janela:
        app.janela.destroy()


# =============================================================================
# FIXTURES DE DADOS REAIS DO BANCO
# =============================================================================

@pytest.fixture
def aluno_real(db_connection) -> Dict[str, Any]:
    """
    Obtém um aluno real do banco para testes.
    
    Returns:
        Dict com dados de aluno real ou None se não houver
    """
    cursor = db_connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM Alunos
            WHERE escola_id = 60 AND status = 'Ativo'
            LIMIT 1
        """)
        return cursor.fetchone()
    finally:
        cursor.close()


@pytest.fixture
def turma_real(db_connection) -> Dict[str, Any]:
    """
    Obtém uma turma real do banco para testes.
    
    Returns:
        Dict com dados de turma real ou None se não houver
    """
    cursor = db_connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT t.*, s.nome as serie_nome
            FROM Turmas t
            JOIN Series s ON t.serie_id = s.id
            WHERE t.escola_id = 60
            LIMIT 1
        """)
        return cursor.fetchone()
    finally:
        cursor.close()


@pytest.fixture
def ano_letivo_atual(db_connection) -> Dict[str, Any]:
    """
    Obtém ano letivo atual do banco.
    
    Returns:
        Dict com dados do ano letivo atual
    """
    cursor = db_connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM anos_letivos
            WHERE ano = YEAR(CURDATE())
            LIMIT 1
        """)
        return cursor.fetchone()
    finally:
        cursor.close()


# =============================================================================
# UTILITÁRIOS DE TESTE
# =============================================================================

def criar_aluno_teste(conn, dados: Dict[str, Any]) -> int:
    """
    Cria aluno de teste no banco.
    
    Args:
        conn: Conexão com banco
        dados: Dados do aluno
        
    Returns:
        ID do aluno criado
    """
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO Alunos (
                nome, data_nascimento, sexo, cpf, cartao_sus, nis,
                endereco, bairro, cidade, estado, cep, escola_id,
                status, local_nascimento
            ) VALUES (
                %(nome)s, %(data_nascimento)s, %(sexo)s, %(cpf)s,
                %(cartao_sus)s, %(nis)s, %(endereco)s, %(bairro)s,
                %(cidade)s, %(estado)s, %(cep)s, %(escola_id)s,
                %(status)s, %(local_nascimento)s
            )
        """
        cursor.execute(query, dados)
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()


def criar_funcionario_teste(conn, dados: Dict[str, Any]) -> int:
    """
    Cria funcionário de teste no banco.
    
    Args:
        conn: Conexão com banco
        dados: Dados do funcionário
        
    Returns:
        ID do funcionário criado
    """
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO Funcionarios (
                nome, cargo, data_nascimento, cpf, telefone,
                polivalente, escola_id
            ) VALUES (
                %(nome)s, %(cargo)s, %(data_nascimento)s, %(cpf)s,
                %(telefone)s, %(polivalente)s, %(escola_id)s
            )
        """
        cursor.execute(query, dados)
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()


# =============================================================================
# VERIFICAÇÕES DE AMBIENTE
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
def verificar_ambiente():
    """
    Verifica que o ambiente está configurado para testes.
    
    Checa:
    - Conexão com banco de dados
    - Variáveis de ambiente
    - Dependências instaladas
    """
    logger.info("Verificando ambiente de testes...")
    
    # Verificar conexão com banco
    try:
        # Entrar no context manager temporariamente para checar a conexão.
        ctx = get_connection()
        conn = ctx.__enter__()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        finally:
            # Garantir fechamento/retorno ao pool
            try:
                ctx.__exit__(None, None, None)
            except Exception:
                logger.exception("Erro ao liberar conexão durante verificação de ambiente")

        logger.info("✓ Conexão com banco de dados OK")
    except Exception as e:
        logger.error(f"✗ Erro ao conectar com banco: {e}")
        pytest.exit("Banco de dados não disponível para testes")
    
    # Verificar variáveis de ambiente
    required_vars = ['DB_HOST', 'DB_USER', 'DB_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Variáveis de ambiente faltando: {missing_vars}")
    else:
        logger.info("✓ Variáveis de ambiente OK")
    
    logger.info("Ambiente de testes configurado")
    yield
    logger.info("Finalizando ambiente de testes")


# =============================================================================
# MARCADORES CUSTOMIZADOS
# =============================================================================

# Aliases de markers para uso direto nos testes (evita atribuição a `pytest.mark`).
integration = pytest.mark.integration
database = pytest.mark.database
slow = pytest.mark.slow
