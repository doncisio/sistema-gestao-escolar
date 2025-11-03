from datetime import datetime
from tkinter import *
from tkinter import messagebox, ttk
from PIL import ImageTk, Image
import mysql.connector
from mysql.connector import Error
from conexao import conectar_bd
from tkcalendar import DateEntry
from Seguranca import atualizar_treeview

class InterfaceEditarAluno:
    def __init__(self, master, janela_principal=None, aluno_id=None):
        # Armazenar a referência da janela principal e o ID do aluno
        self.janela_principal = janela_principal
        self.aluno_id = aluno_id
        
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
        self.master.title("Edição de Aluno")
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
        self.master.grid_rowconfigure(4, weight=1)  # Dados do aluno
        self.master.grid_rowconfigure(5, weight=1)  # Responsáveis
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
        self.criar_form_aluno()
        self.criar_interface_responsaveis()
        
        # Carregar dados do aluno se um ID foi fornecido
        if self.aluno_id:
            self.carregar_dados_aluno()

    def fechar_janela(self):
        # Fechar a conexão com o banco de dados
        if hasattr(self, 'conn') and self.conn:
            try:
                self.cursor.close()
                self.conn.close()
            except:
                pass
        
        # Destruir a janela atual
        self.master.destroy()
        
        # Se a janela principal existir, mostrá-la novamente
        if self.janela_principal:
            self.janela_principal.deiconify()
            
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

        # Frame Formulário do Aluno
        self.frame_aluno = Frame(self.master, bg=self.co1)
        self.frame_aluno.grid(row=4, column=0, sticky='nsew', padx=10, pady=5)

        # Frame Responsáveis
        self.frame_responsaveis_container = Frame(self.master, bg=self.co1)
        self.frame_responsaveis_container.grid(row=5, column=0, sticky='nsew', padx=10, pady=5)

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
                width=950,
                compound=LEFT,
                relief=RAISED,
                anchor=NW,
                font=('Ivy 15 bold'),
                bg=self.co7,
                fg=self.co1
            )
            app_logo_label.place(x=0, y=0)
        except:
            app_logo_label = Label(
                self.frame_logo,
                text=" Edição de Aluno",
                width=950,
                relief=RAISED,
                anchor=NW,
                font=('Ivy 15 bold'),
                bg=self.co7,
                fg=self.co1
            )
            app_logo_label.place(x=0, y=0)

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
               width=15).grid(row=0, column=1, padx=5, pady=5)

        Button(botoes_frame, text="Voltar",
               command=self.fechar_janela,
               font=('Ivy 9'),
               bg=self.co6,
               fg=self.co1,
               width=15).grid(row=0, column=2, padx=5, pady=5)

    def criar_form_aluno(self):
        # Título do formulário
        Label(self.frame_aluno, text="Dados do Aluno", 
            font=('Ivy 12 bold'), bg=self.co1, fg=self.co4).pack(anchor=W, padx=10, pady=5)
        
        # Frame para os campos do formulário
        form_frame = Frame(self.frame_aluno, bg=self.co1)
        form_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Configuração do grid para o formulário
        for i in range(4):  # 4 colunas
            form_frame.grid_columnconfigure(i, weight=1)
        
        # Campos do formulário
        # Nome
        Label(form_frame, text="Nome Completo *", bg=self.co1, fg=self.co4).grid(row=0, column=0, sticky=W, padx=10, pady=5)
        self.e_nome = Entry(form_frame, width=35, justify='left', relief='solid')
        self.e_nome.grid(row=1, column=0, sticky=W, padx=10, pady=5)

        # CPF
        Label(form_frame, text="CPF *", bg=self.co1, fg=self.co4).grid(row=0, column=1, sticky=W, padx=10, pady=5)
        self.e_cpf = Entry(form_frame, width=20, justify='left', relief='solid')
        self.e_cpf.grid(row=1, column=1, sticky=W, padx=10, pady=5)

        # Data de Nascimento
        Label(form_frame, text="Data de Nascimento *", bg=self.co1, fg=self.co4).grid(row=0, column=2, sticky=W, padx=10, pady=5)
        self.c_data_nascimento = DateEntry(
            form_frame,
            width=14,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd'
        )
        self.c_data_nascimento.grid(row=1, column=2, sticky=W, padx=10, pady=5)

        # Sexo
        Label(form_frame, text="Sexo *", bg=self.co1, fg=self.co4).grid(row=2, column=0, sticky=W, padx=10, pady=5)
        self.c_sexo = ttk.Combobox(form_frame, width=12, values=('M', 'F'))
        self.c_sexo.grid(row=3, column=0, sticky=W, padx=10, pady=5)

        # Raça
        Label(form_frame, text="Raça *", bg=self.co1, fg=self.co4).grid(row=2, column=1, sticky=W, padx=10, pady=5)
        self.c_raca = ttk.Combobox(form_frame, width=15)
        self.c_raca.grid(row=3, column=1, sticky=W, padx=10, pady=5)
        
        # Carregar opções de raça
        self.obter_racas()
        
        # Descrição do Transtorno
        Label(form_frame, text="Descrição do Transtorno", bg=self.co1, fg=self.co4).grid(row=2, column=2, sticky=W, padx=10, pady=5)
        self.e_descricao_transtorno = Entry(form_frame, width=25, justify='left', relief='solid')
        self.e_descricao_transtorno.grid(row=3, column=2, sticky=W, padx=10, pady=5)
        
        # Endereço
        Label(form_frame, text="Endereço", bg=self.co1, fg=self.co4).grid(row=4, column=0, sticky=W, padx=10, pady=5)
        self.e_endereco = Entry(form_frame, width=35, justify='left', relief='solid')
        self.e_endereco.grid(row=5, column=0, sticky=W, padx=10, pady=5)

        # Cartão SUS
        Label(form_frame, text="Cartão SUS", bg=self.co1, fg=self.co4).grid(row=4, column=1, sticky=W, padx=10, pady=5)
        self.e_sus = Entry(form_frame, width=20, justify='left', relief='solid')
        self.e_sus.grid(row=5, column=1, sticky=W, padx=10, pady=5)

        # Série
        Label(form_frame, text="Série *", bg=self.co1, fg=self.co4).grid(row=6, column=0, sticky=W, padx=10, pady=5)
        self.c_serie = ttk.Combobox(form_frame, width=15)
        self.c_serie.grid(row=7, column=0, sticky=W, padx=10, pady=5)
        self.c_serie.bind("<<ComboboxSelected>>", self.atualizar_turmas)
        
        # Carregar opções de série
        self.obter_series()
        
        # Turma
        Label(form_frame, text="Turma *", bg=self.co1, fg=self.co4).grid(row=6, column=1, sticky=W, padx=10, pady=5)
        self.c_turma = ttk.Combobox(form_frame, width=15)
        self.c_turma.grid(row=7, column=1, sticky=W, padx=10, pady=5)
        self.c_turma.bind("<<ComboboxSelected>>", self.atualizar_turno)
        
        # Turno
        Label(form_frame, text="Turno *", bg=self.co1, fg=self.co4).grid(row=6, column=2, sticky=W, padx=10, pady=5)
        self.c_turno = ttk.Combobox(form_frame, width=15, state="readonly")
        self.c_turno.grid(row=7, column=2, sticky=W, padx=10, pady=5)

    def criar_interface_responsaveis(self):
        # Título do frame de responsáveis
        Label(self.frame_responsaveis_container, text="Responsáveis", 
              font=('Ivy 12 bold'), bg=self.co1, fg=self.co4).pack(anchor=W, padx=10, pady=5)
        
        # Criando um canvas com scrollbar para os responsáveis
        self.canvas_frame = Frame(self.frame_responsaveis_container, bg=self.co1)
        self.canvas_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        self.canvas = Canvas(self.canvas_frame, bg=self.co1)
        scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        
        # Frame interno para os responsáveis
        self.frame_responsaveis = Frame(self.canvas, bg=self.co1)
        
        # Configurando o canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Criando uma janela no canvas para o frame
        self.canvas_frame_window = self.canvas.create_window((0, 0), window=self.frame_responsaveis, anchor="nw")
        
        # Configurando o evento de redimensionamento
        self.frame_responsaveis.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
    
    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame_window, width=event.width)

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
        frame_resp.campos = {
            'nome': e_nome_resp,
            'telefone': e_telefone,
            'rg': e_rg,
            'cpf': e_cpf,
            'parentesco': c_parentesco
        }
        
        # Inicializando o ID do responsável (se é um novo responsável)
        frame_resp.responsavel_id = None
        
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
            # 1. Pesquisar turma_id na tabela Matriculas usando aluno_id
            self.cursor.execute(
                "SELECT m.turma_id "
                "FROM matriculas m "
                "INNER JOIN anosletivos a ON m.ano_letivo_id = a.id "
                "WHERE m.aluno_id = %s "
                "AND CURDATE() BETWEEN a.data_inicio AND a.data_fim", 
                (self.aluno_id,)
            )
            turma_id_result = self.cursor.fetchone()
            turma_id = turma_id_result[0] if turma_id_result else None
            self.turma_id_atual = turma_id

            # print(f"Turma ID recuperada: {turma_id}")  # Depuração

            if turma_id:
                # 2. Pesquisar turno e serie_id na tabela Turmas usando turma_id
                self.cursor.execute("SELECT nome, turno, serie_id FROM turmas WHERE id = %s", (turma_id,))
                turma_info = self.cursor.fetchone()
                if turma_info:
                    turma_nome, turno, serie_id = turma_info

                    # print(f"Turma Nome: {turma_nome}, Turno: {turno}, Serie ID: {serie_id}")  # Depuração

                    # 3. Pesquisar nome na tabela Series usando serie_id
                    self.cursor.execute("SELECT nome FROM serie WHERE id = %s", (serie_id,))
                    serie = self.cursor.fetchone()
                    if serie:
                        serie_nome = serie[0]

                        # print(f"Série Nome: {serie_nome}")  # Depuração

                        # Atualiza o Combobox de séries com o nome correto
                        self.c_serie.set(serie_nome)
                        
                        # Carregar as turmas da série selecionada
                        self.obter_turmas(serie_id)
                        self.c_turma.set(turma_nome)  # Define a turma no Combobox
                        self.c_turno.set(turno)  # Define o turno no Combobox

            # 4. Carregar dados do aluno
            self.cursor.execute("SELECT nome, endereco, cpf, sus, sexo, data_nascimento, raca, descricao_transtorno FROM alunos WHERE id = %s", (self.aluno_id,))
            aluno = self.cursor.fetchone()
            if aluno:
                self.e_nome.delete(0, END)
                self.e_nome.insert(0, str(aluno[0]))  # Nome
                self.e_endereco.delete(0, END)
                self.e_endereco.insert(0, str(aluno[1]))  # Endereço
                self.e_cpf.delete(0, END)
                self.e_cpf.insert(0, str(aluno[2]))  # CPF
                self.e_sus.delete(0, END)
                self.e_sus.insert(0, str(aluno[3]))  # SUS
                self.c_sexo.set(str(aluno[4]))  # Sexo
                self.c_data_nascimento.delete(0, END)
                self.c_data_nascimento.set_date(datetime.strptime(str(aluno[5]), "%Y-%m-%d").date())  # Data de Nascimento
                self.c_raca.set(str(aluno[6]))  # Raça
                self.e_descricao_transtorno.delete(0, END)
                self.e_descricao_transtorno.insert(0, str(aluno[7]) if aluno[7] else "")  # Descrição do Transtorno

            # 5. Carregar dados dos responsáveis
            self.cursor.execute(
                "SELECT r.id, r.nome, r.grau_parentesco, r.telefone, r.rg, r.cpf "
                "FROM responsaveis r "
                "JOIN responsaveisalunos ra ON r.id = ra.responsavel_id "
                "JOIN alunos a ON ra.aluno_id = a.id "
                "WHERE a.id = %s", 
                (self.aluno_id,)
            )
            responsaveis = self.cursor.fetchall()
            
            # Preencher os dados dos responsáveis existentes
            for responsavel in responsaveis:
                resp_id, resp_nome, resp_parentesco, resp_telefone, resp_rg, resp_cpf = responsavel
                
                # Criar um novo frame para o responsável
                frame_resp = self.add_responsavel()
                
                # Preencher os campos
                frame_resp.campos['nome'].insert(0, resp_nome if resp_nome else "")
                frame_resp.campos['telefone'].insert(0, resp_telefone if resp_telefone else "")
                frame_resp.campos['rg'].insert(0, resp_rg if resp_rg else "")
                frame_resp.campos['cpf'].insert(0, resp_cpf if resp_cpf else "")
                frame_resp.campos['parentesco'].set(resp_parentesco if resp_parentesco else "")
                
                # Armazenar o ID do responsável no frame para uso posterior
                frame_resp.responsavel_id = resp_id

        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao carregar dados do aluno: {str(err)}")
    def salvar_aluno(self):
        try:
            # Coletar os dados do formulário do aluno
            nome = self.e_nome.get()
            endereco = self.e_endereco.get()
            cpf = self.e_cpf.get()
            sus = self.e_sus.get()
            sexo = self.c_sexo.get()
            data_nascimento = self.c_data_nascimento.get_date().strftime("%Y-%m-%d")
            raca = self.c_raca.get()
            descricao_transtorno = self.e_descricao_transtorno.get()
            
            # Obter o ID da turma selecionada
            turma_nome = self.c_turma.get()
            serie_nome = self.c_serie.get()
            
            # Validar campos obrigatórios
            campos_obrigatorios = {
                'Nome': nome,
                'Data de Nascimento': data_nascimento,
                'Sexo': sexo,
                'Raça': raca
            }
            
            campos_vazios = [campo for campo, valor in campos_obrigatorios.items() if not valor]
            if campos_vazios:
                messagebox.showerror("Erro", f"Os seguintes campos obrigatórios não foram preenchidos: {', '.join(campos_vazios)}")
                return

            # Iniciar a transação
            self.conn.start_transaction()
            
            # Atualizar os dados do aluno
            self.cursor.execute(
                """
                UPDATE alunos 
                SET nome = %s, endereco = %s, cpf = %s, sus = %s, sexo = %s, data_nascimento = %s, raca = %s, descricao_transtorno = %s 
                WHERE id = %s
                """,
                (nome, endereco, cpf, sus, sexo, data_nascimento, raca, descricao_transtorno, self.aluno_id)
            )
            
            # Atualizar a matrícula (turma) se houver uma selecionada
            if turma_nome and serie_nome:
                # Obter o ID da série
                self.cursor.execute("SELECT id FROM serie WHERE nome = %s", (serie_nome,))
                serie_result = self.cursor.fetchone()
                if not serie_result:
                    messagebox.showerror("Erro", f"Série '{serie_nome}' não encontrada.")
                    self.conn.rollback()
                    return
                    
                serie_id = serie_result[0]
                
                # Obter o ID da turma
                self.cursor.execute("SELECT id FROM turmas WHERE nome = %s AND serie_id = %s", (turma_nome, serie_id))
                turma_result = self.cursor.fetchone()
                
                if turma_result:
                    nova_turma_id = turma_result[0]
                    
                    # Verificar se já existe uma matrícula para este aluno
                    self.cursor.execute("SELECT id FROM matriculas WHERE aluno_id = %s", (self.aluno_id,))
                    matricula = self.cursor.fetchone()
                    
                    if matricula:
                        # Atualizar a matrícula existente
                        self.cursor.execute(
                            "UPDATE matriculas SET turma_id = %s WHERE aluno_id = %s",
                            (nova_turma_id, self.aluno_id)
                        )
                    else:
                        # Criar uma nova matrícula
                        self.cursor.execute(
                            "INSERT INTO matriculas (aluno_id, turma_id, data_matricula) VALUES (%s, %s, CURDATE())",
                            (self.aluno_id, nova_turma_id)
                        )
            
            # Salvar os responsáveis
            self.salvar_responsaveis()
            
            # Confirmar a transação
            self.conn.commit()
            
            messagebox.showinfo("Sucesso", "Dados do aluno e responsáveis salvos com sucesso!")
            
            # Fechar a janela após salvar com sucesso
            self.fechar_janela()
            
        except mysql.connector.Error as err:
            # Reverter a transação em caso de erro
            self.conn.rollback()
            messagebox.showerror("Erro", f"Não foi possível salvar os dados: {str(err)}")
        except Exception as err:
            # Reverter a transação em caso de erro
            if hasattr(self, 'conn') and self.conn:
                self.conn.rollback()
            messagebox.showerror("Erro", f"Erro inesperado: {str(err)}")

    def salvar_responsaveis(self):
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
            self.salvar_ou_atualizar_responsavel(frame)
    
    def verificar_responsavel_aluno(self, responsavel_id):
        """Verifica se um responsável já está associado ao aluno"""
        self.cursor.execute(
            "SELECT id FROM responsaveisalunos WHERE responsavel_id = %s AND aluno_id = %s",
            (responsavel_id, self.aluno_id)
        )
        return self.cursor.fetchone() is not None
        
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

        # Verificar se já existe um responsável com esse CPF (somente se for um novo responsável)
        if not responsavel_id and cpf:
            self.cursor.execute("SELECT id FROM responsaveis WHERE cpf = %s", (cpf,))
            resp_existente = self.cursor.fetchone()
            if resp_existente:
                responsavel_id = resp_existente[0]
                # Atualizar os dados do responsável existente
                self.cursor.execute(
                    """
                    UPDATE responsaveis 
                    SET nome = %s, grau_parentesco = %s, telefone = %s, rg = %s
                    WHERE id = %s
                    """,
                    (nome, parentesco, telefone, rg, responsavel_id)
                )
                
                # Verificar se a associação já existe
                if not self.verificar_responsavel_aluno(responsavel_id):
                    # Associar o responsável ao aluno
                    self.cursor.execute(
                        "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s, %s)",
                        (responsavel_id, self.aluno_id)
                    )
                
                return responsavel_id

        if responsavel_id:  # Responsável existente, atualizar
            self.cursor.execute(
                """
                UPDATE responsaveis 
                SET nome = %s, grau_parentesco = %s, telefone = %s, rg = %s, cpf = %s
                WHERE id = %s
                """,
                (nome, parentesco, telefone, rg, cpf, responsavel_id)
            )
            
            # Verificar se a associação já existe
            if not self.verificar_responsavel_aluno(responsavel_id):
                # Associar o responsável ao aluno
                self.cursor.execute(
                    "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s, %s)",
                    (responsavel_id, self.aluno_id)
                )
                
            return responsavel_id
        else:  # Novo responsável, inserir
            # Inserir novo responsável
            self.cursor.execute(
                """
                INSERT INTO responsaveis (nome, grau_parentesco, telefone, rg, cpf)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nome, parentesco, telefone, rg, cpf)
            )
            novo_responsavel_id = self.cursor.lastrowid
            
            # Associar o novo responsável ao aluno
            self.cursor.execute(
                "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s, %s)",
                (novo_responsavel_id, self.aluno_id)
            )
            
            return novo_responsavel_id

    def obter_racas(self):
        try:
            racas = ["Branca", "Preta", "Parda", "Amarela", "Indígena", "Não declarada"]
            self.c_raca['values'] = racas
        except Exception as e:
            print(f"Erro ao obter raças: {e}")

    def obter_series(self):
        try:
            # Consulta para obter as séries disponíveis para a escola e ano letivo
            self.cursor.execute(
                """
                SELECT DISTINCT s.id, s.nome 
                FROM serie s
                JOIN turmas t ON s.id = t.serie_id
                WHERE t.ano_letivo_id = %s AND t.escola_id = %s
                ORDER BY s.nome
                """,
                (26, 60)  # ano_letivo_id=26 e escola_id=60
            )
            series = self.cursor.fetchall()
            self.series_map = {serie[1]: serie[0] for serie in series}  # Mapeia nome da série para ID
            self.c_serie['values'] = list(self.series_map.keys())  # Preenche o Combobox de séries
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter séries: {str(e)}")

    def obter_turmas(self, serie_id):
        try:
            # Consulta para obter as turmas da série, ano letivo e escola especificados
            self.cursor.execute(
                """
                SELECT id, nome, turno 
                FROM turmas 
                WHERE serie_id = %s AND ano_letivo_id = %s AND escola_id = %s
                ORDER BY nome
                """,
                (serie_id, 26, 60)  # ano_letivo_id=26 e escola_id=60
            )
            turmas = self.cursor.fetchall()
            self.turmas_map = {turma[1]: turma[0] for turma in turmas}  # Mapeia nome da turma para ID
            self.c_turma['values'] = list(self.turmas_map.keys())  # Preenche o Combobox de turmas

            # Se houver apenas uma turma, seleciona automaticamente
            if len(turmas) == 1:
                turma_nome = turmas[0][1]  # Nome da turma
                turno = turmas[0][2]  # Turno da turma

                # Seleciona a turma e o turno automaticamente
                self.c_turma.set(turma_nome)
                self.c_turno.set(turno)
            else:
                # Limpa a seleção de turma e turno se houver mais de uma turma
                self.c_turma.set("")
                self.c_turno.set("")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter turmas: {str(e)}")
    def obter_turno(self, turma_nome, serie_id):
        try:
            self.cursor.execute("SELECT turno FROM turmas WHERE nome = %s AND serie_id = %s", (turma_nome, serie_id))
            turno = self.cursor.fetchone()
            if turno:
                self.c_turno.set(turno[0])
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter turno: {str(e)}")

    def atualizar_turmas(self, event):
        try:
            serie_nome = self.c_serie.get()
            if serie_nome in self.series_map:
                serie_id = self.series_map[serie_nome]
                self.obter_turmas(serie_id)  # Carrega as turmas para a série selecionada
                # Limpa a seleção de turma e turno
                self.c_turma.set("")
                self.c_turno.set("")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar turmas: {str(e)}")

    def atualizar_turno(self, event):
        try:
            serie_nome = self.c_serie.get()
            turma_nome = self.c_turma.get()
            
            if serie_nome in self.series_map and turma_nome:
                serie_id = self.series_map[serie_nome]
                # Consulta para obter o turno da turma selecionada
                self.cursor.execute(
                    """
                    SELECT turno 
                    FROM turmas 
                    WHERE nome = %s AND serie_id = %s AND ano_letivo_id = %s AND escola_id = %s
                    """,
                    (turma_nome, serie_id, 26, 60)  # ano_letivo_id=26 e escola_id=60
                )
                turno = self.cursor.fetchone()
                if turno:
                    self.c_turno.set(turno[0])  # Define o turno no Combobox
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar turno: {str(e)}")