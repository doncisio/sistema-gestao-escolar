"""
Interface Unificada de Matrícula
Mescla funcionalidades de InterfaceEdicaoAluno.editar_matricula() e ui/matricula_modal.py
"""

from datetime import datetime
from tkinter import Toplevel, Frame, Label, Entry, Button, StringVar, Canvas, Scrollbar
from tkinter import LEFT, RIGHT, BOTH, X, Y, VERTICAL, W, messagebox, ttk
from typing import Any, Optional, cast, Dict, Callable
from src.core.config_logs import get_logger

logger = get_logger(__name__)


class InterfaceMatriculaUnificada:
    """
    Interface unificada para criar e editar matrículas.
    Combina todas as funcionalidades das interfaces antigas.
    """
    
    def __init__(
        self,
        parent,
        aluno_id: int,
        nome_aluno: str,
        colors: Dict[str, str],
        conn=None,
        cursor=None,
        callback_sucesso: Optional[Callable] = None
    ):
        """
        Inicializa a interface unificada de matrícula.
        
        Args:
            parent: Janela pai
            aluno_id: ID do aluno
            nome_aluno: Nome do aluno
            colors: Dicionário de cores da interface
            conn: Conexão com banco de dados (opcional)
            cursor: Cursor do banco de dados (opcional)
            callback_sucesso: Função a ser chamada após sucesso
        """
        self.parent = parent
        self.aluno_id = aluno_id
        self.nome_aluno = nome_aluno
        self.colors = colors
        self.callback_sucesso = callback_sucesso
        
        # Conexão com banco de dados
        self.conn_externa = conn
        self.cursor_externo = cursor
        self.conn = None
        self.cursor = None
        
        # Dados da matrícula
        self.matricula_id = None
        self.matricula_existente = False
        self.ano_letivo_id = None
        
        # Dicionários de mapeamento
        self.series_map = {}
        self.turmas_map = {}
        self.escolas_map = {}
        
        # Variáveis dos campos
        self.serie_var = None
        self.turma_var = None
        self.status_var = None
        self.data_matricula_var = None
        self.escola_origem_var = None
        self.escola_destino_var = None
        
        # Criar interface
        self._inicializar_conexao()
        self._criar_interface()
    
    def _inicializar_conexao(self):
        """Inicializa conexão com banco de dados."""
        try:
            if self.conn_externa and self.cursor_externo:
                self.conn = self.conn_externa
                self.cursor = self.cursor_externo
            else:
                from src.core.conexao import conectar_bd
                self.conn = conectar_bd()
                if self.conn is None:
                    raise Exception("Não foi possível conectar ao banco de dados")
                self.cursor = cast(Any, self.conn).cursor()
        except Exception as e:
            logger.exception(f"Erro ao inicializar conexão: {e}")
            messagebox.showerror("Erro", f"Erro ao conectar ao banco: {str(e)}")
            raise
    
    def _criar_interface(self):
        """Cria a interface completa."""
        try:
            # Obter ano letivo atual
            self._obter_ano_letivo_atual()
            
            # Criar janela
            self.janela = Toplevel(self.parent)
            self.janela.title(f"Matrícula - {self.nome_aluno}")
            self.janela.geometry("550x650")
            self.janela.configure(background=self.colors.get('co1', '#FFFFFF'))
            self.janela.transient(self.parent)
            self.janela.focus_force()
            self.janela.grab_set()
            
            # Canvas com scroll
            canvas = Canvas(self.janela, bg=self.colors.get('co1', '#FFFFFF'))
            scrollbar = Scrollbar(self.janela, orient=VERTICAL, command=canvas.yview)
            frame_principal = Frame(canvas, bg=self.colors.get('co1', '#FFFFFF'), padx=20, pady=20)
            
            frame_principal.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=frame_principal, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            # Verificar se já existe matrícula
            self._verificar_matricula_existente()
            
            # Título
            titulo_text = "Editar Matrícula" if self.matricula_existente else "Nova Matrícula"
            Label(
                frame_principal,
                text=titulo_text,
                font=("Arial", 16, "bold"),
                bg=self.colors.get('co1', '#FFFFFF'),
                fg=self.colors.get('co5', '#003A70')
            ).pack(pady=(0, 10))
            
            # Informações do aluno
            info_frame = Frame(frame_principal, bg=self.colors.get('co0', '#F5F5F5'), relief='solid', bd=1)
            info_frame.pack(fill=X, pady=10, padx=5)
            
            Label(
                info_frame,
                text=f"Aluno: {self.nome_aluno}",
                font=("Arial", 12, "bold"),
                bg=self.colors.get('co0', '#F5F5F5'),
                fg=self.colors.get('co7', '#333333')
            ).pack(anchor=W, padx=10, pady=5)
            
            # Obter ano letivo
            cast(Any, self.cursor).execute(
                "SELECT ano_letivo FROM anosletivos WHERE id = %s",
                (self.ano_letivo_id,)
            )
            resultado_ano = cast(Any, self.cursor).fetchone()
            ano_letivo_texto = resultado_ano[0] if resultado_ano else "Atual"
            
            Label(
                info_frame,
                text=f"Ano Letivo: {ano_letivo_texto}",
                font=("Arial", 11),
                bg=self.colors.get('co0', '#F5F5F5'),
                fg=self.colors.get('co7', '#333333')
            ).pack(anchor=W, padx=10, pady=(0, 5))
            
            if self.matricula_existente:
                Label(
                    info_frame,
                    text=f"ID Matrícula: {self.matricula_id}",
                    font=("Arial", 10),
                    bg=self.colors.get('co0', '#F5F5F5'),
                    fg=self.colors.get('co4', '#4A86E8')
                ).pack(anchor=W, padx=10, pady=(0, 5))
            
            # === SEÇÃO: DATA DA MATRÍCULA ===
            data_frame = Frame(frame_principal, bg=self.colors.get('co1', '#FFFFFF'))
            data_frame.pack(fill=X, pady=10)
            
            Label(
                data_frame,
                text="Data da Matrícula (dd/mm/aaaa):",
                font=("Arial", 11, "bold"),
                bg=self.colors.get('co1', '#FFFFFF'),
                fg=self.colors.get('co5', '#003A70')
            ).pack(anchor=W, pady=(0, 5))
            
            self.data_matricula_var = StringVar()
            Entry(
                data_frame,
                textvariable=self.data_matricula_var,
                width=50,
                font=("Arial", 10),
                bg=self.colors.get('co0', '#F5F5F5')
            ).pack(fill=X, pady=5)
            
            # === SEÇÃO: STATUS ===
            status_frame = Frame(frame_principal, bg=self.colors.get('co1', '#FFFFFF'))
            status_frame.pack(fill=X, pady=10)
            
            Label(
                status_frame,
                text="Status da Matrícula:",
                font=("Arial", 11, "bold"),
                bg=self.colors.get('co1', '#FFFFFF'),
                fg=self.colors.get('co5', '#003A70')
            ).pack(anchor=W, pady=(0, 5))
            
            self.status_var = StringVar()
            cb_status = ttk.Combobox(
                status_frame,
                textvariable=self.status_var,
                values=['Ativo', 'Evadido', 'Cancelado', 'Transferido', 'Concluído'],
                width=47,
                state="readonly"
            )
            cb_status.pack(fill=X, pady=5)
            
            # === SEÇÃO: SÉRIE ===
            serie_frame = Frame(frame_principal, bg=self.colors.get('co1', '#FFFFFF'))
            serie_frame.pack(fill=X, pady=10)
            
            Label(
                serie_frame,
                text="Série:",
                font=("Arial", 11, "bold"),
                bg=self.colors.get('co1', '#FFFFFF'),
                fg=self.colors.get('co5', '#003A70')
            ).pack(anchor=W, pady=(0, 5))
            
            self.serie_var = StringVar()
            self.cb_serie = ttk.Combobox(
                serie_frame,
                textvariable=self.serie_var,
                width=47,
                state="readonly"
            )
            self.cb_serie.pack(fill=X, pady=5)
            
            # === SEÇÃO: TURMA ===
            turma_frame = Frame(frame_principal, bg=self.colors.get('co1', '#FFFFFF'))
            turma_frame.pack(fill=X, pady=10)
            
            Label(
                turma_frame,
                text="Turma:",
                font=("Arial", 11, "bold"),
                bg=self.colors.get('co1', '#FFFFFF'),
                fg=self.colors.get('co5', '#003A70')
            ).pack(anchor=W, pady=(0, 5))
            
            self.turma_var = StringVar()
            self.cb_turma = ttk.Combobox(
                turma_frame,
                textvariable=self.turma_var,
                width=47,
                state="readonly"
            )
            self.cb_turma.pack(fill=X, pady=5)
            
            # === SEÇÃO: ESCOLA DE ORIGEM ===
            escola_origem_frame = Frame(frame_principal, bg=self.colors.get('co1', '#FFFFFF'))
            escola_origem_frame.pack(fill=X, pady=10)
            
            Label(
                escola_origem_frame,
                text="Escola de Origem (se transferido de outra escola):",
                font=("Arial", 11, "bold"),
                bg=self.colors.get('co1', '#FFFFFF'),
                fg=self.colors.get('co5', '#003A70')
            ).pack(anchor=W, pady=(0, 5))
            
            self.escola_origem_var = StringVar()
            self.cb_escola_origem = ttk.Combobox(
                escola_origem_frame,
                textvariable=self.escola_origem_var,
                width=47,
                state="readonly"
            )
            self.cb_escola_origem.pack(fill=X, pady=5)
            
            # === SEÇÃO: ESCOLA DE DESTINO ===
            escola_destino_frame = Frame(frame_principal, bg=self.colors.get('co1', '#FFFFFF'))
            escola_destino_frame.pack(fill=X, pady=10)
            
            Label(
                escola_destino_frame,
                text="Escola de Destino (se transferindo para outra escola):",
                font=("Arial", 11, "bold"),
                bg=self.colors.get('co1', '#FFFFFF'),
                fg=self.colors.get('co5', '#003A70')
            ).pack(anchor=W, pady=(0, 5))
            
            self.escola_destino_var = StringVar()
            self.cb_escola_destino = ttk.Combobox(
                escola_destino_frame,
                textvariable=self.escola_destino_var,
                width=47,
                state="readonly"
            )
            self.cb_escola_destino.pack(fill=X, pady=5)
            
            # Carregar dados
            self._carregar_series()
            self._carregar_escolas()
            
            # Vincular evento de mudança de série
            self.cb_serie.bind("<<ComboboxSelected>>", self._carregar_turmas)
            
            # Preencher dados se matrícula existente
            if self.matricula_existente:
                self._preencher_dados_matricula()
            else:
                # Definir valores padrão para nova matrícula
                self.data_matricula_var.set(datetime.now().strftime('%d/%m/%Y'))
                self.status_var.set('Ativo')
                if self.cb_serie['values']:
                    self.cb_serie.current(0)
                    self._carregar_turmas()
            
            # Separador
            Frame(
                frame_principal,
                height=2,
                bg=self.colors.get('co2', '#e5e5e5')
            ).pack(fill=X, pady=20)
            
            # Botões
            botoes_frame = Frame(frame_principal, bg=self.colors.get('co1', '#FFFFFF'))
            botoes_frame.pack(fill=X, pady=10)
            
            # Botão para adicionar nova escola
            Button(
                botoes_frame,
                text="➕ Nova Escola",
                command=self._adicionar_nova_escola,
                font=('Arial', 10),
                bg=self.colors.get('co4', '#4A86E8'),
                fg='#FFFFFF',
                width=15,
                relief='raised'
            ).pack(side=LEFT, padx=5)
            
            # Botão salvar
            texto_salvar = "Atualizar" if self.matricula_existente else "Matricular"
            Button(
                botoes_frame,
                text=texto_salvar,
                command=self._salvar_matricula,
                font=('Arial', 10, 'bold'),
                bg=self.colors.get('co3', '#00a095'),
                fg='#FFFFFF',
                width=15,
                relief='raised'
            ).pack(side=LEFT, padx=5)
            
            # Botão cancelar
            Button(
                botoes_frame,
                text="Cancelar",
                command=self._fechar_janela,
                font=('Arial', 10),
                bg=self.colors.get('co6', '#ef5350'),
                fg='#FFFFFF',
                width=15,
                relief='raised'
            ).pack(side=RIGHT, padx=5)
            
        except Exception as e:
            logger.exception(f"Erro ao criar interface: {e}")
            messagebox.showerror("Erro", f"Erro ao criar interface: {str(e)}")
            self._fechar_janela()
    
    def _obter_ano_letivo_atual(self):
        """Obtém o ID do ano letivo atual."""
        try:
            # Buscar ano letivo atual baseado no ano corrente
            from datetime import datetime
            ano_atual = datetime.now().year
            
            cast(Any, self.cursor).execute("""
                SELECT id FROM anosletivos 
                WHERE ano_letivo = %s
                LIMIT 1
            """, (ano_atual,))
            resultado = cast(Any, self.cursor).fetchone()
            
            # Se não encontrar o ano atual, pegar o mais recente
            if not resultado:
                cast(Any, self.cursor).execute("""
                    SELECT id FROM anosletivos 
                    ORDER BY ano_letivo DESC 
                    LIMIT 1
                """)
                resultado = cast(Any, self.cursor).fetchone()
            
            if not resultado:
                raise Exception("Nenhum ano letivo encontrado no banco de dados.")
            
            self.ano_letivo_id = resultado[0]
            logger.info(f"Ano letivo atual: {self.ano_letivo_id}")
            
        except Exception as e:
            logger.exception(f"Erro ao obter ano letivo: {e}")
            raise
    
    def _verificar_matricula_existente(self):
        """Verifica se já existe matrícula para o aluno no ano letivo atual."""
        try:
            cast(Any, self.cursor).execute("""
                SELECT id FROM matriculas
                WHERE aluno_id = %s AND ano_letivo_id = %s
            """, (self.aluno_id, self.ano_letivo_id))
            
            resultado = cast(Any, self.cursor).fetchone()
            
            if resultado:
                self.matricula_id = resultado[0]
                self.matricula_existente = True
                logger.info(f"Matrícula existente encontrada: {self.matricula_id}")
            else:
                self.matricula_existente = False
                logger.info("Nenhuma matrícula existente - será criada nova matrícula")
                
        except Exception as e:
            logger.exception(f"Erro ao verificar matrícula: {e}")
            self.matricula_existente = False
    
    def _carregar_series(self):
        """Carrega as séries disponíveis."""
        try:
            cast(Any, self.cursor).execute("""
                SELECT DISTINCT s.id, s.nome 
                FROM series s
                JOIN turmas t ON s.id = t.serie_id
                WHERE t.escola_id = 60
                AND t.ano_letivo_id = %s
                ORDER BY s.nome
            """, (self.ano_letivo_id,))
            
            series = cast(Any, self.cursor).fetchall()
            
            if not series:
                messagebox.showwarning("Aviso", "Não foram encontradas séries disponíveis para matrícula.")
                return
            
            self.series_map.clear()
            for serie in series:
                self.series_map[serie[1]] = serie[0]
            
            self.cb_serie['values'] = list(self.series_map.keys())
            logger.info(f"Carregadas {len(series)} séries")
            
        except Exception as e:
            logger.exception(f"Erro ao carregar séries: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar séries: {str(e)}")
    
    def _carregar_turmas(self, event=None):
        """Carrega as turmas da série selecionada."""
        try:
            serie_nome = self.serie_var.get()
            if not serie_nome or serie_nome not in self.series_map:
                return
            
            serie_id = self.series_map[serie_nome]
            
            cast(Any, self.cursor).execute("""
                SELECT id, nome, turno
                FROM turmas 
                WHERE serie_id = %s 
                AND escola_id = 60 
                AND ano_letivo_id = %s
                ORDER BY nome, turno
            """, (serie_id, self.ano_letivo_id))
            
            turmas = cast(Any, self.cursor).fetchall()
            
            if not turmas:
                self.cb_turma['values'] = []
                self.turma_var.set('')
                messagebox.showwarning("Aviso", f"Não há turmas disponíveis para a série {serie_nome}.")
                return
            
            self.turmas_map.clear()
            for turma in turmas:
                # Se nome está vazio, usar turno
                nome_turma = turma[1] if turma[1] else turma[2]
                # Se há apenas uma turma, mostrar como "Única"
                if len(turmas) == 1:
                    nome_turma = "Única"
                self.turmas_map[nome_turma] = turma[0]
            
            self.cb_turma['values'] = list(self.turmas_map.keys())
            
            # Se houver apenas uma turma, selecionar automaticamente
            if len(turmas) == 1:
                self.cb_turma.current(0)
            
            logger.info(f"Carregadas {len(turmas)} turmas para série {serie_nome}")
            
        except Exception as e:
            logger.exception(f"Erro ao carregar turmas: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar turmas: {str(e)}")
    
    def _carregar_escolas(self):
        """Carrega as escolas cadastradas."""
        try:
            cast(Any, self.cursor).execute("""
                SELECT id, nome 
                FROM escolas
                ORDER BY nome
            """)
            
            escolas = cast(Any, self.cursor).fetchall()
            
            self.escolas_map.clear()
            self.escolas_map[''] = None  # Opção vazia
            
            for escola in escolas:
                self.escolas_map[escola[1]] = escola[0]
            
            valores_escolas = [''] + [e[1] for e in escolas]
            self.cb_escola_origem['values'] = valores_escolas
            self.cb_escola_destino['values'] = valores_escolas
            
            logger.info(f"Carregadas {len(escolas)} escolas")
            
        except Exception as e:
            logger.exception(f"Erro ao carregar escolas: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar escolas: {str(e)}")
    
    def _preencher_dados_matricula(self):
        """Preenche os campos com os dados da matrícula existente."""
        try:
            cast(Any, self.cursor).execute("""
                SELECT m.data_matricula, m.status, m.turma_id, 
                       m.escola_origem_id, m.escola_destino_id,
                       t.nome as turma_nome, t.turno, s.nome as serie_nome, s.id as serie_id
                FROM matriculas m
                LEFT JOIN turmas t ON m.turma_id = t.id
                LEFT JOIN series s ON t.serie_id = s.id
                WHERE m.id = %s
            """, (self.matricula_id,))
            
            dados = cast(Any, self.cursor).fetchone()
            
            if not dados:
                messagebox.showerror("Erro", "Não foi possível carregar os dados da matrícula.")
                return
            
            # Preencher data
            if dados[0]:
                self.data_matricula_var.set(dados[0].strftime('%d/%m/%Y'))
            
            # Preencher status
            if dados[1]:
                self.status_var.set(dados[1])
            
            # Preencher série
            if dados[7]:  # serie_nome
                self.serie_var.set(dados[7])
                # Carregar turmas da série
                self._carregar_turmas()
                
                # Preencher turma
                if dados[5]:  # turma_nome
                    turma_display = dados[5] if dados[5] else dados[6]  # nome ou turno
                    # Se há apenas uma turma, foi renomeada para "Única"
                    if len(self.turmas_map) == 1:
                        turma_display = "Única"
                    self.turma_var.set(turma_display)
            
            # Preencher escola de origem
            if dados[3]:  # escola_origem_id
                cast(Any, self.cursor).execute("SELECT nome FROM escolas WHERE id = %s", (dados[3],))
                escola_origem = cast(Any, self.cursor).fetchone()
                if escola_origem:
                    self.escola_origem_var.set(escola_origem[0])
            
            # Preencher escola de destino
            if dados[4]:  # escola_destino_id
                cast(Any, self.cursor).execute("SELECT nome FROM escolas WHERE id = %s", (dados[4],))
                escola_destino = cast(Any, self.cursor).fetchone()
                if escola_destino:
                    self.escola_destino_var.set(escola_destino[0])
            
            logger.info("Dados da matrícula preenchidos com sucesso")
            
        except Exception as e:
            logger.exception(f"Erro ao preencher dados da matrícula: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar dados: {str(e)}")
    
    def _adicionar_nova_escola(self):
        """Abre modal para adicionar nova escola."""
        try:
            dialog_escola = Toplevel(self.janela)
            dialog_escola.title("Adicionar Nova Escola")
            dialog_escola.geometry("450x500")
            dialog_escola.configure(background=self.colors.get('co1', '#FFFFFF'))
            dialog_escola.transient(self.janela)
            dialog_escola.focus_force()
            dialog_escola.grab_set()

            form_frame = Frame(dialog_escola, padx=20, pady=20, bg=self.colors.get('co1', '#FFFFFF'))
            form_frame.pack(fill=BOTH, expand=True)

            Label(
                form_frame,
                text="Adicionar Nova Escola",
                font=("Arial", 14, "bold"),
                bg=self.colors.get('co1', '#FFFFFF'),
                fg=self.colors.get('co5', '#003A70')
            ).pack(pady=(0, 20))

            # Nome (obrigatório)
            Label(form_frame, text="Nome: *", font=("Arial", 10, "bold"),
                  bg=self.colors.get('co1', '#FFFFFF'),
                  fg=self.colors.get('co7', '#333333')).pack(anchor=W, pady=(5, 2))
            nome_entry = Entry(form_frame, width=50, font=("Arial", 10),
                              bg=self.colors.get('co0', '#F5F5F5'))
            nome_entry.pack(fill=X, pady=(0, 10))

            # Endereço
            Label(form_frame, text="Endereço:", font=("Arial", 10, "bold"),
                  bg=self.colors.get('co1', '#FFFFFF'),
                  fg=self.colors.get('co7', '#333333')).pack(anchor=W, pady=(5, 2))
            endereco_entry = Entry(form_frame, width=50, font=("Arial", 10),
                                  bg=self.colors.get('co0', '#F5F5F5'))
            endereco_entry.pack(fill=X, pady=(0, 10))

            # INEP
            Label(form_frame, text="INEP:", font=("Arial", 10, "bold"),
                  bg=self.colors.get('co1', '#FFFFFF'),
                  fg=self.colors.get('co7', '#333333')).pack(anchor=W, pady=(5, 2))
            inep_entry = Entry(form_frame, width=50, font=("Arial", 10),
                              bg=self.colors.get('co0', '#F5F5F5'))
            inep_entry.pack(fill=X, pady=(0, 10))

            # CNPJ
            Label(form_frame, text="CNPJ:", font=("Arial", 10, "bold"),
                  bg=self.colors.get('co1', '#FFFFFF'),
                  fg=self.colors.get('co7', '#333333')).pack(anchor=W, pady=(5, 2))
            cnpj_entry = Entry(form_frame, width=50, font=("Arial", 10),
                              bg=self.colors.get('co0', '#F5F5F5'))
            cnpj_entry.pack(fill=X, pady=(0, 10))

            # Município
            Label(form_frame, text="Município:", font=("Arial", 10, "bold"),
                  bg=self.colors.get('co1', '#FFFFFF'),
                  fg=self.colors.get('co7', '#333333')).pack(anchor=W, pady=(5, 2))
            municipio_entry = Entry(form_frame, width=50, font=("Arial", 10),
                                   bg=self.colors.get('co0', '#F5F5F5'))
            municipio_entry.pack(fill=X, pady=(0, 10))

            # Nota sobre campos obrigatórios
            Label(form_frame, text="* Campo obrigatório", font=("Arial", 9, "italic"),
                  bg=self.colors.get('co1', '#FFFFFF'),
                  fg=self.colors.get('co7', '#333333')).pack(anchor=W, pady=(5, 10))

            def salvar_nova_escola():
                try:
                    nome = nome_entry.get().strip()
                    if not nome:
                        messagebox.showwarning("Aviso", "O nome da escola é obrigatório.")
                        nome_entry.focus()
                        return
                    
                    cast(Any, self.cursor).execute("""
                        INSERT INTO escolas (nome, endereco, inep, cnpj, municipio)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        nome,
                        endereco_entry.get().strip(),
                        inep_entry.get().strip(),
                        cnpj_entry.get().strip(),
                        municipio_entry.get().strip()
                    ))
                    
                    if self.conn:
                        cast(Any, self.conn).commit()
                    
                    novo_id = cast(Any, self.cursor).lastrowid
                    
                    # Atualizar comboboxes
                    self.escolas_map[nome] = novo_id
                    valores_escolas = [''] + [e for e in self.escolas_map.keys() if e != '']
                    self.cb_escola_origem['values'] = valores_escolas
                    self.cb_escola_destino['values'] = valores_escolas
                    
                    messagebox.showinfo("Sucesso", f"Escola '{nome}' adicionada com sucesso!")
                    logger.info(f"Nova escola adicionada: {nome} (ID: {novo_id})")
                    dialog_escola.destroy()
                    
                except Exception as e:
                    if self.conn:
                        cast(Any, self.conn).rollback()
                    logger.exception(f"Erro ao adicionar escola: {e}")
                    messagebox.showerror("Erro", f"Erro ao adicionar escola: {str(e)}")

            # Botões
            botoes_frame = Frame(form_frame, bg=self.colors.get('co1', '#FFFFFF'))
            botoes_frame.pack(fill=X, pady=20)

            Button(
                botoes_frame,
                text="Salvar",
                command=salvar_nova_escola,
                bg=self.colors.get('co3', '#00a095'),
                fg='#FFFFFF',
                width=15,
                font=('Arial', 10, 'bold'),
                relief='raised'
            ).pack(side=LEFT, padx=5)
            
            Button(
                botoes_frame,
                text="Cancelar",
                command=dialog_escola.destroy,
                bg=self.colors.get('co6', '#ef5350'),
                fg='#FFFFFF',
                width=15,
                font=('Arial', 10),
                relief='raised'
            ).pack(side=RIGHT, padx=5)
            
            nome_entry.focus()

        except Exception as e:
            logger.exception(f"Erro ao abrir formulário de escola: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir formulário: {str(e)}")
    
    def _salvar_matricula(self):
        """Salva ou atualiza a matrícula."""
        try:
            # Validar campos obrigatórios
            if not self.serie_var.get() or self.serie_var.get() not in self.series_map:
                messagebox.showwarning("Aviso", "Por favor, selecione uma série válida.")
                self.cb_serie.focus()
                return
            
            if not self.turma_var.get() or self.turma_var.get() not in self.turmas_map:
                messagebox.showwarning("Aviso", "Por favor, selecione uma turma válida.")
                self.cb_turma.focus()
                return
            
            if not self.status_var.get():
                messagebox.showwarning("Aviso", "Por favor, selecione um status.")
                return
            
            # Validar e converter data
            data_str = self.data_matricula_var.get()
            try:
                data_matricula = datetime.strptime(data_str, '%d/%m/%Y').date()
            except ValueError:
                messagebox.showwarning("Aviso", "Data inválida. Use o formato dd/mm/aaaa.")
                return
            
            # Obter IDs
            turma_id = self.turmas_map[self.turma_var.get()]
            status = self.status_var.get()
            
            escola_origem_nome = self.escola_origem_var.get()
            escola_destino_nome = self.escola_destino_var.get()
            
            escola_origem_id = self.escolas_map.get(escola_origem_nome) if escola_origem_nome else None
            escola_destino_id = self.escolas_map.get(escola_destino_nome) if escola_destino_nome else None
            
            if self.matricula_existente:
                # Atualizar matrícula existente
                # Obter status anterior para histórico
                cast(Any, self.cursor).execute(
                    "SELECT status FROM matriculas WHERE id = %s",
                    (self.matricula_id,)
                )
                status_anterior = cast(Any, self.cursor).fetchone()[0]
                
                cast(Any, self.cursor).execute("""
                    UPDATE matriculas 
                    SET data_matricula = %s,
                        status = %s,
                        turma_id = %s,
                        escola_origem_id = %s,
                        escola_destino_id = %s
                    WHERE id = %s
                """, (data_matricula, status, turma_id, escola_origem_id, escola_destino_id, self.matricula_id))
                
                # Registrar histórico se status mudou
                if status != status_anterior:
                    try:
                        cast(Any, self.cursor).execute("""
                            INSERT INTO historico_matricula 
                            (matricula_id, status_anterior, status_novo, data_mudanca)
                            VALUES (%s, %s, %s, %s)
                        """, (self.matricula_id, status_anterior, status, datetime.now().date()))
                    except Exception as hist_err:
                        logger.error(f"Erro ao registrar histórico: {hist_err}")
                
                if self.conn:
                    cast(Any, self.conn).commit()
                
                messagebox.showinfo("Sucesso", "Matrícula atualizada com sucesso!")
                logger.info(f"Matrícula {self.matricula_id} atualizada")
                
            else:
                # Criar nova matrícula
                cast(Any, self.cursor).execute("""
                    INSERT INTO matriculas 
                    (aluno_id, turma_id, ano_letivo_id, data_matricula, status, 
                     escola_origem_id, escola_destino_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (self.aluno_id, turma_id, self.ano_letivo_id, data_matricula, status,
                      escola_origem_id, escola_destino_id))
                
                self.matricula_id = cast(Any, self.cursor).lastrowid
                
                # Registrar no histórico
                try:
                    cast(Any, self.cursor).execute("""
                        INSERT INTO historico_matricula 
                        (matricula_id, status_anterior, status_novo, data_mudanca)
                        VALUES (%s, NULL, %s, %s)
                    """, (self.matricula_id, status, datetime.now().date()))
                except Exception as hist_err:
                    logger.error(f"Erro ao registrar histórico inicial: {hist_err}")
                
                if self.conn:
                    cast(Any, self.conn).commit()
                
                messagebox.showinfo("Sucesso", "Aluno matriculado com sucesso!")
                logger.info(f"Nova matrícula criada: ID {self.matricula_id}")
            
            # Chamar callback de sucesso se fornecido
            if self.callback_sucesso:
                try:
                    self.callback_sucesso()
                except Exception as callback_err:
                    logger.error(f"Erro no callback de sucesso: {callback_err}")
            
            # Fechar janela
            self._fechar_janela()
            
        except Exception as e:
            if self.conn:
                cast(Any, self.conn).rollback()
            logger.exception(f"Erro ao salvar matrícula: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar matrícula: {str(e)}")
    
    def _fechar_janela(self):
        """Fecha a janela e limpa recursos."""
        try:
            # Fechar cursor e conexão se foram criados aqui
            if not self.conn_externa and self.cursor:
                try:
                    self.cursor.close()
                except:
                    pass
            
            if not self.conn_externa and self.conn:
                try:
                    self.conn.close()
                except:
                    pass
            
            # Fechar janela
            if hasattr(self, 'janela') and self.janela:
                self.janela.destroy()
                
        except Exception as e:
            logger.error(f"Erro ao fechar janela: {e}")


def abrir_interface_matricula(parent, aluno_id: int, nome_aluno: str, colors: Dict[str, str],
                               conn=None, cursor=None, callback_sucesso: Optional[Callable] = None):
    """
    Função auxiliar para abrir a interface unificada de matrícula.
    
    Args:
        parent: Janela pai
        aluno_id: ID do aluno
        nome_aluno: Nome do aluno
        colors: Dicionário de cores
        conn: Conexão com banco (opcional)
        cursor: Cursor do banco (opcional)
        callback_sucesso: Callback após sucesso (opcional)
    
    Returns:
        Instância de InterfaceMatriculaUnificada
    """
    return InterfaceMatriculaUnificada(
        parent=parent,
        aluno_id=aluno_id,
        nome_aluno=nome_aluno,
        colors=colors,
        conn=conn,
        cursor=cursor,
        callback_sucesso=callback_sucesso
    )
