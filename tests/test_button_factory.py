"""
Testes para ButtonFactory (Sprint 17)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from ui.button_factory import ButtonFactory


class TestButtonFactory:
    """Testes para a classe ButtonFactory"""
    
    @pytest.fixture
    def mock_janela(self):
        """Mock da janela Tk"""
        janela = Mock()
        janela.config = Mock()
        return janela
    
    @pytest.fixture
    def mock_frame_dados(self):
        """Mock do frame de dados"""
        frame = Mock()
        return frame
    
    @pytest.fixture
    def mock_callbacks(self):
        """Mock do ActionCallbacksManager"""
        callbacks = Mock()
        callbacks.cadastrar_novo_aluno = Mock()
        callbacks.cadastrar_novo_funcionario = Mock()
        callbacks.abrir_historico_escolar = Mock()
        callbacks.abrir_interface_administrativa = Mock()
        callbacks.abrir_horarios_escolares = Mock()
        callbacks.lista_atualizada = Mock()
        callbacks.lista_reuniao = Mock()
        callbacks.lista_notas = Mock()
        callbacks.abrir_cadastro_notas = Mock()
        callbacks.relatorio_contatos_responsaveis = Mock()
        
        # Reports submock
        callbacks.reports = Mock()
        callbacks.reports.lista_frequencia = Mock()
        callbacks.reports.relatorio_lista_alfabetica = Mock()
        callbacks.reports.relatorio_alunos_transtornos = Mock()
        
        # Declaracao submock
        callbacks.declaracao = Mock()
        
        # Administrativo submock
        callbacks.abrir_transicao_ano_letivo = Mock()
        callbacks.abrir_gerenciador_documentos = Mock()
        callbacks.abrir_gerenciador_licencas = Mock()
        
        return callbacks
    
    @pytest.fixture
    def colors(self):
        """Dicionário de cores"""
        return {
            'co0': '#F5F5F5',
            'co1': '#003A70',
            'co2': '#77B341',
            'co3': '#E2418E',
            'co4': '#4A86E8',
            'co5': '#F26A25',
            'co6': '#F7B731',
            'co7': '#333333',
            'co8': '#BF3036',
            'co9': '#6FA8DC'
        }
    
    @pytest.fixture
    def button_factory(self, mock_janela, mock_frame_dados, mock_callbacks, colors):
        """Fixture do ButtonFactory"""
        return ButtonFactory(
            janela=mock_janela,
            frame_dados=mock_frame_dados,
            callbacks=mock_callbacks,
            colors=colors
        )
    
    def test_init(self, button_factory, mock_janela, mock_frame_dados, mock_callbacks, colors):
        """Testa inicialização do ButtonFactory"""
        assert button_factory.janela == mock_janela
        assert button_factory.frame_dados == mock_frame_dados
        assert button_factory.callbacks == mock_callbacks
        assert button_factory.colors == colors
        assert isinstance(button_factory._image_refs, dict)
        assert len(button_factory._image_refs) == 0
    
    def test_load_image_success(self, button_factory):
        """Testa carregamento de imagem com sucesso"""
        with patch('ui.button_factory.Image.open') as mock_open:
            mock_img = Mock()
            mock_img.resize = Mock(return_value=mock_img)
            mock_open.return_value = mock_img
            
            with patch('ui.button_factory.ImageTk.PhotoImage') as mock_photo:
                mock_photo_instance = Mock()
                mock_photo.return_value = mock_photo_instance
                
                result = button_factory._load_image('test.png')
                
                assert result == mock_photo_instance
                assert 'test.png' in button_factory._image_refs
    
    def test_load_image_not_found(self, button_factory):
        """Testa carregamento de imagem inexistente"""
        result = button_factory._load_image('nonexistent.png')
        assert result is None
        assert 'nonexistent.png' not in button_factory._image_refs
    
    @patch('ui.button_factory.Button')
    def test_create_button_without_icon(self, mock_button_class, button_factory):
        """Testa criação de botão sem ícone"""
        parent = Mock()
        callback = Mock()
        
        mock_button_instance = Mock()
        mock_button_class.return_value = mock_button_instance
        
        result = button_factory._create_button(
            parent=parent,
            text="Test Button",
            command=callback,
            bg_color='#FF0000'
        )
        
        assert result == mock_button_instance
        mock_button_class.assert_called_once()
        call_kwargs = mock_button_class.call_args[1]
        assert call_kwargs['text'] == "Test Button"
        assert call_kwargs['command'] == callback
        assert call_kwargs['bg'] == '#FF0000'
    
    @patch('ui.button_factory.Frame')
    def test_criar_botoes_principais(self, mock_frame_class, button_factory):
        """Testa criação dos botões principais"""
        mock_frame_instance = Mock()
        mock_frame_class.return_value = mock_frame_instance
        
        with patch.object(button_factory, '_create_button') as mock_create_button:
            mock_button = Mock()
            mock_create_button.return_value = mock_button
            
            result = button_factory.criar_botoes_principais()
            
            # Deve criar frame
            mock_frame_class.assert_called_once()
            
            # Deve criar 7 botões
            assert mock_create_button.call_count == 7
            
            # Verificar que callbacks corretos foram passados
            calls = mock_create_button.call_args_list
            assert calls[0][1]['command'] == button_factory.callbacks.cadastrar_novo_aluno
            assert calls[1][1]['command'] == button_factory.callbacks.cadastrar_novo_funcionario
            assert calls[2][1]['command'] == button_factory.callbacks.abrir_historico_escolar
            assert calls[3][1]['command'] == button_factory.callbacks.abrir_interface_administrativa
            
            assert result == mock_frame_instance
    
    @patch('ui.button_factory.Menu')
    def test_criar_menu_bar(self, mock_menu_class, button_factory):
        """Testa criação da barra de menus"""
        mock_menu = Mock()
        mock_menu_class.return_value = mock_menu
        
        result = button_factory.criar_menu_bar()
        
        # Deve criar menu bar
        assert mock_menu_class.call_count >= 1
        
        # Deve adicionar cascades (menus principais)
        assert mock_menu.add_cascade.call_count >= 6  # 6 menus principais
        
        assert result == mock_menu
    
    def test_fazer_backup(self, button_factory):
        """Testa callback de backup"""
        with patch('ui.button_factory.Seguranca') as mock_seguranca:
            mock_seguranca.fazer_backup = Mock()
            
            button_factory._fazer_backup()
            
            mock_seguranca.fazer_backup.assert_called_once()
    
    def test_restaurar_backup(self, button_factory):
        """Testa callback de restaurar backup"""
        with patch('ui.button_factory.Seguranca') as mock_seguranca:
            mock_seguranca.restaurar_backup = Mock()
            
            button_factory._restaurar_backup()
            
            mock_seguranca.restaurar_backup.assert_called_once()
    
    @patch('ui.button_factory.Menu')
    def test_configurar_interface(self, mock_menu_class, button_factory):
        """Testa configuração completa da interface"""
        mock_menu = Mock()
        mock_menu_class.return_value = mock_menu
        
        with patch.object(button_factory, 'criar_botoes_principais') as mock_botoes:
            with patch.object(button_factory, 'criar_menu_bar') as mock_menu_bar:
                mock_menu_bar.return_value = mock_menu
                
                button_factory.configurar_interface()
                
                # Deve criar botões
                mock_botoes.assert_called_once()
                
                # Deve criar menu bar
                mock_menu_bar.assert_called_once()
                
                # Deve configurar menu na janela
                button_factory.janela.config.assert_called_once_with(menu=mock_menu)


class TestButtonFactoryIntegration:
    """Testes de integração para ButtonFactory"""
    
    def test_full_initialization_flow(self):
        """Testa fluxo completo de inicialização"""
        mock_janela = Mock()
        mock_janela.config = Mock()
        mock_frame = Mock()
        mock_callbacks = Mock()
        
        # Configurar todos os callbacks necessários
        for attr in ['cadastrar_novo_aluno', 'cadastrar_novo_funcionario',
                     'abrir_historico_escolar', 'abrir_interface_administrativa',
                     'abrir_horarios_escolares', 'abrir_transicao_ano_letivo',
                     'abrir_gerenciador_documentos', 'abrir_gerenciador_licencas',
                     'lista_atualizada', 'lista_reuniao', 'lista_notas',
                     'abrir_cadastro_notas', 'relatorio_contatos_responsaveis']:
            setattr(mock_callbacks, attr, Mock())
        
        mock_callbacks.reports = Mock()
        mock_callbacks.declaracao = Mock()
        
        colors = {'co0': '#FFF', 'co1': '#000', 'co2': '#0F0', 'co3': '#00F',
                  'co4': '#F00', 'co5': '#FF0', 'co6': '#0FF', 'co7': '#F0F',
                  'co8': '#888', 'co9': '#CCC'}
        
        factory = ButtonFactory(
            janela=mock_janela,
            frame_dados=mock_frame,
            callbacks=mock_callbacks,
            colors=colors
        )
        
        assert factory is not None
        assert factory.janela == mock_janela
        assert len(factory._image_refs) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
