"""
Testes para services/boletim_service.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.boletim_service import (
    obter_ano_letivo_atual,
    verificar_status_matricula,
    decidir_tipo_documento,
    gerar_boletim_ou_transferencia,
    validar_aluno_para_boletim
)


class TestObterAnoLetivoAtual:
    """Testes para obter_ano_letivo_atual()"""
    
    @patch('services.boletim_service.get_cursor')
    def test_retorna_ano_corrente(self, mock_get_cursor):
        """Deve retornar ID do ano letivo corrente"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 5}
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        resultado = obter_ano_letivo_atual()
        
        assert resultado == 5
        mock_cursor.execute.assert_called_once()
    
    @patch('services.boletim_service.get_cursor')
    def test_retorna_ano_mais_recente_quando_corrente_nao_existe(self, mock_get_cursor):
        """Deve retornar ano mais recente se corrente não existir"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [None, {'id': 4}]
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        resultado = obter_ano_letivo_atual()
        
        assert resultado == 4
        assert mock_cursor.execute.call_count == 2
    
    @patch('services.boletim_service.get_cursor')
    def test_retorna_none_quando_nenhum_ano_existe(self, mock_get_cursor):
        """Deve retornar None se nenhum ano letivo existir"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        resultado = obter_ano_letivo_atual()
        
        assert resultado is None
    
    @patch('services.boletim_service.get_cursor')
    def test_suporta_tupla_result(self, mock_get_cursor):
        """Deve suportar resultado como tupla"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (3,)
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        resultado = obter_ano_letivo_atual()
        
        assert resultado == 3


class TestVerificarStatusMatricula:
    """Testes para verificar_status_matricula()"""
    
    @patch('services.boletim_service.get_cursor')
    def test_retorna_dados_matricula_dict(self, mock_get_cursor):
        """Deve retornar dados da matrícula (dict)"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'status': 'Ativo',
            'nome': 'João Silva',
            'ano_letivo': 2025
        }
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        resultado = verificar_status_matricula(1, 5, 60)
        
        assert resultado == {
            'status': 'Ativo',
            'nome_aluno': 'João Silva',
            'ano_letivo': 2025
        }
    
    @patch('services.boletim_service.get_cursor')
    def test_retorna_dados_matricula_tuple(self, mock_get_cursor):
        """Deve retornar dados da matrícula (tuple)"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ('Transferido', 'Maria Santos', 2024)
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        resultado = verificar_status_matricula(2, 4, 60)
        
        assert resultado == {
            'status': 'Transferido',
            'nome_aluno': 'Maria Santos',
            'ano_letivo': 2024
        }
    
    @patch('services.boletim_service.get_cursor')
    def test_retorna_none_quando_matricula_nao_existe(self, mock_get_cursor):
        """Deve retornar None se matrícula não existir"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        resultado = verificar_status_matricula(999, 5, 60)
        
        assert resultado is None


class TestDecidirTipoDocumento:
    """Testes para decidir_tipo_documento()"""
    
    @patch('services.boletim_service.verificar_status_matricula')
    @patch('services.boletim_service.obter_ano_letivo_atual')
    def test_retorna_boletim_para_aluno_ativo(self, mock_ano, mock_status):
        """Deve retornar 'Boletim' para aluno ativo"""
        mock_ano.return_value = 5
        mock_status.return_value = {
            'status': 'Ativo',
            'nome_aluno': 'João Silva',
            'ano_letivo': 2025
        }
        
        tipo, dados = decidir_tipo_documento(1, 5)
        
        assert tipo == 'Boletim'
        assert dados['status'] == 'Ativo'
    
    @patch('services.boletim_service.verificar_status_matricula')
    @patch('services.boletim_service.obter_ano_letivo_atual')
    def test_retorna_transferencia_para_aluno_transferido(self, mock_ano, mock_status):
        """Deve retornar 'Transferência' para aluno transferido"""
        mock_ano.return_value = 5
        mock_status.return_value = {
            'status': 'Transferido',
            'nome_aluno': 'Maria Santos',
            'ano_letivo': 2025
        }
        
        tipo, dados = decidir_tipo_documento(2, 5)
        
        assert tipo == 'Transferência'
        assert dados['status'] == 'Transferido'
    
    @patch('services.boletim_service.verificar_status_matricula')
    @patch('services.boletim_service.obter_ano_letivo_atual')
    def test_retorna_erro_quando_ano_nao_determinado(self, mock_ano, mock_status):
        """Deve retornar erro se ano letivo não puder ser determinado"""
        mock_ano.return_value = None
        
        tipo, dados = decidir_tipo_documento(1, None)
        
        assert tipo == 'Erro'
        assert 'mensagem' in dados
    
    @patch('services.boletim_service.verificar_status_matricula')
    @patch('services.boletim_service.obter_ano_letivo_atual')
    def test_retorna_erro_quando_matricula_nao_encontrada(self, mock_ano, mock_status):
        """Deve retornar erro se matrícula não for encontrada"""
        mock_ano.return_value = 5
        mock_status.return_value = None
        
        tipo, dados = decidir_tipo_documento(999, 5)
        
        assert tipo == 'Erro'
        assert 'status da matrícula' in dados['mensagem']


