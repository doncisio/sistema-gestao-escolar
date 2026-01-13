"""
Módulo de gerenciamento de menus da interface.
Encapsula a criação e configuração de menus contextuais e dropdown do main.py.
"""

from tkinter import Menu
from typing import Optional, Dict, Callable
import logging

logger = logging.getLogger(__name__)


class MenuManager:
    """
    Gerenciador de menus da aplicação.
    Encapsula criação de menu contextual e menus dropdown.
    """
    
    def __init__(self, janela, action_handler=None):
        """
        Inicializa o gerenciador de menus.
        
        Args:
            janela: Janela Tkinter principal
            action_handler: Instância de ActionHandler para callbacks de ações
        """
        self.janela = janela
        self.action_handler = action_handler
        self.menu_contextual = None
        self.logger = logger
        
    def criar_menu_contextual(self, treeview, callbacks: Optional[Dict[str, Callable]] = None):
        """
        Cria menu contextual para a Treeview com ações de editar, excluir, etc.
        
        Args:
            treeview: Widget Treeview onde o menu será anexado
            callbacks: Dict com callbacks para ações do menu
                      Ex: {'editar': func_editar, 'excluir': func_excluir}
        
        Returns:
            Menu: Instância do menu contextual criado
        """
        try:
            self.menu_contextual = Menu(self.janela, tearoff=0)
            
            # Callbacks padrão
            default_callbacks = {
                'editar': self.action_handler.editar_aluno if self.action_handler else None,
                'excluir': self.action_handler.excluir_aluno if self.action_handler else None,
                'detalhes': self.action_handler.ver_detalhes_aluno if self.action_handler else None
            }
            
            # Sobrescrever com callbacks fornecidos
            if callbacks:
                default_callbacks.update(callbacks)
            
            # Adicionar itens ao menu
            editar_cb = default_callbacks.get('editar')
            if editar_cb is not None:
                self.menu_contextual.add_command(
                    label="Editar",
                    command=editar_cb
                )
            
            excluir_cb = default_callbacks.get('excluir')
            if excluir_cb is not None:
                self.menu_contextual.add_command(
                    label="Excluir",
                    command=excluir_cb
                )
            
            self.menu_contextual.add_separator()
            
            detalhes_cb = default_callbacks.get('detalhes')
            if detalhes_cb is not None:
                self.menu_contextual.add_command(
                    label="Ver Detalhes",
                    command=detalhes_cb
                )
            
            # Bind do clique direito
            def mostrar_menu(event):
                if self.menu_contextual is None:
                    return

                # Verificar se o widget Treeview ainda existe (proteção contra widgets destruídos)
                try:
                    if not getattr(treeview, 'winfo_exists', lambda: False)() or not treeview.winfo_exists():
                        self.logger.warning('Treeview não existe mais ao tentar abrir menu contextual')
                        return
                except Exception:
                    # Se houver qualquer problema consultando o widget, logar e abortar
                    self.logger.exception('Erro ao verificar existência do Treeview antes de mostrar o menu')
                    return

                try:
                    # Selecionar item sob o cursor
                    item = None
                    try:
                        item = treeview.identify_row(event.y)
                    except Exception:
                        self.logger.exception('Erro ao identificar linha no Treeview')

                    if item:
                        try:
                            treeview.selection_set(item)
                            treeview.focus(item)
                        except Exception:
                            self.logger.exception('Erro ao selecionar/focar item no Treeview')

                    try:
                        self.menu_contextual.tk_popup(event.x_root, event.y_root)
                    except Exception:
                        self.logger.exception('Erro ao exibir menu contextual (tk_popup)')
                finally:
                    try:
                        self.menu_contextual.grab_release()
                    except Exception:
                        self.logger.exception('Erro ao liberar grab do menu contextual')
            
            treeview.bind("<Button-3>", mostrar_menu)  # Clique direito
            
            self.logger.debug("Menu contextual criado com sucesso")
            return self.menu_contextual
            
        except Exception as e:
            self.logger.error(f"Erro ao criar menu contextual: {str(e)}")
            return None
    
    def criar_menu_relatorios(self, parent_widget, callbacks: Optional[Dict[str, Callable]] = None):
        """
        Cria menu dropdown de relatórios.
        
        Args:
            parent_widget: Widget pai onde o menu será anexado
            callbacks: Dict com callbacks para cada tipo de relatório
        
        Returns:
            Menu: Instância do menu de relatórios criado
        """
        try:
            menu_relatorios = Menu(self.janela, tearoff=0)
            
            # Callbacks padrão (podem ser sobrescritos)
            default_callbacks = callbacks or {}
            
            # Submenus por categoria
            menu_listas = Menu(menu_relatorios, tearoff=0)
            menu_relatorios.add_cascade(label="Listas", menu=menu_listas)
            
            if default_callbacks.get('lista_alfabetica'):
                menu_listas.add_command(
                    label="Lista Alfabética",
                    command=default_callbacks['lista_alfabetica']
                )
            
            if default_callbacks.get('lista_frequencia'):
                menu_listas.add_command(
                    label="Lista de Frequência",
                    command=default_callbacks['lista_frequencia']
                )
            
            if default_callbacks.get('lista_reuniao'):
                menu_listas.add_command(
                    label="Lista de Reunião",
                    command=default_callbacks['lista_reuniao']
                )
            
            if default_callbacks.get('lista_fardamento'):
                menu_listas.add_command(
                    label="Lista de Fardamento",
                    command=default_callbacks['lista_fardamento']
                )
            
            # Submenu de Boletins
            menu_boletins = Menu(menu_relatorios, tearoff=0)
            menu_relatorios.add_cascade(label="Boletins", menu=menu_boletins)
            
            if default_callbacks.get('boletim_bimestral'):
                menu_boletins.add_command(
                    label="Boletim Bimestral",
                    command=default_callbacks['boletim_bimestral']
                )
            
            # Submenu de Atas
            menu_atas = Menu(menu_relatorios, tearoff=0)
            menu_relatorios.add_cascade(label="Atas", menu=menu_atas)
            
            if default_callbacks.get('ata_1a5'):
                menu_atas.add_command(
                    label="Ata 1º ao 5º Ano",
                    command=default_callbacks['ata_1a5']
                )
            
            if default_callbacks.get('ata_6a9'):
                menu_atas.add_command(
                    label="Ata 6º ao 9º Ano",
                    command=default_callbacks['ata_6a9']
                )
            
            self.logger.debug("Menu de relatórios criado com sucesso")
            return menu_relatorios
            
        except Exception as e:
            self.logger.error(f"Erro ao criar menu de relatórios: {str(e)}")
            return None
    
    def criar_menu_declaracoes(self, parent_widget, callbacks: Optional[Dict[str, Callable]] = None):
        """
        Cria menu dropdown de declarações.
        
        Args:
            parent_widget: Widget pai onde o menu será anexado
            callbacks: Dict com callbacks para cada tipo de declaração
        
        Returns:
            Menu: Instância do menu de declarações criado
        """
        try:
            menu_declaracoes = Menu(self.janela, tearoff=0)
            
            default_callbacks = callbacks or {}
            
            if default_callbacks.get('declaracao_aluno'):
                menu_declaracoes.add_command(
                    label="Declaração de Aluno",
                    command=default_callbacks['declaracao_aluno']
                )
            
            if default_callbacks.get('declaracao_funcionario'):
                menu_declaracoes.add_command(
                    label="Declaração de Funcionário",
                    command=default_callbacks['declaracao_funcionario']
                )
            
            if default_callbacks.get('declaracao_comparecimento'):
                menu_declaracoes.add_command(
                    label="Declaração de Comparecimento",
                    command=default_callbacks['declaracao_comparecimento']
                )
            
            self.logger.debug("Menu de declarações criado com sucesso")
            return menu_declaracoes
            
        except Exception as e:
            self.logger.error(f"Erro ao criar menu de declarações: {str(e)}")
            return None
    
    def criar_menu_meses(self, callback_mes: Callable):
        """
        Cria menu com lista de meses do ano.
        Útil para seleção de período em relatórios.
        
        Args:
            callback_mes: Função chamada quando um mês é selecionado
                         Recebe (numero_mes, nome_mes) como argumentos
        
        Returns:
            Menu: Instância do menu de meses criado
        """
        try:
            from src.utils.dates import nome_mes_pt
            
            menu_meses = Menu(self.janela, tearoff=0)
            
            for num_mes in range(1, 13):
                nome = nome_mes_pt(num_mes)
                menu_meses.add_command(
                    label=nome,
                    command=lambda n=num_mes, nm=nome: callback_mes(n, nm)
                )
            
            self.logger.debug("Menu de meses criado com sucesso")
            return menu_meses
            
        except Exception as e:
            self.logger.error(f"Erro ao criar menu de meses: {str(e)}")
            return None
    
    def anexar_menu_a_botao(self, botao, menu):
        """
        Anexa um menu dropdown a um botão.
        
        Args:
            botao: Widget Button
            menu: Menu a ser anexado
        """
        try:
            def mostrar_menu(event=None):
                try:
                    # Posicionar menu abaixo do botão
                    x = botao.winfo_rootx()
                    y = botao.winfo_rooty() + botao.winfo_height()
                    menu.tk_popup(x, y)
                finally:
                    menu.grab_release()
            
            botao.config(command=mostrar_menu)
            
        except Exception as e:
            self.logger.error(f"Erro ao anexar menu a botão: {str(e)}")
