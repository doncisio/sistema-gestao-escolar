"""
Testes para o módulo ui.actions.
Testa os handlers de ações da interface.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ui.actions import ActionHandler


class TestActionHandlerInit:
    """Testes de inicialização do ActionHandler."""
    
    def test_init_stores_app_reference(self):
        """Testa que __init__ armazena referência da aplicação."""
        app = Mock()
        handler = ActionHandler(app)
        
        assert handler.app is app
        assert handler.logger is not None


class TestActionHandlerCadastro:
    """Testes de ações de cadastro."""
    
    def test_cadastrar_novo_aluno_abre_janela(self):
        """Testa que cadastrar_novo_aluno abre janela de cadastro."""
        with patch('ui.actions.Toplevel') as mock_toplevel:
            with patch('InterfaceCadastroAluno.InterfaceCadastroAluno') as mock_interface:
                # Setup
                app = Mock()
                app.janela = Mock()
                app.colors = {'co1': '#ffffff'}
                app.table_manager = Mock()
                
                janela_cadastro = Mock()
                mock_toplevel.return_value = janela_cadastro
                
                handler = ActionHandler(app)
                
                # Execute
                handler.cadastrar_novo_aluno()
                
                # Verify
                mock_toplevel.assert_called_once_with(app.janela)
                janela_cadastro.title.assert_called_once_with("Cadastrar Novo Aluno")
                janela_cadastro.geometry.assert_called_once_with('950x670')
                janela_cadastro.configure.assert_called_once_with(background='#ffffff')
                app.janela.withdraw.assert_called_once()
                mock_interface.assert_called_once()
    
    def test_cadastrar_novo_funcionario_abre_janela(self):
        """Testa que cadastrar_novo_funcionario abre janela de cadastro."""
        with patch('ui.actions.Toplevel') as mock_toplevel:
            with patch('InterfaceCadastroFuncionario.InterfaceCadastroFuncionario') as mock_interface:
                # Setup
                app = Mock()
                app.janela = Mock()
                app.colors = {'co1': '#ffffff'}
                app.table_manager = Mock()
                
                janela_cadastro = Mock()
                mock_toplevel.return_value = janela_cadastro
                
                handler = ActionHandler(app)
                
                # Execute
                handler.cadastrar_novo_funcionario()
                
                # Verify
                mock_toplevel.assert_called_once_with(app.janela)
                janela_cadastro.title.assert_called_once_with("Cadastrar Novo Funcionário")
                app.janela.withdraw.assert_called_once()


class TestActionHandlerEdicao:
    """Testes de ações de edição."""
    
    @patch('ui.actions.messagebox')
    def test_editar_aluno_sem_selecao_mostra_aviso(self, mock_messagebox):
        """Testa que editar_aluno sem seleção mostra aviso."""
        # Setup
        app = Mock()
        app.table_manager = Mock()
        app.table_manager.tree = Mock()
        app.table_manager.get_selected_item.return_value = None
        
        handler = ActionHandler(app)
        
        # Execute
        handler.editar_aluno()
        
        # Verify
        mock_messagebox.showwarning.assert_called_once_with(
            "Aviso", 
            "Selecione um aluno para editar"
        )
    
    def test_editar_aluno_com_selecao_abre_janela(self):
        """Testa que editar_aluno com seleção abre janela de edição."""
        with patch('ui.actions.messagebox'):
            with patch('ui.actions.Toplevel') as mock_toplevel:
                with patch('InterfaceEdicaoAluno.InterfaceEdicaoAluno') as mock_interface:
                    # Setup
                    app = Mock()
                    app.janela = Mock()
                    app.colors = {'co1': '#ffffff'}
                    app.table_manager = Mock()
                    app.table_manager.tree = Mock()
                    app.table_manager.get_selected_item.return_value = (123, 'João Silva', '2010-05-15')
                    
                    janela_edicao = Mock()
                    mock_toplevel.return_value = janela_edicao
                    
                    handler = ActionHandler(app)
                    
                    # Execute
                    handler.editar_aluno()
                    
                    # Verify
                    mock_toplevel.assert_called_once_with(app.janela)
                    janela_edicao.title.assert_called_once_with("Editar Aluno - ID: 123")
                    app.janela.withdraw.assert_called_once()
                    mock_interface.assert_called_once()


class TestActionHandlerExclusao:
    """Testes de ações de exclusão."""
    
    @patch('ui.actions.messagebox')
    def test_excluir_aluno_sem_selecao_mostra_aviso(self, mock_messagebox):
        """Testa que excluir_aluno sem seleção mostra aviso."""
        # Setup
        app = Mock()
        app.table_manager = Mock()
        app.table_manager.tree = Mock()
        app.table_manager.get_selected_item.return_value = None
        
        handler = ActionHandler(app)
        
        # Execute
        handler.excluir_aluno()
        
        # Verify
        mock_messagebox.showwarning.assert_called_once_with(
            "Aviso",
            "Selecione um aluno para excluir"
        )
    
    @patch('ui.actions.messagebox')
    @patch('services.aluno_service.excluir_aluno_com_confirmacao')
    def test_excluir_aluno_com_selecao_chama_servico(self, mock_excluir, mock_messagebox):
        """Testa que excluir_aluno com seleção chama serviço de exclusão."""
        # Setup
        app = Mock()
        app.table_manager = Mock()
        app.table_manager.tree = Mock()
        app.table_manager.get_selected_item.return_value = (456, 'Maria Santos', '2012-03-20')
        
        mock_excluir.return_value = True
        
        handler = ActionHandler(app)
        
        # Execute
        handler.excluir_aluno()
        
        # Verify
        mock_excluir.assert_called_once()
        call_args = mock_excluir.call_args
        assert call_args[0][0] == 456  # aluno_id
        assert call_args[0][1] == 'Maria Santos'  # nome_aluno
    
    @patch('ui.actions.messagebox')
    @patch('services.aluno_service.excluir_aluno_com_confirmacao')
    def test_excluir_aluno_sucesso_atualiza_tabela(self, mock_excluir, mock_messagebox):
        """Testa que exclusão bem-sucedida atualiza a tabela."""
        # Setup
        app = Mock()
        app.table_manager = Mock()
        app.table_manager.tree = Mock()
        app.table_manager.get_selected_item.return_value = (789, 'José Silva', '2011-08-10')
        
        mock_excluir.return_value = True
        
        handler = ActionHandler(app)
        handler._atualizar_tabela = Mock()
        
        # Execute
        handler.excluir_aluno()
        
        # Verify
        handler._atualizar_tabela.assert_called_once()


class TestActionHandlerNavigacao:
    """Testes de ações de navegação."""
    
    def test_abrir_historico_escolar_abre_janela(self):
        """Testa que abrir_historico_escolar abre a interface correta."""
        with patch('ui.actions.Toplevel') as mock_toplevel:
            with patch('interface_historico_otimizada.InterfaceHistoricoOtimizada') as mock_interface:
                # Setup
                app = Mock()
                app.janela = Mock()
                app.colors = {'co1': '#ffffff'}
                
                janela_historico = Mock()
                mock_toplevel.return_value = janela_historico
                
                handler = ActionHandler(app)
                
                # Execute
                handler.abrir_historico_escolar()
                
                # Verify
                mock_toplevel.assert_called_once_with(app.janela)
                janela_historico.title.assert_called_once_with("Histórico Escolar")
                janela_historico.geometry.assert_called_once_with('1200x700')
                app.janela.withdraw.assert_called_once()
    
    def test_abrir_interface_administrativa_abre_janela(self):
        """Testa que abrir_interface_administrativa abre a interface correta."""
        with patch('ui.actions.Toplevel') as mock_toplevel:
            with patch('interface_administrativa.InterfaceAdministrativa') as mock_interface:
                # Setup
                app = Mock()
                app.janela = Mock()
                app.colors = {'co1': '#ffffff'}
                
                janela_admin = Mock()
                mock_toplevel.return_value = janela_admin
                
                handler = ActionHandler(app)
                
                # Execute
                handler.abrir_interface_administrativa()
                
                # Verify
                mock_toplevel.assert_called_once_with(app.janela)
                janela_admin.title.assert_called_once_with("Administração do Sistema")
                janela_admin.geometry.assert_called_once_with('1000x600')
                app.janela.withdraw.assert_called_once()


class TestActionHandlerPesquisa:
    """Testes de ações de pesquisa."""
    
    def test_pesquisar_termo_vazio_atualiza_tabela(self):
        """Testa que pesquisa com termo vazio atualiza para mostrar todos."""
        # Setup
        app = Mock()
        app.table_manager = Mock()
        
        handler = ActionHandler(app)
        handler._atualizar_tabela = Mock()
        
        # Execute
        handler.pesquisar("")
        
        # Verify
        handler._atualizar_tabela.assert_called_once()
    
    def test_pesquisar_termo_valido_registra_log(self):
        """Testa que pesquisa com termo válido registra no log."""
        # Setup
        app = Mock()
        app.table_manager = Mock()
        
        handler = ActionHandler(app)
        handler.logger = Mock()
        
        # Execute
        with patch('ui.actions.messagebox'):
            handler.pesquisar("João")
        
        # Verify
        handler.logger.info.assert_called_once()
        assert "João" in str(handler.logger.info.call_args)


class TestActionHandlerDetalhes:
    """Testes de ações de visualização de detalhes."""
    
    @patch('ui.actions.messagebox')
    def test_ver_detalhes_sem_selecao_mostra_aviso(self, mock_messagebox):
        """Testa que ver_detalhes_aluno sem seleção mostra aviso."""
        # Setup
        app = Mock()
        app.table_manager = Mock()
        app.table_manager.tree = Mock()
        app.table_manager.get_selected_item.return_value = None
        
        handler = ActionHandler(app)
        
        # Execute
        handler.ver_detalhes_aluno()
        
        # Verify
        mock_messagebox.showwarning.assert_called_once_with(
            "Aviso",
            "Selecione um aluno para ver detalhes"
        )
    
    @patch('ui.actions.messagebox')
    def test_ver_detalhes_com_selecao_registra_log(self, mock_messagebox):
        """Testa que ver_detalhes_aluno com seleção registra no log."""
        # Setup
        app = Mock()
        app.table_manager = Mock()
        app.table_manager.tree = Mock()
        app.table_manager.get_selected_item.return_value = (999, 'Carlos Souza', '2013-12-05')
        
        handler = ActionHandler(app)
        handler.logger = Mock()
        
        # Execute
        handler.ver_detalhes_aluno()
        
        # Verify
        handler.logger.info.assert_called_once()
        assert "999" in str(handler.logger.info.call_args)
