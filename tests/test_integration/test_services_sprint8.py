"""
Testes de integração para declaracao_service e estatistica_service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.declaracao_service import (
    identificar_tipo_pessoa,
    obter_dados_aluno_para_declaracao,
    obter_dados_funcionario_para_declaracao,
    validar_dados_declaracao,
    registrar_geracao_declaracao
)
from src.services.estatistica_service import (
    obter_estatisticas_alunos,
    obter_estatisticas_por_ano_letivo,
    obter_alunos_por_situacao,
    calcular_media_idade_alunos
)


class TestDeclaracaoServiceIntegration:
    """Testes de integração para declaracao_service"""
    
    @patch('services.declaracao_service.get_cursor')
    def test_identificar_aluno(self, mock_get_cursor):
        """Deve identificar pessoa como Aluno"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 1}
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        sucesso, tipo = identificar_tipo_pessoa(1)
        
        assert sucesso is True
        assert tipo == 'Aluno'
    
    @patch('services.declaracao_service.get_cursor')
    def test_identificar_funcionario(self, mock_get_cursor):
        """Deve identificar pessoa como Funcionário"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [None, {'id': 1}]
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        sucesso, tipo = identificar_tipo_pessoa(1)
        
        assert sucesso is True
        assert tipo == 'Funcionário'
    
    @patch('services.declaracao_service.get_cursor')
    def test_obter_dados_aluno_completo(self, mock_get_cursor):
        """Deve obter dados completos do aluno para declaração"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'aluno_id': 1,
            'nome': 'João Silva',
            'cpf': '123.456.789-00',
            'data_nascimento': '2010-05-15',
            'matricula': 'MAT2025001',
            'serie': '5º Ano',
            'turma': 'A',
            'turno': 'Matutino'
        }
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        dados = obter_dados_aluno_para_declaracao(1)
        
        assert dados is not None
        assert dados['nome'] == 'João Silva'
        assert dados['serie'] == '5º Ano'
    
    @patch('services.declaracao_service.get_cursor')
    def test_obter_dados_funcionario_completo(self, mock_get_cursor):
        """Deve obter dados completos do funcionário para declaração"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'funcionario_id': 1,
            'nome': 'Maria Santos',
            'cpf': '987.654.321-00',
            'cargo': 'Professor(a)',
            'data_admissao': '2020-02-01'
        }
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        dados = obter_dados_funcionario_para_declaracao(1)
        
        assert dados is not None
        assert dados['nome'] == 'Maria Santos'
        assert dados['cargo'] == 'Professor(a)'
    
    def test_validar_dados_aluno_transferencia(self):
        """Deve validar dados de aluno para declaração de transferência"""
        dados = {
            'nome': 'João Silva',
            'matricula': 'MAT2025001',
            'serie': '5º Ano',
            'turma': 'A'
        }
        
        valido, mensagem = validar_dados_declaracao('Aluno', dados, 'Transferência')
        
        assert valido is True
        assert mensagem == ''
    
    def test_validar_dados_aluno_incompletos(self):
        """Deve rejeitar dados incompletos de aluno"""
        dados = {
            'nome': 'João Silva'
            # Faltam matrícula, série, turma
        }
        
        valido, mensagem = validar_dados_declaracao('Aluno', dados, 'Transferência')
        
        assert valido is False
        assert 'incompletos' in mensagem.lower()
    
    def test_validar_dados_funcionario_trabalho(self):
        """Deve validar dados de funcionário para declaração de trabalho"""
        dados = {
            'nome': 'Maria Santos',
            'cargo': 'Professor(a)',
            'data_admissao': '2020-02-01'
        }
        
        valido, mensagem = validar_dados_declaracao('Funcionário', dados, 'Trabalho')
        
        assert valido is True
    
    @patch('services.declaracao_service.get_cursor')
    def test_registrar_geracao_declaracao(self, mock_get_cursor):
        """Deve registrar geração de declaração no sistema"""
        mock_cursor = MagicMock()
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        sucesso = registrar_geracao_declaracao(
            pessoa_id=1,
            tipo_pessoa='Aluno',
            tipo_declaracao='Transferência',
            motivo_outros=None
        )
        
        assert sucesso is True
        mock_cursor.execute.assert_called_once()


class TestEstatisticaServiceIntegration:
    """Testes de integração para estatistica_service"""
    
    @patch('services.estatistica_service.get_cursor')
    def test_obter_estatisticas_alunos(self, mock_get_cursor):
        """Deve obter estatísticas gerais de alunos"""
        mock_cursor = MagicMock()
        
        # Mock para total de alunos
        mock_cursor.fetchone.side_effect = [
            {'total_alunos': 150},  # total
            {'alunos_ativos': 145},  # ativos
            {'alunos_sem_matricula': 5}  # sem matrícula
        ]
        
        # Mock para alunos por série
        mock_cursor.fetchall.side_effect = [
            [
                {'serie': '1º Ano', 'quantidade': 30},
                {'serie': '2º Ano', 'quantidade': 25},
                {'serie': '3º Ano', 'quantidade': 28}
            ],
            [
                {'turno': 'Matutino', 'quantidade': 90},
                {'turno': 'Vespertino', 'quantidade': 60}
            ]
        ]
        
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        resultado = obter_estatisticas_alunos(escola_id=60)
        
        assert resultado is not None
        assert resultado['total_alunos'] == 150
        assert resultado['alunos_ativos'] == 145
        assert len(resultado['alunos_por_serie']) == 3
        assert len(resultado['alunos_por_turno']) == 2
    
    @patch('services.estatistica_service.get_cursor')
    def test_obter_estatisticas_por_ano_letivo(self, mock_get_cursor):
        """Deve obter estatísticas por ano letivo específico"""
        mock_cursor = MagicMock()
        
        mock_cursor.fetchone.return_value = {
            'total_matriculas': 148,
            'matriculas_ativas': 145,
            'matriculas_transferidas': 3,
            'matriculas_evadidas': 0,
            'taxa_conclusao': 98.0
        }
        
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        resultado = obter_estatisticas_por_ano_letivo(5, escola_id=60)
        
        assert resultado is not None
        assert resultado['total_matriculas'] == 148
        assert resultado['matriculas_ativas'] == 145
        assert resultado['taxa_conclusao'] == 98.0
    
    @patch('services.estatistica_service.get_cursor')
    def test_obter_alunos_por_situacao_com_matricula(self, mock_get_cursor):
        """Deve filtrar alunos com matrícula"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'aluno_id': 1,
                'nome': 'João Silva',
                'serie': '5º Ano',
                'turma': 'A',
                'status_matricula': 'Ativo'
            },
            {
                'aluno_id': 2,
                'nome': 'Maria Santos',
                'serie': '6º Ano',
                'turma': 'B',
                'status_matricula': 'Ativo'
            }
        ]
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        resultado = obter_alunos_por_situacao('com_matricula', escola_id=60)
        
        assert len(resultado) == 2
        assert resultado[0]['nome'] == 'João Silva'
    
    @patch('services.estatistica_service.get_cursor')
    def test_obter_alunos_sem_matricula(self, mock_get_cursor):
        """Deve filtrar alunos sem matrícula"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'aluno_id': 5,
                'nome': 'Pedro Costa',
                'data_nascimento': '2010-03-20'
            }
        ]
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        resultado = obter_alunos_por_situacao('sem_matricula', escola_id=60)
        
        assert len(resultado) == 1
        assert resultado[0]['nome'] == 'Pedro Costa'
    
    @patch('services.estatistica_service.get_cursor')
    def test_calcular_media_idade_alunos(self, mock_get_cursor):
        """Deve calcular média de idade dos alunos"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'media_idade': 10.5}
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        resultado = calcular_media_idade_alunos(escola_id=60)
        
        assert resultado == 10.5
    
    @patch('services.estatistica_service.get_cursor')
    def test_calcular_media_idade_retorna_zero_sem_alunos(self, mock_get_cursor):
        """Deve retornar 0 se não houver alunos"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'media_idade': None}
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        resultado = calcular_media_idade_alunos(escola_id=60)
        
        assert resultado == 0.0


class TestFluxosCompletos:
    """Testes de fluxos completos entre services"""
    
    @patch('services.declaracao_service.get_cursor')
    def test_fluxo_geracao_declaracao_aluno(self, mock_get_cursor):
        """Teste fluxo completo de geração de declaração de aluno"""
        mock_cursor = MagicMock()
        
        # 1. Identificar tipo
        mock_cursor.fetchone.side_effect = [
            {'id': 1},  # é aluno
            {  # dados do aluno
                'aluno_id': 1,
                'nome': 'João Silva',
                'cpf': '123.456.789-00',
                'matricula': 'MAT2025001',
                'serie': '5º Ano',
                'turma': 'A'
            }
        ]
        mock_get_cursor.return_value.__enter__.return_value = mock_cursor
        
        # Executar fluxo
        sucesso, tipo = identificar_tipo_pessoa(1)
        assert sucesso and tipo == 'Aluno'
        
        mock_cursor.fetchone.side_effect = [
            {
                'aluno_id': 1,
                'nome': 'João Silva',
                'cpf': '123.456.789-00',
                'matricula': 'MAT2025001',
                'serie': '5º Ano',
                'turma': 'A'
            }
        ]
        
        dados = obter_dados_aluno_para_declaracao(1)
        assert dados is not None
        
        valido, msg = validar_dados_declaracao('Aluno', dados, 'Transferência')
        assert valido
        
        sucesso_registro = registrar_geracao_declaracao(1, 'Aluno', 'Transferência')
        assert sucesso_registro
