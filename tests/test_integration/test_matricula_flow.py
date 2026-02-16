"""
Testes de integração para o fluxo completo de matrícula.
Testa a integração entre ActionHandler, MatriculaModal e matricula_service.
"""
import pytest
import tkinter as tk
from tkinter import ttk
from unittest.mock import Mock, patch, MagicMock
from src.ui.actions import ActionHandler
from src.ui.matricula_modal import MatriculaModal, abrir_matricula_modal


@pytest.fixture
def root():
    """Fixture para criar janela Tk de teste."""
    root = tk.Tk()
    yield root
    root.destroy()


@pytest.fixture
def mock_app(root):
    """Fixture para criar mock da Application."""
    app = Mock()
    app.janela = root
    app.cores = {
        'co0': '#FFFFFF', 'co1': '#000000', 'co2': '#4080BF',
        'co3': '#38576b', 'co4': '#403d3d', 'co5': '#e06636',
        'co6': '#038cfc', 'co7': '#3fbfb9', 'co8': '#263238',
        'co9': '#e9edf5'
    }
    app.table_manager = Mock()
    app.table_manager.tree = ttk.Treeview(root)
    app.update_status = Mock()
    return app


class TestMatriculaIntegrationFlow:
    """Testes de integração para fluxo de matrícula."""
    
    @patch('src.ui.matricula_modal.obter_ano_letivo_atual')
    @patch('src.ui.matricula_modal.verificar_matricula_existente')
    @patch('src.ui.matricula_modal.obter_series_disponiveis')
    def test_abrir_modal_matricula_com_sucesso(
        self, mock_series, mock_verificar, mock_ano, root, mock_app
    ):
        """Testa abertura do modal de matrícula com dados válidos."""
        # Arrange
        mock_ano.return_value = (True, {'id': 1, 'ano': 2025})
        mock_verificar.return_value = (False, None)  # Sem matrícula ativa
        mock_series.return_value = (True, [
            {'id': 1, 'nome': '1º Ano'},
            {'id': 2, 'nome': '2º Ano'}
        ])
        
        # Act
        modal = MatriculaModal(
            parent=root,
            aluno_id=123,
            nome_aluno="João Silva",
            colors=mock_app.cores
        )
        
        # Assert
        assert modal.aluno_id == 123
        assert modal.nome_aluno == "João Silva"
        mock_ano.assert_called_once()
        mock_verificar.assert_called_once_with(123, 1)
        mock_series.assert_called_once()
    
    @patch('src.ui.matricula_modal.obter_ano_letivo_atual')
    def test_modal_falha_sem_ano_letivo(self, mock_ano, root, mock_app):
        """Testa que modal não abre se não há ano letivo configurado."""
        # Arrange
        mock_ano.return_value = (False, "Nenhum ano letivo configurado")
        
        # Act & Assert
        with patch('tkinter.messagebox.showerror') as mock_error:
            modal = MatriculaModal(
                parent=root,
                aluno_id=123,
                nome_aluno="João Silva",
                colors=mock_app.cores
            )
            mock_error.assert_called_once()
    
    @patch('src.ui.matricula_modal.obter_ano_letivo_atual')
    @patch('src.ui.matricula_modal.verificar_matricula_existente')
    def test_modal_alerta_matricula_existente(
        self, mock_verificar, mock_ano, root, mock_app
    ):
        """Testa que modal alerta quando aluno já tem matrícula ativa."""
        # Arrange
        mock_ano.return_value = (True, {'id': 1, 'ano': 2025})
        mock_verificar.return_value = (True, {'turma': '1º Ano A', 'status': 'Ativo'})
        
        # Act & Assert
        with patch('tkinter.messagebox.showwarning') as mock_warning:
            modal = MatriculaModal(
                parent=root,
                aluno_id=123,
                nome_aluno="João Silva",
                colors=mock_app.cores
            )
            mock_warning.assert_called_once()
    
    @patch('src.ui.matricula_modal.obter_ano_letivo_atual')
    @patch('src.ui.matricula_modal.verificar_matricula_existente')
    @patch('src.ui.matricula_modal.obter_series_disponiveis')
    @patch('src.ui.matricula_modal.obter_turmas_por_serie')
    def test_atualizar_turmas_ao_selecionar_serie(
        self, mock_turmas, mock_series, mock_verificar, mock_ano, root, mock_app
    ):
        """Testa que turmas são carregadas ao selecionar série."""
        # Arrange
        mock_ano.return_value = (True, {'id': 1, 'ano': 2025})
        mock_verificar.return_value = (False, None)
        mock_series.return_value = (True, [{'id': 1, 'nome': '1º Ano'}])
        mock_turmas.return_value = (True, [
            {'id': 10, 'nome': 'Turma A'},
            {'id': 11, 'nome': 'Turma B'}
        ])
        
        modal = MatriculaModal(
            parent=root,
            aluno_id=123,
            nome_aluno="João Silva",
            colors=mock_app.cores
        )
        
        # Simula seleção de série
        if hasattr(modal, 'serie_var') and modal.serie_var:
            modal.serie_var.set('1º Ano')
            setattr(modal, '_series_data', [{'id': 1, 'nome': '1º Ano'}])
            
            # Act
            modal._atualizar_turmas()
            
            # Assert
            mock_turmas.assert_called_once_with(1, 1)
    
    @patch('src.ui.matricula_modal.obter_ano_letivo_atual')
    @patch('src.ui.matricula_modal.verificar_matricula_existente')
    @patch('src.ui.matricula_modal.obter_series_disponiveis')
    @patch('src.ui.matricula_modal.matricular_aluno')
    def test_confirmar_matricula_com_sucesso(
        self, mock_matricular, mock_series, mock_verificar, mock_ano, root, mock_app
    ):
        """Testa confirmação de matrícula com sucesso."""
        # Arrange
        mock_ano.return_value = (True, {'id': 1, 'ano': 2025})
        mock_verificar.return_value = (False, None)
        mock_series.return_value = (True, [{'id': 1, 'nome': '1º Ano'}])
        mock_matricular.return_value = (True, "Aluno matriculado com sucesso")
        
        callback = Mock()
        modal = MatriculaModal(
            parent=root,
            aluno_id=123,
            nome_aluno="João Silva",
            colors=mock_app.cores,
            callback_sucesso=callback
        )
        
        # Configura dados necessários
        if hasattr(modal, 'serie_var') and modal.serie_var:
            modal.serie_var.set('1º Ano')
            setattr(modal, '_series_data', [{'id': 1, 'nome': '1º Ano'}])
        
        if hasattr(modal, 'turma_var') and modal.turma_var:
            modal.turma_var.set('Turma A')
            setattr(modal.turma_var, '_turmas_data', [{'id': 10, 'nome': 'Turma A'}])
        
        # Act
        with patch('tkinter.messagebox.showinfo') as mock_info:
            modal._confirmar_matricula()
            
            # Assert
            mock_matricular.assert_called_once_with(123, 10, 1, 'Ativo')
            mock_info.assert_called_once()
            callback.assert_called_once()
    
    @patch('src.ui.matricula_modal.obter_ano_letivo_atual')
    @patch('src.ui.matricula_modal.verificar_matricula_existente')
    @patch('src.ui.matricula_modal.obter_series_disponiveis')
    def test_confirmar_matricula_sem_serie_selecionada(
        self, mock_series, mock_verificar, mock_ano, root, mock_app
    ):
        """Testa que matrícula falha sem série selecionada."""
        # Arrange
        mock_ano.return_value = (True, {'id': 1, 'ano': 2025})
        mock_verificar.return_value = (False, None)
        mock_series.return_value = (True, [{'id': 1, 'nome': '1º Ano'}])
        
        modal = MatriculaModal(
            parent=root,
            aluno_id=123,
            nome_aluno="João Silva",
            colors=mock_app.cores
        )
        
        # Act & Assert
        with patch('tkinter.messagebox.showwarning') as mock_warning:
            modal._confirmar_matricula()
            mock_warning.assert_called_once()
    
    @patch('src.ui.actions.abrir_matricula_modal')
    def test_action_handler_matricular_aluno(self, mock_abrir_modal, mock_app):
        """Testa que ActionHandler chama o modal de matrícula corretamente."""
        # Arrange
        handler = ActionHandler(mock_app)
        mock_app.table_manager.get_selected_item.return_value = {
            'id': 123,
            'nome': 'João Silva'
        }
        
        # Act
        handler.matricular_aluno_modal()
        
        # Assert
        mock_abrir_modal.assert_called_once_with(
            parent=mock_app.janela,
            aluno_id=123,
            nome_aluno='João Silva',
            colors=mock_app.cores,
            callback_sucesso=handler._atualizar_tabela
        )
    
    @patch('src.ui.actions.abrir_matricula_modal')
    def test_action_handler_matricular_sem_selecao(self, mock_abrir_modal, mock_app):
        """Testa que ActionHandler alerta quando nenhum aluno está selecionado."""
        # Arrange
        handler = ActionHandler(mock_app)
        mock_app.table_manager.get_selected_item.return_value = None
        
        # Act & Assert
        with patch('tkinter.messagebox.showwarning') as mock_warning:
            handler.matricular_aluno_modal()
            mock_warning.assert_called_once()
            mock_abrir_modal.assert_not_called()


