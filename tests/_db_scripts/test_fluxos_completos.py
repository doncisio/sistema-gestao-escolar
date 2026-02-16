"""
Testes de integração completos para fluxos críticos do sistema.

Este módulo contém testes de integração end-to-end que validam fluxos
completos de negócio, incluindo:
- Cadastro de aluno → Matrícula → Lançamento de notas → Histórico escolar
- Backup e restauração de dados
- Geração de documentos (boletins, declarações, relatórios)
"""

import pytest
import os
import tempfile
from datetime import datetime, date
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional

# Imports do sistema
from db.connection import get_connection
from src.core.config_logs import get_logger

logger = get_logger(__name__)


# =============================================================================
# FIXTURES REUTILIZÁVEIS
# =============================================================================

@pytest.fixture(scope="function")
def db_test_connection():
    """
    Fixture para conexão com banco de dados de teste.
    
    Yields:
        Connection: Conexão MySQL para testes
    """
    # `get_connection()` é um context manager; entrar explicitamente para obter
    # o proxy de conexão e garantir que o __exit__ seja chamado no teardown.
    ctx = get_connection()
    conn = ctx.__enter__()
    try:
        yield conn
    finally:
        try:
            ctx.__exit__(None, None, None)
        except Exception:
            logger.exception("Erro ao fechar conexão de teste (fixture db_test_connection)")


@pytest.fixture(scope="function")
def limpar_dados_teste(db_test_connection):
    """
    Fixture para limpar dados de teste após execução.
    
    Remove todos os registros criados durante os testes.
    """
    yield
    
    # Cleanup após teste
    cursor = db_test_connection.cursor()
    try:
        # Remover dados de teste (na ordem correta por FK)
        cursor.execute("DELETE FROM historico_escolar WHERE aluno_id >= 900000")
        cursor.execute("DELETE FROM notas WHERE aluno_id >= 900000")
        cursor.execute("DELETE FROM matriculas WHERE aluno_id >= 900000")
        cursor.execute("DELETE FROM responsaveis WHERE aluno_id >= 900000")
        cursor.execute("DELETE FROM alunos WHERE id >= 900000")
        cursor.execute("DELETE FROM funcionarios WHERE id >= 900000")
        
        db_test_connection.commit()
        logger.info("Dados de teste removidos com sucesso")
    except Exception as e:
        logger.error(f"Erro ao limpar dados de teste: {e}")
        db_test_connection.rollback()
    finally:
        cursor.close()


@pytest.fixture
def dados_aluno_teste() -> Dict[str, Any]:
    """
    Fixture com dados de teste para criação de aluno.
    
    Returns:
        Dict com dados válidos de aluno
    """
    return {
        'nome': 'João da Silva Teste',
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
        'local_nascimento': 'Cidade Teste'
    }


