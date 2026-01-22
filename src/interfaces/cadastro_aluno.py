from src.core.config_logs import get_logger
from src.core.config import get_icon_path
logger = get_logger(__name__)
from datetime import datetime
from tkinter import (
    Label, Frame, Button, Entry, Toplevel, Canvas, Scrollbar,
    NW, LEFT, RIGHT, TOP, BOTTOM, W, E, N, S,
    BOTH, X, Y, VERTICAL, HORIZONTAL, END,
    TRUE, FALSE, GROOVE, RAISED, FLAT, RIDGE, StringVar
)
from tkinter import messagebox, ttk
from PIL import ImageTk, Image
import mysql.connector
from mysql.connector import Error
from src.core.conexao import conectar_bd
from db.connection import get_connection, get_cursor
from tkcalendar import DateEntry
from typing import Any, cast

# Constante útil para `sticky` em grids (N, S, E, W concatenados)
NSEW = N + E + S + W

class InterfaceCadastroAluno:
    def __init__(self, master, janela_principal=None):
        # Armazenar a referência da janela principal
        self.janela_principal = janela_principal
        
        # Variável para controlar se um aluno foi cadastrado com sucesso
        self.aluno_cadastrado = False
        
        # Se a janela principal foi fornecida, escondê-la
        if self.janela_principal:
            self.janela_principal.withdraw()
        
        # Variáveis globais
        self.lista_frames_responsaveis = []
        self.contador_responsaveis = 0
        self.opcoes_parentesco = ["Mãe", "Pai", "Tio", "Tia", "Avô", "Avó", "Outro"]
        
        # Cores
        self.co0 = "#2e2d2b"  # preta
        self.co1 = "#feffff"  # Branca
        self.co2 = "#e5e5e5"  # Cinza
        self.co3 = "#00a095"  # Verde 
        self.co4 = "#403d3d"  # Letra
        self.co5 = "#003452"  # Azul
        self.co6 = "#ef5350"  # Vermelho
        self.co7 = "#038cfc"  # azul
        self.co8 = "#263238"  # +verde
        self.co9 = "#e9edf5"  # +verde

        self.master = master
        self.master.title("Cadastro de Aluno")
        self.master.geometry('950x670')
        self.master.configure(background=self.co1)
        self.master.resizable(width=TRUE, height=TRUE)
        
        # Capturar evento de fechamento da janela
        self.master.protocol("WM_DELETE_WINDOW", self.fechar_janela)

        # Configurar a janela para expandir
        self.master.grid_rowconfigure(0, weight=0)  # Logo
        self.master.grid_rowconfigure(1, weight=0)  # Separador
        self.master.grid_rowconfigure(2, weight=0)  # Botões
        self.master.grid_rowconfigure(3, weight=0)  # Separador
        self.master.grid_rowconfigure(4, weight=1)  # Canvas com conteúdo (modificado)
        self.master.grid_columnconfigure(0, weight=1)

        # Não manter conexão persistente na instância; usar context managers quando necessário
        self.conn = None
        self.cursor = None

        # Criar frames e componentes da interface
        self.criar_frames()
        self.criar_header()
        self.criar_botoes()
        self.criar_conteudo_principal()  # Novo método para todo o conteúdo

    def fechar_janela(self):
        # Confirmar com o usuário se deseja realmente fechar (apenas se nenhum aluno foi cadastrado)
        if not self.aluno_cadastrado and messagebox.askyesno("Confirmar", "Deseja realmente sair? Os dados não salvos serão perdidos.") is False:
            return
            
        # Não há conexão persistente para fechar aqui (usamos context managers)
        
        # Salvar o estado antes de destruir a janela
        aluno_foi_cadastrado = self.aluno_cadastrado
        janela_principal = self.janela_principal
        
        # Destruir a janela atual
        self.master.destroy()
        
        # Se a janela principal existir, mostrá-la novamente
        if janela_principal:
            janela_principal.deiconify()
            
            # Nota: A atualização automática da tabela foi removida para evitar conflitos
            # A tabela será atualizada quando o usuário interagir com ela novamente

    def atualizar_janela_principal(self):
        """Método auxiliar para atualizar a tabela principal de forma segura"""
        try:
            # Usar importação local para evitar problemas de importação circular
            import main
            
            # Atualizar a tabela principal de forma simples
            main.atualizar_tabela_principal()
            logger.info("Tabela principal atualizada com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar tabela principal: {str(e)}")
            # Não tentar recriar a interface, apenas registrar o erro

    def criar_frames(self):
        # Frame Logo
        self.frame_logo = Frame(self.master, height=52, bg=self.co7)
        self.frame_logo.grid(row=0, column=0, sticky='nsew')

        # Separador
        ttk.Separator(self.master, orient=HORIZONTAL).grid(row=1, column=0, sticky='ew')

        # Frame Botões
        self.frame_botoes = Frame(self.master, height=65, bg=self.co1)
        self.frame_botoes.grid(row=2, column=0, sticky='nsew')

        # Separador
        ttk.Separator(self.master, orient=HORIZONTAL).grid(row=3, column=0, sticky='ew')

        # Frame para o canvas principal com scrollbar
        self.frame_principal = Frame(self.master, bg=self.co1)
        self.frame_principal.grid(row=4, column=0, sticky='nsew', padx=10, pady=5)

    def criar_header(self):
        # Título no frame_logo
        try:
            app_img = Image.open(get_icon_path('learning.png'))
            app_img = app_img.resize((45, 45))
            self.app_logo = ImageTk.PhotoImage(app_img)
            app_logo_label = Label(
                self.frame_logo, 
                image=self.app_logo,
                text=" Cadastro de Aluno",
                compound=LEFT,
                relief=RAISED,
                anchor=NW,
                font=('Ivy 15 bold'),
                bg=self.co7,
                fg=self.co1
            )
            app_logo_label.pack(fill=BOTH, expand=True)
        except:
            app_logo_label = Label(
                self.frame_logo,
                text=" Cadastro de Aluno",
                relief=RAISED,
                anchor=NW,
                font=('Ivy 15 bold'),
                bg=self.co7,
                fg=self.co1
            )
            app_logo_label.pack(fill=BOTH, expand=True)

    def criar_botoes(self):
        # Frame para os botões
        botoes_frame = Frame(self.frame_botoes, bg=self.co1)
        botoes_frame.pack(fill=X, expand=True, padx=10, pady=5)

        # Configurar grid
        for i in range(3):
            botoes_frame.grid_columnconfigure(i, weight=1)

        # Botões
        Button(botoes_frame, text="Salvar Aluno", 
               command=self.salvar_aluno,
               font=('Ivy 9 bold'),
               bg=self.co3,
               fg=self.co1,
               width=15).grid(row=0, column=0, padx=5, pady=5)

        Button(botoes_frame, text="Adicionar Responsável",
               command=self.add_responsavel,
               font=('Ivy 9'),
               bg=self.co1,
               fg=self.co0,
               width=20).grid(row=0, column=1, padx=5, pady=5)

        Button(botoes_frame, text="Voltar",
               command=self.fechar_janela,
               font=('Ivy 9'),
               bg=self.co6,
               fg=self.co1,
               width=15).grid(row=0, column=2, padx=5, pady=5)

    def criar_conteudo_principal(self):
        """Método que cria um único canvas com scrollbar para todo o conteúdo"""
        # Criando um canvas com scrollbar para todo o conteúdo
        self.canvas_frame = Frame(self.frame_principal, bg=self.co1)
        self.canvas_frame.pack(fill=BOTH, expand=True)
        
        # Adicionando scrollbar vertical única
        self.vscrollbar = Scrollbar(self.canvas_frame, orient="vertical")
        self.vscrollbar.pack(side=RIGHT, fill=Y)
        
        # Adicionando canvas principal
        self.canvas = Canvas(self.canvas_frame, bg=self.co1, yscrollcommand=self.vscrollbar.set)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Configurando scrollbar para controlar o canvas
        self.vscrollbar.config(command=self.canvas.yview)
        
        # Criando frame interno para conter todo o conteúdo
        self.content_frame = Frame(self.canvas, bg=self.co1)
        
        # Criando uma janela no canvas para o frame de conteúdo
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor=NW)
        
        # Garantir que o content_frame se expanda para a largura do canvas
        def _configure_canvas(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        
        self.canvas.bind("<Configure>", _configure_canvas)
        self.content_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Adicionar binding da roda do mouse para rolagem
        self.canvas.bind("<MouseWheel>", lambda event: self._on_canvas_mousewheel(event, self.canvas))  # Windows
        self.canvas.bind("<Button-4>", lambda event: self._on_canvas_mousewheel(event, self.canvas))    # Linux
        self.canvas.bind("<Button-5>", lambda event: self._on_canvas_mousewheel(event, self.canvas))    # Linux
        
        # Criar o formulário do aluno e a seção de responsáveis
        self.criar_form_aluno()
        self.criar_interface_responsaveis()

    def criar_form_aluno(self):
        # Título do formulário com design moderno
        titulo_frame = Frame(self.content_frame, bg=self.co1, pady=5)
        titulo_frame.pack(fill=X, padx=10)
        
        Label(titulo_frame, text="Cadastro de Aluno", 
            font=('Arial 14 bold'), bg=self.co1, fg=self.co5).pack(anchor=W)
        Label(titulo_frame, text="Preencha os dados do aluno nos campos abaixo", 
            font=('Arial 10'), bg=self.co1, fg=self.co4).pack(anchor=W)
        
        # Criando o frame do formulário diretamente no content_frame
        form_frame = Frame(self.content_frame, bg=self.co1)
        form_frame.pack(fill=X, expand=True, padx=10, pady=5)
        
        # Configuração do grid para o formulário
        for i in range(3):  # 3 colunas
            form_frame.grid_columnconfigure(i, weight=1)
        
        # Estilo para os rótulos e campos
        label_style = {'bg': self.co1, 'fg': self.co4, 'font': ('Arial', 10)}
        entry_style = {'width': 30, 'justify': 'left', 'relief': 'solid', 'font': ('Arial', 10)}
        combo_style = {'width': 28, 'font': ('Arial', 10)}
        
        # COLUNA 1 - Informações Básicas
        col1_frame = Frame(form_frame, bg=self.co1, padx=10, pady=5, relief="flat")
        col1_frame.grid(row=0, column=0, sticky=NSEW)
        
        # Título da seção
        Label(col1_frame, text="Informações Básicas", font=('Arial 11 bold'), bg=self.co1, fg=self.co5).pack(anchor=W, pady=(0, 10))
        
        # Nome (Obrigatório)
        Label(col1_frame, text="Nome Completo *", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_nome = Entry(col1_frame, **entry_style)
        self.e_nome.pack(fill=X, pady=(0, 10))
        
        # Data de Nascimento
        Label(col1_frame, text="Data de Nascimento (DD/MM/AAAA)", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_data_nascimento = Entry(col1_frame, **entry_style)
        self.e_data_nascimento.pack(fill=X, pady=(0, 10))
        
        # Local de Nascimento
        Label(col1_frame, text="Local de Nascimento", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_local_nascimento = Entry(col1_frame, **entry_style)
        self.e_local_nascimento.pack(fill=X, pady=(0, 10))
        self.e_local_nascimento.insert(0, "Paço do Lumiar")  # Valor padrão
        
        # UF de Nascimento
        Label(col1_frame, text="UF de Nascimento", **label_style).pack(anchor=W, pady=(5, 0))
        self.c_uf_nascimento = ttk.Combobox(col1_frame, values=self.obter_estados_brasileiros(), **combo_style)
        self.c_uf_nascimento.pack(anchor=W, pady=(0, 10))
        self.c_uf_nascimento.set("MA")  # Valor padrão
        
        # COLUNA 2 - Informações Adicionais
        col2_frame = Frame(form_frame, bg=self.co1, padx=10, pady=5, relief="flat")
        col2_frame.grid(row=0, column=1, sticky=NSEW)
        
        # Título da seção
        Label(col2_frame, text="Informações Adicionais", font=('Arial 11 bold'), bg=self.co1, fg=self.co5).pack(anchor=W, pady=(0, 10))
        
        # CPF
        Label(col2_frame, text="CPF", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_cpf = Entry(col2_frame, **entry_style)
        self.e_cpf.pack(fill=X, pady=(0, 10))
        
        # NIS
        Label(col2_frame, text="NIS", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_nis = Entry(col2_frame, **entry_style)
        self.e_nis.pack(fill=X, pady=(0, 10))
        
        # Cartão SUS
        Label(col2_frame, text="Cartão SUS", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_sus = Entry(col2_frame, **entry_style)
        self.e_sus.pack(fill=X, pady=(0, 10))
        
        # Endereço
        Label(col2_frame, text="Endereço", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_endereco = Entry(col2_frame, **entry_style)
        self.e_endereco.pack(fill=X, pady=(0, 10))
        
        # Sexo
        Label(col2_frame, text="Sexo", **label_style).pack(anchor=W, pady=(5, 0))
        self.c_sexo = ttk.Combobox(col2_frame, values=('M', 'F'), **combo_style)
        self.c_sexo.pack(anchor=W, pady=(0, 10))
        
        # COLUNA 3 - Informações Escolares e Específicas
        col3_frame = Frame(form_frame, bg=self.co1, padx=10, pady=5, relief="flat")
        col3_frame.grid(row=0, column=2, sticky=NSEW)
        
        # Título da seção
        Label(col3_frame, text="Informações Escolares", font=('Arial 11 bold'), bg=self.co1, fg=self.co5).pack(anchor=W, pady=(0, 10))
        
        # Escola
        Label(col3_frame, text="Escola *", **label_style).pack(anchor=W, pady=(5, 0))
        self.c_escola = ttk.Combobox(col3_frame, **combo_style)
        self.c_escola.pack(fill=X, pady=(0, 10))
        self.obter_escolas()
        
        # Raça
        Label(col3_frame, text="Raça *", **label_style).pack(anchor=W, pady=(5, 0))
        self.c_raca = ttk.Combobox(col3_frame, values=('preto', 'pardo', 'branco', 'indígena', 'amarelo'), **combo_style)
        self.c_raca.pack(anchor=W, pady=(0, 10))
        self.c_raca.set("pardo")  # Valor padrão
        
        # Descrição do Transtorno
        Label(col3_frame, text="Descrição do Transtorno", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_descricao_transtorno = Entry(col3_frame, **entry_style)
        self.e_descricao_transtorno.pack(fill=X, pady=(0, 10))
        self.e_descricao_transtorno.insert(0, "Nenhum")  # Valor padrão

    def criar_interface_responsaveis(self):
        # Título do frame de responsáveis
        titulo_resp_frame = Frame(self.content_frame, bg=self.co1, pady=5)
        titulo_resp_frame.pack(fill=X, padx=10, pady=(20, 5))
        
        Label(titulo_resp_frame, text="Responsáveis", 
              font=('Ivy 12 bold'), bg=self.co1, fg=self.co4).pack(anchor=W)
        
        # Frame para responsáveis direto no content_frame
        self.frame_responsaveis = Frame(self.content_frame, bg=self.co1)
        self.frame_responsaveis.pack(fill=X, expand=True, padx=10, pady=5)

    def _on_canvas_mousewheel(self, event, canvas):
        # Função genérica para rolar qualquer canvas com mousewheel
        if event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")
        else:  # Windows
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def add_responsavel(self):
        self.contador_responsaveis += 1
        
        # Criando um frame para cada responsável
        frame_resp = Frame(self.frame_responsaveis, bg=self.co2, bd=1, relief="solid")
        frame_resp.pack(fill=X, expand=True, padx=5, pady=5)
        
        # Configurar o layout do frame responsável para ser responsivo
        for i in range(4):  # 4 colunas
            frame_resp.grid_columnconfigure(i, weight=1)
        
        # Adicionando o frame à lista para controle
        self.lista_frames_responsaveis.append(frame_resp)
        
        # Título do responsável
        l_titulo = Label(frame_resp, text=f"Responsável {self.contador_responsaveis}", height=1, 
                        anchor=NW, font=('Ivy 12 bold'), bg=self.co2, fg=self.co4)
        l_titulo.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        # Botão para remover o responsável
        b_remover = Button(frame_resp, text="Remover", bg=self.co6, fg=self.co1, 
                           font=('Ivy 8'), relief=RAISED, overrelief=RIDGE, 
                           command=lambda f=frame_resp: self.remover_responsavel(f))
        b_remover.grid(row=0, column=3, padx=5, pady=5, sticky="e")
        
        # Campos do responsável
        # Nome
        l_nome_resp = Label(frame_resp, text="Nome do Responsável *", height=1, anchor=NW, 
                          font=('Ivy 10'), bg=self.co2, fg=self.co4)
        l_nome_resp.grid(row=1, column=0, sticky="w", padx=10, pady=2)
        e_nome_resp = Entry(frame_resp, justify='left', relief='solid')
        e_nome_resp.grid(row=2, column=0, sticky="ew", padx=10, pady=2)
        
        # Telefone
        l_telefone = Label(frame_resp, text="Telefone", height=1, anchor=NW, 
                          font=('Ivy 10'), bg=self.co2, fg=self.co4)
        l_telefone.grid(row=1, column=1, sticky="w", padx=10, pady=2)
        e_telefone = Entry(frame_resp, justify='left', relief='solid')
        e_telefone.grid(row=2, column=1, sticky="ew", padx=10, pady=2)
        
        # RG
        l_rg = Label(frame_resp, text="RG", height=1, anchor=NW, 
                    font=('Ivy 10'), bg=self.co2, fg=self.co4)
        l_rg.grid(row=1, column=2, sticky="w", padx=10, pady=2)
        e_rg = Entry(frame_resp, justify='left', relief='solid')
        e_rg.grid(row=2, column=2, sticky="ew", padx=10, pady=2)
        
        # CPF
        l_cpf = Label(frame_resp, text="CPF *", height=1, anchor=NW, 
                     font=('Ivy 10'), bg=self.co2, fg=self.co4)
        l_cpf.grid(row=1, column=3, sticky="w", padx=10, pady=2)
        e_cpf = Entry(frame_resp, justify='left', relief='solid')
        e_cpf.grid(row=2, column=3, sticky="ew", padx=10, pady=2)
        
        # Parentesco
        l_parentesco = Label(frame_resp, text="Parentesco", height=1, anchor=NW, 
                            font=('Ivy 10'), bg=self.co2, fg=self.co4)
        l_parentesco.grid(row=3, column=0, sticky="w", padx=10, pady=2)
        c_parentesco = ttk.Combobox(frame_resp, values=self.opcoes_parentesco)
        c_parentesco.grid(row=4, column=0, sticky="ew", padx=10, pady=2)
        
        # Armazenando as entradas no frame para recuperação posterior
        cast(Any, frame_resp).campos = {
            'nome': e_nome_resp,
            'telefone': e_telefone,
            'rg': e_rg,
            'cpf': e_cpf,
            'parentesco': c_parentesco
        }
        
        # Inicializando o ID do responsável (se é um novo responsável)
        cast(Any, frame_resp).responsavel_id = None
        
        # Atualiza a região de rolagem do canvas
        self.frame_responsaveis.update_idletasks()
        
        return frame_resp

    def remover_responsavel(self, frame):
        if len(self.lista_frames_responsaveis) > 1:  # Garantir que haja pelo menos um responsável
            self.lista_frames_responsaveis.remove(frame)
            frame.destroy()
            self.reordenar_responsaveis()
        else:
            messagebox.showwarning("Aviso", "É necessário manter pelo menos um responsável!")

    def reordenar_responsaveis(self):
        for i, frame in enumerate(self.lista_frames_responsaveis, 1):
            for widget in frame.winfo_children():
                if isinstance(widget, Label) and "Responsável" in widget.cget("text"):
                    widget.config(text=f"Responsável {i}")
                    break

    def salvar_aluno(self):
        try:
            # Coletar os dados do formulário do aluno
            nome = self.e_nome.get()
            data_nascimento_str = self.e_data_nascimento.get().strip()
            # Validação e conversão da data
            try:
                data_nascimento = datetime.strptime(data_nascimento_str, "%d/%m/%Y").strftime("%Y-%m-%d") if data_nascimento_str else None
            except ValueError:
                messagebox.showerror("Erro", "Data de nascimento inválida! Use o formato DD/MM/AAAA.")
                return
            local_nascimento = self.e_local_nascimento.get()
            uf_nascimento = self.c_uf_nascimento.get()
            endereco = self.e_endereco.get()
            sus = self.e_sus.get()
            sexo = self.c_sexo.get()
            cpf = self.e_cpf.get()
            nis = self.e_nis.get()
            raca = self.c_raca.get()
            escola_nome = self.c_escola.get()
            descricao_transtorno = self.e_descricao_transtorno.get()
            
            # Validar campos obrigatórios
            campos_obrigatorios = {
                'Nome': nome,
                'Escola': escola_nome,
                'Raça': raca
            }
            
            campos_vazios = [campo for campo, valor in campos_obrigatorios.items() if not valor]
            if campos_vazios:
                messagebox.showerror("Erro", f"Os seguintes campos obrigatórios não foram preenchidos: {', '.join(campos_vazios)}")
                return

            # Obter o ID da escola selecionada
            escola_id = None
            if escola_nome in self.escolas_map:
                escola_id = self.escolas_map[escola_nome]
            else:
                messagebox.showerror("Erro", "Escola inválida. Por favor, selecione uma escola da lista.")
                return

            # Inserir o aluno no banco de dados dentro de uma transação
            with get_connection() as conn:
                cur = cast(Any, conn).cursor()
                cur.execute(
                    """
                    INSERT INTO alunos (
                        nome, data_nascimento, local_nascimento, UF_nascimento,
                        endereco, sus, sexo, cpf, nis, raca, escola_id, 
                        descricao_transtorno
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        nome, data_nascimento, local_nascimento, uf_nascimento,
                        endereco, sus, sexo, cpf, nis, raca, escola_id, 
                        descricao_transtorno
                    )
                )

                # Obter o ID do aluno inserido
                aluno_id = cast(Any, cur).lastrowid

                # Salvar os responsáveis usando o mesmo cursor/transação
                self.salvar_responsaveis(aluno_id, cur)

                try:
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise

                try:
                    cur.close()
                except Exception:
                    pass

            messagebox.showinfo("Sucesso", "Aluno cadastrado com sucesso!")

            # Marcar que um aluno foi cadastrado com sucesso
            self.aluno_cadastrado = True

            # Fechar a janela após salvar com sucesso
            self.fechar_janela()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Não foi possível salvar os dados: {str(err)}")
            if hasattr(self, 'conn') and self.conn:
                cast(Any, self.conn).rollback()
        except Exception as err:
            messagebox.showerror("Erro", f"Erro inesperado: {str(err)}")
            if hasattr(self, 'conn') and self.conn:
                cast(Any, self.conn).rollback()

    def salvar_responsaveis(self, aluno_id, cur):
        # Verificar se há pelo menos um responsável
        responsaveis_validos = [frame for frame in self.lista_frames_responsaveis if frame.winfo_exists() and frame.campos['nome'].get()]
        
        if not responsaveis_validos:
            messagebox.showerror("Erro", "É necessário ter pelo menos um responsável para o aluno.")
            raise Exception("Nenhum responsável válido encontrado")
            
        # Validar responsáveis
        for frame in responsaveis_validos:
            campos = frame.campos
            campos_resp_obrigatorios = {
                f"Nome do Responsável": campos['nome'].get(),
                f"Parentesco": campos['parentesco'].get(),
                f"Telefone": campos['telefone'].get()
            }
            
            campos_resp_vazios = [campo for campo, valor in campos_resp_obrigatorios.items() if not valor]
            if campos_resp_vazios:
                messagebox.showerror("Erro", f"Os seguintes campos obrigatórios não foram preenchidos: {', '.join(campos_resp_vazios)}")
                raise Exception("Campos obrigatórios de responsável não preenchidos")
        
        # Processar cada responsável
        for frame in responsaveis_validos:
            self.salvar_ou_atualizar_responsavel(frame, aluno_id, cur)
    
    def salvar_ou_atualizar_responsavel(self, frame, aluno_id, cur):
        campos = frame.campos
        nome = campos['nome'].get()
        telefone = campos['telefone'].get()
        rg = campos['rg'].get()
        cpf = campos['cpf'].get()
        parentesco = campos['parentesco'].get()
        responsavel_id = getattr(frame, 'responsavel_id', None)
        
        if not nome:  # Se o nome estiver vazio, não processa
            return None

        # Verificar se já existe um responsável com esse CPF (somente se for um novo responsável)
        if not responsavel_id and cpf:
            cur.execute("SELECT id FROM responsaveis WHERE cpf = %s", (cpf,))
            resp_existente = cur.fetchone()
            if resp_existente:
                responsavel_id = resp_existente[0]
                # Atualizar os dados do responsável existente
                cur.execute(
                    """
                    UPDATE responsaveis 
                    SET nome = %s, grau_parentesco = %s, telefone = %s, rg = %s
                    WHERE id = %s
                    """,
                    (nome, parentesco, telefone, rg, responsavel_id)
                )
                
                # Associar o responsável ao aluno
                cur.execute(
                    "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s, %s)",
                    (responsavel_id, aluno_id)
                )
                
                return responsavel_id

        if responsavel_id:  # Responsável existente, atualizar
            cur.execute(
                """
                UPDATE responsaveis 
                SET nome = %s, grau_parentesco = %s, telefone = %s, rg = %s, cpf = %s
                WHERE id = %s
                """,
                (nome, parentesco, telefone, rg, cpf, responsavel_id)
            )
            
            # Associar o responsável ao aluno
            cur.execute(
                "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s, %s)",
                (responsavel_id, aluno_id)
            )
                
            return responsavel_id
        else:  # Novo responsável, inserir
            # Inserir novo responsável
            cur.execute(
                """
                INSERT INTO responsaveis (nome, grau_parentesco, telefone, rg, cpf)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nome, parentesco, telefone, rg, cpf)
            )
            novo_responsavel_id = cast(Any, cur).lastrowid
            
            # Associar o novo responsável ao aluno
            cur.execute(
                "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s, %s)",
                (novo_responsavel_id, aluno_id)
            )
            
            return novo_responsavel_id

    def obter_escolas(self):
        """Obtém a lista de escolas do banco de dados"""
        try:
            with get_cursor() as cur:
                cur.execute("SELECT id, nome FROM escolas ORDER BY nome, id")
                escolas = cur.fetchall()
            
            # Criar mapeamento e valores para combobox
            self.escolas_map = {}
            escolas_valores = []
            
            for escola in escolas:
                # Compatível com cursor dictionary=True ou tupla
                escola_id = escola['id'] if isinstance(escola, dict) else escola[0]
                nome = escola['nome'] if isinstance(escola, dict) else escola[1]

                # Se já existe uma escola com este nome, adicionar o ID ao nome para diferenciar
                if nome in self.escolas_map:
                    nome_com_id = f"{nome} (ID: {escola_id})"
                    escolas_valores.append(nome_com_id)
                    self.escolas_map[nome_com_id] = escola_id
                else:
                    escolas_valores.append(nome)
                    self.escolas_map[nome] = escola_id
            
            self.c_escola['values'] = escolas_valores
            
            # Define escola padrão se disponível
            if len(escolas) > 0:
                for nome, escola_id in self.escolas_map.items():
                    if escola_id == 3:  # Escola padrão com ID 3
                        self.c_escola.set(nome)
                        break
                if not self.c_escola.get():  # Se não encontrou escola ID 3
                    self.c_escola.set(escolas_valores[0])  # Primeira escola
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter escolas: {str(e)}")

    def obter_estados_brasileiros(self):
        """Retorna a lista de UFs brasileiras"""
        return [
            "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", 
            "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", 
            "SP", "SE", "TO"
        ]