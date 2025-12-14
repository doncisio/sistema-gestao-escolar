from config_logs import get_logger
logger = get_logger(__name__)
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from conexao import conectar_bd
import config
import pandas as pd
from datetime import datetime
from utilitarios.conversoes import to_safe_float
import mysql.connector
import os

# Imports para controle de perfil de usuário
from config import perfis_habilitados
from services.perfil_filter_service import PerfilFilterService, get_turmas_usuario
from auth.usuario_logado import UsuarioLogado
from auth.decorators import requer_permissao

# Import para integração com banco de questões
from banco_questoes.resposta_service import RespostaService

class InterfaceCadastroEdicaoNotas:
    def __init__(self, root=None, aluno_id=None, janela_principal=None):
        # Armazenar referência à janela principal
        self.janela_principal = janela_principal
        
        # Se root for None, cria uma nova janela
        if root is None:
            self.janela = tk.Toplevel()
            self.janela.title("Cadastro/Edição de Notas")
            self.janela.geometry("1000x700")
            self.janela.grab_set()  # Torna a janela modal
            self.janela.focus_force()
            
            # Configurar evento de fechamento
            self.janela.protocol("WM_DELETE_WINDOW", self.ao_fechar_janela)
        else:
            self.janela = root

        # Definir as cores para a interface - mesmas cores da main.py
        self.co0 = "#F5F5F5"  # Branco suave para o fundo
        self.co1 = "#003A70"  # Azul escuro (principal)
        self.co2 = "#77B341"  # Verde
        self.co3 = "#E2418E"  # Rosa/Magenta
        self.co4 = "#4A86E8"  # Azul mais claro
        self.co7 = "#333333"  # Cinza escuro
        self.co8 = "#BF3036"  # Vermelho
        self.co9 = "#999999"  # Cinza claro
        
        # Variável para controle de ajustes agendados
        self._ajuste_agendado = None
        
        # Configurar a janela
        self.janela.configure(bg=self.co0)
        # Inicializações padrão para atributos usados pela classe
        # Declarações explícitas ajudam o Pylance a reconhecer os atributos
        self.entradas_notas: dict = {}
        self.notas_dict: dict = {}
        self.alunos_ids: list = []
        self.num_para_id: dict = {}
        self.id_para_num: dict = {}
        self.niveis_map: dict = {}
        self.series_map: dict = {}
        self.turmas_map: dict = {}
        self.disciplinas_map: dict = {}
        self.tabela = None
        self._usar_editor_unico = False
        self._editor_unico = None
        self._editor_aluno_id = None
        # Conjunto de IDs com notas inválidas (string não convertida por parse_nota)
        self.invalid_notas = set()
        
        # Obter ano letivo atual
        self.ano_letivo_atual = self.obter_ano_letivo_atual()
        
        # Inicializar interface
        if self.ano_letivo_atual is not None:
            self.criar_interface()
        else:
            messagebox.showerror("Erro", "Não foi possível obter o ano letivo. A interface será fechada.")
            self.janela.destroy()
    
    def obter_ano_letivo_atual(self):
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if conn is None:
                messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao banco de dados.")
                return None

            cursor = conn.cursor()

            # Primeiro tenta obter o ano letivo do ano atual
            cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = YEAR(CURDATE())")
            resultado_ano = cursor.fetchone()

            if not resultado_ano:
                # Se não encontrar o ano atual, busca o mais recente
                cursor.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                resultado_ano = cursor.fetchone()

            if not resultado_ano:
                messagebox.showwarning("Aviso", "Não foi possível determinar o ano letivo atual.")
                return None

            ano_letivo_id = resultado_ano[0]

            return ano_letivo_id

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter ano letivo atual: {e}")
            return None
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
    
    def criar_barra_menu(self):
        """Cria a barra de menu no topo da janela (estilo página principal)"""
        # Criar a barra de menu
        self.menubar = tk.Menu(self.janela)
        self.janela.config(menu=self.menubar)
        
        # Menu GEDUC
        menu_geduc = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="🌐 GEDUC", menu=menu_geduc)
        
        menu_geduc.add_command(
            label="🔄 Preencher do GEDUC",
            command=self.abrir_preenchimento_automatico
        )
        menu_geduc.add_command(
            label="📥 Extrair Todas Disciplinas",
            command=self.extrair_todas_disciplinas_geduc
        )
        menu_geduc.add_command(
            label="📝 Recuperação Bimestral",
            command=self.processar_recuperacao_bimestral
        )
        
        # Menu Importar/Exportar
        menu_io = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="📊 Importar/Exportar", menu=menu_io)
        
        menu_io.add_command(
            label="📥 Importar do Excel",
            command=self.importar_do_excel,
            accelerator="Ctrl+I"
        )
        menu_io.add_separator()
        menu_io.add_command(
            label="📄 Exportar Template",
            command=self.exportar_template_excel,
            accelerator="Ctrl+T"
        )
        menu_io.add_command(
            label="📤 Exportar para Excel",
            command=self.exportar_para_excel,
            accelerator="Ctrl+E"
        )
        
        # Vincular os atalhos de teclado para Importar/Exportar
        self.janela.bind('<Control-i>', lambda e: self.importar_do_excel())
        self.janela.bind('<Control-I>', lambda e: self.importar_do_excel())
        self.janela.bind('<Control-t>', lambda e: self.exportar_template_excel())
        self.janela.bind('<Control-T>', lambda e: self.exportar_template_excel())
        self.janela.bind('<Control-e>', lambda e: self.exportar_para_excel())
        self.janela.bind('<Control-E>', lambda e: self.exportar_para_excel())
        
        # Menu Ações (botões que sobraram)
        menu_acoes = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="⚙️ Ações", menu=menu_acoes)
        
        menu_acoes.add_command(
            label="💾 Salvar Notas",
            command=self.salvar_notas,
            accelerator="Ctrl+S"
        )
        menu_acoes.add_command(
            label="🧹 Limpar Campos",
            command=self.limpar_campos,
            accelerator="Ctrl+L"
        )
        menu_acoes.add_separator()
        menu_acoes.add_command(
            label="🔄 Atualizar",
            command=self.carregar_notas_alunos,
            accelerator="F5"
        )
        
        # Vincular os atalhos de teclado
        self.janela.bind('<Control-s>', lambda e: self.salvar_notas())
        self.janela.bind('<Control-S>', lambda e: self.salvar_notas())
        self.janela.bind('<Control-l>', lambda e: self.limpar_campos())
        self.janela.bind('<Control-L>', lambda e: self.limpar_campos())
        self.janela.bind('<F5>', lambda e: self.carregar_notas_alunos())
    
    def criar_interface(self):
        # Verificar se o ano letivo foi obtido com sucesso
        if self.ano_letivo_atual is None:
            messagebox.showerror("Erro", "Não foi possível obter o ano letivo atual. A interface será fechada.")
            self.janela.destroy()
            return
        
        # Criar barra de menu no topo (estilo página principal)
        self.criar_barra_menu()
        
        # Criar frames principais (seguindo o modelo do main.py)
        self.criar_frames()
        
        # Criar título da janela
        self.criar_cabecalho("Cadastro e Edição de Notas")
        
        # Criar área de seleção
        self.criar_area_selecao()
        
        # Criar área de notas (inicialmente vazia)
        self.criar_area_notas()
    
    def criar_frames(self):
        # Frame superior para título
        self.frame_titulo = tk.Frame(self.janela, bg=self.co1)
        self.frame_titulo.pack(side="top", fill="x")
        
        # Frame para seleções
        self.frame_selecao = tk.Frame(self.janela, bg=self.co0)
        self.frame_selecao.pack(side="top", fill="x", padx=10, pady=5)
        
        # Frame para estatísticas
        self.frame_estatisticas = tk.LabelFrame(self.janela, text="Estatísticas", bg=self.co0, font=("Arial", 10, "bold"))
        self.frame_estatisticas.pack(side="bottom", fill="x", padx=10, pady=5)
        
        # Frame para tabela de notas (deve ser o último para preencher o espaço restante)
        self.frame_notas = tk.Frame(self.janela, bg=self.co0)
        self.frame_notas.pack(side="top", fill="both", expand=True, padx=10, pady=5)
    
    def criar_cabecalho(self, titulo):
        # Limpar frame de título
        for widget in self.frame_titulo.winfo_children():
            widget.destroy()
        
        # Título principal
        label_titulo = tk.Label(self.frame_titulo, text=titulo, font=("Arial", 14, "bold"), bg=self.co1, fg="white")
        label_titulo.pack(fill="x", padx=10, pady=10)
    
    def criar_area_selecao(self):
        # Limpar frame de seleção
        for widget in self.frame_selecao.winfo_children():
            widget.destroy()
        
        # Criar grid para componentes de seleção
        for i in range(3):
            self.frame_selecao.columnconfigure(i, weight=1)
        
        # Seção 1: Seleção de Nível, Série e Turma
        frame_sec1 = tk.LabelFrame(self.frame_selecao, text="Selecione a Turma", bg=self.co0, font=("Arial", 10, "bold"))
        frame_sec1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        tk.Label(frame_sec1, text="Nível de Ensino:", bg=self.co0).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cb_nivel = ttk.Combobox(frame_sec1, width=25, state="readonly")
        self.cb_nivel.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.cb_nivel.bind("<<ComboboxSelected>>", lambda e: [self.carregar_series(e), self.carregar_disciplinas(e)])
        
        tk.Label(frame_sec1, text="Série:", bg=self.co0).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.cb_serie = ttk.Combobox(frame_sec1, width=25, state="readonly")
        self.cb_serie.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.cb_serie.bind("<<ComboboxSelected>>", self.carregar_turmas)
        
        tk.Label(frame_sec1, text="Turma:", bg=self.co0).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.cb_turma = ttk.Combobox(frame_sec1, width=25, state="readonly")
        self.cb_turma.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        # Não associamos mais ao carregar_disciplinas, apenas atualiza notas quando a turma mudar
        self.cb_turma.bind("<<ComboboxSelected>>", self.carregar_notas_alunos)
        
        # Seção 2: Seleção de Disciplina
        frame_sec2 = tk.LabelFrame(self.frame_selecao, text="Selecione a Disciplina", bg=self.co0, font=("Arial", 10, "bold"))
        frame_sec2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        tk.Label(frame_sec2, text="Disciplina:", bg=self.co0).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cb_disciplina = ttk.Combobox(frame_sec2, width=30, state="readonly")
        self.cb_disciplina.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.cb_disciplina.bind("<<ComboboxSelected>>", self.carregar_notas_alunos)
        
        # Seção 3: Seleção de Bimestre
        frame_sec3 = tk.LabelFrame(self.frame_selecao, text="Selecione o Bimestre", bg=self.co0, font=("Arial", 10, "bold"))
        frame_sec3.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        tk.Label(frame_sec3, text="Bimestre:", bg=self.co0).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cb_bimestre = ttk.Combobox(frame_sec3, width=15, state="readonly", 
                                      values=["1º bimestre", "2º bimestre", "3º bimestre", "4º bimestre"])
        self.cb_bimestre.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.cb_bimestre.current(0)
        self.cb_bimestre.bind("<<ComboboxSelected>>", self.carregar_avaliacoes_disponiveis)
        
        # Botão para carregar
        btn_carregar = tk.Button(frame_sec3, text="Carregar Notas", 
                               command=self.carregar_notas_alunos,
                               bg=self.co4, fg="white", font=("Arial", 10, "bold"))
        btn_carregar.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # ========================================================================
        # NOVA SEÇÃO: Avaliações (Banco de Questões)
        # ========================================================================
        frame_avaliacao = tk.LabelFrame(
            self.frame_selecao, text="📋 Avaliação (Banco de Questões - Opcional)", 
            bg=self.co0, font=("Arial", 10, "bold")
        )
        frame_avaliacao.grid(row=1, column=0, columnspan=3, padx=5, pady=10, sticky="ew")
        
        tk.Label(frame_avaliacao, text="Avaliação:", bg=self.co0).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cb_avaliacao = ttk.Combobox(frame_avaliacao, width=50, state="readonly")
        self.cb_avaliacao.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.cb_avaliacao.bind("<<ComboboxSelected>>", self.ao_selecionar_avaliacao)
        
        # Botões de ação para avaliações
        tk.Button(
            frame_avaliacao, text="📝 Registrar Respostas",
            command=self.abrir_janela_respostas,
            bg=self.co4, fg="white", font=("Arial", 9, "bold")
        ).grid(row=0, column=2, padx=5)
        
        tk.Button(
            frame_avaliacao, text="✍️ Fila de Correção",
            command=self.abrir_fila_correcao,
            bg=self.co2, fg="white", font=("Arial", 9, "bold")
        ).grid(row=0, column=3, padx=5)
        
        tk.Button(
            frame_avaliacao, text="📥 Importar CSV",
            command=self.importar_respostas_csv,
            bg=self.co9, fg="white", font=("Arial", 9, "bold")
        ).grid(row=0, column=4, padx=5)
        
        tk.Button(
            frame_avaliacao, text="🔄 Sincronizar Notas",
            command=self.sincronizar_avaliacoes_para_notas,
            bg="#FF8C00", fg="white", font=("Arial", 9, "bold")
        ).grid(row=0, column=5, padx=5)
        
        # Carregar níveis de ensino inicialmente
        self.carregar_niveis_ensino()
    
    def criar_area_notas(self):
        # Limpar frame de notas
        for widget in self.frame_notas.winfo_children():
            widget.destroy()
        
        # Adicionar mensagem inicial
        label_msg = tk.Label(self.frame_notas, text="Selecione um Nível de Ensino, Série, Turma e Disciplina para carregar as notas",
                           font=("Arial", 12), bg=self.co0)
        label_msg.pack(expand=True, fill="both", padx=20, pady=20)
    
    def criar_estatisticas(self):
        # Limpar frame de estatísticas
        for widget in self.frame_estatisticas.winfo_children():
            widget.destroy()
        
        # Grid para estatísticas - distribuição mais equilibrada
        for i in range(6):
            self.frame_estatisticas.columnconfigure(i, weight=1)
        
        # Labels para estatísticas
        tk.Label(self.frame_estatisticas, text="Média da Turma:", bg=self.co0).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.lbl_media_turma = tk.Label(self.frame_estatisticas, text="--", bg=self.co0, font=("Arial", 10, "bold"), width=5)
        self.lbl_media_turma.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        tk.Label(self.frame_estatisticas, text="Maior Nota:", bg=self.co0).grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.lbl_maior_nota = tk.Label(self.frame_estatisticas, text="--", bg=self.co0, font=("Arial", 10, "bold"), width=5)
        self.lbl_maior_nota.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        tk.Label(self.frame_estatisticas, text="Menor Nota:", bg=self.co0).grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.lbl_menor_nota = tk.Label(self.frame_estatisticas, text="--", bg=self.co0, font=("Arial", 10, "bold"), width=5)
        self.lbl_menor_nota.grid(row=0, column=5, padx=5, pady=5, sticky="w")
        
        tk.Label(self.frame_estatisticas, text="Abaixo da Média:", bg=self.co0).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.lbl_abaixo_media = tk.Label(self.frame_estatisticas, text="--", bg=self.co0, font=("Arial", 10, "bold"), width=5)
        self.lbl_abaixo_media.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        tk.Label(self.frame_estatisticas, text="Acima da Média:", bg=self.co0).grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.lbl_acima_media = tk.Label(self.frame_estatisticas, text="--", bg=self.co0, font=("Arial", 10, "bold"), width=5)
        self.lbl_acima_media.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        tk.Label(self.frame_estatisticas, text="Total de Alunos:", bg=self.co0).grid(row=1, column=4, padx=5, pady=5, sticky="e")
        self.lbl_total_alunos = tk.Label(self.frame_estatisticas, text="0", bg=self.co0, font=("Arial", 10, "bold"), width=5)
        self.lbl_total_alunos.grid(row=1, column=5, padx=5, pady=5, sticky="w")
    
    def carregar_niveis_ensino(self):
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if conn is None:
                messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao banco de dados.")
                return

            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM niveisensino ORDER BY nome")
            niveis = cursor.fetchall()

            if not niveis:
                messagebox.showinfo("Informação", "Nenhum nível de ensino encontrado no banco de dados.")
                return

            self.niveis_map = {nivel[1]: nivel[0] for nivel in niveis}
            self.cb_nivel['values'] = list(self.niveis_map.keys())
            if self.cb_nivel['values']:
                self.cb_nivel.current(0)
                self.carregar_series()
                # Também carregar disciplinas inicialmente
                self.carregar_disciplinas()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar níveis de ensino: {e}")
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
    
    def carregar_series(self, event=None):
        if not self.cb_nivel.get():
            return
        
        nivel_id = self.niveis_map.get(self.cb_nivel.get())
        if nivel_id is None:
            return
        
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if conn is None:
                messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao banco de dados.")
                return

            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM series WHERE nivel_id = %s ORDER BY nome", self._norm_params((nivel_id,)))
            series = cursor.fetchall()

            self.series_map = {serie[1]: serie[0] for serie in series}
            self.cb_serie['values'] = list(self.series_map.keys())
            if self.cb_serie['values']:
                self.cb_serie.current(0)
                self.carregar_turmas()
            else:
                self.cb_serie.set("")
                self.cb_turma.set("")
                self.cb_turma['values'] = []
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar séries: {e}")
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
    
    def carregar_turmas(self, event=None):
        if not self.cb_serie.get():
            return
        
        serie_id = self.series_map.get(self.cb_serie.get())
        if serie_id is None:
            return
        
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if conn is None:
                messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao banco de dados.")
                return

            cursor = conn.cursor()
            
            # Obter filtro de turmas baseado no perfil do usuário
            turmas_permitidas = get_turmas_usuario()
            
            # Construir query com filtro de perfil se necessário
            if turmas_permitidas is None:
                # Admin/Coordenador - sem filtro
                cursor.execute("""
                    SELECT t.id, CONCAT(t.nome, ' - ', t.turno) AS turma_nome 
                    FROM turmas t 
                    WHERE t.serie_id = %s AND t.ano_letivo_id = %s
                    ORDER BY t.nome
                """, self._norm_params((serie_id, self.ano_letivo_atual)))
            elif not turmas_permitidas:
                # Professor sem turmas vinculadas
                self.turmas_map = {}
                self.cb_turma['values'] = []
                self.cb_turma.set("")
                self.cb_disciplina.set("")
                self.cb_disciplina['values'] = []
                messagebox.showinfo(
                    "Sem turmas", 
                    "Você não possui turmas vinculadas para lançamento de notas.\n"
                    "Contate a coordenação para vincular suas disciplinas."
                )
                return
            else:
                # Professor - filtrar apenas turmas vinculadas
                placeholders = ','.join(['%s'] * len(turmas_permitidas))
                cursor.execute(f"""
                    SELECT t.id, CONCAT(t.nome, ' - ', t.turno) AS turma_nome 
                    FROM turmas t 
                    WHERE t.serie_id = %s AND t.ano_letivo_id = %s
                    AND t.id IN ({placeholders})
                    ORDER BY t.nome
                """, self._norm_params((serie_id, self.ano_letivo_atual, *turmas_permitidas)))
            
            turmas = cursor.fetchall()

            self.turmas_map = {turma[1]: turma[0] for turma in turmas}
            self.cb_turma['values'] = list(self.turmas_map.keys())
            if self.cb_turma['values']:
                self.cb_turma.current(0)
                # Sempre recarregar as disciplinas quando a turma mudar
                self.carregar_disciplinas()
            else:
                self.cb_turma.set("")
                self.cb_disciplina.set("")
                self.cb_disciplina['values'] = []
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar turmas: {e}")
            logger.error(f"Erro detalhado ao carregar turmas: {str(e)}")
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
    
    def carregar_disciplinas(self, event=None):
        if not self.cb_nivel.get():
            return
        
        nivel_id = self.niveis_map.get(self.cb_nivel.get())
        if nivel_id is None:
            return
        
        # Obter turma selecionada para filtro de professor
        turma_id = self.turmas_map.get(self.cb_turma.get()) if self.cb_turma.get() else None
        
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if conn is None:
                messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao banco de dados.")
                return

            cursor = conn.cursor()
            
            # Verificar se é professor e aplicar filtro de disciplinas
            if perfis_habilitados() and UsuarioLogado.get_perfil() == 'professor':
                funcionario_id = UsuarioLogado.get_funcionario_id()
                if funcionario_id and turma_id:
                    # Professor: buscar apenas disciplinas que ele leciona na turma
                    cursor.execute("""
                        SELECT DISTINCT d.id, d.nome 
                        FROM disciplinas d
                        INNER JOIN funcionario_disciplinas fd ON fd.disciplina_id = d.id
                        WHERE fd.funcionario_id = %s 
                        AND fd.turma_id = %s
                        AND d.escola_id = %s
                        ORDER BY d.nome
                    """, self._norm_params((funcionario_id, turma_id, config.ESCOLA_ID)))
                    disciplinas = cursor.fetchall()
                    
                    if not disciplinas:
                        # Tentar sem filtro de turma (caso disciplinas não estejam vinculadas corretamente)
                        cursor.execute("""
                            SELECT DISTINCT d.id, d.nome 
                            FROM disciplinas d
                            INNER JOIN funcionario_disciplinas fd ON fd.disciplina_id = d.id
                            WHERE fd.funcionario_id = %s 
                            AND d.nivel_id = %s
                            AND d.escola_id = %s
                            ORDER BY d.nome
                        """, self._norm_params((funcionario_id, nivel_id, config.ESCOLA_ID)))
                        disciplinas = cursor.fetchall()
                else:
                    disciplinas = []
            else:
                # Admin/Coordenador: todas as disciplinas do nível
                cursor.execute("""
                    SELECT id, nome 
                    FROM disciplinas 
                    WHERE nivel_id = %s AND escola_id = %s
                    ORDER BY nome
                """, self._norm_params((nivel_id, config.ESCOLA_ID)))
                disciplinas = cursor.fetchall()

                # Se não encontrar disciplinas com nivel_id, tenta buscar todas da escola
                if not disciplinas:
                    cursor.execute("""
                        SELECT id, nome 
                        FROM disciplinas 
                        WHERE escola_id = %s
                        ORDER BY nome
                    """, self._norm_params((config.ESCOLA_ID,)))
                    disciplinas = cursor.fetchall()

            if not disciplinas:
                msg = "Não há disciplinas vinculadas a você nesta turma." if perfis_habilitados() and UsuarioLogado.get_perfil() == 'professor' else "Não há disciplinas cadastradas para esta escola."
                messagebox.showinfo("Informação", msg)
                self.cb_disciplina.set("")
                self.cb_disciplina['values'] = []
                return

            self.disciplinas_map = {disc[1]: disc[0] for disc in disciplinas}
            self.cb_disciplina['values'] = list(self.disciplinas_map.keys())
            if self.cb_disciplina['values']:
                self.cb_disciplina.current(0)
            # Carrega automaticamente as notas quando a disciplina for selecionada
            self.janela.after(100, self.carregar_notas_alunos)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar disciplinas: {e}")
            logger.error(f"Erro detalhado: {str(e)}")
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
    
    def carregar_notas_alunos(self, event=None):
        # Verificações iniciais
        if not self.cb_turma.get():
            logger.info("Nenhuma turma selecionada. Não é possível carregar notas.")
            return
            
        if not self.cb_disciplina.get():
            logger.info("Nenhuma disciplina selecionada. Não é possível carregar notas.")
            return
            
        if not self.cb_bimestre.get():
            logger.info("Nenhum bimestre selecionado. Não é possível carregar notas.")
            return
        
        # Limpar frame de notas
        for widget in self.frame_notas.winfo_children():
            widget.destroy()
        
        # Verificar se os dicionários de mapeamento foram criados corretamente
        if not hasattr(self, 'turmas_map') or not self.turmas_map:
            messagebox.showerror("Erro", "O mapeamento de turmas não foi criado corretamente.")
            logger.error("Erro: turmas_map não existe ou está vazio")
            return
            
        if not hasattr(self, 'disciplinas_map') or not self.disciplinas_map:
            messagebox.showerror("Erro", "O mapeamento de disciplinas não foi criado corretamente.")
            logger.error("Erro: disciplinas_map não existe ou está vazio")
            return
        
        # Validar seleções
        turma = self.cb_turma.get()
        disciplina = self.cb_disciplina.get()
        bimestre = self.cb_bimestre.get()
        
        # print(f"Validando - Turma: {turma}, Disciplina: {disciplina}, Bimestre: {bimestre}")
        # print(f"Mapeamento de turmas: {self.turmas_map}")
        # print(f"Mapeamento de disciplinas: {self.disciplinas_map}")
        
        # Obter IDs das seleções
        turma_id = self.turmas_map.get(turma)
        disciplina_id = self.disciplinas_map.get(disciplina)
        
        # Verificar se os IDs foram obtidos corretamente
        if turma_id is None:
            messagebox.showerror("Erro", f"Não foi possível obter o ID da turma: '{turma}'")
            logger.info(f"Turmas disponíveis: {self.turmas_map}")
            return
            
        if disciplina_id is None:
            messagebox.showerror("Erro", f"Não foi possível obter o ID da disciplina: '{disciplina}'")
            logger.info(f"Disciplinas disponíveis: {self.disciplinas_map}")
            return
        
        # Guardar IDs para uso em outras funções
        self.turma_id = turma_id
        self.disciplina_id = disciplina_id
        self.bimestre = bimestre
        
        # print(f"Carregando notas - Turma: {turma_id}, Disciplina: {disciplina_id}, Bimestre: {bimestre}")
        
        try:
            conn = conectar_bd()
            cursor = None
            if conn is None:
                messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao banco de dados.")
                return
            cursor = conn.cursor()
            
            # Buscar alunos da turma em ordem alfabética
            cursor.execute("""
                SELECT a.id, a.nome, m.status 
                FROM alunos a
                JOIN matriculas m ON a.id = m.aluno_id
                WHERE m.turma_id = %s 
                AND m.ano_letivo_id = %s 
                AND m.status IN ('Ativo', 'Transferido')
                AND a.escola_id = %s
                ORDER BY a.nome
            """, self._norm_params((turma_id, self.ano_letivo_atual, config.ESCOLA_ID)))
            
            alunos = cursor.fetchall()
            
            # fechará em finally
            
            logger.info(f"Alunos encontrados: {len(alunos)}")
            
            if not alunos:
                messagebox.showinfo("Informação", "Não há alunos matriculados nesta turma.")
                return
            
            # Armazenar dados para uso posterior
            self.alunos = alunos
            self.disciplina_id = disciplina_id
            self.bimestre = bimestre
            
            # print("Criando tabela de notas...")
            # Criar tabela de notas
            self.criar_tabela_notas(alunos)
            
            logger.info("Atualizando estatísticas...")
            # Atualizar estatísticas
            self.criar_estatisticas()
            self.atualizar_estatisticas()
            logger.info("Notas carregadas com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
    
    def criar_tabela_notas(self, alunos):
        # Frame com scroll para a tabela
        frame_tabela = tk.Frame(self.frame_notas, bg=self.co0)
        frame_tabela.pack(fill="both", expand=True)
        
        # Criar tabela Treeview
        colunas = ["num", "nome", "nota"]
        self.tabela = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=15)
        
        # Definir cabeçalhos
        self.tabela.heading("num", text="Nº")
        self.tabela.heading("nome", text="Nome do Aluno")
        self.tabela.heading("nota", text="Nota")
        
        # Configurar colunas
        self.tabela.column("num", width=40, anchor="center")
        self.tabela.column("nome", width=460, anchor="w")
        self.tabela.column("nota", width=80, anchor="center")
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        scrollbar_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self.tabela.xview)
        self.tabela.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Posicionar elementos
        self.tabela.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        
        # Preparar estruturas para notas e mapeamentos
        self.notas_dict = {}  # {aluno_id: nota_str}
        self.alunos_ids = []  # Lista para manter a ordem dos IDs dos alunos
        self.num_para_id = {}  # Mapeamento de número sequencial para ID do aluno
        self.id_para_num = {}  # Mapeamento de ID do aluno para número sequencial

        # Configurando um estilo para destacar os alunos transferidos
        style = ttk.Style()
        style.configure("Transferido.Treeview.Row", foreground="blue")

        # Numerar os alunos sequencialmente (começando de 1) e preencher Treeview
        for num, aluno in enumerate(alunos, 1):
            aluno_id = aluno[0]
            nome_aluno = aluno[1]
            status_aluno = aluno[2] if len(aluno) > 2 else "Ativo"

            nome_display = f"{nome_aluno} (Transferido)" if status_aluno == "Transferido" else nome_aluno

            self.alunos_ids.append(aluno_id)
            self.num_para_id[num] = aluno_id
            self.id_para_num[aluno_id] = num

            # Buscar nota existente e guardar em dicionário
            nota = self.buscar_nota_existente(aluno_id, self.disciplina_id, self.bimestre)
            nota_str = str(nota) if nota is not None else ""
            self.notas_dict[aluno_id] = nota_str

            # Inserir na tabela
            item_id = self.tabela.insert("", "end", values=(num, nome_display, nota_str))
            if status_aluno == "Transferido":
                self.tabela.item(item_id, tags=("transferido",))

        # Criar editor único (reutilizável) para a coluna de notas
        self._usar_editor_unico = True
        self._editor_unico = tk.Entry(self.tabela, width=8, font=("Arial", 10), bg="white", relief="solid", borderwidth=1, justify="center")
        self._editor_unico.bind("<Return>", lambda e: self._fechar_editor(commit=True, mover_proximo=True))
        self._editor_unico.bind("<Tab>", lambda e: self._fechar_editor(commit=True, mover_proximo=True))
        self._editor_unico.bind("<FocusOut>", lambda e: self._fechar_editor(commit=True, mover_proximo=False))
        # Variável para saber qual aluno está sendo editado
        self._editor_aluno_id = None

        # Eventos para abrir o editor ao clicar/dar duplo-clique na célula de nota
        dbl_cb = getattr(self, '_on_treeview_double_click', None)
        if callable(dbl_cb):
            self.tabela.bind("<Double-1>", dbl_cb)
        else:
            self.tabela.bind("<Double-1>", lambda e: None)

        ret_cb = getattr(self, '_on_treeview_return', None)
        if callable(ret_cb):
            # wrapper para receber o event arg
            self.tabela.bind("<Return>", lambda e, f=ret_cb: f())
        else:
            self.tabela.bind("<Return>", lambda e: None)
        
        # Configurar cor para os alunos transferidos
        self.tabela.tag_configure("transferido", foreground="blue")
        # Tag para destacar linhas com nota inválida
        try:
            self.tabela.tag_configure("nota_invalida", background="#FFCCCC")
        except Exception:
            pass
        
        # Eventos de seleção: ao selecionar um item, abrir o editor na coluna nota
        sel_cb = getattr(self, '_on_treeview_select', None)
        if callable(sel_cb):
            self.tabela.bind("<<TreeviewSelect>>", lambda e, f=sel_cb: f())
        else:
            self.tabela.bind("<<TreeviewSelect>>", lambda e: None)

        # Permitir foco no Treeview para navegação por teclado
        try:
            self.tabela.focus_set()
        except Exception:
            pass

        # Bind de teclas Up/Down para navegar entre linhas e abrir o editor
        try:
            self.tabela.bind('<Up>', self._on_key_up)
            self.tabela.bind('<Down>', self._on_key_down)
            # Também vincular na janela para garantir captura mesmo quando foco não estiver no treeview
            self.janela.bind('<Up>', lambda e: self._on_key_up(e))
            self.janela.bind('<Down>', lambda e: self._on_key_down(e))
        except Exception:
            pass

        # Quando usar editor único, as rotinas de ajuste de múltiplas entradas tornam-se no-op
        # Mantemos os bindings existentes, mas os handlers verificarão a flag
        self.tabela.bind("<ButtonRelease-1>", self.ajustar_entradas)
        self.tabela.bind("<Motion>", self.ajustar_entradas)
        self.tabela.bind("<Configure>", self.ajustar_entradas)
        self.janela.bind("<Configure>", self.ajustar_entradas)
        self.frame_notas.bind("<Configure>", self.ajustar_entradas)
        
        # Focar no primeiro aluno (selecionar primeira linha)
        if self.alunos_ids:
            primeiro_id = self.alunos_ids[0]
            # Atrasar ligeiramente a seleção/abertura do editor inicial
            try:
                self.janela.after(150, lambda id=primeiro_id: self.selecionar_item_por_id(id))
            except Exception:
                self.selecionar_item_por_id(primeiro_id)
    
    def forcar_redesenho_entradas(self):
        """Força o redesenho de todas as entradas para garantir que elas sejam visíveis"""
        try:
            # print("Forçando redesenho das entradas...")
            # Atualizar a interface
            self.janela.update_idletasks()
            
            # Verificar se os dicionários necessários estão presentes
            if not hasattr(self, 'entradas_notas') or not self.entradas_notas:
                logger.info("Não há entradas de notas para redesenhar")
                return
                
            if not hasattr(self, 'id_para_num') or not self.id_para_num:
                logger.info("Mapeamento de ID para número não existe")
                return
            
            # Se estamos usando editor único, não há múltiplas entradas para redesenhar
            if getattr(self, '_usar_editor_unico', False):
                return

            # Reposicionar todas as entradas (comportamento legacy)
            if hasattr(self, 'entradas_notas'):
                for aluno_id, entrada in self.entradas_notas.items():
                    try:
                        if not entrada.winfo_exists():
                            continue
                        entrada.place_forget()
                    except Exception as e:
                        logger.error(f"Erro ao esconder entrada do aluno {aluno_id}: {e}")

            # Aplicar ajuste de entradas que irá reposicionar tudo corretamente
            self._realizar_ajuste_entradas()
            
        except Exception as e:
            logger.error(f"Erro ao redesenhar entradas: {e}")
            import traceback
            traceback.print_exc()
    
    def navegar_para_proxima_entrada(self, event):
        """Move o foco para a próxima entrada de nota após pressionar Tab ou Enter"""
        # Se estamos usando editor único, navegar entre alunos via lista ordenada
        if getattr(self, '_usar_editor_unico', False):
            current = self._editor_aluno_id
            if current is None:
                return "break"
            try:
                idx = self.alunos_ids.index(current)
            except ValueError:
                return "break"
            # Próximo índice
            next_idx = (idx + 1) % len(self.alunos_ids)
            next_id = self.alunos_ids[next_idx]
            self._fechar_editor(commit=True, mover_proximo=False)
            self.abrir_editor_para_aluno(next_id)
            return "break"

        # Comportamento legacy (entradas individuais)
        current_focus_id = None
        for aluno_id, entrada in self.entradas_notas.items():
            if entrada == self.janela.focus_get():
                current_focus_id = aluno_id
                break
        if current_focus_id is not None:
            try:
                index = self.alunos_ids.index(current_focus_id)
                if index < len(self.alunos_ids) - 1:
                    proximo_id = self.alunos_ids[index + 1]
                    proxima_entrada = self.entradas_notas[proximo_id]
                    proxima_entrada.focus_set()
                    proxima_entrada.select_range(0, tk.END)
                    self.selecionar_item_por_id(proximo_id)
                    t = getattr(self, 'tabela', None)
                    if t and t.selection():
                        t.see(t.selection()[0])
                else:
                    primeiro_id = self.alunos_ids[0]
                    self.entradas_notas[primeiro_id].focus_set()
                    self.entradas_notas[primeiro_id].select_range(0, tk.END)
                    self.selecionar_item_por_id(primeiro_id)
                    t = getattr(self, 'tabela', None)
                    if t and t.selection():
                        t.see(t.selection()[0])
            except (ValueError, IndexError):
                pass

        return "break"
    
    def navegar_para_entrada_anterior(self, event):
        """Move o foco para a entrada de nota anterior após pressionar Shift+Tab"""
        # Suporte para editor único
        if getattr(self, '_usar_editor_unico', False):
            current = self._editor_aluno_id
            if current is None:
                return "break"
            try:
                idx = self.alunos_ids.index(current)
            except ValueError:
                return "break"
            prev_idx = (idx - 1) % len(self.alunos_ids)
            prev_id = self.alunos_ids[prev_idx]
            self._fechar_editor(commit=True, mover_proximo=False)
            self.abrir_editor_para_aluno(prev_id)
            return "break"

        current_focus_id = None
        for aluno_id, entrada in self.entradas_notas.items():
            if entrada == self.janela.focus_get():
                current_focus_id = aluno_id
                break

        if current_focus_id is not None:
            try:
                index = self.alunos_ids.index(current_focus_id)
                if index > 0:
                    anterior_id = self.alunos_ids[index - 1]
                    anterior_entrada = self.entradas_notas[anterior_id]
                    anterior_entrada.focus_set()
                    anterior_entrada.select_range(0, tk.END)
                    self.selecionar_item_por_id(anterior_id)
                    t = getattr(self, 'tabela', None)
                    if t and t.selection():
                        t.see(t.selection()[0])
                else:
                    ultimo_id = self.alunos_ids[-1]
                    self.entradas_notas[ultimo_id].focus_set()
                    self.entradas_notas[ultimo_id].select_range(0, tk.END)
                    self.selecionar_item_por_id(ultimo_id)
                    t = getattr(self, 'tabela', None)
                    if t and t.selection():
                        t.see(t.selection()[0])
            except (ValueError, IndexError):
                pass

        return "break"
    
    def focar_entrada_selecionada(self, event):
        """Quando um item da tabela é selecionado, coloca o foco na entrada de nota correspondente"""
        t = getattr(self, 'tabela', None)
        selection = t.selection() if t else ()
        if selection:
            item = selection[0]
            valores = t.item(item, "values") if t else None
            if valores:
                num_sequencial = int(valores[0])
                aluno_id = self.num_para_id.get(num_sequencial)
                # Ao usar editor único, abrir diretamente o editor para esse aluno
                if getattr(self, '_usar_editor_unico', False):
                    # abrir editor posicionado para o aluno selecionado
                    self.abrir_editor_para_aluno(aluno_id)
                    return

        # Não faz mais nada; focar é tratado pela abertura do editor

    def _get_item_id_by_aluno(self, aluno_id):
        """Retorna o item_id do Treeview correspondente ao aluno_id ou None."""
        if aluno_id is None:
            return None

        # Usar mapeamento direto se disponível
        try:
            num = self.id_para_num.get(aluno_id)
        except Exception:
            num = None

        if num is not None:
            t = getattr(self, 'tabela', None)
            if t is None:
                return None
            for item_id in t.get_children():
                vals = t.item(item_id, "values")
                if vals and str(vals[0]) == str(num):
                    return item_id

        # Fallback: tentar comparar via num_para_id
        try:
            t = getattr(self, 'tabela', None)
            if t is None:
                return None
            for item_id in t.get_children():
                vals = t.item(item_id, "values")
                if vals:
                    try:
                        num_seq = int(vals[0])
                    except Exception:
                        continue
                    if self.num_para_id.get(num_seq) == aluno_id:
                        return item_id
        except Exception:
            pass

        return None

    def selecionar_item_por_id(self, aluno_id):
        """Seleciona no Treeview o item correspondente ao aluno_id e abre o editor (se aplicável)."""
        try:
            item_id = self._get_item_id_by_aluno(aluno_id)
            if not item_id:
                return

            # Selecionar o item na Treeview e trazê-lo à vista
            t = getattr(self, 'tabela', None)
            if t is None:
                return
            try:
                t.selection_set(item_id)
            except Exception:
                pass
            try:
                t.see(item_id)
            except Exception:
                pass

            # Se estamos usando editor único, abrir o editor para esse aluno
            if getattr(self, '_usar_editor_unico', False):
                try:
                    # Determinar aluno_id a partir do mapping caso tenha sido passado num
                    self.abrir_editor_para_aluno(aluno_id)
                except Exception:
                    pass
        except Exception:
            pass
        # fim selecionar_item_por_id

    def abrir_editor_para_aluno(self, aluno_id):
        """Abre o editor único posicionado sobre a célula 'nota' do aluno especificado."""
        if not getattr(self, '_usar_editor_unico', False):
            return

        item_id = self._get_item_id_by_aluno(aluno_id)
        if not item_id:
            return

        # Garantir que a tabela exista e o item esteja visível
        t = getattr(self, 'tabela', None)
        if t is None:
            return
        try:
            t.see(item_id)

            # Obter bbox da célula de nota
            bbox = t.bbox(item_id, 'nota')
            if not bbox:
                # Pode não estar visível imediatamente; tentar forçar redraw e tentar novamente
                t.update_idletasks()
                bbox = t.bbox(item_id, 'nota')
                if not bbox:
                    return

            x, y, width, height = bbox
            # Posicionar editor dentro do treeview
            e = getattr(self, '_editor_unico', None)
            if e is None:
                return
            e.place(in_=t, x=x+5, y=y+2, width=width-10, height=height-4)
        except Exception:
            return

        # Carregar valor atual
        valor = self.notas_dict.get(aluno_id, "")
        e = getattr(self, '_editor_unico', None)
        if e is None:
            return
        e.delete(0, tk.END)
        if valor is not None:
            e.insert(0, str(valor))

        self._editor_aluno_id = aluno_id
        e.focus_set()
        try:
            e.select_range(0, tk.END)
        except Exception:
            pass

    def _fechar_editor(self, commit=True, mover_proximo=False):
        """Fecha o editor único, opcionalmente gravando o valor e movendo para o próximo aluno."""
        if not getattr(self, '_usar_editor_unico', False):
            return

        # Se não houver editor ativo, tentar esconder e sair
        if self._editor_aluno_id is None:
            try:
                e = getattr(self, '_editor_unico', None)
                if e is not None:
                    e.place_forget()
            except Exception:
                pass
            return

        # Garantir que o editor exista
        e = getattr(self, '_editor_unico', None)
        if e is None:
            return

        valor = e.get().strip()
        aluno_id = self._editor_aluno_id

        if commit:
            # Normalizar/validar usando parse_nota; armazenar string normalizada ou vazio
            parsed = self.parse_nota(valor)
            if parsed is not None:
                self.notas_dict[aluno_id] = str(parsed)
                # Atualizar célula na treeview
                item_id = self._get_item_id_by_aluno(aluno_id)
                if item_id:
                    t = getattr(self, 'tabela', None)
                    if t:
                        t.set(item_id, 'nota', str(parsed))
                        # Se estava marcado como inválido, remover a marcação
                        try:
                            if aluno_id in getattr(self, 'invalid_notas', set()):
                                self.invalid_notas.discard(aluno_id)
                            tags = list(t.item(item_id, 'tags') or [])
                            if 'nota_invalida' in tags:
                                try:
                                    tags.remove('nota_invalida')
                                except Exception:
                                    pass
                                t.item(item_id, tags=tuple(tags))
                        except Exception:
                            pass
            else:
                # Se inválido, manter como texto bruto (ou limpar)
                if valor == "":
                    self.notas_dict[aluno_id] = ""
                    item_id = self._get_item_id_by_aluno(aluno_id)
                    if item_id:
                        t = getattr(self, 'tabela', None)
                        if t:
                            t.set(item_id, 'nota', "")
                            # remover marcação caso exista
                            try:
                                if aluno_id in getattr(self, 'invalid_notas', set()):
                                    self.invalid_notas.discard(aluno_id)
                                tags = list(t.item(item_id, 'tags') or [])
                                if 'nota_invalida' in tags:
                                    try:
                                        tags.remove('nota_invalida')
                                    except Exception:
                                        pass
                                    t.item(item_id, tags=tuple(tags))
                            except Exception:
                                pass
                else:
                    # manter valor bruto para que usuário corrija
                    self.notas_dict[aluno_id] = valor
                    item_id = self._get_item_id_by_aluno(aluno_id)
                    if item_id:
                        t = getattr(self, 'tabela', None)
                        if t:
                            t.set(item_id, 'nota', valor)
                            # marcar como inválido para destaque visual
                            try:
                                self.invalid_notas.add(aluno_id)
                                tags = list(t.item(item_id, 'tags') or [])
                                if 'nota_invalida' not in tags:
                                    tags.append('nota_invalida')
                                    t.item(item_id, tags=tuple(tags))
                            except Exception:
                                pass

        # Esconder editor
        try:
            e.place_forget()
        except Exception:
            pass

        self._editor_aluno_id = None

        # Atualizar estatísticas
        try:
            self.atualizar_estatisticas()
        except Exception:
            pass

        # Mover para próximo se solicitado
        if mover_proximo and getattr(self, 'alunos_ids', None):
            try:
                idx = self.alunos_ids.index(aluno_id)
                next_idx = (idx + 1) % len(self.alunos_ids)
                next_id = self.alunos_ids[next_idx]
                # abrir próximo editor após breve atraso para permitir o place_forget completar
                self.janela.after(50, lambda: self.abrir_editor_para_aluno(next_id))
            except Exception:
                pass

    def _on_treeview_double_click(self, event):
        """Handler para duplo clique no Treeview. Abre editor se clicou na coluna de nota."""
        t = getattr(self, 'tabela', None)
        if t is None:
            return
        region = t.identify_region(event.x, event.y)
        if region != 'cell':
            return
        col = t.identify_column(event.x)
        row = t.identify_row(event.y)
        # coluna '#3' corresponde a terceira coluna -> 'nota'
        if col == '#3' and row:
            valores = t.item(row, 'values')
            if valores:
                num = int(valores[0])
                aluno_id = self.num_para_id.get(num)
                if aluno_id:
                    self.abrir_editor_para_aluno(aluno_id)

    def _on_treeview_return(self):
        """Abrir editor na linha selecionada quando Return pressionado sobre a tabela."""
        t = getattr(self, 'tabela', None)
        sel = t.selection() if t else ()
        if not sel:
            return
        item = sel[0]
        vals = t.item(item, 'values') if t else None
        if not vals:
            return
        num = int(vals[0])
        aluno_id = self.num_para_id.get(num)
        if aluno_id:
            self.abrir_editor_para_aluno(aluno_id)

    def _on_treeview_select(self):
        # Comportamento simples: focar entrada selecionada via método existente
        try:
            self.focar_entrada_selecionada(None)
        except Exception:
            pass

    def _on_key_down(self, event):
        """Handler para tecla Down: move seleção para a próxima linha e abre o editor."""
        try:
            t = getattr(self, 'tabela', None)
            if t is None:
                return "break"

            children = list(t.get_children())
            if not children:
                return "break"

            sel = t.selection()
            if not sel:
                target = children[0]
            else:
                try:
                    idx = children.index(sel[0])
                    next_idx = min(len(children) - 1, idx + 1)
                    target = children[next_idx]
                except ValueError:
                    target = children[0]

            # Selecionar e mostrar
            try:
                t.selection_set(target)
            except Exception:
                pass
            try:
                t.see(target)
            except Exception:
                pass

            # Abrir editor para a linha selecionada
            vals = t.item(target, 'values')
            if vals:
                try:
                    num = int(vals[0])
                    aluno_id = self.num_para_id.get(num)
                    if aluno_id:
                        self.abrir_editor_para_aluno(aluno_id)
                except Exception:
                    pass
        except Exception:
            pass
        return "break"

    def _on_key_up(self, event):
        """Handler para tecla Up: move seleção para a linha anterior e abre o editor."""
        try:
            t = getattr(self, 'tabela', None)
            if t is None:
                return "break"

            children = list(t.get_children())
            if not children:
                return "break"

            sel = t.selection()
            if not sel:
                target = children[-1]
            else:
                try:
                    idx = children.index(sel[0])
                    prev_idx = max(0, idx - 1)
                    target = children[prev_idx]
                except ValueError:
                    target = children[-1]

            # Selecionar e mostrar
            try:
                t.selection_set(target)
            except Exception:
                pass
            try:
                t.see(target)
            except Exception:
                pass

            # Abrir editor para a linha selecionada
            vals = t.item(target, 'values')
            if vals:
                try:
                    num = int(vals[0])
                    aluno_id = self.num_para_id.get(num)
                    if aluno_id:
                        self.abrir_editor_para_aluno(aluno_id)
                except Exception:
                    pass
        except Exception:
            pass
        return "break"
    
    def ajustar_entradas(self, event=None):
        # Reposicionar todas as entradas conforme a tabela é rolada
        try:
            # Cancela ajuste anterior agendado para evitar múltiplas chamadas
            if self._ajuste_agendado:
                self.janela.after_cancel(self._ajuste_agendado)
                self._ajuste_agendado = None
            
            # Agenda ajuste para dar tempo da geometria atualizar
            # Se estamos usando editor único, nada a ajustar (editor será reposicionado quando necessário)
            if getattr(self, '_usar_editor_unico', False):
                return

            self._ajuste_agendado = self.janela.after(10, self._realizar_ajuste_entradas)
        except Exception as e:
            logger.error(f"Erro ao agendar ajuste: {e}")
    
    def _realizar_ajuste_entradas(self):
        # Realiza o ajuste efetivo das entradas
        try:
            self._ajuste_agendado = None
            
            # Verificar se os dicionários necessários existem
            # Quando usando editor único, nada a ajustar aqui
            if getattr(self, '_usar_editor_unico', False):
                return

            if not hasattr(self, 'entradas_notas') or not self.entradas_notas:
                return

            if not hasattr(self, 'id_para_num') or not self.id_para_num:
                return
            
            # Força atualização da geometria da tabela antes de pegar bbox
            t = getattr(self, 'tabela', None)
            if t is None:
                return
            # Força atualização da geometria da tabela antes de pegar bbox
            t.update_idletasks()

            for aluno_id, entrada in self.entradas_notas.items():
                try:
                    # Verificar se a entrada ainda existe
                    if not entrada.winfo_exists():
                        continue
                        
                    # Identificar o número sequencial para este aluno_id
                    num_sequencial = self.id_para_num.get(aluno_id)
                    if not num_sequencial:
                        continue
                        
                    # Encontrar o item da tabela para este número sequencial
                    for item_id in t.get_children():
                        valores = t.item(item_id, "values")
                        if valores and str(valores[0]) == str(num_sequencial):
                            bbox = t.bbox(item_id, "nota")
                            if bbox:  # Verificar se o item está visível
                                x, y, width, height = bbox
                                # Configurar tamanho visível da entrada
                                entrada.place(x=x+5, y=y+2, width=width-10, height=height-4)
                                entrada.lift()  # Garantir que a entrada esteja acima de outros widgets
                            else:
                                entrada.place_forget()  # Esconder entradas de itens não visíveis
                            break
                except Exception as e:
                    logger.error(f"Erro ao ajustar entrada para aluno ID {aluno_id}: {e}")
            
            # Forçar a atualização da interface
            self.janela.update_idletasks()
        except Exception as e:
            logger.error(f"Erro geral ao ajustar entradas: {e}")
    
    def buscar_nota_existente(self, aluno_id, disciplina_id, bimestre):
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if conn is None:
                logger.error("Erro de conexão ao buscar nota: conectar_bd() retornou None")
                return None
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nota 
                FROM notas 
                WHERE aluno_id = %s AND disciplina_id = %s AND bimestre = %s AND ano_letivo_id = %s
            """, self._norm_params((aluno_id, disciplina_id, bimestre, self.ano_letivo_atual)))
            resultado = cursor.fetchone()

            if resultado:
                return resultado[0]
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar nota: {e}")
            return None
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def parse_nota(self, texto):
        """
        Converte e valida uma string de nota para float.

        Retorna None quando a entrada for vazia ou inválida.
        Aceita vírgula como separador decimal.
        Valida intervalo entre 0 e 100 (ajustar se necessário).
        """
        if texto is None:
            return None
        s = str(texto).strip()
        if s == "":
            return None
        s = s.replace(',', '.')
        try:
            v = float(s)
        except (ValueError, TypeError):
            return None
        if v < 0 or v > 100:
            return None
        return v

    def _normalize_param(self, val):
        """Normaliza um único parâmetro antes de passá-lo a cursor.execute.

        - Converte sets/tuplas/listas em strings separadas por vírgula (para evitar
          passar coleções diretamente ao driver).
        - Converte booleanos para int.
        - Mantém int/float/Decimal/str/bytes como estão.
        - Converte NaN para None.
        - Valores desconhecidos são convertidos para str().
        """
        try:
            # Evitar passar coleções diretamente (p.ex. set)
            if isinstance(val, (set, list, tuple)):
                try:
                    return ','.join(str(x) for x in val)
                except Exception:
                    return str(val)

            # Booleanos para int (opcional)
            if isinstance(val, bool):
                return int(val)

            # Tipos primitivos aceitos pelo driver
            from decimal import Decimal
            if isinstance(val, (int, float, Decimal, str, bytes)):
                # Tratar NaN
                try:
                    import math
                    if isinstance(val, float) and math.isnan(val):
                        return None
                except Exception:
                    pass
                return val

            # Tratar pandas/Numpy NaN-like
            try:
                import math
                if hasattr(val, 'item'):
                    v = val.item()
                    if isinstance(v, float) and math.isnan(v):
                        return None
                    return v
            except Exception:
                pass

            # Fallback: converter para string
            return str(val)
        except Exception:
            return str(val)

    def _norm_params(self, params):
        """Normaliza uma sequência/tupla de parâmetros para passar ao cursor.

        Retorna uma tuple com parâmetros transformados por `_normalize_param`.
        """
        if params is None:
            return None
        try:
            return tuple(self._normalize_param(p) for p in params)
        except Exception:
            # Em caso de erro, tentar forçar a conversão simples
            try:
                return tuple(str(p) for p in params)
            except Exception:
                return params
    
    def atualizar_estatisticas(self, event=None):
        # Coletar notas válidas
        notas = []
        
        # Se usando editor único, iterar sobre notas_dict
        if getattr(self, '_usar_editor_unico', False):
            for aluno_id in self.alunos_ids:
                nota_texto = self.notas_dict.get(aluno_id, "")
                if nota_texto is None:
                    continue
                try:
                    nota_val = self.parse_nota(nota_texto)
                    if nota_val is not None:
                        notas.append(nota_val)
                except Exception:
                    pass
        else:
            for entrada in self.entradas_notas.values():
                try:
                    nota_texto = entrada.get().strip()
                    if nota_texto:
                        nota_val = self.parse_nota(nota_texto)
                        if nota_val is not None:
                            notas.append(nota_val)
                except Exception:
                    pass
        
        # Atualizar estatísticas
        if notas:
            media = sum(notas) / len(notas)
            maior = max(notas)
            menor = min(notas)
            
            abaixo_media = sum(1 for nota in notas if nota < 60.0)
            acima_media = sum(1 for nota in notas if nota >= 60.0)
            
            # Atualizar os labels
            self.lbl_media_turma.config(text=f"{media:.1f}")
            self.lbl_maior_nota.config(text=f"{maior:.1f}")
            self.lbl_menor_nota.config(text=f"{menor:.1f}")
            self.lbl_abaixo_media.config(text=str(abaixo_media))
            self.lbl_acima_media.config(text=str(acima_media))
            self.lbl_total_alunos.config(text=str(len(self.alunos)))
            
            # Definir cores para média da turma
            if media < 60.0:
                self.lbl_media_turma.config(fg="red")
            else:
                self.lbl_media_turma.config(fg="green")
        else:
            # Reiniciar labels se não houver notas
            self.lbl_media_turma.config(text="--", fg="black")
            self.lbl_maior_nota.config(text="--")
            self.lbl_menor_nota.config(text="--")
            self.lbl_abaixo_media.config(text="--")
            self.lbl_acima_media.config(text="--")
            self.lbl_total_alunos.config(text=str(len(self.alunos)))
    
    def salvar_notas(self):
        # Verificar permissão para salvar notas (se perfis habilitados)
        if perfis_habilitados():
            perfil = UsuarioLogado.get_perfil()
            if perfil == 'coordenador':
                # Coordenador pode visualizar mas não editar notas
                messagebox.showwarning(
                    "Sem Permissão",
                    "Coordenadores podem visualizar notas, mas não têm permissão para editá-las.\n"
                    "Apenas professores podem lançar notas em suas próprias turmas."
                )
                return
            elif perfil == 'professor':
                # Verificar se a turma atual pertence ao professor
                turma_id = self.turmas_map.get(self.cb_turma.get()) if self.cb_turma.get() else None
                if turma_id and not PerfilFilterService.pode_acessar_turma(turma_id):
                    messagebox.showerror(
                        "Sem Permissão",
                        "Você não tem permissão para lançar notas nesta turma."
                    )
                    return
        
        # IMPORTANTE: Forçar o fechamento do editor antes de salvar
        # Isso garante que a nota sendo editada seja salva no notas_dict
        if getattr(self, '_usar_editor_unico', False) and getattr(self, '_editor_aluno_id', None) is not None:
            try:
                self._fechar_editor(commit=True, mover_proximo=False)
                # Pequeno delay para garantir que o editor foi fechado
                self.janela.update_idletasks()
            except Exception as e:
                logger.error(f"Erro ao fechar editor antes de salvar: {e}")
        
        # Log de depuração
        logger.info("=== INICIANDO SALVAMENTO DE NOTAS ===")
        logger.info(f"Disciplina ID: {getattr(self, 'disciplina_id', None)}")
        logger.info(f"Bimestre: {getattr(self, 'bimestre', None)}")
        logger.info(f"Ano Letivo: {getattr(self, 'ano_letivo_atual', None)}")
        logger.info(f"Usar editor único: {getattr(self, '_usar_editor_unico', False)}")
        logger.info(f"Notas dict: {getattr(self, 'notas_dict', {})}")
        logger.info(f"Alunos IDs: {getattr(self, 'alunos_ids', [])}")
        
        # Suporta tanto o modo legacy (entradas por linha) quanto o editor único
        has_entries = hasattr(self, 'entradas_notas') and bool(getattr(self, 'entradas_notas', {}))
        has_notas_dict = getattr(self, '_usar_editor_unico', False) and hasattr(self, 'notas_dict') and bool(getattr(self, 'notas_dict', {}))
        
        logger.info(f"Has entries: {has_entries}, Has notas_dict: {has_notas_dict}")
        
        if not (has_entries or has_notas_dict):
            messagebox.showinfo("Aviso", "Não há notas para salvar.")
            return

        # Bloquear salvamento se houver notas marcadas como inválidas
        try:
            invalids = getattr(self, 'invalid_notas', set())
            if invalids:
                # Construir uma listagem breve para o usuário (número sequencial ou nome)
                lista_amostra = []
                for aid in list(invalids)[:10]:
                    num = self.id_para_num.get(aid)
                    nome = None
                    try:
                        nome = next((a[1] for a in getattr(self, 'alunos', []) if a[0] == aid), None)
                    except Exception:
                        nome = None
                    if nome:
                        lista_amostra.append(f"{num} - {nome}" if num else nome)
                    else:
                        lista_amostra.append(str(num) if num else str(aid))

                amostra_txt = ", ".join(lista_amostra)
                messagebox.showwarning("Notas Inválidas", f"Existem {len(invalids)} notas inválidas. Corrija-as antes de salvar.\n\nExemplos: {amostra_txt}")
                return
        except Exception:
            pass
        
        conn = conectar_bd()
        if conn is None:
            messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao banco de dados.")
            return

        cursor = conn.cursor()
        count_inseridas = 0
        count_atualizadas = 0
        count_removidas = 0

        try:
            # Iterar na ordem dos alunos
            for aluno_id in self.alunos_ids:
                nota_texto = str(self.notas_dict.get(aluno_id, "")).strip()

                # Verificar se já existe uma nota para este aluno, disciplina e bimestre
                cursor.execute("""
                    SELECT id FROM notas 
                    WHERE aluno_id = %s AND disciplina_id = %s AND bimestre = %s AND ano_letivo_id = %s
                """, self._norm_params((aluno_id, self.disciplina_id, self.bimestre, self.ano_letivo_atual)))

                resultado = cursor.fetchone()

                # Se a entrada estiver vazia e existir uma nota no banco, remover a nota
                if not nota_texto and resultado:
                    cursor.execute("""
                        DELETE FROM notas 
                        WHERE id = %s
                    """, self._norm_params((resultado[0],)))
                    count_removidas += 1
                    continue

                # Se a entrada estiver vazia e não existir nota, pular
                if not nota_texto:
                    continue

                # Normalizar e validar nota
                nota = self.parse_nota(nota_texto)
                if nota is None:
                    messagebox.showwarning("Aviso", f"Nota inválida para o aluno ID {aluno_id}. A nota deve ser um número entre 0 e 100.")
                    continue

                # Se a nota era marcada como inválida, remover a marcação agora que está válida
                try:
                    if aluno_id in getattr(self, 'invalid_notas', set()):
                        self.invalid_notas.discard(aluno_id)
                    t = getattr(self, 'tabela', None)
                    item_id = self._get_item_id_by_aluno(aluno_id)
                    if t and item_id:
                        tags = list(t.item(item_id, 'tags') or [])
                        if 'nota_invalida' in tags:
                            try:
                                tags.remove('nota_invalida')
                            except Exception:
                                pass
                            t.item(item_id, tags=tuple(tags))
                except Exception:
                    pass
                if resultado:
                    # Atualizar a nota existente
                    cursor.execute("""
                        UPDATE notas 
                        SET nota = %s 
                        WHERE id = %s
                    """, self._norm_params((nota, resultado[0])))
                    count_atualizadas += 1
                else:
                    # Inserir nova nota
                    cursor.execute("""
                        INSERT INTO notas (aluno_id, disciplina_id, bimestre, nota, ano_letivo_id) 
                        VALUES (%s, %s, %s, %s, %s)
                    """, self._norm_params((aluno_id, self.disciplina_id, self.bimestre, nota, self.ano_letivo_atual)))
                    count_inseridas += 1

            conn.commit()
            messagebox.showinfo("Sucesso", f"Notas salvas com sucesso!\n\nNovas notas: {count_inseridas}\nNotas atualizadas: {count_atualizadas}\nNotas removidas: {count_removidas}")
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            messagebox.showerror("Erro", f"Erro ao salvar notas: {e}")
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
    
    def limpar_campos(self):
        # Limpar todas as entradas de notas
        if getattr(self, '_usar_editor_unico', False):
            # Limpar dicionário de notas e atualizar a tabela
            for aluno_id in list(self.notas_dict.keys()):
                self.notas_dict[aluno_id] = ""
                # Atualizar célula na treeview
                # Encontrar item correspondente
                num = self.id_para_num.get(aluno_id)
                if num:
                    t = getattr(self, 'tabela', None)
                    if t:
                        for item_id in t.get_children():
                            vals = t.item(item_id, "values")
                            if vals and str(vals[0]) == str(num):
                                t.set(item_id, 'nota', "")
                                break
        elif hasattr(self, 'entradas_notas'):
            for entrada in self.entradas_notas.values():
                entrada.delete(0, tk.END)

        # Atualizar estatísticas
        self.atualizar_estatisticas()
        # Limpar marcações de notas inválidas
        try:
            if hasattr(self, 'invalid_notas'):
                self.invalid_notas.clear()
            t = getattr(self, 'tabela', None)
            if t:
                for item_id in t.get_children():
                    tags = list(t.item(item_id, 'tags') or [])
                    if 'nota_invalida' in tags:
                        try:
                            tags.remove('nota_invalida')
                        except Exception:
                            pass
                        t.item(item_id, tags=tuple(tags))
        except Exception:
            pass
    
    def exportar_para_excel(self):
        # Se não houver alunos/carregamento
        if not hasattr(self, 'alunos') or not self.alunos:
            messagebox.showinfo("Aviso", "Não há notas para exportar.")
            return
        
        try:
            # Coletar dados para exportação
            dados_notas = []
            
            for aluno in self.alunos:
                aluno_id = aluno[0]
                if getattr(self, '_usar_editor_unico', False):
                    nota_texto = str(self.notas_dict.get(aluno_id, "")).strip()
                else:
                    nota_texto = self.entradas_notas[aluno_id].get().strip()
                nota = nota_texto if nota_texto else ""
                
                dados_notas.append({
                    'ID': aluno_id,
                    'Nome do Aluno': aluno[1],
                    'Nota': nota
                })
            
            # Criar DataFrame
            df = pd.DataFrame(dados_notas)
            
            # Solicitar local para salvar
            data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"Notas_{self.cb_turma.get().replace(' ', '_')}_{self.cb_disciplina.get().replace(' ', '_')}_{self.bimestre.replace(' ', '_')}_{data_atual}.xlsx"
            
            caminho_arquivo = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=nome_arquivo
            )
            
            if not caminho_arquivo:
                return  # Usuário cancelou
            
            # Exportar para Excel
            df.to_excel(caminho_arquivo, index=False)
            
            # Perguntar se deseja abrir o arquivo
            if messagebox.askyesno("Sucesso", f"Arquivo exportado com sucesso!\n\nDeseja abrir o arquivo agora?"):
                os.startfile(caminho_arquivo) if os.name == 'nt' else os.system(f"xdg-open {caminho_arquivo}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar notas: {e}")

    def importar_do_excel(self):
        # Permite importação tanto em modo legacy quanto com editor único
        has_entries = hasattr(self, 'entradas_notas') and bool(getattr(self, 'entradas_notas', {}))
        has_notas_dict = getattr(self, '_usar_editor_unico', False) and hasattr(self, 'notas_dict')
        if not (has_entries or has_notas_dict):
            messagebox.showinfo("Aviso", "Selecione uma turma e disciplina primeiro para poder importar notas.")
            return
        
        try:
            # Solicitar o arquivo Excel
            caminho_arquivo = filedialog.askopenfilename(
                filetypes=[("Arquivos Excel", "*.xlsx;*.xls")],
                title="Selecione o arquivo Excel com as notas"
            )
            
            if not caminho_arquivo:
                return  # Usuário cancelou
            
            # Ler o arquivo Excel
            df = pd.read_excel(caminho_arquivo)
            
            # Verificar se o formato é válido
            colunas_necessarias = ["ID", "Nome do Aluno", "Nota"]
            colunas_faltantes = [col for col in colunas_necessarias if col not in df.columns]
            
            if colunas_faltantes:
                messagebox.showerror("Erro de Formato", 
                                    f"O arquivo Excel não contém todas as colunas necessárias.\n"
                                    f"Colunas faltantes: {', '.join(colunas_faltantes)}\n\n"
                                    f"O arquivo deve conter as colunas: {', '.join(colunas_necessarias)}")
                return
            
            # Dicionário para mapear ID do aluno para o objeto de entrada
            alunos_encontrados = 0
            notas_atualizadas = 0
            
            # Processar cada linha do Excel
            for _, row in df.iterrows():
                aluno_id = int(row["ID"])
                nota_texto = row["Nota"]

                # Verificar se o aluno existe nas entradas
                if getattr(self, '_usar_editor_unico', False):
                    # Estamos usando notas_dict
                    if aluno_id in self.notas_dict:
                        alunos_encontrados += 1
                        nota_parsed = self.parse_nota(nota_texto)
                        if nota_parsed is not None:
                            self.notas_dict[aluno_id] = str(nota_parsed)
                            # Atualizar célula na treeview
                            num = self.id_para_num.get(aluno_id)
                            if num:
                                t = getattr(self, 'tabela', None)
                                if t:
                                    for item_id in t.get_children():
                                        vals = t.item(item_id, "values")
                                        if vals and str(vals[0]) == str(num):
                                            t.set(item_id, 'nota', str(nota_parsed))
                                            break
                            notas_atualizadas += 1
                        else:
                            if str(nota_texto).strip() and str(nota_texto).strip().lower() != 'nan':
                                # Marcar como inválido para correção manual
                                try:
                                    self.invalid_notas.add(aluno_id)
                                    num = self.id_para_num.get(aluno_id)
                                    t = getattr(self, 'tabela', None)
                                    if t and num:
                                        for item_id in t.get_children():
                                            vals = t.item(item_id, "values")
                                            if vals and str(vals[0]) == str(num):
                                                tags = list(t.item(item_id, 'tags') or [])
                                                if 'nota_invalida' not in tags:
                                                    tags.append('nota_invalida')
                                                    t.item(item_id, tags=tuple(tags))
                                                break
                                except Exception:
                                    logger.info(f"Valor de nota inválido para aluno ID {aluno_id}: {nota_texto}")
                else:
                    if aluno_id in self.entradas_notas:
                        alunos_encontrados += 1
                        nota_parsed = self.parse_nota(nota_texto)
                        if nota_parsed is not None:
                            self.entradas_notas[aluno_id].delete(0, tk.END)
                            self.entradas_notas[aluno_id].insert(0, str(nota_parsed))
                            notas_atualizadas += 1
                        else:
                            if str(nota_texto).strip() and str(nota_texto).strip().lower() != 'nan':
                                # Marcar como inválido na tabela legacy
                                try:
                                    self.invalid_notas.add(aluno_id)
                                    t = getattr(self, 'tabela', None)
                                    num = self.id_para_num.get(aluno_id)
                                    if t and num:
                                        for item_id in t.get_children():
                                            vals = t.item(item_id, "values")
                                            if vals and str(vals[0]) == str(num):
                                                tags = list(t.item(item_id, 'tags') or [])
                                                if 'nota_invalida' not in tags:
                                                    tags.append('nota_invalida')
                                                    t.item(item_id, tags=tuple(tags))
                                                break
                                except Exception:
                                    logger.info(f"Valor de nota inválido para aluno ID {aluno_id}: {nota_texto}")
            
            # Atualizar estatísticas
            self.atualizar_estatisticas()
            
            # Mostrar resumo da importação
            messagebox.showinfo("Importação Concluída", 
                               f"Importação concluída com sucesso!\n\n"
                               f"Alunos encontrados: {alunos_encontrados}\n"
                               f"Notas atualizadas: {notas_atualizadas}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao importar arquivo Excel: {e}")
            import traceback
            traceback.print_exc()
            
    def exportar_template_excel(self):
        """Exporta um template Excel para preenchimento de notas"""
        if not hasattr(self, 'alunos') or not self.alunos:
            messagebox.showinfo("Aviso", "Selecione uma turma primeiro para exportar o template.")
            return
        
        try:
            # Criar DataFrame com informações dos alunos
            dados = []
            for aluno in self.alunos:
                dados.append({
                    'ID': aluno[0],
                    'Nome do Aluno': aluno[1],
                    'Nota': ''  # Célula vazia para preenchimento
                })
            
            df = pd.DataFrame(dados)
            
            # Solicitar local para salvar
            turma = self.cb_turma.get().replace(' ', '_') if hasattr(self, 'cb_turma') else "turma"
            disciplina = self.cb_disciplina.get().replace(' ', '_') if hasattr(self, 'cb_disciplina') else "disciplina"
            bimestre = self.bimestre.replace(' ', '_') if hasattr(self, 'bimestre') else "bimestre"
            
            nome_arquivo = f"Template_Notas_{turma}_{disciplina}_{bimestre}.xlsx"
            
            caminho_arquivo = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=nome_arquivo
            )
            
            if not caminho_arquivo:
                return  # Usuário cancelou
            
            # Exportar para Excel
            df.to_excel(caminho_arquivo, index=False)
            
            messagebox.showinfo("Sucesso", f"Template exportado com sucesso:\n{caminho_arquivo}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar template: {e}")
            
    def atualizar_interface(self):
        """Atualiza a interface após mudanças na seleção"""
        self.criar_estatisticas()
        self.atualizar_estatisticas()

    def abrir_preenchimento_automatico(self):
        """Abre o assistente de preenchimento automático do GEDUC"""
        try:
            # Importar o integrador (apenas quando necessário)
            from integrador_preenchimento import adicionar_preenchimento_automatico_na_interface
            
            # Verificar se já tem um integrador ativo
            if not hasattr(self, 'integrador_preenchimento'):
                # Criar integrador
                self.integrador_preenchimento = adicionar_preenchimento_automatico_na_interface(self)
            
            # Iniciar preenchimento
            self.integrador_preenchimento.iniciar_preenchimento_automatico()
            
        except ImportError as e:
            messagebox.showerror(
                "Erro", 
                f"Módulo de preenchimento automático não encontrado!\n\n"
                f"Certifique-se de que os arquivos estão presentes:\n"
                f"- preencher_notas_automatico.py\n"
                f"- integrador_preenchimento.py\n\n"
                f"Erro: {str(e)}"
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar preenchimento automático:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def extrair_todas_disciplinas_geduc(self):
        """
        Extrai TODAS as disciplinas de uma turma do GEDUC e salva direto no banco
        Retorna relatório de alunos não encontrados
        """
        try:
            import threading
            from automatizar_extracao_geduc import AutomacaoGEDUC
            import unicodedata
            
            # Validar seleções
            if not self.cb_serie.get():
                messagebox.showerror("Erro", "Selecione uma série!")
                return
            
            if not self.cb_turma.get():
                messagebox.showerror("Erro", "Selecione uma turma!")
                return
            
            if not self.cb_bimestre.get():
                messagebox.showerror("Erro", "Selecione um bimestre!")
                return
            
            # Preparar dados
            serie_nome = self.cb_serie.get()
            turma_completa = self.cb_turma.get()
            bimestre_texto = self.cb_bimestre.get()
            bimestre_num = int(bimestre_texto.split('º')[0].strip())
            
            # Extrair turma e turno
            # Formato esperado: "XXX - TURNO" ou apenas "XXX" ou " - TURNO" (quando só tem turno)
            if ' - ' in turma_completa:
                partes = turma_completa.split(' - ')
                turma_nome = partes[0].strip() if partes[0].strip() else ""
                turma_turno = partes[1].strip() if len(partes) > 1 else ""
            else:
                turma_nome = turma_completa.strip()
                turma_turno = ""
            
            # Construir nome para busca no GEDUC
            # GEDUC usa formatos: "2º ANO-MATU", "6º ANO-VESP - A"
            # Precisamos construir: SÉRIE + TURNO (com possíveis variações)
            
            # Se turma_nome está vazio, significa que só temos turno
            if not turma_nome:
                # Formato: "SÉRIE TURNO" (ex: "2º Ano MAT")
                nome_busca_geduc = f"{serie_nome} {turma_turno}" if turma_turno else serie_nome
            else:
                # Tem letra de turma: "SÉRIE TURNO LETRA" (ex: "6º Ano VESP A")
                if turma_turno:
                    nome_busca_geduc = f"{serie_nome} {turma_turno} {turma_nome}"
                else:
                    nome_busca_geduc = f"{serie_nome} {turma_nome}"
            
            # Solicitar credenciais
            credenciais = self._solicitar_credenciais_geduc()
            if not credenciais:
                return
            
            # Confirmar
            msg = (
                f"🔄 EXTRAÇÃO COMPLETA DO GEDUC\n\n"
                f"📚 Turma: {turma_completa}\n"
                f"📅 Bimestre: {bimestre_num}º\n\n"
                f"⚙️ Este processo irá:\n"
                f"1. Fazer login no GEDUC\n"
                f"2. Buscar TODAS as disciplinas da turma\n"
                f"3. Extrair notas de todos os alunos\n"
                f"4. Salvar DIRETO no banco de dados\n"
                f"5. Gerar relatório de inconsistências\n\n"
                f"⏱️ Tempo estimado: 2-5 minutos\n\n"
                f"Continuar?"
            )
            
            if not messagebox.askyesno("Confirmar Extração Completa", msg):
                return
            
            # Criar janela de progresso
            janela_progresso = self._criar_janela_progresso()
            
            # Executar em thread
            def executar():
                self._executar_extracao_completa(
                    credenciais,
                    serie_nome,
                    turma_nome,
                    turma_turno,
                    nome_busca_geduc,
                    turma_completa,
                    bimestre_num,
                    janela_progresso
                )
            
            thread = threading.Thread(target=executar, daemon=True)
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar extração:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def _solicitar_credenciais_geduc(self):
        """Abre janela para solicitar credenciais do GEDUC"""
        janela_cred = tk.Toplevel(self.janela)
        janela_cred.title("Credenciais GEDUC")
        janela_cred.geometry("400x200")
        janela_cred.resizable(False, False)
        janela_cred.grab_set()
        
        # Centralizar
        janela_cred.update_idletasks()
        x = (janela_cred.winfo_screenwidth() // 2) - (400 // 2)
        y = (janela_cred.winfo_screenheight() // 2) - (200 // 2)
        janela_cred.geometry(f'400x200+{x}+{y}')
        
        # Variáveis
        usuario_var = tk.StringVar(value=getattr(config, 'GEDUC_DEFAULT_USER', ''))
        senha_var = tk.StringVar(value=getattr(config, 'GEDUC_DEFAULT_PASS', ''))
        resultado = {}
        resultado['confirmado'] = False
        
        # Conteúdo
        tk.Label(
            janela_cred,
            text="Credenciais do GEDUC",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        tk.Label(
            janela_cred,
            text="⚠️ Você precisará resolver o reCAPTCHA no navegador",
            font=("Arial", 9, "italic"),
            fg="#E65100"
        ).pack(pady=5)
        
        # Campos
        frame_campos = tk.Frame(janela_cred)
        frame_campos.pack(pady=10, padx=20)
        
        tk.Label(frame_campos, text="Usuário:", width=10, anchor="w").grid(row=0, column=0, pady=5)
        entry_usuario = tk.Entry(frame_campos, textvariable=usuario_var, width=25)
        entry_usuario.grid(row=0, column=1, pady=5)
        
        tk.Label(frame_campos, text="Senha:", width=10, anchor="w").grid(row=1, column=0, pady=5)
        entry_senha = tk.Entry(frame_campos, textvariable=senha_var, width=25, show="*")
        entry_senha.grid(row=1, column=1, pady=5)
        
        # Botões
        frame_botoes = tk.Frame(janela_cred)
        frame_botoes.pack(pady=10)
        
        def confirmar():
            if not usuario_var.get() or not senha_var.get():
                messagebox.showerror("Erro", "Preencha usuário e senha!", parent=janela_cred)
                return
            resultado['confirmado'] = True
            resultado['usuario'] = usuario_var.get()
            resultado['senha'] = senha_var.get()
            janela_cred.destroy()
        
        def cancelar():
            resultado['confirmado'] = False
            janela_cred.destroy()
        
        tk.Button(
            frame_botoes,
            text="Confirmar",
            command=confirmar,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_botoes,
            text="Cancelar",
            command=cancelar,
            bg="#F44336",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12
        ).pack(side="left", padx=5)
        
        entry_usuario.focus()
        janela_cred.wait_window()
        
        if resultado['confirmado']:
            return {
                'usuario': resultado['usuario'],
                'senha': resultado['senha']
            }
        return None
    
    def _criar_janela_progresso(self):
        """Cria janela de progresso para extração"""
        janela = tk.Toplevel(self.janela)
        janela.title("Extraindo do GEDUC...")
        janela.geometry("600x400")
        janela.resizable(False, False)
        
        # Centralizar
        janela.update_idletasks()
        x = (janela.winfo_screenwidth() // 2) - (600 // 2)
        y = (janela.winfo_screenheight() // 2) - (400 // 2)
        janela.geometry(f'600x400+{x}+{y}')
        
        # Título
        tk.Label(
            janela,
            text="🔄 Extração em Andamento",
            font=("Arial", 14, "bold"),
            bg=self.co1,
            fg="white"
        ).pack(fill="x", pady=10)
        
        # Área de log
        frame_log = tk.Frame(janela)
        frame_log.pack(fill="both", expand=True, padx=10, pady=10)
        
        text_log = tk.Text(frame_log, height=15, font=("Consolas", 9), bg="white", fg="black")
        text_log.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(frame_log, command=text_log.yview)
        scrollbar.pack(side="right", fill="y")
        text_log.config(yscrollcommand=scrollbar.set)
        
        # Armazenar referências
        # (atributo `text_log` é criado quando necessário via `setattr` em tempo de execução)
        
        return janela
    
    def _executar_extracao_completa(self, credenciais, serie_nome, turma_nome, turma_turno, 
                                    nome_busca_geduc, turma_completa, bimestre_num, janela_progresso):
        """Executa a extração completa de todas as disciplinas"""
        from automatizar_extracao_geduc import AutomacaoGEDUC
        import unicodedata
        import time
        
        def log(msg):
            """Adiciona mensagem ao log"""
            # Sempre imprimir no console
            logger.info(msg)
            # Atualizar o widget de log somente no thread principal (thread-safe)
            try:
                self.janela.after(0, lambda m=msg: (
                    janela_progresso.text_log.insert(tk.END, m + "\n"),
                    janela_progresso.text_log.see(tk.END)
                ))
            except Exception:
                # Em caso de erro ao agendar, garantir que ao menos o print ocorreu
                pass
        
        automacao = None
        try:
            log("="*60)
            log("EXTRAÇÃO COMPLETA DO GEDUC")
            log("="*60)
            
            # Iniciar automação
            log("\n→ Iniciando navegador...")
            automacao = AutomacaoGEDUC(headless=False)
            
            if not automacao.iniciar_navegador():
                log("✗ Falha ao iniciar navegador")
                self.janela.after(0, lambda: messagebox.showerror("Erro", "Falha ao iniciar navegador!"))
                return
            
            log("✓ Navegador iniciado")
            
            # Login
            log("\n→ Fazendo login no GEDUC...")
            if not automacao.fazer_login(credenciais['usuario'], credenciais['senha'], timeout_recaptcha=120):
                log("✗ Falha no login")
                self.janela.after(0, lambda: messagebox.showerror("Erro", "Falha no login!"))
                return
            
            log("✓ Login realizado")
            
            # Acessar registro de notas
            log("\n→ Acessando registro de notas...")
            if not automacao.acessar_registro_notas():
                log("✗ Falha ao acessar página")
                return
            
            log("✓ Página de notas carregada")
            
            # Buscar turma (usando lógica do integrador_preenchimento.py)
            log(f"\n→ Procurando turma no GEDUC:")
            log(f"   Série: {serie_nome}")
            log(f"   Turno: {turma_turno}")
            log(f"   Turma: {turma_nome}")
            log(f"   Nome completo para busca: {nome_busca_geduc}")
            log(f"   Ordem: {{SÉRIE}} + {{TURNO}} + {{TURMA}}")
            
            turmas = automacao.obter_opcoes_select('IDTURMA')
            log(f"\n   Turmas disponíveis no GEDUC:")
            for t in turmas[:10]:
                log(f"     • {t['text']}")
            if len(turmas) > 10:
                log(f"     ... e mais {len(turmas) - 10} turmas")
            
            # Normalizar busca (função do integrador)
            def normalizar_para_busca(texto):
                """Remove acentos, símbolos, espaços extras e converte para maiúsculas"""
                # Remover acentuação
                texto = ''.join(c for c in unicodedata.normalize('NFD', texto) 
                               if unicodedata.category(c) != 'Mn')
                # Remover símbolos especiais
                texto = texto.replace('º', '').replace('ª', '')
                # Converter para maiúsculas e remover espaços extras
                texto = ' '.join(texto.upper().split())
                return texto
            
            # Preparar busca
            nome_completo_norm = normalizar_para_busca(nome_busca_geduc)
            log(f"\n   Valor normalizado para busca: '{nome_completo_norm}'")
            
            # Procurar turma
            turma_id = None
            turma_encontrada = None
            
            log(f"\n   Comparando com cada turma:")
            
            for turma in turmas:
                turma_text = turma['text'].strip()
                turma_text_norm = normalizar_para_busca(turma_text)
                
                # Debug: mostrar comparação
                log(f"     • '{turma_text}' → '{turma_text_norm}'")
                
                # MÉTODO 1: Comparação EXATA
                if turma_text_norm == nome_completo_norm:
                    turma_id = turma['value']
                    turma_encontrada = turma_text
                    log(f"       ✓✓ MATCH EXATO!")
                    break
                
                # MÉTODO 2: Formatos com hífen
                # GEDUC: "7 ANO-VESP", "6 ANO-VESP - A", "2 ANO-MATU"
                # Busca: "7 ANO VESP", "6 ANO VESP A", "2 ANO MAT"
                partes_busca = nome_completo_norm.split()
                
                if len(partes_busca) >= 2:
                    formatos_busca = []
                    
                    if len(partes_busca) == 3:
                        # "2 ANO MAT" → testar "2 ANO-MAT" e "2 ANO-MATU"
                        base = ' '.join(partes_busca[:-1])
                        turno = partes_busca[-1]
                        
                        # Formatos padrão
                        formatos_busca.append(f"{base}-{turno}")
                        formatos_busca.append(f"{base} - {turno}")
                        
                        # Variações do turno (MAT→MATU, VESP→VESPERTINO, etc.)
                        if turno == "MAT":
                            formatos_busca.append(f"{base}-MATU")
                            formatos_busca.append(f"{base} - MATU")
                            formatos_busca.append(f"{base}-MATUTINO")
                        elif turno == "VESP":
                            formatos_busca.append(f"{base}-VESPERTINO")
                            formatos_busca.append(f"{base} - VESPERTINO")
                        elif turno == "NOT":
                            formatos_busca.append(f"{base}-NOTURNO")
                            formatos_busca.append(f"{base} - NOTURNO")
                    
                    elif len(partes_busca) == 4:
                        # "6 ANO VESP A" → "6 ANO-VESP - A"
                        formatos_busca.append(f"{partes_busca[0]} {partes_busca[1]}-{partes_busca[2]} - {partes_busca[3]}")
                        formatos_busca.append(f"{partes_busca[0]} {partes_busca[1]}-{partes_busca[2]}-{partes_busca[3]}")
                    
                    for formato in formatos_busca:
                        if turma_text_norm == formato:
                            turma_id = turma['value']
                            turma_encontrada = turma_text
                            log(f"       ✓✓ MATCH com formato '{formato}'!")
                            break
                
                if turma_id:
                    break
                
                # MÉTODO 3: Começa com (para turmas com letras)
                if turma_text_norm.startswith(nome_completo_norm):
                    turma_id = turma['value']
                    turma_encontrada = turma_text
                    log(f"       ✓ MATCH: começa com '{nome_completo_norm}'")
                    break
                
                # MÉTODO 4: Similaridade com turnos (buscar por série + parte do turno)
                # Ex: "2 ANO MAT" deve encontrar "2 ANO-MATU"
                if len(partes_busca) >= 3:
                    serie_busca = ' '.join(partes_busca[:-1])  # "2 ANO"
                    turno_busca = partes_busca[-1]  # "MAT"
                    
                    # Verificar se a turma do GEDUC começa com a série e contém parte do turno
                    if turma_text_norm.startswith(serie_busca) and turno_busca in turma_text_norm:
                        turma_id = turma['value']
                        turma_encontrada = turma_text
                        log(f"       ✓ MATCH PARCIAL: série '{serie_busca}' + turno contém '{turno_busca}'")
                        break
            
            if not turma_id:
                log(f"\n✗ Turma não encontrada no GEDUC")
                log(f"   Nome buscado: '{nome_busca_geduc}' (normalizado: '{nome_completo_norm}')")
                log(f"   Turma completa: {turma_completa}")
                log(f"\n   💡 DICA: Compare com as turmas disponíveis acima")
                log(f"   Ordem GEDUC: {{SÉRIE}} + {{TURNO}} + {{TURMA}}")
                self.janela.after(0, lambda: messagebox.showerror(
                    "Erro", 
                    f"Turma não encontrada: {nome_busca_geduc}\n\n"
                    f"Verifique o log para comparar com as turmas do GEDUC."
                ))
                return
            
            log(f"\n✓ Turma encontrada: {turma_encontrada}")
            
            # Selecionar turma
            automacao.selecionar_opcao('IDTURMA', turma_id)
            time.sleep(1)
            
            # Obter todas as disciplinas
            log("\n→ Carregando disciplinas...")
            disciplinas = automacao.obter_opcoes_select('IDTURMASDISP')
            log(f"✓ {len(disciplinas)} disciplinas encontradas")
            
            # Buscar alunos da turma no banco local
            log("\n→ Carregando alunos do banco local...")
            alunos_local = self._buscar_alunos_turma_local(self.turma_id)
            log(f"✓ {len(alunos_local)} alunos no banco local")
            
            # Buscar nivel_id da turma para filtrar disciplinas corretamente
            log("\n→ Identificando nível de ensino da turma...")
            nivel_id_turma = self._obter_nivel_turma(self.turma_id)
            if nivel_id_turma:
                log(f"✓ Nível de ensino: ID {nivel_id_turma}")
            else:
                log(f"⚠️ Não foi possível identificar o nível de ensino")
            
            # Estatísticas
            total_notas_inseridas = 0
            total_notas_atualizadas = 0
            alunos_nao_encontrados = set()
            disciplinas_processadas = []
            
            # Processar cada disciplina
            for idx, disciplina in enumerate(disciplinas, 1):
                log(f"\n[{idx}/{len(disciplinas)}] Processando: {disciplina['text']}")
                
                # Buscar ID da disciplina no banco local (com filtro de nível se disponível)
                disciplina_id = self._buscar_disciplina_local(disciplina['text'], nivel_id_turma)
                if not disciplina_id:
                    log(f"  ⚠️ Disciplina não encontrada no banco local: {disciplina['text']}")
                    continue
                
                # Selecionar disciplina
                automacao.selecionar_opcao('IDTURMASDISP', disciplina['value'])
                time.sleep(0.5)
                
                # Selecionar bimestre
                automacao.selecionar_bimestre(bimestre_num)
                time.sleep(0.5)
                
                # Carregar alunos
                automacao.clicar_exibir_alunos()
                time.sleep(2)
                
                # Extrair notas
                dados = automacao.extrair_notas_pagina_atual(
                    turma_nome=turma_completa,
                    disciplina_nome=disciplina['text'],
                    bimestre_numero=bimestre_num
                )
                
                if not dados or not dados['alunos']:
                    log(f"  ⚠️ Nenhuma nota encontrada")
                    continue
                
                log(f"  ✓ {len(dados['alunos'])} alunos com notas")
                
                # Salvar no banco
                inseridas, atualizadas, nao_encontrados = self._salvar_notas_banco(
                    dados['alunos'],
                    alunos_local,
                    disciplina_id,
                    bimestre_num,
                    self.ano_letivo_atual
                )
                
                total_notas_inseridas += inseridas
                total_notas_atualizadas += atualizadas
                alunos_nao_encontrados.update(nao_encontrados)
                
                log(f"  ✓ Salvo: {inseridas} novas, {atualizadas} atualizadas")
                if nao_encontrados:
                    log(f"  ⚠️ {len(nao_encontrados)} alunos não encontrados no sistema")
                
                disciplinas_processadas.append(disciplina['text'])
            
            # Relatório final
            log("\n" + "="*60)
            log("EXTRAÇÃO CONCLUÍDA!")
            log("="*60)
            log(f"📚 Disciplinas processadas: {len(disciplinas_processadas)}")
            log(f"✅ Notas inseridas: {total_notas_inseridas}")
            log(f"🔄 Notas atualizadas: {total_notas_atualizadas}")
            log(f"⚠️ Alunos não encontrados: {len(alunos_nao_encontrados)}")
            
            if alunos_nao_encontrados:
                log("\nAlunos do GEDUC não encontrados no sistema local:")
                for nome in sorted(alunos_nao_encontrados):
                    log(f"  • {nome}")
            
            log("\n" + "="*60)
            
            # Mostrar mensagem de sucesso
            msg_final = (
                f"✅ EXTRAÇÃO CONCLUÍDA!\n\n"
                f"📚 Disciplinas: {len(disciplinas_processadas)}\n"
                f"✅ Notas inseridas: {total_notas_inseridas}\n"
                f"🔄 Notas atualizadas: {total_notas_atualizadas}\n"
                f"⚠️ Alunos não encontrados: {len(alunos_nao_encontrados)}"
            )
            
            if alunos_nao_encontrados:
                msg_final += f"\n\nVerifique o log para detalhes dos alunos não encontrados."
            
            self.janela.after(0, lambda: messagebox.showinfo("Extração Concluída", msg_final))
            
        except Exception as e:
            log(f"\n✗ ERRO: {e}")
            import traceback
            traceback.print_exc()
            log(traceback.format_exc())
            self.janela.after(0, lambda: messagebox.showerror("Erro", f"Erro durante extração:\n{str(e)}"))
        
        finally:
            if automacao:
                log("\n→ Fechando navegador em 5 segundos...")
                time.sleep(5)
                automacao.fechar()
                log("✓ Navegador fechado")
    
    def _obter_nivel_turma(self, turma_id):
        """
        Obtém o nivel_id (Nível de Ensino) de uma turma
        
        Returns:
            nivel_id ou None se não encontrar
        """
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if conn is None:
                logger.error("Erro de conexão ao obter nível da turma: conectar_bd() retornou None")
                return None
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT s.nivel_id
                FROM turmas t
                JOIN series s ON t.serie_id = s.id
                WHERE t.id = %s
                LIMIT 1
            """, (turma_id,))
            
            resultado = cursor.fetchone()
            
            return resultado[0] if resultado else None
            
        except Exception as e:
            logger.error(f"Erro ao obter nível da turma: {e}")
            return None
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
    
    def _buscar_alunos_turma_local(self, turma_id):
        """Busca alunos da turma no banco local"""
        import unicodedata
        
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if conn is None:
                logger.error("Erro de conexão ao buscar alunos locais: conectar_bd() retornou None")
                return {}
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT a.id, a.nome
                FROM alunos a
                JOIN matriculas m ON a.id = m.aluno_id
                WHERE m.turma_id = %s 
                AND m.ano_letivo_id = %s 
                AND m.status IN ('Ativo', 'Transferido')
                AND a.escola_id = %s
                ORDER BY a.nome
            """, self._norm_params((turma_id, self.ano_letivo_atual, config.ESCOLA_ID)))
            
            alunos = cursor.fetchall()
            
            # Criar dicionário com nomes normalizados
            def normalizar_nome(nome):
                # Remover acentuação
                nome = ''.join(c for c in unicodedata.normalize('NFD', nome) 
                              if unicodedata.category(c) != 'Mn')
                # Remover sufixos comuns (do GEDUC e do sistema local)
                sufixos = [
                    '( Transferencia Externa )',  # GEDUC
                    '( TRANSFERENCIA EXTERNA )',  # GEDUC maiúsculo
                    ' (TRANSFERIDO)',              # Sistema local
                    ' (EVADIDO)',                  # Sistema local
                    ' - TRANSFERIDO',              # Sistema local
                    '(Transferido)',               # Variações
                    '(TRANSFERIDO)',
                    ' - Transferido',
                    ' (Evadido)',
                    ' - Evadido'
                ]
                nome_upper = nome.upper()
                for sufixo in sufixos:
                    if nome_upper.endswith(sufixo.upper()):
                        nome = nome[:-(len(sufixo))]
                        break
                return nome.upper().strip()
            
            alunos_dict = {}
            for aluno_id, nome in alunos:
                nome_norm = normalizar_nome(nome)
                alunos_dict[nome_norm] = aluno_id
            
            return alunos_dict
            
        except Exception as e:
            logger.error(f"Erro ao buscar alunos locais: {e}")
            return {}
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
    
    def _buscar_disciplina_local(self, nome_disciplina, nivel_id=None):
        """
        Busca ID da disciplina no banco local pelo nome e nível
        
        Args:
            nome_disciplina: Nome da disciplina
            nivel_id: ID do nível de ensino (opcional, mas recomendado)
        """
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if conn is None:
                logger.error("Erro de conexão ao buscar disciplina: conectar_bd() retornou None")
                return None
            cursor = conn.cursor()
            
            # Se nivel_id foi fornecido, buscar com filtro de nível
            if nivel_id:
                # Buscar por nome exato + nível
                cursor.execute("""
                    SELECT id FROM disciplinas 
                    WHERE nome = %s AND nivel_id = %s AND escola_id = %s
                    LIMIT 1
                """, self._norm_params((nome_disciplina, nivel_id, config.ESCOLA_ID)))
                
                resultado = cursor.fetchone()
                
                if resultado:
                    return resultado[0]
                
                # Se não encontrar, tentar busca parcial + nível
                cursor.execute("""
                    SELECT id FROM disciplinas 
                    WHERE nome LIKE %s AND nivel_id = %s AND escola_id = %s
                    LIMIT 1
                """, self._norm_params((f"%{nome_disciplina}%", nivel_id, config.ESCOLA_ID)))
                
                resultado = cursor.fetchone()
                
                if resultado:
                    return resultado[0]
            
            # Se não tem nivel_id OU não encontrou com nivel_id, buscar sem filtro
            # Reutilizar a mesma conexão/cursor
            # Buscar por nome exato (sem nivel_id)
            cursor.execute("""
                SELECT id FROM disciplinas 
                WHERE nome = %s AND escola_id = %s
                LIMIT 1
            """, self._norm_params((nome_disciplina, config.ESCOLA_ID)))
            
            resultado = cursor.fetchone()
            
            if resultado:
                return resultado[0]
            
            # Busca parcial (último recurso)
            cursor.execute("""
                SELECT id FROM disciplinas 
                WHERE nome LIKE %s AND escola_id = %s
                LIMIT 1
            """, self._norm_params((f"%{nome_disciplina}%", config.ESCOLA_ID)))
            
            resultado = cursor.fetchone()
            
            return resultado[0] if resultado else None
            
        except Exception as e:
            logger.error(f"Erro ao buscar disciplina: {e}")
            return None
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except Exception:
                pass
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
    
    def _salvar_notas_banco(self, alunos_geduc, alunos_local, disciplina_id, bimestre_num, ano_letivo_id):
        """
        Salva notas no banco de dados
        
        Returns:
            (inseridas, atualizadas, nao_encontrados)
        """
        import unicodedata
        
        def normalizar_nome(nome):
            nome = ''.join(c for c in unicodedata.normalize('NFD', nome) 
                          if unicodedata.category(c) != 'Mn')
            # Remover sufixos comuns (do GEDUC e do sistema local)
            sufixos = [
                '( Transferencia Externa )',  # GEDUC
                '( TRANSFERENCIA EXTERNA )',  # GEDUC maiúsculo
                ' (TRANSFERIDO)',              # Sistema local
                ' (EVADIDO)',                  # Sistema local
                ' - TRANSFERIDO',              # Sistema local
                '(Transferido)',               # Variações
                '(TRANSFERIDO)',
                ' - Transferido',
                ' (Evadido)',
                ' - Evadido'
            ]
            nome_upper = nome.upper()
            for sufixo in sufixos:
                if nome_upper.endswith(sufixo.upper()):
                    nome = nome[:-(len(sufixo))]
                    break
            return nome.upper().strip()
        
        try:
            from db.connection import get_cursor
            inseridas = 0
            atualizadas = 0
            nao_encontrados = []

            bimestre_texto = f"{bimestre_num}º bimestre"

            with get_cursor(commit=True) as cursor:
                for aluno_geduc in alunos_geduc:
                    nome_geduc = aluno_geduc['nome']
                    nota_media = aluno_geduc.get('media')

                    if nota_media is None or nota_media == '':
                        continue

                    # Normalizar nome
                    nome_norm = normalizar_nome(nome_geduc)

                    # Buscar ID do aluno no banco local
                    aluno_id = alunos_local.get(nome_norm)

                    if not aluno_id:
                        nao_encontrados.append(nome_geduc)
                        continue

                    # Verificar se já existe nota
                    cursor.execute("""
                        SELECT id, nota FROM notas 
                        WHERE aluno_id = %s 
                        AND disciplina_id = %s 
                        AND bimestre = %s 
                        AND ano_letivo_id = %s
                    """, self._norm_params((aluno_id, disciplina_id, bimestre_texto, ano_letivo_id)))

                    resultado = cursor.fetchone()

                    if resultado:
                        # Atualizar
                        cursor.execute("""
                            UPDATE notas 
                            SET nota = %s 
                            WHERE id = %s
                        """, self._norm_params((nota_media, resultado[0])))
                        atualizadas += 1
                    else:
                        # Inserir
                        cursor.execute("""
                            INSERT INTO notas (aluno_id, disciplina_id, bimestre, nota, ano_letivo_id) 
                            VALUES (%s, %s, %s, %s, %s)
                        """, self._norm_params((aluno_id, disciplina_id, bimestre_texto, nota_media, ano_letivo_id)))
                        inseridas += 1

            return inseridas, atualizadas, nao_encontrados

        except Exception as e:
            logger.error(f"Erro ao salvar notas: {e}")
            import traceback
            traceback.print_exc()
            return 0, 0, []

    def processar_recuperacao_bimestral(self):
        """
        Processa recuperação bimestral para TODAS as turmas e disciplinas de um bimestre
        """
        try:
            import threading
            from automatizar_extracao_geduc import AutomacaoGEDUC
            
            # Validar seleção de bimestre
            if not self.cb_bimestre.get():
                messagebox.showerror("Erro", "Selecione um bimestre!")
                return
            
            # Extrair número do bimestre
            bimestre_texto = self.cb_bimestre.get()
            bimestre_num = int(bimestre_texto.split('º')[0].strip())
            
            # Solicitar credenciais
            credenciais = self._solicitar_credenciais_geduc()
            if not credenciais:
                return
            
            # Confirmar ação de produção
            msg = (
                f"🔄 PROCESSAMENTO DE RECUPERAÇÃO BIMESTRAL\n\n"
                f"📅 Bimestre: {bimestre_num}º\n\n"
                f"⚙️ Este processo irá:\n"
                f"1. Fazer login no GEDUC\n"
                f"2. Buscar TODAS as turmas da escola\n"
                f"3. Para cada turma, processar TODAS as disciplinas\n"
                f"4. Extrair 'Média Atual' e 'Recuperação'\n"
                f"5. Atualizar banco: se (nota/10 < 6) e (nota/10 < Recuperação)\n"
                f"   então nota = Recuperação * 10\n\n"
                f"⏱️ Tempo estimado: 5-15 minutos\n\n"
                f"⚠️ ATENÇÃO: Isso irá processar TODAS as turmas!\n\n"
                f"Continuar?"
            )
            
            if not messagebox.askyesno("Confirmar Recuperação Bimestral", msg):
                return
            
            # Criar janela de progresso
            janela_progresso = self._criar_janela_progresso()
            
            # Executar em thread (modo produção - sem debug)
            def executar():
                self._executar_recuperacao_completa(
                    credenciais,
                    bimestre_num,
                    janela_progresso,
                    modo_debug=False
                )
            
            thread = threading.Thread(target=executar, daemon=True)
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar recuperação:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def _executar_recuperacao_completa(self, credenciais, bimestre_num, janela_progresso, modo_debug=False):
        """Executa o processamento de recuperação para todas as turmas e disciplinas"""
        from automatizar_extracao_geduc import AutomacaoGEDUC
        import time
        import unicodedata
        
        def log(msg):
            """Adiciona mensagem ao log"""
            # Sempre imprimir no console
            logger.info(msg)
            # Atualizar o widget de log somente no thread principal (thread-safe)
            try:
                self.janela.after(0, lambda m=msg: (
                    janela_progresso.text_log.insert(tk.END, m + "\n"),
                    janela_progresso.text_log.see(tk.END)
                ))
            except Exception:
                # Se falhar ao agendar no thread principal, apenas garantir que o print ocorreu
                pass
        
        def normalizar_nome_turma(texto):
            """Normaliza nome para comparação"""
            texto = ''.join(c for c in unicodedata.normalize('NFD', texto) 
                           if unicodedata.category(c) != 'Mn')
            texto = texto.replace('º', '').replace('ª', '')
            return ' '.join(texto.upper().split())
        
        automacao = None
        try:
            log("="*60)
            log("PROCESSAMENTO DE RECUPERAÇÃO BIMESTRAL")
            log("="*60)
            
            # Iniciar automação
            log("\n→ Iniciando navegador...")
            automacao = AutomacaoGEDUC(headless=False)
            
            if not automacao.iniciar_navegador():
                log("✗ Falha ao iniciar navegador")
                self.janela.after(0, lambda: messagebox.showerror("Erro", "Falha ao iniciar navegador!"))
                return
            
            log("✓ Navegador iniciado")
            
            # Login
            log("\n→ Fazendo login no GEDUC...")
            if not automacao.fazer_login(credenciais['usuario'], credenciais['senha'], timeout_recaptcha=120):
                log("✗ Falha no login")
                self.janela.after(0, lambda: messagebox.showerror("Erro", "Falha no login!"))
                return
            
            log("✓ Login realizado")
            
            # Acessar página de recuperação bimestral
            log("\n→ Acessando recuperação bimestral...")
            if not automacao.acessar_recuperacao_bimestral():
                log("✗ Falha ao acessar página")
                return
            
            log("✓ Página de recuperação bimestral carregada")
            
            # Obter todas as turmas
            log("\n→ Carregando lista de turmas...")
            turmas = automacao.obter_opcoes_select('IDTURMA')
            log(f"✓ {len(turmas)} turmas encontradas")
            
            # Estatísticas
            total_turmas_processadas = 0
            total_disciplinas_processadas = 0
            total_alunos_atualizados = 0
            turmas_com_erro = []
            
            # Processar cada turma
            for idx_turma, turma in enumerate(turmas, 1):
                turma_nome = turma['text']
                turma_id_geduc = turma['value']
                
                log(f"\n{'='*60}")
                log(f"[{idx_turma}/{len(turmas)}] Processando turma: {turma_nome}")
                log(f"{'='*60}")
                
                try:
                    # Buscar turma no banco local
                    turma_id_local = self._buscar_turma_local_por_nome(turma_nome)
                    if not turma_id_local:
                        log(f"  ⚠️ Turma não encontrada no banco local")
                        continue
                    
                    # Obter nivel_id da turma
                    nivel_id_turma = self._obter_nivel_turma(turma_id_local)
                    if not nivel_id_turma:
                        log(f"  ⚠️ Não foi possível identificar o nível de ensino")
                        continue
                    
                    log(f"  ✓ Turma local: ID {turma_id_local}, Nível: {nivel_id_turma}")
                    
                    # Buscar alunos da turma no banco local
                    alunos_local = self._buscar_alunos_turma_local(turma_id_local)
                    log(f"  ✓ {len(alunos_local)} alunos no banco local")
                    
                    # Selecionar turma no GEDUC
                    automacao.selecionar_opcao('IDTURMA', turma_id_geduc)
                    time.sleep(1)
                    
                    # Obter disciplinas da turma
                    disciplinas = automacao.obter_opcoes_select('IDTURMASDISP')
                    log(f"  ✓ {len(disciplinas)} disciplinas encontradas")
                    
                    disciplinas_processadas_turma = 0
                    
                    # Processar cada disciplina
                    for idx_disc, disciplina in enumerate(disciplinas, 1):
                        disciplina_nome = disciplina['text']
                        disciplina_id_geduc = disciplina['value']
                        
                        log(f"\n  [{idx_disc}/{len(disciplinas)}] {disciplina_nome}")
                        
                        # Buscar disciplina no banco local
                        disciplina_id_local = self._buscar_disciplina_local(disciplina_nome, nivel_id_turma)
                        if not disciplina_id_local:
                            log(f"    ⚠️ Disciplina não encontrada no banco local")
                            continue
                        
                        # Selecionar disciplina
                        automacao.selecionar_opcao('IDTURMASDISP', disciplina_id_geduc)
                        time.sleep(0.5)
                        
                        # Selecionar bimestre
                        automacao.selecionar_bimestre(bimestre_num)
                        time.sleep(0.5)
                        
                        # Carregar alunos
                        automacao.clicar_exibir_alunos()
                        time.sleep(2)
                        
                        # Extrair dados de recuperação usando função específica
                        dados_recuperacao = automacao.extrair_recuperacao_pagina_atual()
                        
                        if not dados_recuperacao:
                            log(f"    ⚠️ Nenhum dado extraído")
                            continue
                        
                        log(f"    ✓ {len(dados_recuperacao)} registros extraídos")
                        
                        # Processar recuperação no banco
                        atualizados = self._processar_recuperacao_banco(
                            dados_recuperacao,
                            alunos_local,
                            disciplina_id_local,
                            bimestre_num,
                            self.ano_letivo_atual,
                            log_debug=log if modo_debug else None
                        )
                        
                        log(f"    ✓ {atualizados} alunos atualizados")
                        
                        total_alunos_atualizados += atualizados
                        disciplinas_processadas_turma += 1
                        total_disciplinas_processadas += 1
                    
                    log(f"\n  ✅ Turma concluída: {disciplinas_processadas_turma} disciplinas processadas")
                    total_turmas_processadas += 1
                    
                except Exception as e:
                    log(f"  ✗ ERRO ao processar turma: {e}")
                    turmas_com_erro.append(turma_nome)
                    continue
            
            # Relatório final
            log("\n" + "="*60)
            log("RECUPERAÇÃO BIMESTRAL CONCLUÍDA!")
            log("="*60)
            log(f"🏫 Turmas processadas: {total_turmas_processadas}/{len(turmas)}")
            log(f"📚 Disciplinas processadas: {total_disciplinas_processadas}")
            log(f"✅ Alunos atualizados: {total_alunos_atualizados}")
            
            if turmas_com_erro:
                log(f"\n⚠️ Turmas com erro ({len(turmas_com_erro)}):")
                for turma in turmas_com_erro:
                    log(f"  • {turma}")
            
            log("\n" + "="*60)
            
            # Mensagem final
            msg_final = (
                f"✅ RECUPERAÇÃO CONCLUÍDA!\n\n"
                f"🏫 Turmas: {total_turmas_processadas}/{len(turmas)}\n"
                f"📚 Disciplinas: {total_disciplinas_processadas}\n"
                f"✅ Alunos atualizados: {total_alunos_atualizados}"
            )
            
            if turmas_com_erro:
                msg_final += f"\n\n⚠️ {len(turmas_com_erro)} turmas com erro (veja o log)"
            
            self.janela.after(0, lambda: messagebox.showinfo("Recuperação Concluída", msg_final))
            
        except Exception as e:
            log(f"\n✗ ERRO: {e}")
            import traceback
            traceback.print_exc()
            log(traceback.format_exc())
            self.janela.after(0, lambda: messagebox.showerror("Erro", f"Erro durante recuperação:\n{str(e)}"))
        
        finally:
            if automacao:
                log("\n→ Fechando navegador em 5 segundos...")
                time.sleep(5)
                automacao.fechar()
                log("✓ Navegador fechado")
    
    def _buscar_turma_local_por_nome(self, nome_turma_geduc):
        """
        Busca ID da turma no banco local pelo nome do GEDUC
        
        Args:
            nome_turma_geduc: Nome da turma como aparece no GEDUC (ex: "2º ANO-MATU", "6º ANO-VESP - A")
        
        Returns:
            ID da turma ou None se não encontrar
        """
        import unicodedata
        
        def normalizar(texto):
            """Remove acentos e converte para maiúsculas"""
            texto = ''.join(c for c in unicodedata.normalize('NFD', texto) 
                           if unicodedata.category(c) != 'Mn')
            texto = texto.replace('º', '').replace('ª', '')
            return ' '.join(texto.upper().split())
        
        try:
            from db.connection import get_cursor

            with get_cursor() as cursor:
                # Buscar todas as turmas da escola
                cursor.execute("""
                    SELECT t.id, t.nome, s.nome as serie_nome, t.turno
                    FROM turmas t
                    JOIN series s ON t.serie_id = s.id
                    WHERE t.escola_id = %s
                    AND t.ano_letivo_id = %s
                """, self._norm_params((config.ESCOLA_ID, self.ano_letivo_atual)))

                turmas = cursor.fetchall()

            # Normalizar nome do GEDUC
            nome_geduc_norm = normalizar(nome_turma_geduc)
            
            # Tentar encontrar correspondência
            for turma_id, turma_nome, serie_nome, turno in turmas:
                # Construir nome completo da turma local
                # Formato: "SÉRIE TURNO TURMA"
                nome_completo = f"{serie_nome} {turno} {turma_nome}".strip()
                nome_completo_norm = normalizar(nome_completo)
                
                # Tentar diferentes formatos
                # 1. Comparação exata
                if nome_geduc_norm == nome_completo_norm:
                    return turma_id
                
                # 2. GEDUC usa hífen: "2 ANO-MATU" vs "2 ANO MATU"
                nome_com_hifen = f"{serie_nome}-{turno} {turma_nome}".strip()
                nome_com_hifen_norm = normalizar(nome_com_hifen)
                if nome_geduc_norm == nome_com_hifen_norm:
                    return turma_id
                
                # 3. GEDUC usa hífen e travessão: "6 ANO-VESP - A"
                nome_hifen_travessao = f"{serie_nome}-{turno} - {turma_nome}".strip()
                nome_hifen_travessao_norm = normalizar(nome_hifen_travessao)
                if nome_geduc_norm == nome_hifen_travessao_norm:
                    return turma_id
                
                # 4. Match parcial: "1 ANO-MATU" começa com "1 ANO MAT"
                # ou "1 ANO MAT" está contido em "1 ANO-MATU"
                if nome_completo_norm and nome_geduc_norm.startswith(nome_completo_norm):
                    return turma_id
                
                if nome_com_hifen_norm and nome_geduc_norm.startswith(nome_com_hifen_norm):
                    return turma_id
            
            return None

        except Exception as e:
            logger.error(f"Erro ao buscar turma local: {e}")
            return None
    

    def _processar_recuperacao_banco(self, dados_recuperacao, alunos_local, disciplina_id, bimestre_num, ano_letivo_id, log_debug=None):
        """
        Processa recuperação: atualiza nota se (nota/10 < 6) e (nota/10 < Recuperação)
        
        Args:
            dados_recuperacao: Lista de dicts com 'nome', 'recuperacao'
            alunos_local: Dict {nome_normalizado: aluno_id}
            disciplina_id: ID da disciplina
            bimestre_num: Número do bimestre
            ano_letivo_id: ID do ano letivo
            log_debug: Função de log para modo debug (opcional)
        
        Returns:
            Número de alunos atualizados
        """
        import unicodedata
        
        def normalizar_nome(nome):
            nome = ''.join(c for c in unicodedata.normalize('NFD', nome) 
                          if unicodedata.category(c) != 'Mn')
            sufixos = [
                '( Transferencia Externa )', '( TRANSFERENCIA EXTERNA )',
                ' (TRANSFERIDO)', ' (EVADIDO)', ' - TRANSFERIDO',
                '(Transferido)', '(TRANSFERIDO)', ' - Transferido',
                ' (Evadido)', ' - Evadido'
            ]
            nome_upper = nome.upper()
            for sufixo in sufixos:
                if nome_upper.endswith(sufixo.upper()):
                    nome = nome[:-(len(sufixo))]
                    break
            return nome.upper().strip()
        
        try:
            from db.connection import get_cursor

            atualizados = 0
            bimestre_texto = f"{bimestre_num}º bimestre"

            # Debug: cabeçalho se log_debug está ativo
            if log_debug:
                log_debug("\n    " + "="*70)
                log_debug("    📊 ANÁLISE DETALHADA POR ALUNO")
                log_debug("    " + "="*70)

            with get_cursor(commit=True) as cursor:
                for aluno_rec in dados_recuperacao:
                    nome = aluno_rec['nome']
                    recuperacao = aluno_rec.get('recuperacao')

                    # Debug: mostrar aluno processado
                    if log_debug:
                        log_debug(f"\n    👤 Aluno: {nome}")
                        log_debug(f"       Recuperação GEDUC: {recuperacao if recuperacao is not None else 'SEM NOTA'}")

                    # Verificar se tem nota de recuperação
                    if recuperacao is None or recuperacao == '':
                        if log_debug:
                            log_debug(f"       ⚠️ Sem nota de recuperação - IGNORADO")
                        continue

                    # Normalizar nome
                    nome_norm = normalizar_nome(nome)

                    # Buscar ID do aluno
                    aluno_id = alunos_local.get(nome_norm)
                    if not aluno_id:
                        if log_debug:
                            log_debug(f"       ⚠️ Aluno não encontrado no banco local - IGNORADO")
                        continue

                    # Buscar nota atual no banco
                    cursor.execute("""
                        SELECT id, nota FROM notas 
                        WHERE aluno_id = %s 
                        AND disciplina_id = %s 
                        AND bimestre = %s 
                        AND ano_letivo_id = %s
                    """, self._norm_params((aluno_id, disciplina_id, bimestre_texto, ano_letivo_id)))

                    resultado = cursor.fetchone()

                    if not resultado:
                        if log_debug:
                            log_debug(f"       ⚠️ Sem nota no banco - IGNORADO")
                        continue

                    nota_id, nota_atual = resultado

                    # Converter nota_atual para escala 0-10
                    # Usar helper seguro para converter (trata NaN, strings, Decimal etc.)
                    v = to_safe_float(nota_atual)
                    nota_atual_decimal = (v / 10.0) if v is not None else 0

                    # Debug: mostrar nota do banco
                    if log_debug:
                        log_debug(f"       Nota Banco: {nota_atual} (escala 100) = {nota_atual_decimal:.1f} (escala 10)")

                    # Aplicar regra: se (nota/10 < 6) e (Recuperação >= nota/10)
                    condicao1 = nota_atual_decimal < 6.0
                    condicao2 = recuperacao >= nota_atual_decimal

                    if log_debug:
                        log_debug(f"       Verificações:")
                        log_debug(f"         • nota/10 < 6? {nota_atual_decimal:.1f} < 6.0 = {condicao1}")
                        log_debug(f"         • Recup >= nota/10? {recuperacao:.1f} >= {nota_atual_decimal:.1f} = {condicao2}")

                    if condicao1 and condicao2:
                        # Atualizar nota = Recuperação * 10
                        nova_nota = recuperacao * 10

                        if log_debug:
                            log_debug(f"       ✅ SERÁ ATUALIZADO: {nota_atual} → {nova_nota:.0f}")

                        cursor.execute("""
                            UPDATE notas 
                            SET nota = %s 
                            WHERE id = %s
                        """, self._norm_params((nova_nota, nota_id)))

                        atualizados += 1
                    else:
                        if log_debug:
                            log_debug(f"       ❌ NÃO será atualizado (não atende critérios)")

            # Debug: rodapé
            if log_debug:
                log_debug("    " + "="*70)

            return atualizados

        except Exception as e:
            logger.error(f"Erro ao processar recuperação no banco: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def ao_fechar_janela(self):
        """Método chamado quando a janela é fechada pelo usuário"""
        try:
            # Mostrar a janela principal novamente, se existir
            if self.janela_principal:
                self.janela_principal.deiconify()
            
            # Destruir a janela atual
            self.janela.destroy()
        except Exception as e:
            logger.error(f"Erro ao fechar a janela: {e}")

    def focar_campo_seguro(self, campo):
        """Tenta definir o foco em um campo de forma segura, verificando se ele ainda existe"""
        try:
            if campo.winfo_exists():
                campo.focus_set()
                campo.select_range(0, tk.END)  # Seleciona todo o texto para facilitar a edição
        except Exception as e:
            logger.error(f"Erro ao tentar definir foco no campo: {e}")
            # Não propaga o erro, apenas registra no console
    
    # =========================================================================
    # INTEGRAÇÃO COM BANCO DE QUESTÕES - AVALIAÇÕES
    # =========================================================================
    
    def carregar_avaliacoes_disponiveis(self, event=None):
        """Carrega avaliações aplicadas para turma/disciplina/bimestre selecionados."""
        # Também carregar notas (comportamento original)
        self.carregar_notas_alunos(event)
        
        if not self.cb_turma.get() or not self.cb_disciplina.get() or not self.cb_bimestre.get():
            self.cb_avaliacao.set('')
            self.cb_avaliacao['values'] = []
            return
        
        conn = conectar_bd()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            turma_id = self.turmas_map.get(self.cb_turma.get())
            disciplina_nome = self.cb_disciplina.get()
            bimestre = self.cb_bimestre.get()
            
            query = """
                SELECT DISTINCT
                    av.id,
                    av.titulo,
                    aa.data_aplicacao,
                    aa.status
                FROM avaliacoes_aplicadas aa
                INNER JOIN avaliacoes av ON aa.avaliacao_id = av.id
                WHERE aa.turma_id = %s
                  AND av.componente_curricular = %s
                  AND av.bimestre = %s
                  AND aa.status IN ('em_andamento', 'aguardando_lancamento', 'concluida')
                ORDER BY aa.data_aplicacao DESC
            """
            
            cursor.execute(query, (turma_id, disciplina_nome, bimestre))
            avaliacoes = cursor.fetchall()
            
            # Preencher combobox
            valores = [f"{av[0]} - {av[1]} ({av[2].strftime('%d/%m/%Y')})" for av in avaliacoes]
            self.cb_avaliacao['values'] = valores
            
            if valores:
                self.cb_avaliacao.current(0)
                logger.info(f"{len(valores)} avaliação(ões) encontrada(s)")
            else:
                self.cb_avaliacao.set('')
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao carregar avaliações: {e}")
    
    def ao_selecionar_avaliacao(self, event=None):
        """Atualiza informações quando uma avaliação é selecionada."""
        if not self.cb_avaliacao.get():
            return
        avaliacao_id = int(self.cb_avaliacao.get().split(' - ')[0])
        logger.info(f"Avaliação selecionada: ID {avaliacao_id}")
    
    def abrir_janela_respostas(self):
        """Abre janela para registrar respostas de alunos."""
        if not self.cb_avaliacao.get():
            messagebox.showwarning("Aviso", "Selecione uma avaliação primeiro.")
            return
        
        try:
            from JanelaRegistroRespostas import JanelaRegistroRespostas
            
            avaliacao_id = int(self.cb_avaliacao.get().split(' - ')[0])
            turma_id = self.turmas_map.get(self.cb_turma.get())
            
            JanelaRegistroRespostas(self.root, 
                                   avaliacao_id=avaliacao_id,
                                   turma_id=turma_id,
                                   ano_letivo_atual=self.ano_letivo_atual)
        except Exception as e:
            logger.error(f"Erro ao abrir janela de respostas: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir janela: {str(e)}")
    
    def abrir_fila_correcao(self):
        """Abre janela com fila de correção de questões dissertativas."""
        if not self.cb_avaliacao.get():
            messagebox.showwarning("Aviso", "Selecione uma avaliação primeiro.")
            return
        
        try:
            from JanelaFilaCorrecao import JanelaFilaCorrecao
            
            avaliacao_id = int(self.cb_avaliacao.get().split(' - ')[0])
            turma_id = self.turmas_map.get(self.cb_turma.get())
            
            JanelaFilaCorrecao(self.root,
                             professor_id=None,  # Pode filtrar por professor se necessário
                             turma_id=turma_id,
                             avaliacao_id=avaliacao_id)
        except Exception as e:
            logger.error(f"Erro ao abrir fila de correção: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir fila: {str(e)}")
    
    def importar_respostas_csv(self):
        """Importa respostas via CSV."""
        if not self.cb_avaliacao.get():
            messagebox.showwarning("Aviso", "Selecione uma avaliação.")
            return
        
        arquivo = filedialog.askopenfilename(
            title="CSV de Respostas",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")]
        )
        
        if arquivo:
            messagebox.showinfo("Em Desenvolvimento", f"Arquivo: {arquivo}\\n\\nPróxima etapa.")
    
    def sincronizar_avaliacoes_para_notas(self):
        """Sincroniza notas finalizadas para tabela notas."""
        if not self.cb_avaliacao.get():
            messagebox.showwarning("Aviso", "Selecione uma avaliação.")
            return
        
        avaliacao_id = int(self.cb_avaliacao.get().split(' - ')[0])
        turma_id = self.turmas_map.get(self.cb_turma.get())
        
        if not messagebox.askyesno("Confirmar", "Sincronizar notas finalizadas para o sistema?"):
            return
        
        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            
            # Buscar finalizadas
            cursor.execute("""
                SELECT aa.aluno_id, aa.nota_total, av.componente_curricular, av.bimestre
                FROM avaliacoes_alunos aa
                INNER JOIN avaliacoes av ON aa.avaliacao_id = av.id
                WHERE aa.avaliacao_id = %s AND aa.turma_id = %s 
                  AND aa.status = 'finalizada' AND aa.presente = TRUE
            """, (avaliacao_id, turma_id))
            
            avaliacoes_finalizadas = cursor.fetchall()
            
            if not avaliacoes_finalizadas:
                cursor.close()
                conn.close()
                messagebox.showinfo("Info", "Nenhuma avaliação finalizada.")
                return
            
            sincronizadas = 0
            for aluno_id, nota, componente, bimestre in avaliacoes_finalizadas:
                cursor.execute("SELECT id FROM disciplinas WHERE nome = %s", (componente,))
                disciplina = cursor.fetchone()
                if not disciplina:
                    continue
                
                cursor.execute("""
                    INSERT INTO notas (ano_letivo_id, aluno_id, disciplina_id, bimestre, nota)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE nota = VALUES(nota)
                """, (self.ano_letivo_atual, aluno_id, disciplina[0], bimestre, nota))
                
                sincronizadas += 1
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messagebox.showinfo("Sucesso", f"✅ {sincronizadas} nota(s) sincronizada(s)!")
            self.carregar_notas_alunos()
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar: {e}")
            messagebox.showerror("Erro", str(e))

# Função para ser chamada a partir do sistema principal
def abrir_interface_notas(janela_principal=None):
    """
    Abre a interface de cadastro e edição de notas.
    
    Args:
        janela_principal: Referência à janela principal para restaurá-la quando a interface for fechada
        
    Retorna a instância da interface criada.
    """
    try:
        # Esconder a janela principal se for fornecida
        if janela_principal:
            janela_principal.withdraw()
            
        # Criar a instância da interface
        interface = InterfaceCadastroEdicaoNotas(janela_principal=janela_principal)
        return interface
    except Exception as e:
        # Em caso de erro, garantir que a janela principal seja visível novamente
        if janela_principal:
            janela_principal.deiconify()
            
        import traceback
        traceback.print_exc()
        messagebox.showerror("Erro", f"Erro ao abrir interface de notas: {str(e)}")
        return None

# Se o arquivo for executado diretamente
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal se executado diretamente
    app = InterfaceCadastroEdicaoNotas(janela_principal=root)
    root.mainloop()