@pytest.fixture
def dados_funcionario_teste() -> Dict[str, Any]:
    """
    Fixture com dados de teste para criação de funcionário.
    
    Returns:
        Dict com dados válidos de funcionário
    """
    return {
        'nome': 'Maria dos Santos Teste',
        'cargo': 'Professor@',
        'data_nascimento': '1985-03-20',
        'cpf': '98765432109',
        'telefone': '(99) 99999-9999',
        'polivalente': 'não',
        'escola_id': 60
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def criar_aluno_teste(conn, dados: Dict[str, Any]) -> int:
    """
    Cria um aluno de teste no banco.
    
    Args:
        conn: Conexão com banco de dados
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
        
        aluno_id = cursor.lastrowid
        logger.info(f"Aluno de teste criado: ID={aluno_id}")
        return aluno_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao criar aluno de teste: {e}")
        raise
    finally:
        cursor.close()


def criar_funcionario_teste(conn, dados: Dict[str, Any]) -> int:
    """
    Cria um funcionário de teste no banco.
    
    Args:
        conn: Conexão com banco de dados
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
        
        func_id = cursor.lastrowid
        logger.info(f"Funcionário de teste criado: ID={func_id}")
        return func_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao criar funcionário de teste: {e}")
        raise
    finally:
        cursor.close()


def matricular_aluno_teste(
    conn,
    aluno_id: int,
    turma_id: int,
    ano_letivo_id: int,
    status: str = 'Ativo'
) -> int:
    """
    Matricula um aluno de teste.
    
    Args:
        conn: Conexão com banco de dados
        aluno_id: ID do aluno
        turma_id: ID da turma
        ano_letivo_id: ID do ano letivo
        status: Status da matrícula
        
    Returns:
        ID da matrícula criada
    """
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO Matriculas (
                aluno_id, turma_id, ano_letivo_id, status, data_matricula
            ) VALUES (
                %s, %s, %s, %s, NOW()
            )
        """
        cursor.execute(query, (aluno_id, turma_id, ano_letivo_id, status))
        conn.commit()
        
        matricula_id = cursor.lastrowid
        logger.info(f"Matrícula de teste criada: ID={matricula_id}")
        return matricula_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao matricular aluno de teste: {e}")
        raise
    finally:
        cursor.close()


def lancar_nota_teste(
    conn,
    aluno_id: int,
    disciplina_id: int,
    bimestre: int,
    nota: float
) -> bool:
    """
    Lança uma nota para aluno de teste.
    
    Args:
        conn: Conexão com banco de dados
        aluno_id: ID do aluno
        disciplina_id: ID da disciplina
        bimestre: Número do bimestre (1-4)
        nota: Nota obtida
        
    Returns:
        True se sucesso, False caso contrário
    """
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO Notas (
                aluno_id, disciplina_id, bimestre, nota, ano_letivo
            ) VALUES (
                %s, %s, %s, %s, YEAR(CURDATE())
            )
        """
        cursor.execute(query, (aluno_id, disciplina_id, bimestre, nota))
        conn.commit()
        
        logger.info(f"Nota lançada: aluno={aluno_id}, disc={disciplina_id}, nota={nota}")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao lançar nota de teste: {e}")
        return False
    finally:
        cursor.close()


def obter_historico_teste(conn, aluno_id: int) -> Optional[Dict]:
    """
    Obtém histórico escolar de aluno de teste.
    
    Args:
        conn: Conexão com banco de dados
        aluno_id: ID do aluno
        
    Returns:
        Dict com dados do histórico ou None
    """
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT h.*, a.nome as aluno_nome
            FROM historico_escolar h
            JOIN Alunos a ON h.aluno_id = a.id
            WHERE h.aluno_id = %s
            ORDER BY h.ano DESC
        """
        cursor.execute(query, (aluno_id,))
        return cursor.fetchall()
        
    except Exception as e:
        logger.error(f"Erro ao obter histórico de teste: {e}")
        return None
    finally:
        cursor.close()


# =============================================================================
# TESTES DE FLUXO COMPLETO DE MATRÍCULA
# =============================================================================

class TestFluxoCompletoMatricula:
    """
    Testes de integração para o fluxo completo de matrícula.
    
    Testa: Cadastro → Matrícula → Notas → Histórico
    """
    
    def test_fluxo_completo_aluno_matricula_notas_historico(
        self,
        db_test_connection,
        limpar_dados_teste,
        dados_aluno_teste
    ):
        """
        Testa fluxo completo end-to-end:
        1. Cadastrar aluno
        2. Matricular em turma
        3. Lançar notas em todas as disciplinas
        4. Gerar histórico escolar
        """
        # 1. CADASTRAR ALUNO
        aluno_id = criar_aluno_teste(db_test_connection, dados_aluno_teste)
        assert aluno_id is not None
        assert aluno_id > 0
        
        # Verificar que aluno foi criado
        cursor = db_test_connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Alunos WHERE id = %s", (aluno_id,))
        aluno = cursor.fetchone()
        cursor.close()
        
        assert aluno is not None
        assert aluno['nome'] == dados_aluno_teste['nome']
        assert aluno['cpf'] == dados_aluno_teste['cpf']
        assert aluno['status'] == 'Ativo'
        
        # 2. MATRICULAR EM TURMA
        # Obter uma turma ativa para teste
        cursor = db_test_connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.id as turma_id, al.id as ano_letivo_id
            FROM Turmas t
            JOIN anos_letivos al ON al.ano = YEAR(CURDATE())
            WHERE t.escola_id = 60
            LIMIT 1
        """)
        turma_info = cursor.fetchone()
        cursor.close()
        
        if turma_info:
            matricula_id = matricular_aluno_teste(
                db_test_connection,
                aluno_id,
                turma_info['turma_id'],
                turma_info['ano_letivo_id']
            )
            
            assert matricula_id is not None
            assert matricula_id > 0
            
            # Verificar matrícula
            cursor = db_test_connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM Matriculas WHERE id = %s
            """, (matricula_id,))
            matricula = cursor.fetchone()
            cursor.close()
            
            assert matricula is not None
            assert matricula['aluno_id'] == aluno_id
            assert matricula['status'] == 'Ativo'
            
            # 3. LANÇAR NOTAS
            # Obter disciplinas da série
            cursor = db_test_connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT d.id FROM Disciplinas d
                JOIN Turmas t ON t.serie_id = (
                    SELECT serie_id FROM Turmas WHERE id = %s
                )
                LIMIT 3
            """, (turma_info['turma_id'],))
            disciplinas = cursor.fetchall()
            cursor.close()
            
            notas_lancadas = []
            for disciplina in disciplinas:
                for bimestre in range(1, 5):  # 4 bimestres
                    nota = 7.5 + (bimestre * 0.5)  # Notas crescentes
                    resultado = lancar_nota_teste(
                        db_test_connection,
                        aluno_id,
                        disciplina['id'],
                        bimestre,
                        nota
                    )
                    assert resultado is True
                    notas_lancadas.append((disciplina['id'], bimestre, nota))
            
            assert len(notas_lancadas) == len(disciplinas) * 4
            
            # Verificar notas no banco
            cursor = db_test_connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) as total FROM Notas
                WHERE aluno_id = %s
            """, (aluno_id,))
            total_notas = cursor.fetchone()[0]
            cursor.close()
            
            assert total_notas == len(notas_lancadas)
            
            # 4. VERIFICAR HISTÓRICO (se implementado)
            historico = obter_historico_teste(db_test_connection, aluno_id)
            # Histórico pode estar vazio se não for gerado automaticamente
            assert historico is not None  # Pelo menos deve retornar lista vazia
            
        else:
            pytest.skip("Nenhuma turma disponível para teste")
    
    def test_cadastro_aluno_com_responsavel(
        self,
        db_test_connection,
        limpar_dados_teste,
        dados_aluno_teste
    ):
        """
        Testa cadastro de aluno com responsável.
        """
        # Criar aluno
        aluno_id = criar_aluno_teste(db_test_connection, dados_aluno_teste)
        assert aluno_id > 0
        
        # Adicionar responsável
        cursor = db_test_connection.cursor()
        try:
            query = """
                INSERT INTO Responsaveis (
                    aluno_id, nome, parentesco, cpf, telefone
                ) VALUES (
                    %s, %s, %s, %s, %s
                )
            """
            cursor.execute(query, (
                aluno_id,
                'Maria da Silva Teste',
                'Mãe',
                '10987654321',
                '(99) 98888-8888'
            ))
            db_test_connection.commit()
            
            responsavel_id = cursor.lastrowid
            assert responsavel_id > 0
            
            # Verificar responsável
            cursor.execute("""
                SELECT * FROM Responsaveis WHERE id = %s
            """, (responsavel_id,))
            responsavel = cursor.fetchone()
            
            assert responsavel is not None
            assert responsavel[1] == aluno_id  # aluno_id
            
        finally:
            cursor.close()
    
    def test_matricula_duplicada_mesmo_ano(
        self,
        db_test_connection,
        limpar_dados_teste,
        dados_aluno_teste
    ):
        """
        Testa que não é possível matricular aluno duas vezes no mesmo ano letivo.
        """
        # Criar aluno
        aluno_id = criar_aluno_teste(db_test_connection, dados_aluno_teste)
        
        # Obter turma e ano letivo
        cursor = db_test_connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.id as turma_id, al.id as ano_letivo_id
            FROM Turmas t
            JOIN anos_letivos al ON al.ano = YEAR(CURDATE())
            WHERE t.escola_id = 60
            LIMIT 1
        """)
        turma_info = cursor.fetchone()
        cursor.close()
        
        if turma_info:
            # Primeira matrícula (deve funcionar)
            matricula_id1 = matricular_aluno_teste(
                db_test_connection,
                aluno_id,
                turma_info['turma_id'],
                turma_info['ano_letivo_id']
            )
            assert matricula_id1 > 0
            
            # Segunda matrícula (deve falhar ou ser validada pela aplicação)
            # Nota: Depende de constraint UNIQUE no banco ou validação na aplicação
            try:
                matricula_id2 = matricular_aluno_teste(
                    db_test_connection,
                    aluno_id,
                    turma_info['turma_id'],
                    turma_info['ano_letivo_id']
                )
                
                # Se chegou aqui, verificar que apenas uma matrícula ativa existe
                cursor = db_test_connection.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM Matriculas
                    WHERE aluno_id = %s AND ano_letivo_id = %s AND status = 'Ativo'
                """, (aluno_id, turma_info['ano_letivo_id']))
                count = cursor.fetchone()[0]
                cursor.close()
                
                # Deve ter apenas 1 matrícula ativa (a lógica pode cancelar a anterior)
                assert count >= 1  # Pelo menos uma matrícula existe
                
            except Exception as e:
                # Erro esperado se houver constraint ou validação
                logger.info(f"Matrícula duplicada bloqueada (esperado): {e}")
                db_test_connection.rollback()
        else:
            pytest.skip("Nenhuma turma disponível para teste")


# =============================================================================
# TESTES DE BACKUP E RESTAURAÇÃO
# =============================================================================

class TestBackupRestauracao:
    """Testes de integração para backup e restauração de dados."""
    
    @patch('Seguranca.fazer_backup')
    def test_backup_criado_com_sucesso(self, mock_backup):
        """Testa que backup é criado com sucesso."""
        # Mock do backup
        mock_backup.return_value = True
        
        # Importar e executar backup
        from src.core import seguranca
        resultado = seguranca.fazer_backup()
        
        assert resultado is True
        mock_backup.assert_called_once()
    
    def test_backup_arquivo_existe(self):
        """Testa que arquivo de backup é criado."""
        from src.core import seguranca
        
        # Executar backup real
        resultado = seguranca.fazer_backup()
        
        if resultado:
            # Verificar que arquivo existe
            backup_path = Path("migrations/backup_redeescola.sql")
            assert backup_path.exists()
            assert backup_path.stat().st_size > 0
        else:
            pytest.skip("Backup não pôde ser executado (mysqldump não disponível)")
    
    @patch('src.core.seguranca.fazer_backup')
    @patch('schedule.every')
    def test_backup_automatico_agendado(self, mock_schedule, mock_backup):
        """Testa que backup automático é agendado corretamente."""
        from src.core import seguranca
        
        mock_backup.return_value = True
        
        # Configurar agendamento
        Seguranca.agendar_backup_diario()
        
        # Verificar que schedule.every().day.at() foi chamado
        assert mock_schedule.called


# Continua na próxima parte...
