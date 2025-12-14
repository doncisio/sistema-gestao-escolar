"""
Diálogos reutilizáveis para seleção de períodos e configuração de relatórios.
"""
import tkinter as tk
from tkinter import ttk, messagebox, StringVar, IntVar, Frame, Label, Button, Entry, Checkbutton
from typing import Optional, List, Dict, Callable, Tuple
from src.core.config_logs import get_logger

logger = get_logger(__name__)


class SeletorMesDialog:
    """Diálogo para seleção de mês."""
    
    def __init__(
        self,
        parent: tk.Tk,
        titulo: str,
        callback: Callable[[int], None],
        colors: Dict[str, str]
    ):
        """
        Inicializa o diálogo de seleção de mês.
        
        Args:
            parent: Janela pai
            titulo: Título do diálogo
            callback: Função chamada com o mês selecionado (1-12)
            colors: Dicionário com cores
        """
        self.callback = callback
        self.colors = colors
        
        # Criar diálogo
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(titulo)
        self.dialog.geometry("300x200")
        self.dialog.configure(bg=colors['co1'])
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centralizar
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (200 // 2)
        self.dialog.geometry(f"300x200+{x}+{y}")
        
        self._criar_interface()
    
    def _criar_interface(self) -> None:
        """Cria a interface do diálogo."""
        # Label
        Label(
            self.dialog,
            text="Selecione o mês:",
            font=('Ivy', 12),
            bg=self.colors['co1'],
            fg=self.colors['co0']
        ).pack(pady=20)
        
        # Combobox de meses
        self.mes_var = StringVar()
        meses = [
            "Janeiro", "Fevereiro", "Março", "Abril",
            "Maio", "Junho", "Julho", "Agosto",
            "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        
        mes_combo = ttk.Combobox(
            self.dialog,
            textvariable=self.mes_var,
            values=meses,
            state='readonly',
            width=20,
            font=('Ivy', 10)
        )
        mes_combo.pack(pady=10)
        mes_combo.current(0)  # Selecionar Janeiro por padrão
        
        # Botões
        frame_botoes = Frame(self.dialog, bg=self.colors['co1'])
        frame_botoes.pack(pady=20)
        
        Button(
            frame_botoes,
            text="Cancelar",
            command=self.dialog.destroy,
            width=10,
            bg=self.colors['co4'],
            fg=self.colors['co0'],
            font=('Ivy', 10)
        ).pack(side='left', padx=5)
        
        Button(
            frame_botoes,
            text="Confirmar",
            command=self._confirmar,
            width=10,
            bg=self.colors['co2'],
            fg=self.colors['co0'],
            font=('Ivy', 10, 'bold')
        ).pack(side='left', padx=5)
    
    def _confirmar(self) -> None:
        """Confirma a seleção."""
        try:
            mes_nome = self.mes_var.get()
            meses = [
                "Janeiro", "Fevereiro", "Março", "Abril",
                "Maio", "Junho", "Julho", "Agosto",
                "Setembro", "Outubro", "Novembro", "Dezembro"
            ]
            mes_numero = meses.index(mes_nome) + 1
            
            self.dialog.destroy()
            self.callback(mes_numero)
            
        except Exception as e:
            logger.exception("Erro ao confirmar seleção de mês")
            messagebox.showerror("Erro", f"Erro ao processar seleção: {str(e)}")


class SeletorBimestreDialog:
    """Diálogo para seleção de bimestre."""
    
    def __init__(
        self,
        parent: tk.Tk,
        titulo: str,
        callback: Callable[[int, bool], None],
        colors: Dict[str, str],
        permitir_nulos: bool = True
    ):
        """
        Inicializa o diálogo de seleção de bimestre.
        
        Args:
            parent: Janela pai
            titulo: Título do diálogo
            callback: Função chamada com (bimestre, preencher_nulos)
            colors: Dicionário com cores
            permitir_nulos: Se permite opção de preencher nulos
        """
        self.callback = callback
        self.colors = colors
        self.permitir_nulos = permitir_nulos
        
        # Criar diálogo
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(titulo)
        self.dialog.geometry("300x250" if permitir_nulos else "300x200")
        self.dialog.configure(bg=colors['co1'])
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centralizar
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (250 // 2)
        self.dialog.geometry(f"300x250+{x}+{y}" if permitir_nulos else f"300x200+{x}+{y}")
        
        self._criar_interface()
    
    def _criar_interface(self) -> None:
        """Cria a interface do diálogo."""
        # Label
        Label(
            self.dialog,
            text="Selecione o bimestre:",
            font=('Ivy', 12),
            bg=self.colors['co1'],
            fg=self.colors['co0']
        ).pack(pady=20)
        
        # Combobox de bimestres
        self.bimestre_var = StringVar()
        bimestres = ["1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"]
        
        bimestre_combo = ttk.Combobox(
            self.dialog,
            textvariable=self.bimestre_var,
            values=bimestres,
            state='readonly',
            width=20,
            font=('Ivy', 10)
        )
        bimestre_combo.pack(pady=10)
        bimestre_combo.current(0)
        
        # Checkbox preencher nulos
        if self.permitir_nulos:
            self.preencher_nulos_var = IntVar(value=0)
            Checkbutton(
                self.dialog,
                text="Preencher campos vazios com '-'",
                variable=self.preencher_nulos_var,
                bg=self.colors['co1'],
                fg=self.colors['co0'],
                font=('Ivy', 9),
                selectcolor=self.colors['co9']
            ).pack(pady=5)
        
        # Botões
        frame_botoes = Frame(self.dialog, bg=self.colors['co1'])
        frame_botoes.pack(pady=20)
        
        Button(
            frame_botoes,
            text="Cancelar",
            command=self.dialog.destroy,
            width=10,
            bg=self.colors['co4'],
            fg=self.colors['co0'],
            font=('Ivy', 10)
        ).pack(side='left', padx=5)
        
        Button(
            frame_botoes,
            text="Confirmar",
            command=self._confirmar,
            width=10,
            bg=self.colors['co2'],
            fg=self.colors['co0'],
            font=('Ivy', 10, 'bold')
        ).pack(side='left', padx=5)
    
    def _confirmar(self) -> None:
        """Confirma a seleção."""
        try:
            bimestre_texto = self.bimestre_var.get()
            bimestre = int(bimestre_texto[0])  # Pega o primeiro caractere (1, 2, 3 ou 4)
            
            preencher_nulos = bool(self.preencher_nulos_var.get()) if self.permitir_nulos else False
            
            self.dialog.destroy()
            self.callback(bimestre, preencher_nulos)
            
        except Exception as e:
            logger.exception("Erro ao confirmar seleção de bimestre")
            messagebox.showerror("Erro", f"Erro ao processar seleção: {str(e)}")


class SeletorAnoLetivoDialog:
    """Diálogo para seleção de ano letivo."""
    
    def __init__(
        self,
        parent: tk.Tk,
        titulo: str,
        callback: Callable[[int], None],
        colors: Dict[str, str],
        anos_disponiveis: Optional[List[int]] = None
    ):
        """
        Inicializa o diálogo de seleção de ano letivo.
        
        Args:
            parent: Janela pai
            titulo: Título do diálogo
            callback: Função chamada com o ano selecionado
            colors: Dicionário com cores
            anos_disponiveis: Lista de anos disponíveis (ou None para gerar automático)
        """
        self.callback = callback
        self.colors = colors
        
        if anos_disponiveis is None:
            from datetime import datetime
            ano_atual = datetime.now().year
            anos_disponiveis = list(range(ano_atual - 2, ano_atual + 3))
        
        self.anos = anos_disponiveis
        
        # Criar diálogo
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(titulo)
        self.dialog.geometry("300x200")
        self.dialog.configure(bg=colors['co1'])
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centralizar
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (200 // 2)
        self.dialog.geometry(f"300x200+{x}+{y}")
        
        self._criar_interface()
    
    def _criar_interface(self) -> None:
        """Cria a interface do diálogo."""
        # Label
        Label(
            self.dialog,
            text="Selecione o ano letivo:",
            font=('Ivy', 12),
            bg=self.colors['co1'],
            fg=self.colors['co0']
        ).pack(pady=20)
        
        # Combobox de anos
        self.ano_var = StringVar()
        
        ano_combo = ttk.Combobox(
            self.dialog,
            textvariable=self.ano_var,
            values=[str(ano) for ano in self.anos],
            state='readonly',
            width=20,
            font=('Ivy', 10)
        )
        ano_combo.pack(pady=10)
        
        if self.anos:
            ano_combo.current(len(self.anos) // 2)  # Selecionar ano do meio
        
        # Botões
        frame_botoes = Frame(self.dialog, bg=self.colors['co1'])
        frame_botoes.pack(pady=20)
        
        Button(
            frame_botoes,
            text="Cancelar",
            command=self.dialog.destroy,
            width=10,
            bg=self.colors['co4'],
            fg=self.colors['co0'],
            font=('Ivy', 10)
        ).pack(side='left', padx=5)
        
        Button(
            frame_botoes,
            text="Confirmar",
            command=self._confirmar,
            width=10,
            bg=self.colors['co2'],
            fg=self.colors['co0'],
            font=('Ivy', 10, 'bold')
        ).pack(side='left', padx=5)
    
    def _confirmar(self) -> None:
        """Confirma a seleção."""
        try:
            ano = int(self.ano_var.get())
            self.dialog.destroy()
            self.callback(ano)
            
        except Exception as e:
            logger.exception("Erro ao confirmar seleção de ano")
            messagebox.showerror("Erro", f"Erro ao processar seleção: {str(e)}")


# Funções helper para criar diálogos facilmente
def selecionar_mes(parent: tk.Tk, titulo: str, callback: Callable[[int], None], colors: Dict[str, str]) -> None:
    """Abre diálogo de seleção de mês."""
    SeletorMesDialog(parent, titulo, callback, colors)


def selecionar_bimestre(
    parent: tk.Tk,
    titulo: str,
    callback: Callable[[int, bool], None],
    colors: Dict[str, str],
    permitir_nulos: bool = True
) -> None:
    """Abre diálogo de seleção de bimestre."""
    SeletorBimestreDialog(parent, titulo, callback, colors, permitir_nulos)


def selecionar_ano_letivo(
    parent: tk.Tk,
    titulo: str,
    callback: Callable[[int], None],
    colors: Dict[str, str],
    anos_disponiveis: Optional[List[int]] = None
) -> None:
    """Abre diálogo de seleção de ano letivo."""
    SeletorAnoLetivoDialog(parent, titulo, callback, colors, anos_disponiveis)