class TestGerarBoletimOuTransferencia:
    """Testes para gerar_boletim_ou_transferencia()"""
    
    @patch('services.boletim_service.decidir_tipo_documento')
    @patch('services.boletim_service.obter_ano_letivo_atual')
    def test_gera_boletim_para_aluno_ativo(self, mock_ano, mock_decidir):
        """Deve gerar boletim para aluno ativo"""
        mock_ano.return_value = 5
        mock_decidir.return_value = ('Boletim', {
            'nome_aluno': 'João Silva',
            'ano_letivo': 2025
        })
        
        with patch('services.boletim_service.boletim') as mock_boletim:
            mock_boletim.return_value = True
            
            sucesso, mensagem = gerar_boletim_ou_transferencia(1, 5)
            
            assert sucesso is True
            assert 'Boletim gerado' in mensagem
            mock_boletim.assert_called_once_with(1, 5)
    
    @patch('services.boletim_service.decidir_tipo_documento')
    @patch('services.boletim_service.obter_ano_letivo_atual')
    def test_gera_transferencia_para_aluno_transferido(self, mock_ano, mock_decidir):
        """Deve gerar documento de transferência"""
        mock_ano.return_value = 5
        mock_decidir.return_value = ('Transferência', {
            'nome_aluno': 'Maria Santos',
            'ano_letivo': 2025
        })
        
        with patch('services.boletim_service.gerar_documento_transferencia') as mock_transf:
            sucesso, mensagem = gerar_boletim_ou_transferencia(2, 5)
            
            assert sucesso is True
            assert 'transferência' in mensagem.lower()
            mock_transf.assert_called_once_with(2, 5)
    
    @patch('services.boletim_service.decidir_tipo_documento')
    def test_retorna_erro_quando_decisao_falha(self, mock_decidir):
        """Deve retornar erro se decisão de documento falhar"""
        mock_decidir.return_value = ('Erro', {'mensagem': 'Erro ao verificar'})
        
        sucesso, mensagem = gerar_boletim_ou_transferencia(999, 5)
        
        assert sucesso is False
        assert 'Erro ao verificar' in mensagem


class TestValidarAlunoParaBoletim:
    """Testes para validar_aluno_para_boletim()"""
    
    @patch('services.boletim_service.verificar_status_matricula')
    @patch('services.boletim_service.obter_ano_letivo_atual')
    @patch('services.boletim_service.get_cursor')
    def test_valida_aluno_existente_com_matricula(self, mock_cursor_ctx, mock_ano, mock_status):
        """Deve validar aluno existente com matrícula"""
        mock_ano.return_value = 5
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 1}
        mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor
        mock_status.return_value = {'status': 'Ativo'}
        
        valido, mensagem = validar_aluno_para_boletim(1, 5)
        
        assert valido is True
        assert mensagem == ''
    
    @patch('services.boletim_service.obter_ano_letivo_atual')
    @patch('services.boletim_service.get_cursor')
    def test_retorna_erro_para_aluno_inexistente(self, mock_cursor_ctx, mock_ano):
        """Deve retornar erro para aluno inexistente"""
        mock_ano.return_value = 5
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor
        
        valido, mensagem = validar_aluno_para_boletim(999, 5)
        
        assert valido is False
        assert 'não encontrado' in mensagem
    
    @patch('services.boletim_service.verificar_status_matricula')
    @patch('services.boletim_service.obter_ano_letivo_atual')
    @patch('services.boletim_service.get_cursor')
    def test_retorna_erro_para_aluno_sem_matricula(self, mock_cursor_ctx, mock_ano, mock_status):
        """Deve retornar erro para aluno sem matrícula no ano"""
        mock_ano.return_value = 5
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 1}
        mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor
        mock_status.return_value = None
        
        valido, mensagem = validar_aluno_para_boletim(1, 5)
        
        assert valido is False
        assert 'não possui matrícula' in mensagem
