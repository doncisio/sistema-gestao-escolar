"""
Classe principal da aplicação de gestão escolar

Este módulo define a classe Application que encapsula toda a lógica de
inicialização e gerenciamento da interface Tkinter, substituindo variáveis
globais por atributos de instância.
"""

from tkinter import Tk, Frame, StringVar, NSEW, EW, TRUE
from tkinter.ttk import Style, Separator
from typing import Optional, Dict, Any
import os

from config_logs import get_logger
from conexao import inicializar_pool, fechar_pool
from db.connection import get_connection
from ui.dashboard import DashboardManager
from ui.table import TableManager
from ui.action_callbacks import ActionCallbacksManager
from ui.button_factory import ButtonFactory
from ui.menu import MenuManager

# Logger
logger = get_logger(__name__)


class Application:
    """
    Classe principal da aplicação que gerencia a janela Tkinter e o estado da aplicação.
    
    Encapsula variáveis que antes eram globais:
    - janela: instância Tk principal
    - cores: dicionário com paleta de cores (co0-co9)
    - frames: referências aos frames principais da UI
    - estado: selected_item, query, etc.
    - managers: dashboard_manager, etc.
    
    Attributes:
        janela (Tk): Janela principal da aplicação
        colors (Dict[str, str]): Paleta de cores da aplicação
        frames (Dict[str, Frame]): Frames principais (logo, dados, detalhes, tabela)
        dashboard_manager (Optional[DashboardManager]): Gerenciador do dashboard
        selected_item (Optional[Any]): Item atualmente selecionado na tabela
        query (Optional[str]): Query de pesquisa atual
        status_label (Optional[Any]): Label de status no rodapé
        label_rodape (Optional[Any]): Label adicional no rodapé
    """
    
    def __init__(self):
        """Inicializa a aplicação e seus componentes."""
        logger.debug("Inicializando aplicação...")
        
        # Estado da aplicação
        self.selected_item: Optional[Any] = None
        self.query: Optional[str] = None
        self.status_label: Optional[Any] = None
        self.label_rodape: Optional[Any] = None
        
        # Managers
        self.dashboard_manager: Optional[DashboardManager] = None
        self.table_manager: Optional[TableManager] = None
        self.action_callbacks: Optional[ActionCallbacksManager] = None
        self.button_factory: Optional[ButtonFactory] = None
        self.menu_manager: Optional[MenuManager] = None
        self.e_nome_pesquisa = None  # Entry de pesquisa
        
        # Janela principal (será criada no setup)
        self.janela: Optional[Tk] = None
        
        # Paleta de cores
        self.colors: Dict[str, str] = {}
        
        # Frames da interface
        self.frames: Dict[str, Frame] = {}
        
        # Inicializar pool de conexões
        self._initialize_connection_pool()
        
        # Setup da aplicação
        self._setup_window()
        self._setup_colors()
        self._setup_styles()
    
    def _initialize_connection_pool(self):
        """Inicializa o pool de conexões com o banco de dados."""
        try:
            logger.debug("Inicializando connection pool...")
            inicializar_pool()
            logger.debug("Connection pool inicializado com sucesso")
        except Exception as e:
            logger.exception(f"Erro ao inicializar connection pool: {e}")
            raise
    
    def _setup_window(self):
        """Configura a janela principal da aplicação."""
        self.janela = Tk()
        
        # Obter nome da escola do banco de dados
        nome_escola = self._get_school_name()
        
        # Configurar janela
        self.janela.title(f"Sistema de Gerenciamento da {nome_escola}")
        self.janela.geometry('850x670')
        self.janela.resizable(width=TRUE, height=TRUE)
        
        # Configurar grid da janela para expansão
        self.janela.grid_rowconfigure(0, weight=0)  # Logo
        self.janela.grid_rowconfigure(1, weight=0)  # Separador
        self.janela.grid_rowconfigure(2, weight=0)  # Dados
        self.janela.grid_rowconfigure(3, weight=0)  # Separador
        self.janela.grid_rowconfigure(4, weight=1)  # Detalhes (expande)
        self.janela.grid_rowconfigure(5, weight=0)  # Separador
        self.janela.grid_rowconfigure(6, weight=1)  # Tabela (expande)
        self.janela.grid_rowconfigure(7, weight=0)  # Separador
        self.janela.grid_rowconfigure(8, weight=0)  # Rodapé
        self.janela.grid_columnconfigure(0, weight=1)  # Coluna principal
        
        logger.debug(f"Janela configurada: {nome_escola}")
    
    def _get_school_name(self) -> str:
        """
        Obtém o nome da escola do banco de dados.
        
        Returns:
            str: Nome da escola ou "Escola" como fallback
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nome FROM Escolas WHERE id = %s", (60,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    return str(result[0])
                
                cursor.close()
        except Exception as e:
            logger.warning(f"Erro ao obter nome da escola: {e}")
        
        return "Escola"
    
    def _setup_colors(self):
        """Define a paleta de cores da aplicação."""
        # Garantir que a janela foi criada antes de acessar seus métodos
        assert self.janela is not None, "Janela não inicializada ao configurar cores"
        self.colors = {
            'co0': "#F5F5F5",  # Branco suave para o fundo
            'co1': "#003A70",  # Azul escuro (identidade visual)
            'co2': "#77B341",  # Verde
            'co3': "#E2418E",  # Rosa/Magenta
            'co4': "#4A86E8",  # Azul mais claro
            'co5': "#F26A25",  # Laranja
            'co6': "#F7B731",  # Amarelo
            'co7': "#333333",  # Cinza escuro
            'co8': "#BF3036",  # Vermelho
            'co9': "#6FA8DC",  # Azul claro
        }
        
        # Configurar background da janela
        self.janela.configure(background=self.colors['co1'])
        
        logger.debug("Cores configuradas")
    
    def _setup_styles(self):
        """Configura os estilos ttk da aplicação."""
        style = Style(self.janela)
        style.theme_use("clam")
        
        # Configuração de estilos personalizados
        style.configure(
            "TButton",
            background=self.colors['co4'],
            foreground=self.colors['co0'],
            font=('Ivy', 10)
        )
        style.configure(
            "TLabel",
            background=self.colors['co1'],
            foreground=self.colors['co0'],
            font=('Ivy', 10)
        )
        style.configure(
            "TEntry",
            background=self.colors['co0'],
            font=('Ivy', 10)
        )
        style.map(
            "TButton",
            background=[('active', self.colors['co2'])],
            foreground=[('active', self.colors['co0'])]
        )
        
        logger.debug("Estilos configurados")
    
    def setup_frames(self):
        """
        Cria e configura os frames principais da interface.
        
        Este método deve ser chamado após a inicialização básica e antes
        de adicionar conteúdo aos frames.
        """
        from ui.frames import criar_frames
        
        # Criar frames usando a função modular (assinatura: criar_frames(janela, co0, co1))
        self.frames = criar_frames(
            self.janela,
            self.colors['co0'],
            self.colors['co1']
        )
        
        logger.debug(f"Frames criados: {list(self.frames.keys())}")
    
    def setup_logo(self):
        """Cria o logo/header da aplicação."""
        from ui.frames import criar_logo
        # A função criar_logo tem assinatura: (frame_logo, nome_escola, co0, co1, co7)
        criar_logo(
            frame_logo=self.frames['frame_logo'],
            nome_escola=self._get_school_name(),
            co0=self.colors['co0'],
            co1=self.colors['co1'],
            co7=self.colors['co7']
        )
        
        logger.debug("Logo configurado")
    
    def setup_search(self, callback_pesquisa):
        """
        Cria a barra de pesquisa.
        
        Args:
            callback_pesquisa: Função callback para executar pesquisa
            
        Returns:
            Entry widget criado
        """
        from ui.frames import criar_pesquisa
        
        # assinatura: criar_pesquisa(frame_dados, pesquisar_callback, co0, co1, co4)
        e_nome_pesquisa = criar_pesquisa(
            frame_dados=self.frames['frame_dados'],
            pesquisar_callback=callback_pesquisa,
            co0=self.colors['co0'],
            co1=self.colors['co1'],
            co4=self.colors['co4']
        )
        
        # Armazenar referência ao Entry widget (não em frames, pois Entry != Frame)
        self.e_nome_pesquisa = e_nome_pesquisa
        
        logger.debug("Barra de pesquisa configurada")
        return e_nome_pesquisa
    
    def setup_footer(self):
        """Cria o rodapé com labels de status."""
        from ui.frames import criar_rodape
        # assinatura: criar_rodape(janela, co0, co1, co2) -> (label_rodape, status_label)
        result = criar_rodape(
            self.janela,
            co0=self.colors['co0'],
            co1=self.colors['co1'],
            co2=self.colors['co2']
        )

        # Armazenar referências aos labels
        self.label_rodape, self.status_label = result
        
        logger.debug("Rodapé configurado")
    
    def setup_table(self, on_select_callback=None, on_keyboard_callback=None):
        """
        Cria e configura a tabela principal.
        
        Args:
            on_select_callback: Callback para evento de seleção de item
            on_keyboard_callback: Callback para eventos de teclado
        """
        if 'frame_tabela' not in self.frames:
            logger.warning("Frame de tabela não existe ainda. Execute setup_frames() primeiro.")
            return
        
        self.table_manager = TableManager(
            parent_frame=self.frames['frame_tabela'],
            colors=self.colors
        )
        
        self.table_manager.criar_tabela(
            on_select_callback=on_select_callback,
            on_keyboard_callback=on_keyboard_callback
        )
        
        logger.debug("Tabela configurada")
    
    def setup_action_callbacks(self, atualizar_tabela_callback=None):
        """Cria e configura o ActionCallbacksManager para gerenciar ações da UI."""
        self.action_callbacks = ActionCallbacksManager(self.janela, atualizar_tabela_callback)
        logger.debug("ActionCallbacksManager configurado")
    
    def setup_button_factory(self):
        """Cria e configura o ButtonFactory para criar botões e menus."""
        if not self.action_callbacks:
            self.setup_action_callbacks()
        
        if 'frame_dados' not in self.frames:
            logger.warning("Frame de dados não existe. Execute setup_frames() primeiro.")
            return
        
        self.button_factory = ButtonFactory(
            janela=self.janela,
            frame_dados=self.frames['frame_dados'],
            callbacks=self.action_callbacks,
            colors=self.colors
        )
        logger.debug("ButtonFactory configurado")
    
    def setup_menu_manager(self):
        """Cria e configura o MenuManager para gerenciar menus contextuais."""
        self.menu_manager = MenuManager(self.janela)
        logger.debug("MenuManager configurado")
    
    def setup_context_menu(self, editar_callback=None):
        """
        Cria menu contextual para a tabela.
        
        Args:
            editar_callback: Callback para a opção 'Editar' do menu contextual
        """
        # Inicializar MenuManager se necessário
        if not self.menu_manager:
            self.setup_menu_manager()
        
        # Verificar se MenuManager foi inicializado
        if not self.menu_manager:
            logger.error("Erro: MenuManager não foi inicializado")
            return
        
        if not self.table_manager or not self.table_manager.treeview:
            logger.warning("TableManager não inicializado. Execute setup_table() primeiro.")
            return
        
        callbacks = {'editar': editar_callback} if editar_callback else {}
        self.menu_manager.criar_menu_contextual(
            treeview=self.table_manager.treeview,
            callbacks=callbacks
        )
        logger.debug("Menu contextual configurado")
    
    def setup_action_buttons_and_menus(self):
        """
        Cria botões de ação e barra de menus usando ButtonFactory.
        
        Este método substitui a antiga função criar_acoes() do main.py.
        """
        # Inicializar MenuManager se ainda não existe
        if not self.menu_manager:
            self.setup_menu_manager()
        
        # Inicializar ButtonFactory se ainda não existe
        if not self.button_factory:
            self.setup_button_factory()
        
        # Verificar se ButtonFactory foi inicializado com sucesso
        if not self.button_factory:
            logger.error("Erro: ButtonFactory não foi inicializado")
            return
        
        # Configurar interface completa (botões + menus)
        self.button_factory.configurar_interface()
        
        logger.debug("Botões e menus configurados via ButtonFactory")
    
    def update_status(self, message: str):
        """
        Atualiza a mensagem de status no rodapé.
        
        Args:
            message: Mensagem a ser exibida
        """
        if self.status_label:
            self.status_label.config(text=message)
            logger.debug(f"Status atualizado: {message}")
    
    def on_close(self):
        """Handler para o fechamento da janela."""
        logger.info("Fechando aplicação...")
        
        # Fechar dashboard manager se existir
        if self.dashboard_manager:
            try:
                # Implementar cleanup do dashboard se necessário
                pass
            except Exception as e:
                logger.error(f"Erro ao fechar dashboard: {e}")
        
        # Fechar connection pool
        try:
            fechar_pool()
            logger.info("Connection pool fechado")
        except Exception as e:
            logger.error(f"Erro ao fechar connection pool: {e}")
        
        # Destruir janela (assegurar que 'janela' foi inicializada)
        assert self.janela is not None, "Janela não inicializada ao fechar"
        self.janela.destroy()
        logger.info("Aplicação encerrada")
    
    def run(self):
        """
        Inicia o loop principal da aplicação.
        
        Este método bloqueia até que a janela seja fechada.
        """
        # Configurar protocolo de fechamento (garantir que a janela existe)
        assert self.janela is not None, "Janela não inicializada ao executar run"
        self.janela.protocol("WM_DELETE_WINDOW", self.on_close)
        
        logger.debug("Iniciando mainloop...")
        self.janela.mainloop()
