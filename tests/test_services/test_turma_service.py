"""
Testes para o módulo services.turma_service
Testa funções de gerenciamento de turmas
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.turma_service import (
    listar_turmas,
    obter_turma_por_id,
    verificar_capacidade_turma,
    criar_turma,
    atualizar_turma,
    excluir_turma,
    buscar_turmas,
    obter_turmas_por_serie,
    obter_turmas_por_turno
)


class TestListarTurmas:
    """Testes para listar_turmas()"""
    
    @patch('src.services.turma_service.get_connection')
    def test_listar_todas_turmas(self, mock_conn):
        """Testa listagem de todas as turmas sem filtros"""
        # Setup
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'nome': 'A', 'turno': 'Matutino', 'total_alunos': 25},
            {'id': 2, 'nome': 'B', 'turno': 'Vespertino', 'total_alunos': 23}
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        # Execute
        turmas = listar_turmas()
        
        # Verify
        assert len(turmas) == 2
        assert turmas[0]['nome'] == 'A'
        assert turmas[1]['total_alunos'] == 23
    
    @patch('src.services.turma_service.get_connection')
    def test_listar_turmas_por_serie(self, mock_conn):
        """Testa filtro por série"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [{'id': 1, 'nome': 'A', 'serie_id': 5}]
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        turmas = listar_turmas(serie_id=5, ano_letivo_id=2025)
        
        assert len(turmas) == 1
        mock_cursor.execute.assert_called_once()
    
    @patch('src.services.turma_service.get_connection')
    def test_listar_turmas_por_turno(self, mock_conn):
        """Testa filtro por turno"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'turno': 'Matutino'},
            {'id': 2, 'turno': 'Matutino'}
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        turmas = listar_turmas(turno='Matutino', ano_letivo_id=2025)
        
        assert len(turmas) == 2
        assert all(t['turno'] == 'Matutino' for t in turmas)


class TestObterTurmaPorId:
    """Testes para obter_turma_por_id()"""
    
    @patch('src.services.turma_service.get_connection')
    def test_obter_turma_existente(self, mock_conn):
        """Testa obtenção de turma existente"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {
            'id': 10,
            'nome': 'Turma A',
            'total_alunos': 30,
            'capacidade_maxima': 35
        }
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        turma = obter_turma_por_id(10)
        
        assert turma is not None
        assert turma['id'] == 10
        assert turma['nome'] == 'Turma A'
    
    @patch('src.services.turma_service.get_connection')
    def test_obter_turma_inexistente(self, mock_conn):
        """Testa obtenção de turma que não existe"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        turma = obter_turma_por_id(999)
        
        assert turma is None


class TestVerificarCapacidadeTurma:
    """Testes para verificar_capacidade_turma()"""
    
    @patch('src.services.turma_service.obter_turma_por_id')
    def test_turma_com_vagas(self, mock_obter):
        """Testa turma com vagas disponíveis"""
        mock_obter.return_value = {
            'id': 1,
            'total_alunos': 25,
            'capacidade_maxima': 30
        }
        
        tem_vaga, total, capacidade = verificar_capacidade_turma(1)
        
        assert tem_vaga is True
        assert total == 25
        assert capacidade == 30
    
    @patch('src.services.turma_service.obter_turma_por_id')
    def test_turma_lotada(self, mock_obter):
        """Testa turma sem vagas"""
        mock_obter.return_value = {
            'id': 1,
            'total_alunos': 30,
            'capacidade_maxima': 30
        }
        
        tem_vaga, total, capacidade = verificar_capacidade_turma(1)
        
        assert tem_vaga is False
        assert total == 30
        assert capacidade == 30
    
    @patch('src.services.turma_service.obter_turma_por_id')
    def test_turma_inexistente(self, mock_obter):
        """Testa verificação de turma que não existe"""
        mock_obter.return_value = None
        
        tem_vaga, total, capacidade = verificar_capacidade_turma(999)
        
        assert tem_vaga is False
        assert total == 0
        assert capacidade == 0


class TestCriarTurma:
    """Testes para criar_turma()"""
    
    @patch('src.services.turma_service.get_connection')
    @patch('src.services.turma_service.listar_turmas')
    def test_criar_turma_sucesso(self, mock_listar, mock_conn):
        """Testa criação de turma bem-sucedida"""
        mock_listar.return_value = []  # Nenhuma turma existente
        mock_cursor = Mock()
        mock_cursor.lastrowid = 100
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.__enter__.return_value.commit = Mock()
        
        sucesso, msg, turma_id = criar_turma(
            nome='A',
            turno='Matutino',
            capacidade_maxima=30,
            ano_letivo_id=2025,
            serie_id=5,
            escola_id=60
        )
        
        assert sucesso is True
        assert 'sucesso' in msg.lower()
        assert turma_id == 100
    
    def test_criar_turma_nome_vazio(self):
        """Testa validação de nome vazio"""
        sucesso, msg, turma_id = criar_turma(
            nome='',
            turno='Matutino',
            capacidade_maxima=30,
            ano_letivo_id=2025,
            serie_id=5,
            escola_id=60
        )
        
        assert sucesso is False
        assert 'obrigatório' in msg.lower()
        assert turma_id is None
    
    def test_criar_turma_turno_invalido(self):
        """Testa validação de turno inválido"""
        sucesso, msg, turma_id = criar_turma(
            nome='A',
            turno='Integral',  # Turno não permitido
            capacidade_maxima=30,
            ano_letivo_id=2025,
            serie_id=5,
            escola_id=60
        )
        
        assert sucesso is False
        assert 'inválido' in msg.lower()
    
    @patch('src.services.turma_service.listar_turmas')
    def test_criar_turma_duplicada(self, mock_listar):
        """Testa tentativa de criar turma com nome duplicado"""
        mock_listar.return_value = [{'nome': 'A'}]
        
        sucesso, msg, turma_id = criar_turma(
            nome='A',
            turno='Matutino',
            capacidade_maxima=30,
            ano_letivo_id=2025,
            serie_id=5,
            escola_id=60
        )
        
        assert sucesso is False
        assert 'já existe' in msg.lower()


class TestAtualizarTurma:
    """Testes para atualizar_turma()"""
    
    @patch('src.services.turma_service.get_connection')
    @patch('src.services.turma_service.obter_turma_por_id')
    def test_atualizar_nome_turma(self, mock_obter, mock_conn):
        """Testa atualização do nome da turma"""
        mock_obter.return_value = {'id': 1, 'nome': 'A', 'total_alunos': 20}
        mock_conn.return_value.__enter__.return_value.cursor = Mock()
        mock_conn.return_value.__enter__.return_value.commit = Mock()
        
        sucesso, msg = atualizar_turma(1, nome='B')
        
        assert sucesso is True
        assert 'atualizada' in msg.lower()
    
    @patch('src.services.turma_service.obter_turma_por_id')
    def test_atualizar_turma_inexistente(self, mock_obter):
        """Testa atualização de turma que não existe"""
        mock_obter.return_value = None
        
        sucesso, msg = atualizar_turma(999, nome='Nova')
        
        assert sucesso is False
        assert 'não encontrada' in msg.lower()
    
    @patch('src.services.turma_service.obter_turma_por_id')
    def test_atualizar_capacidade_menor_que_alunos(self, mock_obter):
        """Testa validação de capacidade menor que total de alunos"""
        mock_obter.return_value = {'id': 1, 'total_alunos': 30}
        
        sucesso, msg = atualizar_turma(1, capacidade_maxima=25)
        
        assert sucesso is False
        assert 'menor que o total' in msg.lower()


class TestExcluirTurma:
    """Testes para excluir_turma()"""
    
    @patch('src.services.turma_service.get_connection')
    @patch('src.services.turma_service.obter_turma_por_id')
    def test_excluir_turma_vazia(self, mock_obter, mock_conn):
        """Testa exclusão de turma sem alunos"""
        mock_obter.return_value = {'id': 1, 'nome': 'A', 'total_alunos': 0}
        mock_conn.return_value.__enter__.return_value.cursor = Mock()
        mock_conn.return_value.__enter__.return_value.commit = Mock()
        
        sucesso, msg = excluir_turma(1)
        
        assert sucesso is True
        assert 'excluída' in msg.lower()
    
    @patch('src.services.turma_service.obter_turma_por_id')
    def test_excluir_turma_com_alunos(self, mock_obter):
        """Testa validação de exclusão de turma com alunos"""
        mock_obter.return_value = {'id': 1, 'nome': 'A', 'total_alunos': 25}
        
        sucesso, msg = excluir_turma(1, verificar_matriculas=True)
        
        assert sucesso is False
        assert 'possui' in msg.lower() and 'aluno' in msg.lower()


class TestBuscarTurmas:
    """Testes para buscar_turmas()"""
    
    @patch('src.services.turma_service.get_connection')
    def test_buscar_por_nome(self, mock_conn):
        """Testa busca por nome de turma"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'nome': 'Turma A'},
            {'id': 2, 'nome': 'Turma A - Especial'}
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        turmas = buscar_turmas('Turma A')
        
        assert len(turmas) == 2
        assert 'Turma A' in turmas[0]['nome']
