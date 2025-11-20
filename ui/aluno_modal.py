"""
Modal para edição de aluno.
Segue o padrão estabelecido em MatriculaModal e FuncionarioModal.
"""
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Optional, Callable
from config_logs import get_logger
from services.aluno_service import obter_aluno_por_id

logger = get_logger(__name__)


class AlunoModal:
    """Modal para edição de dados de aluno usando InterfaceEdicaoAluno."""
    
    def __init__(
        self,
        parent: tk.Tk,
        aluno_id: int,
        colors: Dict[str, str],
        callback_sucesso: Optional[Callable[[], None]] = None
    ):
        """
        Inicializa o modal de edição de aluno.
        
        Args:
            parent: Janela pai
            aluno_id: ID do aluno a ser editado
            colors: Dicionário com cores da aplicação
            callback_sucesso: Callback executado após sucesso
        """
        self.parent = parent
        self.aluno_id = aluno_id
        self.colors = colors
        self.callback_sucesso = callback_sucesso
        
        # Janela de edição
        self.janela_edicao: Optional[tk.Toplevel] = None
        
        # Verifica se aluno existe e abre interface
        self._abrir_interface()
    
    def _abrir_interface(self) -> None:
        """Abre a interface de edição do aluno."""
        try:
            # Verificar se aluno existe
            aluno = obter_aluno_por_id(self.aluno_id)
            if not aluno:
                messagebox.showerror(
                    "Erro",
                    f"Aluno com ID {self.aluno_id} não encontrado"
                )
                logger.warning(f"Aluno {self.aluno_id} não encontrado")
                return
            
            # Importar interface de edição
            from InterfaceEdicaoAluno import InterfaceEdicaoAluno
            
            # Criar janela modal
            self.janela_edicao = tk.Toplevel(self.parent)
            self.janela_edicao.title(f"Editar Aluno - ID: {self.aluno_id}")
            self.janela_edicao.geometry('950x670')
            self.janela_edicao.configure(background=self.colors['co1'])
            self.janela_edicao.focus_set()
            self.janela_edicao.grab_set()  # Modal
            
            # Esconder janela pai
            self.parent.withdraw()
            
            # Criar interface de edição
            app_edicao = InterfaceEdicaoAluno(
                self.janela_edicao,
                self.aluno_id,
                janela_principal=self.parent
            )
            
            # Configurar fechamento
            self.janela_edicao.protocol("WM_DELETE_WINDOW", self._ao_fechar)
            
            logger.info(f"Interface de edição aberta para aluno {self.aluno_id}")
            
        except ImportError as e:
            logger.exception("Erro ao importar InterfaceEdicaoAluno")
            messagebox.showerror(
                "Erro",
                f"Erro ao carregar interface de edição: {str(e)}"
            )
            self._restaurar_janela_pai()
            
        except Exception as e:
            logger.exception(f"Erro ao abrir interface de edição do aluno {self.aluno_id}")
            messagebox.showerror(
                "Erro",
                f"Erro ao abrir interface de edição: {str(e)}"
            )
            self._restaurar_janela_pai()
    
    def _ao_fechar(self) -> None:
        """Callback executado ao fechar a janela de edição."""
        try:
            # Restaurar janela pai
            self._restaurar_janela_pai()
            
            # Executar callback de sucesso
            if self.callback_sucesso:
                self.callback_sucesso()
            
            # Destruir janela de edição
            if self.janela_edicao:
                self.janela_edicao.destroy()
            
            logger.info(f"Interface de edição fechada para aluno {self.aluno_id}")
            
        except Exception as e:
            logger.exception("Erro ao fechar interface de edição")
            self._restaurar_janela_pai()
    
    def _restaurar_janela_pai(self) -> None:
        """Restaura a visibilidade da janela pai."""
        try:
            if self.parent:
                self.parent.deiconify()
        except Exception as e:
            logger.exception("Erro ao restaurar janela pai")


def abrir_aluno_modal(
    parent: tk.Tk,
    aluno_id: int,
    colors: Dict[str, str],
    callback_sucesso: Optional[Callable[[], None]] = None
) -> None:
    """
    Função helper para abrir o modal de edição de aluno.
    
    Args:
        parent: Janela pai
        aluno_id: ID do aluno a ser editado
        colors: Dicionário com cores da aplicação
        callback_sucesso: Callback executado após sucesso
    """
    AlunoModal(parent, aluno_id, colors, callback_sucesso)
