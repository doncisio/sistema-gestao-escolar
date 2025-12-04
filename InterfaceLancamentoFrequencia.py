"""
Interface de Lançamento de Frequência de Alunos.

Permite que professores lancem as faltas dos alunos por bimestre,
com filtro de turmas e disciplinas baseado no perfil do usuário.
"""

from config_logs import get_logger
logger = get_logger(__name__)
import tkinter as tk
from tkinter import ttk, messagebox
from conexao import conectar_bd
import config
from datetime import datetime
from typing import cast, Optional

# Imports para controle de perfil de usuário
from config import perfis_habilitados
from services.perfil_filter_service import PerfilFilterService, get_turmas_usuario
from auth.usuario_logado import UsuarioLogado
from auth.decorators import requer_permissao


class InterfaceLancamentoFrequencia:
    """Interface para lançamento de frequência/faltas de alunos."""
    
    def __init__(self, root=None, janela_principal=None):
        """
        Inicializa a interface de lançamento de frequência.
        
        Args:
            root: Janela Tk/Toplevel existente ou None para criar nova
            janela_principal: Referência à janela principal da aplicação
        """
        self.janela_principal = janela_principal
        
        # Se root for None, cria uma nova janela
        if root is None:
            self.janela = tk.Toplevel()
            self.janela.title("Lançamento de Frequência - Alunos")
            self.janela.geometry("900x650")
            self.janela.grab_set()
            self.janela.focus_force()
            self.janela.protocol("WM_DELETE_WINDOW", self.ao_fechar_janela)
        else:
            self.janela = root

        # Cores padrão do sistema
        self.co0 = "#F5F5F5"  # Branco suave para o fundo
        self.co1 = "#003A70"  # Azul escuro (principal)
        self.co2 = "#77B341"  # Verde
        self.co3 = "#E2418E"  # Rosa/Magenta
        self.co4 = "#4A86E8"  # Azul mais claro
        self.co7 = "#333333"  # Cinza escuro
        self.co8 = "#BF3036"  # Vermelho
        self.co9 = "#999999"  # Cinza claro
        
        self.janela.configure(bg=self.co0)
        
        # Estado interno
        self.entradas_faltas: dict = {}  # {aluno_id: Entry widget}
        self.alunos_data: list = []  # Lista de dicts com dados dos alunos
        self.niveis_map: dict = {}
        self.series_map: dict = {}
        self.turmas_map: dict = {}
        
        # Obter ano letivo atual
        from typing import Optional, cast
        self.ano_letivo_atual: Optional[int] = None
        # Obter ano letivo atual e tentar converter para int com segurança
        _ano_temp = self.obter_ano_letivo_atual()
        if _ano_temp is not None:
            try:
                self.ano_letivo_atual = int(_ano_temp)
            except Exception:
                # Se não for possível converter, mantemos None e exibimos aviso
                logger.warning(f"Não foi possível converter ano letivo retornado ({_ano_temp}) para int")
        
        if self.ano_letivo_atual is not None:
            self.criar_interface()
        else:
            messagebox.showerror("Erro", "Não foi possível obter o ano letivo. A interface será fechada.")
            self.janela.destroy()
    
    def ao_fechar_janela(self):
        """Trata o evento de fechamento da janela."""
        # Remover binding global do mousewheel
        try:
            if hasattr(self, '_canvas_alunos') and self._canvas_alunos:
                self._canvas_alunos.unbind_all("<MouseWheel>")
        except Exception:
            pass
        if self.janela_principal:
            self.janela_principal.deiconify()
        self.janela.destroy()
    
    def obter_ano_letivo_atual(self) -> "Optional[int]":
        """Obtém o ID do ano letivo atual.

        Retorna `int` quando encontrado ou `None` caso contrário. Converte
        valores numéricos (por exemplo Decimal) para `int` para manter tipos
        consistentes com as anotações do código e evitar avisos do Pylance.
        """
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if conn is None:
                return None

            cursor = conn.cursor()

            # Tenta obter o ano letivo correspondente ao ano corrente
            cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = YEAR(CURDATE()) LIMIT 1")
            resultado = cursor.fetchone()

            if not resultado:
                # Se não encontrar, busca o mais recente
                cursor.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                resultado = cursor.fetchone()

            if not resultado:
                return None

            # Resultado pode ser tuple/list ou dict dependendo do cursor
            if isinstance(resultado, dict):
                val = next(iter(resultado.values()))
            else:
                val = resultado[0]

            # Converter somente para tipos previsíveis para evitar erros de tipo
            try:
                import decimal, numbers, datetime as _dt

                if isinstance(val, int):
                    return val
                if isinstance(val, (decimal.Decimal, float)):
                    return int(val)
                if isinstance(val, str) and val.isdigit():
                    return int(val)
                # Em caso de objetos date/datetime, tentamos extrair o ano (não esperado aqui)
                if isinstance(val, (_dt.date, _dt.datetime)):
                    logger.warning(f"id de ano letivo retornou date/datetime, ignorando: {val}")
                    return None

            except Exception:
                logger.warning(f"Tipo inesperado para id de ano letivo: {type(val)} - valor: {val}")

            # Fallback genérico: tentar int(str(val)) apenas como última opção
            try:
                return int(str(val))
            except Exception:
                logger.warning(f"Valor de id de ano letivo não convertido: {val}")
                return None

        except Exception as e:
            logger.error(f"Erro ao obter ano letivo atual: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def criar_interface(self):
        """Cria a interface principal."""
        self.criar_frames()
        self.criar_cabecalho("Lançamento de Frequência - Alunos")
        self.criar_area_selecao()
        self.criar_area_faltas()
        self.criar_estatisticas()
        self.carregar_niveis_ensino()
    
    def criar_frames(self):
        """Cria os frames principais da interface."""
        # Frame superior para título
        self.frame_titulo = tk.Frame(self.janela, bg=self.co1)
        self.frame_titulo.pack(side="top", fill="x")
        
        # Frame para seleções
        self.frame_selecao = tk.Frame(self.janela, bg=self.co0)
        self.frame_selecao.pack(side="top", fill="x", padx=10, pady=5)
        
        # Frame para estatísticas (no final)
        self.frame_estatisticas = tk.LabelFrame(
            self.janela, text="Resumo", bg=self.co0, font=("Arial", 10, "bold")
        )
        self.frame_estatisticas.pack(side="bottom", fill="x", padx=10, pady=5)
        
        # Frame para lista de alunos
        self.frame_alunos = tk.Frame(self.janela, bg=self.co0)
        self.frame_alunos.pack(side="top", fill="both", expand=True, padx=10, pady=5)
    
    def criar_cabecalho(self, titulo: str):
        """Cria o cabeçalho com título."""
        for widget in self.frame_titulo.winfo_children():
            widget.destroy()
        
        label_titulo = tk.Label(
            self.frame_titulo, text=titulo, 
            font=("Arial", 14, "bold"), bg=self.co1, fg="white"
        )
        label_titulo.pack(fill="x", padx=10, pady=10)
    
    def criar_area_selecao(self):
        """Cria a área de seleção de turma e bimestre."""
        for widget in self.frame_selecao.winfo_children():
            widget.destroy()
        
        # Grid para componentes
        for i in range(3):
            self.frame_selecao.columnconfigure(i, weight=1)
        
        # Seção 1: Seleção de Nível, Série e Turma
        frame_turma = tk.LabelFrame(
            self.frame_selecao, text="Selecione a Turma", 
            bg=self.co0, font=("Arial", 10, "bold")
        )
        frame_turma.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        tk.Label(frame_turma, text="Nível de Ensino:", bg=self.co0).grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.cb_nivel = ttk.Combobox(frame_turma, width=25, state="readonly")
        self.cb_nivel.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.cb_nivel.bind("<<ComboboxSelected>>", self.carregar_series)
        
        tk.Label(frame_turma, text="Série:", bg=self.co0).grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        self.cb_serie = ttk.Combobox(frame_turma, width=25, state="readonly")
        self.cb_serie.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.cb_serie.bind("<<ComboboxSelected>>", self.carregar_turmas)
        
        tk.Label(frame_turma, text="Turma:", bg=self.co0).grid(
            row=2, column=0, padx=5, pady=5, sticky="w"
        )
        self.cb_turma = ttk.Combobox(frame_turma, width=25, state="readonly")
        self.cb_turma.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.cb_turma.bind("<<ComboboxSelected>>", self.carregar_alunos)
        
        # Seção 2: Seleção de Bimestre
        frame_bimestre = tk.LabelFrame(
            self.frame_selecao, text="Selecione o Bimestre", 
            bg=self.co0, font=("Arial", 10, "bold")
        )
        frame_bimestre.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        tk.Label(frame_bimestre, text="Bimestre:", bg=self.co0).grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.cb_bimestre = ttk.Combobox(
            frame_bimestre, width=15, state="readonly",
            values=["1º bimestre", "2º bimestre", "3º bimestre", "4º bimestre"]
        )
        self.cb_bimestre.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.cb_bimestre.current(0)
        self.cb_bimestre.bind("<<ComboboxSelected>>", self.carregar_alunos)
        
        # Botão para carregar
        btn_carregar = tk.Button(
            frame_bimestre, text="Carregar Alunos",
            command=self.carregar_alunos,
            bg=self.co4, fg="white", font=("Arial", 10, "bold")
        )
        btn_carregar.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Seção 3: Ações
        frame_acoes = tk.LabelFrame(
            self.frame_selecao, text="Ações", 
            bg=self.co0, font=("Arial", 10, "bold")
        )
        frame_acoes.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        btn_salvar = tk.Button(
            frame_acoes, text="💾 Salvar Faltas",
            command=self.salvar_faltas,
            bg=self.co2, fg="white", font=("Arial", 10, "bold")
        )
        btn_salvar.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        btn_limpar = tk.Button(
            frame_acoes, text="🧹 Limpar Campos",
            command=self.limpar_campos,
            bg=self.co9, fg="white", font=("Arial", 10, "bold")
        )
        btn_limpar.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    
    def criar_area_faltas(self):
        """Cria a área onde os alunos e campos de faltas serão exibidos."""
        for widget in self.frame_alunos.winfo_children():
            widget.destroy()
        
        # Mensagem inicial
        self.label_msg = tk.Label(
            self.frame_alunos,
            text="Selecione um Nível, Série, Turma e Bimestre para carregar os alunos",
            font=("Arial", 12), bg=self.co0
        )
        self.label_msg.pack(expand=True, fill="both", padx=20, pady=20)
    
    def criar_estatisticas(self):
        """Cria a área de estatísticas/resumo."""
        for widget in self.frame_estatisticas.winfo_children():
            widget.destroy()
        
        for i in range(6):
            self.frame_estatisticas.columnconfigure(i, weight=1)
        
        tk.Label(self.frame_estatisticas, text="Total de Alunos:", bg=self.co0).grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        self.lbl_total_alunos = tk.Label(
            self.frame_estatisticas, text="0", bg=self.co0, 
            font=("Arial", 10, "bold"), width=5
        )
        self.lbl_total_alunos.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        tk.Label(self.frame_estatisticas, text="Total de Faltas:", bg=self.co0).grid(
            row=0, column=2, padx=5, pady=5, sticky="e"
        )
        self.lbl_total_faltas = tk.Label(
            self.frame_estatisticas, text="0", bg=self.co0,
            font=("Arial", 10, "bold"), width=5
        )
        self.lbl_total_faltas.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        tk.Label(self.frame_estatisticas, text="Média de Faltas:", bg=self.co0).grid(
            row=0, column=4, padx=5, pady=5, sticky="e"
        )
        self.lbl_media_faltas = tk.Label(
            self.frame_estatisticas, text="0.0", bg=self.co0,
            font=("Arial", 10, "bold"), width=5
        )
        self.lbl_media_faltas.grid(row=0, column=5, padx=5, pady=5, sticky="w")
    
    def carregar_niveis_ensino(self):
        """Carrega os níveis de ensino disponíveis."""
        conn = None
        cursor = None
        ano = self.ano_letivo_atual
        if ano is None:
            logger.error("Ano letivo atual indefinido ao salvar faltas")
            messagebox.showerror("Erro", "Ano letivo não configurado.")
            return
        ano = int(ano)
        try:
            conn = conectar_bd()
            if conn is None:
                messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                return

            cursor = conn.cursor()
            ano = self.ano_letivo_atual
            if ano is None:
                logger.error("Ano letivo atual indefinido ao salvar faltas")
                messagebox.showerror("Erro", "Ano letivo não configurado.")
                return
            ano = int(ano)
            cursor.execute("SELECT id, nome FROM niveisensino ORDER BY nome")
            niveis = cursor.fetchall()

            if not niveis:
                messagebox.showinfo("Informação", "Nenhum nível de ensino encontrado.")
                return

            self.niveis_map = {nivel[1]: nivel[0] for nivel in niveis}
            self.cb_nivel['values'] = list(self.niveis_map.keys())
            if self.cb_nivel['values']:
                self.cb_nivel.current(0)
                self.carregar_series()
        except Exception as e:
            logger.error(f"Erro ao carregar níveis: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar níveis de ensino: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def carregar_series(self, event=None):
        """Carrega as séries do nível selecionado."""
        if not self.cb_nivel.get():
            return
        
        nivel_id = self.niveis_map.get(self.cb_nivel.get())
        if nivel_id is None:
            return
        
        conn = None
        cursor = None
        ano = self.ano_letivo_atual
        if ano is None:
            logger.error("Ano letivo atual indefinido ao salvar faltas")
            messagebox.showerror("Erro", "Ano letivo não configurado.")
            return
        ano = int(ano)

        try:
            conn = conectar_bd()
            if conn is None:
                return

            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome FROM series WHERE nivel_id = %s ORDER BY nome",
                (nivel_id,)
            )
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
            logger.error(f"Erro ao carregar séries: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def carregar_turmas(self, event=None):
        """Carrega as turmas da série selecionada, aplicando filtro de perfil."""
        if not self.cb_serie.get():
            return
        
        serie_id = self.series_map.get(self.cb_serie.get())
        if serie_id is None:
            return
        # Normalizar tipo para int (ajuda o verificador estático)
        serie_id = int(serie_id)
        
        conn = None
        cursor = None
        ano = self.ano_letivo_atual
        if ano is None:
            logger.error("Ano letivo atual indefinido ao salvar faltas")
            messagebox.showerror("Erro", "Ano letivo não configurado.")
            return
        ano = int(ano)

        try:
            conn = conectar_bd()
            if conn is None:
                return

            cursor = conn.cursor()
            # Garantir ano letivo definido e normalizado
            ano = self.ano_letivo_atual
            if ano is None:
                logger.error("Ano letivo atual indefinido ao carregar turmas")
                return
            ano = int(ano)

            # Obter filtro de turmas baseado no perfil
            turmas_permitidas = get_turmas_usuario()
            
            if turmas_permitidas is None:
                # Admin/Coordenador - sem filtro
                cursor.execute("""
                    SELECT t.id, CONCAT(t.nome, ' - ', t.turno) AS turma_nome 
                    FROM turmas t 
                    WHERE t.serie_id = %s AND t.ano_letivo_id = %s
                    ORDER BY t.nome
                """, (serie_id, cast(int, self.ano_letivo_atual)))
            elif not turmas_permitidas:
                # Professor sem turmas vinculadas
                self.turmas_map = {}
                self.cb_turma['values'] = []
                self.cb_turma.set("")
                messagebox.showinfo(
                    "Sem turmas", 
                    "Você não possui turmas vinculadas para lançamento de frequência.\n"
                    "Contate a coordenação para vincular suas turmas."
                )
                return
            else:
                # Professor - filtrar apenas turmas vinculadas
                # Garantir sequência de parâmetros como tuple para evitar problemas
                # com o analisador de tipos do driver (e também aceitar set/list)
                placeholders = ','.join(['%s'] * len(turmas_permitidas))
                params = (serie_id, cast(int, self.ano_letivo_atual)) + tuple(int(x) for x in turmas_permitidas)
                cursor.execute(f"""
                    SELECT t.id, CONCAT(t.nome, ' - ', t.turno) AS turma_nome 
                    FROM turmas t 
                    WHERE t.serie_id = %s AND t.ano_letivo_id = %s
                    AND t.id IN ({placeholders})
                    ORDER BY t.nome
                """, params)
            
            turmas = cursor.fetchall()

            self.turmas_map = {turma[1]: turma[0] for turma in turmas}
            self.cb_turma['values'] = list(self.turmas_map.keys())
            if self.cb_turma['values']:
                self.cb_turma.current(0)
            else:
                self.cb_turma.set("")
        except Exception as e:
            logger.error(f"Erro ao carregar turmas: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar turmas: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def carregar_alunos(self, event=None):
        """Carrega os alunos da turma selecionada e suas faltas do bimestre."""
        if not self.cb_turma.get() or not self.cb_bimestre.get():
            return
        
        turma_id = self.turmas_map.get(self.cb_turma.get())
        bimestre = self.cb_bimestre.get()
        
        if turma_id is None:
            return
        turma_id = int(turma_id)
        
        conn = None
        cursor = None
        ano = self.ano_letivo_atual
        if ano is None:
            logger.error("Ano letivo atual indefinido ao salvar faltas")
            messagebox.showerror("Erro", "Ano letivo não configurado.")
            return
        ano = int(ano)

        try:
            conn = conectar_bd()
            if conn is None:
                return

            cursor = conn.cursor(dictionary=True)
            ano = self.ano_letivo_atual
            if ano is None:
                logger.error("Ano letivo atual indefinido ao carregar alunos")
                return
            ano = int(ano)
            
            # Buscar alunos matriculados na turma
            cursor.execute("""
                SELECT 
                    a.id AS aluno_id,
                    a.nome AS nome_aluno,
                    COALESCE(fb.faltas, 0) AS faltas
                FROM alunos a
                INNER JOIN matriculas m ON m.aluno_id = a.id
                LEFT JOIN faltas_bimestrais fb ON fb.aluno_id = a.id 
                    AND fb.bimestre = %s 
                    AND fb.ano_letivo_id = %s
                WHERE m.turma_id = %s 
                AND m.status = 'Ativo'
                AND m.ano_letivo_id = %s
                ORDER BY a.nome
            """, (str(bimestre), cast(int, self.ano_letivo_atual), int(turma_id), cast(int, self.ano_letivo_atual)))
            
            self.alunos_data = cursor.fetchall()
            
            if not self.alunos_data:
                messagebox.showinfo("Informação", "Nenhum aluno matriculado nesta turma.")
                self.criar_area_faltas()
                return
            
            # Criar a interface com os alunos
            self.criar_tabela_alunos()
            self.atualizar_estatisticas()
            
        except Exception as e:
            logger.error(f"Erro ao carregar alunos: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar alunos: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def criar_tabela_alunos(self):
        """Cria a tabela com os alunos e campos de entrada de faltas."""
        # Limpar frame
        for widget in self.frame_alunos.winfo_children():
            widget.destroy()
        
        self.entradas_faltas = {}
        
        # Frame com scroll
        canvas = tk.Canvas(self.frame_alunos, bg=self.co0)
        self._canvas_alunos = canvas  # Guardar referência para unbind
        scrollbar = ttk.Scrollbar(self.frame_alunos, orient="vertical", command=canvas.yview)
        frame_scroll = tk.Frame(canvas, bg=self.co0)
        
        frame_scroll.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=frame_scroll, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Configurar scroll com mousewheel
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except Exception:
                pass
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Cabeçalhos
        headers = ["Nº", "Nome do Aluno", "Faltas"]
        for i, header in enumerate(headers):
            tk.Label(
                frame_scroll, text=header, font=("Arial", 10, "bold"),
                bg=self.co1, fg="white", padx=10, pady=5
            ).grid(row=0, column=i, sticky="ew", padx=1, pady=1)
        
        # Configurar larguras das colunas
        frame_scroll.columnconfigure(0, minsize=50)
        frame_scroll.columnconfigure(1, minsize=400)
        frame_scroll.columnconfigure(2, minsize=100)
        
        # Linhas com alunos
        for idx, aluno in enumerate(self.alunos_data, start=1):
            aluno_id = aluno['aluno_id']
            
            # Número
            tk.Label(
                frame_scroll, text=str(idx), font=("Arial", 10),
                bg=self.co0, padx=10, pady=3
            ).grid(row=idx, column=0, sticky="ew", padx=1, pady=1)
            
            # Nome
            tk.Label(
                frame_scroll, text=aluno['nome_aluno'], font=("Arial", 10),
                bg=self.co0, anchor="w", padx=10, pady=3
            ).grid(row=idx, column=1, sticky="ew", padx=1, pady=1)
            
            # Campo de faltas
            var_faltas = tk.StringVar(value=str(aluno['faltas']))
            entry_faltas = ttk.Entry(
                frame_scroll, width=10, textvariable=var_faltas,
                justify="center"
            )
            entry_faltas.grid(row=idx, column=2, sticky="ew", padx=1, pady=1)
            
            # Vincular evento de mudança para atualizar estatísticas
            entry_faltas.bind("<KeyRelease>", lambda e: self.atualizar_estatisticas())
            
            self.entradas_faltas[aluno_id] = entry_faltas
        
        # Layout
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def atualizar_estatisticas(self):
        """Atualiza as estatísticas de faltas."""
        total_alunos = len(self.alunos_data)
        total_faltas = 0
        
        for aluno_id, entry in self.entradas_faltas.items():
            try:
                faltas = int(entry.get() or 0)
                total_faltas += faltas
            except ValueError:
                pass
        
        media = total_faltas / total_alunos if total_alunos > 0 else 0
        
        self.lbl_total_alunos.config(text=str(total_alunos))
        self.lbl_total_faltas.config(text=str(total_faltas))
        self.lbl_media_faltas.config(text=f"{media:.1f}")
    
    def salvar_faltas(self):
        """Salva as faltas dos alunos no banco de dados."""
        if not self.cb_turma.get() or not self.cb_bimestre.get():
            messagebox.showwarning("Aviso", "Selecione uma turma e bimestre.")
            return
        
        # Verificar permissão (coordenador não pode editar)
        if perfis_habilitados():
            perfil = UsuarioLogado.get_perfil()
            if perfil == 'coordenador':
                messagebox.showwarning(
                    "Acesso Negado",
                    "Coordenadores podem visualizar mas não podem editar a frequência.\n"
                    "Entre em contato com o professor responsável ou administrador."
                )
                return
            
            # Verificar se professor tem acesso à turma
            if perfil == 'professor':
                turma_id = self.turmas_map.get(self.cb_turma.get())
                turmas_permitidas = get_turmas_usuario()
                
                if turmas_permitidas is not None and turma_id not in turmas_permitidas:
                    messagebox.showerror(
                        "Acesso Negado",
                        "Você não tem permissão para lançar frequência nesta turma."
                    )
                    return
        
        bimestre = self.cb_bimestre.get()
        
        # Validar entradas
        dados_para_salvar = []
        for aluno_id, entry in self.entradas_faltas.items():
            valor = entry.get().strip()
            if not valor:
                valor = "0"
            
            try:
                faltas = int(valor)
                if faltas < 0:
                    raise ValueError("Valor negativo")
                dados_para_salvar.append((aluno_id, faltas))
            except ValueError:
                messagebox.showerror(
                    "Erro de Validação",
                    f"Valor inválido de faltas para o aluno ID {aluno_id}.\n"
                    "Use apenas números inteiros não negativos."
                )
                return
        
        conn = None
        cursor = None
        # Garantir que temos ano letivo atual antes de salvar
        if self.ano_letivo_atual is None:
            _ano = self.obter_ano_letivo_atual()
            if _ano is not None:
                try:
                    self.ano_letivo_atual = int(_ano)
                except Exception:
                    self.ano_letivo_atual = None
        if self.ano_letivo_atual is None:
            messagebox.showerror("Erro", "Ano letivo atual indefinido. Não é possível salvar as faltas.")
            return
        try:
            conn = conectar_bd()
            if conn is None:
                messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                return

            cursor = conn.cursor()
            
            salvos = 0
            for aluno_id, faltas in dados_para_salvar:
                # Verificar se já existe registro
                cursor.execute("""
                    SELECT id FROM faltas_bimestrais 
                    WHERE aluno_id = %s AND bimestre = %s AND ano_letivo_id = %s
                """, (int(aluno_id), str(bimestre), cast(int, self.ano_letivo_atual)))
                
                resultado = cursor.fetchone()
                
                if resultado:
                    # Atualizar registro existente
                    cursor.execute("""
                        UPDATE faltas_bimestrais 
                        SET faltas = %s 
                        WHERE aluno_id = %s AND bimestre = %s AND ano_letivo_id = %s
                    """, (int(faltas), int(aluno_id), str(bimestre), cast(int, self.ano_letivo_atual)))
                else:
                    # Inserir novo registro
                    cursor.execute("""
                        INSERT INTO faltas_bimestrais (aluno_id, bimestre, ano_letivo_id, faltas)
                        VALUES (%s, %s, %s, %s)
                    """, (int(aluno_id), str(bimestre), cast(int, self.ano_letivo_atual), int(faltas)))
                
                salvos += 1
            
            conn.commit()
            
            messagebox.showinfo(
                "Sucesso",
                f"Frequência salva com sucesso!\n{salvos} registros atualizados."
            )
            
            logger.info(f"Frequência salva: {salvos} alunos, bimestre {bimestre}")
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao salvar faltas: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar faltas: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def limpar_campos(self):
        """Limpa todos os campos de entrada de faltas."""
        for entry in self.entradas_faltas.values():
            entry.delete(0, tk.END)
            entry.insert(0, "0")
        self.atualizar_estatisticas()


def abrir_interface_frequencia(janela_principal=None):
    """
    Função auxiliar para abrir a interface de frequência.
    
    Args:
        janela_principal: Referência à janela principal (opcional)
    """
    try:
        interface = InterfaceLancamentoFrequencia(janela_principal=janela_principal)
        return interface
    except Exception as e:
        logger.error(f"Erro ao abrir interface de frequência: {e}")
        messagebox.showerror("Erro", f"Não foi possível abrir a interface: {e}")
        return None
