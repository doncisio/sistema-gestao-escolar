from src.core.config_logs import get_logger
from src.core.config import get_icon_path, ANO_LETIVO_ATUAL
logger = get_logger(__name__)
from tkinter import (
    Label, Frame, Button, Entry, Toplevel, Canvas, Scrollbar,
    NW, LEFT, RIGHT, TOP, BOTTOM, W, E, N, S,
    BOTH, X, Y, VERTICAL, HORIZONTAL, END,
    TRUE, FALSE, GROOVE, RAISED, FLAT, StringVar
)
from tkinter import ttk, messagebox
from PIL import ImageTk, Image
from src.core.conexao import conectar_bd
from typing import Any, cast

class InterfaceAdministrativa:
    def __init__(self, master, janela_principal=None):
        # Armazenar a referÃªncia da janela principal
        self.janela_principal = janela_principal
        
        # Se a janela principal foi fornecida, escondÃª-la
        if self.janela_principal:
            self.janela_principal.withdraw()
        
        # Cores - usando esquema de cores similar ao da main.py
        self.co0 = "#2e2d2b"  # Preta
        self.co1 = "#feffff"  # Branca
        self.co2 = "#e5e5e5"  # Cinza claro
        self.co3 = "#00a095"  # Verde
        self.co4 = "#403d3d"  # Letra cinza escuro
        self.co5 = "#003452"  # Azul escuro
        self.co6 = "#ef5350"  # Vermelho
        self.co7 = "#038cfc"  # Azul principal
        self.co8 = "#263238"  # Verde escuro
        self.co9 = "#e9edf5"  # Azul claro
        
        # Novas cores para melhorar a estÃ©tica
        self.co10 = "#f5f5f5"  # Fundo alternativo
        self.co11 = "#d0d0d0"  # Borda
        self.co12 = "#6c757d"  # Texto secundÃ¡rio

        self.master = master
        self.master.title("AdministraÃ§Ã£o - Escolas e Disciplinas")
        self.master.geometry('950x670')
        self.master.configure(background=self.co10)  # Alterado para cor de fundo mais suave
        self.master.resizable(width=TRUE, height=TRUE)
        
        # Adicionar um botÃ£o de maximizar no tÃ­tulo da janela (Windows)
        try:
            self.master.attributes('-toolwindow', False)
            self.master.attributes('-fullscreen', False)
        except:
            pass
        
        # Vincular evento de redimensionamento da janela
        self.master.bind("<Configure>", self.on_window_resize)
        
        # Capturar evento de fechamento da janela
        self.master.protocol("WM_DELETE_WINDOW", self.fechar_janela)

        # Configurar a janela para expandir
        self.master.grid_rowconfigure(0, weight=0)  # Logo
        self.master.grid_rowconfigure(1, weight=0)  # Separador
        self.master.grid_rowconfigure(2, weight=0)  # Dados
        self.master.grid_rowconfigure(3, weight=0)  # Separador
        self.master.grid_rowconfigure(4, weight=3)  # Tabela Escolas (peso maior)
        self.master.grid_rowconfigure(5, weight=2)  # Tabela Disciplinas
        self.master.grid_columnconfigure(0, weight=1)  # Coluna principal expande

        # Conectar ao banco de dados usando a mesma funÃ§Ã£o que main.py
        self.conn = conectar_bd()
        if self.conn is None:
            messagebox.showerror("Erro de ConexÃ£o", "NÃ£o foi possÃ­vel conectar ao banco de dados")
            self.fechar_janela()
            return

        try:
            self.cursor = self.conn.cursor()
        except Exception as e:
            messagebox.showerror("Erro de ConexÃ£o", f"NÃ£o foi possÃ­vel criar cursor: {str(e)}")
            self.fechar_janela()
            return

        # Criar frames
        self.criar_frames()
        self.criar_header()
        self.criar_botoes()
        self.criar_tabelas()
        self.carregar_escolas()

    def fechar_janela(self):
        # Fechar a conexÃ£o com o banco de dados
        if hasattr(self, 'conn') and self.conn:
            try:
                self.cursor.close()
                self.conn.close()
            except:
                pass
        
        # Destruir a janela atual
        self.master.destroy()
        
        # Se a janela principal existir, mostrÃ¡-la novamente
        if self.janela_principal:
            self.janela_principal.deiconify()
            
    def criar_frames(self):
        # Frame Logo
        self.frame_logo = Frame(self.master, height=52, bg=self.co7)
        self.frame_logo.grid(row=0, column=0, sticky='nsew')
        self.frame_logo.grid_propagate(False)  # Manter altura fixa
        self.frame_logo.grid_columnconfigure(0, weight=1)  # Permitir expansÃ£o horizontal

        # Separador
        ttk.Separator(self.master, orient=HORIZONTAL).grid(row=1, column=0, sticky='ew')

        # Frame Dados (BotÃµes)
        self.frame_dados = Frame(self.master, height=65, bg=self.co10)
        self.frame_dados.grid(row=2, column=0, sticky='nsew', padx=5)

        # Separador
        ttk.Separator(self.master, orient=HORIZONTAL).grid(row=3, column=0, sticky='ew')

        # Frame Escolas - com borda e cor de fundo mais suave
        self.frame_escolas = Frame(self.master, bg=self.co10, 
                                   highlightbackground=self.co11, 
                                   highlightthickness=1)
        self.frame_escolas.grid(row=4, column=0, sticky='nsew', padx=10, pady=5)
        
        # Divisor entre Escolas e Disciplinas
        divisor_frame = Frame(self.master, height=2, bg=self.co11)
        divisor_frame.grid(row=4, column=0, sticky='sew', padx=10)

        # Frame Disciplinas - com borda e cor de fundo mais suave
        self.frame_disciplinas = Frame(self.master, bg=self.co10, 
                                       highlightbackground=self.co11, 
                                       highlightthickness=1)
        self.frame_disciplinas.grid(row=5, column=0, sticky='nsew', padx=10, pady=5)

    def criar_header(self):
        # TÃ­tulo no frame_logo
        try:
            app_img = Image.open(get_icon_path('learning.png'))
            app_img = app_img.resize((45, 45))
            self.app_logo = ImageTk.PhotoImage(app_img)
            app_logo_label = Label(
                self.frame_logo, 
                image=self.app_logo,
                text=" GestÃ£o de Escolas e Disciplinas",
                compound=LEFT,
                relief=RAISED,
                anchor=W,
                font=('Ivy 15 bold'),
                bg=self.co7,
                fg=self.co1
            )
            app_logo_label.pack(fill=BOTH, expand=True, padx=0, pady=0)
        except:
            app_logo_label = Label(
                self.frame_logo,
                text=" GestÃ£o de Escolas e Disciplinas",
                relief=RAISED,
                anchor=W,
                font=('Ivy 15 bold'),
                bg=self.co7,
                fg=self.co1
            )
            app_logo_label.pack(fill=BOTH, expand=True, padx=0, pady=0)

    def criar_botoes(self):
        # Frame para os botÃµes
        botoes_frame = Frame(self.frame_dados, bg=self.co10)
        botoes_frame.pack(fill=X, expand=True, padx=10, pady=10)

        # Configurar grid
        for i in range(5):
            botoes_frame.grid_columnconfigure(i, weight=1)

        # Estilo comum para os botÃµes
        estilo_botao = {
            'font': ('Ivy', 9, 'bold'),
            'relief': FLAT,
            'padx': 10,
            'pady': 5,
            'bd': 0,
            'width': 15
        }
        
        # BotÃµes de aÃ§Ã£o - estilo verde/azul
        Button(botoes_frame, text="Nova Escola", 
               command=self.adicionar_escola,
               bg=self.co3,
               fg=self.co1,
               activebackground=self.co5,
               activeforeground=self.co1,
               **estilo_botao).grid(row=0, column=0, padx=5, pady=5)

        Button(botoes_frame, text="Editar Escola",
               command=self.editar_escola,
               bg=self.co5,
               fg=self.co1,
               activebackground=self.co3,
               activeforeground=self.co1,
               **estilo_botao).grid(row=0, column=1, padx=5, pady=5)

        Button(botoes_frame, text="Nova Disciplina",
               command=self.adicionar_disciplina,
               bg=self.co3,
               fg=self.co1,
               activebackground=self.co5,
               activeforeground=self.co1,
               **estilo_botao).grid(row=0, column=2, padx=5, pady=5)

        Button(botoes_frame, text="Editar Disciplina",
               command=self.editar_disciplina,
               bg=self.co5,
               fg=self.co1,
               activebackground=self.co3,
               activeforeground=self.co1,
               **estilo_botao).grid(row=0, column=3, padx=5, pady=5)
               
        # BotÃ£o para maximizar - estilo diferenciado
        self.tela_cheia = False
        self.btn_maximizar = Button(botoes_frame, 
               text="Maximizar",
               command=self.alternar_tela_cheia,
               bg=self.co7,
               fg=self.co1,
               activebackground=self.co5,
               activeforeground=self.co1,
               **estilo_botao)
        self.btn_maximizar.grid(row=0, column=4, padx=5, pady=5)

    def criar_tabelas(self):
        # Estilo para as tabelas
        style = ttk.Style()
        
        # ConfiguraÃ§Ã£o geral das tabelas
        style.configure("mystyle.Treeview",
                       highlightthickness=0,
                       bd=0,
                       font=('Calibri', 11),
                       background=self.co1,
                       foreground=self.co4,
                       rowheight=25,
                       fieldbackground=self.co1)
                       
        # ConfiguraÃ§Ã£o dos cabeÃ§alhos
        style.configure("mystyle.Treeview.Heading",
                       font=('Calibri', 13, 'bold'),
                       background=self.co5,
                       foreground=self.co1,
                       relief='flat')
                       
        style.map("mystyle.Treeview.Heading",
                 background=[('active', self.co7)])
                 
        # ConfiguraÃ§Ã£o das linhas selecionadas                
        style.map("mystyle.Treeview",
                 background=[('selected', self.co7)],
                 foreground=[('selected', self.co1)])
                 
        style.layout("mystyle.Treeview",
                    [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])

        # ===== SEÃ‡ÃƒO DE ESCOLAS =====
        # Frame e TÃ­tulo Escolas
        escola_label = Label(self.frame_escolas,
                           text="Escolas",
                           font=('Ivy 12 bold'),
                           bg=self.co10,
                           fg=self.co4)
        escola_label.pack(anchor=W, padx=10, pady=5)

        # Frame para pesquisa de escolas
        frame_pesquisa = Frame(self.frame_escolas, bg=self.co10)
        frame_pesquisa.pack(fill=X, padx=10, pady=5)

        # Campo de pesquisa
        Label(frame_pesquisa, text="Pesquisar:", bg=self.co10, fg=self.co4).pack(side=LEFT, padx=5)
        
        # Estilizar o campo de pesquisa
        self.entrada_pesquisa = Entry(frame_pesquisa, width=30, 
                                     bg=self.co1, fg=self.co4,
                                     relief=FLAT,
                                     highlightbackground=self.co11,
                                     highlightthickness=1)
        self.entrada_pesquisa.pack(side=LEFT, padx=5)
        self.entrada_pesquisa.insert(0, "Digite o nome, INEP, CNPJ ou municÃ­pio")
        self.entrada_pesquisa.config(fg=self.co12)
        
        # Eventos para limpar o texto de ajuda
        def on_focus_in(event):
            if self.entrada_pesquisa.get() == "Digite o nome, INEP, CNPJ ou municÃ­pio":
                self.entrada_pesquisa.delete(0, END)
                self.entrada_pesquisa.config(fg=self.co4)
        
        def on_focus_out(event):
            if not self.entrada_pesquisa.get():
                self.entrada_pesquisa.insert(0, "Digite o nome, INEP, CNPJ ou municÃ­pio")
                self.entrada_pesquisa.config(fg=self.co12)
                
        self.entrada_pesquisa.bind("<FocusIn>", on_focus_in)
        self.entrada_pesquisa.bind("<FocusOut>", on_focus_out)
        self.entrada_pesquisa.bind("<Return>", self.pesquisar_escolas)  # Pesquisar ao pressionar Enter

        # BotÃ£o de pesquisa estilizado
        Button(frame_pesquisa, text="Pesquisar", 
               command=self.pesquisar_escolas, 
               bg=self.co7, 
               fg=self.co1,
               relief=FLAT,
               padx=10).pack(side=LEFT, padx=5)

        # BotÃ£o para limpar pesquisa estilizado
        Button(frame_pesquisa, text="Mostrar Todas", 
               command=self.carregar_escolas, 
               bg=self.co5, 
               fg=self.co1,
               relief=FLAT,
               padx=10).pack(side=LEFT, padx=5)

        # Frame para conter a tabela e scrollbar
        tree_frame_escolas = Frame(self.frame_escolas)
        tree_frame_escolas.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # Scrollbars para a tabela de escolas
        scroll_y_escolas = ttk.Scrollbar(tree_frame_escolas)
        scroll_y_escolas.pack(side=RIGHT, fill=Y)

        scroll_x_escolas = ttk.Scrollbar(tree_frame_escolas, orient='horizontal')
        scroll_x_escolas.pack(side=BOTTOM, fill=X)

        # Tabela de escolas
        self.tree_escolas = ttk.Treeview(
            tree_frame_escolas,
            columns=("ID", "Nome", "EndereÃ§o", "INEP", "CNPJ", "MunicÃ­pio"),
            show='headings',
            style="mystyle.Treeview",
            yscrollcommand=scroll_y_escolas.set,
            xscrollcommand=scroll_x_escolas.set
        )

        self.tree_escolas.pack(fill=BOTH, expand=True)

        scroll_y_escolas.config(command=self.tree_escolas.yview)
        scroll_x_escolas.config(command=self.tree_escolas.xview)

        # Configurar colunas da tabela de escolas
        for col in ("ID", "Nome", "EndereÃ§o", "INEP", "CNPJ", "MunicÃ­pio"):
            self.tree_escolas.heading(col, text=col, anchor=W)
            self.tree_escolas.column(col, width=150, anchor=W)
            
        # Ajustar larguras das colunas
        self.tree_escolas.column("ID", width=50)
        self.tree_escolas.column("Nome", width=250)
        self.tree_escolas.column("EndereÃ§o", width=250)
        self.tree_escolas.column("INEP", width=100)
        self.tree_escolas.column("CNPJ", width=150)
        self.tree_escolas.column("MunicÃ­pio", width=150)

        # ===== SEÃ‡ÃƒO DE DISCIPLINAS =====
        # Frame e Tabela Disciplinas
        disciplina_label = Label(self.frame_disciplinas,
                               text="Disciplinas da Escola Selecionada",
                               font=('Ivy 12 bold'),
                               bg=self.co10,
                               fg=self.co4)
        disciplina_label.pack(anchor=W, padx=10, pady=5)

        # InstruÃ§Ã£o para disciplinas
        Label(self.frame_disciplinas, 
              text="Selecione uma escola acima para visualizar suas disciplinas", 
              font=('Ivy 9 italic'),
              bg=self.co10, 
              fg=self.co12).pack(anchor=W, padx=10, pady=2)

        # Frame para conter a tabela e scrollbar
        tree_frame_disciplinas = Frame(self.frame_disciplinas, bg=self.co10)
        tree_frame_disciplinas.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # Scrollbars para a tabela de disciplinas
        scroll_y_disciplinas = ttk.Scrollbar(tree_frame_disciplinas)
        scroll_y_disciplinas.pack(side=RIGHT, fill=Y)

        scroll_x_disciplinas = ttk.Scrollbar(tree_frame_disciplinas, orient='horizontal')
        scroll_x_disciplinas.pack(side=BOTTOM, fill=X)

        # Tabela de disciplinas
        self.tree_disciplinas = ttk.Treeview(
            tree_frame_disciplinas,
            columns=("ID", "Nome", "NÃ­vel", "Carga HorÃ¡ria"),
            show='headings',
            style="mystyle.Treeview",
            yscrollcommand=scroll_y_disciplinas.set,
            xscrollcommand=scroll_x_disciplinas.set
        )

        self.tree_disciplinas.pack(fill=BOTH, expand=True)

        scroll_y_disciplinas.config(command=self.tree_disciplinas.yview)
        scroll_x_disciplinas.config(command=self.tree_disciplinas.xview)

        # Configurar colunas da tabela de disciplinas
        for col in ("ID", "Nome", "NÃ­vel", "Carga HorÃ¡ria"):
            self.tree_disciplinas.heading(col, text=col, anchor=W)
            self.tree_disciplinas.column(col, width=150, anchor=W)
            
        # Ajustar larguras das colunas de disciplinas
        self.tree_disciplinas.column("ID", width=50)
        self.tree_disciplinas.column("Nome", width=250)

        # Vincular eventos Ã s tabelas
        self.tree_escolas.bind("<ButtonRelease-1>", self.selecionar_escola)
        self.tree_disciplinas.bind("<ButtonRelease-1>", self.selecionar_disciplina)
        
        # InstruÃ§Ãµes visuais estilizadas
        Label(self.frame_escolas, 
              text="Clique em uma escola para visualizar suas disciplinas", 
              font=('Ivy 9 italic'),
              bg=self.co10, 
              fg=self.co12).pack(anchor=W, padx=10, pady=2)

    def carregar_escolas(self):
        # Limpar a tabela
        for item in self.tree_escolas.get_children():
            self.tree_escolas.delete(item)

        try:
            # Limpar a pesquisa se existir
            if hasattr(self, 'entrada_pesquisa'):
                self.entrada_pesquisa.delete(0, END)
                self.entrada_pesquisa.insert(0, "Digite o nome, INEP, CNPJ ou municÃ­pio")
                self.entrada_pesquisa.config(fg=self.co12)
                
            # Remover status labels anteriores se existirem
            for widget in self.frame_escolas.winfo_children():
                if isinstance(widget, Label) and (widget.cget("text").startswith("Total de escolas:") or 
                                                 widget.cget("text").startswith("Encontradas") or
                                                 widget.cget("text").startswith("Nenhuma escola")):
                    widget.destroy()
            
            # Carregar escolas do banco de dados
            cast(Any, self.cursor).execute("""
                SELECT id, nome, endereco, inep,
                CONCAT(
                    SUBSTR(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), 1, 2), '.',
                    SUBSTR(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), 3, 3), '.',
                    SUBSTR(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), 6, 3), '/',
                    SUBSTR(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), 9, 4), '-',
                    SUBSTR(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), 13, 2)
                ) AS cnpj,
                municipio 
                FROM escolas
                ORDER BY nome
            """)
            escolas = self.cursor.fetchall()
            
            # Criar um frame para a mensagem de status com fundo destacado
            status_frame = Frame(self.frame_escolas, bg=self.co9, padx=5, pady=3)
            status_frame.pack(anchor=E, padx=10, pady=5)
            
            # Exibir nÃºmero total de escolas
            total_escolas = len(escolas)
            status_label = Label(status_frame, 
                               text=f"Total de escolas: {total_escolas}", 
                               font=('Ivy', 9, 'bold'),
                               bg=self.co9, 
                               fg=self.co5)
            status_label.pack()
            
            # Configurar remoÃ§Ã£o automÃ¡tica apÃ³s alguns segundos
            self.master.after(5000, status_frame.destroy)
            
            for escola in escolas:
                self.tree_escolas.insert('', 'end', values=escola)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar escolas: {str(e)}")

    def carregar_disciplinas(self, escola_id):
        # Limpar a tabela
        for item in self.tree_disciplinas.get_children():
            self.tree_disciplinas.delete(item)

        try:
            # Carregar disciplinas do banco de dados usando a tabela niveisensino
            try:
                cast(Any, self.cursor).execute("""
                    SELECT d.id, d.nome, n.nome as nivel, d.carga_horaria 
                    FROM disciplinas d
                    LEFT JOIN niveisensino n ON d.nivel_id = n.id
                    WHERE d.escola_id = %s
                """, (escola_id,))
            except Exception as e:
                # Se o JOIN falhar, tente carregar apenas os dados bÃ¡sicos
                if "niveisensino" in str(e):
                    cast(Any, self.cursor).execute("""
                        SELECT id, nome, nivel_id as nivel, carga_horaria 
                        FROM disciplinas 
                        WHERE escola_id = %s
                    """, (escola_id,))
                else:
                    raise e
                    
            disciplinas = self.cursor.fetchall()
            for disciplina in disciplinas:
                self.tree_disciplinas.insert('', 'end', values=disciplina)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar disciplinas: {str(e)}")

    def selecionar_escola(self, event):
        try:
            # Obter a escola selecionada
            selected_item = self.tree_escolas.selection()[0]
            escola_id = self.tree_escolas.item(selected_item, 'values')[0]
            # Carregar disciplinas da escola selecionada
            self.carregar_disciplinas(escola_id)
        except IndexError:
            pass

    def selecionar_disciplina(self, event):
        try:
            # Obter a disciplina selecionada
            selected_item = self.tree_disciplinas.selection()[0]
            disciplina_values = self.tree_disciplinas.item(selected_item, 'values')
            # Aqui vocÃª pode adicionar aÃ§Ãµes especÃ­ficas para quando uma disciplina Ã© selecionada
        except IndexError:
            pass

    def adicionar_escola(self):
        # Criar janela de diÃ¡logo para adicionar escola
        dialog = Toplevel(self.master)
        dialog.title("Adicionar Nova Escola")
        dialog.geometry("400x450")
        dialog.configure(background=self.co10)
        dialog.transient(self.master)
        dialog.focus_force()
        dialog.grab_set()

        # Estilo para os campos
        estilo_label = {'font': ('Ivy', 10, 'bold'), 'bg': self.co10, 'fg': self.co4}
        estilo_entry = {'width': 40, 'bg': self.co1, 'relief': FLAT, 
                         'highlightbackground': self.co11, 'highlightthickness': 1}

        # CabeÃ§alho
        header_frame = Frame(dialog, bg=self.co7, height=40)
        header_frame.pack(fill=X, pady=(0, 15))
        
        Label(header_frame, text="Adicionar Nova Escola", font=('Ivy', 12, 'bold'), 
             bg=self.co7, fg=self.co1, padx=10, pady=5).pack(fill=X)

        # Frame para os campos do formulÃ¡rio
        form_frame = Frame(dialog, padx=20, pady=10, bg=self.co10)
        form_frame.pack(fill=BOTH, expand=True)

        # Campos do formulÃ¡rio
        Label(form_frame, text="Nome:", **estilo_label).pack(anchor=W, pady=(5, 2))
        nome_entry = Entry(form_frame, **estilo_entry)
        nome_entry.pack(fill=X, pady=(0, 10))

        Label(form_frame, text="EndereÃ§o:", **estilo_label).pack(anchor=W, pady=(5, 2))
        endereco_entry = Entry(form_frame, **estilo_entry)
        endereco_entry.pack(fill=X, pady=(0, 10))

        Label(form_frame, text="INEP:", **estilo_label).pack(anchor=W, pady=(5, 2))
        inep_entry = Entry(form_frame, **estilo_entry)
        inep_entry.pack(fill=X, pady=(0, 10))

        Label(form_frame, text="CNPJ:", **estilo_label).pack(anchor=W, pady=(5, 2))
        cnpj_entry = Entry(form_frame, **estilo_entry)
        cnpj_entry.pack(fill=X, pady=(0, 10))

        Label(form_frame, text="MunicÃ­pio:", **estilo_label).pack(anchor=W, pady=(5, 2))
        municipio_entry = Entry(form_frame, **estilo_entry)
        municipio_entry.pack(fill=X, pady=(0, 10))

        def salvar():
            try:
                # Inserir nova escola no banco de dados
                cast(Any, self.cursor).execute("""
                    INSERT INTO escolas (nome, endereco, inep, cnpj, municipio)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    nome_entry.get(),
                    endereco_entry.get(),
                    inep_entry.get(),
                    cnpj_entry.get(),
                    municipio_entry.get()
                ))
                if hasattr(self, 'conn') and self.conn:
                    cast(Any, self.conn).commit()
                messagebox.showinfo("Sucesso", "Escola adicionada com sucesso!")
                dialog.destroy()
                self.carregar_escolas()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao adicionar escola: {str(e)}")

        # Frame para botÃµes
        botoes_frame = Frame(dialog, bg=self.co10, pady=10)
        botoes_frame.pack(fill=X, side=BOTTOM)

        Button(botoes_frame, text="Salvar",
               command=salvar,
               bg=self.co3,
               fg=self.co1,
               relief=FLAT,
               width=15,
               font=('Ivy', 9, 'bold'),
               padx=10,
               pady=5).pack(pady=10)

    def editar_escola(self):
        try:
            selected_item = self.tree_escolas.selection()[0]
            escola_values = self.tree_escolas.item(selected_item, 'values')
            
            dialog = Toplevel(self.master)
            dialog.title("Editar Escola")
            dialog.geometry("400x400")
            dialog.transient(self.master)
            dialog.focus_force()
            dialog.grab_set()

            # Campos do formulÃ¡rio
            Label(dialog, text="Nome:", font=('Ivy 10')).pack(pady=5)
            nome_entry = Entry(dialog, width=40)
            nome_entry.insert(0, escola_values[1])
            nome_entry.pack(pady=5)

            Label(dialog, text="EndereÃ§o:", font=('Ivy 10')).pack(pady=5)
            endereco_entry = Entry(dialog, width=40)
            endereco_entry.insert(0, escola_values[2])
            endereco_entry.pack(pady=5)

            Label(dialog, text="INEP:", font=('Ivy 10')).pack(pady=5)
            inep_entry = Entry(dialog, width=40)
            inep_entry.insert(0, escola_values[3])
            inep_entry.pack(pady=5)

            Label(dialog, text="CNPJ:", font=('Ivy 10')).pack(pady=5)
            cnpj_entry = Entry(dialog, width=40)
            cnpj_entry.insert(0, escola_values[4])
            cnpj_entry.pack(pady=5)

            Label(dialog, text="MunicÃ­pio:", font=('Ivy 10')).pack(pady=5)
            municipio_entry = Entry(dialog, width=40)
            municipio_entry.insert(0, escola_values[5])
            municipio_entry.pack(pady=5)

            def salvar_edicao():
                try:
                    cast(Any, self.cursor).execute("""
                        UPDATE escolas
                        SET nome = %s, endereco = %s, inep = %s, cnpj = %s, municipio = %s
                        WHERE id = %s
                    """, (
                        nome_entry.get(),
                        endereco_entry.get(),
                        inep_entry.get(),
                        cnpj_entry.get(),
                        municipio_entry.get(),
                        escola_values[0]
                    ))
                    if hasattr(self, 'conn') and self.conn:
                        cast(Any, self.conn).commit()
                    messagebox.showinfo("Sucesso", "Escola atualizada com sucesso!")
                    dialog.destroy()
                    self.carregar_escolas()
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao atualizar escola: {str(e)}")

            def excluir():
                if messagebox.askyesno("Confirmar ExclusÃ£o", 
                                     "Tem certeza que deseja excluir esta escola? Todas as disciplinas associadas tambÃ©m serÃ£o excluÃ­das."):
                    try:
                        cast(Any, self.cursor).execute("DELETE FROM disciplinas WHERE escola_id = %s", (escola_values[0],))
                        cast(Any, self.cursor).execute("DELETE FROM escolas WHERE id = %s", (escola_values[0],))
                        if hasattr(self, 'conn') and self.conn:
                            cast(Any, self.conn).commit()
                        messagebox.showinfo("Sucesso", "Escola excluÃ­da com sucesso!")
                        dialog.destroy()
                        self.carregar_escolas()
                    except Exception as e:
                        messagebox.showerror("Erro", f"Erro ao excluir escola: {str(e)}")

            # BotÃµes
            Button(dialog, text="Salvar AlteraÃ§Ãµes",
                   command=salvar_edicao,
                   bg=self.co3,
                   fg=self.co1,
                   width=20).pack(pady=10)

            Button(dialog, text="Excluir Escola",
                   command=excluir,
                   bg=self.co6,
                   fg=self.co1,
                   width=20).pack(pady=10)

        except IndexError:
            messagebox.showwarning("Aviso", "Por favor, selecione uma escola para editar.")

    def adicionar_disciplina(self):
        try:
            selected_escola = self.tree_escolas.selection()[0]
            escola_id = self.tree_escolas.item(selected_escola, 'values')[0]
            escola_nome = self.tree_escolas.item(selected_escola, 'values')[1]

            # Inicializar variÃ¡veis
            disciplinas_existentes = []
            nivel_atual_id = None
            carga_total_id = None

            dialog = Toplevel(self.master)
            dialog.title(f"Gerenciar Disciplinas - {escola_nome}")
            dialog.geometry("650x650")  # Aumentei a altura da janela
            dialog.transient(self.master)
            dialog.focus_force()
            dialog.grab_set()
            dialog.configure(bg=self.co10)
            
            # Centralizar a janela
            self.centralizar_janela(dialog)

            # Criar um canvas com scrollbar para garantir que todo conteÃºdo seja acessÃ­vel
            canvas_principal = Canvas(dialog, bg=self.co10, highlightthickness=0)
            scrollbar_principal = Scrollbar(dialog, orient=VERTICAL, command=canvas_principal.yview)
            
            # Frame principal que vai conter todo o conteÃºdo
            master_frame = Frame(canvas_principal, bg=self.co10)
            
            # Configurar o canvas para rolar o frame principal quando seu tamanho mudar
            def configure_canvas(event):
                canvas_principal.configure(scrollregion=canvas_principal.bbox("all"))
                # Ajustar a largura do frame interno para corresponder ao canvas
                canvas_principal.itemconfig(frame_window, width=event.width)
            
            # Criar uma janela dentro do canvas que conterÃ¡ o frame principal
            frame_window = canvas_principal.create_window((0, 0), window=master_frame, anchor=NW)
            
            # Vincular eventos de redimensionamento
            master_frame.bind("<Configure>", configure_canvas)
            canvas_principal.bind("<Configure>", configure_canvas)
            
            # Configurar o scrollbar
            canvas_principal.configure(yscrollcommand=scrollbar_principal.set)
            
            # Empacotar canvas e scrollbar
            canvas_principal.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar_principal.pack(side=RIGHT, fill=Y)
            
            # Adicionar suporte para rolagem com mouse
            def _bind_mousewheel(event):
                canvas_principal.bind_all("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas_principal))
            
            def _unbind_mousewheel(event):
                canvas_principal.unbind_all("<MouseWheel>")
                
            canvas_principal.bind("<Enter>", _bind_mousewheel)
            canvas_principal.bind("<Leave>", _unbind_mousewheel)

            # Lista de disciplinas predefinidas
            disciplinas = [
                "LÃNGUA PORTUGUESA", "MATEMÃTICA", "HISTÃ“RIA", "GEOGRAFIA", "CIÃŠNCIAS",
                "ARTE", "ENSINO RELIGIOSO", "EDUCAÃ‡ÃƒO FÃSICA", "LÃNGUA INGLESA", "FILOSOFIA",
            ]
            
            # Frame principal com rolagem - agora serÃ¡ colocado dentro do master_frame
            main_frame = Frame(master_frame, bg=self.co10)
            main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
            
            # Carregar nÃ­veis do banco de dados
            try:
                cast(Any, self.cursor).execute("SELECT id, nome FROM niveisensino")
                niveis = self.cursor.fetchall()
                nivel_atual_id = None
                
                Label(main_frame, text="NÃ­vel de Ensino:", font=('Ivy 11 bold'), bg=self.co10).pack(anchor=W, pady=(0, 5))
                nivel_var = StringVar(dialog)
                nivel_menu = ttk.Combobox(main_frame, textvariable=nivel_var, values=[str(nivel[1]) for nivel in niveis], width=40)
                nivel_menu.pack(fill=X, pady=(0, 15))
                
                # Obter o ano letivo atual
                cast(Any, self.cursor).execute("SELECT id, ano_letivo FROM anosletivos WHERE ano_letivo = %s", (ANO_LETIVO_ATUAL,))
                resultado_ano = self.cursor.fetchone()
                
                if not resultado_ano:
                    # Se nÃ£o encontrar o ano atual, pegar o Ãºltimo registrado
                    cast(Any, self.cursor).execute("SELECT id, ano_letivo FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                    resultado_ano = self.cursor.fetchone()
                
                if resultado_ano:
                    ano_letivo_id, ano_letivo = resultado_ano
                else:
                    # Default se nÃ£o encontrar nenhum ano letivo
                    ano_letivo_id, ano_letivo = None, None
                
                # Frame para carga horÃ¡ria total (alternativa Ã s individuais)
                total_frame = Frame(main_frame, bg=self.co10, padx=10, pady=10, bd=1, relief=GROOVE)
                total_frame.pack(fill=X, pady=10)
                
                Label(total_frame, 
                     text="Carga HorÃ¡ria Total do NÃ­vel", 
                     font=('Ivy 11 bold'), 
                     bg=self.co10).pack(anchor=W)
                
                Label(total_frame, 
                     text="Insira a carga horÃ¡ria total quando nÃ£o especificar as cargas por disciplina",
                     font=('Ivy 9 italic'), 
                     bg=self.co10, 
                     fg=self.co12).pack(anchor=W, pady=(0, 5))
                
                # Frame para seleÃ§Ã£o de ano letivo e sÃ©rie
                selecao_frame = Frame(total_frame, bg=self.co10)
                selecao_frame.pack(fill=X, pady=5)
                
                # Carregar anos letivos
                cast(Any, self.cursor).execute("SELECT id, ano_letivo FROM anosletivos ORDER BY ano_letivo DESC")
                anos_letivos = self.cursor.fetchall()
                
                Label(selecao_frame, text="Ano Letivo:", bg=self.co10).pack(side=LEFT, padx=(0, 5))
                ano_var = StringVar(dialog)
                ano_menu = ttk.Combobox(selecao_frame, textvariable=ano_var, 
                                      values=[f"{ano[1]}" for ano in anos_letivos], 
                                      width=10)
                ano_menu.pack(side=LEFT, padx=5)
                
                # Carregar sÃ©ries/nÃ­veis
                cast(Any, self.cursor).execute("SELECT id, nome FROM series ORDER BY nome")
                series = self.cursor.fetchall()
                
                Label(selecao_frame, text="SÃ©rie:", bg=self.co10).pack(side=LEFT, padx=(20, 5))
                serie_var = StringVar(dialog)
                serie_menu = ttk.Combobox(selecao_frame, textvariable=serie_var, 
                                        values=[str(serie[1]) for serie in series], 
                                        width=20)
                serie_menu.pack(side=LEFT, padx=5)
                
                # Linha com campo de carga horÃ¡ria
                campos_frame = Frame(total_frame, bg=self.co10)
                campos_frame.pack(fill=X, pady=5)
                
                Label(campos_frame, text="Carga horÃ¡ria total:", bg=self.co10).pack(side=LEFT, padx=(0, 5))
                carga_total_entry = Entry(campos_frame, width=10)
                carga_total_entry.pack(side=LEFT, padx=5)
                
                # BotÃ£o para adicionar nova carga horÃ¡ria
                def adicionar_carga_horaria():
                    try:
                        ano_selecionado = ano_var.get()
                        serie_selecionada = serie_var.get()
                        carga_horaria = carga_total_entry.get().strip()
                        
                        if not ano_selecionado or not serie_selecionada or not carga_horaria:
                            messagebox.showerror("Erro", "Por favor, preencha todos os campos.")
                            return
                            
                        # Obter IDs
                        ano_id = next((ano[0] for ano in anos_letivos if str(ano[1]) == ano_selecionado), None)
                        serie_id = next((serie[0] for serie in series if serie[1] == serie_selecionada), None)
                        
                        if not ano_id or not serie_id:
                            messagebox.showerror("Erro", "Erro ao identificar ano letivo ou sÃ©rie.")
                            return
                            
                        try:
                            carga_horaria_valor = int(carga_horaria)
                        except ValueError:
                            messagebox.showerror("Erro", "A carga horÃ¡ria deve ser um nÃºmero inteiro.")
                            return
                        
                        # Verificar se jÃ¡ existe um registro para esta combinaÃ§Ã£o
                        cast(Any, self.cursor).execute("""
                            SELECT id FROM carga_horaria_total 
                            WHERE serie_id = %s AND escola_id = %s AND ano_letivo_id = %s
                        """, (serie_id, escola_id, ano_id))
                        
                        resultado = self.cursor.fetchone()
                        
                        if resultado:
                            # Atualizar registro existente
                            cast(Any, self.cursor).execute("""
                                UPDATE carga_horaria_total 
                                SET carga_horaria_total = %s 
                                WHERE id = %s
                            """, (carga_horaria_valor, resultado[0]))
                            mensagem = "Carga horÃ¡ria total atualizada com sucesso!"
                        else:
                            # Inserir novo registro
                            cast(Any, self.cursor).execute("""
                                INSERT INTO carga_horaria_total 
                                (serie_id, ano_letivo_id, escola_id, carga_horaria_total) 
                                VALUES (%s, %s, %s, %s)
                            """, (serie_id, ano_id, escola_id, carga_horaria_valor))
                            mensagem = "Carga horÃ¡ria total adicionada com sucesso!"
                        
                        if self.conn:
                            cast(Any, self.conn).commit()
                        messagebox.showinfo("Sucesso", mensagem)
                        
                        # Limpar campos
                        carga_total_entry.delete(0, END)
                        
                    except Exception as e:
                        messagebox.showerror("Erro", f"Erro ao processar carga horÃ¡ria: {str(e)}")
                
                # BotÃ£o para adicionar
                Button(campos_frame, 
                       text="Adicionar Carga HorÃ¡ria",
                       command=adicionar_carga_horaria,
                       bg=self.co3,
                       fg=self.co1,
                       font=('Ivy 9'),
                       padx=10).pack(side=LEFT, padx=(20, 0))
                
                # Frame para mostrar cargas horÃ¡rias existentes
                listagem_frame = Frame(total_frame, bg=self.co10)
                listagem_frame.pack(fill=X, pady=10)
                
                Label(listagem_frame, 
                     text="Cargas HorÃ¡rias Cadastradas:", 
                     font=('Ivy 10 bold'),
                     bg=self.co10).pack(anchor=W)
                
                # Criar Treeview para mostrar cargas horÃ¡rias
                tree_frame = Frame(listagem_frame, bg=self.co10)
                tree_frame.pack(fill=X, pady=5)
                
                # Scrollbar para a treeview
                scrollbar = ttk.Scrollbar(tree_frame)
                scrollbar.pack(side=RIGHT, fill=Y)
                
                # Treeview para cargas horÃ¡rias
                carga_tree = ttk.Treeview(tree_frame, 
                                        columns=("Ano", "SÃ©rie", "Carga"),
                                        show='headings',
                                        yscrollcommand=scrollbar.set)
                
                carga_tree.heading("Ano", text="Ano Letivo")
                carga_tree.heading("SÃ©rie", text="SÃ©rie")
                carga_tree.heading("Carga", text="Carga HorÃ¡ria")
                
                carga_tree.column("Ano", width=100)
                carga_tree.column("SÃ©rie", width=150)
                carga_tree.column("Carga", width=100)
                
                carga_tree.pack(side=LEFT, fill=X, expand=True)
                scrollbar.config(command=carga_tree.yview)
                
                # FunÃ§Ã£o para carregar cargas horÃ¡rias
                def carregar_cargas_horarias():
                    # Limpar treeview
                    for item in carga_tree.get_children():
                        carga_tree.delete(item)
                    
                    try:
                        # Buscar cargas horÃ¡rias
                        cast(Any, self.cursor).execute("""
                            SELECT cht.id, cht.carga_horaria_total, al.ano_letivo, s.nome
                            FROM carga_horaria_total cht
                            JOIN anosletivos al ON cht.ano_letivo_id = al.id
                            JOIN series s ON cht.serie_id = s.id
                            WHERE cht.escola_id = %s
                            ORDER BY al.ano_letivo DESC, s.nome
                        """, (escola_id,))
                        
                        cargas = self.cursor.fetchall()
                        
                        for carga in cargas:
                            carga_tree.insert('', 'end', values=(
                                carga[2],  # ano_letivo
                                carga[3],  # nome da sÃ©rie
                                carga[1]   # carga_horaria_total
                            ))
                            
                    except Exception as e:
                        logger.error(f"Erro ao carregar cargas horÃ¡rias: {str(e)}")
                
                # Carregar cargas horÃ¡rias iniciais
                carregar_cargas_horarias()
                
                # BotÃ£o para atualizar listagem
                Button(listagem_frame, 
                       text="Atualizar Listagem",
                       command=carregar_cargas_horarias,
                       bg=self.co7,
                       fg=self.co1,
                       font=('Ivy 9'),
                       padx=10).pack(anchor=W, pady=5)
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar dados: {str(e)}")
                niveis = []
                nivel_var = StringVar(dialog)
                disciplinas_existentes = []
                ano_letivo_id = None
                carga_total_id = None
            
            # Frame para escolher qual nÃ­vel editar/visualizar
            escolha_frame = Frame(main_frame, bg=self.co10)
            escolha_frame.pack(fill=X, pady=5)
            
            Label(escolha_frame, text="Selecione o nÃ­vel para gerenciar disciplinas:", 
                 font=('Ivy 10'), bg=self.co10).pack(side=LEFT, padx=5)
            
            # BotÃ£o para carregar disciplinas do nÃ­vel selecionado
            carregar_btn = Button(
                escolha_frame,
                text="Carregar Disciplinas",
                command=lambda: carregar_disciplinas_nivel(),
                bg=self.co7,
                fg=self.co1,
                font=('Ivy 9'),
                padx=5
            )
            carregar_btn.pack(side=RIGHT, padx=5)
            
            # Separador
            ttk.Separator(main_frame, orient=HORIZONTAL).pack(fill=X, pady=10)
            
            # Frame para conter os campos de disciplinas com scrollbar
            canvas_frame = Frame(main_frame, bg=self.co10)
            canvas_frame.pack(fill=BOTH, expand=True, pady=10)

            canvas = Canvas(canvas_frame, bg=self.co10, highlightthickness=0)
            scrollbar = Scrollbar(canvas_frame, orient=VERTICAL, command=canvas.yview)
            
            disciplinas_frame = Frame(canvas, bg=self.co10)
            disciplinas_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=disciplinas_frame, anchor=NW, width=600)
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            # Lista para armazenar os widgets de disciplinas
            disciplina_widgets = []
            
            # FunÃ§Ã£o para adicionar um novo campo de disciplina (para nova disciplina)
            def adicionar_campo_disciplina(nome_disciplina="", carga_horaria="", disciplina_id=None):
                frame = Frame(disciplinas_frame, bg=self.co10, padx=5, pady=5, bd=1, relief=GROOVE)
                frame.pack(fill=X, expand=True, pady=5)
                
                # Combobox para seleÃ§Ã£o de disciplina
                Label(frame, text="Disciplina:", font=('Ivy 10'), bg=self.co10).grid(row=0, column=0, sticky=W, padx=5, pady=5)
                disciplina_var = StringVar(value=nome_disciplina)
                disciplina_cb = ttk.Combobox(frame, textvariable=disciplina_var, values=disciplinas, width=30)
                disciplina_cb.grid(row=0, column=1, sticky=W, padx=5, pady=5)
                
                # Permitir entrada de texto livre para novas disciplinas
                disciplina_cb['state'] = 'normal'
                
                # Campo para carga horÃ¡ria
                Label(frame, text="Carga HorÃ¡ria (opcional):", font=('Ivy 10'), bg=self.co10).grid(row=1, column=0, sticky=W, padx=5, pady=5)
                carga_horaria_entry = Entry(frame, width=10)
                carga_horaria_entry.insert(0, carga_horaria)
                carga_horaria_entry.grid(row=1, column=1, sticky=W, padx=5, pady=5)
                
                # Texto de status (para mostrar 'Nova' ou 'Existente')
                status_label = Label(
                    frame, 
                    text="Nova" if disciplina_id is None else "Existente", 
                    font=('Ivy 8 italic'),
                    bg=self.co10,
                    fg=self.co3 if disciplina_id is None else self.co7
                )
                status_label.grid(row=1, column=2, sticky=W, padx=5, pady=5)
                
                # BotÃ£o para remover este campo
                remove_btn = Button(
                    frame, 
                    text="âœ•",
                    command=lambda f=frame: remover_campo(f),
                    bg=self.co6,
                    fg=self.co1,
                    width=2,
                    font=('Ivy 8')
                )
                remove_btn.grid(row=0, column=3, sticky=E, padx=5, pady=5)
                
                # Armazenar widgets para recuperar valores depois
                widgets = {
                    'frame': frame,
                    'disciplina_var': disciplina_var,
                    'carga_horaria_entry': carga_horaria_entry,
                    'disciplina_id': disciplina_id  # None para novas, ID para existentes
                }
                disciplina_widgets.append(widgets)
                
                return frame
            
            # FunÃ§Ã£o para remover um campo de disciplina
            def remover_campo(frame):
                # Remover o widget da lista
                for i, widget_dict in enumerate(disciplina_widgets):
                    if widget_dict['frame'] == frame:
                        disciplina_widgets.pop(i)
                        break
                
                # Destruir o frame
                frame.destroy()
                
                # Atualizar canvas
                disciplinas_frame.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
            
            # FunÃ§Ã£o para limpar os campos de disciplina
            def limpar_campos_disciplina():
                # Destruir todos os frames de disciplina
                for widget_dict in disciplina_widgets[:]:
                    widget_dict['frame'].destroy()
                
                # Limpar a lista
                disciplina_widgets.clear()
                
                # Atualizar canvas
                disciplinas_frame.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
            
            # FunÃ§Ã£o para carregar disciplinas do nÃ­vel selecionado
            def carregar_disciplinas_nivel():
                try:
                    nivel_nome = nivel_var.get()
                    if not nivel_nome:
                        messagebox.showerror("Erro", "Por favor, selecione um nÃ­vel de ensino.")
                        return
                        
                    nivel_id = next((nivel[0] for nivel in niveis if nivel[1] == nivel_nome), None)
                    if nivel_id is None:
                        messagebox.showerror("Erro", "NÃ­vel de ensino selecionado nÃ£o encontrado.")
                        return
                    
                    # Atualizar variÃ¡veis globais
                    nonlocal disciplinas_existentes, nivel_atual_id
                    nivel_atual_id = nivel_id
                    
                    # Limpar campos existentes
                    limpar_campos_disciplina()
                    
                    # Obter disciplinas para este nÃ­vel
                    cast(Any, self.cursor).execute("""
                        SELECT id, nome, carga_horaria 
                        FROM disciplinas 
                        WHERE escola_id = %s AND nivel_id = %s
                        ORDER BY nome
                    """, (escola_id, nivel_id))
                    
                    disciplinas_nivel = self.cursor.fetchall()
                    disciplinas_existentes = disciplinas_nivel
                    
                    if not disciplinas_nivel:
                        messagebox.showinfo(
                            "InformaÃ§Ã£o", 
                            f"NÃ£o hÃ¡ disciplinas cadastradas para o nÃ­vel '{nivel_nome}'.\n"+
                            f"SerÃ£o adicionadas as disciplinas padrÃ£o abaixo. Ajuste conforme necessÃ¡rio."
                        )
                        # Adicionar as disciplinas padrÃ£o
                        for disciplina in disciplinas:
                            adicionar_campo_disciplina(nome_disciplina=disciplina, carga_horaria="")
                    else:
                        # Adicionar campos para as disciplinas existentes
                        for disciplina in disciplinas_nivel:
                            adicionar_campo_disciplina(
                                nome_disciplina=str(disciplina[1]),
                                carga_horaria=str(disciplina[2]),
                                disciplina_id=disciplina[0]
                            )
                    
                    # Atualizar canvas
                    disciplinas_frame.update_idletasks()
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao carregar disciplinas: {str(e)}")
            
            # Vincular evento de seleÃ§Ã£o do combobox de nÃ­vel
            nivel_menu.bind("<<ComboboxSelected>>", lambda e: carregar_disciplinas_nivel())
            
            # Se jÃ¡ temos disciplinas, carregar o nÃ­vel atual
            if disciplinas_existentes and nivel_atual_id:
                # Agrupar disciplinas por nÃ­vel
                niveis_info = {}
                for d in disciplinas_existentes:
                    nivel_id = d[3]
                    nivel_nome = d[4]
                    if nivel_id not in niveis_info:
                        niveis_info[nivel_id] = {'nome': nivel_nome, 'disciplinas': []}
                    niveis_info[nivel_id]['disciplinas'].append({
                        'id': d[0],
                        'nome': d[1],
                        'carga_horaria': d[2]
                    })
                
                # Mostrar contagem de disciplinas por nÃ­vel
                info_texto = "Disciplinas por nÃ­vel:\n"
                for nivel_id, info in niveis_info.items():
                    info_texto += f"â€¢ {info['nome']}: {len(info['disciplinas'])} disciplina(s)\n"
                
                info_label = Label(main_frame, text=info_texto, font=('Ivy 9'), 
                                  bg=self.co10, justify=LEFT)
                info_label.pack(fill=X, pady=5, anchor=W)
                
                # Carregar automaticamente as disciplinas do nÃ­vel selecionado
                self.master.after(100, carregar_disciplinas_nivel)
            else:
                # Se nÃ£o temos disciplinas, mostrar instruÃ§Ãµes
                instrucao = Label(main_frame, 
                                 text="Selecione um nÃ­vel de ensino e clique em 'Carregar Disciplinas'",
                                 font=('Ivy 10 italic'),
                                 bg=self.co10,
                                 fg=self.co12)
                instrucao.pack(pady=10)
                
                # Adicionar um campo vazio para iniciar
                adicionar_campo_disciplina()

            # Adicionar botÃ£o para incluir mais disciplinas
            def adicionar_mais_disciplinas():
                adicionar_campo_disciplina()
                # Atualizar canvas
                disciplinas_frame.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
                # Scrollar para o final
                canvas.yview_moveto(1.0)
            
            # BotÃ£o para adicionar mais disciplinas
            adicionar_btn = Button(
                main_frame, 
                text="+ Adicionar Mais Disciplinas",
                command=adicionar_mais_disciplinas,
                bg=self.co7,
                fg=self.co1,
                font=('Ivy 10 bold'),
                bd=0,
                padx=10,
                pady=5
            )
            adicionar_btn.pack(pady=10)
            
            # FunÃ§Ã£o para salvar as disciplinas
            def salvar_edicao():
                try:
                    nivel_nome = nivel_var.get()
                    if not nivel_nome:
                        messagebox.showerror("Erro", "Por favor, selecione um nÃ­vel de ensino.")
                        return
                        
                    nivel_id = next((nivel[0] for nivel in niveis if nivel[1] == nivel_nome), None)
                    if nivel_id is None:
                        messagebox.showerror("Erro", "NÃ­vel de ensino selecionado nÃ£o encontrado.")
                        return
                    
                    # Validar e coletar dados de cada disciplina
                    novas_disciplinas = []
                    disciplinas_atualizadas = []
                    ids_para_manter = []
                    
                    for widget_dict in disciplina_widgets:
                        nome_disciplina = widget_dict['disciplina_var'].get().strip()
                        carga_horaria = widget_dict['carga_horaria_entry'].get().strip()
                        disciplina_id = widget_dict['disciplina_id']
                        
                        # Verificar apenas se o nome da disciplina estÃ¡ preenchido
                        if nome_disciplina:
                            # Tratar carga horÃ¡ria (opcional)
                            carga_horaria_valor = None
                            if carga_horaria:
                                try:
                                    # Validar carga horÃ¡ria como nÃºmero quando presente
                                    carga_horaria_valor = int(carga_horaria)
                                except ValueError:
                                    messagebox.showerror("Erro", f"Carga horÃ¡ria para '{nome_disciplina}' deve ser um nÃºmero.")
                                    return
                            
                            if disciplina_id is None:
                                # Nova disciplina
                                novas_disciplinas.append((nome_disciplina, carga_horaria_valor))
                            else:
                                # Disciplina existente para atualizar
                                disciplinas_atualizadas.append((nome_disciplina, carga_horaria_valor, disciplina_id))
                                ids_para_manter.append(disciplina_id)
                    
                    # Verificar se hÃ¡ pelo menos uma disciplina para processar
                    if not novas_disciplinas and not disciplinas_atualizadas:
                        messagebox.showerror("Erro", "Pelo menos uma disciplina deve ser preenchida.")
                        return
                    
                    # Obter IDs de todas as disciplinas existentes deste nÃ­vel nesta escola
                    cast(Any, self.cursor).execute("""
                        SELECT id FROM disciplinas 
                        WHERE escola_id = %s AND nivel_id = %s
                    """, (escola_id, nivel_id))
                    
                    todas_disciplinas = [d[0] for d in self.cursor.fetchall()]
                    
                    # Determinar disciplinas para excluir (as que nÃ£o estÃ£o em ids_para_manter)
                    ids_para_excluir = [id for id in todas_disciplinas if id not in ids_para_manter]
                    
                    # Inserir, atualizar e excluir no banco de dados
                    disciplinas_adicionadas = 0
                    disciplinas_atualizadas_count = 0
                    disciplinas_excluidas = 0
                    
                    # 1. Adicionar novas disciplinas
                    for nome_disciplina, carga_horaria in novas_disciplinas:
                        cast(Any, self.cursor).execute("""
                            INSERT INTO disciplinas (nome, nivel_id, carga_horaria, escola_id)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            nome_disciplina,
                            nivel_id,
                            carga_horaria,  # Pode ser None agora
                            escola_id
                        ))
                        disciplinas_adicionadas += 1
                    
                    # 2. Atualizar disciplinas existentes
                    for nome_disciplina, carga_horaria, disciplina_id in disciplinas_atualizadas:
                        cast(Any, self.cursor).execute("""
                            UPDATE disciplinas
                            SET nome = %s, carga_horaria = %s, nivel_id = %s
                            WHERE id = %s
                        """, (
                            nome_disciplina,
                            carga_horaria,  # Pode ser None agora
                            nivel_id,
                            disciplina_id
                        ))
                        disciplinas_atualizadas_count += 1
                    
                    # 3. Excluir disciplinas removidas
                    for disciplina_id in ids_para_excluir:
                        cast(Any, self.cursor).execute("""
                            DELETE FROM disciplinas WHERE id = %s
                        """, (disciplina_id,))
                        disciplinas_excluidas += 1
                    
                    if hasattr(self,'conn') and self.conn:
                        cast(Any, self.conn).commit()
                    
                    # Processar carga horÃ¡ria total se fornecida
                    carga_total = carga_total_entry.get().strip()
                    if carga_total and ano_letivo_id:
                        try:
                            carga_total_valor = int(carga_total)
                            
                            if carga_total_id:
                                # Atualizar registro existente
                                cast(Any, self.cursor).execute("""
                                    UPDATE carga_horaria_total 
                                    SET carga_horaria_total = %s 
                                    WHERE id = %s
                                """, (carga_total_valor, carga_total_id))
                            else:
                                # Inserir novo registro
                                cast(Any, self.cursor).execute("""
                                    INSERT INTO carga_horaria_total 
                                    (serie_id, ano_letivo_id, escola_id, carga_horaria_total) 
                                    VALUES (%s, %s, %s, %s)
                                """, (nivel_id, ano_letivo_id, escola_id, carga_total_valor))
                            
                            if hasattr(self,'conn') and self.conn:
                                cast(Any, self.conn).commit()
                        except ValueError:
                            messagebox.showwarning("Aviso", "A carga horÃ¡ria total deve ser um nÃºmero inteiro. Este campo nÃ£o foi salvo.")
                        except Exception as e:
                            logger.error(f"Erro ao salvar carga horÃ¡ria total: {str(e)}")
                    
                    # Montar mensagem de sucesso
                    mensagem = "OperaÃ§Ãµes realizadas com sucesso!\n\n"
                    if disciplinas_adicionadas > 0:
                        mensagem += f"â€¢ {disciplinas_adicionadas} disciplina(s) adicionada(s)\n"
                    if disciplinas_atualizadas_count > 0:
                        mensagem += f"â€¢ {disciplinas_atualizadas_count} disciplina(s) atualizada(s)\n"
                    if disciplinas_excluidas > 0:
                        mensagem += f"â€¢ {disciplinas_excluidas} disciplina(s) excluÃ­da(s)\n"
                    
                    # Adicionar informaÃ§Ã£o sobre carga horÃ¡ria total
                    carga_total = carga_total_entry.get().strip()
                    if carga_total and ano_letivo_id:
                        try:
                            int(carga_total)  # Verificar se Ã© um nÃºmero vÃ¡lido (jÃ¡ validado anteriormente)
                            if carga_total_id:
                                mensagem += f"â€¢ Carga horÃ¡ria total atualizada para {carga_total} horas\n"
                            else:
                                mensagem += f"â€¢ Carga horÃ¡ria total definida como {carga_total} horas\n"
                        except ValueError:
                            pass  # Erro jÃ¡ tratado anteriormente
                    
                    messagebox.showinfo("Sucesso", mensagem)
                    dialog.destroy()
                    self.carregar_disciplinas(escola_id)
                    
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao processar disciplinas: {str(e)}")

            # Frame para botÃµes de aÃ§Ã£o
            botoes_frame = Frame(main_frame, bg=self.co10)
            botoes_frame.pack(fill=X, pady=10)
            
            # BotÃ£o para salvar
            Button(
                botoes_frame, 
                text="Salvar AlteraÃ§Ãµes",
                command=salvar_edicao,
                bg=self.co3,
                fg=self.co1,
                font=('Ivy 10 bold'),
                width=20,
                padx=10,
                pady=8
            ).pack(side=RIGHT, padx=5)
            
            # BotÃ£o para cancelar
            Button(
                botoes_frame, 
                text="Cancelar",
                command=dialog.destroy,
                bg=self.co12,
                fg=self.co1,
                font=('Ivy 10'),
                width=10,
                padx=10,
                pady=8
            ).pack(side=LEFT, padx=5)

        except IndexError:
            messagebox.showwarning("Aviso", "Por favor, selecione uma escola primeiro.")

    def editar_disciplina(self):
        try:
            selected_escola = self.tree_escolas.selection()[0]
            escola_id = self.tree_escolas.item(selected_escola, 'values')[0]
            escola_nome = self.tree_escolas.item(selected_escola, 'values')[1]

            # Inicializar variÃ¡veis
            disciplinas_existentes = []
            nivel_atual_id = None
            carga_total_id = None

            dialog = Toplevel(self.master)
            dialog.title(f"Gerenciar Disciplinas - {escola_nome}")
            dialog.geometry("650x650")  # Aumentei a altura da janela
            dialog.transient(self.master)
            dialog.focus_force()
            dialog.grab_set()
            dialog.configure(bg=self.co10)
            
            # Centralizar a janela
            self.centralizar_janela(dialog)

            # Criar um canvas com scrollbar para garantir que todo conteÃºdo seja acessÃ­vel
            canvas_principal = Canvas(dialog, bg=self.co10, highlightthickness=0)
            scrollbar_principal = Scrollbar(dialog, orient=VERTICAL, command=canvas_principal.yview)
            
            # Frame principal que vai conter todo o conteÃºdo
            master_frame = Frame(canvas_principal, bg=self.co10)
            
            # Configurar o canvas para rolar o frame principal quando seu tamanho mudar
            def configure_canvas(event):
                canvas_principal.configure(scrollregion=canvas_principal.bbox("all"))
                # Ajustar a largura do frame interno para corresponder ao canvas
                canvas_principal.itemconfig(frame_window, width=event.width)
            
            # Criar uma janela dentro do canvas que conterÃ¡ o frame principal
            frame_window = canvas_principal.create_window((0, 0), window=master_frame, anchor=NW)
            
            # Vincular eventos de redimensionamento
            master_frame.bind("<Configure>", configure_canvas)
            canvas_principal.bind("<Configure>", configure_canvas)
            
            # Configurar o scrollbar
            canvas_principal.configure(yscrollcommand=scrollbar_principal.set)
            
            # Empacotar canvas e scrollbar
            canvas_principal.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar_principal.pack(side=RIGHT, fill=Y)
            
            # Adicionar suporte para rolagem com mouse
            def _bind_mousewheel(event):
                canvas_principal.bind_all("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas_principal))
            
            def _unbind_mousewheel(event):
                canvas_principal.unbind_all("<MouseWheel>")
                
            canvas_principal.bind("<Enter>", _bind_mousewheel)
            canvas_principal.bind("<Leave>", _unbind_mousewheel)

            # Lista de disciplinas predefinidas
            disciplinas = [
                "LÃNGUA PORTUGUESA", "MATEMÃTICA", "HISTÃ“RIA", "GEOGRAFIA", "CIÃŠNCIAS",
                "ARTE", "ENSINO RELIGIOSO", "EDUCAÃ‡ÃƒO FÃSICA", "LÃNGUA INGLESA", "FILOSOFIA",
            ]
            
            # Frame principal com rolagem - agora serÃ¡ colocado dentro do master_frame
            main_frame = Frame(master_frame, bg=self.co10)
            main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
            
            # Carregar nÃ­veis do banco de dados
            try:
                cast(Any, self.cursor).execute("SELECT id, nome FROM niveisensino")
                niveis = self.cursor.fetchall()
                nivel_atual_id = None
                
                Label(main_frame, text="NÃ­vel de Ensino:", font=('Ivy 11 bold'), bg=self.co10).pack(anchor=W, pady=(0, 5))
                nivel_var = StringVar(dialog)
                nivel_menu = ttk.Combobox(main_frame, textvariable=nivel_var, values=[str(nivel[1]) for nivel in niveis], width=40)
                nivel_menu.pack(fill=X, pady=(0, 15))
                
                # Obter o ano letivo atual
                cast(Any, self.cursor).execute("SELECT id, ano_letivo FROM anosletivos WHERE ano_letivo = %s", (ANO_LETIVO_ATUAL,))
                resultado_ano = self.cursor.fetchone()
                
                if not resultado_ano:
                    # Se nÃ£o encontrar o ano atual, pegar o Ãºltimo registrado
                    cast(Any, self.cursor).execute("SELECT id, ano_letivo FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                    resultado_ano = self.cursor.fetchone()
                
                if resultado_ano:
                    ano_letivo_id, ano_letivo = resultado_ano
                else:
                    # Default se nÃ£o encontrar nenhum ano letivo
                    ano_letivo_id, ano_letivo = None, None
                
                # Frame para carga horÃ¡ria total (alternativa Ã s individuais)
                total_frame = Frame(main_frame, bg=self.co10, padx=10, pady=10, bd=1, relief=GROOVE)
                total_frame.pack(fill=X, pady=10)
                
                Label(total_frame, 
                     text="Carga HorÃ¡ria Total do NÃ­vel", 
                     font=('Ivy 11 bold'), 
                     bg=self.co10).pack(anchor=W)
                
                Label(total_frame, 
                     text="Insira a carga horÃ¡ria total quando nÃ£o especificar as cargas por disciplina",
                     font=('Ivy 9 italic'), 
                     bg=self.co10, 
                     fg=self.co12).pack(anchor=W, pady=(0, 5))
                
                # Frame para seleÃ§Ã£o de ano letivo e sÃ©rie
                selecao_frame = Frame(total_frame, bg=self.co10)
                selecao_frame.pack(fill=X, pady=5)
                
                # Carregar anos letivos
                cast(Any, self.cursor).execute("SELECT id, ano_letivo FROM anosletivos ORDER BY ano_letivo DESC")
                anos_letivos = self.cursor.fetchall()
                
                Label(selecao_frame, text="Ano Letivo:", bg=self.co10).pack(side=LEFT, padx=(0, 5))
                ano_var = StringVar(dialog)
                ano_menu = ttk.Combobox(selecao_frame, textvariable=ano_var, 
                                      values=[f"{ano[1]}" for ano in anos_letivos], 
                                      width=10)
                ano_menu.pack(side=LEFT, padx=5)
                
                # Carregar sÃ©ries/nÃ­veis
                cast(Any, self.cursor).execute("SELECT id, nome FROM series ORDER BY nome")
                series = self.cursor.fetchall()
                
                Label(selecao_frame, text="SÃ©rie:", bg=self.co10).pack(side=LEFT, padx=(20, 5))
                serie_var = StringVar(dialog)
                serie_menu = ttk.Combobox(selecao_frame, textvariable=serie_var, 
                                        values=[str(serie[1]) for serie in series], 
                                        width=20)
                serie_menu.pack(side=LEFT, padx=5)
                
                # Linha com campo de carga horÃ¡ria
                campos_frame = Frame(total_frame, bg=self.co10)
                campos_frame.pack(fill=X, pady=5)
                
                Label(campos_frame, text="Carga horÃ¡ria total:", bg=self.co10).pack(side=LEFT, padx=(0, 5))
                carga_total_entry = Entry(campos_frame, width=10)
                carga_total_entry.pack(side=LEFT, padx=5)
                
                # BotÃ£o para adicionar nova carga horÃ¡ria
                def adicionar_carga_horaria():
                    try:
                        ano_selecionado = ano_var.get()
                        serie_selecionada = serie_var.get()
                        carga_horaria = carga_total_entry.get().strip()
                        
                        if not ano_selecionado or not serie_selecionada or not carga_horaria:
                            messagebox.showerror("Erro", "Por favor, preencha todos os campos.")
                            return
                            
                        # Obter IDs
                        ano_id = next((ano[0] for ano in anos_letivos if str(ano[1]) == ano_selecionado), None)
                        serie_id = next((serie[0] for serie in series if serie[1] == serie_selecionada), None)
                        
                        if not ano_id or not serie_id:
                            messagebox.showerror("Erro", "Erro ao identificar ano letivo ou sÃ©rie.")
                            return
                            
                        try:
                            carga_horaria_valor = int(carga_horaria)
                        except ValueError:
                            messagebox.showerror("Erro", "A carga horÃ¡ria deve ser um nÃºmero inteiro.")
                            return
                        
                        # Verificar se jÃ¡ existe um registro para esta combinaÃ§Ã£o
                        cast(Any, self.cursor).execute("""
                            SELECT id FROM carga_horaria_total 
                            WHERE serie_id = %s AND escola_id = %s AND ano_letivo_id = %s
                        """, (serie_id, escola_id, ano_id))
                        
                        resultado = self.cursor.fetchone()
                        
                        if resultado:
                            # Atualizar registro existente
                            cast(Any, self.cursor).execute("""
                                UPDATE carga_horaria_total 
                                SET carga_horaria_total = %s 
                                WHERE id = %s
                            """, (carga_horaria_valor, resultado[0]))
                            mensagem = "Carga horÃ¡ria total atualizada com sucesso!"
                        else:
                            # Inserir novo registro
                            cast(Any, self.cursor).execute("""
                                INSERT INTO carga_horaria_total 
                                (serie_id, ano_letivo_id, escola_id, carga_horaria_total) 
                                VALUES (%s, %s, %s, %s)
                            """, (serie_id, ano_id, escola_id, carga_horaria_valor))
                            mensagem = "Carga horÃ¡ria total adicionada com sucesso!"
                        
                        if hasattr(self,'conn') and self.conn:
                            cast(Any, self.conn).commit()
                        messagebox.showinfo("Sucesso", mensagem)
                        
                        # Limpar campos
                        carga_total_entry.delete(0, END)
                        
                    except Exception as e:
                        messagebox.showerror("Erro", f"Erro ao processar carga horÃ¡ria: {str(e)}")
                
                # BotÃ£o para adicionar
                Button(campos_frame, 
                       text="Adicionar Carga HorÃ¡ria",
                       command=adicionar_carga_horaria,
                       bg=self.co3,
                       fg=self.co1,
                       font=('Ivy 9'),
                       padx=10).pack(side=LEFT, padx=(20, 0))
                
                # Frame para mostrar cargas horÃ¡rias existentes
                listagem_frame = Frame(total_frame, bg=self.co10)
                listagem_frame.pack(fill=X, pady=10)
                
                Label(listagem_frame, 
                     text="Cargas HorÃ¡rias Cadastradas:", 
                     font=('Ivy 10 bold'),
                     bg=self.co10).pack(anchor=W)
                
                # Criar Treeview para mostrar cargas horÃ¡rias
                tree_frame = Frame(listagem_frame, bg=self.co10)
                tree_frame.pack(fill=X, pady=5)
                
                # Scrollbar para a treeview
                scrollbar = ttk.Scrollbar(tree_frame)
                scrollbar.pack(side=RIGHT, fill=Y)
                
                # Treeview para cargas horÃ¡rias
                carga_tree = ttk.Treeview(tree_frame, 
                                        columns=("Ano", "SÃ©rie", "Carga"),
                                        show='headings',
                                        yscrollcommand=scrollbar.set)
                
                carga_tree.heading("Ano", text="Ano Letivo")
                carga_tree.heading("SÃ©rie", text="SÃ©rie")
                carga_tree.heading("Carga", text="Carga HorÃ¡ria")
                
                carga_tree.column("Ano", width=100)
                carga_tree.column("SÃ©rie", width=150)
                carga_tree.column("Carga", width=100)
                
                carga_tree.pack(side=LEFT, fill=X, expand=True)
                scrollbar.config(command=carga_tree.yview)
                
                # FunÃ§Ã£o para carregar cargas horÃ¡rias
                def carregar_cargas_horarias():
                    # Limpar treeview
                    for item in carga_tree.get_children():
                        carga_tree.delete(item)
                    
                    try:
                        # Buscar cargas horÃ¡rias
                        cast(Any, self.cursor).execute("""
                            SELECT cht.id, cht.carga_horaria_total, al.ano_letivo, s.nome
                            FROM carga_horaria_total cht
                            JOIN anosletivos al ON cht.ano_letivo_id = al.id
                            JOIN series s ON cht.serie_id = s.id
                            WHERE cht.escola_id = %s
                            ORDER BY al.ano_letivo DESC, s.nome
                        """, (escola_id,))
                        
                        cargas = self.cursor.fetchall()
                        
                        for carga in cargas:
                            carga_tree.insert('', 'end', values=(
                                carga[2],  # ano_letivo
                                carga[3],  # nome da sÃ©rie
                                carga[1]   # carga_horaria_total
                            ))
                            
                    except Exception as e:
                        logger.error(f"Erro ao carregar cargas horÃ¡rias: {str(e)}")
                
                # Carregar cargas horÃ¡rias iniciais
                carregar_cargas_horarias()
                
                # BotÃ£o para atualizar listagem
                Button(listagem_frame, 
                       text="Atualizar Listagem",
                       command=carregar_cargas_horarias,
                       bg=self.co7,
                       fg=self.co1,
                       font=('Ivy 9'),
                       padx=10).pack(anchor=W, pady=5)
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar dados: {str(e)}")
                niveis = []
                nivel_var = StringVar(dialog)
                disciplinas_existentes = []
                ano_letivo_id = None
                carga_total_id = None
            
            # Frame para escolher qual nÃ­vel editar/visualizar
            escolha_frame = Frame(main_frame, bg=self.co10)
            escolha_frame.pack(fill=X, pady=5)
            
            Label(escolha_frame, text="Selecione o nÃ­vel para gerenciar disciplinas:", 
                 font=('Ivy 10'), bg=self.co10).pack(side=LEFT, padx=5)
            
            # BotÃ£o para carregar disciplinas do nÃ­vel selecionado
            carregar_btn = Button(
                escolha_frame,
                text="Carregar Disciplinas",
                command=lambda: carregar_disciplinas_nivel(),
                bg=self.co7,
                fg=self.co1,
                font=('Ivy 9'),
                padx=5
            )
            carregar_btn.pack(side=RIGHT, padx=5)
            
            # Separador
            ttk.Separator(main_frame, orient=HORIZONTAL).pack(fill=X, pady=10)
            
            # Frame para conter os campos de disciplinas com scrollbar
            canvas_frame = Frame(main_frame, bg=self.co10)
            canvas_frame.pack(fill=BOTH, expand=True, pady=10)

            canvas = Canvas(canvas_frame, bg=self.co10, highlightthickness=0)
            scrollbar = Scrollbar(canvas_frame, orient=VERTICAL, command=canvas.yview)
            
            disciplinas_frame = Frame(canvas, bg=self.co10)
            disciplinas_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=disciplinas_frame, anchor=NW, width=600)
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            # Lista para armazenar os widgets de disciplinas
            disciplina_widgets = []
            
            # FunÃ§Ã£o para adicionar um novo campo de disciplina (para nova disciplina)
            def adicionar_campo_disciplina(nome_disciplina="", carga_horaria="", disciplina_id=None):
                frame = Frame(disciplinas_frame, bg=self.co10, padx=5, pady=5, bd=1, relief=GROOVE)
                frame.pack(fill=X, expand=True, pady=5)
                
                # Combobox para seleÃ§Ã£o de disciplina
                Label(frame, text="Disciplina:", font=('Ivy 10'), bg=self.co10).grid(row=0, column=0, sticky=W, padx=5, pady=5)
                disciplina_var = StringVar(value=nome_disciplina)
                disciplina_cb = ttk.Combobox(frame, textvariable=disciplina_var, values=disciplinas, width=30)
                disciplina_cb.grid(row=0, column=1, sticky=W, padx=5, pady=5)
                
                # Permitir entrada de texto livre para novas disciplinas
                disciplina_cb['state'] = 'normal'
                
                # Campo para carga horÃ¡ria
                Label(frame, text="Carga HorÃ¡ria (opcional):", font=('Ivy 10'), bg=self.co10).grid(row=1, column=0, sticky=W, padx=5, pady=5)
                carga_horaria_entry = Entry(frame, width=10)
                carga_horaria_entry.insert(0, carga_horaria)
                carga_horaria_entry.grid(row=1, column=1, sticky=W, padx=5, pady=5)
                
                # Texto de status (para mostrar 'Nova' ou 'Existente')
                status_label = Label(
                    frame, 
                    text="Nova" if disciplina_id is None else "Existente", 
                    font=('Ivy 8 italic'),
                    bg=self.co10,
                    fg=self.co3 if disciplina_id is None else self.co7
                )
                status_label.grid(row=1, column=2, sticky=W, padx=5, pady=5)
                
                # BotÃ£o para remover este campo
                remove_btn = Button(
                    frame, 
                    text="âœ•",
                    command=lambda f=frame: remover_campo(f),
                    bg=self.co6,
                    fg=self.co1,
                    width=2,
                    font=('Ivy 8')
                )
                remove_btn.grid(row=0, column=3, sticky=E, padx=5, pady=5)
                
                # Armazenar widgets para recuperar valores depois
                widgets = {
                    'frame': frame,
                    'disciplina_var': disciplina_var,
                    'carga_horaria_entry': carga_horaria_entry,
                    'disciplina_id': disciplina_id  # None para novas, ID para existentes
                }
                disciplina_widgets.append(widgets)
                
                return frame
            
            # FunÃ§Ã£o para remover um campo de disciplina
            def remover_campo(frame):
                # Remover o widget da lista
                for i, widget_dict in enumerate(disciplina_widgets):
                    if widget_dict['frame'] == frame:
                        disciplina_widgets.pop(i)
                        break
                
                # Destruir o frame
                frame.destroy()
                
                # Atualizar canvas
                disciplinas_frame.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
            
            # FunÃ§Ã£o para limpar os campos de disciplina
            def limpar_campos_disciplina():
                # Destruir todos os frames de disciplina
                for widget_dict in disciplina_widgets[:]:
                    widget_dict['frame'].destroy()
                
                # Limpar a lista
                disciplina_widgets.clear()
                
                # Atualizar canvas
                disciplinas_frame.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
            
            # FunÃ§Ã£o para carregar disciplinas do nÃ­vel selecionado
            def carregar_disciplinas_nivel():
                try:
                    nivel_nome = nivel_var.get()
                    if not nivel_nome:
                        messagebox.showerror("Erro", "Por favor, selecione um nÃ­vel de ensino.")
                        return
                        
                    nivel_id = next((nivel[0] for nivel in niveis if nivel[1] == nivel_nome), None)
                    if nivel_id is None:
                        messagebox.showerror("Erro", "NÃ­vel de ensino selecionado nÃ£o encontrado.")
                        return
                    
                    # Atualizar variÃ¡veis globais
                    nonlocal disciplinas_existentes, nivel_atual_id
                    nivel_atual_id = nivel_id
                    
                    # Limpar campos existentes
                    limpar_campos_disciplina()
                    
                    # Obter disciplinas para este nÃ­vel
                    cast(Any, self.cursor).execute("""
                        SELECT id, nome, carga_horaria 
                        FROM disciplinas 
                        WHERE escola_id = %s AND nivel_id = %s
                        ORDER BY nome
                    """, (escola_id, nivel_id))
                    
                    disciplinas_nivel = self.cursor.fetchall()
                    disciplinas_existentes = disciplinas_nivel
                    
                    if not disciplinas_nivel:
                        messagebox.showinfo(
                            "InformaÃ§Ã£o", 
                            f"NÃ£o hÃ¡ disciplinas cadastradas para o nÃ­vel '{nivel_nome}'.\n"+
                            f"SerÃ£o adicionadas as disciplinas padrÃ£o abaixo. Ajuste conforme necessÃ¡rio."
                        )
                        # Adicionar as disciplinas padrÃ£o
                        for disciplina in disciplinas:
                            adicionar_campo_disciplina(nome_disciplina=disciplina, carga_horaria="")
                    else:
                        # Adicionar campos para as disciplinas existentes
                        for disciplina in disciplinas_nivel:
                            adicionar_campo_disciplina(
                                nome_disciplina=str(disciplina[1]),
                                carga_horaria=str(disciplina[2]),
                                disciplina_id=disciplina[0]
                            )
                    
                    # Atualizar canvas
                    disciplinas_frame.update_idletasks()
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao carregar disciplinas: {str(e)}")
            
            # Vincular evento de seleÃ§Ã£o do combobox de nÃ­vel
            nivel_menu.bind("<<ComboboxSelected>>", lambda e: carregar_disciplinas_nivel())
            
            # Se jÃ¡ temos disciplinas, carregar o nÃ­vel atual
            if disciplinas_existentes and nivel_atual_id:
                # Agrupar disciplinas por nÃ­vel
                niveis_info = {}
                for d in disciplinas_existentes:
                    nivel_id = d[3]
                    nivel_nome = d[4]
                    if nivel_id not in niveis_info:
                        niveis_info[nivel_id] = {'nome': nivel_nome, 'disciplinas': []}
                    niveis_info[nivel_id]['disciplinas'].append({
                        'id': d[0],
                        'nome': d[1],
                        'carga_horaria': d[2]
                    })
                
                # Mostrar contagem de disciplinas por nÃ­vel
                info_texto = "Disciplinas por nÃ­vel:\n"
                for nivel_id, info in niveis_info.items():
                    info_texto += f"â€¢ {info['nome']}: {len(info['disciplinas'])} disciplina(s)\n"
                
                info_label = Label(main_frame, text=info_texto, font=('Ivy 9'), 
                                  bg=self.co10, justify=LEFT)
                info_label.pack(fill=X, pady=5, anchor=W)
                
                # Carregar automaticamente as disciplinas do nÃ­vel selecionado
                self.master.after(100, carregar_disciplinas_nivel)
            else:
                # Se nÃ£o temos disciplinas, mostrar instruÃ§Ãµes
                instrucao = Label(main_frame, 
                                 text="Selecione um nÃ­vel de ensino e clique em 'Carregar Disciplinas'",
                                 font=('Ivy 10 italic'),
                                 bg=self.co10,
                                 fg=self.co12)
                instrucao.pack(pady=10)
                
                # Adicionar um campo vazio para iniciar
                adicionar_campo_disciplina()

            # Adicionar botÃ£o para incluir mais disciplinas
            def adicionar_mais_disciplinas():
                adicionar_campo_disciplina()
                # Atualizar canvas
                disciplinas_frame.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
                # Scrollar para o final
                canvas.yview_moveto(1.0)
            
            # BotÃ£o para adicionar mais disciplinas
            adicionar_btn = Button(
                main_frame, 
                text="+ Adicionar Mais Disciplinas",
                command=adicionar_mais_disciplinas,
                bg=self.co7,
                fg=self.co1,
                font=('Ivy 10 bold'),
                bd=0,
                padx=10,
                pady=5
            )
            adicionar_btn.pack(pady=10)
            
            # FunÃ§Ã£o para salvar as disciplinas
            def salvar_edicao():
                try:
                    nivel_nome = nivel_var.get()
                    if not nivel_nome:
                        messagebox.showerror("Erro", "Por favor, selecione um nÃ­vel de ensino.")
                        return
                        
                    nivel_id = next((nivel[0] for nivel in niveis if nivel[1] == nivel_nome), None)
                    if nivel_id is None:
                        messagebox.showerror("Erro", "NÃ­vel de ensino selecionado nÃ£o encontrado.")
                        return
                    
                    # Validar e coletar dados de cada disciplina
                    novas_disciplinas = []
                    disciplinas_atualizadas = []
                    ids_para_manter = []
                    
                    for widget_dict in disciplina_widgets:
                        nome_disciplina = widget_dict['disciplina_var'].get().strip()
                        carga_horaria = widget_dict['carga_horaria_entry'].get().strip()
                        disciplina_id = widget_dict['disciplina_id']
                        
                        # Verificar apenas se o nome da disciplina estÃ¡ preenchido
                        if nome_disciplina:
                            # Tratar carga horÃ¡ria (opcional)
                            carga_horaria_valor = None
                            if carga_horaria:
                                try:
                                    # Validar carga horÃ¡ria como nÃºmero quando presente
                                    carga_horaria_valor = int(carga_horaria)
                                except ValueError:
                                    messagebox.showerror("Erro", f"Carga horÃ¡ria para '{nome_disciplina}' deve ser um nÃºmero.")
                                    return
                            
                            if disciplina_id is None:
                                # Nova disciplina
                                novas_disciplinas.append((nome_disciplina, carga_horaria_valor))
                            else:
                                # Disciplina existente para atualizar
                                disciplinas_atualizadas.append((nome_disciplina, carga_horaria_valor, disciplina_id))
                                ids_para_manter.append(disciplina_id)
                    
                    # Verificar se hÃ¡ pelo menos uma disciplina para processar
                    if not novas_disciplinas and not disciplinas_atualizadas:
                        messagebox.showerror("Erro", "Pelo menos uma disciplina deve ser preenchida.")
                        return
                    
                    # Obter IDs de todas as disciplinas existentes deste nÃ­vel nesta escola
                    cast(Any, self.cursor).execute("""
                        SELECT id FROM disciplinas 
                        WHERE escola_id = %s AND nivel_id = %s
                    """, (escola_id, nivel_id))
                    
                    todas_disciplinas = [d[0] for d in self.cursor.fetchall()]
                    
                    # Determinar disciplinas para excluir (as que nÃ£o estÃ£o em ids_para_manter)
                    ids_para_excluir = [id for id in todas_disciplinas if id not in ids_para_manter]
                    
                    # Inserir, atualizar e excluir no banco de dados
                    disciplinas_adicionadas = 0
                    disciplinas_atualizadas_count = 0
                    disciplinas_excluidas = 0
                    
                    # 1. Adicionar novas disciplinas
                    for nome_disciplina, carga_horaria in novas_disciplinas:
                        cast(Any, self.cursor).execute("""
                            INSERT INTO disciplinas (nome, nivel_id, carga_horaria, escola_id)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            nome_disciplina,
                            nivel_id,
                            carga_horaria,  # Pode ser None agora
                            escola_id
                        ))
                        disciplinas_adicionadas += 1
                    
                    # 2. Atualizar disciplinas existentes
                    for nome_disciplina, carga_horaria, disciplina_id in disciplinas_atualizadas:
                        cast(Any, self.cursor).execute("""
                            UPDATE disciplinas
                            SET nome = %s, carga_horaria = %s, nivel_id = %s
                            WHERE id = %s
                        """, (
                            nome_disciplina,
                            carga_horaria,  # Pode ser None agora
                            nivel_id,
                            disciplina_id
                        ))
                        disciplinas_atualizadas_count += 1
                    
                    # 3. Excluir disciplinas removidas
                    for disciplina_id in ids_para_excluir:
                        cast(Any, self.cursor).execute("""
                            DELETE FROM disciplinas WHERE id = %s
                        """, (disciplina_id,))
                        disciplinas_excluidas += 1

                    if hasattr(self,'conn') and self.conn:
                        cast(Any, self.conn).commit()
                    
                    # Processar carga horÃ¡ria total se fornecida
                    carga_total = carga_total_entry.get().strip()
                    if carga_total and ano_letivo_id:
                        try:
                            carga_total_valor = int(carga_total)
                            
                            if carga_total_id:
                                # Atualizar registro existente
                                cast(Any, self.cursor).execute("""
                                    UPDATE carga_horaria_total 
                                    SET carga_horaria_total = %s 
                                    WHERE id = %s
                                """, (carga_total_valor, carga_total_id))
                            else:
                                # Inserir novo registro
                                cast(Any, self.cursor).execute("""
                                    INSERT INTO carga_horaria_total 
                                    (serie_id, ano_letivo_id, escola_id, carga_horaria_total) 
                                    VALUES (%s, %s, %s, %s)
                                """, (nivel_id, ano_letivo_id, escola_id, carga_total_valor))
                            
                            if hasattr(self,'conn') and self.conn:
                                cast(Any, self.conn).commit()
                        except ValueError:
                            messagebox.showwarning("Aviso", "A carga horÃ¡ria total deve ser um nÃºmero inteiro. Este campo nÃ£o foi salvo.")
                        except Exception as e:
                            logger.error(f"Erro ao salvar carga horÃ¡ria total: {str(e)}")
                    
                    # Montar mensagem de sucesso
                    mensagem = "OperaÃ§Ãµes realizadas com sucesso!\n\n"
                    if disciplinas_adicionadas > 0:
                        mensagem += f"â€¢ {disciplinas_adicionadas} disciplina(s) adicionada(s)\n"
                    if disciplinas_atualizadas_count > 0:
                        mensagem += f"â€¢ {disciplinas_atualizadas_count} disciplina(s) atualizada(s)\n"
                    if disciplinas_excluidas > 0:
                        mensagem += f"â€¢ {disciplinas_excluidas} disciplina(s) excluÃ­da(s)\n"
                    
                    # Adicionar informaÃ§Ã£o sobre carga horÃ¡ria total
                    carga_total = carga_total_entry.get().strip()
                    if carga_total and ano_letivo_id:
                        try:
                            int(carga_total)  # Verificar se Ã© um nÃºmero vÃ¡lido (jÃ¡ validado anteriormente)
                            if carga_total_id:
                                mensagem += f"â€¢ Carga horÃ¡ria total atualizada para {carga_total} horas\n"
                            else:
                                mensagem += f"â€¢ Carga horÃ¡ria total definida como {carga_total} horas\n"
                        except ValueError:
                            pass  # Erro jÃ¡ tratado anteriormente
                    
                    messagebox.showinfo("Sucesso", mensagem)
                    dialog.destroy()
                    self.carregar_disciplinas(escola_id)
                    
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao processar disciplinas: {str(e)}")

            # Frame para botÃµes de aÃ§Ã£o
            botoes_frame = Frame(main_frame, bg=self.co10)
            botoes_frame.pack(fill=X, pady=10)
            
            # BotÃ£o para salvar
            Button(
                botoes_frame, 
                text="Salvar AlteraÃ§Ãµes",
                command=salvar_edicao,
                bg=self.co3,
                fg=self.co1,
                font=('Ivy 10 bold'),
                width=20,
                padx=10,
                pady=8
            ).pack(side=RIGHT, padx=5)
            
            # BotÃ£o para cancelar
            Button(
                botoes_frame, 
                text="Cancelar",
                command=dialog.destroy,
                bg=self.co12,
                fg=self.co1,
                font=('Ivy 10'),
                width=10,
                padx=10,
                pady=8
            ).pack(side=LEFT, padx=5)

        except IndexError:
            messagebox.showwarning("Aviso", "Por favor, selecione uma escola primeiro.")

    def centralizar_janela(self, janela):
        """
        Centraliza uma janela na tela.
        """
        # Atualizar a janela para garantir que os widgets sejam medidos corretamente
        janela.update_idletasks()
        
        # Obter as dimensÃµes da tela
        largura_tela = janela.winfo_screenwidth()
        altura_tela = janela.winfo_screenheight()
        
        # Obter as dimensÃµes da janela
        largura_janela = janela.winfo_width()
        altura_janela = janela.winfo_height()
        
        # Calcular a posiÃ§Ã£o para centralizar
        x = (largura_tela - largura_janela) // 2
        y = (altura_tela - altura_janela) // 2
        
        # Definir a posiÃ§Ã£o da janela
        janela.geometry(f"+{x}+{y}")
        
        # Adicionar teclas de atalho para facilitar a navegaÃ§Ã£o
        def on_page_up(event):
            for canvas in janela.winfo_children():
                if isinstance(canvas, Canvas):
                    canvas.yview_scroll(-5, "units")
        
        def on_page_down(event):
            for canvas in janela.winfo_children():
                if isinstance(canvas, Canvas):
                    canvas.yview_scroll(5, "units")
        
        # Vincular teclas de atalho
        janela.bind("<Prior>", on_page_up)  # Page Up
        janela.bind("<Next>", on_page_down)  # Page Down

    def pesquisar_escolas(self, event=None):
        """
        Pesquisa escolas com base no termo inserido pelo usuÃ¡rio.
        Pode ser chamado por evento (pressionar Enter) ou pelo botÃ£o de pesquisa.
        """
        # Obter o termo de pesquisa
        termo = self.entrada_pesquisa.get().strip()
        
        # Ignorar o texto de ajuda
        if termo == "Digite o nome, INEP, CNPJ ou municÃ­pio":
            termo = ""
        
        # Se o termo estiver vazio, carregar todas as escolas
        if not termo:
            self.carregar_escolas()
            return
            
        # Limpar a tabela
        for item in self.tree_escolas.get_children():
            self.tree_escolas.delete(item)
            
        # Remover status labels anteriores se existirem
        for widget in self.frame_escolas.winfo_children():
            if isinstance(widget, Label) and (widget.cget("text").startswith("Total de escolas:") or 
                                             widget.cget("text").startswith("Encontradas") or
                                             widget.cget("text").startswith("Nenhuma escola")):
                widget.destroy()
            elif isinstance(widget, Frame) and len(widget.winfo_children()) > 0:
                for child in widget.winfo_children():
                    if isinstance(child, Label) and (child.cget("text").startswith("Total de escolas:") or 
                                                   child.cget("text").startswith("Encontradas") or
                                                   child.cget("text").startswith("Nenhuma escola")):
                        widget.destroy()
                        break
            
        try:
            # Consulta SQL com like para pesquisar pelo nome, INEP, CNPJ ou municÃ­pio
            cast(Any, self.cursor).execute("""
                SELECT id, nome, endereco, inep,
                CONCAT(
                    SUBSTR(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), 1, 2), '.',
                    SUBSTR(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), 3, 3), '.',
                    SUBSTR(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), 6, 3), '/',
                    SUBSTR(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), 9, 4), '-',
                    SUBSTR(REPLACE(REPLACE(REPLACE(cnpj, '.', ''), '/', ''), '-', ''), 13, 2)
                ) AS cnpj,
                municipio 
                FROM escolas
                WHERE nome LIKE %s 
                OR inep LIKE %s 
                OR cnpj LIKE %s 
                OR municipio LIKE %s
                ORDER BY nome
            """, (f"%{termo}%", f"%{termo}%", f"%{termo}%", f"%{termo}%"))
            
            # Preencher a tabela com os resultados
            escolas = self.cursor.fetchall()
            
            # Criar um frame para a mensagem de status
            status_frame = Frame(self.frame_escolas, padx=5, pady=3)
            status_frame.pack(anchor=E, padx=10, pady=5)
            
            if not escolas:
                # Se nÃ£o houver resultados, mostrar mensagem com fundo vermelho claro
                status_frame.configure(bg='#ffebee')  # Vermelho muito claro
                status_label = Label(status_frame, 
                                   text=f"Nenhuma escola encontrada para: '{termo}'", 
                                   font=('Ivy', 9, 'bold'),
                                   bg='#ffebee', 
                                   fg=self.co6)
                status_label.pack()
            else:
                # Adicionar as escolas encontradas Ã  tabela
                for escola in escolas:
                    self.tree_escolas.insert('', 'end', values=escola)
                
                # Mostrar nÃºmero de resultados encontrados com fundo verde claro
                status_frame.configure(bg='#e8f5e9')  # Verde muito claro
                status_label = Label(status_frame, 
                                   text=f"Encontradas {len(escolas)} escolas para: '{termo}'", 
                                   font=('Ivy', 9, 'bold'),
                                   bg='#e8f5e9', 
                                   fg=self.co3)
                status_label.pack()
                    
            # Configurar remoÃ§Ã£o automÃ¡tica apÃ³s alguns segundos
            self.master.after(5000, status_frame.destroy)
                    
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao pesquisar escolas: {str(e)}")

    def on_window_resize(self, event=None):
        """
        Ajusta os elementos da interface quando a janela Ã© redimensionada.
        """
        # SÃ³ processar quando o evento for da janela principal
        # Proteger contra chamada sem evento (event pode ser None)
        if event is None or getattr(event, 'widget', None) != self.master:
            return
            
        # Re-configurar larguras das colunas proporcionalmente ao tamanho da janela
        window_width = self.master.winfo_width()
        
        # Ajustar colunas da tabela de escolas (se existir)
        if hasattr(self, 'tree_escolas'):
            if window_width > 900:
                # Para janelas grandes, ajustar proporcionalmente
                self.tree_escolas.column("ID", width=int(window_width * 0.05))
                self.tree_escolas.column("Nome", width=int(window_width * 0.25))
                self.tree_escolas.column("EndereÃ§o", width=int(window_width * 0.25))
                self.tree_escolas.column("INEP", width=int(window_width * 0.10))
                self.tree_escolas.column("CNPJ", width=int(window_width * 0.15))
                self.tree_escolas.column("MunicÃ­pio", width=int(window_width * 0.15))
                
        # Ajustar colunas da tabela de disciplinas (se existir)
        if hasattr(self, 'tree_disciplinas'):
            if window_width > 900:
                # Para janelas grandes, ajustar proporcionalmente
                self.tree_disciplinas.column("ID", width=int(window_width * 0.05))
                self.tree_disciplinas.column("Nome", width=int(window_width * 0.40))
                self.tree_disciplinas.column("NÃ­vel", width=int(window_width * 0.30))
                self.tree_disciplinas.column("Carga HorÃ¡ria", width=int(window_width * 0.20))

    def alternar_tela_cheia(self):
        """
        Alterna entre o modo de tela normal e tela cheia/maximizada.
        """
        if self.tela_cheia:
            # Voltar para o tamanho normal
            self.master.state('normal')
            self.btn_maximizar.config(text="Maximizar")
            self.tela_cheia = False
        else:
            # Maximizar a janela
            self.master.state('zoomed')
            self.btn_maximizar.config(text="Restaurar")
            self.tela_cheia = True
        
        # ForÃ§ar ajuste das colunas apÃ³s redimensionamento
        self.master.update_idletasks()  # Garante que a janela foi redimensionada antes de ajustar
        
        # Criar um evento de redimensionamento simulado
        event = type('Event', (), {'widget': self.master})
        self.on_window_resize(event)  # Chama o mÃ©todo de redimensionamento com o evento simulado

    def _on_mousewheel(self, event, canvas):
        """
        Permite a rolagem do canvas com a roda do mouse.
        CompatÃ­vel com Windows e outros sistemas.
        """
        try:
            # No Windows, event.delta funciona diretamente
            if hasattr(event, 'num') and event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
                # Rolagem para baixo
                canvas.yview_scroll(1, "units")
            elif hasattr(event, 'num') and event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
                # Rolagem para cima
                canvas.yview_scroll(-1, "units")
        except Exception as e:
            # Em caso de erro, apenas ignorar para nÃ£o afetar a experiÃªncia do usuÃ¡rio
            logger.error(f"Erro ao processar rolagem do mouse: {str(e)}")

    def __del__(self):
        # MÃ©todo nÃ£o Ã© mais necessÃ¡rio pois a limpeza estÃ¡ em fechar_janela
        pass
