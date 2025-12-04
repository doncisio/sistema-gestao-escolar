from config_logs import get_logger
from config import get_icon_path
logger = get_logger(__name__)
from datetime import datetime
from tkinter import (
    Label, Frame, Button, Entry, Toplevel, Canvas, Scrollbar,
    NW, LEFT, RIGHT, TOP, BOTTOM, W, E, N, S,
    BOTH, X, Y, VERTICAL, HORIZONTAL, END,
    TRUE, FALSE, GROOVE, RAISED, FLAT, StringVar
)
from tkinter import messagebox, ttk
from PIL import ImageTk, Image
import mysql.connector
from mysql.connector import Error
from conexao import conectar_bd
import tkinter as tk
from tkcalendar import DateEntry
from InterfaceGerenciamentoLicencas import abrir_interface_licencas
from typing import Any, cast

class InterfaceEdicaoFuncionario:
    def __init__(self, master, funcionario_id, janela_principal=None):
        # Armazenar a referência da janela principal
        self.janela_principal = janela_principal
        
        # Armazenar o ID do funcionário que está sendo editado
        self.funcionario_id = funcionario_id
        
        # Variável para controlar se um funcionário foi atualizado com sucesso
        self.funcionario_atualizado = False
        
        # Se a janela principal foi fornecida, escondê-la
        if self.janela_principal:
            self.janela_principal.withdraw()
        
        # Variáveis globais
        self.lista_frames_disciplinas = []
        self.contador_disciplinas = 0
        self.turmas_map = {}
        self.turmas_disciplina_map = {}
        self.turmas_volante_map = {}
        self.disciplinas_map = {}
        self.escolas_map = {}
        
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
        self.master.title("Edição de Funcionário")
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
        self.master.grid_rowconfigure(4, weight=1)  # Conteúdo principal (com scroll)
        self.master.grid_columnconfigure(0, weight=1)

        # Conectar ao banco de dados
        self.conn: Any = None
        self.cursor: Any = None
        try:
            self.conn = conectar_bd()
            if self.conn is None:
                raise Exception("Falha ao conectar ao banco de dados")
            self.cursor = cast(Any, self.conn).cursor(buffered=True)
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao banco de dados: {str(e)}")
            self.fechar_janela()
            return

        # Criar frames e componentes da interface
        self.criar_frames()
        self.criar_header()
        self.criar_botoes()
        self.criar_form_funcionario()
        self.criar_interface_disciplinas()

        # Carregar os dados do funcionário
        self.carregar_dados_funcionario()

    def fechar_janela(self):
        # Confirmar com o usuário se deseja realmente fechar (apenas se nenhum funcionário foi atualizado)
        if not self.funcionario_atualizado and messagebox.askyesno("Confirmar", "Deseja realmente sair? As alterações não salvas serão perdidas.") is False:
            return
        
        # Remover bindings globais antes de destruir a janela
        try:
            self.canvas.unbind_all("<MouseWheel>")
        except Exception:
            pass
            
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
            
            # Nota: A atualização automática da tabela foi removida para evitar conflitos
            # A tabela será atualizada quando o usuário interagir com ela novamente
    
    def atualizar_janela_principal(self):
        """Método auxiliar para atualizar a tabela principal de forma segura"""
        try:
            # Verificar se a janela principal está visível
            if not self.janela_principal or not self.janela_principal.winfo_viewable():
                logger.info("Janela principal não está visível, pulando atualização")
                return
                
            # Usar importação local para evitar problemas de importação circular
            try:
                import main
            except Exception:
                main = None

            # Tentar atualizar via getattr para evitar alerta do analisador (Pylance)
            try:
                updater = getattr(main, 'atualizar_tabela_principal', None)
                if callable(updater):
                    updater()
                    logger.info("Tabela principal atualizada com sucesso")
                else:
                    logger.info("Módulo 'main' não expõe 'atualizar_tabela_principal'; pulando atualização")
            except Exception as update_error:
                logger.info(f"Não foi possível atualizar a tabela principal: {str(update_error)}")
                logger.info("A tabela será atualizada na próxima vez que você navegar pelos registros")
                
        except Exception as e:
            logger.error(f"Erro ao atualizar tabela principal: {str(e)}")

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

        # Frame principal com scrollbar
        self.frame_principal = Frame(self.master, bg=self.co1)
        self.frame_principal.grid(row=4, column=0, sticky='nsew')
        
        # Canvas para scrollbar
        self.canvas = Canvas(self.frame_principal, bg=self.co1)
        self.scrollbar = ttk.Scrollbar(self.frame_principal, orient="vertical", command=self.canvas.yview)
        
        # Frame interno para o conteúdo
        self.frame_conteudo = Frame(self.canvas, bg=self.co1)
        
        # Configurar o canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Criar janela no canvas
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.frame_conteudo, anchor="nw")
        
        # Configurar eventos de redimensionamento
        self.frame_conteudo.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Habilitar scroll com a roda do mouse
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Frame Formulário do Funcionário
        self.frame_funcionario = Frame(self.frame_conteudo, bg=self.co1)
        self.frame_funcionario.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # Frame Disciplinas (para professores)
        self.frame_disciplinas_container = Frame(self.frame_conteudo, bg=self.co1)
        self.frame_disciplinas_container.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Inicialmente ocultar o frame de disciplinas
        self.frame_disciplinas_container.pack_forget()

    def criar_header(self):
        # Título no frame_logo
        try:
            app_img = Image.open(get_icon_path('learning.png'))
            app_img = app_img.resize((45, 45))
            self.app_logo = ImageTk.PhotoImage(app_img)
            app_logo_label = Label(
                self.frame_logo, 
                image=self.app_logo,
                text=" Edição de Funcionário",
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
                text=" Edição de Funcionário",
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
        for i in range(6):  # Aumentado para 6 colunas para acomodar os botões
            botoes_frame.grid_columnconfigure(i, weight=1)

        # Botões
        Button(botoes_frame, text="Atualizar Funcionário", 
               command=self.atualizar_funcionario,
               font=('Ivy 9 bold'),
               bg=self.co3,
               fg=self.co1,
               width=15).grid(row=0, column=0, padx=5, pady=5)

        self.btn_disciplinas = Button(botoes_frame, text="Adicionar Disciplina",
               command=self.add_disciplina,
               font=('Ivy 9'),
               bg=self.co1,
               fg=self.co0,
               width=20,
               state=tk.DISABLED)
        self.btn_disciplinas.grid(row=0, column=1, padx=5, pady=5)
        
        # Botão de Licenças (moved to col 3)

        # Botão para Vincular (novo)
        self.btn_vincular = Button(botoes_frame, text="Vincular",
            command=self.vincular_funcionario,
            font=('Ivy 9'),
            bg='#28a745',
            fg=self.co1,
            width=15, cursor="hand2")
        self.btn_vincular.grid(row=0, column=2, padx=5, pady=5)

        # Botão para Desvincular (novo)
        self.btn_desvincular = Button(botoes_frame, text="Desvincular",
            command=self.desvincular_funcionario,
            font=('Ivy 9'),
            bg=self.co6,
            fg=self.co1,
            width=15, cursor="hand2")
        self.btn_desvincular.grid(row=0, column=3, padx=5, pady=5)

        Button(botoes_frame, text="Gerenciar Licenças",
            command=lambda: abrir_interface_licencas(self.funcionario_id),
            font=('Ivy 9'),
            bg=self.co5,
            fg=self.co1,
            width=15).grid(row=0, column=4, padx=5, pady=5)

        Button(botoes_frame, text="Voltar",
            command=self.fechar_janela,
            font=('Ivy 9'),
            bg=self.co6,
            fg=self.co1,
            width=15).grid(row=0, column=5, padx=5, pady=5)

    def criar_form_funcionario(self):
        # Título do formulário com design moderno
        titulo_frame = Frame(self.frame_funcionario, bg=self.co1, pady=5)
        titulo_frame.pack(fill=X, padx=10)
        
        Label(titulo_frame, text="Edição de Funcionário", 
            font=('Arial 14 bold'), bg=self.co1, fg=self.co5).pack(anchor=W)
        Label(titulo_frame, text="Edite os dados do funcionário nos campos abaixo", 
            font=('Arial 10'), bg=self.co1, fg=self.co4).pack(anchor=W)
        
        # Frame para os campos do formulário
        form_frame = Frame(self.frame_funcionario, bg=self.co1)
        form_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Configuração do grid para o formulário
        for i in range(3):  # 3 colunas
            form_frame.grid_columnconfigure(i, weight=1)
        
        # Estilo para os rótulos e campos
        label_style = {'bg': self.co1, 'fg': self.co4, 'font': ('Arial', 10)}
        entry_style = {'width': 30, 'justify': 'left', 'relief': 'solid', 'font': ('Arial', 10)}
        combo_style = {'width': 28, 'font': ('Arial', 10)}
        
        # COLUNA 1 - Informações Básicas
        col1_frame = Frame(form_frame, bg=self.co1, padx=10, pady=5, relief="flat")
        col1_frame.grid(row=0, column=0, sticky=tk.NSEW)
        
        # Título da seção
        Label(col1_frame, text="Informações Básicas", font=('Arial 11 bold'), bg=self.co1, fg=self.co5).pack(anchor=W, pady=(0, 10))
        
        # Nome (Obrigatório)
        Label(col1_frame, text="Nome Completo *", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_nome = Entry(col1_frame, **entry_style)
        self.e_nome.pack(fill=X, pady=(0, 10))
        
        # Matrícula
        Label(col1_frame, text="Matrícula", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_matricula = Entry(col1_frame, **entry_style)
        self.e_matricula.pack(fill=X, pady=(0, 10))
        
        # Data de Admissão
        Label(col1_frame, text="Data de Admissão", **label_style).pack(anchor=W, pady=(5, 0))
        self.c_data_admissao = DateEntry(
            col1_frame,
            width=28,
            background=self.co5,
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            font=('Arial', 10)
        )
        self.c_data_admissao.pack(anchor=W, pady=(0, 10))
        
        # Data de Nascimento
        Label(col1_frame, text="Data de Nascimento", **label_style).pack(anchor=W, pady=(5, 0))
        self.c_data_nascimento = DateEntry(
            col1_frame,
            width=28,
            background=self.co5,
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            font=('Arial', 10)
        )
        self.c_data_nascimento.pack(anchor=W, pady=(0, 10))
        
        # COLUNA 2 - Informações Profissionais
        col2_frame = Frame(form_frame, bg=self.co1, padx=10, pady=5, relief="flat")
        col2_frame.grid(row=0, column=1, sticky=tk.NSEW)
        
        # Título da seção
        Label(col2_frame, text="Informações Profissionais", font=('Arial 11 bold'), bg=self.co1, fg=self.co5).pack(anchor=W, pady=(0, 10))
        
        # Cargo (Obrigatório)
        Label(col2_frame, text="Cargo *", **label_style).pack(anchor=W, pady=(5, 0))
        self.c_cargo = ttk.Combobox(col2_frame, values=self.obter_cargos(), **combo_style)
        self.c_cargo.pack(anchor=W, pady=(0, 10))
        self.c_cargo.bind('<<ComboboxSelected>>', self.atualizar_interface_cargo)
        
        # Função
        Label(col2_frame, text="Função", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_funcao = Entry(col2_frame, **entry_style)
        self.e_funcao.pack(fill=X, pady=(0, 10))
        
        # Vínculo (Obrigatório)
        Label(col2_frame, text="Vínculo *", **label_style).pack(anchor=W, pady=(5, 0))
        self.c_vinculo = ttk.Combobox(col2_frame, values=('Efetivo', 'Seletivo', 'Comissionado', 'Contratado'), **combo_style)
        self.c_vinculo.pack(anchor=W, pady=(0, 10))
        
        # Carga Horária (Obrigatório)
        Label(col2_frame, text="Carga Horária *", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_carga_horaria = Entry(col2_frame, **entry_style)
        self.e_carga_horaria.pack(fill=X, pady=(0, 10))
        
        # Turno
        Label(col2_frame, text="Turno", **label_style).pack(anchor=W, pady=(5, 0))
        # Popular os valores do combobox a partir do enum do banco (`funcionarios.turno`)
        try:
            enum_vals = self._get_enum_values('funcionarios', 'turno')
            ui_values = [self.db_to_ui_turno(v) or str(v) for v in enum_vals] if enum_vals else ['Matutino', 'Vespertino', 'Matutino/Vespertino']
        except Exception:
            ui_values = ['Matutino', 'Vespertino', 'Matutino/Vespertino']
        self.c_turno = ttk.Combobox(col2_frame, values=ui_values, **combo_style)
        self.c_turno.pack(anchor=W, pady=(0, 10))
        
        # COLUNA 3 - Informações Complementares
        col3_frame = Frame(form_frame, bg=self.co1, padx=10, pady=5, relief="flat")
        col3_frame.grid(row=0, column=2, sticky=tk.NSEW)
        
        # Título da seção
        Label(col3_frame, text="Informações Complementares", font=('Arial 11 bold'), bg=self.co1, fg=self.co5).pack(anchor=W, pady=(0, 10))
        
        # CPF
        Label(col3_frame, text="CPF", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_cpf = Entry(col3_frame, **entry_style)
        self.e_cpf.pack(fill=X, pady=(0, 10))

        # Telefone
        Label(col3_frame, text="Telefone", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_telefone = Entry(col3_frame, **entry_style)
        self.e_telefone.pack(fill=X, pady=(0, 10))
        
        # WhatsApp
        Label(col3_frame, text="WhatsApp", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_whatsapp = Entry(col3_frame, **entry_style)
        self.e_whatsapp.pack(fill=X, pady=(0, 10))
        
        # Email
        Label(col3_frame, text="Email", **label_style).pack(anchor=W, pady=(5, 0))
        self.e_email = Entry(col3_frame, **entry_style)
        self.e_email.pack(fill=X, pady=(0, 10))

        # Seção para professores (inicialmente oculta)
        self.frame_professor = Frame(self.frame_funcionario, bg=self.co1)
        self.frame_professor.pack(fill=BOTH, expand=True, pady=10)
        
        # Título da seção de professor
        Label(self.frame_professor, text="Informações de Professor", 
              font=('Arial 11 bold'), bg=self.co1, fg=self.co5).pack(anchor=W, pady=(0, 10))
        
        # Frame para os campos do professor
        prof_frame = Frame(self.frame_professor, bg=self.co1)
        prof_frame.pack(fill=BOTH, expand=True)
        
        # Configuração do grid para o formulário do professor
        for i in range(3):  # 3 colunas
            prof_frame.grid_columnconfigure(i, weight=1)
        
        # Polivalente
        Label(prof_frame, text="Polivalente *", **label_style).grid(row=0, column=0, sticky=W, padx=10)
        self.c_polivalente = ttk.Combobox(prof_frame, values=('sim', 'não'), **combo_style)
        self.c_polivalente.grid(row=1, column=0, sticky=W, padx=10, pady=(0, 10))
        self.c_polivalente.bind('<<ComboboxSelected>>', self.atualizar_interface_polivalente)
        
        # Professor Volante (apenas para polivalentes)
        self.lbl_volante = Label(prof_frame, text="Professor Volante", **label_style)
        self.lbl_volante.grid(row=0, column=1, sticky=W, padx=10)
        self.c_volante = ttk.Combobox(prof_frame, values=('sim', 'não'), **combo_style)
        self.c_volante.grid(row=1, column=1, sticky=W, padx=10, pady=(0, 10))
        self.c_volante.set('não')  # Valor padrão
        self.lbl_volante.grid_remove()  # Inicialmente oculto
        self.c_volante.grid_remove()  # Inicialmente oculto
        
        # Escola
        Label(prof_frame, text="Escola *", **label_style).grid(row=2, column=1, sticky=W, padx=10)
        self.c_escola = ttk.Combobox(prof_frame, **combo_style, state="readonly")
        self.c_escola.grid(row=3, column=1, sticky=W, padx=10, pady=(0, 10))
        self.obter_escolas()

        # Checkbox para indicar vínculo com a escola (ID: 60)
        self.var_vinculado_escola = tk.IntVar(value=1)
        self.chk_vinculado = tk.Checkbutton(
            prof_frame,
            text='Vinculado à escola (ID: 60)',
            variable=self.var_vinculado_escola,
            bg=self.co1,
            fg=self.co4,
            anchor=W,
            onvalue=1,
            offvalue=0
        )
        self.chk_vinculado.grid(row=4, column=1, sticky=W, padx=10, pady=(0, 8))
        
        # Nota: As turmas são selecionadas através do frame de disciplinas
        # Professores volantes também usam o frame de disciplinas para selecionar suas turmas
        
        # Inicialmente ocultar o frame de professor
        self.frame_professor.pack_forget()

    def criar_interface_disciplinas(self):
        # Título do frame de disciplinas
        self.frame_disciplinas_titulo = Frame(self.frame_disciplinas_container, bg=self.co1)
        self.frame_disciplinas_titulo.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        
        self.lbl_disciplinas = Label(self.frame_disciplinas_titulo, text="Disciplinas", 
                                     font=('Ivy 12 bold'), bg=self.co1, fg=self.co4)
        self.lbl_disciplinas.grid(row=0, column=0, sticky='w')
        
        # Criando um canvas com scrollbar para as disciplinas
        self.canvas_disciplinas_frame = Frame(self.frame_disciplinas_container, bg=self.co1)
        self.canvas_disciplinas_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        
        self.canvas_disciplinas = Canvas(self.canvas_disciplinas_frame, bg=self.co1)
        scrollbar_disciplinas = ttk.Scrollbar(self.canvas_disciplinas_frame, orient="vertical", command=self.canvas_disciplinas.yview)
        
        # Frame interno para as disciplinas
        self.frame_disciplinas = Frame(self.canvas_disciplinas, bg=self.co1)
        
        # Configurando o canvas
        self.canvas_disciplinas.configure(yscrollcommand=scrollbar_disciplinas.set)
        scrollbar_disciplinas.pack(side="right", fill="y")
        self.canvas_disciplinas.pack(side="left", fill="both", expand=True)
        
        # Criando uma janela no canvas para o frame
        self.canvas_disciplinas_window = self.canvas_disciplinas.create_window((0, 0), window=self.frame_disciplinas, anchor="nw")
        
        # Configurando o evento de redimensionamento
        self.frame_disciplinas.bind("<Configure>", self.on_frame_disciplinas_configure)
        self.canvas_disciplinas.bind("<Configure>", self.on_canvas_disciplinas_configure)
        
        # Inicialmente ocultar o frame de disciplinas
        self.frame_disciplinas_container.pack_forget()

    def _get_enum_values(self, table, column):
        """Retorna a lista de valores permitidos para um ENUM no banco (sem aspas)."""
        try:
            self.cursor.execute("SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s", (table, column))
            row = self.cursor.fetchone()
            if not row or not row[0]:
                return []
            col_type = row[0]
            inside = col_type[col_type.find('(')+1:col_type.rfind(')')]
            parts = [p.strip().strip("'") for p in inside.split(',')]
            return parts
        except Exception:
            return []

    def normalize_turno(self, ui_value):
        """Converte valor da UI para um valor compatível com funcionarios.turno.
        Retorna None para gravar NULL quando não existir correspondência.
        """
        if not ui_value:
            return None

        enum_vals = self._get_enum_values('funcionarios', 'turno')
        if ui_value in enum_vals:
            return ui_value

        mapping = {
            'Matutino': ['MAT', 'Matutino'],
            'Vespertino': ['VESP', 'Vespertino'],
            'Matutino/Vespertino': ['Matutino/Vespertino'],
            'Noturno': ['Noturno']
        }

        for key, candidates in mapping.items():
            if ui_value == key:
                for cand in candidates:
                    if cand in enum_vals:
                        return cand

        if 'MAT' in enum_vals and ui_value.lower().startswith('mat'):
            return 'MAT'
        if 'VESP' in enum_vals and ui_value.lower().startswith('ves'):
            return 'VESP'

        return None

    def db_to_ui_turno(self, db_value):
        """Converte um valor vindo do banco para o rótulo exibido na UI."""
        if not db_value:
            return ""

        # Valores curtos para rótulos longos
        reverse_map = {
            'MAT': 'Matutino',
            'VESP': 'Vespertino',
            'Matutino': 'Matutino',
            'Vespertino': 'Vespertino',
            'Matutino/Vespertino': 'Matutino/Vespertino',
            'Noturno': 'Noturno'
        }

        return reverse_map.get(db_value, db_value)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
    
    def _on_mousewheel(self, event):
        """Permite rolar o canvas com a roda do mouse"""
        try:
            if self.canvas.winfo_exists():
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except Exception:
            # Canvas foi destruído, ignorar o evento
            pass
    
    def on_frame_disciplinas_configure(self, event):
        self.canvas_disciplinas.configure(scrollregion=self.canvas_disciplinas.bbox("all"))
    
    def on_canvas_disciplinas_configure(self, event):
        self.canvas_disciplinas.itemconfig(self.canvas_disciplinas_window, width=event.width)

    def atualizar_interface_cargo(self, event=None):
        cargo = self.c_cargo.get()
        
        # Mostrar ou ocultar o frame de professor (aceitar variações como 'Professor')
        try:
            is_prof = isinstance(cargo, str) and cargo.startswith('Professor')
        except Exception:
            is_prof = False

        # Mostrar ou ocultar o frame de professor
        if is_prof:
            self.frame_professor.pack(fill=BOTH, expand=True, pady=10)
            self.frame_disciplinas_container.pack(fill=BOTH, expand=True, padx=10, pady=5)
            self.btn_disciplinas.config(state=tk.NORMAL)
        else:
            self.frame_professor.pack_forget()
            self.frame_disciplinas_container.pack_forget()
            self.btn_disciplinas.config(state=tk.DISABLED)
            
            # Limpar as disciplinas existentes
            for frame in self.lista_frames_disciplinas:
                if frame.winfo_exists():
                    frame.destroy()
            self.lista_frames_disciplinas = []
            self.contador_disciplinas = 0

    def atualizar_interface_polivalente(self, event=None):
        polivalente = self.c_polivalente.get()
        
        # Mostrar ou ocultar controles específicos
        if polivalente == "sim":
            # Professor polivalente - mostrar campo de professor volante
            self.lbl_volante.grid()
            self.c_volante.grid()
            
            # Manter frame de disciplinas e botão habilitado
            self.frame_disciplinas_container.pack(fill=BOTH, expand=True, padx=10, pady=5)
            self.btn_disciplinas.config(state=tk.NORMAL)
        else:
            # Professor não polivalente - mostrar disciplinas
            self.frame_disciplinas_container.pack(fill=BOTH, expand=True, padx=10, pady=5)
            self.btn_disciplinas.config(state=tk.NORMAL)
            
            # Ocultar campo de professor volante
            self.lbl_volante.grid_remove()
            self.c_volante.grid_remove()
            
            # Adicionar pelo menos uma disciplina
            if len(self.lista_frames_disciplinas) == 0:
                self.add_disciplina()

    def add_disciplina(self):
        logger.info(f"\n>>> ADD_DISCIPLINA chamado!")
        logger.info(f">>> frame_disciplinas existe: {hasattr(self, 'frame_disciplinas')}")
        if hasattr(self, 'frame_disciplinas'):
            logger.info(f">>> frame_disciplinas winfo_exists: {self.frame_disciplinas.winfo_exists()}")
        
        self.contador_disciplinas += 1
        
        # Criando um frame para cada disciplina
        frame_disc = Frame(self.frame_disciplinas, bg=self.co2, bd=2, relief="groove")
        frame_disc.pack(fill=X, expand=True, padx=5, pady=8)
        
        logger.info(f">>> Frame disciplina #{self.contador_disciplinas} criado com sucesso!")
        
        # Adicionando o frame à lista para controle
        self.lista_frames_disciplinas.append(frame_disc)
        
        # Cabeçalho do frame de disciplina
        header_frame = Frame(frame_disc, bg=self.co5)
        header_frame.pack(fill=X)
        
        # Título da disciplina
        l_titulo = Label(header_frame, text=f"  Disciplina {self.contador_disciplinas}", 
                        anchor=W, font=('Arial 11 bold'), bg=self.co5, fg=self.co1, padx=10, pady=5)
        l_titulo.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Botão para remover a disciplina
        b_remover = Button(header_frame, text="✖ Remover", bg=self.co6, fg=self.co1, 
                           font=('Arial 9 bold'), relief=FLAT, 
                           command=lambda f=frame_disc: self.remover_disciplina(f), cursor="hand2")
        b_remover.pack(side=RIGHT, padx=5, pady=2)
        
        # Container para o conteúdo
        content_frame = Frame(frame_disc, bg=self.co2, padx=10, pady=10)
        content_frame.pack(fill=BOTH, expand=True)
        
        # Seleção de disciplina
        Label(content_frame, text="Disciplina *", 
              font=('Arial 10 bold'), bg=self.co2, fg=self.co4).pack(anchor=W, pady=(0, 3))
        
        c_disciplina = ttk.Combobox(content_frame, width=50, font=('Arial 10'))
        c_disciplina.pack(fill=X, pady=(0, 15))
        
        # Carregar as disciplinas disponíveis
        self.carregar_disciplinas(c_disciplina)
        
        # Armazenar o combobox no frame para recuperação posterior
        cast(Any, frame_disc).c_disciplina = c_disciplina
        
        # Seleção de turmas para esta disciplina
        Label(content_frame, text="Turmas * (Selecione uma ou mais turmas usando Ctrl+Clique)", 
              font=('Arial 10 bold'), bg=self.co2, fg=self.co4).pack(anchor=W, pady=(0, 3))
        
        # Frame para a lista de turmas com borda
        frame_turmas_container = Frame(content_frame, bg=self.co4, bd=1, relief="solid")
        frame_turmas_container.pack(fill=BOTH, expand=True)
        
        frame_turmas = Frame(frame_turmas_container, bg=self.co1)
        frame_turmas.pack(fill=BOTH, expand=True, padx=1, pady=1)
        
        # Lista de turmas com scrollbar
        scrollbar = Scrollbar(frame_turmas)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Criar uma Listbox para selecionar múltiplas turmas
        lista_turmas = tk.Listbox(frame_turmas, width=50, height=6, 
                       selectmode=tk.MULTIPLE, exportselection=0,
                               font=('Arial 9'), bg=self.co1, 
                               selectbackground=self.co5, selectforeground=self.co1)
        lista_turmas.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Configurar a scrollbar
        lista_turmas.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=lista_turmas.yview)
        
        # Carregar turmas disponíveis
        self.carregar_turmas_para_disciplina(lista_turmas)
        
        # Armazenar a lista de turmas no frame para recuperação posterior
        cast(Any, frame_disc).lista_turmas = lista_turmas
        
        # Adicionar evento para atualizar disciplinas quando turmas forem selecionadas
        lista_turmas.bind('<<ListboxSelect>>', lambda e: self.atualizar_disciplinas_por_turmas(frame_disc))
        
        # Label informativa
        info_label = Label(content_frame, 
                          text="💡 Dica: Mantenha Ctrl pressionado para selecionar várias turmas",
                          font=('Arial 8 italic'), bg=self.co2, fg=self.co4)
        info_label.pack(anchor=W, pady=(5, 0))
        
        # Atualiza a região de rolagem do canvas
        self.frame_disciplinas.update_idletasks()
        
        return frame_disc
        
    def carregar_turmas_para_disciplina(self, lista_turmas):
        """Carrega as turmas disponíveis para a disciplina"""
        try:
            # Obter as turmas da escola 60
            self.cursor.execute("""
                SELECT t.id, s.nome as serie_nome, t.nome as turma_nome,
                CASE WHEN t.turno = 'MAT' THEN 'Matutino' ELSE 'Vespertino' END as turno_nome
                FROM turmas t 
                JOIN series s ON t.serie_id = s.id 
                WHERE t.escola_id = 60
                ORDER BY s.nome, t.nome
            """)
            
            turmas = self.cursor.fetchall()
            self.turmas_disciplina_map = {}
            
            # Limpar a lista
            lista_turmas.delete(0, END)
            
            # Adicionar as turmas à lista com formatação melhorada
            for turma in turmas:
                turma_id = turma[0]
                serie_nome = turma[1]
                turma_nome = turma[2]
                turno_nome = turma[3]
                
                # Formato: "1º Ano - Turma A (Matutino)"
                display_text = f"{serie_nome} - Turma {turma_nome} ({turno_nome})"
                
                lista_turmas.insert(END, display_text)
                self.turmas_disciplina_map[display_text] = turma_id
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar turmas para disciplina: {str(e)}")

    def remover_disciplina(self, frame):
        if len(self.lista_frames_disciplinas) > 1:  # Garantir que haja pelo menos uma disciplina
            self.lista_frames_disciplinas.remove(frame)
            frame.destroy()
            self.reordenar_disciplinas()
        else:
            messagebox.showwarning("Aviso", "É necessário manter pelo menos uma disciplina para professores não polivalentes!")

    def reordenar_disciplinas(self):
        for i, frame in enumerate(self.lista_frames_disciplinas, 1):
            for widget in frame.winfo_children():
                if isinstance(widget, Label) and "Disciplina" in widget.cget("text"):
                    widget.config(text=f"Disciplina {i}")
                    break

    def carregar_disciplinas(self, combobox, nivel_ids=None):
        """Carrega disciplinas, opcionalmente filtradas por nível de ensino"""
        try:
            if nivel_ids:
                # Filtrar por níveis de ensino específicos
                placeholders = ', '.join(['%s'] * len(nivel_ids))
                query = f"SELECT id, nome FROM disciplinas WHERE escola_id = 60 AND nivel_id IN ({placeholders}) ORDER BY nome"
                self.cursor.execute(query, nivel_ids)
            else:
                # Carregar todas as disciplinas
                self.cursor.execute("SELECT id, nome FROM disciplinas WHERE escola_id = 60 ORDER BY nome")
            
            disciplinas = self.cursor.fetchall()
            
            if not disciplinas:
                if nivel_ids:
                    messagebox.showwarning("Aviso", f"Não foram encontradas disciplinas para os níveis de ensino selecionados.")
                else:
                    messagebox.showwarning("Aviso", "Não foram encontradas disciplinas para a escola (ID: 60).")
                combobox['values'] = []
                return
                
            self.disciplinas_map = {disciplina[1]: disciplina[0] for disciplina in disciplinas}
            combobox['values'] = list(self.disciplinas_map.keys())
            
            # Selecionar a primeira disciplina por padrão
            if combobox['values']:
                combobox.set(combobox['values'][0])
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar disciplinas: {str(e)}")
            combobox['values'] = []

    def atualizar_disciplinas_por_turmas(self, frame_disc):
        """Atualiza o combobox de disciplinas baseado nas turmas selecionadas"""
        try:
            # Obter turmas selecionadas
            turmas_selecionadas = cast(Any, frame_disc).lista_turmas.curselection()
            
            if not turmas_selecionadas:
                # Se nenhuma turma selecionada, mostrar todas as disciplinas
                self.carregar_disciplinas(cast(Any, frame_disc).c_disciplina)
                return
            
            # Obter IDs das turmas selecionadas
            turmas_ids = []
            for idx in turmas_selecionadas:
                turma_nome = cast(Any, frame_disc).lista_turmas.get(idx)
                turma_id = self.turmas_disciplina_map.get(turma_nome)
                if turma_id:
                    turmas_ids.append(turma_id)
            
            if not turmas_ids:
                return
            
            # Buscar os níveis de ensino das turmas selecionadas
            placeholders = ', '.join(['%s'] * len(turmas_ids))
            query = f"""
                SELECT DISTINCT s.nivel_id
                FROM turmas t
                JOIN series s ON t.serie_id = s.id
                WHERE t.id IN ({placeholders})
            """
            self.cursor.execute(query, turmas_ids)
            niveis = [row[0] for row in self.cursor.fetchall()]
            
            if niveis:
                # Salvar a disciplina atualmente selecionada
                disciplina_atual = cast(Any, frame_disc).c_disciplina.get()
                
                # Carregar disciplinas filtradas por nível
                self.carregar_disciplinas(cast(Any, frame_disc).c_disciplina, niveis)
                
                # Tentar restaurar a seleção anterior se ainda estiver disponível
                if disciplina_atual and disciplina_atual in cast(Any, frame_disc).c_disciplina['values']:
                    cast(Any, frame_disc).c_disciplina.set(disciplina_atual)
                    
        except Exception as e:
            logger.error(f"Erro ao atualizar disciplinas por turmas: {str(e)}")
            # Em caso de erro, carregar todas as disciplinas
            self.carregar_disciplinas(cast(Any, frame_disc).c_disciplina)

    def carregar_dados_funcionario(self):
        try:
            # Buscar dados do funcionário
            self.cursor.execute("""
                SELECT 
                    f.id, f.matricula, f.data_admissao, f.nome, f.cpf, f.carga_horaria,
                    f.vinculo, f.cargo, f.funcao, f.turno, f.turma, f.telefone, f.whatsapp, 
                    f.email, f.data_nascimento, f.polivalente, f.escola_id, f.volante,
                    e.nome as escola_nome
                FROM funcionarios f
                LEFT JOIN escolas e ON f.escola_id = e.id
                WHERE f.id = %s
            """, (self.funcionario_id,))
            
            funcionario = self.cursor.fetchone()
            
            if funcionario:
                # Preencher os campos com os dados do funcionário
                self.e_nome.insert(0, funcionario[3] or "")  # nome
                self.e_matricula.insert(0, funcionario[1] or "")  # matricula
                
                # Data de admissão
                if funcionario[2]:  # data_admissao
                    self.c_data_admissao.set_date(funcionario[2])
                
                # Data de nascimento
                if funcionario[14]:  # data_nascimento
                    self.c_data_nascimento.set_date(funcionario[14])
                
                self.c_cargo.set(funcionario[7] or "")  # cargo
                self.e_funcao.insert(0, funcionario[8] or "")  # funcao
                self.c_vinculo.set(funcionario[6] or "")  # vinculo
                self.e_carga_horaria.insert(0, funcionario[5] or "")  # carga_horaria
                self.e_cpf.insert(0, funcionario[4] or "")  # cpf
                self.e_telefone.insert(0, funcionario[11] or "")  # telefone
                self.e_whatsapp.insert(0, funcionario[12] or "")  # whatsapp
                self.e_email.insert(0, funcionario[13] or "")  # email
                
                # Salvar estado de escola carregado para uso como fallback
                try:
                    self._loaded_escola_id = funcionario[16]
                except Exception:
                    self._loaded_escola_id = None

                # Ajustar o checkbox e o combobox de escola conforme o dado carregado
                try:
                    if funcionario[16]:
                        try:
                            self.c_escola.set(funcionario[18] or "")  # escola_nome
                        except Exception:
                            pass
                        try:
                            self.var_vinculado_escola.set(1)
                        except Exception:
                            pass
                    else:
                        try:
                            self.var_vinculado_escola.set(0)
                        except Exception:
                            pass
                except Exception:
                    pass

                # Carregar turno para todos os funcionários
                try:
                    ui_turno = self.db_to_ui_turno(funcionario[9]) or ""
                    self.c_turno.set(ui_turno)
                    logger.info(f"Carregado turno para funcionário #{self.funcionario_id}: db='{funcionario[9]}' ui='{ui_turno}' values={self.c_turno['values']}")
                except Exception as e:
                    logger.error(f"Erro ao setar c_turno: {e}")

                # Se for professor, carregar dados específicos
                # Aceitar variações do cargo que indiquem "Professor"
                if funcionario[7] and isinstance(funcionario[7], str) and funcionario[7].startswith('Professor'):
                    self.frame_professor.pack(fill=BOTH, expand=True, pady=10)
                    self.c_polivalente.set(funcionario[15] or "não")  # polivalente
                    
                    # Se for polivalente, mostrar campo de professor volante
                    if funcionario[15] == "sim":
                        self.lbl_volante.grid()
                        self.c_volante.grid()
                        self.c_volante.set(funcionario[17] or "não")  # volante
                    
                    # (Escola e checkbox já foram ajustados acima para todos os funcionários)
                    
                    # Sempre carregar disciplinas para professores (polivalentes ou não)
                    self.frame_disciplinas_container.pack(fill=BOTH, expand=True, padx=10, pady=5)
                    self.btn_disciplinas.config(state=tk.NORMAL)
                    self.carregar_disciplinas_funcionario()
                # Ajustar visibilidade dos botões de vínculo
                try:
                    self.update_vinculo_buttons()
                except Exception:
                    pass
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados do funcionário: {str(e)}")

    def carregar_disciplinas_funcionario(self):
        try:
            logger.info(f"\n=== CARREGANDO DISCIPLINAS DO FUNCIONÁRIO {self.funcionario_id} ===")
            
            # Consulta para obter as disciplinas e turmas do professor
            self.cursor.execute("""
                SELECT d.nome, fd.disciplina_id, fd.turma_id
                FROM funcionario_disciplinas fd
                JOIN disciplinas d ON fd.disciplina_id = d.id
                WHERE fd.funcionario_id = %s
            """, (self.funcionario_id,))
            
            registros = self.cursor.fetchall()
            logger.info(f"Registros encontrados: {len(registros)}")
            
            if registros:
                # Agrupar disciplinas e suas turmas
                disciplinas_map = {}
                for registro in registros:
                    disciplina_nome = registro[0]
                    disciplina_id = registro[1]
                    turma_id = registro[2]
                    logger.info(f"  - Disciplina: {disciplina_nome} (ID: {disciplina_id}), Turma ID: {turma_id}")
                    
                    if disciplina_id not in disciplinas_map:
                        disciplinas_map[disciplina_id] = {
                            'nome': disciplina_nome,
                            'turmas': [turma_id] if turma_id else []
                        }
                    elif turma_id:  # Adicionar turma à disciplina existente
                        disciplinas_map[disciplina_id]['turmas'].append(turma_id)
                
                logger.info(f"\nDisciplinas agrupadas: {len(disciplinas_map)}")
                
                # Para cada disciplina, criar um frame
                for disciplina_id, info in disciplinas_map.items():
                    logger.info(f"\nCriando frame para disciplina: {info['nome']}")
                    frame_disc = self.add_disciplina()
                    cast(Any, frame_disc).c_disciplina.set(info['nome'])
                    logger.info(f"  Disciplina definida: {cast(Any, frame_disc).c_disciplina.get()}")
                    
                    # Selecionar as turmas
                    if info['turmas']:
                        # Obter nomes das turmas para os IDs
                        turmas_ids = info['turmas']
                        logger.info(f"  Turmas IDs para selecionar: {turmas_ids}")
                        logger.info(f"  Mapa de turmas disponível: {self.turmas_disciplina_map}")
                        
                        # Verificar se alguma turma tem ID definido
                        if any(turma_id is not None for turma_id in turmas_ids):
                            # Converter IDs para nomes
                            turmas_nomes = []
                            for i in range(cast(Any, frame_disc).lista_turmas.size()):
                                turma_nome = cast(Any, frame_disc).lista_turmas.get(i)
                                turma_id = self.turmas_disciplina_map.get(turma_nome)
                                if turma_id in turmas_ids:
                                    turmas_nomes.append(i)
                                    logger.info(f"    ✓ Turma encontrada: {turma_nome} (índice {i})")
                            
                            logger.info(f"  Índices para selecionar: {turmas_nomes}")
                            
                            # Selecionar as turmas na lista
                            for idx in turmas_nomes:
                                cast(Any, frame_disc).lista_turmas.selection_set(idx)
                                logger.info(f"    Selecionado índice {idx}")
            else:
                logger.info("Nenhum registro encontrado para este funcionário")
                
            logger.info("=== FIM DO CARREGAMENTO ===\n")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar disciplinas do professor: {str(e)}")
            logger.info(f"Exceção completa ao carregar disciplinas: {str(e)}")
            import traceback
            traceback.print_exc()

    def obter_nome_turma(self, turma_id):
        try:
            # Obter nome completo da turma similar ao formato usado em obter_turmas
            self.cursor.execute("""
                SELECT CONCAT(t.nome, ' - ', s.nome, ' (', 
                CASE WHEN t.turno = 'MAT' THEN 'Matutino' ELSE 'Vespertino' END, ')') as nome_completo 
                FROM turmas t 
                JOIN series s ON t.serie_id = s.id 
                WHERE t.id = %s
            """, (turma_id,))
            turma = self.cursor.fetchone()
            
            if turma and turma[0]:
                # Se a turma existe, verifica se está na lista de turmas disponíveis
                nome_turma = turma[0]
                
                # Se a turma não estiver na lista de turmas disponíveis (não é da escola 60)
                # precisamos recarregar a lista de turmas sem filtro
                if nome_turma not in self.turmas_map:
                    # Verificar escola da turma
                    self.cursor.execute("SELECT escola_id FROM turmas WHERE id = %s", (turma_id,))
                    escola_turma = self.cursor.fetchone()[0]
                    
                    # Se for diferente de 60, mostrar aviso
                    if escola_turma != 60:
                        messagebox.showwarning(
                            "Aviso", 
                            f"A turma selecionada pertence a outra escola (ID: {escola_turma}). "
                            f"Recomendado selecionar turma da escola principal (ID: 60)."
                        )
                
                return nome_turma
            return ""
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter nome da turma: {str(e)}")
            return ""

    def obter_nome_escola(self, escola_id):
        try:
            self.cursor.execute("SELECT nome FROM escolas WHERE id = %s", (escola_id,))
            escola = self.cursor.fetchone()
            return escola[0] if escola else ""
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter nome da escola: {str(e)}")
            return ""

    def update_vinculo_buttons(self):
        """Mostra apenas o botão apropriado (Vincular ou Desvincular) com base no estado atual do vínculo.
        Se o funcionário estiver vinculado (escola_id não NULL) mostra apenas Desvincular; caso contrário mostra apenas Vincular.
        """
        vinculado = False

        # Primeiro tente consultar o banco apenas se a conexão existir
        try:
            conn_ok = hasattr(self, 'conn') and self.conn and (getattr(self.conn, 'is_connected', lambda: True)())
        except Exception:
            conn_ok = False

        if conn_ok and hasattr(self, 'cursor'):
            try:
                self.cursor.execute("SELECT escola_id FROM funcionarios WHERE id = %s", (self.funcionario_id,))
                row = self.cursor.fetchone()
                if row and row[0] is not None:
                    vinculado = True
            except Exception as e:
                # Falhou ao usar o cursor (ex: cursor desconectado) — usar fallback local
                logger.error(f"Erro ao atualizar botões de vínculo: {e}")

        # Fallback: usar estado carregado local ou variável do checkbox
        if not vinculado:
            if hasattr(self, '_loaded_escola_id') and self._loaded_escola_id is not None:
                vinculado = True
            else:
                try:
                    if hasattr(self, 'var_vinculado_escola') and self.var_vinculado_escola.get() == 1:
                        vinculado = True
                except Exception:
                    pass

        # Ajustar visibilidade dos botões conforme vinculado
        try:
            if vinculado:
                try:
                    self.btn_vincular.grid_remove()
                except Exception:
                    pass
                try:
                    self.btn_desvincular.grid()
                except Exception:
                    pass
            else:
                try:
                    self.btn_desvincular.grid_remove()
                except Exception:
                    pass
                try:
                    self.btn_vincular.grid()
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Erro ao ajustar visibilidade dos botões de vínculo: {e}")

    def atualizar_funcionario(self):
        try:
            # Coletar os dados do formulário
            nome = self.e_nome.get()
            matricula = self.e_matricula.get()
            # Se a matrícula estiver vazia, definir como None (NULL no banco de dados)
            if matricula == "":
                matricula = None
                
            data_admissao = self.c_data_admissao.get_date().strftime("%Y-%m-%d") if self.c_data_admissao.get() else None
            data_nascimento = self.c_data_nascimento.get_date().strftime("%Y-%m-%d") if self.c_data_nascimento.get() else None
            cargo = self.c_cargo.get()
            funcao = self.e_funcao.get()
            vinculo = self.c_vinculo.get()
            carga_horaria = self.e_carga_horaria.get()
            cpf = self.e_cpf.get()
            telefone = self.e_telefone.get()
            whatsapp = self.e_whatsapp.get()
            email = self.e_email.get()
            
            # Campos obrigatórios para todos
            campos_obrigatorios = {
                'Nome': nome,
                'Cargo': cargo,
                'Vínculo': vinculo,
                'Carga Horária': carga_horaria
            }
            
            campos_vazios = [campo for campo, valor in campos_obrigatorios.items() if not valor]
            if campos_vazios:
                messagebox.showerror("Erro", f"Os seguintes campos obrigatórios não foram preenchidos: {', '.join(campos_vazios)}")
                return
            
            # Obter o valor de polivalente
            polivalente = self.c_polivalente.get()
            
            # Regras para professores
            if cargo == "Professor@":
                # Professor precisa informar se é polivalente
                if not polivalente:
                    messagebox.showerror("Erro", "Informe se o professor é polivalente.")
                    return
                
                # Todos os professores podem ter disciplinas, então verificamos se há pelo menos uma
                # (não é obrigatório, mas se tiver, deve estar preenchida corretamente)
                if self.lista_frames_disciplinas:
                    # Verificar se cada disciplina tem pelo menos uma turma selecionada
                    for frame in self.lista_frames_disciplinas:
                        if frame.winfo_exists():
                            disciplina_nome = cast(Any, frame).c_disciplina.get()
                            if not disciplina_nome:
                                messagebox.showerror("Erro", "Todas as disciplinas adicionadas devem ser selecionadas.")
                                return
                            
                            turmas_selecionadas = cast(Any, frame).lista_turmas.curselection()
                            if not turmas_selecionadas:
                                messagebox.showerror("Erro", "Selecione pelo menos uma turma para cada disciplina.")
                                return
                
                # Para professores, turma_id é None (será definido na tabela funcionario_disciplinas)
                turma_id = None
            else:
                # Para não professores, turma e polivalente são None/não
                turma_id = None
                polivalente = "não"
            
            # Obter o ID da escola
            escola_nome = self.c_escola.get()
            if escola_nome in self.escolas_map:
                escola_id = self.escolas_map[escola_nome]
            else:
                escola_id = 60  # ID da escola padrão
            
            # Obter turno baseado na seleção e normalizar para o formato do banco
            ui_turno = self.c_turno.get()
            turno = self.normalize_turno(ui_turno)
            
            # Verificar se professor não polivalente está substituindo um polivalente em licença
            professor_substituido = None
            if cargo == "Professor@" and polivalente == "não" and vinculo in ["Seletivo", "Contratado"]:
                # Se for professor não polivalente com vínculo seletivo ou contratado
                # Verificar primeira disciplina para obter uma turma
                if self.lista_frames_disciplinas and self.lista_frames_disciplinas[0].winfo_exists():
                    disciplina_nome = cast(Any, self.lista_frames_disciplinas[0]).c_disciplina.get()
                    turmas_selecionadas = cast(Any, self.lista_frames_disciplinas[0]).lista_turmas.curselection()
                    
                    if turmas_selecionadas:
                        turma_nome = cast(Any, self.lista_frames_disciplinas[0]).lista_turmas.get(turmas_selecionadas[0])
                        primeira_turma_id = self.turmas_disciplina_map.get(turma_nome)
                        
                        # Verificar se está substituindo um professor em licença
                        professor_substituido = self.verificar_professores_em_licenca("Professor@", "sim", primeira_turma_id)
                        
                        # Se for encontrado um professor em licença, perguntar se é uma substituição
                        if professor_substituido:
                            resposta = messagebox.askyesno(
                                "Substituição de Professor", 
                                f"O professor polivalente {professor_substituido[1]} está de licença para esta turma. "
                                f"Este professor não polivalente está sendo contratado para substituí-lo?")
                            
                            if not resposta:
                                professor_substituido = None
            
            # Atualizar o funcionário no banco de dados
            self.cursor.execute(
                """
                UPDATE funcionarios SET
                    nome = %s, matricula = %s, data_admissao = %s, data_nascimento = %s,
                    cpf = %s, carga_horaria = %s, vinculo = %s, cargo = %s, funcao = %s,
                    turno = %s, turma = %s, telefone = %s, whatsapp = %s, email = %s,
                    polivalente = %s, escola_id = %s, volante = %s
                WHERE id = %s
                """,
                (
                    nome, matricula, data_admissao, data_nascimento, cpf, carga_horaria,
                    vinculo, cargo, funcao, turno, turma_id, telefone, whatsapp, email,
                    polivalente, escola_id, self.c_volante.get() if cargo == "Professor@" and polivalente == "sim" else "não",
                    self.funcionario_id
                )
            )

            # Se o usuário desmarcou o vínculo com a escola, aplicar desvinculação adicional
            if hasattr(self, 'var_vinculado_escola') and self.var_vinculado_escola.get() == 0:
                # Preparar atualização para remover vínculo e setar data_saida/ativo quando existirem
                extras = []
                params_extras = []
                # Verificar se as colunas existem
                try:
                    self.cursor.execute(
                        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'funcionarios' AND COLUMN_NAME = 'data_saida'"
                    )
                    has_data_saida = self.cursor.fetchone()[0] > 0
                except Exception:
                    has_data_saida = False

                try:
                    self.cursor.execute(
                        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'funcionarios' AND COLUMN_NAME = 'ativo'"
                    )
                    has_ativo = self.cursor.fetchone()[0] > 0
                except Exception:
                    has_ativo = False

                if has_data_saida:
                    extras.append("data_saida = %s")
                    params_extras.append(datetime.today().strftime("%Y-%m-%d"))
                if has_ativo:
                    extras.append("ativo = %s")
                    params_extras.append(0)

                # Sempre remover escola_id
                sql_extra = "UPDATE funcionarios SET escola_id = NULL"
                if extras:
                    sql_extra += ", " + ", ".join(extras)
                sql_extra += " WHERE id = %s"

                try:
                    params_extras.append(self.funcionario_id)
                    self.cursor.execute(sql_extra, params_extras)
                except Exception as e:
                    logger.error(f"Erro ao aplicar desvinculação adicional: {e}")
            
            # Para todos os professores, atualizar as disciplinas se houver
            if cargo == "Professor@" and self.lista_frames_disciplinas:
                # Primeiro, remover todas as disciplinas antigas
                self.cursor.execute("""
                    DELETE FROM funcionario_disciplinas 
                    WHERE funcionario_id = %s
                """, (self.funcionario_id,))
                
                # Depois, inserir as novas disciplinas
                for frame in self.lista_frames_disciplinas:
                    if frame.winfo_exists():
                        disciplina_nome = cast(Any, frame).c_disciplina.get()
                        if disciplina_nome and disciplina_nome in self.disciplinas_map:
                            disciplina_id = self.disciplinas_map[disciplina_nome]
                            
                            # Obter as turmas selecionadas
                            turmas_selecionadas = frame.lista_turmas.curselection()
                            
                            if turmas_selecionadas:  # Se há turmas selecionadas
                                for idx in turmas_selecionadas:
                                    turma_nome = frame.lista_turmas.get(idx)
                                    turma_id = self.turmas_disciplina_map.get(turma_nome)
                                    
                                    if turma_id:
                                        self.cursor.execute(
                                            "INSERT INTO funcionario_disciplinas (funcionario_id, disciplina_id, turma_id) VALUES (%s, %s, %s)",
                                            (self.funcionario_id, disciplina_id, turma_id)
                                        )
                            else:  # Se nenhuma turma foi selecionada, inserir apenas a disciplina
                                self.cursor.execute(
                                    "INSERT INTO funcionario_disciplinas (funcionario_id, disciplina_id, turma_id) VALUES (%s, %s, NULL)",
                                    (self.funcionario_id, disciplina_id)
                                )
            
            # Se for uma substituição, registrar no banco
            if professor_substituido:
                self.cursor.execute(
                    """
                    INSERT INTO substituicoes_professores (
                        professor_id, substituido_id, data_inicio
                    )
                    VALUES (%s, %s, CURRENT_DATE())
                    """,
                    (self.funcionario_id, professor_substituido[0])
                )
            
            # Confirmar a operação
            self.conn.commit()
            
            messagebox.showinfo("Sucesso", "Funcionário atualizado com sucesso!")
            
            # Marcar que a atualização foi bem-sucedida
            self.funcionario_atualizado = True
            
            # Fechar a janela
            self.fechar_janela()
            # Atualizar visibilidade dos botões caso a janela continue aberta
            try:
                self.update_vinculo_buttons()
            except Exception:
                pass
            
        except Exception as e:
            logger.error(f"Erro ao atualizar funcionário: {e}")
            self.conn.rollback()
            messagebox.showerror("Erro", f"Ocorreu um erro ao atualizar o funcionário: {str(e)}")

    def desvincular_funcionario(self):
        """Desvincula o funcionário da escola (define escola_id = NULL).
        Realiza confirmação, verifica existência de colunas opcionais e aplica a alteração.
        """
        confirmar = messagebox.askyesno("Confirmar desvinculação", "Deseja realmente desvincular este funcionário da escola? Esta ação pode ser revertida manualmente.")
        if not confirmar:
            return

        try:
            # Verificar estado atual
            self.cursor.execute("SELECT escola_id FROM funcionarios WHERE id = %s", (self.funcionario_id,))
            row = self.cursor.fetchone()
            if not row:
                messagebox.showerror("Erro", "Funcionário não encontrado no banco de dados.")
                return

            if row[0] is None:
                messagebox.showinfo("Informação", "Funcionário já está sem vínculo com a escola.")
                return

            # Preparar alteração considerando colunas opcionais
            extras = []
            params = []

            try:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'funcionarios' AND COLUMN_NAME = 'data_saida'"
                )
                has_data_saida = self.cursor.fetchone()[0] > 0
            except Exception:
                has_data_saida = False

            try:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'funcionarios' AND COLUMN_NAME = 'ativo'"
                )
                has_ativo = self.cursor.fetchone()[0] > 0
            except Exception:
                has_ativo = False

            if has_data_saida:
                extras.append("data_saida = %s")
                params.append(datetime.today().strftime("%Y-%m-%d"))
            if has_ativo:
                extras.append("ativo = %s")
                params.append(0)

            sql = "UPDATE funcionarios SET escola_id = NULL"
            if extras:
                sql += ", " + ", ".join(extras)
            sql += " WHERE id = %s"

            params.append(self.funcionario_id)

            # Executar atualização
            self.cursor.execute(sql, params)
            self.conn.commit()

            # Atualizar UI
            try:
                self.var_vinculado_escola.set(0)
            except Exception:
                pass
            try:
                self.c_escola.set("")
            except Exception:
                pass

            # Atualizar estado carregado local
            try:
                self._loaded_escola_id = None
            except Exception:
                pass

            self.funcionario_atualizado = True
            messagebox.showinfo("Sucesso", "Funcionário desvinculado com sucesso.")

            # Tentar atualizar a janela principal se houver
            try:
                self.atualizar_janela_principal()
            except Exception:
                pass

            # Atualizar visibilidade dos botões
            try:
                self.update_vinculo_buttons()
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Erro ao desvincular funcionário: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
            messagebox.showerror("Erro", f"Falha ao desvincular funcionário: {str(e)}")

    def vincular_funcionario(self):
        """Vincula (ou revincula) o funcionário a uma escola. Usa a escola selecionada em `c_escola` ou 60 por padrão.
        Remove `data_saida` e marca `ativo=1` quando as colunas existirem.
        """
        confirmar = messagebox.askyesno("Confirmar vinculação", "Deseja realmente vincular este funcionário à escola selecionada?")
        if not confirmar:
            return

        try:
            # Verificar existência do funcionário
            self.cursor.execute("SELECT escola_id FROM funcionarios WHERE id = %s", (self.funcionario_id,))
            row = self.cursor.fetchone()
            if not row:
                messagebox.showerror("Erro", "Funcionário não encontrado no banco de dados.")
                return

            if row[0] is not None:
                messagebox.showinfo("Informação", "Funcionário já está vinculado a uma escola.")
                return

            # Determinar escola alvo
            escola_nome = self.c_escola.get()
            if escola_nome in self.escolas_map:
                escola_id = self.escolas_map[escola_nome]
            else:
                escola_id = 60

            extras = []
            params = []

            try:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'funcionarios' AND COLUMN_NAME = 'data_saida'"
                )
                has_data_saida = self.cursor.fetchone()[0] > 0
            except Exception:
                has_data_saida = False

            try:
                self.cursor.execute(
                    "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'funcionarios' AND COLUMN_NAME = 'ativo'"
                )
                has_ativo = self.cursor.fetchone()[0] > 0
            except Exception:
                has_ativo = False

            # Remover data_saida (set NULL) se existir e set ativo = 1
            if has_data_saida:
                extras.append("data_saida = NULL")
            if has_ativo:
                extras.append("ativo = %s")
                params.append(1)

            sql = "UPDATE funcionarios SET escola_id = %s"
            params_insert = [escola_id]
            if extras:
                sql += ", " + ", ".join(extras)
            sql += " WHERE id = %s"
            params_insert.extend(params)
            params_insert.append(self.funcionario_id)

            # Executar atualização
            self.cursor.execute(sql, params_insert)
            self.conn.commit()

            # Atualizar UI
            try:
                self.var_vinculado_escola.set(1)
            except Exception:
                pass
            try:
                # Setar o nome exibido da escola
                self.c_escola.set(self.obter_nome_escola(escola_id) or "")
            except Exception:
                pass

            # Atualizar estado carregado local
            try:
                self._loaded_escola_id = escola_id
            except Exception:
                pass

            self.funcionario_atualizado = True
            messagebox.showinfo("Sucesso", "Funcionário vinculado com sucesso.")

            try:
                self.atualizar_janela_principal()
            except Exception:
                pass

            # Atualizar visibilidade dos botões
            try:
                self.update_vinculo_buttons()
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Erro ao vincular funcionário: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
            messagebox.showerror("Erro", f"Falha ao vincular funcionário: {str(e)}")

    def verificar_professores_em_licenca(self, cargo, polivalente, turma_id):
        if cargo != "Professor@" or polivalente != "não" or not turma_id:
            return None
        
        try:
            # Buscar professor polivalente que está de licença e associado à mesma turma
            self.cursor.execute("""
                SELECT f.id, f.nome
                FROM funcionarios f
                JOIN licencas l ON f.id = l.funcionario_id
                WHERE f.cargo = 'Professor@'
                AND f.polivalente = 'sim'
                AND f.turma = %s
                AND CURRENT_DATE() BETWEEN l.data_inicio AND l.data_fim
                LIMIT 1
            """, (turma_id,))
            
            resultado = self.cursor.fetchone()
            
            if resultado:
                return resultado
            return None
        except Exception as e:
            logger.error(f"Erro ao verificar professores em licença: {e}")
            return None

    def obter_cargos(self):
        """Retorna a lista de cargos disponíveis"""
        return [
            'Administrador do Sistemas', 'Gestor Escolar', 'Professor@', 
            'Auxiliar administrativo', 'Agente de Portaria', 'Merendeiro', 
            'Auxiliar de serviços gerais', 'Técnico em Administração Escolar', 
            'Especialista (Coordenadora)', 'Tutor/Cuidador', 'Vigia Noturno', 
            'Interprete de Libras'
        ]

    def obter_escolas(self):
        """Obtém a lista de escolas do banco de dados"""
        try:
            # Limitar apenas à escola com ID 60
            self.cursor.execute("SELECT id, nome FROM escolas WHERE id = 60")
            escolas = self.cursor.fetchall()
            self.escolas_map = {escola[1]: escola[0] for escola in escolas}
            self.c_escola['values'] = list(self.escolas_map.keys())
            
            # Define a escola única como selecionada
            if len(escolas) > 0:
                self.c_escola.set(list(self.escolas_map.keys())[0])
            else:
                # Caso a escola ID 60 não seja encontrada, buscar todas as escolas
                self.cursor.execute("SELECT id, nome FROM escolas ORDER BY nome, id")
                escolas = self.cursor.fetchall()
                
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
                
                # Tentar selecionar a escola 60 se disponível
                for nome, id in self.escolas_map.items():
                    if id == 60:
                        self.c_escola.set(nome)
                        break
                if not self.c_escola.get() and escolas:  # Se não encontrou escola ID 60
                    self.c_escola.set(list(self.escolas_map.keys())[0])  # Primeira escola
                
                messagebox.showwarning("Aviso", "A escola padrão (ID: 60) não foi encontrada. Selecione uma escola manualmente.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter escolas: {str(e)}")

    def obter_turmas(self):
        """Método obsoleto - mantido por compatibilidade mas não faz nada
        As turmas agora são gerenciadas através do frame de disciplinas"""
        pass

    def atualizar_turmas_por_escola(self, event=None):
        """Método obsoleto - mantido por compatibilidade mas não faz nada
        As turmas agora são gerenciadas através do frame de disciplinas"""
        pass