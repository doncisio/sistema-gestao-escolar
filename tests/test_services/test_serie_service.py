"""
Testes para o módulo services.serie_service
Testa funções de gerenciamento de séries escolares
"""

import pytest
from unittest.mock import Mock, patch
from src.services.serie_service import (
    listar_series,
    obter_serie_por_id,
    obter_serie_por_nome,
    obter_proxima_serie,
    obter_serie_anterior,
    validar_progressao_serie,
    obter_estatisticas_serie,
    buscar_series,
    obter_ciclos
)


class TestListarSeries:
    """Testes para listar_series()"""
    
    @patch('src.services.serie_service.get_connection')
    def test_listar_todas_series(self, mock_conn):
        """Testa listagem de todas as séries"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'nome': '1º Ano', 'ciclo': 'Ensino Fundamental I', 'ordem': 1},
            {'id': 2, 'nome': '2º Ano', 'ciclo': 'Ensino Fundamental I', 'ordem': 2}
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        series = listar_series()
        
        assert len(series) == 2
        assert series[0]['nome'] == '1º Ano'
    
    @patch('src.services.serie_service.get_connection')
    def test_listar_series_por_ciclo(self, mock_conn):
        """Testa filtro por ciclo"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'nome': '1º Ano', 'ciclo': 'Ensino Fundamental I'}
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        series = listar_series(ciclo='Ensino Fundamental I')
        
        assert len(series) == 1
        mock_cursor.execute.assert_called_once()


class TestObterSeriePorId:
    """Testes para obter_serie_por_id()"""
    
    @patch('src.services.serie_service.get_connection')
    def test_obter_serie_existente(self, mock_conn):
        """Testa obtenção de série existente"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {
            'id': 5,
            'nome': '5º Ano',
            'ciclo': 'Ensino Fundamental I',
            'ordem': 5
        }
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        serie = obter_serie_por_id(5)
        
        assert serie is not None
        assert serie['nome'] == '5º Ano'
    
    @patch('src.services.serie_service.get_connection')
    def test_obter_serie_inexistente(self, mock_conn):
        """Testa série que não existe"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        serie = obter_serie_por_id(999)
        
        assert serie is None


class TestObterSeriePorNome:
    """Testes para obter_serie_por_nome()"""
    
    @patch('src.services.serie_service.get_connection')
    def test_obter_serie_por_nome_existente(self, mock_conn):
        """Testa busca por nome"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {
            'id': 3,
            'nome': '3º Ano',
            'ordem': 3
        }
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        serie = obter_serie_por_nome('3º Ano')
        
        assert serie is not None
        assert serie['id'] == 3


class TestProximaSerie:
    """Testes para obter_proxima_serie()"""
    
    @patch('src.services.serie_service.get_connection')
    @patch('src.services.serie_service.obter_serie_por_id')
    def test_obter_proxima_serie(self, mock_obter, mock_conn):
        """Testa obtenção da próxima série"""
        mock_obter.return_value = {'id': 1, 'nome': '1º Ano', 'ordem': 1}
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {
            'id': 2,
            'nome': '2º Ano',
            'ordem': 2
        }
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        proxima = obter_proxima_serie(1)
        
        assert proxima is not None
        assert proxima['nome'] == '2º Ano'
    
    @patch('src.services.serie_service.get_connection')
    @patch('src.services.serie_service.obter_serie_por_id')
    def test_ultima_serie_sem_proxima(self, mock_obter, mock_conn):
        """Testa última série sem próxima"""
        mock_obter.return_value = {'id': 12, 'nome': '3º Ano EM', 'ordem': 12}
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        proxima = obter_proxima_serie(12)
        
        assert proxima is None


class TestSerieAnterior:
    """Testes para obter_serie_anterior()"""
    
    @patch('src.services.serie_service.get_connection')
    @patch('src.services.serie_service.obter_serie_por_id')
    def test_obter_serie_anterior(self, mock_obter, mock_conn):
        """Testa obtenção da série anterior"""
        mock_obter.return_value = {'id': 5, 'nome': '5º Ano', 'ordem': 5}
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {
            'id': 4,
            'nome': '4º Ano',
            'ordem': 4
        }
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        anterior = obter_serie_anterior(5)
        
        assert anterior is not None
        assert anterior['nome'] == '4º Ano'


class TestValidarProgressao:
    """Testes para validar_progressao_serie()"""
    
    @patch('src.services.serie_service.obter_serie_por_id')
    def test_progressao_valida_sequencial(self, mock_obter):
        """Testa progressão válida sequencial"""
        mock_obter.side_effect = [
            {'id': 1, 'nome': '1º Ano', 'ordem': 1},
            {'id': 2, 'nome': '2º Ano', 'ordem': 2}
        ]
        
        valido, msg = validar_progressao_serie(1, 2)
        
        assert valido is True
        assert 'válida' in msg.lower()
    
    @patch('src.services.serie_service.obter_serie_por_id')
    def test_progressao_invalida_regressiva(self, mock_obter):
        """Testa progressão inválida (regressiva)"""
        mock_obter.side_effect = [
            {'id': 5, 'nome': '5º Ano', 'ordem': 5},
            {'id': 3, 'nome': '3º Ano', 'ordem': 3}
        ]
        
        valido, msg = validar_progressao_serie(5, 3)
        
        assert valido is False
        assert 'inválida' in msg.lower()
    
    @patch('src.services.serie_service.obter_serie_por_id')
    def test_progressao_pulando_series(self, mock_obter):
        """Testa progressão pulando séries"""
        mock_obter.side_effect = [
            {'id': 1, 'nome': '1º Ano', 'ordem': 1},
            {'id': 3, 'nome': '3º Ano', 'ordem': 3}
        ]
        
        valido, msg = validar_progressao_serie(1, 3)
        
        assert valido is True
        assert 'pulando' in msg.lower() or 'Atenção' in msg


class TestEstatisticasSerie:
    """Testes para obter_estatisticas_serie()"""
    
    @patch('src.services.serie_service.get_connection')
    def test_obter_estatisticas(self, mock_conn):
        """Testa obtenção de estatísticas de série"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {
            'id': 5,
            'nome': '5º Ano',
            'total_turmas': 3,
            'total_alunos': 85,
            'alunos_ativos': 80,
            'capacidade_total': 90
        }
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        stats = obter_estatisticas_serie(5, 2025)
        
        assert stats is not None
        assert stats['total_turmas'] == 3
        assert 'taxa_ocupacao' in stats
    
    @patch('src.services.serie_service.get_connection')
    def test_estatisticas_serie_sem_turmas(self, mock_conn):
        """Testa estatísticas de série sem turmas"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        stats = obter_estatisticas_serie(999, 2025)
        
        assert stats['total_turmas'] == 0
        assert stats['taxa_ocupacao'] == 0.0


class TestBuscarSeries:
    """Testes para buscar_series()"""
    
    @patch('src.services.serie_service.get_connection')
    def test_buscar_series_por_nome(self, mock_conn):
        """Testa busca por nome"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'nome': '1º Ano'},
            {'id': 2, 'nome': '2º Ano'}
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        series = buscar_series('Ano')
        
        assert len(series) == 2


class TestObterCiclos:
    """Testes para obter_ciclos()"""
    
    @patch('src.services.serie_service.get_connection')
    def test_obter_todos_ciclos(self, mock_conn):
        """Testa obtenção de todos os ciclos"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('Ensino Fundamental I',),
            ('Ensino Fundamental II',),
            ('Ensino Médio',)
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        ciclos = obter_ciclos()
        
        assert len(ciclos) == 3
        assert 'Ensino Fundamental I' in ciclos
