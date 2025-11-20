"""
Testes para o módulo services/funcionario_service.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services import funcionario_service as fs


class TestCriarFuncionario:
    """Testes para criar_funcionario"""
    
    @patch('services.funcionario_service.get_cursor')
    def test_criar_funcionario_sucesso(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = None  # CPF não existe
        mock_cursor_instance.lastrowid = 123
        
        sucesso, mensagem, func_id = fs.criar_funcionario(
            nome="Maria Santos",
            cpf="12345678900",
            cargo="Professor",
            data_admissao="2025-01-15"
        )
        
        assert sucesso is True
        assert func_id == 123
        assert "sucesso" in mensagem.lower()
    
    @patch('services.funcionario_service.get_cursor')
    def test_criar_funcionario_cpf_duplicado(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = {'id': 1}  # CPF já existe
        
        sucesso, mensagem, func_id = fs.criar_funcionario(
            nome="Maria Santos",
            cpf="12345678900",
            cargo="Professor",
            data_admissao="2025-01-15"
        )
        
        assert sucesso is False
        assert func_id is None
        assert "já cadastrado" in mensagem.lower()
    
    def test_criar_funcionario_campos_obrigatorios_faltando(self):
        sucesso, mensagem, func_id = fs.criar_funcionario(
            nome="",
            cpf="12345678900",
            cargo="Professor",
            data_admissao="2025-01-15"
        )
        
        assert sucesso is False
        assert func_id is None
        assert "obrigatórios" in mensagem.lower()


class TestAtualizarFuncionario:
    """Testes para atualizar_funcionario"""
    
    @patch('services.funcionario_service.get_cursor')
    def test_atualizar_funcionario_sucesso(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = {'id': 1}
        
        sucesso, mensagem = fs.atualizar_funcionario(
            1,
            nome="Maria Santos Silva",
            email="maria@escola.com"
        )
        
        assert sucesso is True
        assert "atualizado" in mensagem.lower()
    
    @patch('services.funcionario_service.get_cursor')
    def test_atualizar_funcionario_inexistente(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = None
        
        sucesso, mensagem = fs.atualizar_funcionario(999, nome="Teste")
        
        assert sucesso is False
        assert "não encontrado" in mensagem.lower()
    
    def test_atualizar_funcionario_sem_campos(self):
        sucesso, mensagem = fs.atualizar_funcionario(1)
        
        assert sucesso is False
        assert "nenhum campo" in mensagem.lower()


class TestExcluirFuncionario:
    """Testes para excluir_funcionario"""
    
    @patch('services.funcionario_service.get_cursor')
    def test_excluir_funcionario_sucesso(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.side_effect = [
            {'nome': 'João Silva'},  # funcionário existe
            {'total': 0}  # sem turmas vinculadas
        ]
        
        sucesso, mensagem = fs.excluir_funcionario(1)
        
        assert sucesso is True
        assert "excluído" in mensagem.lower()
    
    @patch('services.funcionario_service.get_cursor')
    def test_excluir_funcionario_com_vinculos(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.side_effect = [
            {'nome': 'João Silva'},
            {'total': 3}  # 3 turmas vinculadas
        ]
        
        sucesso, mensagem = fs.excluir_funcionario(1)
        
        assert sucesso is False
        assert "turma" in mensagem.lower()
    
    @patch('services.funcionario_service.get_cursor')
    def test_excluir_funcionario_inexistente(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = None
        
        sucesso, mensagem = fs.excluir_funcionario(999)
        
        assert sucesso is False
        assert "não encontrado" in mensagem.lower()


class TestListarFuncionarios:
    """Testes para listar_funcionarios"""
    
    @patch('services.funcionario_service.get_cursor')
    def test_listar_funcionarios_sucesso(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchall.return_value = [
            {'id': 1, 'nome': 'João Silva', 'cargo': 'Professor'},
            {'id': 2, 'nome': 'Maria Santos', 'cargo': 'Coordenador'}
        ]
        
        resultado = fs.listar_funcionarios()
        
        assert len(resultado) == 2
        assert resultado[0]['nome'] == 'João Silva'
    
    @patch('services.funcionario_service.get_cursor')
    def test_listar_funcionarios_com_filtro_cargo(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchall.return_value = [
            {'id': 1, 'nome': 'João Silva', 'cargo': 'Professor'}
        ]
        
        resultado = fs.listar_funcionarios(cargo='Professor')
        
        assert len(resultado) == 1
        assert resultado[0]['cargo'] == 'Professor'
    
    @patch('services.funcionario_service.get_cursor')
    def test_listar_funcionarios_vazio(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchall.return_value = []
        
        resultado = fs.listar_funcionarios()
        
        assert resultado == []


class TestBuscarFuncionario:
    """Testes para buscar_funcionario"""
    
    @patch('services.funcionario_service.get_cursor')
    def test_buscar_funcionario_sucesso(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchall.return_value = [
            {'id': 1, 'nome': 'João Silva', 'cpf': '12345678900'}
        ]
        
        resultado = fs.buscar_funcionario("João")
        
        assert len(resultado) == 1
        assert resultado[0]['nome'] == 'João Silva'
    
    def test_buscar_funcionario_termo_vazio(self):
        resultado = fs.buscar_funcionario("")
        
        assert resultado == []
    
    @patch('services.funcionario_service.get_cursor')
    def test_buscar_funcionario_por_cpf(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchall.return_value = [
            {'id': 1, 'nome': 'João Silva', 'cpf': '12345678900'}
        ]
        
        resultado = fs.buscar_funcionario("123456")
        
        assert len(resultado) == 1


class TestObterFuncionarioPorId:
    """Testes para obter_funcionario_por_id"""
    
    @patch('services.funcionario_service.get_cursor')
    def test_obter_funcionario_sucesso(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = {
            'id': 1, 'nome': 'João Silva', 'cargo': 'Professor'
        }
        
        resultado = fs.obter_funcionario_por_id(1)
        
        assert resultado is not None
        assert resultado['nome'] == 'João Silva'
    
    @patch('services.funcionario_service.get_cursor')
    def test_obter_funcionario_inexistente(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = None
        
        resultado = fs.obter_funcionario_por_id(999)
        
        assert resultado is None


class TestObterTurmasProfessor:
    """Testes para obter_turmas_professor"""
    
    @patch('services.funcionario_service.get_cursor')
    def test_obter_turmas_professor_sucesso(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchall.return_value = [
            {'id': 10, 'nome': 'Turma A', 'serie': '1º Ano'},
            {'id': 11, 'nome': 'Turma B', 'serie': '2º Ano'}
        ]
        
        resultado = fs.obter_turmas_professor(1)
        
        assert len(resultado) == 2
        assert resultado[0]['nome'] == 'Turma A'
    
    @patch('services.funcionario_service.get_cursor')
    def test_obter_turmas_professor_vazio(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchall.return_value = []
        
        resultado = fs.obter_turmas_professor(1)
        
        assert resultado == []