class TestFuncionarioIntegrationFlow:
    """Testes de integração para operações de funcionários."""
    
    @patch('src.services.funcionario_service.buscar_funcionario')
    def test_buscar_funcionario_com_resultados(self, mock_buscar, mock_app):
        """Testa busca de funcionário com resultados."""
        # Arrange
        handler = ActionHandler(mock_app)
        mock_buscar.return_value = (True, [
            {'id': 1, 'nome': 'Maria Silva', 'cpf': '123.456.789-00'},
            {'id': 2, 'nome': 'João Silva', 'cpf': '987.654.321-00'}
        ])
        
        # Act
        handler.buscar_funcionario("Silva")
        
        # Assert
        mock_buscar.assert_called_once_with("Silva")
        mock_app.table_manager.atualizar_dados.assert_called_once()
        mock_app.update_status.assert_called_once()
    
    @patch('src.services.funcionario_service.buscar_funcionario')
    def test_buscar_funcionario_sem_resultados(self, mock_buscar, mock_app):
        """Testa busca de funcionário sem resultados."""
        # Arrange
        handler = ActionHandler(mock_app)
        mock_buscar.return_value = (True, [])
        
        # Act
        with patch('tkinter.messagebox.showinfo') as mock_info:
            handler.buscar_funcionario("NomeInexistente")
            
            # Assert
            mock_info.assert_called_once()
    
    @patch('src.services.funcionario_service.listar_funcionarios')
    def test_listar_funcionarios_todos(self, mock_listar, mock_app):
        """Testa listagem de todos os funcionários."""
        # Arrange
        handler = ActionHandler(mock_app)
        mock_listar.return_value = (True, [
            {'id': 1, 'nome': 'Maria Silva', 'cargo': 'Professor'},
            {'id': 2, 'nome': 'João Silva', 'cargo': 'Coordenador'}
        ])
        
        # Act
        handler.listar_funcionarios()
        
        # Assert
        mock_listar.assert_called_once_with(None)
        mock_app.table_manager.atualizar_dados.assert_called_once()
    
    @patch('src.services.funcionario_service.listar_funcionarios')
    def test_listar_funcionarios_por_cargo(self, mock_listar, mock_app):
        """Testa listagem de funcionários filtrada por cargo."""
        # Arrange
        handler = ActionHandler(mock_app)
        mock_listar.return_value = (True, [
            {'id': 1, 'nome': 'Maria Silva', 'cargo': 'Professor'}
        ])
        
        # Act
        handler.listar_funcionarios("Professor")
        
        # Assert
        mock_listar.assert_called_once_with("Professor")
    
    @patch('src.services.funcionario_service.excluir_funcionario')
    def test_excluir_funcionario_com_sucesso(self, mock_excluir, mock_app):
        """Testa exclusão de funcionário com sucesso."""
        # Arrange
        handler = ActionHandler(mock_app)
        mock_app.table_manager.get_selected_item.return_value = {
            'id': 123,
            'nome': 'João Silva'
        }
        mock_excluir.return_value = (True, "Funcionário excluído com sucesso")
        
        # Act
        with patch('tkinter.messagebox.askyesno', return_value=True):
            with patch('tkinter.messagebox.showinfo') as mock_info:
                handler.excluir_funcionario()
                
                # Assert
                mock_excluir.assert_called_once_with(123)
                mock_info.assert_called_once()
                mock_app.table_manager.atualizar_dados.assert_called_once()
    
    @patch('src.services.funcionario_service.excluir_funcionario')
    def test_excluir_funcionario_com_vinculos(self, mock_excluir, mock_app):
        """Testa que exclusão falha quando funcionário tem vínculos."""
        # Arrange
        handler = ActionHandler(mock_app)
        mock_app.table_manager.get_selected_item.return_value = {
            'id': 123,
            'nome': 'João Silva'
        }
        mock_excluir.return_value = (
            False, 
            "Não é possível excluir: funcionário possui turmas associadas"
        )
        
        # Act
        with patch('tkinter.messagebox.askyesno', return_value=True):
            with patch('tkinter.messagebox.showerror') as mock_error:
                handler.excluir_funcionario()
                
                # Assert
                mock_error.assert_called_once()
    
    @patch('src.services.funcionario_service.excluir_funcionario')
    def test_excluir_funcionario_cancelado(self, mock_excluir, mock_app):
        """Testa que exclusão não ocorre quando usuário cancela."""
        # Arrange
        handler = ActionHandler(mock_app)
        mock_app.table_manager.get_selected_item.return_value = {
            'id': 123,
            'nome': 'João Silva'
        }
        
        # Act
        with patch('tkinter.messagebox.askyesno', return_value=False):
            handler.excluir_funcionario()
            
            # Assert
            mock_excluir.assert_not_called()
