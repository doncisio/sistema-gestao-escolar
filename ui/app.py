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
from config import get_icon_path
from conexao import inicializar_pool, fechar_pool
from db.connection import get_connection

# Importar settings centralizado
try:
    from config.settings import settings
except ImportError:
    settings = None
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
    
    def __init__(self, usuario=None):
        """
        Inicializa a aplicação e seus componentes.
        
        Args:
            usuario: Usuário logado (opcional, quando sistema de perfis está ativo)
        """
        logger.debug("Inicializando aplicação...")
        
        # Usuário logado (None se perfis desabilitados)
        self.usuario = usuario
        
        # Estado da aplicação
        self.selected_item: Optional[Any] = None
        self.query: Optional[str] = None
        self.status_label: Optional[Any] = None
        self.label_rodape: Optional[Any] = None
        self.readonly_mode: bool = False  # Flag para modo somente leitura
        
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
        Obtém o nome da escola do banco de dados com modo degradado.
        
        Returns:
            str: Nome da escola ou "Escola" como fallback
        """
        try:
            # Obter ID da escola da configuração
            escola_id = settings.app.escola_id if settings else 60
            
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nome FROM Escolas WHERE id = %s", (escola_id,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    return str(result[0])
                
                cursor.close()
        except Exception as e:
            logger.warning(f"Erro ao obter nome da escola: {e}")
            logger.info("Sistema será iniciado em modo somente leitura")
            
            # Ativar modo somente leitura
            self.readonly_mode = True
            
            # Exibir aviso visual na UI (após janela estar pronta)
            if hasattr(self, 'janela') and self.janela:
                try:
                    import tkinter.messagebox as mb
                    self.janela.after(100, lambda: mb.showwarning(
                        "Modo Somente Leitura",
                        "Não foi possível conectar ao banco de dados.\n\n"
                        "O sistema será iniciado em modo somente leitura.\n"
                        "Funções de edição estarão desabilitadas."
                    ))
                except Exception:
                    pass  # Evitar erro se tkinter não estiver pronto
        
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
    
    def setup_dashboard(self, criar_agora=False):
        """
        Inicializa o DashboardManager (opcionalmente cria o dashboard).
        
        Este método configura o dashboard com gráfico de pizza mostrando
        a distribuição de alunos por série e turma.
        
        Args:
            criar_agora: Se True, cria o dashboard imediatamente. Se False, apenas
                        inicializa o manager para criação sob demanda.
        """
        if 'frame_tabela' not in self.frames:
            logger.warning("Frame de tabela não existe. Execute setup_frames() primeiro.")
            return
        
        try:
            from services.db_service import DbService
            from config import get_flag
            
            # Frame getter para o dashboard
            frame_getter = lambda: self.frames.get('frame_tabela')
            
            # Criar serviço de banco de dados
            db_service = DbService(get_connection)
            
            # Cache para estatísticas do dashboard (vazio inicialmente)
            cache_estatisticas = {'timestamp': None, 'dados': None}
            
            # Criar DashboardManager
            escola_id = settings.app.escola_id if settings else 60
            self.dashboard_manager = DashboardManager(
                janela=self.janela,
                db_service=db_service,
                frame_getter=frame_getter,
                cache_ref=cache_estatisticas,
                escola_id=escola_id,
                co_bg=self.colors['co1'],
                co_fg=self.colors['co0'],
                co_accent=self.colors['co4']
            )
            
            logger.debug("✓ DashboardManager instanciado com sucesso")
            
            # Criar o dashboard apenas se solicitado
            if criar_agora:
                # Verificar se dashboard por perfil está habilitado
                dashboard_por_perfil = get_flag('dashboard_por_perfil', True)
                
                if dashboard_por_perfil and self.usuario:
                    # Usar dashboard específico por perfil
                    self.dashboard_manager.criar_dashboard_por_perfil(self.usuario)
                    logger.debug(f"✓ Dashboard por perfil criado para {self.usuario.perfil_display}")
                else:
                    # Dashboard padrão (administrador)
                    self.dashboard_manager.criar_dashboard()
                    logger.debug("✓ Dashboard padrão criado e exibido")
            else:
                logger.info("✓ Dashboard configurado para carregamento sob demanda")
            
        except Exception as e:
            logger.error(f"Erro ao configurar dashboard: {e}", exc_info=True)
    
    def update_status(self, message: str):
        """
        Atualiza a mensagem de status no rodapé.
        
        Args:
            message: Mensagem a ser exibida
        """
        if self.status_label:
            self.status_label.config(text=message)
            logger.debug(f"Status atualizado: {message}")
    
    def _pesquisar_callback(self, event=None):
        """
        Callback de pesquisa integrado.
        
        Args:
            event: Evento Tkinter (opcional)
        """
        from ui.search import pesquisar_alunos_funcionarios
        
        # Obter referência ao Entry de pesquisa
        e_nome_pesquisa = self.e_nome_pesquisa
        if e_nome_pesquisa:
            texto = e_nome_pesquisa.get()
            
            # Executar pesquisa
            pesquisar_alunos_funcionarios(
                texto_pesquisa=texto,
                get_treeview_func=lambda: self.table_manager.treeview if self.table_manager else None,
                get_tabela_frame_func=lambda: self.table_manager.tabela_frame if self.table_manager else None,
                frame_tabela=self.frames.get('frame_tabela'),
                criar_tabela_func=lambda: self.setup_table(on_select_callback=self._on_select_callback),
                criar_dashboard_func=lambda: self.dashboard_manager.criar_dashboard() if self.dashboard_manager else None
            )
    
    def _on_select_callback(self, event):
        """
        Callback de seleção na tabela.
        
        Args:
            event: Evento Tkinter de seleção
        """
        try:
            from ui.detalhes import exibir_detalhes_item
            from tkinter import Frame, Label, LEFT, BOTH, TRUE, X
            from PIL import Image, ImageTk
            
            if not self.table_manager or not self.table_manager.treeview:
                return
            
            treeview = self.table_manager.treeview
            selected = treeview.selection()
            
            if not selected:
                return
            
            item = selected[0]
            values = treeview.item(item, 'values')
            
            if not values or len(values) < 3:
                return
            
            # Estrutura Sprint 15: (id, nome, tipo, cargo, data_nascimento)
            item_id = values[0]
            tipo = values[2]
            
            # Atualizar selected_item na aplicação
            self.selected_item = {'tipo': tipo, 'id': item_id, 'values': values}
            
            logger.debug(f"Item selecionado: {tipo} ID={item_id}")
            
            # Atualizar logo/título
            if 'frame_logo' in self.frames:
                frame_logo = self.frames['frame_logo']
                for widget in frame_logo.winfo_children():
                    widget.destroy()
                
                # Criar frame para o título
                titulo_frame = Frame(frame_logo, bg=self.colors['co0'])
                titulo_frame.pack(fill=BOTH, expand=TRUE)
                
                try:
                    # Tentar carregar ícone
                    app_lp = Image.open(get_icon_path('learning.png'))
                    app_lp = app_lp.resize((30, 30))
                    app_lp = ImageTk.PhotoImage(app_lp)
                    app_logo = Label(titulo_frame, image=app_lp, text=f"Detalhes: {values[1]}", 
                                    compound=LEFT, anchor='w', font=('Ivy 15 bold'), 
                                    bg=self.colors['co0'], fg=self.colors['co1'], padx=10, pady=5)
                    # Manter referência à imagem
                    setattr(app_logo, '_image_ref', app_lp)
                    app_logo.pack(fill=X, expand=TRUE)
                except:
                    # Fallback sem ícone
                    app_logo = Label(titulo_frame, text=f"Detalhes: {values[1]}", 
                                    anchor='w', font=('Ivy 15 bold'), 
                                    bg=self.colors['co0'], fg=self.colors['co1'], padx=10, pady=5)
                    app_logo.pack(fill=X, expand=TRUE)
            
            # Exibir detalhes no frame_detalhes
            if 'frame_detalhes' in self.frames:
                exibir_detalhes_item(
                    frame_detalhes=self.frames['frame_detalhes'],
                    tipo=tipo,
                    item_id=item_id,
                    values=values,
                    colors=self.colors
                )
            
        except Exception as e:
            logger.exception(f"Erro ao processar seleção: {e}")
    
    def _editar_callback(self):
        """
        Callback de edição via menu contextual.
        """
        from tkinter import messagebox, Toplevel
        
        try:
            if not self.selected_item:
                messagebox.showwarning("Aviso", "Nenhum item selecionado")
                return
            
            tipo = self.selected_item.get('tipo')
            item_id = self.selected_item.get('id')
            
            if not self.janela:
                messagebox.showerror("Erro", "Janela principal não disponível")
                return
            
            if tipo == 'Aluno':
                from InterfaceEdicaoAluno import InterfaceEdicaoAluno
                
                # Criar janela Toplevel para edição
                janela_edicao = Toplevel(self.janela)
                
                # Abrir interface de edição
                InterfaceEdicaoAluno(janela_edicao, item_id, janela_principal=self.janela)
                logger.info(f"Interface de edição aberta para aluno {item_id}")
                    
            elif tipo == 'Funcionário':
                from InterfaceEdicaoFuncionario import InterfaceEdicaoFuncionario
                
                # Criar janela Toplevel para edição
                janela_edicao = Toplevel(self.janela)
                
                # Abrir interface de edição
                InterfaceEdicaoFuncionario(janela_edicao, item_id, janela_principal=self.janela)
                logger.info(f"Interface de edição aberta para funcionário {item_id}")
                    
        except Exception as e:
            logger.exception(f"Erro ao editar item: {e}")
            messagebox.showerror("Erro", f"Erro ao editar: {e}")
    
    def on_close(self):
        """Handler para o fechamento da janela."""
        logger.debug("Fechando aplicação...")
        
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
            logger.debug("Connection pool fechado")
        except Exception as e:
            logger.error(f"Erro ao fechar connection pool: {e}")
        
        # Destruir janela (assegurar que 'janela' foi inicializada)
        assert self.janela is not None, "Janela não inicializada ao fechar"
        self.janela.destroy()
        logger.debug("Aplicação encerrada")
    
    def _enable_readonly_mode(self):
        """
        Ativa o modo somente leitura, desabilitando botões de edição.
        """
        try:
            # Desabilitar botões de edição via ButtonFactory
            if self.button_factory:
                # Obter referência aos botões do ButtonFactory
                botoes_frame = self.frames.get('frame_dados')
                if botoes_frame:
                    for widget in botoes_frame.winfo_children():
                        # Desabilitar botões que não sejam de consulta
                        if hasattr(widget, 'configure'):
                            text = widget.cget('text') if hasattr(widget, 'cget') else ''
                            # Manter apenas botões de visualização/consulta
                            if any(palavra in text.lower() for palavra in ['adicionar', 'editar', 'excluir', 'novo', 'cadastrar']):
                                widget.configure(state='disabled')
            
            # Desabilitar menus de edição
            if self.menu_manager:
                # Implementar desabilitação de itens de menu se necessário
                pass
            
            # Atualizar título da janela
            if self.janela:
                titulo_atual = self.janela.title()
                self.janela.title(f"{titulo_atual} [SOMENTE LEITURA]")
            
            logger.info("✓ Modo somente leitura ativado - funções de edição desabilitadas")
            
        except Exception as e:
            logger.error(f"Erro ao ativar modo somente leitura: {e}")
    
    def setup_backup(self, test_mode: bool = False):
        """
        Configura e inicia o sistema de backup automático.
        
        Args:
            test_mode: Se True, não inicia o backup automático
        """
        # Verificar modo de teste via parâmetro ou settings
        is_test_mode = test_mode
        if settings and settings.app.test_mode:
            is_test_mode = True
        
        # Verificar se backup está habilitado via settings
        backup_enabled = True
        if settings:
            backup_enabled = settings.backup.enabled
        
        if is_test_mode:
            logger.warning("⚠️ SISTEMA EM MODO DE TESTE - Backups automáticos desabilitados")
            return
        
        if not backup_enabled:
            logger.info("ℹ️ Sistema de backup desabilitado via configuração")
            return
        
        try:
            import Seguranca
            logger.debug("Iniciando sistema de backup automático...")
            Seguranca.iniciar_backup_automatico()
            logger.debug("✓ Sistema de backup iniciado")
        except Exception as e:
            logger.error(f"Erro ao iniciar backup automático: {e}")
            # Não propagar erro - permitir que aplicação continue sem backup
    
    def on_close_with_backup(self, test_mode: bool = False):
        """
        Handler de fechamento que inclui backup automático.
        
        Args:
            test_mode: Se True, não executa backup final
        """
        # Verificar modo de teste via parâmetro ou settings
        is_test_mode = test_mode
        if settings and settings.app.test_mode:
            is_test_mode = True
        
        # Parar o sistema de backup automático e executar backup final
        if not is_test_mode:
            try:
                import Seguranca
                logger.info("Executando backup final antes de fechar...")
                Seguranca.parar_backup_automatico(executar_backup_final=True)
            except Exception as e:
                logger.error(f"Erro ao executar backup final: {e}")
                # Não bloquear o fechamento por causa de erro no backup
        
        # Chamar o handler padrão de fechamento
        self.on_close()
    
    def initialize(self):
        """
        Inicializa todos os componentes da aplicação em sequência.
        
        Este método orquestra toda a configuração da interface:
        - Frames principais
        - Logo e cabeçalho
        - Callbacks de ações
        - Botões e menus
        - Barra de pesquisa
        - Tabela principal
        - Rodapé
        - Dashboard
        - Menu contextual
        
        Este método deve ser chamado após a criação da instância Application
        e antes de run().
        """
        logger.debug("Inicializando componentes da aplicação...")
        
        # Adicionar referência ao app na janela para acesso pelos callbacks
        if self.janela:
            setattr(self.janela, '_app_instance', self)  # type: ignore
        
        # 1. Configurar frames principais
        logger.debug("Configurando frames...")
        self.setup_frames()
        
        # 2. Configurar logo
        logger.debug("Configurando logo...")
        self.setup_logo()
        
        # 3. Configurar callbacks de ações
        logger.debug("Configurando action callbacks...")
        self.setup_action_callbacks(atualizar_tabela_callback=None)
        
        # 4. Configurar botões e menus usando ButtonFactory
        logger.debug("Configurando botões e menus...")
        self.setup_action_buttons_and_menus()
        
        # 5. Configurar barra de pesquisa
        logger.debug("Configurando pesquisa...")
        self.setup_search(callback_pesquisa=self._pesquisar_callback)
        
        # 6. Configurar tabela principal
        logger.debug("Configurando tabela...")
        self.setup_table(
            on_select_callback=self._on_select_callback,
            on_keyboard_callback=None
        )
        
        # 7. Configurar rodapé
        logger.debug("Configurando rodapé...")
        self.setup_footer()
        
        # 8. Configurar e exibir dashboard automaticamente (otimizado)
        logger.debug("Configurando dashboard...")
        self.setup_dashboard(criar_agora=True)
        
        # 9. Configurar menu contextual
        logger.debug("Configurando menu contextual...")
        self.setup_context_menu(editar_callback=self._editar_callback)
        
        # 10. Aplicar modo somente leitura se necessário
        if self.readonly_mode:
            logger.info("Aplicando modo somente leitura...")
            self._enable_readonly_mode()
        
        # Mensagem de sucesso (resumida)
        logger.info("Sistema inicializado com sucesso")
    
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
