"""
Interface para selecionar estudantes que assinaram os termos do Programa Cuidar dos Olhos.
"""

from tkinter import Toplevel, Frame, Label, Button, messagebox, Scrollbar, Canvas, Entry, StringVar
from tkinter.ttk import Checkbutton
import tkinter as tk
import json
from pathlib import Path

from src.ui.colors import COLORS
from src.core.config_logs import get_logger
from src.relatorios.geradores.termo_cuidar_olhos import obter_alunos_ativos, obter_responsaveis_do_aluno

logger = get_logger(__name__)

# Arquivo para salvar seleções
SELECOES_FILE = Path(__file__).parent.parent.parent / 'temp' / 'selecoes_estudantes_cuidar_olhos.json'


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
        self.janela.geometry("1000x750")
        self.janela.configure(bg=COLORS.co1)
        
        # Centralizar na tela
        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.janela.winfo_screenheight() // 2) - (750 // 2)
        self.janela.geometry(f"1000x750+{x}+{y}")
        
        # Ocultar janela principal
        self.janela_pai.withdraw()
        
        # Configurar fechamento para restaurar janela principal
        self.janela.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        
        # Dados
        self.alunos_responsaveis = []  # Lista de tuplas (aluno, responsavel, var_checkbox, frame_widget)
        self.selecionados = []
        self.texto_busca = StringVar()
        self.texto_busca.trace('w', lambda *args: self._filtrar_lista())
        
        # Garantir que a pasta temp existe
        SELECOES_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Criar interface
        self._criar_widgets()
        
        # Carregar dados
        self._carregar_dados()
        
        # Carregar seleções salvas
        self._carregar_selecoes_salvas()
    
    def _ao_fechar(self):
        """Restaura a janela principal e fecha esta janela."""
        self.janela_pai.deiconify()
        self.janela.destroy()
    
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
        ).pack(pady=(0, 15))
        
        # Frame de busca
        frame_busca = Frame(frame_principal, bg=COLORS.co1)
        frame_busca.pack(fill='x', pady=(0, 10))
        
        Label(
            frame_busca,
            text="🔍 Buscar:",
            font=("Arial", 10, "bold"),
            bg=COLORS.co1,
            fg=COLORS.co0
        ).pack(side='left', padx=(0, 5))
        
        self.entry_busca = Entry(
            frame_busca,
            textvariable=self.texto_busca,
            font=("Arial", 10),
            width=40
        )
        self.entry_busca.pack(side='left', padx=5)
        
        Label(
            frame_busca,
            text="(Digite nome do aluno ou responsável)",
            font=("Arial", 9),
            bg=COLORS.co1,
            fg='#666'
        ).pack(side='left', padx=5)
        
        # Frame de botões de ação rápida
        frame_acoes = Frame(frame_principal, bg=COLORS.co1)
        frame_acoes.pack(fill='x', pady=(0, 10))
        
        Button(
            frame_acoes,
            text="✓ Selecionar Todos",
            font=("Arial", 9, "bold"),
            bg=COLORS.co4,
            fg=COLORS.co0,
            command=self._selecionar_todos,
            width=17
        ).pack(side='left', padx=2)
        
        Button(
            frame_acoes,
            text="✗ Desmarcar Todos",
            font=("Arial", 9, "bold"),
            bg=COLORS.co6,
            fg=COLORS.co0,
            command=self._desmarcar_todos,
            width=17
        ).pack(side='left', padx=2)
        
        Button(
            frame_acoes,
            text="⇄ Inverter Seleção",
            font=("Arial", 9, "bold"),
            bg='#FF8C00',
            fg=COLORS.co0,
            command=self._inverter_selecao,
            width=17
        ).pack(side='left', padx=2)
        
        Button(
            frame_acoes,
            text="🗑 Limpar Salvas",
            font=("Arial", 9, "bold"),
            bg='#E91E63',
            fg=COLORS.co0,
            command=self._limpar_selecoes_salvas,
            width=17
        ).pack(side='left', padx=2)
        
        # Contador de selecionados
        self.label_selecionados = Label(
            frame_acoes,
            text="0 selecionados",
            font=("Arial", 10, "bold"),
            bg=COLORS.co1,
            fg='#FF6B00'
        )
        self.label_selecionados.pack(side='right', padx=10)
        
        Label(
            frame_acoes,
            text="Total:",
            font=("Arial", 10),
            bg=COLORS.co1,
            fg=COLORS.co0
        ).pack(side='right', padx=(10, 5))
        
        self.label_total = Label(
            frame_acoes,
            text="0",
            font=("Arial", 10, "bold"),
            bg=COLORS.co1,
            fg=COLORS.co4
        )
        self.label_total.pack(side='right')
        
        # Frame para botões de seleção por série (será preenchido depois)
        self.frame_series = Frame(frame_principal, bg=COLORS.co1)
        self.frame_series.pack(fill='x', pady=(0, 10))
        
        # Frame com scroll para lista de alunos
        frame_lista = Frame(frame_principal, bg=COLORS.co0)
        frame_lista.pack(fill='both', expand=True, pady=(0, 20))
        
        # Canvas e Scrollbar
        self.canvas = Canvas(frame_lista, bg=COLORS.co0, highlightthickness=0)
        scrollbar = Scrollbar(frame_lista, orient="vertical", command=self.canvas.yview)
        self.frame_checkboxes = Frame(self.canvas, bg=COLORS.co0)
        
        self.frame_checkboxes.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.frame_checkboxes, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
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
            command=self._ao_fechar,
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
                        # Adicionar callback para atualizar contador
                        var.trace('w', lambda *args: self._atualizar_contador())
                        self.alunos_responsaveis.append((aluno, responsavel, var, None))  # None será o frame
                        total += 1
            
            # Criar checkboxes
            self._criar_checkboxes()
            
            # Criar botões de seleção por série
            self._criar_botoes_series()
            
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
        
        for idx, item in enumerate(self.alunos_responsaveis):
            aluno, responsavel, var, _ = item
            serie = aluno['nome_serie']
            por_serie[serie].append(idx)
        
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
            indices = sorted(por_serie[serie], key=lambda i: self.alunos_responsaveis[i][0]['nome_aluno'])
            
            for idx in indices:
                aluno, responsavel, var, _ = self.alunos_responsaveis[idx]
                
                frame_item = Frame(self.frame_checkboxes, bg=COLORS.co0)
                frame_item.grid(row=row, column=0, columnspan=3, sticky='ew', padx=10, pady=2)
                
                # Atualizar referência do frame na tupla
                self.alunos_responsaveis[idx] = (aluno, responsavel, var, frame_item)
                
                checkbox = Checkbutton(
                    frame_item,
                    variable=var,
                    style='TCheckbutton',
                    command=lambda f=frame_item, v=var: self._atualizar_destaque(f, v)
                )
                checkbox.pack(side='left', padx=5)
                
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
    
    def _criar_botoes_series(self):
        """Cria botões para selecionar por série."""
        # Obter séries únicas
        series = set()
        for aluno, _, _, _ in self.alunos_responsaveis:
            series.add(aluno['nome_serie'])
        
        if not series:
            return
        
        Label(
            self.frame_series,
            text="Selecionar por série:",
            font=("Arial", 9, "bold"),
            bg=COLORS.co1,
            fg=COLORS.co0
        ).pack(side='left', padx=(0, 10))
        
        # Criar botão para cada série
        for serie in sorted(series):
            Button(
                self.frame_series,
                text=serie,
                font=("Arial", 8),
                bg='#4CAF50',
                fg=COLORS.co0,
                command=lambda s=serie: self._selecionar_serie(s),
                width=12
            ).pack(side='left', padx=2)
    
    
    def _selecionar_todos(self):
        """Seleciona todos os checkboxes visíveis."""
        for aluno, _, var, frame in self.alunos_responsaveis:
            if frame and frame.winfo_viewable():
                var.set(True)
                self._atualizar_destaque(frame, var)
        self._salvar_selecoes()
    
    def _desmarcar_todos(self):
        """Desmarca todos os checkboxes."""
        for _, _, var, frame in self.alunos_responsaveis:
            var.set(False)
            if frame:
                self._atualizar_destaque(frame, var)
        self._salvar_selecoes()
    
    def _inverter_selecao(self):
        """Inverte a seleção atual (visíveis apenas)."""
        for aluno, _, var, frame in self.alunos_responsaveis:
            if frame and frame.winfo_viewable():
                var.set(not var.get())
                self._atualizar_destaque(frame, var)
        self._salvar_selecoes()
    
    def _selecionar_serie(self, serie):
        """Seleciona todos os alunos de uma série específica."""
        for aluno, _, var, frame in self.alunos_responsaveis:
            if aluno['nome_serie'] == serie:
                var.set(True)
                if frame:
                    self._atualizar_destaque(frame, var)
        self._salvar_selecoes()
    
    def _filtrar_lista(self):
        """Filtra a lista baseado no texto de busca."""
        texto = self.texto_busca.get().lower().strip()
        
        for aluno, responsavel, var, frame in self.alunos_responsaveis:
            if frame:
                if not texto:
                    # Mostrar todos se não há busca
                    frame.grid()
                else:
                    # Verificar se o texto está no nome do aluno ou responsável
                    nome_aluno = aluno['nome_aluno'].lower()
                    nome_resp = responsavel['nome'].lower()
                    
                    if texto in nome_aluno or texto in nome_resp:
                        frame.grid()
                    else:
                        frame.grid_remove()
        
        # Atualizar contador
        self._atualizar_contador()
    
    def _atualizar_contador(self):
        """Atualiza o contador de selecionados."""
        count = sum(1 for _, _, var, _ in self.alunos_responsaveis if var.get())
        self.label_selecionados.config(text=f"{count} selecionados")
    
    def _atualizar_destaque(self, frame, var, salvar=True):
        """Atualiza o destaque visual do item selecionado."""
        cor = '#E3F2FD' if var.get() else COLORS.co0
        
        frame.config(bg=cor)
        for widget in frame.winfo_children():
            try:
                # Tentar configurar bg - nem todos os widgets suportam (ex: ttk.Checkbutton)
                widget.config(bg=cor)
            except tk.TclError:
                # Ignorar widgets que não suportam bg (geralmente widgets ttk)
                pass
        
        # Salvar seleções automaticamente (exceto durante carregamento)
        if salvar:
            self._salvar_selecoes()
    
    def _salvar_selecoes(self):
        """Salva as seleções atuais em arquivo JSON."""
        try:
            selecoes = []
            for aluno, responsavel, var, _ in self.alunos_responsaveis:
                if var.get():
                    # Criar chave única: id_aluno + id_responsavel
                    chave = f"{aluno['id']}_{responsavel['id']}"
                    selecoes.append(chave)
            
            with open(SELECOES_FILE, 'w', encoding='utf-8') as f:
                json.dump(selecoes, f)
            
            logger.debug(f"Seleções salvas: {len(selecoes)} itens")
        except Exception as e:
            logger.warning(f"Erro ao salvar seleções: {e}")
    
    def _carregar_selecoes_salvas(self):
        """Carrega seleções salvas do arquivo JSON."""
        try:
            if not SELECOES_FILE.exists():
                logger.debug("Nenhuma seleção salva encontrada")
                return
            
            with open(SELECOES_FILE, 'r', encoding='utf-8') as f:
                selecoes = json.load(f)
            
            if not selecoes:
                return
            
            selecoes_set = set(selecoes)
            count = 0
            
            # Aplicar seleções
            for aluno, responsavel, var, frame in self.alunos_responsaveis:
                chave = f"{aluno['id']}_{responsavel['id']}"
                if chave in selecoes_set:
                    var.set(True)
                    if frame:
                        self._atualizar_destaque(frame, var, salvar=False)
                    count += 1
            
            logger.info(f"Seleções carregadas: {count} de {len(selecoes)} itens encontrados")
            
            if count > 0:
                messagebox.showinfo(
                    "Seleções Restauradas",
                    f"✓ {count} seleção(ões) anterior(es) restaurada(s)!\n\n"
                    f"Você pode continuar de onde parou."
                )
        
        except Exception as e:
            logger.warning(f"Erro ao carregar seleções: {e}")
    
    def _limpar_selecoes_salvas(self):
        """Remove o arquivo de seleções salvas."""
        try:
            if SELECOES_FILE.exists():
                SELECOES_FILE.unlink()
                logger.info("Arquivo de seleções salvas removido")
                messagebox.showinfo(
                    "Limpeza Concluída",
                    "Seleções salvas foram apagadas.\n\n"
                    "Da próxima vez que abrir, começará sem nenhuma seleção."
                )
            else:
                messagebox.showinfo(
                    "Sem Seleções",
                    "Não há seleções salvas para limpar."
                )
        except Exception as e:
            logger.exception(f"Erro ao limpar seleções: {e}")
            messagebox.showerror("Erro", f"Erro ao limpar seleções: {e}")
    
    def _gerar_planilha(self):
        """Gera a planilha PDF com os selecionados."""
        # Coletar selecionados
        selecionados = []
        for aluno, responsavel, var, _ in self.alunos_responsaveis:
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
                self._ao_fechar()
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
