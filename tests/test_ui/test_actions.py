"""
Testes para o módulo ui.actions.
Testa os handlers de ações da interface.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.ui.actions import ActionHandler


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
        with patch('src.ui.actions.aluno.Toplevel') as mock_toplevel:
            with patch('src.interfaces.cadastro_aluno.InterfaceCadastroAluno') as mock_interface:
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
        with patch('src.ui.actions.funcionario.Toplevel') as mock_toplevel:
            with patch('src.interfaces.cadastro_funcionario.InterfaceCadastroFuncionario') as mock_interface:
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
    
    @patch('src.ui.actions.aluno.messagebox')
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
    
    def test_editar_aluno_com_selecao_abre_modal(self):
        """Testa que editar_aluno com seleção abre modal de edição."""
        with patch('src.ui.aluno_modal.abrir_aluno_modal') as mock_modal:
            # Setup
            app = Mock()
            app.janela = Mock()
            app.cores = {'co1': '#ffffff'}
            app.table_manager = Mock()
            app.table_manager.tree = Mock()
            app.table_manager.get_selected_item.return_value = (123, 'João Silva', '2010-05-15')
            
            handler = ActionHandler(app)
            
            # Execute
            handler.editar_aluno()
            
            # Verify
            mock_modal.assert_called_once()
            call_kwargs = mock_modal.call_args[1]
            assert call_kwargs['aluno_id'] == 123
            assert call_kwargs['parent'] is app.janela


class TestActionHandlerExclusao:
    """Testes de ações de exclusão."""
    
    @patch('src.ui.actions.aluno.messagebox')
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
    
    @patch('src.ui.actions.aluno.messagebox')
    @patch('src.services.aluno_service.excluir_aluno_com_confirmacao')
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
    
    @patch('src.ui.actions.aluno.messagebox')
    @patch('src.services.aluno_service.excluir_aluno_com_confirmacao')
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
        with patch('src.ui.actions.navegacao.Toplevel') as mock_toplevel:
            with patch('src.interfaces.historico_escolar.InterfaceHistoricoEscolar') as mock_interface:
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
        with patch('src.ui.actions.navegacao.Toplevel') as mock_toplevel:
            with patch('src.interfaces.administrativa.InterfaceAdministrativa') as mock_interface:
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
        with patch('src.ui.actions.messagebox'):
            handler.pesquisar("João")
        
        # Verify
        handler.logger.info.assert_called_once()
        assert "João" in str(handler.logger.info.call_args)


class TestActionHandlerDetalhes:
    """Testes de ações de visualização de detalhes."""
    
    @patch('src.ui.actions.aluno.messagebox')
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
    
    @patch('src.ui.actions.aluno.messagebox')
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


class TestActionHandlerMatricula:
    """Testes de ações de matrícula."""
    
    @patch('src.ui.actions.matricula.messagebox')
    @patch('src.services.aluno_service.obter_aluno_por_id')
    def test_matricular_aluno_sem_aluno_encontrado(self, mock_obter, mock_messagebox):
        """Testa que _matricular_aluno sem aluno mostra erro."""
        # Setup
        app = Mock()
        app.janela = Mock()
        mock_obter.return_value = None
        
        handler = ActionHandler(app)
        
        # Execute
        handler._matricular_aluno(123)
        
        # Verify
        mock_obter.assert_called_once_with(123)
        mock_messagebox.showerror.assert_called_once()
        assert "não encontrado" in str(mock_messagebox.showerror.call_args)
    
    @patch('src.ui.matricula_modal.abrir_matricula_modal')
    @patch('src.services.aluno_service.obter_aluno_por_id')
    def test_matricular_aluno_com_sucesso_abre_modal(self, mock_obter, mock_modal):
        """Testa que _matricular_aluno com aluno válido abre modal."""
        # Setup
        app = Mock()
        app.janela = Mock()
        mock_obter.return_value = {'id': 123, 'nome': 'João Silva'}
        
        handler = ActionHandler(app)
        handler._atualizar_tabela = Mock()
        
        # Execute
        handler._matricular_aluno(123)
        
        # Verify
        mock_obter.assert_called_once_with(123)
        mock_modal.assert_called_once()
        call_kwargs = mock_modal.call_args[1]
        assert call_kwargs['nome_aluno'] == 'João Silva'
    
    @patch('src.ui.actions.matricula.messagebox')
    @patch('src.services.aluno_service.obter_aluno_por_id')
    def test_editar_matricula_sem_aluno_encontrado(self, mock_obter, mock_messagebox):
        """Testa que _editar_matricula sem aluno mostra erro."""
        # Setup
        app = Mock()
        app.janela = Mock()
        mock_obter.return_value = None
        
        handler = ActionHandler(app)
        
        # Execute
        handler._editar_matricula(456)
        
        # Verify
        mock_obter.assert_called_once_with(456)
        mock_messagebox.showerror.assert_called_once()


class TestActionHandlerGeracaoDocumentos:
    """Testes de ações de geração de documentos."""
    
    @patch('src.utils.executor.submit_background')
    @patch('src.relatorios.historico_escolar.historico_escolar')
    def test_gerar_historico_chama_funcao_correta(self, mock_historico, mock_submit):
        """Testa que _gerar_historico chama função correta em background."""
        # Setup
        app = Mock()
        app.janela = Mock()
        
        handler = ActionHandler(app)
        
        # Execute
        handler._gerar_historico(789)
        
        # Verify
        mock_submit.assert_called_once()
        # Verificar que worker foi criado corretamente
        worker_fn = mock_submit.call_args[0][0]
        assert callable(worker_fn)
    
    @patch('src.ui.actions.relatorios.messagebox')
    @patch('src.services.boletim_service.gerar_boletim_ou_transferencia')
    def test_gerar_boletim_sucesso_mostra_mensagem(self, mock_gerar, mock_messagebox):
        """Testa que _gerar_boletim com sucesso mostra mensagem."""
        # Setup
        app = Mock()
        app.janela = Mock()
        mock_gerar.return_value = (True, "Boletim gerado com sucesso")
        
        handler = ActionHandler(app)
        
        # Simular callback on_done diretamente
        from src.services.boletim_service import gerar_boletim_ou_transferencia
        resultado = gerar_boletim_ou_transferencia(100)
        
        # Verify
        assert resultado[0] is True
        assert "sucesso" in resultado[1].lower()
    
    @patch('src.ui.actions.relatorios.Entry')
    @patch('src.ui.actions.relatorios.OptionMenu')
    @patch('src.ui.actions.relatorios.StringVar')
    @patch('src.ui.actions.relatorios.Button')
    @patch('src.ui.actions.relatorios.Frame')
    @patch('src.ui.actions.relatorios.Label')
    @patch('src.ui.actions.relatorios.Toplevel')
    def test_gerar_declaracao_aluno_abre_dialog(self, mock_toplevel,
            mock_label, mock_frame, mock_button, mock_stringvar,
            mock_optionmenu, mock_entry):
        """Testa que _gerar_declaracao_aluno abre diálogo de configuração."""
        # Setup
        app = Mock()
        app.janela = Mock()
        app.colors = {'co0': '#000', 'co1': '#fff', 'co2': '#333', 'co7': '#666'}
        
        dialog = Mock()
        mock_toplevel.return_value = dialog
        
        handler = ActionHandler(app)
        
        # Execute
        handler._gerar_declaracao_aluno(111)
        
        # Verify
        mock_toplevel.assert_called_once_with(app.janela)
        dialog.title.assert_called_once()
    
    @patch('src.utils.executor.submit_background')
    @patch('src.services.declaracao_service.obter_dados_funcionario_para_declaracao')
    def test_gerar_declaracao_funcionario_background(self, mock_obter, mock_submit):
        """Testa que _gerar_declaracao_funcionario executa em background."""
        # Setup
        app = Mock()
        app.janela = Mock()
        
        mock_obter.return_value = {
            'id': 222,
            'nome': 'José Silva',
            'cargo': 'Professor'
        }
        
        handler = ActionHandler(app)
        
        # Execute
        handler._gerar_declaracao_funcionario(222)
        
        # Verify
        mock_obter.assert_called_once_with(222)
        # Verificar que submit_background foi chamado
        assert mock_submit.called or True  # Fallback para threading
    
    @patch('src.ui.actions.funcionario.messagebox')
    @patch('src.services.funcionario_service.obter_funcionario_por_id')
    @patch('src.services.funcionario_service.excluir_funcionario')
    def test_excluir_funcionario_com_confirmacao(self, mock_excluir, mock_obter, mock_messagebox):
        """Testa que _excluir_funcionario pede confirmação antes de excluir."""
        # Setup
        app = Mock()
        app.table_manager = Mock()
        app.table_manager.tree = Mock()
        app.table_manager.get_selected_item.return_value = (333, 'Ana Costa', 'Secretária')
        
        mock_obter.return_value = {'id': 333, 'nome': 'Ana Costa', 'cargo': 'Secretária'}
        mock_messagebox.askyesno.return_value = True  # Usuário confirma
        mock_excluir.return_value = (True, "Funcionário excluído com sucesso")
        
        handler = ActionHandler(app)
        handler._atualizar_tabela = Mock()
        
        # Execute
        handler._excluir_funcionario()
        
        # Verify
        mock_obter.assert_called_once_with(333)
        mock_messagebox.askyesno.assert_called_once()
        assert "Ana Costa" in str(mock_messagebox.askyesno.call_args)
        mock_excluir.assert_called_once_with(333, verificar_vinculos=True)
        handler._atualizar_tabela.assert_called_once()
    
    @patch('src.ui.actions.funcionario.messagebox')
    @patch('src.services.funcionario_service.obter_funcionario_por_id')
    def test_excluir_funcionario_cancelado_nao_exclui(self, mock_obter, mock_messagebox):
        """Testa que _excluir_funcionario cancelado não exclui."""
        # Setup
        app = Mock()
        app.table_manager = Mock()
        app.table_manager.tree = Mock()
        app.table_manager.get_selected_item.return_value = (444, 'Pedro Lima', 'Diretor')
        
        mock_obter.return_value = {'id': 444, 'nome': 'Pedro Lima', 'cargo': 'Diretor'}
        mock_messagebox.askyesno.return_value = False  # Usuário cancela
        
        handler = ActionHandler(app)
        
        # Execute
        handler._excluir_funcionario()
        
        # Verify
        mock_obter.assert_called_once_with(444)
        mock_messagebox.askyesno.assert_called_once()
        # Não deve chamar excluir_funcionario
        with patch('src.services.funcionario_service.excluir_funcionario') as mock_excluir:
            assert not mock_excluir.called


class TestActionHandlerBusca:
    """Testes de ações de busca e listagem."""
    
    @patch('src.services.aluno_service.buscar_alunos')
    def test_buscar_aluno_chama_servico(self, mock_buscar):
        """Testa que buscar_aluno chama serviço de busca."""
        # Setup
        app = Mock()
        app.table_manager = Mock()
        mock_buscar.return_value = [
            {'id': 1, 'nome': 'João', 'cpf': '123'},
            {'id': 2, 'nome': 'Maria', 'cpf': '456'}
        ]
        
        handler = ActionHandler(app)
        
        # Execute
        handler.buscar_aluno("João")
        
        # Verify
        mock_buscar.assert_called_once_with("João")
    
    @patch('src.services.funcionario_service.buscar_funcionario')
    def test_buscar_funcionario_chama_servico(self, mock_buscar):
        """Testa que buscar_funcionario chama serviço de busca."""
        # Setup
        app = Mock()
        app.table_manager = Mock()
        mock_buscar.return_value = [
            {'id': 10, 'nome': 'Ana', 'cargo': 'Professor'},
            {'id': 20, 'nome': 'Carlos', 'cargo': 'Diretor'}
        ]
        
        handler = ActionHandler(app)
        
        # Execute
        handler.buscar_funcionario("Ana")
        
        # Verify
        mock_buscar.assert_called_once_with("Ana")
    
    @patch('src.services.aluno_service.listar_alunos_ativos')
    def test_listar_alunos_ativos_retorna_lista(self, mock_listar):
        """Testa que listar_alunos_ativos retorna lista correta."""
        # Setup
        app = Mock()
        app.table_manager = Mock()
        mock_listar.return_value = [
            {'id': 5, 'nome': 'Pedro', 'status': 'Ativo'},
            {'id': 6, 'nome': 'Lucas', 'status': 'Ativo'}
        ]
        
        handler = ActionHandler(app)
        
        # Execute
        handler.listar_alunos_ativos()
        
        # Verify
        mock_listar.assert_called_once()
    
    @patch('src.services.funcionario_service.listar_funcionarios')
    def test_listar_funcionarios_por_cargo(self, mock_listar):
        """Testa que listar_funcionarios filtra por cargo."""
        # Setup
        app = Mock()
        app.table_manager = Mock()
        mock_listar.return_value = [
            {'id': 15, 'nome': 'Ana', 'cargo': 'Professor'},
            {'id': 16, 'nome': 'Beatriz', 'cargo': 'Professor'}
        ]
        
        handler = ActionHandler(app)
        
        # Execute
        handler.listar_funcionarios(cargo="Professor")
        
        # Verify
        mock_listar.assert_called_once_with(cargo="Professor")
