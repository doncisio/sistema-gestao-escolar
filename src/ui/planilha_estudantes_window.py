"""
Interface para selecionar estudantes que assinaram os termos do Programa Cuidar dos Olhos.
"""

from tkinter import Toplevel, Frame, Label, Button, messagebox, Scrollbar, Canvas
from tkinter.ttk import Checkbutton
import tkinter as tk

from src.ui.colors import COLORS
from src.core.config_logs import get_logger
from src.relatorios.geradores.termo_cuidar_olhos import obter_alunos_ativos, obter_responsaveis_do_aluno

logger = get_logger(__name__)


class PlanilhaEstudantesWindow:
    """Janela para selecionar estudantes que assinaram os termos."""
    
    def __init__(self, janela_pai):
        """
        Inicializa a janela de seleção de estudantes.
        
        Args:
            janela_pai: Janela pai do Tkinter
        """
        self.janela_pai = janela_pai
        self.janela = Toplevel(janela_pai)
        self.janela.title("Planilha de Estudantes - Cuidar dos Olhos")
        self.janela.geometry("1000x700")
        self.janela.configure(bg=COLORS.co1)
        
        # Centralizar na tela
        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.janela.winfo_screenheight() // 2) - (700 // 2)
        self.janela.geometry(f"1000x700+{x}+{y}")
        
        # Dados
        self.alunos_responsaveis = []  # Lista de tuplas (aluno, responsavel, var_checkbox)
        self.selecionados = []
        
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
            text="Planilha de Levantamento - Estudantes",
            font=("Arial", 16, "bold"),
            bg=COLORS.co1,
            fg=COLORS.co0
        ).pack(pady=(0, 10))
        
        Label(
            frame_principal,
            text="Selecione os estudantes/responsáveis que assinaram os termos",
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
            text="Total de alunos/responsáveis:",
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
        
        # Frame com scroll para lista de alunos
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
        """Carrega os alunos e seus responsáveis."""
        try:
            logger.info("Carregando alunos para planilha...")
            
            # Buscar alunos ativos
            alunos = obter_alunos_ativos()
            
            if not alunos:
                messagebox.showwarning(
                    "Aviso",
                    "Nenhum aluno ativo encontrado."
                )
                return
            
            # Para cada aluno, buscar seus responsáveis
            total = 0
            for aluno in alunos:
                responsaveis = obter_responsaveis_do_aluno(aluno['id'])
                
                if responsaveis:
                    for responsavel in responsaveis:
                        var = tk.BooleanVar(value=False)
                        self.alunos_responsaveis.append((aluno, responsavel, var))
                        total += 1
            
            # Criar checkboxes
            self._criar_checkboxes()
            
            self.label_total.config(text=str(total))
            logger.info(f"{total} aluno-responsável carregados")
            
        except Exception as e:
            logger.exception(f"Erro ao carregar dados: {e}")
            messagebox.showerror(
                "Erro",
                f"Erro ao carregar dados: {e}"
            )
    
    def _criar_checkboxes(self):
        """Cria os checkboxes para cada aluno/responsável."""
        # Agrupar por série
        from collections import defaultdict
        por_serie = defaultdict(list)
        
        for item in self.alunos_responsaveis:
            aluno, responsavel, var = item
            serie = aluno['nome_serie']
            por_serie[serie].append(item)
        
        # Criar checkboxes agrupados por série
        row = 0
        for serie in sorted(por_serie.keys()):
            # Cabeçalho da série
            Label(
                self.frame_checkboxes,
                text=f"═══ {serie} ═══",
                font=("Arial", 11, "bold"),
                bg=COLORS.co4,
                fg=COLORS.co0,
                anchor='w',
                padx=10,
                pady=5
            ).grid(row=row, column=0, columnspan=3, sticky='ew', pady=(10, 5))
            
            row += 1
            
            # Checkboxes dos alunos desta série
            for aluno, responsavel, var in sorted(por_serie[serie], key=lambda x: x[0]['nome_aluno']):
                frame_item = Frame(self.frame_checkboxes, bg=COLORS.co0)
                frame_item.grid(row=row, column=0, columnspan=3, sticky='ew', padx=10, pady=2)
                
                Checkbutton(
                    frame_item,
                    variable=var,
                    style='TCheckbutton'
                ).pack(side='left', padx=5)
                
                # Nome do aluno
                Label(
                    frame_item,
                    text=f"{aluno['nome_aluno'][:40]:<40}",
                    font=("Arial", 9),
                    bg=COLORS.co0,
                    fg='black',
                    anchor='w'
                ).pack(side='left', padx=5)
                
                # Nome do responsável
                Label(
                    frame_item,
                    text=f"→ {responsavel['nome'][:35]:<35}",
                    font=("Arial", 9),
                    bg=COLORS.co0,
                    fg='#666',
                    anchor='w'
                ).pack(side='left', padx=5)
                
                row += 1
    
    def _selecionar_todos(self):
        """Seleciona todos os checkboxes."""
        for _, _, var in self.alunos_responsaveis:
            var.set(True)
    
    def _desmarcar_todos(self):
        """Desmarca todos os checkboxes."""
        for _, _, var in self.alunos_responsaveis:
            var.set(False)
    
    def _gerar_planilha(self):
        """Gera a planilha PDF com os selecionados."""
        # Coletar selecionados
        selecionados = []
        for aluno, responsavel, var in self.alunos_responsaveis:
            if var.get():
                selecionados.append((aluno, responsavel))
        
        if not selecionados:
            messagebox.showwarning(
                "Aviso",
                "Nenhum aluno/responsável selecionado."
            )
            return
        
        try:
            # Importar função de geração
            from src.relatorios.geradores.termo_cuidar_olhos import gerar_planilha_estudantes
            
            logger.info(f"Gerando planilha com {len(selecionados)} estudantes...")
            
            sucesso = gerar_planilha_estudantes(selecionados)
            
            if sucesso:
                messagebox.showinfo(
                    "Sucesso",
                    f"Planilha gerada com sucesso!\n{len(selecionados)} estudantes incluídos."
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
    app = PlanilhaEstudantesWindow(root)
    root.mainloop()
