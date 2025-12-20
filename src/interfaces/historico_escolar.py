import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkinter.font import Font
import os
import sys
import re
import pandas as pd
from datetime import datetime, date
from src.utils.dates import formatar_data
from src.core.conexao import conectar_bd
from src.relatorios.historico_escolar import historico_escolar
from src.utils.utilitarios.escola_cache import get_escola_municipio
import time
from src.core.config_logs import get_logger

_logger = get_logger(__name__)

class InterfaceHistoricoEscolar:
    def __init__(self, janela=None, janela_pai=None):
        # Configuração da janela principal
        if janela:
            self.janela = janela
        else:
            self.janela = tk.Tk()
            self.janela.title("Gerenciamento de Histórico Escolar")
            self.janela.geometry("1200x700")
            
        # Armazenar referência da janela pai
        self.janela_pai = janela_pai
            
        # Inicializar aluno_id como None para evitar erros
        self.aluno_id = None
        self.historico_id = None
        
        # IDs do registro selecionado (para atualização)
        self.registro_disciplina_id = None
        self.registro_serie_id = None
        self.registro_ano_letivo_id = None
        self.registro_escola_id = None
        
        # Dicionários para mapear nomes para IDs
        self.disciplinas_map = {}
        self.series_map = {}
        self.anos_letivos_map = {}
        self.escolas_map = {}
        self.alunos_map = {}  # Novo dicionário para mapear nomes de alunos para seus IDs
        
        # Sistema de cache para melhorar performance
        self._cache_dados_estaticos = {}
        self._cache_alunos = {}
        self._cache_historico = {}
        self._cache_disciplinas_filtradas = {}
        self._cache_timestamp = None
        
        # Fonte para calcular largura de texto
        self.fonte_combobox = ("TkDefaultFont", 9)
        
        # Configurar estilo
        self.style = ttk.Style()
        self.style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        self.style.configure("Title.TLabel", font=("Arial", 10, "bold"))
        self.style.configure("Info.TLabel", font=("Arial", 9))
        self.style.configure("Success.TButton", background="#4CAF50", foreground="white")
        self.style.configure("Warning.TButton", background="#FFC107")
        self.style.configure("Danger.TButton", background="#F44336", foreground="white")
        
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
        
        # Configurar janela
        self.janela.configure(bg=self.co9)
        
        # Variável para armazenar a referência 
        self.mensagem_temporaria = None
        
        # Variáveis para armazenar os valores selecionados
        self.aluno_selecionado = tk.StringVar()
        self.aluno_data_nascimento = tk.StringVar()  # Nova variável para data de nascimento
        self.aluno_sexo = tk.StringVar()  # Nova variável para o sexo do aluno
        self.disciplina_selecionada = tk.StringVar()
        self.ano_letivo_selecionado = tk.StringVar()
        self.serie_selecionada = tk.StringVar()
        self.escola_selecionada = tk.StringVar()
        self.media = tk.StringVar()
        self.conceito = tk.StringVar()
        
        # Variáveis para filtragem
        self.filtro_ano = tk.StringVar()
        self.filtro_disciplina = tk.StringVar()
        self.filtro_situacao = tk.StringVar()
        
        # Criar os frames
        self.criar_frames()
        
        # Configurar tags para colorir linhas com base na situação
        self.treeview_historico.tag_configure('aprovado', foreground='#28a745')  # Verde
        self.treeview_historico.tag_configure('reprovado', foreground='#dc3545')  # Vermelho
        self.treeview_historico.tag_configure('hover', background='#d1e7f7')  # Azul claro quando passa o mouse
        
        # Carregar dados de forma assíncrona após a janela estar visível
        # Isso permite que a interface apareça rapidamente
        self.janela.after(100, self._carregar_dados_inicial)
        
        # Inicialmente, apenas a escola estará habilitada
        self.cb_serie.configure(state="disabled")
        self.cb_ano_letivo.configure(state="disabled")
        self.cb_disciplina.configure(state="disabled")
        
        # Vincular eventos
        self.cb_escola.bind("<<ComboboxSelected>>", self.ao_selecionar_escola)
        self.cb_serie.bind("<<ComboboxSelected>>", self.ao_selecionar_serie)
        self.cb_ano_letivo.bind("<<ComboboxSelected>>", self.ao_selecionar_ano_letivo)
        self.filtro_ano.trace_add("write", lambda *args: self.aplicar_filtros())
        self.filtro_disciplina.trace_add("write", lambda *args: self.aplicar_filtros())
        self.filtro_situacao.trace_add("write", lambda *args: self.aplicar_filtros())

    def formatar_data_nascimento(self, data_obj):
        """
        Formata data de nascimento de forma segura, tratando diferentes tipos de dados.
        
        Args:
            data_obj: Objeto de data que pode ser datetime, date, string ou None
            
        Returns:
            String formatada da data ou mensagem padrão
        """
        if data_obj is None:
            return "Não informada"
        try:
            return formatar_data(data_obj)
        except Exception as e:
            _logger.exception(f"Erro ao formatar data: {e}")
            return "Data inválida"

    def validar_conexao_bd(self):
        """
        Valida se a conexão com o banco de dados está funcionando.
        
        Returns:
            Connection object ou None se houver erro
        """
        try:
            conn = conectar_bd()
            if conn is None:
                messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                return None
            return conn
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao conectar ao banco de dados: {str(e)}")
            return None
    
    def _safe_float_format(self, value, decimals=1):
        """Converte um valor para float de forma segura e formata"""
        try:
            if value is None:
                return "N/A"
            float_val = float(value)
            return f"{float_val:.{decimals}f}"
        except (ValueError, TypeError):
            return "N/A"
    
    def _safe_float_value(self, value):
        """Converte um valor para float de forma segura"""
        try:
            if value is None:
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _safe_str_value(self, value):
        """Converte um valor para string de forma segura"""
        try:
            if value is None:
                return ""
            return str(value)
        except (ValueError, TypeError):
            return ""
    
    def _safe_sql_params(self, *params):
        """Converte parâmetros para formatos seguros para SQL"""
        safe_params = []
        for param in params:
            if param is None:
                safe_params.append(None)
            elif isinstance(param, (int, float, str)):
                safe_params.append(param)
            else:
                # Converter outros tipos para string ou int conforme necessário
                try:
                    # Tentar conversão para int primeiro
                    if str(param).isdigit():
                        safe_params.append(int(param))
                    else:
                        safe_params.append(str(param))
                except (ValueError, TypeError):
                    safe_params.append(str(param))
        return tuple(safe_params)
    
    def _verificar_cache_dados_estaticos(self):
        """Verifica se o cache de dados estáticos ainda é válido (5 minutos)"""
        if not self._cache_timestamp:
            return False
        
        from datetime import datetime, timedelta
        agora = datetime.now()
        tempo_limite = timedelta(minutes=5)
        
        return (agora - self._cache_timestamp) < tempo_limite
    
    def _obter_dados_cache_ou_bd(self):
        """Obtém dados do cache se válido, senão busca no banco"""
        if self._verificar_cache_dados_estaticos() and self._cache_dados_estaticos:
            return self._cache_dados_estaticos
        
        # Buscar do banco de dados
        conn = self.validar_conexao_bd()
        if conn is None:
            return None
        
        cursor = conn.cursor()
        dados = {}
        
        try:
            cursor.execute("START TRANSACTION")
            
            # Carregar dados estáticos em uma única consulta usando UNION ALL
            cursor.execute("""
                SELECT 'ano_letivo' as tipo, id, ano_letivo as nome, NULL as escola_id, NULL as nivel_id 
                FROM anosletivos 
                UNION ALL
                SELECT 'serie' as tipo, id, nome, NULL as escola_id, NULL as nivel_id 
                FROM series 
                UNION ALL
                SELECT 'escola' as tipo, id, nome, NULL as escola_id, NULL as nivel_id 
                FROM escolas 
                UNION ALL
                SELECT 'disciplina' as tipo, id, nome, escola_id, nivel_id 
                FROM disciplinas
                ORDER BY tipo, nome
            """)
            
            resultados = cursor.fetchall()
            
            # Processar resultados agrupados por tipo
            dados = {
                'anos_letivos': [],
                'series': [],
                'escolas': [],
                'disciplinas': []
            }
            
            for tipo, id, nome, escola_id, nivel_id in resultados:
                if tipo == 'ano_letivo':
                    dados['anos_letivos'].append((id, nome))
                elif tipo == 'serie':
                    dados['series'].append((id, nome))
                elif tipo == 'escola':
                    dados['escolas'].append((id, nome))
                elif tipo == 'disciplina':
                    dados['disciplinas'].append((id, nome, escola_id, nivel_id))
            
            cursor.execute("COMMIT")
            
            # Atualizar cache
            self._cache_dados_estaticos = dados
            from datetime import datetime
            self._cache_timestamp = datetime.now()
            
            return dados
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            _logger.exception(f"Erro ao carregar dados: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def _invalidar_cache_dados_estaticos(self):
        """Invalida o cache de dados estáticos"""
        self._cache_dados_estaticos.clear()
        self._cache_timestamp = None

    def criar_frames(self):
        # Frame de título com gradiente
        self.frame_titulo = tk.Frame(self.janela, bg=self.co7, height=60)
        self.frame_titulo.pack(fill=tk.X)
        
        # Título com ícone
        titulo_frame = tk.Frame(self.frame_titulo, bg=self.co7)
        titulo_frame.pack(pady=10)
        
        icone_label = tk.Label(titulo_frame, text="📚", font=("Arial", 20), bg=self.co7, fg=self.co1)
        icone_label.pack(side=tk.LEFT, padx=5)
        
        label_titulo = tk.Label(titulo_frame, text="GESTÃO DE HISTÓRICO ESCOLAR", 
                              font=("Arial", 16, "bold"), bg=self.co7, fg=self.co1)
        label_titulo.pack(side=tk.LEFT)
        
        # Adicionar bordas decorativas
        barra_decorativa = tk.Frame(self.janela, height=3, bg="#FFD700")  # Cor dourada
        barra_decorativa.pack(fill=tk.X, pady=(0, 5))
        
        # Frame mestre para conter pesquisa e filtros lado a lado
        frame_mestre = tk.Frame(self.janela)
        frame_mestre.pack(fill=tk.X, padx=10, pady=5)
        
        # Frame de pesquisa com visual moderno (agora dentro do frame mestre)
        self.frame_pesquisa = tk.LabelFrame(frame_mestre, text="Pesquisa de Aluno", 
                                    bg=self.co1, fg=self.co4, font=("Arial", 10, "bold"))
        self.frame_pesquisa.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Grid de pesquisa
        pesquisa_grid = tk.Frame(self.frame_pesquisa, bg=self.co1)
        pesquisa_grid.pack(padx=10, pady=5, fill=tk.X)
        
        # Pesquisa de aluno com combobox
        tk.Label(pesquisa_grid, text="Pesquisar Aluno:", bg=self.co1, 
                font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
                
        # Criar combobox para pesquisa de alunos
        self.cb_pesquisa_aluno = ttk.Combobox(pesquisa_grid, width=50, textvariable=self.aluno_selecionado)
        self.cb_pesquisa_aluno.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Adicionar binding para filtrar à medida que digita
        self.cb_pesquisa_aluno.bind("<KeyRelease>", self.filtrar_alunos)
        self.cb_pesquisa_aluno.bind("<<ComboboxSelected>>", self.selecionar_aluno)
        self.cb_pesquisa_aluno.bind("<Return>", self.selecionar_aluno)
        
        # Botão de pesquisa moderno
        btn_pesquisar = ttk.Button(pesquisa_grid, text="🔍 Pesquisar", 
                                 command=self.carregar_alunos, style="Success.TButton")
        btn_pesquisar.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Frame de filtros com visual moderno (agora dentro do frame mestre ao lado da pesquisa)
        self.frame_filtros = tk.LabelFrame(frame_mestre, text="Filtros", 
                                    bg=self.co1, fg=self.co4, font=("Arial", 10, "bold"))
        self.frame_filtros.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Grid de filtros
        filtros_grid = tk.Frame(self.frame_filtros, bg=self.co1)
        filtros_grid.pack(padx=10, pady=5, fill=tk.X)
        
        # Filtros adicionais
        tk.Label(filtros_grid, text="Ano Letivo:", bg=self.co1, 
                font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.cb_filtro_ano = ttk.Combobox(filtros_grid, textvariable=self.filtro_ano, width=15)
        self.cb_filtro_ano.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        tk.Label(filtros_grid, text="Disciplina:", bg=self.co1, 
                font=("Arial", 10)).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.cb_filtro_disciplina = ttk.Combobox(filtros_grid, textvariable=self.filtro_disciplina, width=20)
        self.cb_filtro_disciplina.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        tk.Label(filtros_grid, text="Situação:", bg=self.co1, 
                font=("Arial", 10)).grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.cb_filtro_situacao = ttk.Combobox(filtros_grid, textvariable=self.filtro_situacao, width=15)
        self.cb_filtro_situacao.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        
        # Botão para aplicar filtros
        btn_aplicar_filtros = ttk.Button(filtros_grid, text="Aplicar Filtros", 
                                       command=self.aplicar_filtros, style="Success.TButton")
        btn_aplicar_filtros.grid(row=0, column=6, padx=5, pady=5, sticky=tk.W)
        
        # Frame para o formulário de inserção
        self.frame_form = tk.LabelFrame(self.janela, text="Inserir/Editar Histórico", padx=10, pady=10)
        self.frame_form.pack(fill=tk.X, padx=10, pady=5)
        
        # Configurar o grid para distribuir o espaço igualmente
        for i in range(6):
            self.frame_form.columnconfigure(i, weight=1)
        
        # Formulário em grid - agora com informações detalhadas do aluno
        # Primeira linha - Informações completas do aluno
        tk.Label(self.frame_form, text="Aluno:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.lbl_aluno = tk.Label(self.frame_form, textvariable=self.aluno_selecionado)
        self.lbl_aluno.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        # Adicionar mais informações do aluno
        tk.Label(self.frame_form, text="Data Nascimento:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.lbl_data_nascimento = tk.Label(self.frame_form, textvariable=self.aluno_data_nascimento)
        self.lbl_data_nascimento.grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)
        
        tk.Label(self.frame_form, text="Sexo:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.lbl_sexo = tk.Label(self.frame_form, textvariable=self.aluno_sexo)
        self.lbl_sexo.grid(row=0, column=5, padx=5, pady=5, sticky=tk.EW)
        
        # Segunda linha - Campos essenciais agrupados
        # Escola (agora primeiro)
        tk.Label(self.frame_form, text="Escola:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.cb_escola = ttk.Combobox(self.frame_form, textvariable=self.escola_selecionada)
        self.cb_escola.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        self.cb_escola.bind("<<ComboboxSelected>>", self.ao_mudar_filtro)
        
        # Série (agora segundo)
        tk.Label(self.frame_form, text="Série:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.cb_serie = ttk.Combobox(self.frame_form, textvariable=self.serie_selecionada)
        self.cb_serie.grid(row=1, column=3, padx=5, pady=5, sticky=tk.EW)
        self.cb_serie.bind("<<ComboboxSelected>>", self.ao_mudar_filtro)
        
        # Ano Letivo
        tk.Label(self.frame_form, text="Ano Letivo:").grid(row=1, column=4, padx=5, pady=5, sticky=tk.W)
        self.cb_ano_letivo = ttk.Combobox(self.frame_form, textvariable=self.ano_letivo_selecionado)
        self.cb_ano_letivo.grid(row=1, column=5, padx=5, pady=5, sticky=tk.EW)
        self.cb_ano_letivo.bind("<<ComboboxSelected>>", self.ao_mudar_filtro)
        
        # Terceira linha - Disciplina, Média e Conceito juntos
        tk.Label(self.frame_form, text="Disciplina:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.cb_disciplina = ttk.Combobox(self.frame_form, textvariable=self.disciplina_selecionada)
        self.cb_disciplina.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)
        
        tk.Label(self.frame_form, text="Média:").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        self.ent_media = tk.Entry(self.frame_form, textvariable=self.media, width=10)
        self.ent_media.grid(row=2, column=3, padx=5, pady=5, sticky=tk.W)
        self.ent_media.bind("<Return>", self._inserir_com_enter)
        # Validação para aceitar apenas números e ponto decimal
        self.ent_media.bind("<KeyRelease>", self._validar_media)
        
        tk.Label(self.frame_form, text="Conceito:").grid(row=2, column=4, padx=5, pady=5, sticky=tk.W)
        self.ent_conceito = tk.Entry(self.frame_form, textvariable=self.conceito, width=10)
        self.ent_conceito.grid(row=2, column=5, padx=5, pady=5, sticky=tk.W)
        self.ent_conceito.bind("<Return>", self._inserir_com_enter)
        # Validação para aceitar apenas letras maiúsculas
        self.ent_conceito.bind("<KeyRelease>", self._validar_conceito)
        
        # Botões
        frame_botoes = tk.Frame(self.frame_form)
        frame_botoes.grid(row=3, column=0, columnspan=6, pady=10)
        
        btn_inserir = tk.Button(frame_botoes, text="Inserir", command=self.inserir_registro, bg=self.co3, fg=self.co1, width=15)
        btn_inserir.grid(row=0, column=0, padx=5)
        
        btn_atualizar = tk.Button(frame_botoes, text="Atualizar", command=self.atualizar_registro, bg=self.co7, fg=self.co1, width=15)
        btn_atualizar.grid(row=0, column=1, padx=5)
        
        btn_excluir = tk.Button(frame_botoes, text="Excluir", command=self.excluir_registro, bg=self.co6, fg=self.co1, width=15)
        btn_excluir.grid(row=0, column=2, padx=5)
        
        btn_limpar = tk.Button(frame_botoes, text="Limpar", command=lambda: self.limpar_campos(manter_serie_escola_ano=False), bg=self.co0, fg=self.co1, width=15)
        btn_limpar.grid(row=0, column=3, padx=5)
        
        btn_gerar_pdf = tk.Button(frame_botoes, text="Gerar PDF", command=self.gerar_pdf, bg=self.co5, fg=self.co1, width=15)
        btn_gerar_pdf.grid(row=0, column=4, padx=5)

        # Botões removidos: 'Relatório de Desempenho', 'Visualizar Matriz' e 'Importar Excel'
        # Foram removidos conforme solicitado. Ajustamos a posição dos botões seguintes.
        
        # Botão Voltar para a página principal (ajustado)
        btn_voltar = tk.Button(frame_botoes, text="Voltar", command=self.voltar_pagina_principal, bg="#FF9800", fg=self.co1, width=15)
        btn_voltar.grid(row=0, column=5, padx=5)
        
        # Adicionar botão para gerenciar observações (ajustado)
        btn_observacoes = tk.Button(frame_botoes, text="Observações", command=self.gerenciar_observacoes, bg=self.co5, fg=self.co1, width=15)
        btn_observacoes.grid(row=0, column=6, padx=5)
        
        # Botão para exportar para GEDUC (novo)
        btn_exportar_geduc = tk.Button(frame_botoes, text="Exportar GEDUC", command=self.exportar_para_geduc, bg="#FF5722", fg=self.co1, width=15)
        btn_exportar_geduc.grid(row=0, column=7, padx=5)
        
        # Frame para a tabela de histórico do aluno
        self.frame_historico = tk.LabelFrame(self.janela, text="Histórico do Aluno", padx=10, pady=10)
        self.frame_historico.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview para histórico
        colunas_historico = ["ID", "Disciplina", "Ano Letivo", "Série", "Escola", "Média", "Conceito"]
        self.treeview_historico = ttk.Treeview(self.frame_historico, columns=colunas_historico, show="headings", height=10)
        
        # Definindo os cabeçalhos
        for col in colunas_historico:
            self.treeview_historico.heading(col, text=col, anchor=tk.CENTER)
            self.treeview_historico.column(col, width=100, anchor=tk.CENTER)
        
        # Ajustando o tamanho das colunas
        self.treeview_historico.column("ID", width=50, minwidth=50)
        self.treeview_historico.column("Disciplina", width=200, minwidth=150, anchor=tk.W)
        self.treeview_historico.column("Ano Letivo", width=80, minwidth=80)
        self.treeview_historico.column("Série", width=120, minwidth=100, anchor=tk.W)
        self.treeview_historico.column("Escola", width=200, minwidth=150, anchor=tk.W)
        self.treeview_historico.column("Média", width=70, minwidth=70)
        self.treeview_historico.column("Conceito", width=70, minwidth=70)
        
        # Configurar estilo para cores alternadas nas linhas e outros aprimoramentos
        style = ttk.Style()
        style.configure("Treeview", 
                      font=('Arial', 10),
                      rowheight=25,
                      background="#f0f0f0",
                      fieldbackground="#f0f0f0")
        
        style.configure("Treeview.Heading", 
                      font=('Arial', 10, 'bold'),
                      background="#3c7fb1", 
                      foreground="white")
                      
        # Cores alternadas nas linhas da treeview
        style.map('Treeview', 
                background=[('selected', '#308014'), ('alternate', '#e9e9e9')])
        
        # Scrollbar para o histórico
        scrollbar_historico = ttk.Scrollbar(self.frame_historico, orient="vertical", command=self.treeview_historico.yview)
        self.treeview_historico.configure(yscrollcommand=scrollbar_historico.set)
        scrollbar_historico.pack(side=tk.RIGHT, fill=tk.Y)
        self.treeview_historico.pack(fill=tk.BOTH, expand=True)
        
        # Bind para seleção de histórico
        self.treeview_historico.bind("<ButtonRelease-1>", self.selecionar_historico)
        
        # Bind para cores alternadas nas linhas
        self.treeview_historico.bind("<Map>", self._configurar_cores_alternadas)

    def _carregar_dados_inicial(self):
        """Carrega dados iniciais de forma assíncrona após a interface estar visível"""
        try:
            # Carregar dados estáticos (anos letivos, séries, escolas, disciplinas)
            self.carregar_dados()
        except Exception as e:
            _logger.exception(f"Erro ao carregar dados iniciais: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao carregar dados iniciais: {str(e)}")
    
    def ajustar_largura_combobox(self, combobox, valores, largura_minima=10, largura_maxima=50, padding=3):
        """
        Ajusta a largura de um combobox com base no conteúdo mais longo.
        
        Args:
            combobox: O widget ttk.Combobox a ser ajustado
            valores: Lista de valores que serão exibidos no combobox
            largura_minima: Largura mínima do combobox (em caracteres)
            largura_maxima: Largura máxima do combobox (em caracteres)
            padding: Padding adicional para garantir que o texto seja exibido completamente
        """
        if not valores:
            combobox.config(width=largura_minima)
            return
        
        # Considerar também os valores atuais do combobox, para não diminuir a largura se já houver valores longos
        valores_atuais = combobox['values']
        
        # Combinar os valores atuais com os novos valores para cálculo da largura
        todos_valores = list(valores)
        if valores_atuais:
            todos_valores.extend(valores_atuais)
            
        # Adiciona o valor atual selecionado na combobox, se houver
        valor_atual = combobox.get()
        if valor_atual and valor_atual not in todos_valores:
            todos_valores.append(valor_atual)
            
        # Cria um objeto de fonte para calcular a largura do texto
        font = self.fonte_combobox
        
        # Encontra o item mais longo no combobox
        largura_maxima_texto = max(len(str(item)) for item in todos_valores if item)
        
        # Adiciona padding para garantir que o texto seja exibido completamente
        largura_ajustada = min(max(largura_maxima_texto + padding, largura_minima), largura_maxima)
        
        # Configura a largura do combobox
        combobox.config(width=largura_ajustada)

    def carregar_dados(self):
        """Carrega dados estáticos usando cache para melhor performance"""
        # Tentar obter dados do cache primeiro
        dados = self._obter_dados_cache_ou_bd()
        if dados is None:
            messagebox.showerror("Erro", "Erro ao carregar dados do sistema.")
            return
        
        try:
            # Usar threading para não bloquear a interface durante processamento
            # Processar anos letivos
            anos_letivos = dados['anos_letivos']
            anos_letivos.sort(key=lambda x: x[1], reverse=True)  # Ordenar por ano decrescente
            self.anos_letivos_map = {str(ano): id for id, ano in anos_letivos}
            anos_letivos_valores = [str(ano) for id, ano in anos_letivos]
            self.cb_ano_letivo['values'] = anos_letivos_valores
            
            # Processar séries
            series = dados['series']
            series.sort(key=lambda x: x[1])  # Ordenar por nome
            self.series_map = {nome: id for id, nome in series}
            series_valores = [nome for id, nome in series]
            self.cb_serie['values'] = series_valores
            
            # Processar escolas com melhor tratamento de duplicatas
            escolas = dados['escolas']
            escolas.sort(key=lambda x: (x[1], x[0]))  # Ordenar por nome, depois por id
            self.escolas_map = {}
            escolas_valores = []
            nomes_vistos = {}
            
            for id, nome in escolas:
                # Contar quantas vezes este nome já apareceu
                if nome in nomes_vistos:
                    nomes_vistos[nome] += 1
                    nome_com_id = f"{nome} (ID: {id})"
                    escolas_valores.append(nome_com_id)
                    self.escolas_map[nome_com_id] = id
                    # Se for a segunda ocorrência, também atualizar a primeira
                    if nomes_vistos[nome] == 2:
                        # Encontrar o primeiro item e atualizá-lo
                        for i, valor in enumerate(escolas_valores):
                            if valor == nome:
                                primeiro_id = self.escolas_map[nome]
                                novo_nome = f"{nome} (ID: {primeiro_id})"
                                escolas_valores[i] = novo_nome
                                del self.escolas_map[nome]
                                self.escolas_map[novo_nome] = primeiro_id
                                break
                else:
                    nomes_vistos[nome] = 1
                    escolas_valores.append(nome)
                    self.escolas_map[nome] = id
            
            self.cb_escola['values'] = escolas_valores
            
            # Processar disciplinas
            disciplinas = dados['disciplinas']
            disciplinas.sort(key=lambda x: x[1])  # Ordenar por nome
            self.disciplinas_map = {nome: id for id, nome, escola_id, nivel_id in disciplinas}
            # Armazenar também mapeamento completo para uso posterior
            self.disciplinas_completo = {id: {'nome': nome, 'escola_id': escola_id, 'nivel_id': nivel_id} 
                                       for id, nome, escola_id, nivel_id in disciplinas}
            disciplinas_valores = [nome for id, nome, escola_id, nivel_id in disciplinas]
            self.cb_disciplina['values'] = disciplinas_valores
            
            # Ajustar larguras após carregamento (não bloqueia muito)
            self.janela.after(50, lambda: self._ajustar_larguras_comboboxes(
                anos_letivos_valores, series_valores, escolas_valores, disciplinas_valores))
            
            # Carregar alunos em separado (pode ser lazy loaded)
            # Não carregar na inicialização, apenas quando necessário
            # self.carregar_alunos_otimizado()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar dados: {str(e)}")
            _logger.exception(f"Erro ao processar dados: {str(e)}")
    
    def _ajustar_larguras_comboboxes(self, anos_valores, series_valores, escolas_valores, disciplinas_valores):
        """Ajusta larguras de comboboxes de forma não bloqueante"""
        try:
            self.ajustar_largura_combobox(self.cb_ano_letivo, anos_valores)
            self.ajustar_largura_combobox(self.cb_serie, series_valores)
            self.ajustar_largura_combobox(self.cb_escola, escolas_valores)
            self.ajustar_largura_combobox(self.cb_disciplina, disciplinas_valores)
        except Exception as e:
            _logger.exception(f"Erro ao ajustar larguras: {str(e)}")

    def carregar_alunos_otimizado(self):
        """Carrega a lista de alunos para a combobox de forma otimizada"""
        # Não carregar automaticamente, será carregado quando o usuário focar no campo
        # Isso economiza tempo na inicialização
        
        # Configurar binding para carregar alunos quando necessário
        if not hasattr(self, '_alunos_carregados'):
            self._alunos_carregados = False
            # Adicionar binding para carregar apenas quando o usuário focar no campo
            self.cb_pesquisa_aluno.bind("<FocusIn>", self._carregar_alunos_lazy, add="+")
    
    def _carregar_alunos_lazy(self, event=None):
        """Carrega alunos apenas quando necessário (lazy loading)"""
        if self._alunos_carregados:
            return
        
        # Conectar ao banco
        conn = self.validar_conexao_bd()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        try:
            # Carregar apenas os alunos mais recentemente acessados e ativos
            # Usar índice no nome para busca rápida
            cursor.execute("""
                SELECT id, nome, data_nascimento, sexo
                FROM alunos
                WHERE nome IS NOT NULL AND nome != ''
                ORDER BY nome
                LIMIT 50
            """)
            
            alunos = cursor.fetchall()
            self.alunos_map = {}
            self.alunos_info = {}
            
            # Criar lista de nomes para a combobox e mapear nomes para informações completas
            alunos_valores = []
            for aluno_id, nome, data_nascimento, sexo in alunos:
                if nome:  # Verificar se o nome não é nulo
                    alunos_valores.append(nome)
                    self.alunos_map[nome] = aluno_id
                    
                    # Formatar data de nascimento de forma mais eficiente
                    data_formatada = self.formatar_data_nascimento(data_nascimento)
                    
                    # Armazenar informações completas do aluno
                    self.alunos_info[nome] = (aluno_id, data_formatada, sexo)
            
            # Atualizar combobox com valores
            self.cb_pesquisa_aluno['values'] = alunos_valores
            self.ajustar_largura_combobox(self.cb_pesquisa_aluno, alunos_valores)
            
            self._alunos_carregados = True
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar alunos: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def carregar_alunos(self):
        """Mantém compatibilidade com código existente"""
        return self.carregar_alunos_otimizado()

    def filtrar_alunos(self, event=None):
        """Filtra a lista de alunos na combobox conforme o usuário digita - versão otimizada"""
        # Ignorar eventos de navegação que não devem acionar filtragem
        if event and event.keysym in ['Down', 'Up', 'Left', 'Right', 'Tab', 'Return']:
            return
        
        # Importante: guardar o texto atual e posição do cursor
        texto_atual = self.cb_pesquisa_aluno.get()
        try:
            pos_cursor = self.cb_pesquisa_aluno.index("insert")
        except:
            pos_cursor = len(texto_atual)
        
        texto_digitado = texto_atual.lower().strip()
        
        # Se não houver texto suficiente, carregar lista padrão
        if len(texto_digitado) < 2:
            self.carregar_alunos_otimizado()
            return
        
        # Usar cache para evitar consultas repetitivas
        cache_key = f"alunos_filtro_{texto_digitado}"
        if hasattr(self, '_cache_alunos') and cache_key in self._cache_alunos:
            self._aplicar_resultados_alunos(self._cache_alunos[cache_key], texto_atual, pos_cursor)
            return
        
        # Conectar ao banco
        conn = self.validar_conexao_bd()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        try:
            # Usar busca mais eficiente com múltiplas condições
            # Priorizar correspondências exatas no início do nome
            cursor.execute("""
                (SELECT id, nome, data_nascimento, sexo, 1 as prioridade
                 FROM alunos
                 WHERE nome LIKE %s AND nome IS NOT NULL
                 ORDER BY nome
                 LIMIT 25)
                UNION ALL
                (SELECT id, nome, data_nascimento, sexo, 2 as prioridade
                 FROM alunos
                 WHERE nome LIKE %s AND nome NOT LIKE %s AND nome IS NOT NULL
                 ORDER BY nome
                 LIMIT 25)
                ORDER BY prioridade, nome
            """, (f"{texto_digitado}%", f"%{texto_digitado}%", f"{texto_digitado}%"))
            
            alunos = cursor.fetchall()
            
            # Processar resultados
            resultados = []
            for aluno_id, nome, data_nascimento, sexo, prioridade in alunos:
                if nome:  # Verificar se o nome não é nulo
                    data_formatada = self.formatar_data_nascimento(data_nascimento)
                    resultados.append((aluno_id, nome, data_formatada, sexo))
            
            # Armazenar no cache
            if not hasattr(self, '_cache_alunos'):
                self._cache_alunos = {}
            # Limitar tamanho do cache
            if len(self._cache_alunos) > 50:
                self._cache_alunos.clear()
            self._cache_alunos[cache_key] = resultados
            
            # Aplicar resultados
            self._aplicar_resultados_alunos(resultados, texto_atual, pos_cursor)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao filtrar alunos: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    def _aplicar_resultados_alunos(self, resultados, texto_atual, pos_cursor):
        """Aplica os resultados da busca de alunos na interface"""
        try:
            self.alunos_map = {}
            self.alunos_info = {}
            
            # Criar lista de nomes para a combobox e mapear informações
            alunos_valores = []
            for aluno_id, nome, data_formatada, sexo in resultados:
                alunos_valores.append(nome)
                self.alunos_map[nome] = aluno_id
                self.alunos_info[nome] = (aluno_id, data_formatada, sexo)
            
            # Atualizar lista de valores e restaurar o texto digitado pelo usuário
            estado_anterior = self.cb_pesquisa_aluno["state"]
            
            # Configure para estado normal para modificar
            self.cb_pesquisa_aluno["state"] = "normal"
            
            # Atualize a lista de valores
            self.cb_pesquisa_aluno['values'] = alunos_valores
            
            # Restaure o texto que estava sendo digitado
            self.cb_pesquisa_aluno.delete(0, "end")
            self.cb_pesquisa_aluno.insert(0, texto_atual)
            
            # Restaure a posição do cursor
            try:
                self.cb_pesquisa_aluno.icursor(pos_cursor)
            except:
                pass
            
            # Restaure o estado anterior
            self.cb_pesquisa_aluno["state"] = estado_anterior
            
        except Exception as e:
            _logger.exception(f"Erro ao aplicar resultados: {str(e)}")

    def selecionar_aluno(self, event=None):
        """Função chamada quando um aluno é selecionado na combobox"""
        try:
            nome_aluno = self.aluno_selecionado.get()
            
            if not nome_aluno or nome_aluno not in self.alunos_map:
                return
                    
            # Obter ID do aluno e informações adicionais
            self.aluno_id = self.alunos_map[nome_aluno]
            
            # Verificar se temos as informações completas do aluno
            if nome_aluno in self.alunos_info:
                _, data_nascimento, sexo = self.alunos_info[nome_aluno]
                self.aluno_data_nascimento.set(data_nascimento)
                self.aluno_sexo.set(sexo)
            else:
                # Se não tivermos, buscar do banco de dados
                conn = self.validar_conexao_bd()
                if conn is None:
                    return
                
                cursor = conn.cursor()
                
                try:
                    cursor.execute("""
                        SELECT data_nascimento, sexo
                        FROM alunos
                        WHERE id = %s
                    """, (self.aluno_id,))
                    
                    resultado = cursor.fetchone()
                    if resultado:
                        data_nascimento, sexo = resultado
                        data_formatada = self.formatar_data_nascimento(data_nascimento)
                        self.aluno_data_nascimento.set(data_formatada)
                        self.aluno_sexo.set(str(sexo) if sexo else "")
                except Exception as e:
                    _logger.exception(f"Erro ao buscar detalhes do aluno: {str(e)}")
                finally:
                    cursor.close()
                    conn.close()
            
            # Limpar os campos e desativar os comboboxes que dependem da seleção prévia
            self.limpar_campos(manter_aluno=True, manter_serie_escola_ano=False)
            
            # Habilitar outros controles após seleção
            self.cb_escola.configure(state="readonly")
            self.cb_serie.configure(state="disabled")
            self.cb_ano_letivo.configure(state="disabled")
            self.cb_disciplina.configure(state="disabled")
            
            # Carregar o histórico do aluno
            self.carregar_historico()
        except Exception as e:
            _logger.exception(f"Erro ao selecionar aluno: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao selecionar aluno: {str(e)}")
            # Não propagar o erro
            return "break"

    def _formatar_registro_historico(self, registro):
        """
        Função auxiliar para formatar um registro do histórico para a treeview.
        
        Args:
            registro: Tupla contendo os dados do registro
            
        Returns:
            Tupla de valores formatados para inserção na treeview
        """
        # Tratamento de valores nulos e formatação adequada
        id_historico = str(registro[0]) if registro[0] is not None else ""
        disciplina = registro[1] if registro[1] is not None else ""
        ano_letivo = str(registro[2]) if registro[2] is not None else ""
        serie = registro[3] if registro[3] is not None else ""
        escola = registro[4] if registro[4] is not None else ""
        
        # Formatar média com 1 casa decimal apenas se não for nula
        media_valor = None
        if registro[5] is not None:
            try:
                media_valor = float(registro[5])
                media = f"{media_valor:.1f}"
            except (ValueError, TypeError):
                media = ""
                media_valor = None
        else:
            media = ""
            
        conceito = registro[6] if registro[6] is not None else ""
        
        # Determinar a situação do aluno (aprovado ou reprovado)
        situacao = None
        if media_valor is not None:
            situacao = "aprovado" if media_valor >= 6 else "reprovado"
        elif conceito:
            if conceito in ['AD', 'PNAD', 'APNAD']:
                situacao = "aprovado"
            elif conceito == 'RT':
                situacao = "reprovado"
                
        # O ID do registro será usado como tag para aplicar estilos específicos na linha
        return (id_historico, disciplina, ano_letivo, serie, escola, media, conceito, situacao)
        
    def carregar_historico(self):
        """Carrega o histórico do aluno de forma otimizada"""
        # Limpar a treeview
        for i in self.treeview_historico.get_children():
            self.treeview_historico.delete(i)
            
        # Verificar se há um aluno selecionado
        if not hasattr(self, 'aluno_id') or not self.aluno_id:
            return
            
        # Verificar cache primeiro
        cache_key = f"historico_{self.aluno_id}"
        if hasattr(self, '_cache_historico') and cache_key in self._cache_historico:
            cached_data = self._cache_historico[cache_key]
            self._aplicar_dados_historico(cached_data['resultados'], cached_data['anos_letivos'], cached_data['disciplinas'])
            return
            
        # Conectar ao banco
        conn = self.validar_conexao_bd()
        if conn is None:
            return
            
        cursor = conn.cursor()
        
        try:
            # Consulta SQL otimizada com índices compostos - removido LIMIT desnecessário
            # Usar STRAIGHT_JOIN para forçar ordem específica de join (se suportado pelo MySQL)
            cursor.execute("""
                SELECT /*+ USE_INDEX(h, idx_aluno_historico) */
                    h.id, 
                    d.nome AS disciplina, 
                    al.ano_letivo, 
                    s.nome AS serie, 
                    e.nome AS escola, 
                    h.media, 
                    h.conceito,
                    h.disciplina_id, 
                    h.ano_letivo_id, 
                    h.serie_id, 
                    h.escola_id
                FROM historico_escolar h
                INNER JOIN disciplinas d ON h.disciplina_id = d.id
                INNER JOIN anosletivos al ON h.ano_letivo_id = al.id
                INNER JOIN series s ON h.serie_id = s.id
                INNER JOIN escolas e ON h.escola_id = e.id
                WHERE h.aluno_id = %s
                ORDER BY al.ano_letivo DESC, s.id, d.nome
            """, (self.aluno_id,))
            
            resultados = cursor.fetchall()
            
            # Processar dados de forma mais eficiente
            anos_letivos = set()
            disciplinas = set()
            dados_processados = []
            
            # Processar todos os registros em uma única passada
            for registro in resultados:
                # Formatar os dados para exibição
                valores_formatados = self._formatar_registro_historico(registro)
                dados_processados.append((registro, valores_formatados))
                
                # Coletar valores únicos para filtros
                ano_letivo = valores_formatados[2]
                disciplina = valores_formatados[1]
                if ano_letivo:
                    anos_letivos.add(ano_letivo)
                if disciplina:
                    disciplinas.add(disciplina)
            
            # Armazenar no cache
            if not hasattr(self, '_cache_historico'):
                self._cache_historico = {}
            # Limitar tamanho do cache
            if len(self._cache_historico) > 10:
                # Remove o mais antigo
                oldest_key = next(iter(self._cache_historico))
                del self._cache_historico[oldest_key]
                
            self._cache_historico[cache_key] = {
                'resultados': dados_processados,
                'anos_letivos': anos_letivos,
                'disciplinas': disciplinas,
                'timestamp': datetime.now()
            }
            
            # Aplicar dados na interface
            self._aplicar_dados_historico(dados_processados, anos_letivos, disciplinas)
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar histórico: {str(e)}")
            _logger.exception(f"Erro ao carregar histórico: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    def _aplicar_dados_historico(self, dados_processados, anos_letivos, disciplinas):
        """Aplica os dados do histórico na interface de forma otimizada"""
        try:
            # Inserir os resultados na treeview de forma otimizada
            items_para_inserir = []
            
            for registro, valores_formatados in dados_processados:
                # Obter valores a serem mostrados (excluindo a situação)
                valores_display = valores_formatados[:-1]
                
                # Obter situação para definir a tag
                situacao = valores_formatados[-1]
                tags = [str(registro[0])]
                
                if situacao:
                    tags.append(situacao)
                
                items_para_inserir.append((valores_display, tags))
            
            # Inserir todos os itens de uma vez (mais eficiente)
            for valores_display, tags in items_para_inserir:
                self.treeview_historico.insert("", "end", values=valores_display, tags=tags)
            
            # Atualizar os comboboxes de filtro
            anos_valores = ['Todos'] + sorted(anos_letivos, reverse=True)
            disciplinas_valores = ['Todas'] + sorted(disciplinas)
            situacoes_valores = ['Todos', 'Aprovado', 'Reprovado', 'Em Andamento']
            
            self.cb_filtro_ano['values'] = anos_valores
            self.cb_filtro_disciplina['values'] = disciplinas_valores
            self.cb_filtro_situacao['values'] = situacoes_valores
            
            # Ajustar largura dos comboboxes de filtro
            self.ajustar_largura_combobox(self.cb_filtro_ano, anos_valores)
            self.ajustar_largura_combobox(self.cb_filtro_disciplina, disciplinas_valores)
            self.ajustar_largura_combobox(self.cb_filtro_situacao, situacoes_valores)
            
            # Configurar valores padrão dos filtros se necessário
            if not self.filtro_ano.get():
                self.filtro_ano.set('Todos')
            if not self.filtro_disciplina.get():
                self.filtro_disciplina.set('Todas')
            if not self.filtro_situacao.get():
                self.filtro_situacao.set('Todos')
                
        except Exception as e:
            _logger.exception(f"Erro ao aplicar dados do histórico: {str(e)}")
    
    def invalidar_cache_historico(self, aluno_id=None):
        """Invalida o cache do histórico quando há alterações"""
        if not hasattr(self, '_cache_historico'):
            return
            
        if aluno_id:
            cache_key = f"historico_{aluno_id}"
            if cache_key in self._cache_historico:
                del self._cache_historico[cache_key]
        else:
            # Limpar todo o cache
            self._cache_historico.clear()

    def selecionar_historico(self, event):
        # Obter o item selecionado
        item = self.treeview_historico.selection()
        if not item:
            return
            
        # Obter os valores do item (pegar o primeiro item da seleção)
        valores = self.treeview_historico.item(item[0], "values")
        
        # Guardar o ID do histórico
        try:
            self.historico_id = int(valores[0])
        except (ValueError, TypeError, IndexError):
            messagebox.showerror("Erro", "ID do histórico inválido.")
            return
        
        # Conectar ao banco para buscar dados completos
        conn = self.validar_conexao_bd()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        try:
            # Buscar dados completos do histórico
            cursor.execute("""
                SELECT h.id, h.disciplina_id, d.nome AS disciplina_nome, h.media, 
                       h.ano_letivo_id, a.ano_letivo AS ano_letivo_nome,
                       h.serie_id, s.nome AS serie_nome,
                       h.escola_id, e.nome AS escola_nome,
                       h.conceito
                FROM historico_escolar h
                LEFT JOIN disciplinas d ON h.disciplina_id = d.id
                LEFT JOIN anosletivos a ON h.ano_letivo_id = a.id
                LEFT JOIN series s ON h.serie_id = s.id
                LEFT JOIN escolas e ON h.escola_id = e.id
                WHERE h.id = %s
            """, (self.historico_id,))
            
            resultado = cursor.fetchone()
            
            if not resultado:
                messagebox.showerror("Erro", "Registro não encontrado.")
                return
                
            # Habilitar todos os campos para edição
            self.cb_escola.configure(state="normal")
            self.cb_serie.configure(state="normal")
            self.cb_ano_letivo.configure(state="normal")
            self.cb_disciplina.configure(state="normal")
            
            # Armazenar os IDs do registro selecionado para uso na atualização
            self.registro_disciplina_id = resultado[1]  # disciplina_id
            self.registro_serie_id = resultado[6]  # serie_id
            self.registro_ano_letivo_id = resultado[4]  # ano_letivo_id
            self.registro_escola_id = resultado[8]  # escola_id
            
            # Preencher os campos
            self.escola_selecionada.set(str(resultado[9]) if resultado[9] else "")  # Nome da escola
            self.serie_selecionada.set(str(resultado[7]) if resultado[7] else "")  # Nome da série
            self.ano_letivo_selecionado.set(str(resultado[5]) if resultado[5] else "")  # Ano letivo
            self.disciplina_selecionada.set(str(resultado[2]) if resultado[2] else "")  # Nome da disciplina
            
            # Ajustar a largura dos comboboxes com base no item selecionado
            self.ajustar_largura_combobox(self.cb_escola, [str(resultado[9]) if resultado[9] else ""])
            self.ajustar_largura_combobox(self.cb_serie, [str(resultado[7]) if resultado[7] else ""])
            self.ajustar_largura_combobox(self.cb_ano_letivo, [str(resultado[5]) if resultado[5] else ""])
            self.ajustar_largura_combobox(self.cb_disciplina, [str(resultado[2]) if resultado[2] else ""])
            
            # Preencher média e conceito
            self.media.set(f"{resultado[3]:.1f}" if resultado[3] is not None else "")
            self.conceito.set(str(resultado[10]) if resultado[10] else "")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar detalhes do histórico: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def obter_ids_dos_campos(self):
        # Disciplina
        disciplina_texto = self.disciplina_selecionada.get()
        disciplina_id = self.disciplinas_map.get(disciplina_texto) if disciplina_texto else None
        if disciplina_id is not None:
            try:
                disciplina_id = int(str(disciplina_id))
            except (ValueError, TypeError):
                disciplina_id = None
            
        # Série
        serie_texto = self.serie_selecionada.get()
        serie_id = self.series_map.get(serie_texto) if serie_texto else None
        if serie_id is not None:
            try:
                serie_id = int(str(serie_id))
            except (ValueError, TypeError):
                serie_id = None
            
        # Ano Letivo
        ano_letivo_texto = self.ano_letivo_selecionado.get()
        ano_letivo_id = self.anos_letivos_map.get(ano_letivo_texto) if ano_letivo_texto else None
        if ano_letivo_id is not None:
            try:
                ano_letivo_id = int(str(ano_letivo_id))
            except (ValueError, TypeError):
                ano_letivo_id = None
            
        # Escola
        escola_texto = self.escola_selecionada.get()
        escola_id = self.escolas_map.get(escola_texto) if escola_texto else None
        if escola_id is not None:
            try:
                escola_id = int(str(escola_id))
            except (ValueError, TypeError):
                escola_id = None
            
        return disciplina_id, serie_id, ano_letivo_id, escola_id

    def inserir_registro(self):
        # Verificar se há um aluno selecionado
        if not hasattr(self, 'aluno_id') or not self.aluno_id:
            messagebox.showerror("Erro", "Selecione um aluno primeiro.")
            return
            
        # Validação dos campos em ordem hierárquica
        # 1. Verificar escola
        escola_texto = self.escola_selecionada.get()
        if not escola_texto:
            messagebox.showerror("Erro", "Selecione uma escola.")
            self.cb_escola.focus_set()
            return
            
        # 2. Verificar série
        serie_texto = self.serie_selecionada.get()
        if not serie_texto:
            messagebox.showerror("Erro", "Selecione uma série.")
            self.cb_serie.focus_set()
            return
            
        # 3. Verificar ano letivo
        ano_texto = self.ano_letivo_selecionado.get()
        if not ano_texto:
            messagebox.showerror("Erro", "Selecione um ano letivo.")
            self.cb_ano_letivo.focus_set()
            return
            
        # 4. Verificar disciplina
        disciplina_texto = self.disciplina_selecionada.get()
        if not disciplina_texto:
            messagebox.showerror("Erro", "Selecione uma disciplina.")
            self.cb_disciplina.focus_set()
            return
            
        # Validação da média
        media_texto = self.media.get().strip()
        if media_texto:
            try:
                media_valor = float(media_texto.replace(',', '.'))
            except ValueError:
                messagebox.showerror("Erro", "A média deve ser um número válido.")
                return
        else:
            media_valor = None
        
        # Conceito (opcional)
        conceito = self.conceito.get().strip()
        
        # Obter IDs dos campos
        try:
            disciplina_id, serie_id, ano_letivo_id, escola_id = self.obter_ids_dos_campos()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter IDs dos campos: {str(e)}")
            return
            
        # Verificar se já existe um registro para esta combinação
        conn = self.validar_conexao_bd()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id FROM historico_escolar
                WHERE aluno_id = %s AND disciplina_id = %s AND serie_id = %s 
                AND ano_letivo_id = %s AND escola_id = %s
            """, (self.aluno_id, disciplina_id, serie_id, ano_letivo_id, escola_id))
            
            if cursor.fetchone():
                messagebox.showerror("Erro", "Já existe um registro para esta combinação de aluno, disciplina, série, ano letivo e escola.")
                return
                
            # Inserir no banco de dados
            cursor.execute("""
                INSERT INTO historico_escolar 
                (aluno_id, disciplina_id, serie_id, ano_letivo_id, escola_id, media, conceito)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (self.aluno_id, disciplina_id, serie_id, ano_letivo_id, escola_id, media_valor, conceito))
            
            conn.commit()
            self.mostrar_mensagem_temporaria("Registro inserido com sucesso!")
            
            # Invalidar caches relacionados
            self.invalidar_cache_historico(self.aluno_id)
            self.invalidar_cache_filtros(self.aluno_id)
            self.invalidar_cache_disciplinas(self.aluno_id)
            
            # Recarregar histórico
            self.carregar_historico()
            
            # Limpar apenas os campos de disciplina, média e conceito, mantendo aluno, escola, série e ano letivo
            self.disciplina_selecionada.set("")
            self.media.set("")
            self.conceito.set("")
            self.historico_id = None
            
            # Definir o foco no campo de disciplina
            self.cb_disciplina.focus_set()
            
            # Atualizar disciplinas disponíveis após inserção
            self.atualizar_disciplinas()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Erro ao inserir registro: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def atualizar_registro(self):
        # Verificar se há um registro selecionado
        if not hasattr(self, 'historico_id') or not self.historico_id:
            messagebox.showerror("Erro", "Selecione um registro para atualizar.")
            return
            
        # Validação dos campos em ordem hierárquica
        # 1. Verificar escola
        escola_texto = self.escola_selecionada.get()
        if not escola_texto:
            messagebox.showerror("Erro", "Selecione uma escola.")
            self.cb_escola.focus_set()
            return
            
        # 2. Verificar série
        serie_texto = self.serie_selecionada.get()
        if not serie_texto:
            messagebox.showerror("Erro", "Selecione uma série.")
            self.cb_serie.focus_set()
            return
            
        # 3. Verificar ano letivo
        ano_texto = self.ano_letivo_selecionado.get()
        if not ano_texto:
            messagebox.showerror("Erro", "Selecione um ano letivo.")
            self.cb_ano_letivo.focus_set()
            return
            
        # 4. Verificar disciplina
        disciplina_texto = self.disciplina_selecionada.get()
        if not disciplina_texto:
            messagebox.showerror("Erro", "Selecione uma disciplina.")
            self.cb_disciplina.focus_set()
            return
            
        # Validação da média
        media_texto = self.media.get().strip()
        if media_texto:
            try:
                media_valor = float(media_texto.replace(',', '.'))
            except ValueError:
                messagebox.showerror("Erro", "A média deve ser um número válido.")
                return
        else:
            media_valor = None
        
        # Conceito (opcional)
        conceito = self.conceito.get().strip()
        
        # Usar os IDs armazenados do registro selecionado, ou buscar dos mapas se o usuário alterou
        # Verificar se os campos foram alterados comparando com os valores do mapa
        disciplina_texto = self.disciplina_selecionada.get()
        serie_texto = self.serie_selecionada.get()
        ano_texto = self.ano_letivo_selecionado.get()
        escola_texto = self.escola_selecionada.get()
        
        # Tentar obter IDs dos mapas primeiro (caso o usuário tenha alterado)
        disciplina_id = self.disciplinas_map.get(disciplina_texto)
        serie_id = self.series_map.get(serie_texto)
        ano_letivo_id = self.anos_letivos_map.get(ano_texto)
        escola_id = self.escolas_map.get(escola_texto)
        
        # Se não encontrar no mapa, usar os IDs armazenados do registro selecionado
        if disciplina_id is None and hasattr(self, 'registro_disciplina_id'):
            disciplina_id = self.registro_disciplina_id
        if serie_id is None and hasattr(self, 'registro_serie_id'):
            serie_id = self.registro_serie_id
        if ano_letivo_id is None and hasattr(self, 'registro_ano_letivo_id'):
            ano_letivo_id = self.registro_ano_letivo_id
        if escola_id is None and hasattr(self, 'registro_escola_id'):
            escola_id = self.registro_escola_id
        
        # Validar se todos os IDs foram obtidos
        if not all([disciplina_id, serie_id, ano_letivo_id, escola_id]):
            messagebox.showerror("Erro", "Não foi possível obter os IDs dos campos. Por favor, selecione novamente os valores.")
            return
            
        # Verificar se já existe outro registro para esta combinação
        conn = self.validar_conexao_bd()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id FROM historico_escolar
                WHERE aluno_id = %s AND disciplina_id = %s AND serie_id = %s 
                AND ano_letivo_id = %s AND escola_id = %s AND id != %s
            """, (self.aluno_id, disciplina_id, serie_id, ano_letivo_id, escola_id, self.historico_id))
            
            if cursor.fetchone():
                messagebox.showerror("Erro", "Já existe outro registro para esta combinação de aluno, disciplina, série, ano letivo e escola.")
                return
                
            # Atualizar o registro
            cursor.execute("""
                UPDATE historico_escolar SET 
                disciplina_id = %s, serie_id = %s, ano_letivo_id = %s, 
                escola_id = %s, media = %s, conceito = %s
                WHERE id = %s
            """, (disciplina_id, serie_id, ano_letivo_id, escola_id, media_valor, conceito, self.historico_id))
            
            conn.commit()
            self.mostrar_mensagem_temporaria("Registro atualizado com sucesso!")
            
            # Invalidar caches relacionados
            self.invalidar_cache_historico(self.aluno_id)
            self.invalidar_cache_filtros(self.aluno_id)
            self.invalidar_cache_disciplinas(self.aluno_id)
            
            # Recarregar histórico
            self.carregar_historico()
            
            # Limpar apenas os campos de disciplina, média e conceito, mantendo aluno, escola, série e ano letivo
            self.disciplina_selecionada.set("")
            self.media.set("")
            self.conceito.set("")
            self.historico_id = None
            
            # Limpar os IDs do registro selecionado
            self.registro_disciplina_id = None
            self.registro_serie_id = None
            self.registro_ano_letivo_id = None
            self.registro_escola_id = None
            
            # Atualizar disciplinas disponíveis após atualização
            self.atualizar_disciplinas()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Erro ao atualizar registro: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def excluir_registro(self):
        # Verificar se há um registro selecionado
        if not hasattr(self, 'historico_id'):
            messagebox.showerror("Erro", "Selecione um registro para excluir.")
            return
            
        # Confirmar exclusão
        confirmar = messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir este registro?")
        if not confirmar:
            return
            
        # Conectar ao banco
        conn = self.validar_conexao_bd()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        try:
            # Excluir o registro
            cursor.execute("DELETE FROM historico_escolar WHERE id = %s", (self.historico_id,))
            
            # Commit e mensagem
            conn.commit()
            self.mostrar_mensagem_temporaria("Registro excluído com sucesso!")
            
            # Invalidar caches relacionados
            self.invalidar_cache_historico(self.aluno_id)
            self.invalidar_cache_filtros(self.aluno_id)
            self.invalidar_cache_disciplinas(self.aluno_id)
            
            # Atualizar o histórico
            self.carregar_historico()
            
            # Limpar os campos
            self.limpar_campos(manter_aluno=True, manter_serie_escola_ano=True)
            
        except Exception as e:
            # Rollback e mensagem de erro
            conn.rollback()
            messagebox.showerror("Erro", f"Erro ao excluir registro: {str(e)}")
            
        # Fechar conexão
        cursor.close()
        conn.close()

    def _validar_media(self, event=None):
        """
        Valida o campo Média para aceitar apenas números e ponto decimal.
        Remove caracteres inválidos automaticamente.
        """
        valor_atual = self.media.get()
        # Filtra apenas dígitos e ponto decimal
        valor_filtrado = ""
        ponto_encontrado = False
        for char in valor_atual:
            if char.isdigit():
                valor_filtrado += char
            elif char == '.' and not ponto_encontrado:
                valor_filtrado += char
                ponto_encontrado = True
        if valor_filtrado != valor_atual:
            self.media.set(valor_filtrado)
            # Reposiciona o cursor no final
            self.ent_media.icursor(tk.END)
    
    def _validar_conceito(self, event=None):
        """
        Valida o campo Conceito para aceitar apenas letras.
        Converte automaticamente para maiúsculas.
        """
        valor_atual = self.conceito.get()
        # Filtra apenas letras e converte para maiúsculo
        valor_filtrado = ''.join(char.upper() for char in valor_atual if char.isalpha())
        if valor_filtrado != valor_atual:
            self.conceito.set(valor_filtrado)
            # Reposiciona o cursor no final
            self.ent_conceito.icursor(tk.END)

    def _inserir_com_enter(self, event=None):
        """
        Executa inserir_registro apenas se houver dados em Média ou Conceito.
        """
        media_valor = self.media.get().strip()
        conceito_valor = self.conceito.get().strip()
        
        # Só insere se pelo menos um dos campos tiver valor
        if media_valor or conceito_valor:
            self.inserir_registro()

    def limpar_campos(self, manter_aluno=False, manter_serie_escola_ano=False):
        """
        Limpa todos os campos do formulário
        
        Args:
            manter_aluno: Se True, mantém as informações do aluno selecionado
            manter_serie_escola_ano: Se True, mantém série, escola e ano letivo
        """
        if not manter_aluno:
            self.aluno_selecionado.set("")
            self.aluno_data_nascimento.set("")  # Limpar data de nascimento
            self.aluno_sexo.set("")  # Limpar sexo
            self.aluno_id = None
            self.cb_pesquisa_aluno.set("")  # Limpar a combobox de pesquisa
            
        if not manter_serie_escola_ano:
            self.escola_selecionada.set("")
            self.serie_selecionada.set("")
            self.ano_letivo_selecionado.set("")
            
            # Desabilitar comboboxes na ordem correta
            self.cb_escola.configure(state="normal")
            self.cb_serie.configure(state="disabled")
            self.cb_ano_letivo.configure(state="disabled")
            self.cb_disciplina.configure(state="disabled")
            
        self.disciplina_selecionada.set("")
        self.media.set("")
        self.conceito.set("")
        self.historico_id = None
        
        # Limpar os IDs do registro selecionado
        self.registro_disciplina_id = None
        self.registro_serie_id = None
        self.registro_ano_letivo_id = None
        self.registro_escola_id = None

    def mostrar_mensagem_temporaria(self, mensagem, tipo="info"):
        # Remover mensagem anterior se existir
        if self.mensagem_temporaria is not None:
            self.mensagem_temporaria.destroy()
            
        # Criar frame para a mensagem
        cor_fundo = self.co3 if tipo == "info" else self.co6  # Verde para info, vermelho para erro
        cor_texto = self.co1  # Branco
        
        self.mensagem_temporaria = tk.Frame(self.janela, bg=cor_fundo, padx=10, pady=5)
        self.mensagem_temporaria.place(relx=0.5, rely=0.1, anchor="center")
        
        # Texto da mensagem
        tk.Label(self.mensagem_temporaria, text=mensagem, bg=cor_fundo, fg=cor_texto,
               font=("Arial", 10, "bold")).pack(padx=10, pady=5)
        
        # Configurar para desaparecer ao clicar em qualquer lugar ou pressionar qualquer tecla
        self.janela.bind("<Button>", lambda e: self._esconder_mensagem())
        self.janela.bind("<Key>", lambda e: self._esconder_mensagem())
        
        # Configurar para desaparecer automaticamente após 3 segundos
        self.janela.after(3000, self._esconder_mensagem)
        
    def _esconder_mensagem(self):
        # Remover bindings
        self.janela.unbind("<Button>")
        self.janela.unbind("<Key>")
        
        # Remover mensagem se existir
        if self.mensagem_temporaria is not None:
            self.mensagem_temporaria.destroy()
            self.mensagem_temporaria = None

    def gerar_pdf(self):
        # Verificar se há um aluno selecionado
        if not hasattr(self, 'aluno_id') or not self.aluno_id:
            messagebox.showerror("Erro", "Selecione um aluno primeiro.")
            return
        # Chamar wrapper que tenta usar dados em cache/UI para reduzir queries
        self.gerar_historico_com_cache()

    def importar_excel(self):
        # Abrir diálogo para seleção de arquivo
        arquivo = filedialog.askopenfilename(
            title="Selecione o arquivo Excel",
            filetypes=[("Arquivos Excel", "*.xlsx;*.xls")]
        )
        
        if not arquivo:
            return
            
        try:
            # Ler o arquivo Excel
            df = pd.read_excel(arquivo)
            
            # Verificar colunas obrigatórias
            colunas_necessarias = ['aluno_id', 'disciplina_id', 'ano_letivo_id', 'serie_id', 'escola_id']
            colunas_faltantes = [col for col in colunas_necessarias if col not in df.columns]
            
            if colunas_faltantes:
                messagebox.showerror("Erro", f"Colunas faltantes no arquivo: {', '.join(colunas_faltantes)}")
                return
                
            # Conectar ao banco
            conn = self.validar_conexao_bd()
            if conn is None:
                return
            cursor = conn.cursor()
            
            # Contador de registros
            inseridos = 0
            atualizados = 0
            erros = 0
            
            # Processar cada linha
            for idx, row in df.iterrows():
                try:
                    # Verificar se o registro já existe
                    cursor.execute("""
                        SELECT id FROM historico_escolar
                        WHERE aluno_id = %s AND disciplina_id = %s AND ano_letivo_id = %s
                    """, (row['aluno_id'], row['disciplina_id'], row['ano_letivo_id']))
                    
                    registro_existente = cursor.fetchone()
                    
                    # Definir media e conceito
                    media = row.get('media') if 'media' in row and not pd.isna(row['media']) else None
                    conceito = row.get('conceito') if 'conceito' in row and not pd.isna(row['conceito']) else None
                    
                    if registro_existente:
                        # Atualizar registro existente
                        cursor.execute("""
                            UPDATE historico_escolar
                            SET media = %s, conceito = %s, serie_id = %s, escola_id = %s
                            WHERE id = %s
                        """, self._safe_sql_params(media, conceito, row['serie_id'], row['escola_id'], registro_existente[0]))
                        atualizados += 1
                    else:
                        # Inserir novo registro
                        cursor.execute("""
                            INSERT INTO historico_escolar (aluno_id, disciplina_id, media, ano_letivo_id, escola_id, conceito, serie_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (row['aluno_id'], row['disciplina_id'], media, row['ano_letivo_id'], row['escola_id'], conceito, row['serie_id']))
                        inseridos += 1
                        
                except Exception as e:
                    erros += 1
                    linha_numero = idx if isinstance(idx, int) else str(idx)
                    _logger.exception(f"Erro na linha {linha_numero}: {str(e)}")
                    
            # Commit
            conn.commit()
            
            # Construir mensagem de resultado
            mensagem = f"{inseridos} registros foram inseridos com sucesso.\n{erros} registros não puderam ser inseridos."
            
            # Mostrar mensagem
            self.mostrar_mensagem_temporaria(mensagem)
            
            # Atualizar o histórico se um aluno estiver selecionado
            if hasattr(self, 'aluno_id'):
                self.carregar_historico()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao importar arquivo: {str(e)}")
            
        finally:
            # Fechar conexão
            if 'conn' in locals() and conn:
                cursor.close()
                conn.close()

    def gerar_historico_com_cache(self):
        """
        Wrapper que reúne dados já presentes na UI/cache e chama `historico_escolar`
        com parâmetros opcionais para evitar reconsultas ao BD quando possível.
        """
        # Verificar se há um aluno selecionado
        if not hasattr(self, 'aluno_id') or not self.aluno_id:
            messagebox.showerror("Erro", "Selecione um aluno primeiro.")
            return

        # Preparar objeto aluno se tivermos informações em cache
        aluno = None
        try:
            if hasattr(self, 'alunos_info') and self.aluno_selecionado.get() in self.alunos_info:
                info = self.alunos_info[self.aluno_selecionado.get()]
                aluno = {
                    'id': info[0],
                    'nome': self.aluno_selecionado.get(),
                    'data_nascimento': info[1],
                    'sexo': info[2]
                }
        except Exception:
            aluno = None

        # Se `aluno` foi criado a partir do cache, garantir que local_nascimento e UF_nascimento
        # sejam preenchidos — se ausentes, buscar no BD. Registrar tempo desta consulta.
        if aluno is not None:
            need_local = not aluno.get('local_nascimento')
            need_uf = not aluno.get('UF_nascimento')
            if need_local or need_uf:
                try:
                    conn_local = conectar_bd()
                    if conn_local:
                        cur_local = conn_local.cursor()
                        start_q = time.time()
                        cur_local.execute("SELECT local_nascimento, UF_nascimento FROM alunos WHERE id = %s", (self.aluno_id,))
                        row_aluno = cur_local.fetchone()
                        elapsed_ms = int((time.time() - start_q) * 1000)
                        _logger.info(f"event=db_query name=select_aluno_local aluno_id={self.aluno_id} duration_ms={elapsed_ms}")
                        if row_aluno:
                            if need_local:
                                aluno['local_nascimento'] = row_aluno[0]
                            if need_uf:
                                aluno['UF_nascimento'] = row_aluno[1]
                        cur_local.close()
                        conn_local.close()
                except Exception:
                    # Não falhar a geração por causa desse preenchimento
                    pass

        # Tentar usar histórico em cache para reduzir queries
        historico = None
        cache_key = f"historico_{self.aluno_id}"
        if hasattr(self, '_cache_historico') and cache_key in self._cache_historico:
            dados = self._cache_historico[cache_key]['resultados']
            historico = []
            for registro, _ in dados:
                # registro: (h.id, d.nome, al.ano_letivo, s.nome, e.nome, h.media, h.conceito, h.disciplina_id, h.ano_letivo_id, h.serie_id, h.escola_id)
                try:
                    disciplina = registro[1]
                    media = registro[5]
                    conceito = registro[6]
                    serie_id = registro[9] if len(registro) > 9 else None
                    ano_letivo_id = registro[8] if len(registro) > 8 else None
                    historico.append((disciplina, None, serie_id, media, conceito, None, ano_letivo_id))
                except Exception:
                    continue

        # Construir `resultados` (resumo por série) a partir do cache quando possível
        resultados = None
        dados_observacoes = None
        if hasattr(self, '_cache_historico') and cache_key in self._cache_historico:
            registros = self._cache_historico[cache_key]['resultados']
            # Agrupar por serie_id
            resumo_por_serie = {}
            observacoes_set = set()
            for registro, _ in registros:
                try:
                    aluno_id_reg = self.aluno_id
                    serie_id = registro[9] if len(registro) > 9 else None
                    ano_letivo_nome = registro[2] if len(registro) > 2 else None
                    escola_nome = registro[4] if len(registro) > 4 else ''
                    escola_id = registro[10] if len(registro) > 10 else (registro[10] if len(registro) > 10 else None)
                    media = registro[5] if len(registro) > 5 else None
                    conceito = registro[6] if len(registro) > 6 else None

                    if serie_id is None:
                        continue

                    if serie_id not in resumo_por_serie:
                        resumo_por_serie[serie_id] = {
                            'count_media': 0,
                            'count_conceito': 0,
                            'min_media': None,
                            'ano_letivo': ano_letivo_nome,
                            'escola_nome': escola_nome,
                            'escola_id': escola_id
                        }

                    # Atualizar contadores e min_media de acordo com as regras usadas no SQL
                    if media is not None and media != '':
                        try:
                            m = float(media)
                            resumo_por_serie[serie_id]['count_media'] += 1
                            if resumo_por_serie[serie_id]['min_media'] is None or m < resumo_por_serie[serie_id]['min_media']:
                                resumo_por_serie[serie_id]['min_media'] = m
                        except Exception:
                            pass
                    if conceito not in (None, '', 'NULL'):
                        resumo_por_serie[serie_id]['count_conceito'] += 1

                    if serie_id and ano_letivo_nome and escola_id:
                        observacoes_set.add((serie_id, registro[8] if len(registro) > 8 else None, escola_id))
                except Exception:
                    continue

            resultados = []
            for serie_id, info in resumo_por_serie.items():
                # Calcular situação_final usando exatamente a mesma lógica do SQL:
                # 1) WHEN COUNT(media)=0 AND COUNT(conceito)>0 => Promovido(a)
                # 2) WHEN MIN(media) >= 60 => Promovido(a)
                # 3) WHEN MIN(media) < 60 => Retido(a)
                situacao = 'Retido(a)'
                count_media = info.get('count_media', 0)
                count_conceito = info.get('count_conceito', 0)
                min_media = info.get('min_media')

                if count_media == 0 and count_conceito > 0:
                    situacao = 'Promovido(a)'
                elif count_media > 0:
                    try:
                        if min_media is not None and min_media >= 60:
                            situacao = 'Promovido(a)'
                        else:
                            situacao = 'Retido(a)'
                    except Exception:
                        situacao = 'Retido(a)'

                # Tentar obter o município (escola_municipio) consultando o BD quando não estiver disponível
                # Usar cache local por execução para evitar consultas repetidas à mesma escola
                # Obter município usando helper reutilizável com cache em nível de processo
                escola_municipio = ''
                try:
                    escola_nome = info.get('escola_nome')
                    if escola_nome:
                        escola_municipio = get_escola_municipio(escola_nome)
                except Exception:
                    escola_municipio = ''

                resultados.append((self.aluno_id, serie_id, info['ano_letivo'], info['escola_nome'], escola_municipio, situacao))

            # dados_observacoes: lista de tuplas (serie_id, ano_letivo_id, escola_id)
            dados_observacoes = list(observacoes_set) if observacoes_set else None

        # Log básico para auditoria
        _logger.info(f"gerar_historico_com_cache: aluno_id={self.aluno_id} aluno_cached={bool(aluno)} historico_cached={bool(historico)}")

        # Calcular carga_total_por_serie quando usamos histórico vindo do cache
        carga_total_por_serie = None
        if hasattr(self, '_cache_historico') and cache_key in self._cache_historico:
            try:
                # Mapear série -> conjunto de disciplina_ids para consulta única
                serie_para_disciplinas = {}
                disciplina_ids = set()
                serie_ano_escola = {}
                registros_cache = self._cache_historico[cache_key]['resultados']
                for registro, _ in registros_cache:
                    try:
                        disc_id = registro[7] if len(registro) > 7 else None
                        ano_letivo_id = registro[8] if len(registro) > 8 else None
                        serie_id = registro[9] if len(registro) > 9 else None
                        escola_id = registro[10] if len(registro) > 10 else None
                        if serie_id is None:
                            continue
                        if disc_id:
                            disciplina_ids.add(disc_id)
                            serie_para_disciplinas.setdefault(serie_id, set()).add(disc_id)
                        # armazenar um (ano, escola) representativo para a série (usado para carga_horaria_total)
                        if serie_id not in serie_ano_escola and ano_letivo_id and escola_id:
                            serie_ano_escola[serie_id] = (ano_letivo_id, escola_id)
                    except Exception:
                        continue

                # Buscar carga horária das disciplinas necessárias em uma única query
                carga_map = {}
                if disciplina_ids:
                    try:
                        conn_c = conectar_bd()
                        if conn_c:
                            cur_c = conn_c.cursor()
                            placeholders = ','.join(['%s'] * len(disciplina_ids))
                            query = f"SELECT id, carga_horaria FROM disciplinas WHERE id IN ({placeholders})"
                            cur_c.execute(query, tuple(disciplina_ids))
                            for r in cur_c.fetchall():
                                carga_map[r[0]] = r[1]
                            cur_c.close()
                            conn_c.close()
                    except Exception:
                        carga_map = {}

                # Montar carga_total_por_serie com base nas cargas individuais e na tabela de carga total quando disponível
                carga_total_por_serie = {}
                for serie_id, disc_set in serie_para_disciplinas.items():
                    total = 0
                    todas_null = True
                    for did in disc_set:
                        ch = carga_map.get(did)
                        if ch is not None:
                            todas_null = False
                            try:
                                total += int(ch)
                            except Exception:
                                try:
                                    total += float(ch)
                                except Exception:
                                    pass
                    carga_total_por_serie[serie_id] = {
                        'carga_total': total if not todas_null else None,
                        'todas_null': todas_null,
                        'carga_horaria_total': None
                    }

                # Buscar carga_horaria_total por série (quando disponível) para preencher carga_horaria_total
                for serie_id, tup in serie_ano_escola.items():
                    ano_id, escola_id = tup
                    try:
                        conn_ct = conectar_bd()
                        if conn_ct:
                            cur_ct = conn_ct.cursor()
                            start_q = time.time()
                            cur_ct.execute("SELECT carga_horaria_total FROM carga_horaria_total WHERE serie_id = %s AND ano_letivo_id = %s AND escola_id = %s LIMIT 1", (serie_id, ano_id, escola_id))
                            row_ct = cur_ct.fetchone()
                            elapsed_ms = int((time.time() - start_q) * 1000)
                            _logger.info(f"event=db_query name=select_carga_total serie_id={serie_id} ano_letivo_id={ano_id} escola_id={escola_id} duration_ms={elapsed_ms}")
                            if row_ct and row_ct[0] is not None:
                                carga_total_por_serie.setdefault(serie_id, {})['carga_horaria_total'] = row_ct[0]
                            cur_ct.close()
                            conn_ct.close()
                    except Exception:
                        # não falhar a geração por causa desse preenchimento
                        pass

                # Se todas as cargas individuais são nulas, usar a carga_horaria_total quando existir
                for sid, info in carga_total_por_serie.items():
                    if info.get('todas_null') and info.get('carga_horaria_total'):
                        info['carga_total'] = info['carga_horaria_total']

                if not carga_total_por_serie:
                    carga_total_por_serie = None
            except Exception:
                carga_total_por_serie = None

        # Reconstruir `historico` para incluir `carga_horaria` e `carga_horaria_total`
        # quando o histórico original veio do cache (as tuplas do cache não
        # continham as cargas). Isso ajuda `preencher_tabela_estudos_realizados`
        # a mostrar as cargas individuais e a linha TOTAL/CH.
        try:
            if historico is not None and hasattr(self, '_cache_historico') and cache_key in self._cache_historico:
                rebuilt = []
                registros_cache = self._cache_historico[cache_key]['resultados']
                for registro, _ in registros_cache:
                    try:
                        disciplina = registro[1]
                        disc_id = registro[7] if len(registro) > 7 else None
                        ano_letivo_id = registro[8] if len(registro) > 8 else None
                        serie_id = registro[9] if len(registro) > 9 else None
                        escola_id = registro[10] if len(registro) > 10 else None
                        media = registro[5] if len(registro) > 5 else None
                        conceito = registro[6] if len(registro) > 6 else None

                        carga_horaria = None
                        if 'carga_map' in locals() and disc_id is not None:
                            carga_horaria = carga_map.get(disc_id)

                        carga_horaria_total = None
                        if carga_total_por_serie and serie_id in carga_total_por_serie:
                            carga_horaria_total = carga_total_por_serie[serie_id].get('carga_horaria_total') or carga_total_por_serie[serie_id].get('carga_total')

                        rebuilt.append((disciplina, carga_horaria, serie_id, media, conceito, carga_horaria_total, ano_letivo_id))
                    except Exception:
                        continue
                historico = rebuilt
        except Exception:
            pass

        # Chamar gerador de PDF passando os parâmetros que temos (inclui carga_total_por_serie quando calculado)
        try:
            historico_escolar(self.aluno_id, aluno=aluno, historico=historico, resultados=resultados, dados_observacoes=dados_observacoes, carga_total_por_serie=carga_total_por_serie)
            self.mostrar_mensagem_temporaria("Histórico escolar gerado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar histórico: {str(e)}")

    def atualizar_disciplinas(self, event=None):
        """
        Atualiza a lista de disciplinas disponíveis no combobox - versão otimizada com cache
        """
        # Limpar o combobox de disciplinas
        self.disciplina_selecionada.set('')
        
        # Obter dados necessários
        escola_texto = self.escola_selecionada.get()
        serie_texto = self.serie_selecionada.get()
        ano_letivo_texto = self.ano_letivo_selecionado.get()
        
        if not escola_texto or not hasattr(self, 'aluno_id') or not self.aluno_id:
            self.cb_disciplina['values'] = []
            return
        
        # Extrair IDs
        escola_id = self.escolas_map.get(escola_texto)
        serie_id = self.series_map.get(serie_texto)
        ano_letivo_id = self.anos_letivos_map.get(ano_letivo_texto)
        
        # Se algum dos campos não estiver preenchido, não filtrar por disciplinas com nota
        if not (serie_id and escola_id and ano_letivo_id):
            return
        
        # Criar chave de cache
        cache_key = f"disciplinas_{self.aluno_id}_{escola_id}_{serie_id}_{ano_letivo_id}"
        
        # Verificar cache primeiro
        if hasattr(self, '_cache_disciplinas_filtradas') and cache_key in self._cache_disciplinas_filtradas:
            disciplinas_disponiveis = self._cache_disciplinas_filtradas[cache_key]
            self._aplicar_disciplinas_disponiveis(disciplinas_disponiveis)
            return
        
        # Conectar ao banco
        conn = self.validar_conexao_bd()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        try:
            # Consulta otimizada que combina todas as verificações em uma única query
            cursor.execute("""
                SELECT d.id, d.nome
                FROM disciplinas d
                LEFT JOIN series s ON s.id = %s
                WHERE (d.escola_id IS NULL OR d.escola_id = %s)
                AND (d.nivel_id IS NULL OR 
                     (CASE 
                        WHEN REGEXP_SUBSTR(s.nome, '[0-9]+') BETWEEN 1 AND 5 THEN d.nivel_id = 2
                        WHEN REGEXP_SUBSTR(s.nome, '[0-9]+') BETWEEN 6 AND 9 THEN d.nivel_id = 3
                        ELSE 1=1
                      END))
                AND d.id NOT IN (
                    SELECT h.disciplina_id
                    FROM historico_escolar h
                    WHERE h.aluno_id = %s
                    AND h.serie_id = %s
                    AND h.escola_id = %s
                    AND h.ano_letivo_id = %s
                )
                ORDER BY d.nome
            """, self._safe_sql_params(serie_id, escola_id, self.aluno_id, serie_id, escola_id, ano_letivo_id))
            
            todas_disciplinas = cursor.fetchall()
            
            # Processar disciplinas disponíveis
            disciplinas_disponiveis = []
            temp_disciplinas_map = {}
            
            for disc_id, disc_nome in todas_disciplinas:
                disciplinas_disponiveis.append(disc_nome)
                temp_disciplinas_map[disc_nome] = disc_id
            
            # Atualizar o mapa de disciplinas com as disciplinas disponíveis
            self.disciplinas_map.update(temp_disciplinas_map)
            
            # Armazenar no cache
            if not hasattr(self, '_cache_disciplinas_filtradas'):
                self._cache_disciplinas_filtradas = {}
            # Limitar tamanho do cache
            if len(self._cache_disciplinas_filtradas) > 50:
                self._cache_disciplinas_filtradas.clear()
            self._cache_disciplinas_filtradas[cache_key] = disciplinas_disponiveis
            
            # Aplicar na interface
            self._aplicar_disciplinas_disponiveis(disciplinas_disponiveis)
                
        except Exception as e:
            _logger.exception(f"Erro ao atualizar disciplinas: {str(e)}")
            # Fallback para método mais simples se a consulta otimizada falhar
            self._atualizar_disciplinas_fallback(escola_id, serie_id, ano_letivo_id)
        finally:
            cursor.close()
            conn.close()
    
    def _aplicar_disciplinas_disponiveis(self, disciplinas_disponiveis):
        """Aplica a lista de disciplinas disponíveis na interface"""
        try:
            # Atualizar combobox
            atual = self.disciplina_selecionada.get()
            self.cb_disciplina['values'] = disciplinas_disponiveis
            
            # Ajustar a largura do combobox baseado no conteúdo
            self.ajustar_largura_combobox(self.cb_disciplina, disciplinas_disponiveis)
            
            # Manter a seleção atual se ainda for válida
            if atual and atual in disciplinas_disponiveis:
                self.disciplina_selecionada.set(atual)
            else:
                self.disciplina_selecionada.set("")
        except Exception as e:
            _logger.exception(f"Erro ao aplicar disciplinas: {str(e)}")
    
    def _atualizar_disciplinas_fallback(self, escola_id, serie_id, ano_letivo_id):
        """Método fallback para atualizar disciplinas caso a consulta otimizada falhe"""
        conn = self.validar_conexao_bd()
        if conn is None:
            return
        
        cursor = conn.cursor()
        
        try:
            # Buscar todas as disciplinas disponíveis para a escola
            cursor.execute("""
                SELECT d.id, d.nome
                FROM disciplinas d
                WHERE (d.escola_id IS NULL OR d.escola_id = %s)
                ORDER BY d.nome
            """, (escola_id,))
            
            todas_disciplinas = cursor.fetchall()
            
            # Buscar disciplinas que já têm nota
            cursor.execute("""
                SELECT h.disciplina_id
                FROM historico_escolar h
                WHERE h.aluno_id = %s
                AND h.serie_id = %s
                AND h.escola_id = %s
                AND h.ano_letivo_id = %s
            """, self._safe_sql_params(self.aluno_id, serie_id, escola_id, ano_letivo_id))
            
            disciplinas_com_nota = {str(row[0]) for row in cursor.fetchall()}
            
            # Filtrar disciplinas disponíveis
            disciplinas_disponiveis = []
            temp_disciplinas_map = {}
            
            for disc_id, disc_nome in todas_disciplinas:
                if str(disc_id) not in disciplinas_com_nota:
                    disciplinas_disponiveis.append(disc_nome)
                    temp_disciplinas_map[disc_nome] = disc_id
            
            self.disciplinas_map.update(temp_disciplinas_map)
            self._aplicar_disciplinas_disponiveis(disciplinas_disponiveis)
            
        except Exception as e:
            _logger.exception(f"Erro no fallback de disciplinas: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    def invalidar_cache_disciplinas(self, aluno_id=None):
        """Invalida o cache de disciplinas quando há alterações"""
        if not hasattr(self, '_cache_disciplinas_filtradas'):
            return
            
        if aluno_id:
            # Remover apenas os caches do aluno específico
            keys_to_remove = [k for k in self._cache_disciplinas_filtradas.keys() if f"disciplinas_{aluno_id}_" in k]
            for key in keys_to_remove:
                del self._cache_disciplinas_filtradas[key]
        else:
            # Limpar todo o cache
            self._cache_disciplinas_filtradas.clear()

    def voltar_pagina_principal(self):
        """
        Fecha a interface atual e volta para a janela principal.
        """
        if self.janela_pai:
            # Se tiver uma janela pai, mostra ela de volta
            self.janela_pai.deiconify()
            # Fecha a janela atual
            self.janela.destroy()
        else:
            # Se não tiver uma janela pai, apenas fecha a janela atual
            self.janela.destroy()

    def aplicar_filtros(self):
        """Aplica os filtros selecionados na visualização do histórico - versão otimizada"""
        if not hasattr(self, 'aluno_id') or not self.aluno_id:
            return
            
        # Limpar a treeview
        for i in self.treeview_historico.get_children():
            self.treeview_historico.delete(i)
            
        # Criar chave de cache para filtros
        filtros_key = f"{self.filtro_ano.get()}|{self.filtro_disciplina.get()}|{self.filtro_situacao.get()}"
        cache_key = f"filtros_{self.aluno_id}_{filtros_key}"
        
        # Verificar cache primeiro
        if hasattr(self, '_cache_filtros') and cache_key in self._cache_filtros:
            registros_filtrados = self._cache_filtros[cache_key]
            self._aplicar_registros_filtrados(registros_filtrados)
            return
            
        # Construir a consulta SQL com filtros otimizada
        query_base = """
            SELECT /*+ USE_INDEX(h, idx_aluno_historico) */
                h.id, 
                d.nome AS disciplina, 
                al.ano_letivo, 
                s.nome AS serie, 
                e.nome AS escola, 
                h.media, 
                h.conceito,
                h.disciplina_id, 
                h.ano_letivo_id, 
                h.serie_id, 
                h.escola_id
            FROM historico_escolar h
            INNER JOIN disciplinas d ON h.disciplina_id = d.id
            INNER JOIN anosletivos al ON h.ano_letivo_id = al.id
            INNER JOIN series s ON h.serie_id = s.id
            INNER JOIN escolas e ON h.escola_id = e.id
            WHERE h.aluno_id = %s
        """
        
        params = [self.aluno_id]
        condicoes_extras = []
        
        # Aplicar filtros de forma mais eficiente
        if self.filtro_ano.get() and self.filtro_ano.get() != 'Todos':
            condicoes_extras.append("al.ano_letivo = %s")
            params.append(self.filtro_ano.get())
            
        if self.filtro_disciplina.get() and self.filtro_disciplina.get() != 'Todas':
            condicoes_extras.append("d.nome LIKE %s")
            params.append(f"%{self.filtro_disciplina.get()}%")
            
        if self.filtro_situacao.get() and self.filtro_situacao.get() != 'Todos':
            if self.filtro_situacao.get() == 'Aprovado':
                condicoes_extras.append("(h.media >= 60 OR h.conceito IN ('AD', 'PNAD', 'APNAD'))")
            elif self.filtro_situacao.get() == 'Reprovado':
                condicoes_extras.append("(h.media < 60 OR h.conceito = 'RT')")
            
        # Montar query final
        query_final = query_base
        if condicoes_extras:
            query_final += " AND " + " AND ".join(condicoes_extras)
        query_final += " ORDER BY al.ano_letivo DESC, s.id, d.nome"
        
        # Executar a consulta
        conn = self.validar_conexao_bd()
        if conn is None:
            return
        cursor = conn.cursor()
        
        try:
            cursor.execute(query_final, params)
            registros = cursor.fetchall()
            
            # Processar registros
            registros_processados = []
            for registro in registros:
                valores_formatados = self._formatar_registro_historico(registro)
                registros_processados.append((registro, valores_formatados))
            
            # Armazenar no cache
            if not hasattr(self, '_cache_filtros'):
                self._cache_filtros = {}
            # Limitar tamanho do cache
            if len(self._cache_filtros) > 20:
                self._cache_filtros.clear()
            self._cache_filtros[cache_key] = registros_processados
            
            # Aplicar na interface
            self._aplicar_registros_filtrados(registros_processados)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao aplicar filtros: {str(e)}")
            _logger.exception(f"Erro ao aplicar filtros: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    def _aplicar_registros_filtrados(self, registros_processados):
        """Aplica os registros filtrados na treeview"""
        try:
            for registro, valores_formatados in registros_processados:
                # Obter valores a serem mostrados (excluindo a situação)
                valores_display = valores_formatados[:-1]
                
                # Obter situação para definir a tag
                situacao = valores_formatados[-1]
                tags = [str(registro[0])]
                
                if situacao:
                    tags.append(situacao)
                
                # Inserir na treeview
                self.treeview_historico.insert("", "end", values=valores_display, tags=tags)
        except Exception as e:
            _logger.exception(f"Erro ao aplicar registros filtrados: {str(e)}")
    
    def invalidar_cache_filtros(self, aluno_id=None):
        """Invalida o cache de filtros quando há alterações"""
        if not hasattr(self, '_cache_filtros'):
            return
            
        if aluno_id:
            # Remover apenas os caches do aluno específico
            keys_to_remove = [k for k in self._cache_filtros.keys() if f"filtros_{aluno_id}_" in k]
            for key in keys_to_remove:
                del self._cache_filtros[key]
        else:
            # Limpar todo o cache
            self._cache_filtros.clear()
    # Funções de relatório/matriz removidas
    # As funções relacionadas a relatório de desempenho, matriz de séries x disciplinas e importação/exportação
    # foram removidas conforme a solicitação (gerar_relatorio_desempenho, abrir_matriz_series_disciplinas,
    # abrir_matriz_com_escola, exportar_matriz_excel, adicionar_disciplina_matriz, editar_disciplina_matriz,
    # exportar_matriz_pdf, atualizar_visualizacao_matriz, importar_excel).
    # Se for necessário restaurá-las, posso recolocar as implementações ou mover para um módulo separado.

    def atualizar_disciplinas_disponiveis(self):
        """
        Atualiza a lista de disciplinas disponíveis no combobox, 
        excluindo as disciplinas que já possuem nota para o aluno, 
        série, escola e ano letivo selecionados.
        Aplica também filtro pelo nível da série: nivel_id=2 para séries 1 a 5 e nivel_id=3 para séries 6 a 9.
        """
        # Verifica se há um aluno selecionado
        if not hasattr(self, 'aluno_id') or not self.aluno_id:
            return
            
        # Obter série, escola e ano letivo selecionados
        serie_texto = self.serie_selecionada.get()
        escola_texto = self.escola_selecionada.get()
        ano_letivo_texto = self.ano_letivo_selecionado.get()
        
        # Extrair IDs
        serie_id = serie_texto.split(' - ')[0] if serie_texto else None
        escola_id = escola_texto.split(' - ')[0] if escola_texto else None
        ano_letivo_id = ano_letivo_texto.split(' - ')[0] if ano_letivo_texto else None
        
        # Se algum dos campos não estiver preenchido, não filtrar
        if not (serie_id and escola_id and ano_letivo_id):
            return
            
        # Conectar ao banco
        conn = self.validar_conexao_bd()
        if conn is None:
            return
        cursor = conn.cursor()
        
        try:
            # Determinar o nível com base no número da série
            cursor.execute("""
                SELECT nome 
                FROM series 
                WHERE id = %s
            """, self._safe_sql_params(serie_id))
            
            serie_result = cursor.fetchone()
            if not serie_result:
                return
            
            serie_nome = serie_result[0]
            nivel_id = None
            
            # Extrair o número da série do nome
            import re
            numero_serie = re.search(r'(\d+)', str(serie_nome))
            if numero_serie:
                numero = int(numero_serie.group(1))
                if 1 <= numero <= 5:
                    nivel_id = 2  # Fundamental I (1º ao 5º ano)
                elif 6 <= numero <= 9:
                    nivel_id = 3  # Fundamental II (6º ao 9º ano)
            
            # Buscar todas as disciplinas disponíveis para a escola e nível
            if nivel_id:
                cursor.execute("""
                    SELECT d.id, d.nome
                    FROM disciplinas d
                    WHERE (d.escola_id IS NULL OR d.escola_id = %s)
                    AND (d.nivel_id IS NULL OR d.nivel_id = %s)
                    ORDER BY d.id
                """, (escola_id, nivel_id))
            else:
                # Se não conseguir determinar o nível, exibir todas as disciplinas
                cursor.execute("""
                    SELECT d.id, d.nome
                    FROM disciplinas d
                    WHERE (d.escola_id IS NULL OR d.escola_id = %s)
                    ORDER BY d.id
                """, (escola_id,))
            
            todas_disciplinas = cursor.fetchall()
            
            # Buscar disciplinas que já têm nota para este aluno, série, escola e ano letivo
            cursor.execute("""
                SELECT h.disciplina_id
                FROM historico_escolar h
                WHERE h.aluno_id = %s
                AND h.serie_id = %s
                AND h.escola_id = %s
                AND h.ano_letivo_id = %s
            """, (self.aluno_id, serie_id, escola_id, ano_letivo_id))
            
            disciplinas_com_nota = {str(row[0]) for row in cursor.fetchall()}
            
            # Filtrar disciplinas disponíveis
            disciplinas_disponiveis = []
            # Atualizar o mapa de disciplinas conforme necessário
            temp_disciplinas_map = {}
            
            for disc_id, disc_nome in todas_disciplinas:
                if str(disc_id) not in disciplinas_com_nota:
                    disciplinas_disponiveis.append(disc_nome)
                    temp_disciplinas_map[disc_nome] = disc_id
            
            # Atualizar o mapa de disciplinas com as disciplinas disponíveis
            self.disciplinas_map.update(temp_disciplinas_map)
            
            # Atualizar combobox
            atual = self.disciplina_selecionada.get()
            self.cb_disciplina['values'] = disciplinas_disponiveis
            
            # Ajustar a largura do combobox baseado no conteúdo
            self.ajustar_largura_combobox(self.cb_disciplina, disciplinas_disponiveis)
            
            # Manter a seleção atual se ainda for válida
            if atual and atual in disciplinas_disponiveis:
                self.disciplina_selecionada.set(atual)
            else:
                self.disciplina_selecionada.set("")
                
        except Exception as e:
            _logger.exception(f"Erro ao atualizar disciplinas: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    def ao_mudar_filtro(self, event=None):
        """
        Função chamada quando o usuário altera série, escola ou ano letivo.
        """
        widget = event.widget if event else None
        
        # Identificar qual widget foi alterado e chamar a função apropriada
        if widget == self.cb_escola:
            self.ao_selecionar_escola(event)
        elif widget == self.cb_serie:
            self.ao_selecionar_serie(event)
        elif widget == self.cb_ano_letivo:
            self.ao_selecionar_ano_letivo(event)
        else:
            # Caso não identifique o widget, tenta atualizar as disciplinas
            self.atualizar_disciplinas(event)

    def ao_selecionar_escola(self, event=None):
        """
        Função chamada quando o usuário seleciona uma escola.
        Habilita o campo de série e carrega as séries disponíveis.
        """
        escola_texto = self.escola_selecionada.get()
        
        # Limpar e desabilitar campos dependentes
        self.serie_selecionada.set("")
        self.ano_letivo_selecionado.set("")
        self.disciplina_selecionada.set("")
        self.cb_ano_letivo.configure(state="disabled")
        self.cb_disciplina.configure(state="disabled")
        
        if not escola_texto:
            self.cb_serie.configure(state="disabled")
            return
        
        # Habilitar o campo de série
        self.cb_serie.configure(state="normal")
        
        # Ajustar a largura do combobox de série com base em seu conteúdo atual
        series_valores = self.cb_serie['values']
        if series_valores:
            self.ajustar_largura_combobox(self.cb_serie, series_valores)
        
        # Se necessário, aqui poderíamos carregar séries específicas para esta escola
        # Por enquanto, deixamos todas as séries disponíveis como já carregadas em carregar_dados()
    
    def ao_selecionar_serie(self, event=None):
        """
        Função chamada quando o usuário seleciona uma série.
        Habilita o campo de ano letivo.
        """
        serie_texto = self.serie_selecionada.get()
        
        # Limpar e desabilitar campos dependentes
        self.ano_letivo_selecionado.set("")
        self.disciplina_selecionada.set("")
        self.cb_disciplina.configure(state="disabled")
        
        if not serie_texto:
            self.cb_ano_letivo.configure(state="disabled")
            return
        
        # Habilitar o campo de ano letivo
        self.cb_ano_letivo.configure(state="normal")
        
        # Ajustar a largura do combobox de ano letivo com base em seu conteúdo atual
        anos_valores = self.cb_ano_letivo['values']
        if anos_valores:
            self.ajustar_largura_combobox(self.cb_ano_letivo, anos_valores)
        
        # Se necessário, aqui poderíamos filtrar anos letivos específicos
        # Por enquanto, deixamos todos os anos letivos disponíveis como já carregados em carregar_dados()
    
    def ao_selecionar_ano_letivo(self, event=None):
        """
        Função chamada quando o usuário seleciona um ano letivo.
        Habilita o campo de disciplina e atualiza as disciplinas disponíveis.
        """
        ano_letivo_texto = self.ano_letivo_selecionado.get()
        
        # Limpar campo de disciplina
        self.disciplina_selecionada.set("")
        
        if not ano_letivo_texto:
            self.cb_disciplina.configure(state="disabled")
            return
        
        # Habilitar o campo de disciplina
        self.cb_disciplina.configure(state="normal")
        
        # Atualizar a lista de disciplinas disponíveis
        self.atualizar_disciplinas()

    def _configurar_cores_alternadas(self, event):
        """
        Configura cores alternadas nas linhas da treeview.
        """
        # Já não precisamos deste método pois estamos usando o recurso 'alternate' do style.map
        # Porém, vamos adicionar alguns bindings para melhorar a experiência do usuário
        
        # Binding para o efeito de hover (passar o mouse sobre a linha)
        self.treeview_historico.bind("<Enter>", self._on_treeview_hover)
        self.treeview_historico.bind("<Motion>", self._on_treeview_hover)
        self.treeview_historico.bind("<Leave>", self._on_treeview_leave)
    
    def _on_treeview_hover(self, event):
        """Destaca a linha quando o mouse passa por cima"""
        item = self.treeview_historico.identify_row(event.y)
        if item:
            self.treeview_historico.tk.call(self.treeview_historico, "tag", "remove", "hover")
            self.treeview_historico.tk.call(self.treeview_historico, "tag", "add", "hover", item)
    
    def _on_treeview_leave(self, event):
        # Remover tag de hover quando o mouse sai da treeview
        self.treeview_historico.tk.call(self.treeview_historico, "tag", "remove", "hover")

    def gerenciar_observacoes(self):
        # Verificar se há uma série e ano letivo selecionados
        if not self.serie_selecionada.get() or not self.ano_letivo_selecionado.get():
            messagebox.showwarning("Aviso", "Selecione uma série e ano letivo primeiro!")
            return
            
        # Obter os IDs necessários
        serie_id = self.series_map.get(self.serie_selecionada.get())
        ano_letivo_id = self.anos_letivos_map.get(self.ano_letivo_selecionado.get())
        escola_id = self.escolas_map.get(self.escola_selecionada.get())
        
        if not all([serie_id, ano_letivo_id, escola_id]):
            messagebox.showwarning("Aviso", "Dados incompletos para gerenciar observações!")
            return
            
        # Criar janela para gerenciar observações
        janela_obs = tk.Toplevel(self.janela)
        janela_obs.title("Gerenciar Observações do Histórico")
        janela_obs.geometry("600x400")
        janela_obs.configure(bg=self.co9)
        
        # Frame para o texto da observação
        frame_obs = tk.Frame(janela_obs, bg=self.co9)
        frame_obs.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Label e Text widget para a observação
        tk.Label(frame_obs, text="Observação:", bg=self.co9, font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Criar Text widget com scrollbar
        frame_texto = tk.Frame(frame_obs, bg=self.co9)
        frame_texto.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(frame_texto)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        texto_obs = tk.Text(frame_texto, height=10, width=50, yscrollcommand=scrollbar.set)
        texto_obs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=texto_obs.yview)
        
        # Carregar observação existente se houver
        conn = self.validar_conexao_bd()
        if conn is None:
            return
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT observacao 
                FROM observacoes_historico 
                WHERE serie_id = %s AND ano_letivo_id = %s AND escola_id = %s
            """, self._safe_sql_params(serie_id, ano_letivo_id, escola_id))
            resultado = cursor.fetchone()
            if resultado:
                texto_obs.insert("1.0", self._safe_str_value(resultado[0]))
        finally:
            cursor.close()
            conn.close()
        
        # Frame para os botões
        frame_botoes = tk.Frame(janela_obs, bg=self.co9)
        frame_botoes.pack(fill=tk.X, padx=10, pady=10)
        
        def salvar_observacao():
            observacao = texto_obs.get("1.0", tk.END).strip()
            
            conn = self.validar_conexao_bd()
            if conn is None:
                return
            cursor = conn.cursor()
            try:
                # Verificar se já existe uma observação
                cursor.execute("""
                    SELECT id FROM observacoes_historico 
                    WHERE serie_id = %s AND ano_letivo_id = %s AND escola_id = %s
                """, self._safe_sql_params(serie_id, ano_letivo_id, escola_id))
                resultado = cursor.fetchone()
                
                if resultado:
                    # Atualizar observação existente
                    cursor.execute("""
                        UPDATE observacoes_historico 
                        SET observacao = %s 
                        WHERE id = %s
                    """, self._safe_sql_params(observacao, resultado[0]))
                else:
                    # Inserir nova observação
                    cursor.execute("""
                        INSERT INTO observacoes_historico 
                        (serie_id, ano_letivo_id, escola_id, observacao) 
                        VALUES (%s, %s, %s, %s)
                    """, self._safe_sql_params(serie_id, ano_letivo_id, escola_id, observacao))
                
                conn.commit()
                messagebox.showinfo("Sucesso", "Observação salva com sucesso!")
                janela_obs.destroy()
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Erro", f"Erro ao salvar observação: {str(e)}")
            finally:
                cursor.close()
                conn.close()
        
        def excluir_observacao():
            if messagebox.askyesno("Confirmar", "Deseja realmente excluir esta observação?"):
                conn = self.validar_conexao_bd()
                if conn is None:
                    return
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        DELETE FROM observacoes_historico 
                        WHERE serie_id = %s AND ano_letivo_id = %s AND escola_id = %s
                    """, self._safe_sql_params(serie_id, ano_letivo_id, escola_id))
                    conn.commit()
                    messagebox.showinfo("Sucesso", "Observação excluída com sucesso!")
                    janela_obs.destroy()
                except Exception as e:
                    conn.rollback()
                    messagebox.showerror("Erro", f"Erro ao excluir observação: {str(e)}")
                finally:
                    cursor.close()
                    conn.close()
        
        # Botões
        btn_salvar = tk.Button(frame_botoes, text="Salvar", command=salvar_observacao, 
                             bg=self.co3, fg=self.co1, width=15)
        btn_salvar.pack(side=tk.LEFT, padx=5)
        
        btn_excluir = tk.Button(frame_botoes, text="Excluir", command=excluir_observacao,
                              bg=self.co6, fg=self.co1, width=15)
        btn_excluir.pack(side=tk.LEFT, padx=5)
        
        btn_cancelar = tk.Button(frame_botoes, text="Cancelar", command=janela_obs.destroy,
                               bg=self.co0, fg=self.co1, width=15)
        btn_cancelar.pack(side=tk.LEFT, padx=5)

    def _solicitar_credenciais_geduc(self):
        """Solicita credenciais do GEDUC ao usuário"""
        janela_cred = tk.Toplevel(self.janela)
        janela_cred.title("Credenciais GEDUC")
        janela_cred.geometry("400x250")
        janela_cred.resizable(False, False)
        janela_cred.grab_set()
        
        # Centralizar
        janela_cred.update_idletasks()
        x = (janela_cred.winfo_screenwidth() // 2) - (400 // 2)
        y = (janela_cred.winfo_screenheight() // 2) - (250 // 2)
        janela_cred.geometry(f'400x250+{x}+{y}')
        
        # Título
        tk.Label(
            janela_cred,
            text="🔐 Acesso ao GEDUC",
            font=("Arial", 14, "bold"),
            bg=self.co3,
            fg=self.co1
        ).pack(fill="x", pady=(0, 20))
        
        # Frame para campos
        frame_campos = tk.Frame(janela_cred)
        frame_campos.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Usuário
        tk.Label(frame_campos, text="Usuário:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=5)
        entry_usuario = tk.Entry(frame_campos, font=("Arial", 10), width=30)
        entry_usuario.grid(row=0, column=1, pady=5, padx=5)
        
        # Senha
        tk.Label(frame_campos, text="Senha:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=5)
        entry_senha = tk.Entry(frame_campos, font=("Arial", 10), width=30, show="*")
        entry_senha.grid(row=1, column=1, pady=5, padx=5)
        
        # Info
        tk.Label(
            frame_campos,
            text="⚠️ Credenciais do sistema GEDUC online",
            font=("Arial", 8),
            fg=self.co4
        ).grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        # Variável para armazenar resultado
        resultado = {}
        resultado['confirmado'] = False
        
        def confirmar():
            usuario = entry_usuario.get().strip()
            senha = entry_senha.get().strip()
            
            if not usuario or not senha:
                messagebox.showwarning("Aviso", "Preencha usuário e senha!")
                return
            
            resultado['confirmado'] = True
            resultado['usuario'] = usuario
            resultado['senha'] = senha
            janela_cred.destroy()
        
        def cancelar():
            janela_cred.destroy()
        
        # Frame de botões
        frame_botoes = tk.Frame(frame_campos)
        frame_botoes.grid(row=3, column=0, columnspan=2, pady=20)
        
        tk.Button(
            frame_botoes,
            text="Conectar",
            command=confirmar,
            bg=self.co3,
            fg=self.co1,
            font=("Arial", 10, "bold"),
            width=12
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_botoes,
            text="Cancelar",
            command=cancelar,
            bg=self.co6,
            fg=self.co1,
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
    
    def exportar_para_geduc(self):
        """Exportar histórico escolar do aluno selecionado para o GEDUC"""
        if not self.aluno_id:
            messagebox.showwarning("Aviso", "Selecione um aluno primeiro!")
            return
        
        try:
            from src.exportadores.geduc_exportador import exportar_historico_aluno
            
            # 1. Buscar dados do aluno
            conn = conectar_bd()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT nome, matricula 
                FROM alunos 
                WHERE idaluno = %s
            """, (self.aluno_id,))
            
            aluno_dados = cursor.fetchone()
            if not aluno_dados:
                messagebox.showerror("Erro", "Aluno não encontrado no banco de dados!")
                return
            
            nome_aluno, matricula_aluno = aluno_dados
            
            # 2. Buscar histórico escolar
            cursor.execute("""
                SELECT 
                    h.id,
                    h.disciplina_id,
                    d.nome AS disciplina_nome,
                    h.ano_letivo_id,
                    al.ano_letivo,
                    h.serie_id,
                    s.nome AS serie_nome,
                    h.escola_id,
                    e.nome AS escola_nome,
                    h.media,
                    h.conceito,
                    h.carga_horaria,
                    h.faltas,
                    h.situacao
                FROM historico_escolar h
                INNER JOIN disciplinas d ON h.disciplina_id = d.id
                INNER JOIN anosletivos al ON h.ano_letivo_id = al.id
                INNER JOIN series s ON h.serie_id = s.id
                INNER JOIN escolas e ON h.escola_id = e.id
                WHERE h.aluno_id = %s
                ORDER BY al.ano_letivo DESC, s.id, d.nome
            """, (self.aluno_id,))
            
            registros = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not registros:
                messagebox.showwarning(
                    "Sem Dados",
                    f"Não há histórico escolar para {nome_aluno}.\n\n"
                    "Cadastre pelo menos uma disciplina antes de exportar."
                )
                return
            
            # 3. Confirmar exportação
            resposta = messagebox.askyesno(
                "Confirmar Exportação",
                f"📤 EXPORTAR PARA GEDUC\n\n"
                f"Aluno: {nome_aluno}\n"
                f"Matrícula: {matricula_aluno or 'N/A'}\n"
                f"Registros: {len(registros)} disciplina(s)\n\n"
                f"⚙️ Este processo irá:\n"
                f"1. Abrir navegador Chrome\n"
                f"2. Fazer login no GEDUC (você resolverá o reCAPTCHA)\n"
                f"3. Buscar aluno pelo nome\n"
                f"4. Preencher formulário de histórico\n"
                f"5. Enviar dados\n\n"
                f"⏱️ Tempo estimado: 2-3 minutos\n\n"
                f"Continuar?"
            )
            
            if not resposta:
                return
            
            # 4. Solicitar credenciais
            credenciais = self._solicitar_credenciais_geduc()
            if not credenciais:
                return
            
            # 5. Montar dados para exportação
            # IMPORTANTE: Estes valores precisam ser configurados conforme SEU ambiente GEDUC
            # TODO: Criar tabela de mapeamento ou arquivo de configuração
            dados_historico = {
                'nome_aluno': nome_aluno,  # Sistema buscará ID automaticamente
                
                # Valores fixos (AJUSTAR CONFORME SEU GEDUC!)
                'idinstituicao': 1318,  # TODO: Obter do config
                'ano': datetime.now().year,  # Ano atual
                'idcurso': 4,  # TODO: Mapear série → ID curso GEDUC
                'idcurriculo': 69,  # TODO: Obter do GEDUC ou config
                'tipoescola': 1,  # 1=Regular
                'visivel': 1,  # Histórico visível
                
                # Disciplinas do histórico
                'disciplinas': []
            }
            
            # Converter registros para formato GEDUC
            for registro in registros:
                # TODO: Mapear disciplina_id local → ID GEDUC
                # Por enquanto, usando ID local (precisa de tabela de mapeamento)
                disciplina_geduc = {
                    'id': str(registro[1]),  # ID da disciplina (precisa mapear!)
                    'cht': str(registro[11] or 40),  # Carga horária total
                    'media': str(registro[9] or ''),  # Média
                    'falta': str(registro[12] or 0),  # Faltas
                    'situacao': str(registro[13] or '0')  # Situação (0=Aprovado)
                }
                dados_historico['disciplinas'].append(disciplina_geduc)
            
            # 6. Criar janela de progresso
            janela_progresso = tk.Toplevel(self.janela)
            janela_progresso.title("Exportando para GEDUC")
            janela_progresso.geometry("500x300")
            janela_progresso.transient(self.janela)
            janela_progresso.grab_set()
            
            # Centralizar
            janela_progresso.update_idletasks()
            x = (janela_progresso.winfo_screenwidth() // 2) - (500 // 2)
            y = (janela_progresso.winfo_screenheight() // 2) - (300 // 2)
            janela_progresso.geometry(f'500x300+{x}+{y}')
            
            # Título
            tk.Label(
                janela_progresso,
                text="🌐 Exportando para GEDUC",
                font=("Arial", 14, "bold"),
                bg=self.co5,
                fg=self.co1
            ).pack(fill="x", pady=(0, 10))
            
            # Área de log
            frame_log = tk.Frame(janela_progresso)
            frame_log.pack(fill="both", expand=True, padx=10, pady=10)
            
            text_log = tk.Text(frame_log, height=12, font=("Consolas", 9), bg="white", fg="black", wrap=tk.WORD)
            text_log.pack(side="left", fill="both", expand=True)
            
            scrollbar = tk.Scrollbar(frame_log, command=text_log.yview)
            scrollbar.pack(side="right", fill="y")
            text_log.config(yscrollcommand=scrollbar.set)
            
            # Barra de progresso
            progresso = ttk.Progressbar(janela_progresso, mode='indeterminate')
            progresso.pack(pady=10, padx=20, fill=tk.X)
            progresso.start(10)
            
            # Função de callback para atualizar log
            def atualizar_log(mensagem):
                text_log.insert(tk.END, f"{mensagem}\n")
                text_log.see(tk.END)
                janela_progresso.update()
            
            # 7. Executar exportação em thread
            def executar_exportacao():
                try:
                    atualizar_log("="*50)
                    atualizar_log(f"Aluno: {nome_aluno}")
                    atualizar_log(f"Disciplinas: {len(dados_historico['disciplinas'])}")
                    atualizar_log("="*50)
                    atualizar_log("")
                    
                    # Chamar função de exportação
                    resultado = exportar_historico_aluno(
                        aluno_id=self.aluno_id,
                        usuario_geduc=credenciais['usuario'],
                        senha_geduc=credenciais['senha'],
                        dados_historico=dados_historico,
                        callback_progresso=atualizar_log
                    )
                    
                    # Atualizar UI
                    self.janela.after(0, lambda: finalizar_exportacao(resultado))
                    
                except Exception as e:
                    _logger.exception(f"Erro durante exportação: {e}")
                    self.janela.after(0, lambda: erro_exportacao(str(e)))
            
            def finalizar_exportacao(resultado):
                progresso.stop()
                atualizar_log("")
                atualizar_log("="*50)
                
                if resultado['sucesso']:
                    atualizar_log("✅ EXPORTAÇÃO CONCLUÍDA COM SUCESSO!")
                    atualizar_log(f"Registros enviados: {resultado.get('registros_enviados', 0)}")
                    atualizar_log(f"Mensagem: {resultado.get('mensagem', 'N/A')}")
                    atualizar_log("="*50)
                    
                    # Botão fechar
                    tk.Button(
                        janela_progresso,
                        text="Fechar",
                        command=janela_progresso.destroy,
                        bg=self.co3,
                        fg=self.co1,
                        font=("Arial", 10, "bold"),
                        width=15
                    ).pack(pady=10)
                else:
                    atualizar_log("❌ EXPORTAÇÃO FALHOU!")
                    atualizar_log(f"Erro: {resultado.get('erro', 'Erro desconhecido')}")
                    atualizar_log("="*50)
                    
                    # Botão fechar
                    tk.Button(
                        janela_progresso,
                        text="Fechar",
                        command=janela_progresso.destroy,
                        bg=self.co6,
                        fg=self.co1,
                        font=("Arial", 10, "bold"),
                        width=15
                    ).pack(pady=10)
            
            def erro_exportacao(mensagem):
                progresso.stop()
                atualizar_log("")
                atualizar_log("="*50)
                atualizar_log("❌ ERRO INESPERADO!")
                atualizar_log(str(mensagem))
                atualizar_log("="*50)
                
                # Botão fechar
                tk.Button(
                    janela_progresso,
                    text="Fechar",
                    command=janela_progresso.destroy,
                    bg=self.co6,
                    fg=self.co1,
                    font=("Arial", 10, "bold"),
                    width=15
                ).pack(pady=10)
            
            # Iniciar thread
            import threading
            thread = threading.Thread(target=executar_exportacao, daemon=True)
            thread.start()
            
        except ImportError as e:
            messagebox.showerror(
                "Módulo não disponível",
                f"O módulo de exportação GEDUC não está disponível.\n\n"
                f"Erro: {str(e)}\n\n"
                "Verifique se o arquivo src/exportadores/geduc_exportador.py existe."
            )
        except Exception as e:
            _logger.exception(f"Erro inesperado: {e}")
            messagebox.showerror("Erro", f"Erro inesperado:\n{str(e)}")


if __name__ == "__main__":
    app = InterfaceHistoricoEscolar()
    app.janela.mainloop() 