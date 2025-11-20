"""
Testes unitários para ui.app.Application

Este módulo testa a classe Application que encapsula a lógica
da aplicação Tkinter, substituindo variáveis globais por atributos.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from ui.app import Application


@pytest.fixture
def mock_tk():
    """Fixture que mocka a classe Tk."""
    with patch('ui.app.Tk') as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield mock, instance


@pytest.fixture
def mock_get_connection():
    """Fixture que mocka get_connection."""
    with patch('ui.app.get_connection') as mock:
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = ("Escola Teste",)
        conn.cursor.return_value = cursor
        mock.return_value.__enter__.return_value = conn
        mock.return_value.__exit__.return_value = None
        yield mock


@pytest.fixture
def mock_pool():
    """Fixture que mocka inicializar_pool e fechar_pool."""
    with patch('ui.app.inicializar_pool') as mock_init:
        with patch('ui.app.fechar_pool') as mock_close:
            yield mock_init, mock_close


class TestApplicationInit:
    """Testes para inicialização da classe Application."""
    
    def test_init_initializes_state(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que __init__ inicializa o estado corretamente."""
        app = Application()
        
        assert app.selected_item is None
        assert app.query is None
        assert app.status_label is None
        assert app.label_rodape is None
        assert app.dashboard_manager is None
    
    def test_init_initializes_connection_pool(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que __init__ inicializa o pool de conexões."""
        mock_init, _ = mock_pool
        
        app = Application()
        
        mock_init.assert_called_once()
    
    def test_init_creates_window(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que __init__ cria a janela Tk."""
        mock_class, mock_instance = mock_tk
        
        app = Application()
        
        assert app.janela is not None
        mock_class.assert_called_once()
    
    def test_init_sets_window_title_from_db(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que o título da janela usa o nome da escola do banco."""
        _, mock_instance = mock_tk
        
        app = Application()
        
        mock_instance.title.assert_called_once_with("Sistema de Gerenciamento da Escola Teste")
    
    def test_init_sets_window_title_fallback_on_error(self, mock_tk, mock_pool):
        """Testa fallback do nome da escola quando há erro no banco."""
        _, mock_instance = mock_tk
        
        with patch('ui.app.get_connection', side_effect=Exception("DB Error")):
            app = Application()
        
        mock_instance.title.assert_called_once_with("Sistema de Gerenciamento da Escola")
    
    def test_init_configures_colors(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que as cores são configuradas corretamente."""
        app = Application()
        
        assert 'co0' in app.colors
        assert 'co1' in app.colors
        assert len(app.colors) == 10  # co0 a co9
        assert app.colors['co0'] == "#F5F5F5"
        assert app.colors['co1'] == "#003A70"


class TestApplicationSetup:
    """Testes para métodos de setup da Application."""
    
    def test_setup_frames_creates_frames_dict(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que setup_frames cria o dicionário de frames."""
        with patch('ui.frames.criar_frames') as mock_criar:
            mock_criar.return_value = {
                'logo': Mock(),
                'dados': Mock(),
                'detalhes': Mock(),
                'tabela': Mock()
            }
            
            app = Application()
            app.setup_frames()
            
            assert 'logo' in app.frames
            assert 'dados' in app.frames
            assert 'detalhes' in app.frames
            assert 'tabela' in app.frames
    
    def test_setup_logo_calls_criar_logo(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que setup_logo chama criar_logo com parâmetros corretos."""
        with patch('ui.frames.criar_logo') as mock_criar:
            app = Application()
            # Mock _get_school_name
            app._get_school_name = Mock(return_value="Escola Teste")
            app.frames = {'frame_logo': Mock()}
            
            app.setup_logo()
            
            mock_criar.assert_called_once()
            # Verificar argumentos keyword
            call_kwargs = mock_criar.call_args[1]
            assert 'frame_logo' in call_kwargs
            assert 'nome_escola' in call_kwargs
            assert call_kwargs['nome_escola'] == "Escola Teste"
            assert 'co0' in call_kwargs
            assert 'co1' in call_kwargs
            assert 'co7' in call_kwargs
    
    def test_setup_search_calls_criar_pesquisa(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que setup_search chama criar_pesquisa."""
        with patch('ui.frames.criar_pesquisa') as mock_criar:
            app = Application()
            app.frames = {'frame_dados': Mock()}
            callback = Mock()
            
            app.setup_search(callback)
            
            mock_criar.assert_called_once()
            # Verificar argumentos keyword
            call_kwargs = mock_criar.call_args[1]
            assert 'frame_dados' in call_kwargs
            assert 'pesquisar_callback' in call_kwargs
            assert call_kwargs['pesquisar_callback'] is callback
            assert 'co0' in call_kwargs
            assert 'co1' in call_kwargs
            assert 'co4' in call_kwargs
    
    def test_setup_footer_creates_labels(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que setup_footer cria e armazena os labels."""
        with patch('ui.frames.criar_rodape') as mock_criar:
            mock_label_rodape = Mock()
            mock_status_label = Mock()
            # criar_rodape retorna uma tupla (label_rodape, status_label)
            mock_criar.return_value = (mock_label_rodape, mock_status_label)
            
            app = Application()
            app.setup_footer()
            
            # Verificar que foi chamado com os argumentos corretos
            mock_criar.assert_called_once()
            call_kwargs = mock_criar.call_args[1]
            assert 'co0' in call_kwargs
            assert 'co1' in call_kwargs
            assert 'co2' in call_kwargs
            
            # Verificar que os labels foram armazenados
            assert app.label_rodape is mock_label_rodape
            assert app.status_label is mock_status_label


class TestApplicationMethods:
    """Testes para métodos utilitários da Application."""
    
    def test_update_status_updates_label(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que update_status atualiza o label de status."""
        app = Application()
        app.status_label = Mock()
        
        app.update_status("Teste de status")
        
        app.status_label.config.assert_called_once_with(text="Teste de status")
    
    def test_update_status_handles_no_label(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que update_status não falha se label não existe."""
        app = Application()
        app.status_label = None
        
        # Não deve lançar exceção
        app.update_status("Teste")
    
    def test_on_close_closes_pool(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que on_close fecha o connection pool."""
        _, mock_close = mock_pool
        _, mock_instance = mock_tk
        
        app = Application()
        app.on_close()
        
        mock_close.assert_called_once()
    
    def test_on_close_destroys_window(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que on_close destrói a janela."""
        _, mock_instance = mock_tk
        
        app = Application()
        app.on_close()
        
        mock_instance.destroy.assert_called_once()
    
    def test_run_configures_close_protocol(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que run configura o protocolo de fechamento."""
        _, mock_instance = mock_tk
        
        app = Application()
        
        # Mock mainloop para não bloquear o teste
        mock_instance.mainloop = Mock()
        
        app.run()
        
        mock_instance.protocol.assert_called_once_with("WM_DELETE_WINDOW", app.on_close)
    
    def test_run_starts_mainloop(self, mock_tk, mock_get_connection, mock_pool):
        """Testa que run inicia o mainloop."""
        _, mock_instance = mock_tk
        
        app = Application()
        app.run()
        
        mock_instance.mainloop.assert_called_once()


class TestApplicationIntegration:
    """Testes de integração para fluxo completo."""
    
    def test_full_setup_flow(self, mock_tk, mock_get_connection, mock_pool):
        """Testa o fluxo completo de setup da aplicação."""
        with patch('ui.frames.criar_frames') as mock_frames:
            with patch('ui.frames.criar_logo') as mock_logo:
                with patch('ui.frames.criar_pesquisa') as mock_pesquisa:
                    with patch('ui.frames.criar_rodape') as mock_rodape:
                        # Setup mocks
                        mock_frames.return_value = {
                            'frame_logo': Mock(),
                            'frame_dados': Mock(),
                            'frame_detalhes': Mock(),
                            'frame_tabela': Mock()
                        }
                        mock_rodape.return_value = (Mock(), Mock())  # tupla (label_rodape, status_label)
                        
                        # Criar app e configurar componentes
                        app = Application()
                        app._get_school_name = Mock(return_value="Escola Teste")
                        app.setup_frames()
                        app.setup_logo()
                        app.setup_search(Mock())
                        app.setup_footer()
                        
                        # Verificar que tudo foi chamado
                        mock_frames.assert_called_once()
                        mock_logo.assert_called_once()
                        mock_pesquisa.assert_called_once()
                        mock_rodape.assert_called_once()
                        
                        # Verificar estado final
                        assert app.frames is not None
                        assert app.label_rodape is not None
                        assert app.status_label is not None
