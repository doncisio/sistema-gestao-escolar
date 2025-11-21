"""
Gerenciador da tabela (Treeview) principal da aplicação

Este módulo encapsula a lógica de criação e gerenciamento da Treeview,
substituindo a função global criar_tabela() do main.py.
"""

from tkinter import Frame, Label, NSEW, NS, EW, W, BOTH
from tkinter import ttk
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Callable

from config_logs import get_logger

logger = get_logger(__name__)


class TableManager:
    """
    Gerencia a tabela (Treeview) principal da aplicação.
    
    Encapsula:
    - Criação e configuração da Treeview
    - Estilos e cores
    - Barras de rolagem
    - Vinculação de eventos
    - Atualização de dados
    
    Attributes:
        parent_frame (Frame): Frame pai que conterá a tabela
        colors (Dict[str, str]): Dicionário de cores da aplicação
        treeview (ttk.Treeview): Widget da tabela
        tabela_frame (Frame): Frame que contém a tabela e scrollbars
        colunas (List[str]): Lista de nomes das colunas
        df (pd.DataFrame): DataFrame com os dados atuais
    """
    
    def __init__(self, parent_frame: Frame, colors: Dict[str, str]):
        """
        Inicializa o gerenciador da tabela.
        
        Args:
            parent_frame: Frame pai onde a tabela será criada
            colors: Dicionário com as cores da aplicação (co0, co1, co4, etc.)
        """
        self.parent_frame = parent_frame
        self.colors = colors
        
        # Componentes da tabela
        self.treeview: Optional[ttk.Treeview] = None
        self.tabela_frame: Optional[Frame] = None
        self.instrucao_label: Optional[Label] = None
        
        # Dados
        self.colunas: List[str] = ['ID', 'Nome']
        self.df: pd.DataFrame = pd.DataFrame(columns=self.colunas)
        
        logger.debug("TableManager inicializado")
    
    def criar_tabela(
        self,
        colunas: Optional[List[str]] = None,
        df: Optional[pd.DataFrame] = None,
        on_select_callback: Optional[Callable] = None,
        on_keyboard_callback: Optional[Callable] = None
    ):
        """
        Cria e configura a tabela (Treeview).
        
        Args:
            colunas: Lista de nomes das colunas (usa padrão se None)
            df: DataFrame com dados iniciais (usa vazio se None)
            on_select_callback: Callback para evento de seleção (clique)
            on_keyboard_callback: Callback para eventos de teclado
        """
        # Atualizar colunas e dados se fornecidos
        if colunas:
            self.colunas = colunas
        if df is not None:
            self.df = df
        
        # Frame para conter a tabela e sua barra de rolagem
        self.tabela_frame = Frame(self.parent_frame)
        
        # Configurando o gerenciador de layout
        self.tabela_frame.grid_rowconfigure(0, weight=1)
        self.tabela_frame.grid_columnconfigure(0, weight=1)
        
        # Criar e configurar estilo
        self._setup_style()
        
        # Criação do Treeview com barras de rolagem
        self.treeview = ttk.Treeview(
            self.tabela_frame,
            style="mystyle.Treeview",
            columns=self.colunas,
            show='headings'
        )
        
        # Configurar barras de rolagem
        vsb = ttk.Scrollbar(
            self.tabela_frame,
            orient="vertical",
            command=self.treeview.yview
        )
        hsb = ttk.Scrollbar(
            self.tabela_frame,
            orient="horizontal",
            command=self.treeview.xview
        )
        self.treeview.configure(
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        # Posicionar os componentes
        self.treeview.grid(row=0, column=0, sticky=NSEW)
        vsb.grid(row=0, column=1, sticky=NS)
        hsb.grid(row=1, column=0, sticky=EW)
        
        # Configuração das colunas
        for col in self.colunas:
            self.treeview.heading(col, text=col, anchor=W)
            self.treeview.column(col, width=120, anchor=W)
        
        # Adicionar dados iniciais
        self._populate_data()
        
        # Vincular callbacks se fornecidos
        if on_select_callback:
            self.treeview.bind("<ButtonRelease-1>", on_select_callback)
            self.treeview.bind("<Double-1>", on_select_callback)
        
        if on_keyboard_callback:
            self.treeview.bind("<Up>", on_keyboard_callback)
            self.treeview.bind("<Down>", on_keyboard_callback)
            self.treeview.bind("<Prior>", on_keyboard_callback)  # Page Up
            self.treeview.bind("<Next>", on_keyboard_callback)   # Page Down
            self.treeview.bind("<Home>", on_keyboard_callback)   # Home
            self.treeview.bind("<End>", on_keyboard_callback)    # End
        
        # Adicionar dica/instrução visual
        self.instrucao_label = Label(
            self.parent_frame,
            text="Clique ou use as setas do teclado para selecionar um item",
            font=('Ivy 10 italic'),
            bg=self.colors['co1'],
            fg=self.colors['co0']
        )
        
        logger.debug(f"Tabela criada com {len(self.colunas)} colunas e {len(self.df)} registros")
    
    def _setup_style(self):
        """Configura o estilo da Treeview."""
        style = ttk.Style()
        style.configure(
            "mystyle.Treeview",
            highlightthickness=0,
            bd=0,
            font=('Calibri', 11)
        )
        style.configure(
            "mystyle.Treeview.Heading",
            font=('Calibri', 13, 'bold'),
            background=self.colors['co1'],
            foreground=self.colors['co0']
        )
        
        # Configurar cores para linhas selecionadas
        style.map(
            'mystyle.Treeview',
            background=[('selected', self.colors['co4'])],
            foreground=[('selected', self.colors['co0'])]
        )
        
        style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])
        
        logger.debug("Estilo da tabela configurado")
    
    def _populate_data(self):
        """Popula a Treeview com dados do DataFrame."""
        if self.treeview is None or self.df is None:
            return
        
        # Limpar dados existentes
        for item in self.treeview.get_children():
            self.treeview.delete(item)
        
        # Adicionar dados do DataFrame
        for i, row in self.df.iterrows():
            row_list = list(row)
            
            # Padronizar data de nascimento (assumindo índice 4)
            if len(row_list) > 4 and row_list[4]:
                row_list[4] = self._format_date(row_list[4])
            
            self.treeview.insert("", "end", values=row_list)
        
        logger.debug(f"Tabela populada com {len(self.df)} registros")
    
    def _format_date(self, date_value: Any) -> str:
        """
        Formata valor de data para string DD/MM/YYYY.
        
        Args:
            date_value: Valor a ser formatado (string, date, datetime)
            
        Returns:
            String formatada ou valor original se não for data
        """
        try:
            if isinstance(date_value, str):
                # Tenta converter string para data
                data = datetime.strptime(date_value, '%Y-%m-%d')
            elif isinstance(date_value, (datetime, date)):
                data = date_value
            else:
                return str(date_value)
            
            return data.strftime('%d/%m/%Y')
        except Exception as e:
            logger.debug(f"Erro ao formatar data {date_value}: {e}")
            return str(date_value)
    
    def atualizar_dados(self, df: pd.DataFrame, colunas: Optional[List[str]] = None):
        """
        Atualiza os dados da tabela.
        
        Args:
            df: Novo DataFrame com os dados
            colunas: Nova lista de colunas (opcional)
        """
        if colunas:
            self.colunas = colunas
        
        self.df = df
        self._populate_data()
        
        logger.debug(f"Tabela atualizada: {len(self.df)} registros")
    
    def get_selected_item(self) -> Optional[Dict[str, Any]]:
        """
        Retorna o item atualmente selecionado.
        
        Returns:
            Dicionário com os valores do item ou None se nada selecionado
        """
        if not self.treeview:
            return None
        
        selection = self.treeview.selection()
        if not selection:
            return None
        
        item = selection[0]
        values = self.treeview.item(item, "values")
        
        if not values:
            return None
        
        # Criar dicionário com colunas e valores
        return {col: val for col, val in zip(self.colunas, values)}
    
    def show(self):
        """Exibe a tabela no frame pai."""
        if self.tabela_frame:
            self.tabela_frame.pack(fill=BOTH, expand=True)
        if self.instrucao_label:
            self.instrucao_label.pack()
        
        logger.debug("Tabela exibida")
    
    def hide(self):
        """Oculta a tabela do frame pai."""
        if self.tabela_frame:
            self.tabela_frame.pack_forget()
        if self.instrucao_label:
            self.instrucao_label.pack_forget()
        
        logger.debug("Tabela ocultada")
    
    def limpar(self):
        """Limpa todos os itens da tabela."""
        if self.treeview:
            for item in self.treeview.get_children():
                self.treeview.delete(item)
        
        self.df = pd.DataFrame(columns=self.colunas)
        logger.debug("Tabela limpa")
