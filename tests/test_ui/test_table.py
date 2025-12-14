"""
Testes unitários para ui.table.TableManager

Este módulo testa a classe TableManager que gerencia a Treeview.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from src.ui.table import TableManager


@pytest.fixture
def mock_frame():
    """Fixture que mocka um Frame."""
    return MagicMock()


@pytest.fixture
def colors_dict():
    """Fixture com dicionário de cores."""
    return {
        'co0': '#F5F5F5',
        'co1': '#003A70',
        'co4': '#4A86E8'
    }


class TestTableManagerInit:
    """Testes para inicialização do TableManager."""
    
    def test_init_stores_parameters(self, mock_frame, colors_dict):
        """Testa que __init__ armazena os parâmetros corretamente."""
        manager = TableManager(mock_frame, colors_dict)
        
        assert manager.parent_frame is mock_frame
        assert manager.colors == colors_dict
        assert manager.treeview is None
        assert manager.tabela_frame is None
        assert manager.colunas == ['ID', 'Nome']
        assert len(manager.df) == 0


class TestTableManagerCriarTabela:
    """Testes para o método criar_tabela."""
    
    @patch('ui.table.Frame')
    @patch('ui.table.ttk.Treeview')
    @patch('ui.table.ttk.Scrollbar')
    @patch('ui.table.ttk.Style')
    @patch('ui.table.Label')
    def test_criar_tabela_basic(
        self,
        mock_label,
        mock_style,
        mock_scrollbar,
        mock_treeview,
        mock_frame_class,
        mock_frame,
        colors_dict
    ):
        """Testa criação básica da tabela."""
        manager = TableManager(mock_frame, colors_dict)
        manager.criar_tabela()
        
        # Verificar que componentes foram criados
        mock_frame_class.assert_called()
        mock_treeview.assert_called_once()
        mock_label.assert_called_once()
        
        assert manager.treeview is not None
        assert manager.tabela_frame is not None
        assert manager.instrucao_label is not None
    
    @patch('ui.table.Frame')
    @patch('ui.table.ttk.Treeview')
    @patch('ui.table.ttk.Scrollbar')
    @patch('ui.table.ttk.Style')
    @patch('ui.table.Label')
    def test_criar_tabela_with_columns(
        self,
        mock_label,
        mock_style,
        mock_scrollbar,
        mock_treeview,
        mock_frame_class,
        mock_frame,
        colors_dict
    ):
        """Testa criação da tabela com colunas customizadas."""
        manager = TableManager(mock_frame, colors_dict)
        colunas_custom = ['ID', 'Nome', 'Email', 'Telefone']
        
        manager.criar_tabela(colunas=colunas_custom)
        
        assert manager.colunas == colunas_custom
    
    @patch('ui.table.Frame')
    @patch('ui.table.ttk.Treeview')
    @patch('ui.table.ttk.Scrollbar')
    @patch('ui.table.ttk.Style')
    @patch('ui.table.Label')
    def test_criar_tabela_with_callback(
        self,
        mock_label,
        mock_style,
        mock_scrollbar,
        mock_treeview,
        mock_frame_class,
        mock_frame,
        colors_dict
    ):
        """Testa criação da tabela com callbacks."""
        manager = TableManager(mock_frame, colors_dict)
        select_callback = Mock()
        keyboard_callback = Mock()
        
        manager.criar_tabela(
            on_select_callback=select_callback,
            on_keyboard_callback=keyboard_callback
        )
        
        # Verificar que callbacks foram vinculados
        assert manager.treeview.bind.call_count > 0


class TestTableManagerMethods:
    """Testes para métodos auxiliares do TableManager."""
    
    def test_format_date_from_string(self, mock_frame, colors_dict):
        """Testa formatação de data a partir de string."""
        manager = TableManager(mock_frame, colors_dict)
        
        result = manager._format_date('2024-12-25')
        
        assert result == '25/12/2024'
    
    def test_format_date_invalid(self, mock_frame, colors_dict):
        """Testa formatação de valor inválido."""
        manager = TableManager(mock_frame, colors_dict)
        
        result = manager._format_date('não é data')
        
        assert result == 'não é data'
    
    @patch('ui.table.Frame')
    @patch('ui.table.ttk.Treeview')
    @patch('ui.table.ttk.Scrollbar')
    @patch('ui.table.ttk.Style')
    @patch('ui.table.Label')
    def test_atualizar_dados(
        self,
        mock_label,
        mock_style,
        mock_scrollbar,
        mock_treeview,
        mock_frame_class,
        mock_frame,
        colors_dict
    ):
        """Testa atualização de dados da tabela."""
        manager = TableManager(mock_frame, colors_dict)
        manager.criar_tabela()
        
        # Criar DataFrame de teste
        df_novo = pd.DataFrame({
            'ID': [1, 2, 3],
            'Nome': ['Ana', 'Bruno', 'Carlos']
        })
        
        manager.atualizar_dados(df_novo)
        
        assert len(manager.df) == 3
        assert manager.df['Nome'].tolist() == ['Ana', 'Bruno', 'Carlos']
    
    @patch('ui.table.Frame')
    @patch('ui.table.ttk.Treeview')
    @patch('ui.table.ttk.Scrollbar')
    @patch('ui.table.ttk.Style')
    @patch('ui.table.Label')
    def test_show_hide(
        self,
        mock_label,
        mock_style,
        mock_scrollbar,
        mock_treeview,
        mock_frame_class,
        mock_frame,
        colors_dict
    ):
        """Testa métodos show e hide."""
        manager = TableManager(mock_frame, colors_dict)
        manager.criar_tabela()
        
        # Mock dos métodos pack
        manager.tabela_frame.pack = Mock()
        manager.tabela_frame.pack_forget = Mock()
        manager.instrucao_label.pack = Mock()
        manager.instrucao_label.pack_forget = Mock()
        
        # Testar show
        manager.show()
        manager.tabela_frame.pack.assert_called_once()
        manager.instrucao_label.pack.assert_called_once()
        
        # Testar hide
        manager.hide()
        manager.tabela_frame.pack_forget.assert_called_once()
        manager.instrucao_label.pack_forget.assert_called_once()
    
    @patch('ui.table.Frame')
    @patch('ui.table.ttk.Treeview')
    @patch('ui.table.ttk.Scrollbar')
    @patch('ui.table.ttk.Style')
    @patch('ui.table.Label')
    def test_limpar(
        self,
        mock_label,
        mock_style,
        mock_scrollbar,
        mock_treeview,
        mock_frame_class,
        mock_frame,
        colors_dict
    ):
        """Testa limpeza da tabela."""
        manager = TableManager(mock_frame, colors_dict)
        manager.criar_tabela()
        
        # Adicionar dados
        df = pd.DataFrame({'ID': [1], 'Nome': ['Teste']})
        manager.atualizar_dados(df)
        assert len(manager.df) == 1
        
        # Mock get_children para simular itens
        manager.treeview.get_children.return_value = ['item1']
        
        # Limpar
        manager.limpar()
        
        # Verificar que DataFrame ficou vazio
        assert len(manager.df) == 0
        # Verificar que delete foi chamado pelo menos uma vez
        assert manager.treeview.delete.call_count >= 1
