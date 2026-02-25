"""
Interface para selecionar professores e servidores que assinaram os termos do Programa Cuidar dos Olhos.
"""

from tkinter import Toplevel, Frame, Label, Button, messagebox, Scrollbar, Canvas, Entry, StringVar
from tkinter.ttk import Checkbutton
import tkinter as tk
import json
from pathlib import Path

from src.ui.colors import COLORS
from src.core.config_logs import get_logger
from src.core.conexao import conectar_bd
from src.core.config import ANO_LETIVO_ATUAL
from src.relatorios.geradores.termo_cuidar_olhos import obter_professores_ativos, obter_servidores_ativos

logger = get_logger(__name__)

# Arquivo para salvar seleções
SELECOES_FILE = Path(__file__).parent.parent.parent / 'temp' / 'selecoes_profissionais_cuidar_olhos.json'


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
        self.janela.geometry("900x750")
        self.janela.configure(bg=COLORS.co1)
        
        # Centralizar na tela
        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.janela.winfo_screenheight() // 2) - (750 // 2)
        self.janela.geometry(f"900x750+{x}+{y}")
        
        # Ocultar janela principal
        self.janela_pai.withdraw()
        
        # Configurar fechamento para restaurar janela principal
        self.janela.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        
        # Dados
        self.profissionais = []  # Lista de tuplas (funcionario, var_checkbox, tipo, frame_widget)
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
            text="(Digite nome do profissional)",
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
        
        # Frame para botões de categoria
        frame_categorias = Frame(frame_principal, bg=COLORS.co1)
        frame_categorias.pack(fill='x', pady=(0, 10))
        
        Label(
            frame_categorias,
            text="Seleção rápida:",
            font=("Arial", 9, "bold"),
            bg=COLORS.co1,
            fg=COLORS.co0
        ).pack(side='left', padx=(0, 10))
        
        Button(
            frame_categorias,
            text="👨‍🏫 Todos Professores",
            font=("Arial", 9),
            bg='#4CAF50',
            fg=COLORS.co0,
            command=lambda: self._selecionar_categoria('Professor'),
            width=20
        ).pack(side='left', padx=2)
        
        Button(
            frame_categorias,
            text="👔 Todos Servidores",
            font=("Arial", 9),
            bg='#2196F3',
            fg=COLORS.co0,
            command=lambda: self._selecionar_categoria('Servidor'),
            width=20
        ).pack(side='left', padx=2)
        
        # Contador de selecionados
        frame_contador = Frame(frame_principal, bg=COLORS.co1)
        frame_contador.pack(fill='x', pady=(0, 10))
        
        self.label_selecionados = Label(
            frame_contador,
            text="0 selecionados",
            font=("Arial", 10, "bold"),
            bg=COLORS.co1,
            fg='#FF6B00'
        )
        self.label_selecionados.pack(side='right', padx=10)
        
        Label(
            frame_contador,
            text="Total:",
            font=("Arial", 10),
            bg=COLORS.co1,
            fg=COLORS.co0
        ).pack(side='right', padx=(10, 5))
        
        self.label_total = Label(
            frame_contador,
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
                    # Adicionar callback para atualizar contador
                    var.trace('w', lambda *args: self._atualizar_contador())
                    self.profissionais.append((prof, var, 'Professor', None))  # None será o frame
                    total += 1
            
            # Adicionar servidores
            if servidores:
                for serv in servidores:
                    var = tk.BooleanVar(value=False)
                    # Adicionar callback para atualizar contador
                    var.trace('w', lambda *args: self._atualizar_contador())
                    self.profissionais.append((serv, var, 'Servidor', None))  # None será o frame
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
        indices_professores = [i for i, (_, _, t, _) in enumerate(self.profissionais) if t == 'Professor']
        indices_servidores = [i for i, (_, _, t, _) in enumerate(self.profissionais) if t == 'Servidor']
        
        row = 0
        
        # Seção de Professores
        if indices_professores:
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
            
            # Ordenar por nome
            indices_professores_ord = sorted(indices_professores, key=lambda i: self.profissionais[i][0]['nome'])
            
            for idx in indices_professores_ord:
                funcionario, var, tipo, _ = self.profissionais[idx]
                
                frame_item = Frame(self.frame_checkboxes, bg=COLORS.co0)
                frame_item.grid(row=row, column=0, columnspan=3, sticky='ew', padx=10, pady=2)
                
                # Atualizar referência do frame na tupla
                self.profissionais[idx] = (funcionario, var, tipo, frame_item)
                
                checkbox = Checkbutton(
                    frame_item,
                    variable=var,
                    style='TCheckbutton',
                    command=lambda f=frame_item, v=var: self._atualizar_destaque(f, v)
                )
                checkbox.pack(side='left', padx=5)
                
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
        if indices_servidores:
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
            
            # Ordenar por nome
            indices_servidores_ord = sorted(indices_servidores, key=lambda i: self.profissionais[i][0]['nome'])
            
            for idx in indices_servidores_ord:
                funcionario, var, tipo, _ = self.profissionais[idx]
                
                frame_item = Frame(self.frame_checkboxes, bg=COLORS.co0)
                frame_item.grid(row=row, column=0, columnspan=3, sticky='ew', padx=10, pady=2)
                
                # Atualizar referência do frame na tupla
                self.profissionais[idx] = (funcionario, var, tipo, frame_item)
                
                checkbox = Checkbutton(
                    frame_item,
                    variable=var,
                    style='TCheckbutton',
                    command=lambda f=frame_item, v=var: self._atualizar_destaque(f, v)
                )
                checkbox.pack(side='left', padx=5)
                
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
        """Seleciona todos os checkboxes visíveis."""
        for _, var, _, frame in self.profissionais:
            if frame and frame.winfo_viewable():
                var.set(True)
                self._atualizar_destaque(frame, var)
        self._salvar_selecoes()
    
    def _desmarcar_todos(self):
        """Desmarca todos os checkboxes."""
        for _, var, _, frame in self.profissionais:
            var.set(False)
            if frame:
                self._atualizar_destaque(frame, var)
        self._salvar_selecoes()
    
    def _inverter_selecao(self):
        """Inverte a seleção atual (visíveis apenas)."""
        for _, var, _, frame in self.profissionais:
            if frame and frame.winfo_viewable():
                var.set(not var.get())
                self._atualizar_destaque(frame, var)
        self._salvar_selecoes()
    
    def _selecionar_categoria(self, categoria):
        """Seleciona todos os profissionais de uma categoria específica."""
        for _, var, tipo, frame in self.profissionais:
            if tipo == categoria:
                var.set(True)
                if frame:
                    self._atualizar_destaque(frame, var)
        self._salvar_selecoes()
    
    def _filtrar_lista(self):
        """Filtra a lista baseado no texto de busca."""
        texto = self.texto_busca.get().lower().strip()
        
        for funcionario, var, tipo, frame in self.profissionais:
            if frame:
                if not texto:
                    # Mostrar todos se não há busca
                    frame.grid()
                else:
                    # Verificar se o texto está no nome
                    nome = funcionario['nome'].lower()
                    
                    if texto in nome:
                        frame.grid()
                    else:
                        frame.grid_remove()
        
        # Atualizar contador
        self._atualizar_contador()
    
    def _atualizar_contador(self):
        """Atualiza o contador de selecionados."""
        count = sum(1 for _, var, _, _ in self.profissionais if var.get())
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
        """Salva as seleções atuais no banco de dados."""
        try:
            conn = conectar_bd()
            if not conn:
                logger.warning("Não foi possível conectar ao banco para salvar seleções")
                return
            
            cursor = conn.cursor()
            ano_letivo = ANO_LETIVO_ATUAL
            
            # Primeiro, marcar todas as seleções do ano atual como não selecionadas
            cursor.execute("""
                UPDATE cuidar_olhos_selecoes
                SET selecionado = FALSE
                WHERE tipo = 'profissional' AND ano_letivo = %s
            """, (ano_letivo,))
            
            # Salvar seleções atuais
            count = 0
            for funcionario, var, tipo, _ in self.profissionais:
                if var.get():
                    # Inserir ou atualizar seleção
                    cursor.execute("""
                        INSERT INTO cuidar_olhos_selecoes
                        (tipo, funcionario_id, categoria, ano_letivo, selecionado)
                        VALUES ('profissional', %s, %s, %s, TRUE)
                        ON DUPLICATE KEY UPDATE
                        selecionado = TRUE,
                        data_atualizacao = CURRENT_TIMESTAMP
                    """, (funcionario['id'], tipo, ano_letivo))
                    count += 1
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.debug(f"Seleções salvas no BD: {count} itens")
        except Exception as e:
            logger.warning(f"Erro ao salvar seleções no BD: {e}")
    
    def _carregar_selecoes_salvas(self):
        """Carrega seleções salvas do banco de dados."""
        try:
            conn = conectar_bd()
            if not conn:
                logger.warning("Não foi possível conectar ao banco para carregar seleções")
                return
            
            cursor = conn.cursor(dictionary=True)
            ano_letivo = ANO_LETIVO_ATUAL
            
            # Buscar seleções salvas do ano atual
            cursor.execute("""
                SELECT funcionario_id
                FROM cuidar_olhos_selecoes
                WHERE tipo = 'profissional'
                AND ano_letivo = %s
                AND selecionado = TRUE
            """, (ano_letivo,))
            
            selecoes_bd = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not selecoes_bd:
                logger.debug("Nenhuma seleção salva encontrada no BD")
                return
            
            # Criar set de IDs para busca rápida
            selecoes_set = {s['funcionario_id'] for s in selecoes_bd}
            count = 0
            
            # Aplicar seleções
            for funcionario, var, tipo, frame in self.profissionais:
                if funcionario['id'] in selecoes_set:
                    var.set(True)
                    if frame:
                        self._atualizar_destaque(frame, var, salvar=False)
                    count += 1
            
            logger.info(f"Seleções carregadas do BD: {count} de {len(selecoes_bd)} itens encontrados")
            
            if count > 0:
                messagebox.showinfo(
                    "Seleções Restauradas",
                    f"✓ {count} seleção(ões) anterior(es) restaurada(s)!\n\n"
                    f"Você pode continuar de onde parou."
                )
        
        except Exception as e:
            logger.warning(f"Erro ao carregar seleções do BD: {e}")
    
    def _limpar_selecoes_salvas(self):
        """Remove as seleções salvas do banco de dados."""
        try:
            conn = conectar_bd()
            if not conn:
                messagebox.showerror(
                    "Erro",
                    "Não foi possível conectar ao banco de dados."
                )
                return
            
            cursor = conn.cursor()
            ano_letivo = ANO_LETIVO_ATUAL
            
            # Contar seleções antes de limpar
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM cuidar_olhos_selecoes
                WHERE tipo = 'profissional' AND ano_letivo = %s AND selecionado = TRUE
            """, (ano_letivo,))
            result = cursor.fetchone()
            total = result[0] if result else 0
            
            if total == 0:
                messagebox.showinfo(
                    "Sem Seleções",
                    "Não há seleções salvas para limpar."
                )
                cursor.close()
                conn.close()
                return
            
            # Confirmar limpeza
            resposta = messagebox.askyesno(
                "Confirmar Limpeza",
                f"Deseja realmente limpar {total} seleção(ões)?\n\n"
                f"Esta ação não pode ser desfeita."
            )
            
            if resposta:
                # Deletar seleções do ano atual
                cursor.execute("""
                    DELETE FROM cuidar_olhos_selecoes
                    WHERE tipo = 'profissional' AND ano_letivo = %s
                """, (ano_letivo,))
                
                conn.commit()
                logger.info(f"Seleções limpas do BD: {total} itens")
                
                messagebox.showinfo(
                    "Limpeza Concluída",
                    f"{total} seleção(ões) foram apagadas.\n\n"
                    "Da próxima vez que abrir, começará sem nenhuma seleção."
                )
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.exception(f"Erro ao limpar seleções: {e}")
            messagebox.showerror("Erro", f"Erro ao limpar seleções: {e}")
    
    def _gerar_planilha(self):
        """Gera a planilha PDF com os selecionados."""
        # Coletar selecionados
        selecionados = []
        for funcionario, var, tipo, _ in self.profissionais:
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
    app = PlanilhaProfissionaisWindow(root)
    root.mainloop()
