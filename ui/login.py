"""
Tela de Login do Sistema de Gestão Escolar.

Esta tela é exibida quando a feature flag 'perfis_habilitados' está ativa.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
import os

from config_logs import get_logger
from auth import AuthService, UsuarioLogado, Usuario
from ui.colors import COLORS

logger = get_logger(__name__)


class LoginWindow:
    """
    Janela de login do sistema.
    
    Exibe formulário de login e retorna o usuário autenticado.
    """
    
    def __init__(self, on_success: Optional[Callable[[Usuario], None]] = None):
        """
        Inicializa a janela de login.
        
        Args:
            on_success: Callback chamado após login bem-sucedido
        """
        self.on_success = on_success
        self.usuario: Optional[Usuario] = None
        self.janela: Optional[tk.Tk] = None
        
        # Variáveis do formulário
        self.var_username = None
        self.var_senha = None
        self.var_mostrar_senha = None
        
    def mostrar(self) -> Optional[Usuario]:
        """
        Exibe a janela de login e aguarda autenticação.
        
        Returns:
            Usuario autenticado ou None se cancelado/fechado
        """
        self._criar_janela()
        # Garantir ao analisador de tipos que `self.janela` foi criado
        if self.janela is None:
            return None
        self.janela.mainloop()
        return self.usuario
    
    def _criar_janela(self):
        """Cria e configura a janela de login."""
        self.janela = tk.Tk()
        self.janela.title("Login - Sistema de Gestão Escolar")
        
        # Configurações da janela
        largura = 450
        altura = 400
        
        # Centralizar na tela
        screen_width = self.janela.winfo_screenwidth()
        screen_height = self.janela.winfo_screenheight()
        x = (screen_width - largura) // 2
        y = (screen_height - altura) // 2
        
        self.janela.geometry(f"{largura}x{altura}+{x}+{y}")
        self.janela.resizable(False, False)
        self.janela.configure(bg=COLORS.co1)
        
        # Ícone (se existir)
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'aa.ico')
            if os.path.exists(icon_path):
                self.janela.iconbitmap(icon_path)
        except:
            pass
        
        # Protocolo de fechamento
        self.janela.protocol("WM_DELETE_WINDOW", self._on_fechar)
        
        # Criar interface
        self._criar_header()
        self._criar_formulario()
        self._criar_rodape()
        
        # Foco no campo de usuário
        self.entry_username.focus_set()
        
        # Bind Enter para login
        self.janela.bind('<Return>', lambda e: self._fazer_login())
    
    def _criar_header(self):
        """Cria o cabeçalho com logo e título."""
        frame_header = tk.Frame(self.janela, bg=COLORS.co1)
        frame_header.pack(fill='x', pady=(30, 20))
        
        # Título principal
        tk.Label(
            frame_header,
            text="🏫 Sistema de Gestão Escolar",
            font=("Segoe UI", 18, "bold"),
            fg=COLORS.co0,
            bg=COLORS.co1
        ).pack()
        
        # Subtítulo
        tk.Label(
            frame_header,
            text="Faça login para continuar",
            font=("Segoe UI", 11),
            fg=COLORS.co9,
            bg=COLORS.co1
        ).pack(pady=(5, 0))
    
    def _criar_formulario(self):
        """Cria o formulário de login."""
        # Frame central com fundo branco
        frame_form = tk.Frame(
            self.janela,
            bg=COLORS.co0,
            padx=30,
            pady=25
        )
        frame_form.pack(fill='both', expand=True, padx=40)
        
        # Variáveis
        self.var_username = tk.StringVar()
        self.var_senha = tk.StringVar()
        self.var_mostrar_senha = tk.BooleanVar(value=False)
        
        # Campo Usuário
        tk.Label(
            frame_form,
            text="Usuário",
            font=("Segoe UI", 10, "bold"),
            fg=COLORS.co7,
            bg=COLORS.co0,
            anchor='w'
        ).pack(fill='x', pady=(0, 5))
        
        self.entry_username = ttk.Entry(
            frame_form,
            textvariable=self.var_username,
            font=("Segoe UI", 12),
            width=30
        )
        self.entry_username.pack(fill='x', pady=(0, 15), ipady=5)
        
        # Campo Senha
        tk.Label(
            frame_form,
            text="Senha",
            font=("Segoe UI", 10, "bold"),
            fg=COLORS.co7,
            bg=COLORS.co0,
            anchor='w'
        ).pack(fill='x', pady=(0, 5))
        
        # Frame para senha + mostrar
        frame_senha = tk.Frame(frame_form, bg=COLORS.co0)
        frame_senha.pack(fill='x', pady=(0, 10))
        
        self.entry_senha = ttk.Entry(
            frame_senha,
            textvariable=self.var_senha,
            font=("Segoe UI", 12),
            show="●"
        )
        self.entry_senha.pack(side='left', fill='x', expand=True, ipady=5)
        
        # Checkbox mostrar senha
        self.check_mostrar = ttk.Checkbutton(
            frame_form,
            text="Mostrar senha",
            variable=self.var_mostrar_senha,
            command=self._toggle_senha
        )
        self.check_mostrar.pack(anchor='w', pady=(0, 20))
        
        # Mensagem de erro (inicialmente oculta)
        self.label_erro = tk.Label(
            frame_form,
            text="",
            font=("Segoe UI", 9),
            fg=COLORS.co8,
            bg=COLORS.co0,
            wraplength=300
        )
        self.label_erro.pack(fill='x', pady=(0, 10))
        
        # Botão de login
        self.btn_login = tk.Button(
            frame_form,
            text="Entrar",
            font=("Segoe UI", 12, "bold"),
            fg=COLORS.co0,
            bg=COLORS.co4,
            activeforeground=COLORS.co0,
            activebackground=COLORS.co9,
            cursor="hand2",
            relief='flat',
            command=self._fazer_login,
            width=15,
            height=1
        )
        self.btn_login.pack(pady=(10, 0), ipady=5)
    
    def _criar_rodape(self):
        """Cria o rodapé com informações."""
        frame_rodape = tk.Frame(self.janela, bg=COLORS.co1)
        frame_rodape.pack(fill='x', pady=(0, 15))
        
        tk.Label(
            frame_rodape,
            text="© 2025 - Sistema de Gestão Escolar",
            font=("Segoe UI", 8),
            fg=COLORS.co9,
            bg=COLORS.co1
        ).pack()
    
    def _toggle_senha(self):
        """Alterna visibilidade da senha."""
        # Garantir que as variáveis de controle foram inicializadas
        assert self.var_mostrar_senha is not None
        assert hasattr(self, 'entry_senha')
        if self.var_mostrar_senha.get():
            self.entry_senha.configure(show="")
        else:
            self.entry_senha.configure(show="●")
    
    def _mostrar_erro(self, mensagem: str):
        """Exibe mensagem de erro."""
        self.label_erro.configure(text=f"⚠️ {mensagem}")
    
    def _limpar_erro(self):
        """Limpa mensagem de erro."""
        self.label_erro.configure(text="")
    
    def _fazer_login(self):
        """Processa tentativa de login."""
        # Garantir que variáveis de formulário e janela foram inicializadas
        assert self.var_username is not None
        assert self.var_senha is not None
        assert self.janela is not None

        username = self.var_username.get().strip()
        senha = self.var_senha.get()
        
        # Validação básica
        if not username:
            self._mostrar_erro("Digite seu nome de usuário")
            self.entry_username.focus_set()
            return
        
        if not senha:
            self._mostrar_erro("Digite sua senha")
            self.entry_senha.focus_set()
            return
        
        self._limpar_erro()
        
        # Desabilitar botão durante login
        self.btn_login.configure(state='disabled', text='Entrando...')
        self.janela.update()
        
        try:
            # Tentar login
            usuario, mensagem = AuthService.login(username, senha)
            
            if usuario:
                logger.info(f"Login bem-sucedido: {usuario.username}")
                
                # Armazenar no singleton
                UsuarioLogado.set_usuario(usuario)
                self.usuario = usuario
                
                # Verificar se precisa trocar senha
                if usuario.primeiro_acesso:
                    self._solicitar_troca_senha(usuario)
                else:
                    self._login_sucesso()
            else:
                self._mostrar_erro(mensagem)
                self.btn_login.configure(state='normal', text='Entrar')
                self.var_senha.set('')
                self.entry_senha.focus_set()
                
        except Exception as e:
            logger.exception(f"Erro no login: {e}")
            self._mostrar_erro("Erro interno ao fazer login")
            self.btn_login.configure(state='normal', text='Entrar')
    
    def _login_sucesso(self):
        """Processa login bem-sucedido."""
        if self.on_success and self.usuario:
            self.on_success(self.usuario)
        assert self.janela is not None
        self.janela.destroy()
    
    def _solicitar_troca_senha(self, usuario: Usuario):
        """Abre janela para trocar senha no primeiro acesso."""
        assert self.janela is not None
        self.janela.withdraw()  # Esconde janela de login
        
        troca = TrocaSenhaWindow(
            self.janela,
            usuario,
            primeiro_acesso=True
        )
        
        if troca.senha_alterada:
            self._login_sucesso()
        else:
            # Usuário cancelou, mostrar login novamente
            assert self.janela is not None
            self.janela.deiconify()
            self.usuario = None
            UsuarioLogado.limpar()
            self.btn_login.configure(state='normal', text='Entrar')
    
    def _on_fechar(self):
        """Handler para fechamento da janela."""
        self.usuario = None
        if self.janela is not None:
            self.janela.destroy()


class TrocaSenhaWindow:
    """
    Janela para troca de senha.
    
    Usada no primeiro acesso ou quando solicitado pelo usuário.
    """
    
    def __init__(self, parent: tk.Tk, usuario: Usuario, primeiro_acesso: bool = False):
        """
        Inicializa janela de troca de senha.
        
        Args:
            parent: Janela pai
            usuario: Usuário que está trocando senha
            primeiro_acesso: Se True, mostra mensagem especial
        """
        self.usuario = usuario
        self.primeiro_acesso = primeiro_acesso
        self.senha_alterada = False
        
        # Criar janela
        self.janela = tk.Toplevel(parent)
        self.janela.title("Alterar Senha")
        self.janela.transient(parent)
        self.janela.grab_set()
        
        # Configurações
        largura = 400
        altura = 380 if primeiro_acesso else 350
        
        screen_width = self.janela.winfo_screenwidth()
        screen_height = self.janela.winfo_screenheight()
        x = (screen_width - largura) // 2
        y = (screen_height - altura) // 2
        
        self.janela.geometry(f"{largura}x{altura}+{x}+{y}")
        self.janela.resizable(False, False)
        self.janela.configure(bg=COLORS.co0)
        
        self.janela.protocol("WM_DELETE_WINDOW", self._on_fechar)
        
        self._criar_interface()
        self.janela.wait_window()
    
    def _criar_interface(self):
        """Cria interface de troca de senha."""
        # Frame principal
        frame = tk.Frame(self.janela, bg=COLORS.co0, padx=30, pady=20)
        frame.pack(fill='both', expand=True)
        
        # Título
        titulo = "🔐 Primeiro Acesso" if self.primeiro_acesso else "🔐 Alterar Senha"
        tk.Label(
            frame,
            text=titulo,
            font=("Segoe UI", 14, "bold"),
            fg=COLORS.co1,
            bg=COLORS.co0
        ).pack(pady=(0, 10))
        
        # Mensagem para primeiro acesso
        if self.primeiro_acesso:
            tk.Label(
                frame,
                text="Por segurança, você precisa criar uma nova senha.",
                font=("Segoe UI", 10),
                fg=COLORS.co7,
                bg=COLORS.co0,
                wraplength=320
            ).pack(pady=(0, 15))
        
        # Variáveis
        self.var_senha_atual = tk.StringVar()
        self.var_nova_senha = tk.StringVar()
        self.var_confirmar = tk.StringVar()
        
        # Senha atual
        tk.Label(
            frame,
            text="Senha atual:",
            font=("Segoe UI", 10),
            fg=COLORS.co7,
            bg=COLORS.co0,
            anchor='w'
        ).pack(fill='x')
        
        self.entry_atual = ttk.Entry(
            frame,
            textvariable=self.var_senha_atual,
            font=("Segoe UI", 11),
            show="●"
        )
        self.entry_atual.pack(fill='x', pady=(2, 10), ipady=3)
        
        # Nova senha
        tk.Label(
            frame,
            text="Nova senha:",
            font=("Segoe UI", 10),
            fg=COLORS.co7,
            bg=COLORS.co0,
            anchor='w'
        ).pack(fill='x')
        
        ttk.Entry(
            frame,
            textvariable=self.var_nova_senha,
            font=("Segoe UI", 11),
            show="●"
        ).pack(fill='x', pady=(2, 10), ipady=3)
        
        # Confirmar senha
        tk.Label(
            frame,
            text="Confirmar nova senha:",
            font=("Segoe UI", 10),
            fg=COLORS.co7,
            bg=COLORS.co0,
            anchor='w'
        ).pack(fill='x')
        
        ttk.Entry(
            frame,
            textvariable=self.var_confirmar,
            font=("Segoe UI", 11),
            show="●"
        ).pack(fill='x', pady=(2, 10), ipady=3)
        
        # Requisitos da senha
        tk.Label(
            frame,
            text="Mínimo 8 caracteres, incluindo maiúsculas, minúsculas e números",
            font=("Segoe UI", 8),
            fg=COLORS.co7,
            bg=COLORS.co0
        ).pack(pady=(5, 15))
        
        # Mensagem de erro
        self.label_erro = tk.Label(
            frame,
            text="",
            font=("Segoe UI", 9),
            fg=COLORS.co8,
            bg=COLORS.co0,
            wraplength=320
        )
        self.label_erro.pack(pady=(0, 10))
        
        # Botões
        frame_btns = tk.Frame(frame, bg=COLORS.co0)
        frame_btns.pack(fill='x')
        
        tk.Button(
            frame_btns,
            text="Cancelar",
            font=("Segoe UI", 10),
            fg=COLORS.co7,
            bg=COLORS.co0,
            relief='groove',
            command=self._on_fechar,
            width=12
        ).pack(side='left', padx=(0, 10))
        
        self.btn_salvar = tk.Button(
            frame_btns,
            text="Salvar",
            font=("Segoe UI", 10, "bold"),
            fg=COLORS.co0,
            bg=COLORS.co4,
            relief='flat',
            command=self._salvar,
            width=12
        )
        self.btn_salvar.pack(side='right')
        
        self.entry_atual.focus_set()
        self.janela.bind('<Return>', lambda e: self._salvar())
    
    def _salvar(self):
        """Processa alteração de senha."""
        senha_atual = self.var_senha_atual.get()
        nova_senha = self.var_nova_senha.get()
        confirmar = self.var_confirmar.get()
        
        # Validações
        if not senha_atual:
            self.label_erro.configure(text="⚠️ Digite a senha atual")
            return
        
        if not nova_senha:
            self.label_erro.configure(text="⚠️ Digite a nova senha")
            return
        
        if nova_senha != confirmar:
            self.label_erro.configure(text="⚠️ As senhas não conferem")
            return
        
        # Validar força da senha
        from auth.password_utils import validar_forca_senha
        valida, msg = validar_forca_senha(nova_senha)
        if not valida:
            self.label_erro.configure(text=f"⚠️ {msg}")
            return
        
        self.label_erro.configure(text="")
        self.btn_salvar.configure(state='disabled', text='Salvando...')
        self.janela.update()
        
        # Tentar alterar
        sucesso, mensagem = AuthService.alterar_senha(
            self.usuario.id,
            senha_atual,
            nova_senha
        )
        
        if sucesso:
            self.senha_alterada = True
            messagebox.showinfo(
                "Senha Alterada",
                "Sua senha foi alterada com sucesso!",
                parent=self.janela
            )
            self.janela.destroy()
        else:
            self.label_erro.configure(text=f"⚠️ {mensagem}")
            self.btn_salvar.configure(state='normal', text='Salvar')
    
    def _on_fechar(self):
        """Handler para fechamento."""
        if self.primeiro_acesso:
            # No primeiro acesso, é obrigatório trocar
            if messagebox.askyesno(
                "Cancelar",
                "Você precisa alterar sua senha para continuar.\n\n"
                "Deseja realmente cancelar e sair do sistema?",
                parent=self.janela
            ):
                self.janela.destroy()
        else:
            self.janela.destroy()


def abrir_troca_senha(parent: tk.Tk, usuario: Usuario) -> bool:
    """
    Abre janela de troca de senha.
    
    Função auxiliar para ser chamada de outras partes do sistema.
    
    Args:
        parent: Janela pai
        usuario: Usuário que está trocando senha
        
    Returns:
        True se senha foi alterada, False caso contrário
    """
    troca = TrocaSenhaWindow(parent, usuario, primeiro_acesso=False)
    return troca.senha_alterada
