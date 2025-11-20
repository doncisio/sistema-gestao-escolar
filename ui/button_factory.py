"""
Factory para criação de botões e menus da aplicação.

Este módulo extrai a lógica de criação de botões da função criar_acoes()
do main.py, organizando em uma classe reutilizável e testável.
"""

from tkinter import Frame, Button, Menu, LEFT, RIGHT, RIDGE, X, EW
from tkinter import messagebox
from PIL import Image, ImageTk
from typing import Optional, Callable, Dict, Any
from config_logs import get_logger

logger = get_logger(__name__)


class ButtonFactory:
    """
    Factory para criação de botões e menus da interface principal.
    
    Encapsula a lógica de criação de botões, menus e suas imagens,
    que antes estava na função criar_acoes() do main.py.
    """
    
    def __init__(self, janela, frame_dados, callbacks, colors: Dict[str, str]):
        """
        Inicializa o ButtonFactory.
        
        Args:
            janela: Janela principal Tk
            frame_dados: Frame onde os botões serão criados
            callbacks: Instância de ActionCallbacksManager com os callbacks
            colors: Dicionário com cores da aplicação (co0-co9)
        """
        self.janela = janela
        self.frame_dados = frame_dados
        self.callbacks = callbacks
        self.colors = colors
        
        # Armazenar referências de imagens para evitar garbage collection
        self._image_refs = {}
        
        logger.debug("ButtonFactory inicializado")
    
    def _load_image(self, path: str, size: tuple = (18, 18)) -> Optional[Any]:
        """
        Carrega e redimensiona uma imagem.
        
        Args:
            path: Caminho do arquivo de imagem
            size: Tupla (largura, altura) para redimensionamento
            
        Returns:
            ImageTk.PhotoImage ou None se não encontrado
        """
        try:
            img = Image.open(path)
            img = img.resize(size)
            photo = ImageTk.PhotoImage(img)
            # Armazenar referência
            self._image_refs[path] = photo
            return photo
        except FileNotFoundError:
            logger.warning(f"Imagem não encontrada: {path}")
            return None
        except Exception as e:
            logger.error(f"Erro ao carregar imagem {path}: {e}")
            return None
    
    def _create_button(self, parent, text: str, command: Callable, 
                       icon_path: Optional[str] = None, bg_color: Optional[str] = None,
                       **kwargs) -> Button:
        """
        Cria um botão com ou sem ícone.
        
        Args:
            parent: Widget pai onde o botão será criado
            text: Texto do botão
            command: Função callback ao clicar
            icon_path: Caminho opcional do ícone
            bg_color: Cor de fundo do botão
            **kwargs: Argumentos adicionais para Button()
            
        Returns:
            Button criado
        """
        # Configurações padrão
        btn_config = {
            'text': text,
            'command': command,
            'compound': LEFT,
            'overrelief': RIDGE,
            'font': ('Ivy 11'),
            'bg': bg_color or self.colors['co4'],
            'fg': self.colors['co0']
        }
        btn_config.update(kwargs)
        
        # Adicionar ícone se disponível
        if icon_path:
            img = self._load_image(icon_path)
            if img:
                btn_config['image'] = img
        
        btn = Button(parent, **btn_config)
        
        # Manter referência da imagem no botão
        if icon_path and icon_path in self._image_refs:
            btn._image_ref = self._image_refs[icon_path]  # type: ignore
        
        return btn
    
    def criar_botoes_principais(self) -> Frame:
        """
        Cria os botões principais da aplicação.
        
        Returns:
            Frame contendo os botões
        """
        # Frame para os botões de ação
        botoes_frame = Frame(self.frame_dados, bg=self.colors['co1'])
        botoes_frame.pack(fill=X, expand=True, padx=10, pady=5)
        
        # Configurar grid do frame de botões
        for i in range(7):  # 7 colunas para acomodar todos os botões
            botoes_frame.grid_columnconfigure(i, weight=1)
        
        # Botão Novo Aluno
        btn_aluno = self._create_button(
            botoes_frame,
            text="Novo Aluno",
            command=self.callbacks.cadastrar_novo_aluno,
            icon_path='icon/plus.png',
            bg_color=self.colors['co2']
        )
        btn_aluno.grid(row=0, column=0, padx=5, pady=5, sticky=EW)
        
        # Botão Novo Funcionário
        btn_funcionario = self._create_button(
            botoes_frame,
            text="Novo Funcionário",
            command=self.callbacks.cadastrar_novo_funcionario,
            icon_path='icon/video-conference.png',
            bg_color=self.colors['co3']
        )
        btn_funcionario.grid(row=0, column=1, padx=5, pady=5, sticky=EW)
        
        # Botão Histórico Escolar
        btn_historico = self._create_button(
            botoes_frame,
            text="Histórico Escolar",
            command=self.callbacks.abrir_historico_escolar,
            icon_path='icon/history.png',
            bg_color=self.colors['co4']
        )
        btn_historico.grid(row=0, column=2, padx=5, pady=5, sticky=EW)
        
        # Botão Administração
        btn_admin = self._create_button(
            botoes_frame,
            text="Administração",
            command=self.callbacks.abrir_interface_administrativa,
            icon_path='icon/settings.png',
            bg_color=self.colors['co5']
        )
        btn_admin.grid(row=0, column=3, padx=5, pady=5, sticky=EW)
        
        # Botão Backup
        btn_backup = self._create_button(
            botoes_frame,
            text="Backup",
            command=lambda: self._fazer_backup(),
            icon_path='icon/book.png',
            bg_color=self.colors['co6']
        )
        btn_backup.grid(row=0, column=4, padx=5, pady=5, sticky=EW)
        
        # Botão Restaurar
        btn_restaurar = self._create_button(
            botoes_frame,
            text="Restaurar",
            command=lambda: self._restaurar_backup(),
            icon_path='icon/restore.png',
            bg_color=self.colors['co9']
        )
        btn_restaurar.grid(row=0, column=5, padx=5, pady=5, sticky=EW)
        
        # Botão Horários
        btn_horarios = self._create_button(
            botoes_frame,
            text="Horários",
            command=self.callbacks.abrir_horarios_escolares,
            icon_path='icon/schedule.png',
            bg_color=self.colors['co3']
        )
        btn_horarios.grid(row=0, column=6, padx=5, pady=5, sticky=EW)
        
        logger.debug("Botões principais criados (7 botões)")
        return botoes_frame
    
    def _fazer_backup(self):
        """Callback para o botão de backup."""
        try:
            import Seguranca
            Seguranca.fazer_backup()
        except Exception as e:
            logger.exception(f"Erro ao fazer backup: {e}")
            messagebox.showerror("Erro", f"Erro ao fazer backup: {e}")
    
    def _restaurar_backup(self):
        """Callback para o botão de restaurar."""
        try:
            import Seguranca
            Seguranca.restaurar_backup()
        except Exception as e:
            logger.exception(f"Erro ao restaurar backup: {e}")
            messagebox.showerror("Erro", f"Erro ao restaurar backup: {e}")
    
    def criar_menu_bar(self) -> Menu:
        """
        Cria a barra de menus completa da aplicação.
        
        Returns:
            Menu configurado
        """
        menu_font = ('Ivy', 10)
        
        # Barra de menu principal
        menu_bar = Menu(self.janela)
        
        # Menu Cadastro
        cadastro_menu = Menu(menu_bar, tearoff=0, font=menu_font)
        cadastro_menu.add_command(
            label="Novo Aluno",
            command=self.callbacks.cadastrar_novo_aluno,
            font=menu_font
        )
        cadastro_menu.add_command(
            label="Novo Funcionário",
            command=self.callbacks.cadastrar_novo_funcionario,
            font=menu_font
        )
        menu_bar.add_cascade(label="Cadastro", menu=cadastro_menu, font=menu_font)
        
        # Menu Histórico
        historico_menu = Menu(menu_bar, tearoff=0, font=menu_font)
        historico_menu.add_command(
            label="Histórico Escolar",
            command=self.callbacks.abrir_historico_escolar,
            font=menu_font
        )
        menu_bar.add_cascade(label="Histórico", menu=historico_menu, font=menu_font)
        
        # Menu Relatórios
        relatorios_menu = Menu(menu_bar, tearoff=0, font=menu_font)
        
        # Submenu Listas
        listas_menu = Menu(relatorios_menu, tearoff=0, font=menu_font)
        listas_menu.add_command(
            label="Lista Atualizada",
            command=self.callbacks.lista_atualizada,
            font=menu_font
        )
        listas_menu.add_command(
            label="Lista Reunião",
            command=self.callbacks.lista_reuniao,
            font=menu_font
        )
        listas_menu.add_command(
            label="Lista de Notas",
            command=self.callbacks.lista_notas,
            font=menu_font
        )
        listas_menu.add_command(
            label="Lista de Frequências",
            command=self.callbacks.reports.lista_frequencia,
            font=menu_font
        )
        relatorios_menu.add_cascade(label="Listas", menu=listas_menu, font=menu_font)
        
        # Submenu Relatórios Gerais
        relatorios_gerais_menu = Menu(relatorios_menu, tearoff=0, font=menu_font)
        relatorios_gerais_menu.add_command(
            label="Contatos de Responsáveis",
            command=self.callbacks.relatorio_contatos_responsaveis,
            font=menu_font
        )
        relatorios_gerais_menu.add_command(
            label="Lista Alfabética",
            command=self.callbacks.reports.relatorio_lista_alfabetica,
            font=menu_font
        )
        relatorios_gerais_menu.add_command(
            label="Alunos com Transtornos",
            command=self.callbacks.reports.relatorio_alunos_transtornos,
            font=menu_font
        )
        relatorios_menu.add_cascade(
            label="Relatórios Gerais",
            menu=relatorios_gerais_menu,
            font=menu_font
        )
        
        menu_bar.add_cascade(label="Relatórios", menu=relatorios_menu, font=menu_font)
        
        # Menu Notas e Frequências
        notas_menu = Menu(menu_bar, tearoff=0, font=menu_font)
        notas_menu.add_command(
            label="Cadastrar/Editar Notas",
            command=self.callbacks.abrir_cadastro_notas,
            font=menu_font
        )
        notas_menu.add_command(
            label="Relatório de Notas",
            command=lambda: self._gerar_relatorio_notas_wrapper(),
            font=menu_font
        )
        notas_menu.add_command(
            label="Relatório de Notas com Assinatura",
            command=lambda: self._gerar_relatorio_notas_com_assinatura_wrapper(),
            font=menu_font
        )
        
        # Submenu Pendências
        pendencias_menu = Menu(notas_menu, tearoff=0, font=menu_font)
        pendencias_menu.add_command(
            label="Relatório Avançado",
            command=lambda: self._abrir_relatorio_avancado(),
            font=menu_font
        )
        pendencias_menu.add_command(
            label="Relatório de Pendências",
            command=lambda: self._abrir_relatorio_pendencias(),
            font=menu_font
        )
        notas_menu.add_cascade(
            label="Relatórios de Pendências",
            menu=pendencias_menu,
            font=menu_font
        )
        
        menu_bar.add_cascade(label="Notas e Frequências", menu=notas_menu, font=menu_font)
        
        # Menu Administração
        admin_menu = Menu(menu_bar, tearoff=0, font=menu_font)
        admin_menu.add_command(
            label="Interface Administrativa",
            command=self.callbacks.abrir_interface_administrativa,
            font=menu_font
        )
        admin_menu.add_command(
            label="Horários Escolares",
            command=self.callbacks.abrir_horarios_escolares,
            font=menu_font
        )
        admin_menu.add_command(
            label="Transição de Ano Letivo",
            command=self.callbacks.abrir_transicao_ano_letivo,
            font=menu_font
        )
        admin_menu.add_separator()
        admin_menu.add_command(
            label="Backup do Sistema",
            command=self._fazer_backup,
            font=menu_font
        )
        admin_menu.add_command(
            label="Restaurar Backup",
            command=self._restaurar_backup,
            font=menu_font
        )
        menu_bar.add_cascade(label="Administração", menu=admin_menu, font=menu_font)
        
        # Menu Documentos
        documentos_menu = Menu(menu_bar, tearoff=0, font=menu_font)
        documentos_menu.add_command(
            label="Gerenciador de Documentos",
            command=self.callbacks.abrir_gerenciador_documentos,
            font=menu_font
        )
        documentos_menu.add_command(
            label="Gerenciador de Licenças",
            command=self.callbacks.abrir_gerenciador_licencas,
            font=menu_font
        )
        documentos_menu.add_command(
            label="Gerar Declaração",
            command=lambda: self._gerar_declaracao_generica(),
            font=menu_font
        )
        menu_bar.add_cascade(label="Documentos", menu=documentos_menu, font=menu_font)
        
        logger.debug("Barra de menus criada (6 menus principais)")
        return menu_bar
    
    def _gerar_relatorio_notas_wrapper(self):
        """Wrapper para gerar relatório de notas"""
        try:
            from services.report_service import gerar_relatorio_notas
            gerar_relatorio_notas()
        except Exception as e:
            logger.exception(f"Erro ao gerar relatório de notas: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar relatório: {e}")
    
    def _gerar_relatorio_notas_com_assinatura_wrapper(self):
        """Wrapper para gerar relatório de notas com assinatura"""
        try:
            from abrir_relatorio_avancado_com_assinatura import main as gerar_relatorio_com_assinatura  # type: ignore
            gerar_relatorio_com_assinatura()
        except Exception as e:
            logger.exception(f"Erro ao gerar relatório de notas: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar relatório: {e}")
    
    def _abrir_relatorio_avancado(self):
        """Wrapper para abrir relatório avançado"""
        try:
            from abrir_relatorio_avancado_com_assinatura import main as abrir_relatorio_avancado  # type: ignore
            abrir_relatorio_avancado()
        except Exception as e:
            logger.exception(f"Erro ao abrir relatório avançado: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir relatório: {e}")
    
    def _abrir_relatorio_pendencias(self):
        """Wrapper para abrir relatório de pendências"""
        try:
            from services.report_service import gerar_relatorio_pendencias
            # TODO: Adicionar parâmetros apropriados
            logger.warning("Relatório de pendências precisa de implementação dos parâmetros")
            messagebox.showinfo("Info", "Função em implementação - parâmetros necessários")
        except Exception as e:
            logger.exception(f"Erro ao abrir relatório de pendências: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir relatório: {e}")
    
    def _gerar_declaracao_generica(self):
        """Wrapper para gerar declaração genérica"""
        try:
            from Gerar_Declaracao_Aluno import main as gerar_declaracao  # type: ignore
            gerar_declaracao()
        except Exception as e:
            logger.exception(f"Erro ao gerar declaração: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar declaração: {e}")
    
    def configurar_interface(self):
        """
        Configura a interface completa (botões + menus).
        
        Este é o método principal que deve ser chamado para criar
        toda a interface de ações da aplicação.
        """
        # Criar botões principais
        self.criar_botoes_principais()
        
        # Criar e configurar barra de menus
        menu_bar = self.criar_menu_bar()
        self.janela.config(menu=menu_bar)
        
        logger.info("Interface de ações configurada (botões + menus)")

