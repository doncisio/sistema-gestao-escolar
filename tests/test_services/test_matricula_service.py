"""
Testes para o módulo services/matricula_service.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services import matricula_service as ms


class TestObterAnoLetivoAtual:
    """Testes para obter_ano_letivo_atual"""
    
    @patch('services.matricula_service.get_cursor')
    def test_obter_ano_letivo_atual_sucesso(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = {'id': 5}
        
        resultado = ms.obter_ano_letivo_atual()
        
        assert resultado == 5
        mock_cursor_instance.execute.assert_called_once()
    
    @patch('services.matricula_service.get_cursor')
    def test_obter_ano_letivo_atual_nao_encontrado(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = None
        
        resultado = ms.obter_ano_letivo_atual()
        
        assert resultado is None


class TestObterSeriesDisponiveis:
    """Testes para obter_series_disponiveis"""
    
    @patch('services.matricula_service.get_cursor')
    def test_obter_series_sucesso(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchall.return_value = [
            {'id': 1, 'nome': '1º Ano'},
            {'id': 2, 'nome': '2º Ano'}
        ]
        
        resultado = ms.obter_series_disponiveis()
        
        assert len(resultado) == 2
        assert resultado[0]['nome'] == '1º Ano'
    
    @patch('services.matricula_service.get_cursor')
    def test_obter_series_vazio(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchall.return_value = []
        
        resultado = ms.obter_series_disponiveis()
        
        assert resultado == []


class TestObterTurmasPorSerie:
    """Testes para obter_turmas_por_serie"""
    
    @patch('services.matricula_service.get_cursor')
    def test_obter_turmas_sucesso(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchall.return_value = [
            {'id': 10, 'nome': 'Turma A'},
            {'id': 11, 'nome': 'Turma B'}
        ]
        
        resultado = ms.obter_turmas_por_serie(1, 5)
        
        assert len(resultado) == 2
        assert resultado[0]['nome'] == 'Turma A'


class TestVerificarMatriculaExistente:
    """Testes para verificar_matricula_existente"""
    
    @patch('services.matricula_service.get_cursor')
    def test_verificar_matricula_existente_encontrada(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = {
            'id': 1, 'status': 'Ativo', 'turma': 'Turma A', 'serie': '1º Ano'
        }
        
        resultado = ms.verificar_matricula_existente(100, 5)
        
        assert resultado is not None
        assert resultado['status'] == 'Ativo'
    
    @patch('services.matricula_service.get_cursor')
    def test_verificar_matricula_inexistente(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = None
        
        resultado = ms.verificar_matricula_existente(100, 5)
        
        assert resultado is None


class TestMatricularAluno:
    """Testes para matricular_aluno"""
    
    @patch('services.matricula_service.verificar_matricula_existente')
    @patch('services.matricula_service.get_cursor')
    def test_matricular_aluno_sucesso(self, mock_cursor, mock_verificar):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_verificar.return_value = None
        
        sucesso, mensagem = ms.matricular_aluno(100, 10, 5)
        
        assert sucesso is True
        assert "sucesso" in mensagem.lower()
        mock_cursor_instance.execute.assert_called_once()
    
    @patch('services.matricula_service.verificar_matricula_existente')
    def test_matricular_aluno_ja_matriculado(self, mock_verificar):
        mock_verificar.return_value = {
            'id': 1, 'status': 'Ativo', 'turma': 'Turma A'
        }
        
        sucesso, mensagem = ms.matricular_aluno(100, 10, 5)
        
        assert sucesso is False
        assert "já possui matrícula" in mensagem.lower()


class TestTransferirAluno:
    """Testes para transferir_aluno"""
    
    @patch('services.matricula_service.get_cursor')
    def test_transferir_aluno_sucesso(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = {'id': 1}
        
        sucesso, mensagem = ms.transferir_aluno(1, 20)
        
        assert sucesso is True
        assert "sucesso" in mensagem.lower()
    
    @patch('services.matricula_service.get_cursor')
    def test_transferir_aluno_matricula_inexistente(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = None
        
        sucesso, mensagem = ms.transferir_aluno(999, 20)
        
        assert sucesso is False
        assert "não encontrada" in mensagem.lower()


class TestCancelarMatricula:
    """Testes para cancelar_matricula"""
    
    @patch('services.matricula_service.get_cursor')
    def test_cancelar_matricula_sucesso(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = {'id': 1, 'status': 'Ativo'}
        
        sucesso, mensagem = ms.cancelar_matricula(1, "Transferência")
        
        assert sucesso is True
        assert "cancelada" in mensagem.lower()
    
    @patch('services.matricula_service.get_cursor')
    def test_cancelar_matricula_ja_cancelada(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = {'id': 1, 'status': 'Cancelado'}
        
        sucesso, mensagem = ms.cancelar_matricula(1)
        
        assert sucesso is False
        assert "já está cancelada" in mensagem.lower()


class TestAtualizarStatusMatricula:
    """Testes para atualizar_status_matricula"""
    
    @patch('services.matricula_service.get_cursor')
    def test_atualizar_status_sucesso(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = {'id': 1}
        
        sucesso, mensagem = ms.atualizar_status_matricula(1, 'Concluído')
        
        assert sucesso is True
        assert "atualizado" in mensagem.lower()
    
    @patch('services.matricula_service.get_cursor')
    def test_atualizar_status_invalido(self, mock_cursor):
        sucesso, mensagem = ms.atualizar_status_matricula(1, 'StatusInvalido')
        
        assert sucesso is False
        assert "inválido" in mensagem.lower()


class TestObterMatriculaPorId:
    """Testes para obter_matricula_por_id"""
    
    @patch('services.matricula_service.get_cursor')
    def test_obter_matricula_sucesso(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = {
            'id': 1, 'aluno_id': 100, 'status': 'Ativo',
            'aluno_nome': 'João Silva', 'turma_nome': 'Turma A'
        }
        
        resultado = ms.obter_matricula_por_id(1)
        
        assert resultado is not None
        assert resultado['aluno_nome'] == 'João Silva'
    
    @patch('services.matricula_service.get_cursor')
    def test_obter_matricula_inexistente(self, mock_cursor):
        mock_cursor_instance = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor_instance
        mock_cursor_instance.fetchone.return_value = None
        
        resultado = ms.obter_matricula_por_id(999)
        
        assert resultado is None
