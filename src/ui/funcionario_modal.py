"""
Modal para edição de funcionário.
Segue o padrão estabelecido em MatriculaModal para reutilização e desacoplamento.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional, Callable
from src.core.config_logs import get_logger
from src.services.funcionario_service import (
    obter_funcionario_por_id,
    atualizar_funcionario
)

logger = get_logger(__name__)


class FuncionarioModal:
    """Modal para edição de dados de funcionário."""
    
    def __init__(
        self,
        parent: tk.Tk,
        funcionario_id: int,
        colors: Dict[str, str],
        callback_sucesso: Optional[Callable[[], None]] = None
    ):
        """
        Inicializa o modal de edição de funcionário.
        
        Args:
            parent: Janela pai
            funcionario_id: ID do funcionário a ser editado
            colors: Dicionário com cores da aplicação
            callback_sucesso: Callback executado após sucesso
        """
        self.parent = parent
        self.funcionario_id = funcionario_id
        self.colors = colors
        self.callback_sucesso = callback_sucesso
        
        # Dados do funcionário
        self.funcionario_data: Optional[Dict] = None
        
        # Widgets
        self.janela: Optional[tk.Toplevel] = None
        self.nome_var: Optional[tk.StringVar] = None
        self.cpf_var: Optional[tk.StringVar] = None
        self.cargo_var: Optional[tk.StringVar] = None
        self.email_var: Optional[tk.StringVar] = None
        self.telefone_var: Optional[tk.StringVar] = None
        
        # Carrega dados e cria interface
        self._carregar_dados()
        if self.funcionario_data:
            self._criar_interface()
    
    def _carregar_dados(self) -> None:
        """Carrega dados do funcionário do banco."""
        try:
            resultado = obter_funcionario_por_id(self.funcionario_id)
            
            if not resultado:
                messagebox.showerror(
                    "Erro",
                    f"Funcionário com ID {self.funcionario_id} não encontrado"
                )
                logger.warning(f"Funcionário {self.funcionario_id} não encontrado")
                return
            
            self.funcionario_data = resultado
            logger.info(f"Dados do funcionário {self.funcionario_id} carregados com sucesso")
            
        except Exception as e:
            logger.exception(f"Exceção ao carregar dados do funcionário {self.funcionario_id}")
            messagebox.showerror(
                "Erro",
                f"Erro inesperado ao carregar funcionário: {str(e)}"
            )
    
    def _criar_interface(self) -> None:
        """Cria a interface do modal."""
        if not self.funcionario_data:
            logger.error("Tentativa de criar interface sem dados do funcionário")
            return
        
        # Criar janela modal
        self.janela = tk.Toplevel(self.parent)
        self.janela.title("Editar Funcionário")
        self.janela.geometry("500x400")
        self.janela.configure(bg=self.colors['co1'])
        self.janela.resizable(False, False)
        self.janela.transient(self.parent)
        self.janela.grab_set()
        
        # Centralizar janela
        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.janela.winfo_screenheight() // 2) - (400 // 2)
        self.janela.geometry(f"500x400+{x}+{y}")
        
        # Frame principal
        frame_main = tk.Frame(self.janela, bg=self.colors['co1'])
        frame_main.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título
        titulo = tk.Label(
            frame_main,
            text=f"Editar Funcionário - {self.funcionario_data.get('nome', 'N/A')}",
            font=('Ivy', 14, 'bold'),
            bg=self.colors['co1'],
            fg=self.colors['co0']
        )
        titulo.pack(pady=(0, 20))
        
        # Frame de formulário
        frame_form = tk.Frame(frame_main, bg=self.colors['co1'])
        frame_form.pack(fill='both', expand=True)
        
        # Campos do formulário
        self._criar_campo(frame_form, "Nome:", "nome", 0)
        self._criar_campo(frame_form, "CPF:", "cpf", 1, readonly=True)
        self._criar_campo(frame_form, "Cargo:", "cargo", 2)
        self._criar_campo(frame_form, "E-mail:", "email", 3)
        self._criar_campo(frame_form, "Telefone:", "telefone", 4)
        
        # Frame de botões
        frame_botoes = tk.Frame(frame_main, bg=self.colors['co1'])
        frame_botoes.pack(pady=(20, 0))
        
        # Botão Cancelar
        btn_cancelar = tk.Button(
            frame_botoes,
            text="Cancelar",
            command=self.janela.destroy,
            width=12,
            bg=self.colors['co4'],
            fg=self.colors['co0'],
            font=('Ivy', 10, 'bold'),
            relief='raised',
            overrelief='ridge'
        )
        btn_cancelar.pack(side='left', padx=5)
        
        # Botão Salvar
        btn_salvar = tk.Button(
            frame_botoes,
            text="Salvar",
            command=self._salvar_alteracoes,
            width=12,
            bg=self.colors['co2'],
            fg=self.colors['co0'],
            font=('Ivy', 10, 'bold'),
            relief='raised',
            overrelief='ridge'
        )
        btn_salvar.pack(side='left', padx=5)
        
        logger.info(f"Interface do modal de edição criada para funcionário {self.funcionario_id}")
    
    def _criar_campo(
        self, 
        parent: tk.Frame, 
        label: str, 
        campo: str, 
        row: int,
        readonly: bool = False
    ) -> None:
        """
        Cria um campo do formulário.
        
        Args:
            parent: Frame pai
            label: Texto do label
            campo: Nome do campo no dicionário de dados
            row: Linha do grid
            readonly: Se True, campo é somente leitura
        """
        # Label
        lbl = tk.Label(
            parent,
            text=label,
            font=('Ivy', 10),
            bg=self.colors['co1'],
            fg=self.colors['co0'],
            anchor='w'
        )
        lbl.grid(row=row, column=0, sticky='w', pady=5, padx=(0, 10))
        
        # Entry
        valor_campo = self.funcionario_data.get(campo, '') if self.funcionario_data else ''
        var = tk.StringVar(value=valor_campo)
        entry = tk.Entry(
            parent,
            textvariable=var,
            font=('Ivy', 10),
            width=35,
            state='readonly' if readonly else 'normal'
        )
        entry.grid(row=row, column=1, sticky='ew', pady=5)
        
        # Armazena variável
        if campo == 'nome':
            self.nome_var = var
        elif campo == 'cpf':
            self.cpf_var = var
        elif campo == 'cargo':
            self.cargo_var = var
        elif campo == 'email':
            self.email_var = var
        elif campo == 'telefone':
            self.telefone_var = var
        
        # Configura expansão da coluna
        parent.grid_columnconfigure(1, weight=1)
    
    def _salvar_alteracoes(self) -> None:
        """Salva as alterações do funcionário."""
        try:
            # Validações
            if not self.nome_var or not self.nome_var.get().strip():
                messagebox.showwarning(
                    "Atenção",
                    "O nome do funcionário é obrigatório"
                )
                return
            
            if not self.cargo_var or not self.cargo_var.get().strip():
                messagebox.showwarning(
                    "Atenção",
                    "O cargo do funcionário é obrigatório"
                )
                return
            
            # Prepara dados para atualização
            nome = self.nome_var.get().strip()
            cargo = self.cargo_var.get().strip()
            email = self.email_var.get().strip() if self.email_var else ''
            telefone = self.telefone_var.get().strip() if self.telefone_var else ''
            
            # Chama serviço
            sucesso, mensagem = atualizar_funcionario(
                self.funcionario_id,
                nome=nome,
                cargo=cargo,
                email=email,
                telefone=telefone
            )
            
            if not sucesso:
                messagebox.showerror("Erro", mensagem)
                logger.error(f"Erro ao atualizar funcionário {self.funcionario_id}: {mensagem}")
                return
            
            # Sucesso
            messagebox.showinfo("Sucesso", mensagem)
            logger.info(f"Funcionário {self.funcionario_id} atualizado com sucesso")
            
            # Executa callback
            if self.callback_sucesso:
                self.callback_sucesso()
            
            # Fecha modal
            if self.janela:
                self.janela.destroy()
            
        except Exception as e:
            logger.exception(f"Exceção ao salvar alterações do funcionário {self.funcionario_id}")
            messagebox.showerror(
                "Erro",
                f"Erro inesperado ao salvar: {str(e)}"
            )


def abrir_funcionario_modal(
    parent: tk.Tk,
    funcionario_id: int,
    colors: Dict[str, str],
    callback_sucesso: Optional[Callable[[], None]] = None
) -> None:
    """
    Função helper para abrir o modal de edição de funcionário.
    
    Args:
        parent: Janela pai
        funcionario_id: ID do funcionário a ser editado
        colors: Dicionário com cores da aplicação
        callback_sucesso: Callback executado após sucesso
    """
    FuncionarioModal(parent, funcionario_id, colors, callback_sucesso)
