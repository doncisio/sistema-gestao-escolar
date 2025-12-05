"""
Testes Unitários - Transição de Ano Letivo
==========================================

Testes para validar o funcionamento da transição de ano letivo.

Uso:
    pytest tests/test_transicao_ano_letivo.py -v
    
Ou para rodar testes específicos:
    pytest tests/test_transicao_ano_letivo.py::TestVerificacoes -v
"""

import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Importar módulos a testar
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestVerificacoes:
    """Testes das funções de verificação"""
    
    def test_verificar_fim_do_ano_antes_31_12(self):
        """Deve retornar False se ainda não chegou ao fim do ano letivo"""
        from transicao_ano_letivo import InterfaceTransicaoAnoLetivo
        
        # Mock da janela Tkinter
        mock_janela = MagicMock()
        mock_janela.title = MagicMock()
        mock_janela.geometry = MagicMock()
        mock_janela.resizable = MagicMock()
        mock_janela.configure = MagicMock()
        
        with patch('transicao_ano_letivo.Frame'), \
             patch('transicao_ano_letivo.Label'), \
             patch('transicao_ano_letivo.LabelFrame'), \
             patch('transicao_ano_letivo.Button'), \
             patch('transicao_ano_letivo.ttk'), \
             patch.object(InterfaceTransicaoAnoLetivo, 'carregar_dados_iniciais'):
            
            app = InterfaceTransicaoAnoLetivo(mock_janela, mock_janela)
            
            # Simular ano letivo com data_fim no futuro
            app.ano_atual = {
                'ano_letivo': 2025,
                'data_fim': date(2025, 12, 20)
            }
            
            # Mock datetime.now() para uma data antes do fim
            with patch('transicao_ano_letivo.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 11, 15)
                resultado = app.verificar_fim_do_ano()
            
            assert resultado == False, "Deve retornar False antes do fim do ano letivo"
    
    def test_verificar_fim_do_ano_depois_data_fim(self):
        """Deve retornar True se passou da data_fim do ano letivo"""
        from transicao_ano_letivo import InterfaceTransicaoAnoLetivo
        
        mock_janela = MagicMock()
        
        with patch('transicao_ano_letivo.Frame'), \
             patch('transicao_ano_letivo.Label'), \
             patch('transicao_ano_letivo.LabelFrame'), \
             patch('transicao_ano_letivo.Button'), \
             patch('transicao_ano_letivo.ttk'), \
             patch.object(InterfaceTransicaoAnoLetivo, 'carregar_dados_iniciais'):
            
            app = InterfaceTransicaoAnoLetivo(mock_janela, mock_janela)
            
            app.ano_atual = {
                'ano_letivo': 2025,
                'data_fim': date(2025, 12, 20)
            }
            
            with patch('transicao_ano_letivo.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 12, 25)
                resultado = app.verificar_fim_do_ano()
            
            assert resultado == True, "Deve retornar True após o fim do ano letivo"
    
    def test_verificar_fim_do_ano_fallback_31_12(self):
        """Deve usar 31/12 como fallback se data_fim não estiver definida"""
        from transicao_ano_letivo import InterfaceTransicaoAnoLetivo
        
        mock_janela = MagicMock()
        
        with patch('transicao_ano_letivo.Frame'), \
             patch('transicao_ano_letivo.Label'), \
             patch('transicao_ano_letivo.LabelFrame'), \
             patch('transicao_ano_letivo.Button'), \
             patch('transicao_ano_letivo.ttk'), \
             patch.object(InterfaceTransicaoAnoLetivo, 'carregar_dados_iniciais'):
            
            app = InterfaceTransicaoAnoLetivo(mock_janela, mock_janela)
            
            # Sem data_fim
            app.ano_atual = {
                'ano_letivo': 2025,
                'data_fim': None
            }
            
            with patch('transicao_ano_letivo.datetime') as mock_datetime:
                # Depois de 31/12/2025
                mock_datetime.now.return_value = datetime(2026, 1, 5)
                mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
                resultado = app.verificar_fim_do_ano()
            
            # Deve usar fallback 31/12
            assert resultado == True


class TestProgressaoSerie:
    """Testes da progressão automática de série"""
    
    def test_obter_proxima_turma_aprovado(self):
        """Aluno aprovado deve avançar para próxima série"""
        from transicao_ano_letivo import InterfaceTransicaoAnoLetivo
        
        mock_janela = MagicMock()
        
        with patch('transicao_ano_letivo.Frame'), \
             patch('transicao_ano_letivo.Label'), \
             patch('transicao_ano_letivo.LabelFrame'), \
             patch('transicao_ano_letivo.Button'), \
             patch('transicao_ano_letivo.ttk'), \
             patch.object(InterfaceTransicaoAnoLetivo, 'carregar_dados_iniciais'):
            
            app = InterfaceTransicaoAnoLetivo(mock_janela, mock_janela)
            app.escola_id = 60
            
            # Mock do método de buscar próxima turma
            with patch('transicao_ano_letivo.QueriesTransicao.get_proxima_turma') as mock_query:
                mock_query.return_value = 15  # ID da turma do 2º ano
                
                resultado = app.obter_proxima_turma(10, reprovado=False)  # turma_id=10 (1º ano)
                
                assert resultado == 15, "Aprovado deve ir para próxima série"
                mock_query.assert_called_once_with(10, 60)
    
    def test_obter_proxima_turma_reprovado(self):
        """Aluno reprovado deve permanecer na mesma turma"""
        from transicao_ano_letivo import InterfaceTransicaoAnoLetivo
        
        mock_janela = MagicMock()
        
        with patch('transicao_ano_letivo.Frame'), \
             patch('transicao_ano_letivo.Label'), \
             patch('transicao_ano_letivo.LabelFrame'), \
             patch('transicao_ano_letivo.Button'), \
             patch('transicao_ano_letivo.ttk'), \
             patch.object(InterfaceTransicaoAnoLetivo, 'carregar_dados_iniciais'):
            
            app = InterfaceTransicaoAnoLetivo(mock_janela, mock_janela)
            
            resultado = app.obter_proxima_turma(10, reprovado=True)
            
            assert resultado == 10, "Reprovado deve permanecer na mesma turma"
    
    def test_obter_proxima_turma_sem_proxima(self):
        """Se não encontrar próxima turma, deve manter na mesma"""
        from transicao_ano_letivo import InterfaceTransicaoAnoLetivo
        
        mock_janela = MagicMock()
        
        with patch('transicao_ano_letivo.Frame'), \
             patch('transicao_ano_letivo.Label'), \
             patch('transicao_ano_letivo.LabelFrame'), \
             patch('transicao_ano_letivo.Button'), \
             patch('transicao_ano_letivo.ttk'), \
             patch.object(InterfaceTransicaoAnoLetivo, 'carregar_dados_iniciais'):
            
            app = InterfaceTransicaoAnoLetivo(mock_janela, mock_janela)
            app.escola_id = 60
            
            with patch('transicao_ano_letivo.QueriesTransicao.get_proxima_turma') as mock_query:
                mock_query.return_value = None  # Não encontrou próxima
                
                resultado = app.obter_proxima_turma(99, reprovado=False)
                
                assert resultado == 99, "Sem próxima turma deve manter na mesma"


class TestQueriesTransicao:
    """Testes do módulo de queries centralizadas"""
    
    def test_get_turmas_9ano(self):
        """Deve retornar lista de IDs das turmas do 9º ano"""
        from db.queries_transicao import QueriesTransicao
        
        with patch('db.queries_transicao.get_cursor') as mock_cursor:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_ctx.execute = MagicMock()
            mock_ctx.fetchall = MagicMock(return_value=[
                {'id': 10}, {'id': 11}, {'id': 12}
            ])
            mock_cursor.return_value = mock_ctx
            
            resultado = QueriesTransicao.get_turmas_9ano(60)
            
            assert resultado == [10, 11, 12]
    
    def test_get_turmas_9ano_vazio(self):
        """Deve retornar lista vazia se não houver turmas do 9º ano"""
        from db.queries_transicao import QueriesTransicao
        
        with patch('db.queries_transicao.get_cursor') as mock_cursor:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_ctx.fetchall = MagicMock(return_value=None)
            mock_cursor.return_value = mock_ctx
            
            resultado = QueriesTransicao.get_turmas_9ano(60)
            
            assert resultado == []
    
    def test_registrar_auditoria(self):
        """Deve registrar auditoria corretamente"""
        from db.queries_transicao import QueriesTransicao
        
        with patch('db.queries_transicao.get_cursor') as mock_cursor:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_cursor.return_value = mock_ctx
            
            resultado = QueriesTransicao.registrar_auditoria(
                ano_origem=2024,
                ano_destino=2025,
                escola_id=60,
                usuario='admin',
                matriculas_encerradas=100,
                matriculas_criadas=95,
                alunos_promovidos=90,
                alunos_retidos=5,
                alunos_concluintes=10,
                status='sucesso',
                detalhes='Transição completa'
            )
            
            assert resultado == True
            assert mock_ctx.execute.call_count >= 1  # Cria tabela + insere


class TestBackup:
    """Testes do sistema de backup"""
    
    def test_verificar_backup_recente_existe(self):
        """Deve retornar True se backup recente existe"""
        from transicao_ano_letivo import InterfaceTransicaoAnoLetivo
        from pathlib import Path
        
        mock_janela = MagicMock()
        
        with patch('transicao_ano_letivo.Frame'), \
             patch('transicao_ano_letivo.Label'), \
             patch('transicao_ano_letivo.LabelFrame'), \
             patch('transicao_ano_letivo.Button'), \
             patch('transicao_ano_letivo.ttk'), \
             patch.object(InterfaceTransicaoAnoLetivo, 'carregar_dados_iniciais'):
            
            app = InterfaceTransicaoAnoLetivo(mock_janela, mock_janela)
            
            # Mock do Path
            with patch.object(Path, 'exists', return_value=True), \
                 patch.object(Path, 'stat') as mock_stat:
                
                # Simular arquivo modificado há 1 hora
                mock_stat.return_value = MagicMock(
                    st_mtime=(datetime.now().timestamp() - 3600)
                )
                
                resultado = app.verificar_backup_recente()
                
                assert resultado == True
    
    def test_verificar_backup_recente_antigo(self):
        """Deve retornar False se backup é muito antigo (>24h)"""
        from transicao_ano_letivo import InterfaceTransicaoAnoLetivo
        from pathlib import Path
        
        mock_janela = MagicMock()
        
        with patch('transicao_ano_letivo.Frame'), \
             patch('transicao_ano_letivo.Label'), \
             patch('transicao_ano_letivo.LabelFrame'), \
             patch('transicao_ano_letivo.Button'), \
             patch('transicao_ano_letivo.ttk'), \
             patch.object(InterfaceTransicaoAnoLetivo, 'carregar_dados_iniciais'):
            
            app = InterfaceTransicaoAnoLetivo(mock_janela, mock_janela)
            
            with patch.object(Path, 'exists', return_value=True), \
                 patch.object(Path, 'stat') as mock_stat:
                
                # Simular arquivo modificado há 48 horas
                mock_stat.return_value = MagicMock(
                    st_mtime=(datetime.now().timestamp() - 48 * 3600)
                )
                
                resultado = app.verificar_backup_recente()
                
                assert resultado == False


class TestDryRun:
    """Testes do modo dry-run"""
    
    def test_dry_run_nao_altera_banco(self):
        """Modo dry-run não deve persistir alterações"""
        # Este teste verificaria que conn.rollback() é chamado
        # em vez de conn.commit() no modo dry-run
        from transicao_ano_letivo import InterfaceTransicaoAnoLetivo
        
        mock_janela = MagicMock()
        
        with patch('transicao_ano_letivo.Frame'), \
             patch('transicao_ano_letivo.Label'), \
             patch('transicao_ano_letivo.LabelFrame'), \
             patch('transicao_ano_letivo.Button'), \
             patch('transicao_ano_letivo.ttk'), \
             patch.object(InterfaceTransicaoAnoLetivo, 'carregar_dados_iniciais'):
            
            app = InterfaceTransicaoAnoLetivo(mock_janela, mock_janela)
            app._executando = False
            
            # O teste completo precisaria mockar a conexão do banco
            # Por ora, apenas verificamos que o parâmetro dry_run existe
            import inspect
            sig = inspect.signature(app.executar_transicao)
            assert 'dry_run' in sig.parameters


# Fixtures para configuração de testes
@pytest.fixture
def mock_janela():
    """Fixture que retorna uma janela Tkinter mockada"""
    mock = MagicMock()
    mock.title = MagicMock()
    mock.geometry = MagicMock()
    mock.resizable = MagicMock()
    mock.configure = MagicMock()
    mock.after = MagicMock()
    mock.update = MagicMock()
    return mock


@pytest.fixture
def app_transicao(mock_janela):
    """Fixture que retorna uma instância da interface mockada"""
    from transicao_ano_letivo import InterfaceTransicaoAnoLetivo
    
    with patch('transicao_ano_letivo.Frame'), \
         patch('transicao_ano_letivo.Label'), \
         patch('transicao_ano_letivo.LabelFrame'), \
         patch('transicao_ano_letivo.Button'), \
         patch('transicao_ano_letivo.ttk'), \
         patch.object(InterfaceTransicaoAnoLetivo, 'carregar_dados_iniciais'):
        
        app = InterfaceTransicaoAnoLetivo(mock_janela, mock_janela)
        app.escola_id = 60
        app.ano_atual = {'id': 1, 'ano_letivo': 2024, 'data_fim': date(2024, 12, 20)}
        app.ano_novo = {'ano_letivo': 2025}
        app.estatisticas = {
            'total_matriculas': 100,
            'alunos_continuar': 80,
            'alunos_reprovados': 10,
            'alunos_excluir': 5
        }
        return app


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
