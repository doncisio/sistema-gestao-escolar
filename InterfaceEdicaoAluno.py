from datetime import datetime
from tkinter import *
from tkinter import messagebox, ttk
from PIL import ImageTk, Image
import mysql.connector
from mysql.connector import Error
from conexao import conectar_bd
from tkcalendar import DateEntry
from typing import Any, cast

class InterfaceEdicaoAluno:
    def __init__(self, master, aluno_id, janela_principal=None):
        # Armazenar a referência da janela principal e o ID do aluno
        self.janela_principal = janela_principal
        self.aluno_id = aluno_id
        
        # Variáveis globais
        self.lista_frames_responsaveis = []
        self.contador_responsaveis = 0
        self.opcoes_parentesco = ["Mãe", "Pai", "Tio", "Tia", "Avô", "Avó", "Outro"]
        
        # Cores
        self.co0 = "#f0f0f0"  # Branco
        self.co1 = "#ffffff"  # Branco
        self.co2 = "#f5f5f5"  # Cinza claro
        self.co3 = "#4CAF50"  # Verde
        self.co4 = "#333333"  # Cinza escuro
        self.co5 = "#2196F3"  # Azul
        self.co6 = "#f44336"  # Vermelho
        self.co7 = "#1976D2"  # Azul escuro
        self.co8 = "#00a095"  # Verde 
        self.co9 = "#e9edf5"  # +verde

        self.master = master
        self.master.title("Edição de Aluno")
        self.master.geometry("1000x700")
        self.master.configure(background=self.co1)
        self.master.resizable(True, True)
        
        # Capturar evento de fechamento da janela
        self.master.protocol("WM_DELETE_WINDOW", self.fechar_janela)

        # Configurar o grid da janela principal
        self.master.grid_rowconfigure(4, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        # Conectar ao banco de dados
        try:
            self.conn = conectar_bd()
            self.cursor = self.conn.cursor(buffered=True)
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao banco de dados: {str(e)}")
            self.fechar_janela()
            return

        # Criar frames e componentes da interface
        self.criar_frames()
        self.criar_header()
        self.criar_botoes()
        self.criar_conteudo_principal()
        
        # Carregar dados do aluno
        self.carregar_dados_aluno()
        self.carregar_responsaveis()

    def fechar_janela(self):
        # Confirmar com o usuário se deseja realmente fechar
        if messagebox.askyesno("Confirmar", "Deseja realmente fechar a edição? Alterações não salvas serão perdidas."):
            # Fechar conexões com o banco de dados se existirem
            try:
                self.cursor.close()
                self.conn.close()
            except:
                pass
        
            # Destruir a janela atual
            self.master.destroy()
            
            # Restaurar a janela principal se existir
            if self.janela_principal:
                self.janela_principal.deiconify()
                
                # Nota: A atualização automática da tabela foi removida para evitar conflitos
                # A tabela será atualizada quando o usuário interagir com ela novamente
        else:
            # Se o usuário optar por não fechar, apenas retornamos
            return

    def criar_frames(self):
        # Frame Logo
        self.frame_logo = Frame(self.master, height=65, bg=self.co7)
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
        
        # Configurar o grid do frame principal
        self.frame_principal.grid_rowconfigure(0, weight=1)
        self.frame_principal.grid_columnconfigure(0, weight=1)

    def criar_header(self):
        # Título no frame_logo
        try:
            app_img = Image.open('icon/learning.png')
            app_img = app_img.resize((45, 45))
            self.app_logo = ImageTk.PhotoImage(app_img)
            app_logo_label = Label(
                self.frame_logo, 
                image=self.app_logo,
                text=" Edição de Aluno",
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
                text=" Edição de Aluno",
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
        Button(botoes_frame, text="Salvar Alterações", 
               command=self.salvar_alteracoes,
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
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor=NW, width=self.canvas.winfo_width())
        
        # Garantir que o content_frame se expanda para a largura do canvas
        def _configure_canvas(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            # Atualizar a largura da janela do canvas para corresponder à largura do canvas
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        
        self.canvas.bind("<Configure>", _configure_canvas)
        self.content_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Adicionar binding da roda do mouse para rolagem
        self.canvas.bind("<MouseWheel>", lambda event: self._on_canvas_mousewheel(event, self.canvas))  # Windows
        self.canvas.bind("<Button-4>", lambda event: self._on_canvas_mousewheel(event, self.canvas))    # Linux
        self.canvas.bind("<Button-5>", lambda event: self._on_canvas_mousewheel(event, self.canvas))    # Linux
        
        # Criar os componentes da interface
        self.criar_form_aluno()
        self.criar_secao_matricula()
        self.criar_interface_responsaveis()
        
        # Atualizar o scrollregion após criar todos os componentes
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def criar_form_aluno(self):
        # Título do formulário com design moderno
        titulo_frame = Frame(self.content_frame, bg=self.co1, pady=5)
        titulo_frame.pack(fill=X, padx=10)
        
        Label(titulo_frame, text="Dados do Aluno", 
            font=('Arial 14 bold'), bg=self.co1, fg=self.co5).pack(anchor=W)
        Label(titulo_frame, text="Edite os dados do aluno conforme necessário", 
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
        
        # UF de Nascimento
        Label(col1_frame, text="UF de Nascimento", **label_style).pack(anchor=W, pady=(5, 0))
        self.c_uf_nascimento = ttk.Combobox(col1_frame, values=self.obter_estados_brasileiros(), **combo_style)
        self.c_uf_nascimento.pack(anchor=W, pady=(0, 10))
        
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
        
        # Descrição do Transtorno
        Label(col3_frame, text="Descrição do Transtorno", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_descricao_transtorno = Entry(col3_frame, **entry_style)
        self.e_descricao_transtorno.pack(fill=X, pady=(0, 10))

    def criar_secao_matricula(self):
        # Título da seção
        titulo_frame = Frame(self.content_frame, bg=self.co1, pady=5)
        titulo_frame.pack(fill=X, padx=10, pady=(20, 5))
        
        Label(titulo_frame, text="Status da Matrícula", 
            font=('Arial 14 bold'), bg=self.co1, fg=self.co5).pack(anchor=W)
        
        # Frame para exibir dados da matrícula
        self.matricula_status_frame = Frame(self.content_frame, bg=self.co1, bd=1, relief="solid")
        self.matricula_status_frame.pack(fill=X, expand=True, padx=10, pady=5)

    def criar_interface_responsaveis(self):
        # Título do frame de responsáveis e legenda de campos obrigatórios
        titulo_container = Frame(self.content_frame, bg=self.co1)
        titulo_container.pack(fill=X, anchor=W, padx=10, pady=(20, 5))
        
        Label(titulo_container, text="Responsáveis", 
              font=('Arial 14 bold'), bg=self.co1, fg=self.co5).pack(anchor=W, side=LEFT)
        
        # Legenda para campos obrigatórios
        Label(titulo_container, text="* Campo obrigatório", 
              font=('Arial 8 italic'), bg=self.co1, fg="gray").pack(anchor=E, side=RIGHT, padx=10)
        
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
    
    def _on_mousewheel(self, event):
        # Método mantido para compatibilidade
        self._on_canvas_mousewheel(event, self.canvas)

    def add_responsavel(self, dados_resp=None):
        """
        Adiciona um novo frame de responsável.
        Se dados_resp for fornecido, preenche os campos com os dados existentes.
        """
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
                        anchor=NW, font=('Arial 12 bold'), bg=self.co2, fg=self.co4)
        l_titulo.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        # Botão para remover o responsável
        b_remover = Button(frame_resp, text="Remover", bg=self.co6, fg=self.co1, 
                           font=('Arial 8'), relief=RAISED, overrelief=RIDGE, 
                           command=lambda f=frame_resp: self.remover_responsavel(f))
        b_remover.grid(row=0, column=3, padx=5, pady=5, sticky="e")
        
        # Campos do responsável
        # Nome - único campo obrigatório
        l_nome_resp = Label(frame_resp, text="Nome do Responsável *", height=1, anchor=NW, 
                          font=('Arial 10'), bg=self.co2, fg=self.co4)
        l_nome_resp.grid(row=1, column=0, sticky="w", padx=10, pady=2)
        e_nome_resp = Entry(frame_resp, justify='left', relief='solid', font=('Arial', 10))
        e_nome_resp.grid(row=2, column=0, sticky="ew", padx=10, pady=2)
        
        # Telefone - não é mais obrigatório
        l_telefone = Label(frame_resp, text="Telefone", height=1, anchor=NW, 
                          font=('Arial 10'), bg=self.co2, fg=self.co4)
        l_telefone.grid(row=1, column=1, sticky="w", padx=10, pady=2)
        e_telefone = Entry(frame_resp, justify='left', relief='solid', font=('Arial', 10))
        e_telefone.grid(row=2, column=1, sticky="ew", padx=10, pady=2)
        
        # RG
        l_rg = Label(frame_resp, text="RG", height=1, anchor=NW, 
                    font=('Arial 10'), bg=self.co2, fg=self.co4)
        l_rg.grid(row=1, column=2, sticky="w", padx=10, pady=2)
        e_rg = Entry(frame_resp, justify='left', relief='solid', font=('Arial', 10))
        e_rg.grid(row=2, column=2, sticky="ew", padx=10, pady=2)
        
        # CPF - remover o asterisco pois não é obrigatório
        l_cpf = Label(frame_resp, text="CPF", height=1, anchor=NW, 
                     font=('Arial 10'), bg=self.co2, fg=self.co4)
        l_cpf.grid(row=1, column=3, sticky="w", padx=10, pady=2)
        e_cpf = Entry(frame_resp, justify='left', relief='solid', font=('Arial', 10))
        e_cpf.grid(row=2, column=3, sticky="ew", padx=10, pady=2)
        
        # Parentesco
        l_parentesco = Label(frame_resp, text="Parentesco", height=1, anchor=NW, 
                            font=('Arial 10'), bg=self.co2, fg=self.co4)
        l_parentesco.grid(row=3, column=0, sticky="w", padx=10, pady=2)
        c_parentesco = ttk.Combobox(frame_resp, values=self.opcoes_parentesco, font=('Arial', 10))
        c_parentesco.grid(row=4, column=0, sticky="ew", padx=10, pady=2)
        
        # Armazenando as entradas no frame para recuperação posterior
        frame_resp.campos = {
            'nome': e_nome_resp,
            'telefone': e_telefone,
            'rg': e_rg,
            'cpf': e_cpf,
            'parentesco': c_parentesco
        }
        
        # Inicializando o ID do responsável (usado para edição)
        frame_resp.responsavel_id = None
        
        # Se foram fornecidos dados, preencher os campos
        if dados_resp:
            e_nome_resp.insert(0, dados_resp['nome'] or "")
            e_telefone.insert(0, dados_resp['telefone'] or "")
            e_rg.insert(0, dados_resp['rg'] or "")
            e_cpf.insert(0, dados_resp['cpf'] or "")
            c_parentesco.set(dados_resp['grau_parentesco'] or "")
            
            # Salvar o ID do responsável no frame para uso posterior
            frame_resp.responsavel_id = dados_resp['id']
        
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

    def carregar_dados_aluno(self):
        try:
            # Buscar dados do aluno
            cast(Any, self.cursor).execute("""
                SELECT nome, data_nascimento, local_nascimento, UF_nascimento,
                       endereco, sus, sexo, cpf, nis, raca, escola_id,
                       descricao_transtorno
                FROM alunos
                WHERE id = %s
            """, (self.aluno_id,))
            aluno = cast(Any, self.cursor).fetchone()
            
            if aluno:
                nome, data_nascimento, local_nascimento, uf_nascimento, endereco, sus, sexo, cpf, nis, raca, escola_id, descricao_transtorno = aluno
                self.e_nome.delete(0, END)
                self.e_nome.insert(0, nome if nome else "")
                # Exibir data no formato DD/MM/YYYY
                if data_nascimento:
                    try:
                        data_nasc_br = datetime.strptime(str(data_nascimento), "%Y-%m-%d").strftime("%d/%m/%Y")
                    except Exception:
                        data_nasc_br = str(data_nascimento)
                    self.e_data_nascimento.delete(0, END)
                    self.e_data_nascimento.insert(0, data_nasc_br)
                
                self.e_local_nascimento.delete(0, END)
                self.e_local_nascimento.insert(0, local_nascimento if local_nascimento else "")
                
                self.c_uf_nascimento.set(uf_nascimento if uf_nascimento else "")
                
                self.e_endereco.delete(0, END)
                self.e_endereco.insert(0, endereco if endereco else "")
                
                self.e_sus.delete(0, END)
                self.e_sus.insert(0, sus if sus else "")
                
                self.c_sexo.set(sexo if sexo else "")
                
                self.e_cpf.delete(0, END)
                self.e_cpf.insert(0, cpf if cpf else "")
                
                self.e_nis.delete(0, END)
                self.e_nis.insert(0, nis if nis else "")
                
                self.c_raca.set(raca if raca else "")
                
                self.e_descricao_transtorno.delete(0, END)
                self.e_descricao_transtorno.insert(0, descricao_transtorno if descricao_transtorno else "")
                
                # Carregar dados de matrícula
                self.carregar_dados_matricula()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados do aluno: {str(e)}")

    def carregar_responsaveis(self):
        try:
            # Consultar responsáveis associados ao aluno
            cast(Any, self.cursor).execute("""
                SELECT r.id, r.nome, r.grau_parentesco, r.telefone, r.rg, r.cpf
                FROM responsaveis r
                JOIN responsaveisalunos ra ON r.id = ra.responsavel_id
                WHERE ra.aluno_id = %s
            """, (self.aluno_id,))
            
            responsaveis = cast(Any, self.cursor).fetchall()
            
            # Se não há responsáveis, adicionar um frame vazio
            if not responsaveis:
                self.add_responsavel()
                return
            
            # Adicionar um frame para cada responsável
            for resp in responsaveis:
                resp_id, nome, grau_parentesco, telefone, rg, cpf = resp
                dados_resp = {
                    'id': resp_id,
                    'nome': nome,
                    'grau_parentesco': grau_parentesco,
                    'telefone': telefone,
                    'rg': rg,
                    'cpf': cpf
                }
                self.add_responsavel(dados_resp)
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar responsáveis: {str(e)}")
            # Garantir que haja pelo menos um frame de responsável
            if not self.lista_frames_responsaveis:
                self.add_responsavel()

    def salvar_alteracoes(self):
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

            # Atualizar o aluno no banco de dados
            cast(Any, self.cursor).execute(
                """
                UPDATE alunos SET
                    nome = %s,
                    data_nascimento = %s,
                    local_nascimento = %s,
                    UF_nascimento = %s,
                    endereco = %s,
                    sus = %s,
                    sexo = %s,
                    cpf = %s,
                    nis = %s,
                    raca = %s,
                    escola_id = %s,
                    descricao_transtorno = %s
                WHERE id = %s
                """,
                (
                    nome, data_nascimento, local_nascimento, uf_nascimento,
                    endereco, sus, sexo, cpf, nis, raca, escola_id,
                    descricao_transtorno, self.aluno_id
                )
            )
            
            # Salvar os responsáveis
            self.salvar_responsaveis()
            
            # Confirmar a operação
            if hasattr(self, 'conn') and self.conn:
                cast(Any, self.conn).commit()
            
            messagebox.showinfo("Sucesso", "Dados do aluno atualizados com sucesso!")
            
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

    def salvar_responsaveis(self):
        # Verificar se há pelo menos um responsável
        responsaveis_validos = [frame for frame in self.lista_frames_responsaveis if frame.winfo_exists() and frame.campos['nome'].get()]
        
        if not responsaveis_validos:
            messagebox.showerror("Erro", "É necessário ter pelo menos um responsável para o aluno.")
            raise Exception("Nenhum responsável válido encontrado")
            
        # Validar responsáveis
        for frame in responsaveis_validos:
            campos = frame.campos
            # Apenas o nome do responsável é obrigatório
            if not campos['nome'].get():
                messagebox.showerror("Erro", "O Nome do Responsável é obrigatório.")
                raise Exception("Campo obrigatório de responsável não preenchido")
        
        # Primeiro, remover todas as associações existentes entre aluno e responsáveis
        # (preservando os registros de responsáveis para possível reutilização)
        cast(Any, self.cursor).execute(
            "DELETE FROM responsaveisalunos WHERE aluno_id = %s",
            (self.aluno_id,)
        )
        
        # Processar cada responsável
        for frame in responsaveis_validos:
            self.salvar_ou_atualizar_responsavel(frame)
    
    def salvar_ou_atualizar_responsavel(self, frame):
        campos = frame.campos
        nome = campos['nome'].get()
        telefone = campos['telefone'].get()
        rg = campos['rg'].get()
        cpf = campos['cpf'].get()
        parentesco = campos['parentesco'].get()
        responsavel_id = getattr(frame, 'responsavel_id', None)
        
        if not nome:  # Se o nome estiver vazio, não processa
            return None

        try:
            # Verificar se já existe um responsável com esse CPF (somente se CPF não estiver vazio e for um novo responsável)
            if cpf and not responsavel_id:
                cast(Any, self.cursor).execute("SELECT id FROM responsaveis WHERE cpf = %s", (cpf,))
                resp_existente = cast(Any, self.cursor).fetchone()
                if resp_existente:
                    responsavel_id = resp_existente[0]
                    # Atualizar os dados do responsável existente
                    cast(Any, self.cursor).execute(
                        """
                        UPDATE responsaveis 
                        SET nome = %s, grau_parentesco = %s, telefone = %s, rg = %s
                        WHERE id = %s
                        """,
                        (nome, parentesco, telefone, rg, responsavel_id)
                    )
                    
                    # Associar o responsável ao aluno
                    cast(Any, self.cursor).execute(
                        "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s, %s)",
                        (responsavel_id, self.aluno_id)
                    )
                    
                    return responsavel_id

            if responsavel_id:  # Responsável existente, atualizar
                cast(Any, self.cursor).execute(
                    """
                    UPDATE responsaveis 
                    SET nome = %s, grau_parentesco = %s, telefone = %s, rg = %s, cpf = %s
                    WHERE id = %s
                    """,
                    (nome, parentesco, telefone, rg, cpf, responsavel_id)
                )
                
                # Associar o responsável ao aluno
                cast(Any, self.cursor).execute(
                    "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s, %s)",
                    (responsavel_id, self.aluno_id)
                )
                
                return responsavel_id
            else:  # Novo responsável, inserir
                # Inserir novo responsável
                cast(Any, self.cursor).execute(
                    """
                    INSERT INTO responsaveis (nome, grau_parentesco, telefone, rg, cpf)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (nome, parentesco, telefone, rg, cpf)
                )
                novo_responsavel_id = cast(Any, self.cursor).lastrowid
                
                # Associar o novo responsável ao aluno
                cast(Any, self.cursor).execute(
                    "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s, %s)",
                    (novo_responsavel_id, self.aluno_id)
                )
                
                return novo_responsavel_id
        except mysql.connector.Error as err:
            if err.errno == 1062:  # Erro de duplicidade (código para DUPLICATE ENTRY)
                messagebox.showerror("Erro", f"CPF {cpf} já está associado a outro responsável")
            else:
                messagebox.showerror("Erro de Banco de Dados", f"Erro ao salvar responsável: {str(err)}")
            raise Exception(f"Erro ao salvar responsável: {str(err)}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado ao salvar responsável: {str(e)}")
            raise

    def obter_escolas(self):
        """Obtém a lista de escolas do banco de dados"""
        # Inicializar o mapa de escolas antes de qualquer operação
        self.escolas_map = {}
        
        try:
            # Verificar se existe conexão com o banco
            if not hasattr(self, 'conn') or not self.conn:
                self.conn = conectar_bd()
                self.cursor = self.conn.cursor(buffered=True)
                
            cast(Any, self.cursor).execute("SELECT id, nome FROM escolas ORDER BY nome, id")
            escolas = cast(Any, self.cursor).fetchall()
            
            if not escolas:
                messagebox.showwarning("Aviso", "Não foram encontradas escolas no banco de dados.")
                return
            
            # Criar mapeamento e valores para combobox
            self.escolas_map = {}
            escolas_valores = []
            
            for id, nome in escolas:
                # Se já existe uma escola com este nome, adicionar o ID ao nome para diferenciar
                if nome in self.escolas_map:
                    nome_com_id = f"{nome} (ID: {id})"
                    escolas_valores.append(nome_com_id)
                    self.escolas_map[nome_com_id] = id
                else:
                    escolas_valores.append(nome)
                    self.escolas_map[nome] = id
            
            self.c_escola['values'] = escolas_valores
            
            # Configurar valor padrão para a escola ID 60 (se existir)
            encontrou_escola_padrao = False
            for nome, id_escola in self.escolas_map.items():
                if id_escola == 60:  # Escola padrão com ID 60
                    self.c_escola.set(nome)
                    encontrou_escola_padrao = True
                    break
                    
            # Se não encontrou a escola padrão e há escolas disponíveis, seleciona a primeira
            if not encontrou_escola_padrao and self.escolas_map:
                self.c_escola.set(list(self.escolas_map.keys())[0])
                
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao obter escolas: {str(err)}")
            try:
                # Tenta reconectar
                self.conn = conectar_bd()
                self.cursor = self.conn.cursor(buffered=True)
            except:
                pass
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado ao obter escolas: {str(e)}")
            # Em caso de erro, garante que o combobox tenha valores válidos
            self.c_escola['values'] = ["Escola não disponível"]
            self.c_escola.set("Escola não disponível")
            self.escolas_map = {"Escola não disponível": 60}  # Usa valor padrão

    def obter_estados_brasileiros(self):
        """Retorna a lista de UFs brasileiras"""
        return [
            "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", 
            "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", 
            "SP", "SE", "TO"
        ]

    def carregar_dados_matricula(self):
        try:
            # Limpar frame de status da matrícula
            for widget in self.matricula_status_frame.winfo_children():
                widget.destroy()
            
            # Consultar matrícula do aluno
            cast(Any, self.cursor).execute("""
                SELECT m.id, m.status, t.nome as turma, s.nome as serie, m.ano_letivo_id
                FROM matriculas m
                JOIN turmas t ON m.turma_id = t.id
                JOIN serie s ON t.serie_id = s.id
                WHERE m.aluno_id = %s
                ORDER BY m.id DESC
                LIMIT 1
            """, (self.aluno_id,))
            
            matricula = cast(Any, self.cursor).fetchone()
            
            if matricula:
                matricula_id, status, turma, serie, ano_letivo = matricula
                self.matricula_id = matricula_id
                
                # Criar widget para exibir informações
                info_frame = Frame(self.matricula_status_frame, bg=self.co1, padx=10, pady=10)
                info_frame.pack(fill=X)
                
                # Mostrar informações da matrícula
                status_text = f"Status: {status} | Turma: {turma} | Série: {serie} | Ano Letivo: {ano_letivo}"
                
                # Definir a cor do status conforme a situação
                status_color = "black"
                if status == "Ativo":
                    status_color = "green"
                elif status in ["Evadido", "Cancelado", "Transferido"]:
                    status_color = "red"
                elif status == "Concluído":
                    status_color = "blue"
                
                status_label = Label(info_frame, text=status_text, font=('Arial 11'), bg=self.co1, fg=status_color)
                status_label.pack(anchor=W, pady=5)
                
                # Frame para botões
                botoes_frame = Frame(info_frame, bg=self.co1)
                botoes_frame.pack(fill=X, pady=5)
                
                # Adicionar botão de editar matrícula
                Button(botoes_frame, text="Editar Matrícula", 
                      command=self.editar_matricula,
                      font=('Ivy 9'),
                      bg=self.co5,
                      fg=self.co1,
                      width=15).pack(side=LEFT, padx=5)
                
                # Se matrícula não estiver ativa, adicionar botão para nova matrícula
                if status != "Ativo":
                    Button(botoes_frame, text="Nova Matrícula", 
                          command=self.nova_matricula,
                          font=('Ivy 9'),
                          bg=self.co3,
                          fg=self.co1,
                          width=15).pack(side=LEFT, padx=5)
            else:
                # Sem matrícula
                self.matricula_id = None
                
                info_frame = Frame(self.matricula_status_frame, bg=self.co1, padx=10, pady=10)
                info_frame.pack(fill=X)
                
                Label(info_frame, text="Aluno sem matrícula registrada", 
                     font=('Arial 11'), bg=self.co1, fg="gray").pack(anchor=W, pady=5)
                
                # Frame para botões
                botoes_frame = Frame(info_frame, bg=self.co1)
                botoes_frame.pack(fill=X, pady=5)
                
                # Botão para nova matrícula
                Button(botoes_frame, text="Registrar Matrícula", 
                      command=self.nova_matricula,
                      font=('Ivy 9'),
                      bg=self.co3,
                      fg=self.co1,
                      width=15).pack(side=LEFT, padx=5)
                
        except Exception as e:
            # Exibir erro
            info_frame = Frame(self.matricula_status_frame, bg=self.co1, padx=10, pady=10)
            info_frame.pack(fill=X)
            
            Label(info_frame, text=f"Erro ao carregar matrícula: {str(e)}", 
                 font=('Arial 11'), bg=self.co1, fg="red").pack(anchor=W, pady=5)

    def editar_matricula(self):
        # Implementação da função para editar matrícula
        if not hasattr(self, 'matricula_id') or not self.matricula_id:
            messagebox.showwarning("Aviso", "Não há matrícula ativa para editar")
            return
            
        # Janela para editar matrícula
        janela_edicao = Toplevel(self.master)
        janela_edicao.title("Editar Matrícula")
        janela_edicao.geometry("400x250")
        janela_edicao.configure(background=self.co1)
        janela_edicao.transient(self.master)
        janela_edicao.focus_force()
        janela_edicao.grab_set()
        
        # Frame principal
        frame_principal = Frame(janela_edicao, bg=self.co1, padx=20, pady=20)
        frame_principal.pack(fill=BOTH, expand=True)
        
        # Título
        Label(frame_principal, text="Alterar Status da Matrícula", 
              font=("Arial", 14, "bold"), bg=self.co1, fg=self.co5).pack(pady=(0, 20))
        
        # Obter o status atual
        try:
            cast(Any, self.cursor).execute("SELECT status FROM matriculas WHERE id = %s", (self.matricula_id,))
            status_atual = cast(Any, self.cursor).fetchone()[0]
        except:
            status_atual = "Desconhecido"
        
        # Mostrar status atual
        Label(frame_principal, text=f"Status Atual: {status_atual}", 
              font=("Arial", 12), bg=self.co1, fg=self.co4).pack(anchor=W, pady=10)
        
        # Opções de status
        status_opcoes = ['Ativo', 'Evadido', 'Cancelado', 'Transferido', 'Concluído']
        
        # Variável para o novo status
        novo_status = StringVar(frame_principal)
        novo_status.set(status_atual)
        
        # Combobox para selecionar o novo status
        Label(frame_principal, text="Novo Status:", bg=self.co1, fg=self.co4).pack(anchor=W)
        cb_status = ttk.Combobox(frame_principal, textvariable=novo_status, values=status_opcoes, width=30)
        cb_status.pack(fill=X, pady=5)
        
        # Botões
        frame_botoes = Frame(frame_principal, bg=self.co1)
        frame_botoes.pack(fill=X, pady=20)
        
        # Função para salvar a alteração
        def salvar_alteracao():
            if novo_status.get() == status_atual:
                messagebox.showinfo("Aviso", "Nenhuma alteração foi feita")
                janela_edicao.destroy()
                return
                
            try:
                # Atualizar o status da matrícula
                cast(Any, self.cursor).execute(
                    "UPDATE matriculas SET status = %s WHERE id = %s", 
                    (novo_status.get(), self.matricula_id)
                )
                
                # Registrar histórico da alteração de status
                try:
                    cast(Any, self.cursor).execute(
                        """
                        INSERT INTO historico_matricula (matricula_id, status_anterior, status_novo, data_mudanca)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (self.matricula_id, status_atual, novo_status.get(), datetime.today().date())
                    )
                except Exception as hist_err:
                    # Não interromper o fluxo principal, mas informar o usuário
                    print(f"Falha ao registrar histórico da matrícula: {hist_err}")
                
                # Confirmar a operação
                if hasattr(self, 'conn') and self.conn:
                    cast(Any, self.conn).commit()
                
                messagebox.showinfo("Sucesso", "Status da matrícula alterado com sucesso!")
                
                # Atualizar o status na tela
                self.carregar_dados_matricula()
                
                # Fechar a janela
                janela_edicao.destroy()
                
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível alterar o status: {str(e)}")
                if hasattr(self, 'conn') and self.conn:
                    cast(Any, self.conn).rollback()
        
        # Botão salvar
        Button(frame_botoes, text="Salvar", command=salvar_alteracao,
              font=('Ivy 10 bold'), bg=self.co3, fg=self.co1, width=10).pack(side=LEFT, padx=5)
        
        # Botão cancelar
        Button(frame_botoes, text="Cancelar", command=janela_edicao.destroy,
              font=('Ivy 10'), bg=self.co6, fg=self.co1, width=10).pack(side=RIGHT, padx=5)

    def nova_matricula(self):
        # Esta função seria implementada para criar uma nova matrícula
        try:
            # Importar a função de matrícula do módulo principal
            from main import matricular_aluno
            
            # Fechar temporariamente a janela de edição
            self.master.withdraw()
            
            # Chamar a função de matrícula
            matricular_aluno(self.aluno_id)
            
            # Reexibir a janela após a matrícula
            self.master.deiconify()
            
            # Atualizar o status da matrícula
            self.carregar_dados_matricula()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível realizar a matrícula: {str(e)}")
            self.master.deiconify()