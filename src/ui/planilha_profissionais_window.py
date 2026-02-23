"""
Interface para selecionar professores e servidores que assinaram os termos do Programa Cuidar dos Olhos.
"""

from tkinter import Toplevel, Frame, Label, Button, messagebox, Scrollbar, Canvas
from tkinter.ttk import Checkbutton
import tkinter as tk

from src.ui.colors import COLORS
from src.core.config_logs import get_logger
from src.relatorios.geradores.termo_cuidar_olhos import obter_professores_ativos, obter_servidores_ativos

logger = get_logger(__name__)


class PlanilhaProfissionaisWindow:
    """Janela para selecionar professores e servidores que assinaram os termos."""
    
    def __init__(self, janela_pai):
        """
        Inicializa a janela de seleção de profissionais.
        
        Args:
            janela_pai: Janela pai do Tkinter
        """
        self.janela_pai = janela_pai
        self.janela = Toplevel(janela_pai)
        self.janela.title("Planilha de Professores/Servidores - Cuidar dos Olhos")
        self.janela.geometry("900x700")
        self.janela.configure(bg=COLORS.co1)
        
        # Centralizar na tela
        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.janela.winfo_screenheight() // 2) - (700 // 2)
        self.janela.geometry(f"900x700+{x}+{y}")
        
        # Dados
        self.profissionais = []  # Lista de tuplas (funcionario, var_checkbox)
        
        # Criar interface
        self._criar_widgets()
        
        # Carregar dados
        self._carregar_dados()
    
    def _criar_widgets(self):
        """Cria os widgets da interface."""
        # Frame principal
        frame_principal = Frame(self.janela, bg=COLORS.co1, padx=20, pady=20)
        frame_principal.pack(fill='both', expand=True)
        
        # Título
        Label(
            frame_principal,
            text="Planilha de Levantamento - Professores e Servidores",
            font=("Arial", 16, "bold"),
            bg=COLORS.co1,
            fg=COLORS.co0
        ).pack(pady=(0, 10))
        
        Label(
            frame_principal,
            text="Selecione os professores e servidores que assinaram os termos",
            font=("Arial", 11),
            bg=COLORS.co1,
            fg=COLORS.co0
        ).pack(pady=(0, 20))
        
        # Frame de botões de ação rápida
        frame_acoes = Frame(frame_principal, bg=COLORS.co1)
        frame_acoes.pack(fill='x', pady=(0, 10))
        
        Button(
            frame_acoes,
            text="Selecionar Todos",
            font=("Arial", 10, "bold"),
            bg=COLORS.co4,
            fg=COLORS.co0,
            command=self._selecionar_todos,
            width=15
        ).pack(side='left', padx=5)
        
        Button(
            frame_acoes,
            text="Desmarcar Todos",
            font=("Arial", 10, "bold"),
            bg=COLORS.co6,
            fg=COLORS.co0,
            command=self._desmarcar_todos,
            width=15
        ).pack(side='left', padx=5)
        
        Label(
            frame_acoes,
            text="Total de profissionais:",
            font=("Arial", 10),
            bg=COLORS.co1,
            fg=COLORS.co0
        ).pack(side='right', padx=5)
        
        self.label_total = Label(
            frame_acoes,
            text="0",
            font=("Arial", 10, "bold"),
            bg=COLORS.co1,
            fg=COLORS.co4
        )
        self.label_total.pack(side='right')
        
        # Frame com scroll para lista de profissionais
        frame_lista = Frame(frame_principal, bg=COLORS.co0)
        frame_lista.pack(fill='both', expand=True, pady=(0, 20))
        
        # Canvas e Scrollbar
        canvas = Canvas(frame_lista, bg=COLORS.co0, highlightthickness=0)
        scrollbar = Scrollbar(frame_lista, orient="vertical", command=canvas.yview)
        self.frame_checkboxes = Frame(canvas, bg=COLORS.co0)
        
        self.frame_checkboxes.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.frame_checkboxes, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame de botões finais
        frame_botoes = Frame(frame_principal, bg=COLORS.co1)
        frame_botoes.pack(fill='x')
        
        Button(
            frame_botoes,
            text="Gerar Planilha PDF",
            font=("Arial", 12, "bold"),
            bg=COLORS.co4,
            fg=COLORS.co0,
            command=self._gerar_planilha,
            width=20,
            height=2
        ).pack(side='left', padx=5)
        
        Button(
            frame_botoes,
            text="Cancelar",
            font=("Arial", 12, "bold"),
            bg=COLORS.co6,
            fg=COLORS.co0,
            command=self.janela.destroy,
            width=15,
            height=2
        ).pack(side='right', padx=5)
    
    def _carregar_dados(self):
        """Carrega os professores e servidores."""
        try:
            logger.info("Carregando profissionais para planilha...")
            
            # Buscar professores
            professores = obter_professores_ativos()
            
            # Buscar servidores
            servidores = obter_servidores_ativos()
            
            total = 0
            
            # Adicionar professores
            if professores:
                for prof in professores:
                    var = tk.BooleanVar(value=False)
                    self.profissionais.append((prof, var, 'Professor'))
                    total += 1
            
            # Adicionar servidores
            if servidores:
                for serv in servidores:
                    var = tk.BooleanVar(value=False)
                    self.profissionais.append((serv, var, 'Servidor'))
                    total += 1
            
            if total == 0:
                messagebox.showwarning(
                    "Aviso",
                    "Nenhum professor ou servidor encontrado."
                )
                return
            
            # Criar checkboxes
            self._criar_checkboxes()
            
            self.label_total.config(text=str(total))
            logger.info(f"{total} profissionais carregados")
            
        except Exception as e:
            logger.exception(f"Erro ao carregar dados: {e}")
            messagebox.showerror(
                "Erro",
                f"Erro ao carregar dados: {e}"
            )
    
    def _criar_checkboxes(self):
        """Cria os checkboxes para cada profissional."""
        # Separar por tipo (Professor / Servidor)
        professores = [(f, v, t) for f, v, t in self.profissionais if t == 'Professor']
        servidores = [(f, v, t) for f, v, t in self.profissionais if t == 'Servidor']
        
        row = 0
        
        # Seção de Professores
        if professores:
            Label(
                self.frame_checkboxes,
                text="═══ PROFESSORES ═══",
                font=("Arial", 12, "bold"),
                bg=COLORS.co4,
                fg=COLORS.co0,
                anchor='w',
                padx=10,
                pady=5
            ).grid(row=row, column=0, columnspan=3, sticky='ew', pady=(10, 5))
            
            row += 1
            
            for funcionario, var, _ in sorted(professores, key=lambda x: x[0]['nome']):
                frame_item = Frame(self.frame_checkboxes, bg=COLORS.co0)
                frame_item.grid(row=row, column=0, columnspan=3, sticky='ew', padx=10, pady=2)
                
                Checkbutton(
                    frame_item,
                    variable=var,
                    style='TCheckbutton'
                ).pack(side='left', padx=5)
                
                # Nome
                Label(
                    frame_item,
                    text=f"{funcionario['nome'][:50]:<50}",
                    font=("Arial", 9),
                    bg=COLORS.co0,
                    fg='black',
                    anchor='w'
                ).pack(side='left', padx=5)
                
                # Cargo
                cargo_display = funcionario.get('cargo', 'Professor@')
                Label(
                    frame_item,
                    text=f"({cargo_display})",
                    font=("Arial", 9),
                    bg=COLORS.co0,
                    fg='#666',
                    anchor='w'
                ).pack(side='left', padx=5)
                
                row += 1
        
        # Seção de Servidores
        if servidores:
            Label(
                self.frame_checkboxes,
                text="═══ SERVIDORES ═══",
                font=("Arial", 12, "bold"),
                bg=COLORS.co6,
                fg=COLORS.co0,
                anchor='w',
                padx=10,
                pady=5
            ).grid(row=row, column=0, columnspan=3, sticky='ew', pady=(20, 5))
            
            row += 1
            
            for funcionario, var, _ in sorted(servidores, key=lambda x: x[0]['nome']):
                frame_item = Frame(self.frame_checkboxes, bg=COLORS.co0)
                frame_item.grid(row=row, column=0, columnspan=3, sticky='ew', padx=10, pady=2)
                
                Checkbutton(
                    frame_item,
                    variable=var,
                    style='TCheckbutton'
                ).pack(side='left', padx=5)
                
                # Nome
                Label(
                    frame_item,
                    text=f"{funcionario['nome'][:50]:<50}",
                    font=("Arial", 9),
                    bg=COLORS.co0,
                    fg='black',
                    anchor='w'
                ).pack(side='left', padx=5)
                
                # Cargo
                cargo_display = funcionario.get('cargo', 'Servidor')
                Label(
                    frame_item,
                    text=f"({cargo_display})",
                    font=("Arial", 9),
                    bg=COLORS.co0,
                    fg='#666',
                    anchor='w'
                ).pack(side='left', padx=5)
                
                row += 1
    
    def _selecionar_todos(self):
        """Seleciona todos os checkboxes."""
        for _, var, _ in self.profissionais:
            var.set(True)
    
    def _desmarcar_todos(self):
        """Desmarca todos os checkboxes."""
        for _, var, _ in self.profissionais:
            var.set(False)
    
    def _gerar_planilha(self):
        """Gera a planilha PDF com os selecionados."""
        # Coletar selecionados
        selecionados = []
        for funcionario, var, tipo in self.profissionais:
            if var.get():
                selecionados.append((funcionario, tipo))
        
        if not selecionados:
            messagebox.showwarning(
                "Aviso",
                "Nenhum profissional selecionado."
            )
            return
        
        try:
            # Importar função de geração
            from src.relatorios.geradores.termo_cuidar_olhos import gerar_planilha_profissionais
            
            logger.info(f"Gerando planilha com {len(selecionados)} profissionais...")
            
            sucesso = gerar_planilha_profissionais(selecionados)
            
            if sucesso:
                messagebox.showinfo(
                    "Sucesso",
                    f"Planilha gerada com sucesso!\n{len(selecionados)} profissionais incluídos."
                )
                self.janela.destroy()
            else:
                messagebox.showerror(
                    "Erro",
                    "Erro ao gerar planilha. Verifique os logs."
                )
        
        except Exception as e:
            logger.exception(f"Erro ao gerar planilha: {e}")
            messagebox.showerror(
                "Erro",
                f"Erro ao gerar planilha: {e}"
            )


if __name__ == "__main__":
    # Teste da interface
    root = tk.Tk()
    root.withdraw()
    app = PlanilhaProfissionaisWindow(root)
    root.mainloop()
