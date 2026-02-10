"""
Janela para Gerenciamento de Livros Faltantes por Turma.

Esta janela permite registrar e gerenciar a quantidade de livros faltantes
por disciplina para cada turma, incluindo informações sobre editora e coleção.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from typing import Dict, Optional, Any
import logging

from src.core.conexao import conectar_bd
from auth.usuario_logado import UsuarioLogado
from src.core.config import ANO_LETIVO_ATUAL

# Configuração de logging
logger = logging.getLogger(__name__)

# Definição de cores do sistema
co0 = "#F5F5F5"  # Fundo
co1 = "#003A70"  # Azul headers
co2 = "#77B341"  # Verde botão salvar
co6 = "#F7B731"  # Amarelo botão limpar
co7 = "#333333"  # Texto escuro
co8 = "#BF3036"  # Vermelho botão fechar

# Lista de disciplinas padrão
DISCIPLINAS = ["PRT", "MTM", "CNC", "GEO/HIST", "ART"]


class LivrosFaltantesWindow:
    """Janela para gerenciamento de livros faltantes por turma."""
    
    def __init__(self, janela_principal: tk.Tk) -> None:
        """
        Inicializa a janela de livros faltantes.
        
        Args:
            janela_principal: Referência à janela principal do sistema
        """
        self.janela_principal = janela_principal
        self.janela = tk.Toplevel()
        self.janela.title("Gerenciamento de Livros Faltantes")
        
        # Configurações da janela
        self._configurar_janela()
        
        # Variáveis de controle
        self.ano_letivo_var = tk.StringVar()
        self.serie_var = tk.StringVar()
        self.turma_var = tk.StringVar()
        
        # Dicionário para armazenar os widgets de entrada de cada disciplina
        # Estrutura: {disciplina: {'quantidade': Entry, 'editora': Entry, 'colecao': Entry}}
        self.disciplina_entries: Dict[str, Dict[str, tk.Entry]] = {}
        
        # Dados carregados
        self.anos_letivos: list = []
        self.series_disponiveis: list = []
        self.turmas_disponiveis: list = []
        
        # Armazenar dados da turma anterior para reuso
        self.dados_turma_anterior: Optional[Dict[str, Dict[str, str]]] = None
        
        # Criar interface
        self._criar_interface()
        
        # Carregar dados iniciais
        self._carregar_anos_letivos()
        
        # Configurar eventos de fechamento
        self.janela.protocol("WM_DELETE_WINDOW", self._fechar_janela)
        
        # Esconder janela principal
        if self.janela_principal:
            self.janela_principal.withdraw()
    
    def _configurar_janela(self) -> None:
        """Configura propriedades básicas da janela."""
        # Tamanho e posição
        largura = 1000
        altura = 700
        
        # Centralizar na tela
        largura_tela = self.janela.winfo_screenwidth()
        altura_tela = self.janela.winfo_screenheight()
        pos_x = (largura_tela // 2) - (largura // 2)
        pos_y = (altura_tela // 2) - (altura // 2)
        
        self.janela.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
        self.janela.configure(bg=co0)
        self.janela.resizable(True, True)
        
        # Configurar peso das colunas e linhas para responsividade
        self.janela.grid_rowconfigure(0, weight=1)
        self.janela.grid_columnconfigure(0, weight=1)
    
    def _criar_interface(self) -> None:
        """Cria todos os elementos da interface."""
        # Frame principal
        main_frame = tk.Frame(self.janela, bg=co0)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        self._criar_header(main_frame)
        
        # Seleção de filtros
        self._criar_filtros(main_frame)
        
        # Frame de disciplinas com scrollbar
        self._criar_frame_disciplinas(main_frame)
        
        # Observações
        self._criar_campo_observacoes(main_frame)
        
        # Botões de ação
        self._criar_botoes(main_frame)
    
    def _criar_header(self, parent: tk.Frame) -> None:
        """
        Cria o header da janela.
        
        Args:
            parent: Frame pai onde o header será inserido
        """
        header_frame = tk.Frame(parent, bg=co1, height=60)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_propagate(False)
        
        titulo = tk.Label(
            header_frame,
            text="Gerenciamento de Livros Faltantes",
            font=("Segoe UI", 18, "bold"),
            bg=co1,
            fg="white"
        )
        titulo.grid(row=0, column=0, pady=15)
    
    def _criar_filtros(self, parent: tk.Frame) -> None:
        """
        Cria a seção de filtros (Ano Letivo, Série, Turma).
        
        Args:
            parent: Frame pai onde os filtros serão inseridos
        """
        filtros_frame = tk.Frame(parent, bg=co0)
        filtros_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        filtros_frame.grid_columnconfigure(1, weight=1)
        filtros_frame.grid_columnconfigure(3, weight=1)
        filtros_frame.grid_columnconfigure(5, weight=1)
        
        # Ano Letivo
        tk.Label(
            filtros_frame,
            text="Ano Letivo:",
            font=("Segoe UI", 11),
            bg=co0,
            fg=co7
        ).grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        self.combo_ano_letivo = ttk.Combobox(
            filtros_frame,
            textvariable=self.ano_letivo_var,
            state="readonly",
            font=("Segoe UI", 10),
            width=20
        )
        self.combo_ano_letivo.grid(row=0, column=1, padx=(0, 20), sticky="ew")
        self.combo_ano_letivo.bind("<<ComboboxSelected>>", self._on_ano_letivo_changed)
        
        # Série
        tk.Label(
            filtros_frame,
            text="Série:",
            font=("Segoe UI", 11),
            bg=co0,
            fg=co7
        ).grid(row=0, column=2, padx=(0, 10), sticky="w")
        
        self.combo_serie = ttk.Combobox(
            filtros_frame,
            textvariable=self.serie_var,
            state="readonly",
            font=("Segoe UI", 10),
            width=20
        )
        self.combo_serie.grid(row=0, column=3, padx=(0, 20), sticky="ew")
        self.combo_serie.bind("<<ComboboxSelected>>", self._on_serie_changed)
        
        # Turma
        tk.Label(
            filtros_frame,
            text="Turma:",
            font=("Segoe UI", 11),
            bg=co0,
            fg=co7
        ).grid(row=0, column=4, padx=(0, 10), sticky="w")
        
        self.combo_turma = ttk.Combobox(
            filtros_frame,
            textvariable=self.turma_var,
            state="readonly",
            font=("Segoe UI", 10),
            width=20
        )
        self.combo_turma.grid(row=0, column=5, sticky="ew")
        self.combo_turma.bind("<<ComboboxSelected>>", self._on_turma_changed)
    
    def _criar_frame_disciplinas(self, parent: tk.Frame) -> None:
        """
        Cria o frame com scrollbar contendo a tabela de disciplinas.
        
        Args:
            parent: Frame pai onde o frame de disciplinas será inserido
        """
        # Frame container
        container = tk.Frame(parent, bg=co0)
        container.grid(row=3, column=0, sticky="nsew", pady=(0, 20))
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # Canvas com scrollbar
        canvas = tk.Canvas(container, bg=co0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        self.disciplinas_frame = tk.Frame(canvas, bg=co0)
        
        # Configurar canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Grid
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Criar janela no canvas
        canvas_window = canvas.create_window((0, 0), window=self.disciplinas_frame, anchor="nw")
        
        # Atualizar scrollregion quando o frame mudar de tamanho
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        self.disciplinas_frame.bind("<Configure>", _on_frame_configure)
        
        # Ajustar largura do frame ao canvas
        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", _on_canvas_configure)
        
        # Criar campos de disciplinas
        self._criar_campos_disciplinas()
    
    def _criar_campos_disciplinas(self) -> None:
        """Cria a tabela de disciplinas com seus respectivos campos."""
        # Limpar frame
        for widget in self.disciplinas_frame.winfo_children():
            widget.destroy()
        
        self.disciplina_entries.clear()
        
        # Header da tabela
        header_bg = co1
        headers = ["Disciplina", "Quantidade Faltante", "Editora", "Coleção"]
        col_widths = [15, 20, 30, 30]
        
        for col, (header, width) in enumerate(zip(headers, col_widths)):
            header_label = tk.Label(
                self.disciplinas_frame,
                text=header,
                font=("Segoe UI", 11, "bold"),
                bg=header_bg,
                fg="white",
                width=width,
                height=2,
                relief="solid",
                borderwidth=1
            )
            header_label.grid(row=0, column=col, padx=1, pady=1, sticky="ew")
        
        # Configurar peso das colunas
        self.disciplinas_frame.grid_columnconfigure(0, weight=1)
        self.disciplinas_frame.grid_columnconfigure(1, weight=1)
        self.disciplinas_frame.grid_columnconfigure(2, weight=2)
        self.disciplinas_frame.grid_columnconfigure(3, weight=2)
        
        # Criar linhas para cada disciplina
        for idx, disciplina in enumerate(DISCIPLINAS, start=1):
            # Cor alternada para linhas
            bg_color = "white" if idx % 2 == 0 else "#F9F9F9"
            
            # Coluna 1: Nome da Disciplina
            disciplina_label = tk.Label(
                self.disciplinas_frame,
                text=disciplina,
                font=("Segoe UI", 10, "bold"),
                bg=bg_color,
                fg=co7,
                width=15,
                height=2,
                relief="solid",
                borderwidth=1
            )
            disciplina_label.grid(row=idx, column=0, padx=1, pady=1, sticky="ew")
            
            # Coluna 2: Quantidade Faltante
            quantidade_entry = tk.Entry(
                self.disciplinas_frame,
                font=("Segoe UI", 10),
                justify="center",
                relief="solid",
                borderwidth=1
            )
            quantidade_entry.grid(row=idx, column=1, padx=1, pady=1, sticky="ew")
            quantidade_entry.insert(0, "0")
            
            # Coluna 3: Editora
            editora_entry = tk.Entry(
                self.disciplinas_frame,
                font=("Segoe UI", 10),
                relief="solid",
                borderwidth=1
            )
            editora_entry.grid(row=idx, column=2, padx=1, pady=1, sticky="ew")
            
            # Coluna 4: Coleção
            colecao_entry = tk.Entry(
                self.disciplinas_frame,
                font=("Segoe UI", 10),
                relief="solid",
                borderwidth=1
            )
            colecao_entry.grid(row=idx, column=3, padx=1, pady=1, sticky="ew")
            
            # Armazenar referências aos widgets
            self.disciplina_entries[disciplina] = {
                'quantidade': quantidade_entry,
                'editora': editora_entry,
                'colecao': colecao_entry
            }
    
    def _criar_campo_observacoes(self, parent: tk.Frame) -> None:
        """
        Cria o campo de observações.
        
        Args:
            parent: Frame pai onde o campo será inserido
        """
        obs_frame = tk.Frame(parent, bg=co0)
        obs_frame.grid(row=4, column=0, sticky="ew", pady=(0, 20))
        
        tk.Label(
            obs_frame,
            text="Observações:",
            font=("Segoe UI", 11),
            bg=co0,
            fg=co7
        ).pack(anchor="w", pady=(0, 5))
        
        self.observacoes_text = scrolledtext.ScrolledText(
            obs_frame,
            height=5,
            font=("Segoe UI", 10),
            wrap=tk.WORD,
            relief="solid",
            borderwidth=1
        )
        self.observacoes_text.pack(fill="both", expand=True)
    
    def _criar_botoes(self, parent: tk.Frame) -> None:
        """
        Cria os botões de ação.
        
        Args:
            parent: Frame pai onde os botões serão inseridos
        """
        botoes_frame = tk.Frame(parent, bg=co0)
        botoes_frame.grid(row=5, column=0, sticky="ew")
        botoes_frame.grid_columnconfigure(0, weight=1)
        botoes_frame.grid_columnconfigure(1, weight=1)
        botoes_frame.grid_columnconfigure(2, weight=1)
        
        # Botão Salvar
        btn_salvar = tk.Button(
            botoes_frame,
            text="Salvar",
            font=("Segoe UI", 11, "bold"),
            bg=co2,
            fg="white",
            relief="raised",
            borderwidth=2,
            cursor="hand2",
            command=self._salvar_dados,
            height=2
        )
        btn_salvar.grid(row=0, column=0, padx=5, sticky="ew")
        
        # Botão Limpar
        btn_limpar = tk.Button(
            botoes_frame,
            text="Limpar",
            font=("Segoe UI", 11, "bold"),
            bg=co6,
            fg="white",
            relief="raised",
            borderwidth=2,
            cursor="hand2",
            command=self._limpar_formulario,
            height=2
        )
        btn_limpar.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Botão Fechar
        btn_fechar = tk.Button(
            botoes_frame,
            text="Fechar",
            font=("Segoe UI", 11, "bold"),
            bg=co8,
            fg="white",
            relief="raised",
            borderwidth=2,
            cursor="hand2",
            command=self._fechar_janela,
            height=2
        )
        btn_fechar.grid(row=0, column=2, padx=5, sticky="ew")
    
    def _carregar_anos_letivos(self) -> None:
        """Carrega a lista de anos letivos disponíveis."""
        try:
            conn = conectar_bd()
            if not conn:
                messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados")
                return
            
            cursor = conn.cursor(dictionary=True)
            
            # Buscar anos letivos
            cursor.execute("""
                SELECT id, ano_letivo
                FROM anosletivos
                ORDER BY ano_letivo DESC
            """)
            
            self.anos_letivos = cursor.fetchall()
            
            # Preencher combobox
            anos = [str(ano['ano_letivo']) for ano in self.anos_letivos]
            self.combo_ano_letivo['values'] = anos
            
            # Selecionar ano letivo atual se disponível
            ano_atual_str = str(ANO_LETIVO_ATUAL)
            if ano_atual_str in anos:
                self.ano_letivo_var.set(ano_atual_str)
                self._carregar_series_ano()
            elif anos:
                self.ano_letivo_var.set(anos[0])
                self._carregar_series_ano()
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao carregar anos letivos: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar anos letivos: {str(e)}")
    
    def _carregar_series_ano(self) -> None:
        """Carrega as séries que possuem turmas no ano letivo selecionado."""
        try:
            ano_letivo = self.ano_letivo_var.get()
            if not ano_letivo:
                return
            
            # Buscar ID do ano letivo
            ano_letivo_id = None
            for ano in self.anos_letivos:
                if str(ano['ano_letivo']) == ano_letivo:
                    ano_letivo_id = ano['id']
                    break
            
            if not ano_letivo_id:
                return
            
            conn = conectar_bd()
            if not conn:
                return
            
            cursor = conn.cursor(dictionary=True)
            
            # Buscar séries com turmas neste ano letivo (1º ao 7º ano)
            cursor.execute("""
                SELECT DISTINCT s.id, s.nome
                FROM series s
                INNER JOIN turmas t ON s.id = t.serie_id
                WHERE t.ano_letivo_id = %s
                  AND t.escola_id = 60
                  AND s.id BETWEEN 1 AND 7
                ORDER BY s.id, s.nome
            """, (ano_letivo_id,))
            
            self.series_disponiveis = cursor.fetchall()
            
            # Preencher combobox
            series = [serie['nome'] for serie in self.series_disponiveis]
            self.combo_serie['values'] = series
            
            # Limpar seleção
            self.serie_var.set("")
            self.turma_var.set("")
            self.combo_turma['values'] = []
            
            if series:
                self.serie_var.set(series[0])
                self._carregar_turmas()
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao carregar séries: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar séries: {str(e)}")
    
    def _carregar_turmas(self) -> None:
        """Carrega as turmas da série e ano letivo selecionados."""
        try:
            ano_letivo = self.ano_letivo_var.get()
            serie_nome = self.serie_var.get()
            
            if not ano_letivo or not serie_nome:
                return
            
            # Buscar IDs
            ano_letivo_id = None
            for ano in self.anos_letivos:
                if str(ano['ano_letivo']) == ano_letivo:
                    ano_letivo_id = ano['id']
                    break
            
            serie_id = None
            for serie in self.series_disponiveis:
                if serie['nome'] == serie_nome:
                    serie_id = serie['id']
                    break
            
            if not ano_letivo_id or not serie_id:
                return
            
            conn = conectar_bd()
            if not conn:
                return
            
            cursor = conn.cursor(dictionary=True)
            
            # Buscar turmas
            cursor.execute("""
                SELECT DISTINCT nome AS turma
                FROM turmas
                WHERE ano_letivo_id = %s
                  AND serie_id = %s
                  AND escola_id = 60
                ORDER BY nome
            """, (ano_letivo_id, serie_id))
            
            resultados = cursor.fetchall()
            
            # Processar turmas (exibir "Única" para turmas vazias)
            turmas = []
            for row in resultados:
                turma = row['turma']
                if not turma or turma.strip() == '':
                    turmas.append("Única")
                else:
                    turmas.append(turma)
            
            self.turmas_disponiveis = turmas
            self.combo_turma['values'] = turmas
            
            # Limpar seleção
            self.turma_var.set("")
            
            if turmas:
                self.turma_var.set(turmas[0])
                self._carregar_dados()
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao carregar turmas: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar turmas: {str(e)}")
    
    def _carregar_dados(self) -> None:
        """Carrega os dados de livros faltantes para a turma selecionada."""
        try:
            ano_letivo = self.ano_letivo_var.get()
            serie_nome = self.serie_var.get()
            turma = self.turma_var.get()
            
            if not ano_letivo or not serie_nome or not turma:
                return
            
            # Buscar IDs
            ano_letivo_id = None
            for ano in self.anos_letivos:
                if str(ano['ano_letivo']) == ano_letivo:
                    ano_letivo_id = ano['id']
                    break
            
            serie_id = None
            for serie in self.series_disponiveis:
                if serie['nome'] == serie_nome:
                    serie_id = serie['id']
                    break
            
            if not ano_letivo_id or not serie_id:
                return
            
            # Converter "Única" para string vazia
            turma_db = "" if turma == "Única" else turma
            
            conn = conectar_bd()
            if not conn:
                return
            
            cursor = conn.cursor(dictionary=True)
            
            # Buscar dados de livros faltantes
            cursor.execute("""
                SELECT disciplina, quantidade_faltante, editora, colecao, observacao
                FROM livros_faltantes
                WHERE ano_letivo_id = %s
                  AND serie_id = %s
                  AND turma = %s
            """, (ano_letivo_id, serie_id, turma_db))
            
            resultados = cursor.fetchall()
            
            # Limpar formulário primeiro
            self._limpar_formulario()
            
            # Se não houver dados salvos e houver dados da turma anterior, usar como base
            if not resultados and self.dados_turma_anterior:
                logger.info(f"Sem dados para turma atual. Copiando dados da turma anterior.")
                
                for disciplina, dados in self.dados_turma_anterior.items():
                    if disciplina in self.disciplina_entries:
                        entries = self.disciplina_entries[disciplina]
                        
                        # Quantidade
                        entries['quantidade'].delete(0, tk.END)
                        entries['quantidade'].insert(0, dados.get('quantidade', ''))
                        
                        # Editora
                        entries['editora'].delete(0, tk.END)
                        entries['editora'].insert(0, dados.get('editora', ''))
                        
                        # Coleção
                        entries['colecao'].delete(0, tk.END)
                        entries['colecao'].insert(0, dados.get('colecao', ''))
                
                # Mostrar mensagem informativa
                messagebox.showinfo(
                    "Dados Copiados",
                    "Esta turma não possui dados salvos.\n\n"
                    "Os dados da turma anterior foram copiados para facilitar o preenchimento.\n\n"
                    "Você pode editar e salvar normalmente."
                )
            
            # Preencher campos com os dados salvos
            elif resultados:
                # Atualizar dados da turma anterior com os dados atuais
                dados_atuais = {}
                
                for row in resultados:
                    disciplina = row['disciplina']
                    quantidade = row['quantidade_faltante']
                    editora = row['editora'] or ""
                    colecao = row['colecao'] or ""
                    observacao = row['observacao'] or ""
                    
                    # Armazenar para próxima turma
                    dados_atuais[disciplina] = {
                        'quantidade': str(quantidade),
                        'editora': editora,
                        'colecao': colecao
                    }
                    
                    if disciplina in self.disciplina_entries:
                        entries = self.disciplina_entries[disciplina]
                        
                        # Quantidade
                        entries['quantidade'].delete(0, tk.END)
                        entries['quantidade'].insert(0, str(quantidade))
                        
                        # Editora
                        entries['editora'].delete(0, tk.END)
                        entries['editora'].insert(0, editora)
                        
                        # Coleção
                        entries['colecao'].delete(0, tk.END)
                        entries['colecao'].insert(0, colecao)
                    
                    # Observação (só preenche uma vez, pega da primeira disciplina)
                    if observacao and self.observacoes_text.get("1.0", tk.END).strip() == "":
                        self.observacoes_text.delete("1.0", tk.END)
                        self.observacoes_text.insert("1.0", observacao)
                
                # Atualizar dados anteriores
                self.dados_turma_anterior = dados_atuais
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar dados: {str(e)}")
    
    def _salvar_dados(self) -> None:
        """Salva os dados de livros faltantes no banco de dados."""
        try:
            ano_letivo = self.ano_letivo_var.get()
            serie_nome = self.serie_var.get()
            turma = self.turma_var.get()
            
            if not ano_letivo or not serie_nome or not turma:
                messagebox.showwarning("Aviso", "Selecione Ano Letivo, Série e Turma")
                return
            
            # Buscar IDs
            ano_letivo_id = None
            for ano in self.anos_letivos:
                if str(ano['ano_letivo']) == ano_letivo:
                    ano_letivo_id = ano['id']
                    break
            
            serie_id = None
            for serie in self.series_disponiveis:
                if serie['nome'] == serie_nome:
                    serie_id = serie['id']
                    break
            
            if not ano_letivo_id or not serie_id:
                messagebox.showerror("Erro", "Ano letivo ou série inválidos")
                return
            
            # Converter "Única" para string vazia
            turma_db = "" if turma == "Única" else turma
            
            # Obter usuário logado
            usuario = UsuarioLogado.get_usuario()
            username = usuario.username if usuario else "sistema"
            
            # Obter observação
            observacao = self.observacoes_text.get("1.0", tk.END).strip()
            
            conn = conectar_bd()
            if not conn:
                messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados")
                return
            
            cursor = conn.cursor()
            
            # Processar cada disciplina
            registros_salvos = 0
            
            for disciplina, entries in self.disciplina_entries.items():
                try:
                    # Obter valores
                    quantidade_str = entries['quantidade'].get().strip()
                    editora = entries['editora'].get().strip()
                    colecao = entries['colecao'].get().strip()
                    
                    # Validar quantidade
                    try:
                        quantidade = int(quantidade_str) if quantidade_str else 0
                    except ValueError:
                        quantidade = 0
                    
                    # Inserir ou atualizar registro
                    cursor.execute("""
                        INSERT INTO livros_faltantes 
                        (ano_letivo_id, serie_id, turma, disciplina, quantidade_faltante, 
                         editora, colecao, observacao, data_registro, data_atualizacao, usuario_registro)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                        ON DUPLICATE KEY UPDATE
                            quantidade_faltante = VALUES(quantidade_faltante),
                            editora = VALUES(editora),
                            colecao = VALUES(colecao),
                            observacao = VALUES(observacao),
                            data_atualizacao = NOW(),
                            usuario_registro = VALUES(usuario_registro)
                    """, (ano_letivo_id, serie_id, turma_db, disciplina, quantidade,
                          editora, colecao, observacao, username))
                    
                    registros_salvos += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao salvar disciplina {disciplina}: {e}")
                    continue
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messagebox.showinfo(
                "Sucesso",
                f"Dados salvos com sucesso!\n{registros_salvos} disciplinas atualizadas."
            )
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar dados: {str(e)}")
    
    def _limpar_formulario(self) -> None:
        """Limpa todos os campos do formulário."""
        try:
            # Limpar campos de disciplinas
            for disciplina, entries in self.disciplina_entries.items():
                # Quantidade
                entries['quantidade'].delete(0, tk.END)
                entries['quantidade'].insert(0, "0")
                
                # Editora
                entries['editora'].delete(0, tk.END)
                
                # Coleção
                entries['colecao'].delete(0, tk.END)
            
            # Limpar observações
            self.observacoes_text.delete("1.0", tk.END)
            
        except Exception as e:
            logger.error(f"Erro ao limpar formulário: {e}")
            messagebox.showerror("Erro", f"Erro ao limpar formulário: {str(e)}")
    
    def _on_ano_letivo_changed(self, event=None) -> None:
        """
        Callback quando o ano letivo é alterado.
        
        Args:
            event: Evento do Tkinter
        """
        self._carregar_series_ano()
    
    def _on_serie_changed(self, event=None) -> None:
        """
        Callback quando a série é alterada.
        
        Args:
            event: Evento do Tkinter
        """
        self._carregar_turmas()
    
    def _on_turma_changed(self, event=None) -> None:
        """
        Callback quando a turma é alterada.
        
        Args:
            event: Evento do Tkinter
        """
        self._carregar_dados()
    
    def _fechar_janela(self) -> None:
        """Fecha a janela e restaura a janela principal."""
        try:
            if self.janela_principal:
                self.janela_principal.deiconify()
            self.janela.destroy()
        except Exception as e:
            logger.error(f"Erro ao fechar janela: {e}")


def abrir_livros_faltantes(parent=None, janela_principal=None):
    """
    Função helper para abrir a janela de livros faltantes.
    
    Args:
        parent: Janela pai (não utilizado, mantido por compatibilidade)
        janela_principal: Janela principal do sistema (para esconder/mostrar)
    """
    try:
        # Se janela_principal não for passada, usar parent como fallback
        janela_ref = janela_principal if janela_principal else parent
        
        window = LivrosFaltantesWindow(janela_ref)
        window.janela.mainloop()
    except Exception as e:
        logger.error(f"Erro ao abrir janela de livros faltantes: {e}")
        from tkinter import messagebox
        messagebox.showerror("Erro", f"Erro ao abrir janela: {str(e)}")


def main():
    """Função principal para teste standalone."""
    root = tk.Tk()
    root.withdraw()
    app = LivrosFaltantesWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
