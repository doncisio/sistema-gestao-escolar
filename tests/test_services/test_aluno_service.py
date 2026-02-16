"""
Testes unitários para services.aluno_service

Este módulo testa as funções de lógica de negócio relacionadas a alunos,
usando mocks para simular interações com o banco de dados.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import cast
from src.services.aluno_service import (
    verificar_matricula_ativa,
    verificar_historico_matriculas,
    excluir_aluno_com_confirmacao,
    obter_aluno_por_id
)


@pytest.fixture
def mock_cursor():
    """Fixture que retorna um cursor mock configurado."""
    cursor = MagicMock()
    cursor.fetchone = Mock()
    cursor.fetchall = Mock()
    cursor.execute = Mock()
    return cursor


@pytest.fixture
def mock_get_cursor(mock_cursor):
    """Fixture que mocka o context manager get_cursor."""
    with patch('src.services.aluno_service.get_cursor') as mock:
        mock.return_value.__enter__.return_value = mock_cursor
        mock.return_value.__exit__.return_value = None
        yield mock


class TestVerificarMatriculaAtiva:
    """Testes para a função verificar_matricula_ativa."""
    
    def test_aluno_com_matricula_ativa(self, mock_get_cursor, mock_cursor):
        """Testa caso onde aluno possui matrícula ativa."""
        # Configurar mocks
        mock_cursor.fetchone.side_effect = [
            {'id': 1},  # ano letivo
            {'id': 123}  # matrícula encontrada
        ]
        
        resultado = verificar_matricula_ativa(1)
        
        assert resultado is True
        assert mock_cursor.execute.call_count == 2
    
    def test_aluno_sem_matricula_ativa(self, mock_get_cursor, mock_cursor):
        """Testa caso onde aluno não possui matrícula ativa."""
        # Configurar mocks
        mock_cursor.fetchone.side_effect = [
            {'id': 1},  # ano letivo
            None  # nenhuma matrícula encontrada
        ]
        
        resultado = verificar_matricula_ativa(1)
        
        assert resultado is False
        assert mock_cursor.execute.call_count == 2
    
    def test_ano_letivo_nao_encontrado(self, mock_get_cursor, mock_cursor):
        """Testa caso onde não há ano letivo configurado."""
        # Configurar mocks - nenhum ano letivo encontrado
        mock_cursor.fetchone.side_effect = [None, None]
        
        with patch('src.services.aluno_service.messagebox.showwarning'):
            resultado = verificar_matricula_ativa(1)
        
        assert resultado is False
    
    def test_id_invalido(self):
        """Testa comportamento com ID inválido."""
        with patch('src.services.aluno_service.messagebox.showerror'):
            resultado = verificar_matricula_ativa(cast(int, "inválido"))
        
        assert resultado is False


class TestVerificarHistoricoMatriculas:
    """Testes para a função verificar_historico_matriculas."""
    
    def test_aluno_com_historico(self, mock_get_cursor, mock_cursor):
        """Testa caso onde aluno possui histórico de matrículas."""
        # Configurar mock
        mock_cursor.fetchall.return_value = [
            {'ano_letivo': 2025, 'id': 2, 'status': 'Ativo'},
            {'ano_letivo': 2024, 'id': 1, 'status': 'Transferido'}
        ]
        
        tem_historico, anos = verificar_historico_matriculas(1)
        
        assert tem_historico is True
        assert len(anos) == 2
        assert anos[0] == (2025, 2)
        assert anos[1] == (2024, 1)
    
    def test_aluno_sem_historico_retorna_anos_disponiveis(self, mock_get_cursor, mock_cursor):
        """Testa caso onde aluno não tem matrícula mas retorna anos disponíveis."""
        # Configurar mocks
        mock_cursor.fetchall.side_effect = [
            [],  # sem matrículas
            [{'ano_letivo': 2025, 'id': 2}, {'ano_letivo': 2024, 'id': 1}]  # anos disponíveis
        ]
        mock_cursor.fetchone.return_value = None
        
        tem_historico, anos = verificar_historico_matriculas(1)
        
        assert tem_historico is True
        assert len(anos) == 2
    
    def test_id_invalido(self):
        """Testa comportamento com ID inválido."""
        with patch('src.services.aluno_service.messagebox.showerror'):
            tem_historico, anos = verificar_historico_matriculas(cast(int, None))
        
        assert tem_historico is False
        assert anos == []


class TestExcluirAlunoComConfirmacao:
    """Testes para a função excluir_aluno_com_confirmacao."""
    
    def test_exclusao_cancelada_por_matricula_ativa(self, mock_get_cursor, mock_cursor):
        """Testa que não permite excluir aluno com matrícula ativa."""
        # Mock verificar_matricula_ativa para retornar True
        with patch('src.services.aluno_service.verificar_matricula_ativa', return_value=True):
            with patch('src.services.aluno_service.messagebox.showwarning'):
                resultado = excluir_aluno_com_confirmacao(1, "João Silva")
        
        assert resultado is False
    
    def test_exclusao_cancelada_pelo_usuario(self, mock_get_cursor, mock_cursor):
        """Testa cancelamento da exclusão pelo usuário."""
        with patch('src.services.aluno_service.verificar_matricula_ativa', return_value=False):
            with patch('src.services.aluno_service.messagebox.askyesno', return_value=False):
                resultado = excluir_aluno_com_confirmacao(1, "João Silva")
        
        assert resultado is False
    
    def test_exclusao_bem_sucedida(self, mock_get_cursor, mock_cursor):
        """Testa exclusão bem-sucedida de aluno."""
        with patch('src.services.aluno_service.verificar_matricula_ativa', return_value=False):
            with patch('src.services.aluno_service.messagebox.askyesno', return_value=True):
                with patch('src.services.aluno_service.messagebox.showinfo'):
                    resultado = excluir_aluno_com_confirmacao(1, "João Silva")
        
        assert resultado is True
        mock_cursor.execute.assert_called_once()
        # Verificar que o SQL foi executado
        assert "DELETE FROM alunos" in mock_cursor.execute.call_args[0][0]
    
    def test_exclusao_com_callback(self, mock_get_cursor, mock_cursor):
        """Testa que callback é executado após exclusão bem-sucedida."""
        callback = Mock()
        
        with patch('src.services.aluno_service.verificar_matricula_ativa', return_value=False):
            with patch('src.services.aluno_service.messagebox.askyesno', return_value=True):
                with patch('src.services.aluno_service.messagebox.showinfo'):
                    resultado = excluir_aluno_com_confirmacao(1, "João Silva", callback_sucesso=callback)
        
        assert resultado is True
        callback.assert_called_once()


class TestObterAlunoPorId:
    """Testes para a função obter_aluno_por_id."""
    
    def test_aluno_encontrado(self, mock_get_cursor, mock_cursor):
        """Testa obtenção bem-sucedida de dados do aluno."""
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'nome': 'João Silva',
            'data_nascimento': '2010-05-15',
            'cpf': '12345678900',
            'email': 'joao@example.com',
            'telefone': '11999999999',
            'endereco': 'Rua A, 123',
            'escola_id': 60
        }
        
        resultado = obter_aluno_por_id(1)
        
        assert resultado is not None
        assert resultado['nome'] == 'João Silva'
        assert resultado['cpf'] == '12345678900'
    
    def test_aluno_nao_encontrado(self, mock_get_cursor, mock_cursor):
        """Testa caso onde aluno não existe."""
        mock_cursor.fetchone.return_value = None
        
        resultado = obter_aluno_por_id(999)
        
        assert resultado is None
    
    def test_id_invalido(self):
        """Testa comportamento com ID inválido."""
        resultado = obter_aluno_por_id(cast(int, "inválido"))
        
        assert resultado is None
