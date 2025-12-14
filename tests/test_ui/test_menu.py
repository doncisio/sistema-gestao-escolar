"""
Testes para o módulo ui.menu.
Testa o gerenciador de menus e suas funcionalidades.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.ui.menu import MenuManager


class TestMenuManagerInit:
    """Testes de inicialização do MenuManager."""
    
    def test_init_stores_parameters(self):
        """Testa que __init__ armazena parâmetros corretamente."""
        janela = Mock()
        action_handler = Mock()
        
        manager = MenuManager(janela, action_handler)
        
        assert manager.janela is janela
        assert manager.action_handler is action_handler
        assert manager.menu_contextual is None
        assert manager.logger is not None


class TestMenuManagerContextual:
    """Testes de criação de menu contextual."""
    
    @patch('ui.menu.Menu')
    def test_criar_menu_contextual_com_callbacks(self, mock_menu):
        """Testa criação de menu contextual com callbacks fornecidos."""
        # Setup
        janela = Mock()
        treeview = Mock()
        action_handler = Mock()
        action_handler.editar_aluno = Mock()
        action_handler.excluir_aluno = Mock()
        
        menu_instance = Mock()
        mock_menu.return_value = menu_instance
        
        manager = MenuManager(janela, action_handler)
        
        # Execute
        result = manager.criar_menu_contextual(treeview)
        
        # Verify
        mock_menu.assert_called_once_with(janela, tearoff=0)
        assert menu_instance.add_command.call_count >= 2  # Pelo menos editar e excluir
        assert treeview.bind.called
        assert result is menu_instance
    
    @patch('ui.menu.Menu')
    def test_criar_menu_contextual_sem_action_handler(self, mock_menu):
        """Testa criação de menu contextual sem action_handler."""
        # Setup
        janela = Mock()
        treeview = Mock()
        
        menu_instance = Mock()
        mock_menu.return_value = menu_instance
        
        manager = MenuManager(janela, action_handler=None)
        
        # Execute
        result = manager.criar_menu_contextual(treeview)
        
        # Verify - deve criar menu mas sem adicionar comandos (callbacks None)
        mock_menu.assert_called_once_with(janela, tearoff=0)
        assert result is menu_instance
    
    @patch('ui.menu.Menu')
    def test_criar_menu_contextual_com_callbacks_customizados(self, mock_menu):
        """Testa criação de menu com callbacks customizados."""
        # Setup
        janela = Mock()
        treeview = Mock()
        custom_editar = Mock()
        custom_excluir = Mock()
        
        callbacks = {
            'editar': custom_editar,
            'excluir': custom_excluir
        }
        
        menu_instance = Mock()
        mock_menu.return_value = menu_instance
        
        manager = MenuManager(janela)
        
        # Execute
        result = manager.criar_menu_contextual(treeview, callbacks)
        
        # Verify
        assert result is menu_instance


class TestMenuManagerRelatorios:
    """Testes de criação de menu de relatórios."""
    
    @patch('ui.menu.Menu')
    def test_criar_menu_relatorios_completo(self, mock_menu):
        """Testa criação de menu de relatórios com todos callbacks."""
        # Setup
        janela = Mock()
        parent = Mock()
        
        callbacks = {
            'lista_alfabetica': Mock(),
            'lista_frequencia': Mock(),
            'lista_reuniao': Mock(),
            'boletim_bimestral': Mock(),
            'ata_1a5': Mock(),
            'ata_6a9': Mock()
        }
        
        menu_instance = Mock()
        submenu_listas = Mock()
        submenu_boletins = Mock()
        submenu_atas = Mock()
        
        mock_menu.side_effect = [menu_instance, submenu_listas, submenu_boletins, submenu_atas]
        
        manager = MenuManager(janela)
        
        # Execute
        result = manager.criar_menu_relatorios(parent, callbacks)
        
        # Verify
        assert result is menu_instance
        assert menu_instance.add_cascade.call_count == 3  # Listas, Boletins, Atas
    
    @patch('ui.menu.Menu')
    def test_criar_menu_relatorios_sem_callbacks(self, mock_menu):
        """Testa criação de menu de relatórios sem callbacks."""
        # Setup
        janela = Mock()
        parent = Mock()
        
        menu_instance = Mock()
        mock_menu.return_value = menu_instance
        
        manager = MenuManager(janela)
        
        # Execute
        result = manager.criar_menu_relatorios(parent, None)
        
        # Verify
        assert result is menu_instance


class TestMenuManagerDeclaracoes:
    """Testes de criação de menu de declarações."""
    
    @patch('ui.menu.Menu')
    def test_criar_menu_declaracoes_completo(self, mock_menu):
        """Testa criação de menu de declarações com callbacks."""
        # Setup
        janela = Mock()
        parent = Mock()
        
        callbacks = {
            'declaracao_aluno': Mock(),
            'declaracao_funcionario': Mock(),
            'declaracao_comparecimento': Mock()
        }
        
        menu_instance = Mock()
        mock_menu.return_value = menu_instance
        
        manager = MenuManager(janela)
        
        # Execute
        result = manager.criar_menu_declaracoes(parent, callbacks)
        
        # Verify
        assert result is menu_instance
        assert menu_instance.add_command.call_count == 3


class TestMenuManagerMeses:
    """Testes de criação de menu de meses."""
    
    @patch('utils.dates.nome_mes_pt')
    @patch('ui.menu.Menu')
    def test_criar_menu_meses_cria_12_itens(self, mock_menu, mock_nome_mes):
        """Testa que menu de meses cria 12 itens (janeiro a dezembro)."""
        # Setup
        janela = Mock()
        callback = Mock()
        
        menu_instance = Mock()
        mock_menu.return_value = menu_instance
        mock_nome_mes.side_effect = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        
        manager = MenuManager(janela)
        
        # Execute
        result = manager.criar_menu_meses(callback)
        
        # Verify
        assert result is menu_instance
        assert menu_instance.add_command.call_count == 12
        assert mock_nome_mes.call_count == 12


class TestMenuManagerAnexar:
    """Testes de anexar menu a botão."""
    
    def test_anexar_menu_a_botao_configura_command(self):
        """Testa que anexar_menu_a_botao configura o botão corretamente."""
        # Setup
        janela = Mock()
        botao = Mock()
        botao.winfo_rootx = Mock(return_value=100)
        botao.winfo_rooty = Mock(return_value=200)
        botao.winfo_height = Mock(return_value=30)
        
        menu = Mock()
        
        manager = MenuManager(janela)
        
        # Execute
        manager.anexar_menu_a_botao(botao, menu)
        
        # Verify
        botao.config.assert_called_once()
        assert 'command' in botao.config.call_args[1]


class TestMenuManagerErrorHandling:
    """Testes de tratamento de erros."""
    
    @patch('ui.menu.Menu')
    def test_criar_menu_contextual_com_erro_retorna_none(self, mock_menu):
        """Testa que erro na criação retorna None."""
        # Setup
        janela = Mock()
        treeview = Mock()
        
        mock_menu.side_effect = Exception("Erro de teste")
        
        manager = MenuManager(janela)
        
        # Execute
        result = manager.criar_menu_contextual(treeview)
        
        # Verify
        assert result is None
    
    @patch('ui.menu.Menu')
    def test_criar_menu_relatorios_com_erro_retorna_none(self, mock_menu):
        """Testa que erro na criação de relatórios retorna None."""
        # Setup
        janela = Mock()
        parent = Mock()
        
        mock_menu.side_effect = Exception("Erro de teste")
        
        manager = MenuManager(janela)
        
        # Execute
        result = manager.criar_menu_relatorios(parent)
        
        # Verify
        assert result is None
