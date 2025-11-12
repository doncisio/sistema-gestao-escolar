import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkinter.font import Font
import os
import sys
import re
import pandas as pd
from datetime import datetime, date
from conexao import conectar_bd
from historico_escolar import historico_escolar

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
        
        # Preencher os comboboxes
        self.carregar_dados()
        
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
            # Se já é uma string formatada
            if isinstance(data_obj, str):
                # Tentar converter string para datetime para validar formato
                if len(data_obj) == 10 and '/' in data_obj:
                    return data_obj  # Já está no formato dd/mm/yyyy
                elif len(data_obj) == 10 and '-' in data_obj:
                    # Formato yyyy-mm-dd, converter para dd/mm/yyyy
                    partes = data_obj.split('-')
                    if len(partes) == 3:
                        return f"{partes[2]}/{partes[1]}/{partes[0]}"
                
            # Se é objeto datetime ou date
            if isinstance(data_obj, (datetime, date)):
                return data_obj.strftime('%d/%m/%Y')
                
            # Se é um número (timestamp)
            if isinstance(data_obj, (int, float)):
                try:
                    data_convertida = datetime.fromtimestamp(data_obj)
                    return data_convertida.strftime('%d/%m/%Y')
                except:
                    pass
                    
            # Tentar converter string para datetime
            if isinstance(data_obj, str):
                # Tentar diferentes formatos
                formatos = ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y']
                for formato in formatos:
                    try:
                        data_convertida = datetime.strptime(data_obj, formato)
                        return data_convertida.strftime('%d/%m/%Y')
                    except:
                        continue
                        
        except Exception as e:
            print(f"Erro ao formatar data: {e}")
            
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
                FROM serie 
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
            print(f"Erro ao carregar dados: {str(e)}")
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
        self.ent_media.bind("<Return>", lambda event: self.inserir_registro())
        
        tk.Label(self.frame_form, text="Conceito:").grid(row=2, column=4, padx=5, pady=5, sticky=tk.W)
        self.cb_conceito = ttk.Combobox(self.frame_form, textvariable=self.conceito)
        self.cb_conceito['values'] = ['', 'R', 'B', 'O', 'AD', 'PNAD', 'APNAD', 'RT']
        self.ajustar_largura_combobox(self.cb_conceito, self.cb_conceito['values'])
        self.cb_conceito.grid(row=2, column=5, padx=5, pady=5, sticky=tk.EW)
        
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
        
        btn_relatorio = tk.Button(frame_botoes, text="Relatório de Desempenho", command=self.gerar_relatorio_desempenho, 
                                bg="#9C27B0", fg=self.co1, width=20)
        btn_relatorio.grid(row=0, column=5, padx=5)
        
        # Adicionando botão para visualizar matriz de séries x disciplinas
        btn_matriz = tk.Button(frame_botoes, text="Visualizar Matriz", command=self.abrir_matriz_series_disciplinas, 
                             bg="#2196F3", fg=self.co1, width=15)
        btn_matriz.grid(row=0, column=6, padx=5)
        
        btn_importar = tk.Button(frame_botoes, text="Importar Excel", command=self.importar_excel, bg="#8D6E63", fg=self.co1, width=15)
        btn_importar.grid(row=0, column=7, padx=5)
        
        # Botão Voltar para a página principal
        btn_voltar = tk.Button(frame_botoes, text="Voltar", command=self.voltar_pagina_principal, bg="#FF9800", fg=self.co1, width=15)
        btn_voltar.grid(row=0, column=8, padx=5)
        
        # Adicionar botão para gerenciar observações
        btn_observacoes = tk.Button(frame_botoes, text="Observações", command=self.gerenciar_observacoes, bg=self.co5, fg=self.co1, width=15)
        btn_observacoes.grid(row=0, column=9, padx=5)
        
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
            # Processar anos letivos
            anos_letivos = dados['anos_letivos']
            anos_letivos.sort(key=lambda x: x[1], reverse=True)  # Ordenar por ano decrescente
            self.anos_letivos_map = {str(ano): id for id, ano in anos_letivos}
            anos_letivos_valores = [str(ano) for id, ano in anos_letivos]
            self.cb_ano_letivo['values'] = anos_letivos_valores
            self.ajustar_largura_combobox(self.cb_ano_letivo, anos_letivos_valores)
            
            # Processar séries
            series = dados['series']
            series.sort(key=lambda x: x[1])  # Ordenar por nome
            self.series_map = {nome: id for id, nome in series}
            series_valores = [nome for id, nome in series]
            self.cb_serie['values'] = series_valores
            self.ajustar_largura_combobox(self.cb_serie, series_valores)
            
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
            self.ajustar_largura_combobox(self.cb_escola, escolas_valores)
            
            # Processar disciplinas
            disciplinas = dados['disciplinas']
            disciplinas.sort(key=lambda x: x[1])  # Ordenar por nome
            self.disciplinas_map = {nome: id for id, nome, escola_id, nivel_id in disciplinas}
            # Armazenar também mapeamento completo para uso posterior
            self.disciplinas_completo = {id: {'nome': nome, 'escola_id': escola_id, 'nivel_id': nivel_id} 
                                       for id, nome, escola_id, nivel_id in disciplinas}
            disciplinas_valores = [nome for id, nome, escola_id, nivel_id in disciplinas]
            self.cb_disciplina['values'] = disciplinas_valores
            self.ajustar_largura_combobox(self.cb_disciplina, disciplinas_valores)
            
            # Carregar alunos em separado (pode ser paginado)
            self.carregar_alunos_otimizado()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar dados: {str(e)}")
            print(f"Erro ao processar dados: {str(e)}")

    def carregar_alunos_otimizado(self):
        """Carrega a lista de alunos para a combobox de forma otimizada"""
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
            print(f"Erro ao aplicar resultados: {str(e)}")

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
                    print(f"Erro ao buscar detalhes do aluno: {str(e)}")
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
            print(f"Erro ao selecionar aluno: {str(e)}")
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
                INNER JOIN serie s ON h.serie_id = s.id
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
            print(f"Erro ao carregar histórico: {str(e)}")
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
            print(f"Erro ao aplicar dados do histórico: {str(e)}")
    
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
                LEFT JOIN serie s ON h.serie_id = s.id
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
        
        # Obter IDs dos campos
        try:
            disciplina_id, serie_id, ano_letivo_id, escola_id = self.obter_ids_dos_campos()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter IDs dos campos: {str(e)}")
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
            
        # Chamar a função para gerar o PDF
        historico_escolar(self.aluno_id)
        self.mostrar_mensagem_temporaria("Histórico escolar gerado com sucesso!")

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
                    print(f"Erro na linha {linha_numero}: {str(e)}")
                    
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
                LEFT JOIN serie s ON s.id = %s
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
            print(f"Erro ao atualizar disciplinas: {str(e)}")
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
            print(f"Erro ao aplicar disciplinas: {str(e)}")
    
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
            print(f"Erro no fallback de disciplinas: {str(e)}")
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
            INNER JOIN serie s ON h.serie_id = s.id
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
            print(f"Erro ao aplicar filtros: {str(e)}")
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
            print(f"Erro ao aplicar registros filtrados: {str(e)}")
    
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

    def gerar_relatorio_desempenho(self):
        """Gera um relatório de desempenho do aluno"""
        if not hasattr(self, 'aluno_id'):
            messagebox.showerror("Erro", "Selecione um aluno primeiro.")
            return
            
        try:
            conn = self.validar_conexao_bd()
            if conn is None:
                return
            cursor = conn.cursor()
            
            # Buscar informações do aluno
            cursor.execute("""
                SELECT nome, data_nascimento
                FROM alunos
                WHERE id = %s
            """, (self.aluno_id,))
            
            aluno = cursor.fetchone()
            
            if not aluno:
                messagebox.showerror("Erro", "Aluno não encontrado.")
                return
                
            # Buscar médias por disciplina
            cursor.execute("""
                SELECT 
                    d.nome AS disciplina,
                    AVG(h.media) AS media_geral,
                    COUNT(*) AS total_registros,
                    SUM(CASE WHEN h.media >= 6 OR h.conceito IN ('AD', 'PNAD', 'APNAD') 
                        THEN 1 ELSE 0 END) AS aprovacoes
                FROM historico_escolar h
                JOIN disciplinas d ON h.disciplina_id = d.id
                WHERE h.aluno_id = %s
                GROUP BY d.nome
                ORDER BY d.nome
            """, (self.aluno_id,))
            
            desempenho = cursor.fetchall()
            
            # Gerar relatório em PDF
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from datetime import datetime
            import os
            
            # Criar diretório para relatórios se não existir
            if not os.path.exists("relatorios"):
                os.makedirs("relatorios")
                
            # Nome do arquivo
            nome_arquivo = f"relatorios/desempenho_{self.aluno_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Criar documento
            doc = SimpleDocTemplate(nome_arquivo, pagesize=letter)
            elements = []
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30
            )
            
            # Título
            elements.append(Paragraph(f"Relatório de Desempenho - {aluno[0]}", title_style))
            elements.append(Spacer(1, 12))
            
            # Dados do aluno
            data_nascimento = self.formatar_data_nascimento(aluno[1])
            elements.append(Paragraph(f"Data de Nascimento: {data_nascimento}", styles["Normal"]))
            elements.append(Spacer(1, 12))
            
            # Tabela de desempenho
            data = [["Disciplina", "Média Geral", "Total de Registros", "Aprovações", "Taxa de Aprovação"]]
            
            for disc in desempenho:
                try:
                    # Garantir conversões seguras para cálculos
                    total_registros = self._safe_float_value(disc[2])
                    aprovacoes = self._safe_float_value(disc[3])
                    taxa_aprovacao = (aprovacoes / total_registros * 100) if total_registros > 0 else 0
                    
                    data.append([
                        str(disc[0]) if disc[0] is not None else "",
                        self._safe_float_format(disc[1]),
                        str(int(total_registros)),
                        str(int(aprovacoes)),
                        f"{taxa_aprovacao:.1f}%"
                    ])
                except (ValueError, TypeError, ZeroDivisionError) as e:
                    # Em caso de erro, usar valores padrão
                    data.append([
                        str(disc[0]) if disc[0] is not None else "",
                        "N/A",
                        "0",
                        "0",
                        "0.0%"
                    ])
                
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            
            # Gerar PDF
            doc.build(elements)
            
            # Abrir o arquivo
            os.startfile(nome_arquivo)
            
            # Mostrar uma mensagem de sucesso
            self.mostrar_mensagem_temporaria("Relatório de desempenho gerado com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar relatório: {str(e)}")
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    def abrir_matriz_series_disciplinas(self):
        """Abre a visualização da matriz de séries x disciplinas."""
        try:
            # Primeiro, abrir uma janela de seleção de escola
            janela_selecao_escola = tk.Toplevel(self.janela)
            janela_selecao_escola.title("Selecionar Escola")
            janela_selecao_escola.geometry("500x250")
            janela_selecao_escola.configure(bg=self.co9)
            janela_selecao_escola.transient(self.janela)
            janela_selecao_escola.grab_set()  # Torna a janela modal
            
            # Frame principal
            frame_selecao = tk.Frame(janela_selecao_escola, bg=self.co9, padx=20, pady=20)
            frame_selecao.pack(fill=tk.BOTH, expand=True)
            
            # Título
            tk.Label(frame_selecao, text="Selecione uma Escola", 
                   font=("Arial", 14, "bold"), bg=self.co9, fg=self.co4).pack(pady=(0, 20))
            
            # Combobox para seleção de escola
            tk.Label(frame_selecao, text="Escola:", bg=self.co9, fg=self.co4).pack(anchor=tk.W, pady=(10, 5))
            escola_var = tk.StringVar()
            cb_escola = ttk.Combobox(frame_selecao, textvariable=escola_var, width=40)
            cb_escola.pack(fill=tk.X, pady=(0, 15))
            
            # Carregar escolas
            escolas = []
            conn = None
            cursor = None
            
            try:
                conn = self.validar_conexao_bd()
                if conn is None:
                    return
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome FROM escolas ORDER BY nome")
                escolas = cursor.fetchall()
                cb_escola['values'] = [f"{id} - {nome}" for id, nome in escolas]
                if escolas:
                    cb_escola.current(0)  # Selecionar o primeiro por padrão
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar escolas: {str(e)}")
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            
            # Frame para botões
            frame_botoes = tk.Frame(frame_selecao, bg=self.co9)
            frame_botoes.pack(fill=tk.X, pady=15)
            
            # Botão de cancelar
            btn_cancelar = tk.Button(frame_botoes, text="Cancelar", 
                                   command=janela_selecao_escola.destroy,
                                   bg="#9E9E9E", fg="white", padx=15, pady=5)
            btn_cancelar.pack(side=tk.RIGHT, padx=5)
            
            # Botão de confirmar
            def confirmar_selecao():
                # Verificar se uma escola foi selecionada
                if not escola_var.get():
                    messagebox.showwarning("Aviso", "Por favor, selecione uma escola.")
                    return
                
                # Extrair o ID da escola selecionada
                escola_id = int(escola_var.get().split(' - ')[0])
                escola_nome = ' - '.join(escola_var.get().split(' - ')[1:])
                
                # Fechar janela de seleção
                janela_selecao_escola.destroy()
                
                # Abrir a matriz com a escola selecionada
                self.abrir_matriz_com_escola(escola_id, escola_nome)
            
            btn_confirmar = tk.Button(frame_botoes, text="Confirmar", 
                                    command=confirmar_selecao,
                                    bg="#4CAF50", fg="white", padx=15, pady=5)
            btn_confirmar.pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir seleção de escola: {str(e)}")
    
    def abrir_matriz_com_escola(self, escola_id, escola_nome):
        """Abre a matriz de séries x disciplinas para a escola selecionada."""
        try:
            # Criar a janela da matriz
            janela_matriz = tk.Toplevel(self.janela)
            janela_matriz.title(f"Matriz de Séries x Disciplinas - {escola_nome}")
            janela_matriz.geometry("950x650")
            janela_matriz.configure(bg=self.co1)
            
            # Frame para o título
            frame_titulo = tk.Frame(janela_matriz, bg=self.co9, height=70)
            frame_titulo.pack(fill=tk.X)
            
            # Título
            titulo = tk.Label(frame_titulo, text=f"Matriz de Séries x Disciplinas - {escola_nome}",
                           font=("Arial", 14, "bold"), bg=self.co9, fg=self.co1)
            titulo.pack(pady=20)
            
            # Verificar se há um aluno selecionado
            if not self.aluno_selecionado.get():
                aluno_texto = "Visualização Geral"
            else:
                aluno_texto = f"Aluno: {self.aluno_selecionado.get()}"
            
            # Subtítulo com aluno selecionado
            subtitulo = tk.Label(frame_titulo, text=aluno_texto,
                              font=("Arial", 11), bg=self.co9, fg=self.co1)
            subtitulo.pack(pady=(0, 10))
            
            # Frame para o controle de visualização
            frame_controle = tk.Frame(janela_matriz, bg=self.co1, padx=10, pady=10)
            frame_controle.pack(fill=tk.X)
            
            # Botão para alternar entre modo tabela e modo cartões
            modo_var = tk.StringVar(value="tabela")
            btn_alternar = tk.Button(frame_controle, text="Alternar Visualização",
                                   bg=self.co4, fg="white", padx=10, pady=5)
            btn_alternar.pack(side=tk.LEFT)
            
            # Container para as visualizações
            container_frame = tk.Frame(janela_matriz, bg=self.co1, padx=10, pady=10)
            container_frame.pack(fill=tk.BOTH, expand=True)
            
            # Frames para cada modo de visualização
            frame_tabela = tk.Frame(container_frame, bg=self.co1)
            frame_cartoes = tk.Frame(container_frame, bg=self.co1)
            
            # Configurar scrollbars
            canvas_tabela = tk.Canvas(frame_tabela, bg=self.co1)
            frame_conteudo_tabela = tk.Frame(canvas_tabela, bg=self.co1)
            
            canvas_cartoes = tk.Canvas(frame_cartoes, bg=self.co1)
            frame_conteudo_cartoes = tk.Frame(canvas_cartoes, bg=self.co1)
            
            # Função para alternar entre os modos de visualização
            def alternar_modo():
                if modo_var.get() == "tabela":
                    modo_var.set("cartoes")
                    frame_tabela.pack_forget()
                    frame_cartoes.pack(fill=tk.BOTH, expand=True)
                    btn_alternar.config(text="Visualizar em Tabela")
                else:
                    # Mudança para modo tabela
                    modo_var.set("tabela")
                    frame_cartoes.pack_forget()
                    frame_tabela.pack(fill=tk.BOTH, expand=True)
                    btn_alternar.config(text="Visualizar em Cartões")
            
            btn_alternar.config(command=alternar_modo)
            
            # Carregar dados para a matriz
            conn = self.validar_conexao_bd()
            if conn is None:
                return
            cursor = conn.cursor()
            
            # Definir as cores das séries para uso nos cartões
            cores_series = {
                3: ("#4CAF50", "#E8F5E9"),  # Verde - 3º ano
                4: ("#2196F3", "#E3F2FD"),  # Azul - 4º ano
                5: ("#9C27B0", "#F3E5F5"),  # Roxo - 5º ano
                6: ("#FF9800", "#FFF3E0"),  # Laranja - 6º ano
                7: ("#F44336", "#FFEBEE"),  # Vermelho - 7º ano
                8: ("#795548", "#EFEBE9"),  # Marrom - 8º ano
                9: ("#607D8B", "#ECEFF1"),  # Azul cinza - 9º ano
                10: ("#673AB7", "#EDE7F6"), # Roxo profundo - 1º ano (EM)
                11: ("#E91E63", "#FCE4EC")  # Rosa - 2º ano (EM)
            }
            
            # Recuperar séries disponíveis
            cursor.execute("SELECT id, nome FROM serie ORDER BY id")
            series = cursor.fetchall()
            
            # Mapeamento de IDs para nomes de séries
            series_nomes = {serie[0]: serie[1] for serie in series}
            
            # Recuperar disciplinas da escola selecionada
            cursor.execute("""
                SELECT d.id, d.nome 
                FROM disciplinas d
                WHERE d.escola_id = %s
                ORDER BY d.nome
            """, (escola_id,))
            disciplinas = cursor.fetchall()
            
            # Estrutura para armazenar os dados
            dados_matriz = {}
            
            # Se um aluno estiver selecionado, carregar seus dados
            if self.aluno_id:
                # Verificar se a coluna carga_horaria existe
                cursor.execute("SHOW COLUMNS FROM historico_escolar LIKE 'carga_horaria'")
                tem_carga_horaria = cursor.fetchone() is not None
                
                # Consulta adaptativa baseada na existência da coluna carga_horaria
                if tem_carga_horaria:
                    consulta_sql = """
                        SELECT h.disciplina_id, h.serie_id, 
                              CASE 
                                  WHEN h.media IS NOT NULL THEN CONCAT(ROUND(h.media/10, 1))
                                  WHEN h.conceito IS NOT NULL THEN h.conceito
                                  ELSE NULL
                              END as valor,
                              CASE 
                                  WHEN h.carga_horaria IS NOT NULL THEN CONCAT('\nCH: ', h.carga_horaria, 'h')
                                  ELSE ''
                              END as ch,
                              al.ano_letivo
                        FROM historico_escolar h
                        JOIN disciplinas d ON h.disciplina_id = d.id
                        JOIN anosletivos al ON h.ano_letivo_id = al.id
                        WHERE h.aluno_id = %s AND d.escola_id = %s
                        ORDER BY h.disciplina_id, h.serie_id
                    """
                else:
                    consulta_sql = """
                        SELECT h.disciplina_id, h.serie_id, 
                              CASE 
                                  WHEN h.media IS NOT NULL THEN CONCAT(ROUND(h.media/10, 1))
                                  WHEN h.conceito IS NOT NULL THEN h.conceito
                                  ELSE NULL
                              END as valor,
                              '' as ch,
                              al.ano_letivo
                        FROM historico_escolar h
                        JOIN disciplinas d ON h.disciplina_id = d.id
                        JOIN anosletivos al ON h.ano_letivo_id = al.id
                        WHERE h.aluno_id = %s AND d.escola_id = %s
                        ORDER BY h.disciplina_id, h.serie_id
                    """
                    
                cursor.execute(consulta_sql, (self.aluno_id, escola_id))
                registros = cursor.fetchall()
                
                # Inicializar a estrutura de dados
                for disciplina_id, disciplina_nome in disciplinas:
                    dados_matriz[disciplina_id] = {
                        "nome": disciplina_nome,
                        "series": {}
                    }
                
                # Preencher com os dados do aluno
                for disciplina_id, serie_id, valor, ch, ano_letivo in registros:
                    # Garantir que a disciplina existe no dicionário
                    if disciplina_id not in dados_matriz:
                        # Buscar o nome da disciplina
                        cursor.execute("SELECT nome FROM disciplinas WHERE id = %s", self._safe_sql_params(disciplina_id))
                        result = cursor.fetchone()
                        disciplina_nome = result[0] if result else "Disciplina Desconhecida"
                        dados_matriz[disciplina_id] = {
                            "nome": disciplina_nome,
                            "series": {}
                        }
                    
                    # Adicionar valor e carga horária
                    valor_formatado = f"{valor}{ch if ch else ''}"
                    if ano_letivo:
                        valor_formatado = f"{valor_formatado}\n({ano_letivo})"
                    
                    dados_matriz[disciplina_id]["series"][serie_id] = valor_formatado
            else:
                # Inicializar a estrutura de dados sem dados específicos de aluno
                for disciplina_id, disciplina_nome in disciplinas:
                    dados_matriz[disciplina_id] = {
                        "nome": disciplina_nome,
                        "series": {}
                    }
                    
            # Estilos para os cabeçalhos e células
            header_style = {
                "font": ("Arial", 11, "bold"),
                "bg": self.co1,
                "fg": "white",
                "height": 2,
                "padx": 10
            }
            
            row_header_style = {
                "font": ("Arial", 10),
                "bg": self.co1,
                "fg": "white",
                "height": 2,
                "padx": 10,
                "anchor": "w"
            }
            
            cell_style = {
                "font": ("Arial", 10),
                "bg": "#F5F5F5",
                "fg": "#333333",
                "height": 2,
                "padx": 5,
                "pady": 5
            }
            
            alt_cell_style = {
                "font": ("Arial", 10),
                "bg": "#EEEEEE",
                "fg": "#333333",
                "height": 2,
                "padx": 5,
                "pady": 5
            }
            
            titulo_cartao_style = {
                "font": ("Arial", 12, "bold"),
                "padx": 15,
                "pady": 8
            }
            
            # === PREENCHER O MODO TABELA ===
            # Criar uma treeview para exibir os dados em forma de tabela
            frame_tabela = tk.Frame(container_frame)
            tabela = ttk.Treeview(frame_tabela, columns=[serie_id for serie_id in range(3, 12)], show="headings", selectmode="none")
            
            # Configurar as colunas (séries)
            for i, serie_id in enumerate(range(3, 12)):
                tabela.heading(serie_id, text=self._safe_str_value(series_nomes.get(serie_id, f"Série {self._safe_str_value(serie_id)}")))
                tabela.column(serie_id, width=120, anchor="center")
            
            # Preencher a tabela com dados
            for disciplina_id, dados in dados_matriz.items():
                valores = []
                
                # Para cada série, adicionar o valor correspondente
                for serie_id in range(3, 12):
                    valor = dados["series"].get(serie_id, "")
                    valores.append(valor)
                
                # Inserir a linha com o ID da disciplina como tag para identificação posterior
                tabela.insert("", "end", text=dados["nome"], values=valores, tags=(str(disciplina_id),))
            
            # Adicionar texto das disciplinas na primeira coluna
            disciplinas_col = tk.Frame(frame_tabela)
            disciplinas_col.pack(side=tk.LEFT, fill=tk.Y)
            
            # Cabeçalho da coluna das disciplinas
            header_label = tk.Label(disciplinas_col, text="Disciplina", **header_style)
            header_label.pack(fill=tk.X, pady=(0, 1))
            
            # Nomes das disciplinas
            for disciplina_id, dados in dados_matriz.items():
                disc_label = tk.Label(disciplinas_col, text=dados["nome"], **row_header_style, width=15)
                # Armazenar ID no widget usando setattr
                setattr(disc_label, 'disciplina_id', disciplina_id)
                disc_label.pack(fill=tk.X, pady=(0, 1))
                
                # Vincular duplo clique para editar
                disc_label.bind("<Double-1>", lambda e, d_id=disciplina_id: 
                            self.adicionar_disciplina_matriz(janela_matriz, {'disciplina_id': d_id}, escola_id))
            
            # Configurar a tabela
            tabela.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            # Configurar evento de duplo clique em células da tabela
            def ao_clicar_celula(evento):
                # Obter o item clicado
                item = tabela.identify_row(evento.y)
                if not item:
                    return
                
                # Obter a coluna clicada
                coluna = tabela.identify_column(evento.x)
                if not coluna:
                    return
                
                # Extrair IDs
                disciplina_id = tabela.item(item, "tags")[0]  # O ID da disciplina está na tag
                serie_id = int(coluna[1:]) + 2  # Convertendo #1, #2, etc para 3, 4, etc (offset das séries)
                
                # Obter o valor atual
                valores = tabela.item(item, "values")
                idx_coluna = int(coluna[1:]) - 1
                valor_celula = valores[idx_coluna] if idx_coluna < len(valores) else ""
                
                # Abrir diálogo de edição
                self.editar_disciplina_matriz(janela_matriz, int(disciplina_id), serie_id, valor_celula, escola_id)
            
            # Vincular eventos
            tabela.bind("<Double-1>", ao_clicar_celula)
            
            # === PREENCHER O MODO CARTÕES ===
            # Agrupar por série para os cartões
            series_cartoes = {}
            cartoes_criados = []  # Lista para armazenar referências aos cartões criados
            
            for serie_id in range(3, 12):
                series_cartoes[serie_id] = {"nome": series_nomes.get(serie_id, f"Série {serie_id}"), "disciplinas": []}
                
                # Adicionar disciplinas a esta série
                for disciplina_id, dados in dados_matriz.items():
                    if serie_id in dados["series"]:
                        series_cartoes[serie_id]["disciplinas"].append({
                            "id": disciplina_id,
                            "nome": dados["nome"],
                            "nota": dados["series"][serie_id]
                        })
            
            # Criar os cartões agrupados por série
            for row, serie_id in enumerate(range(3, 12)):
                if not series_cartoes[serie_id]["disciplinas"]:
                    continue  # Pular séries sem disciplinas
                
                # Cores para o cartão desta série
                cor_titulo, cor_bg = cores_series.get(serie_id, ("#333333", "#F5F5F5"))
                
                # Frame para o cartão
                cartao_frame = tk.Frame(frame_conteudo_cartoes, bg=cor_bg, bd=0, 
                                       highlightthickness=1, highlightbackground="#BDBDBD")
                cartao_frame.pack(fill=tk.X, pady=10, padx=20)
                
                # Título do cartão (Nome da série)
                titulo_cartao = tk.Label(cartao_frame, text=series_cartoes[serie_id]["nome"], 
                                      bg=cor_titulo, fg="white", **titulo_cartao_style)
                titulo_cartao.pack(fill=tk.X)
                
                # Frame para as disciplinas
                disciplinas_frame = tk.Frame(cartao_frame, bg=cor_bg, padx=15, pady=15)
                disciplinas_frame.pack(fill=tk.X)
                
                # Grid para organizar as disciplinas (3 colunas)
                disciplinas_frame.columnconfigure(0, weight=1)
                disciplinas_frame.columnconfigure(1, weight=1)
                disciplinas_frame.columnconfigure(2, weight=1)
                
                # Adicionar disciplinas ao cartão
                for i, disciplina in enumerate(series_cartoes[serie_id]["disciplinas"]):
                    # Calcular posição na grid
                    col = i % 3
                    row = i // 3
                    
                    # Frame para a disciplina
                    disc_frame = tk.Frame(disciplinas_frame, bg=cor_bg, relief="solid", 
                                        borderwidth=1, padx=8, pady=8)
                    disc_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                    
                    # Armazenar IDs no frame para uso na função de edição
                    # Armazenar IDs e valores no widget usando setattr
                    setattr(disc_frame, 'disciplina_id', disciplina["id"])
                    setattr(disc_frame, 'serie_id', serie_id)
                    setattr(disc_frame, 'valor_celula', disciplina["nota"])
                    
                    # Adicionar à lista de cartões criados
                    cartoes_criados.append(disc_frame)
                    
                    # Criar um frame para o cabeçalho do cartão
                    header_frame = tk.Frame(disc_frame, bg=cor_bg)
                    header_frame.pack(fill=tk.X, anchor="w")
                    
                    # Nome da disciplina com ícone
                    icone_disciplina = "📚"  # Ícone padrão
                    
                    # Personalizar ícone conforme a disciplina
                    nome_disc_lower = disciplina["nome"].lower()
                    if "matemática" in nome_disc_lower or "matematica" in nome_disc_lower:
                        icone_disciplina = "🔢"
                    elif "português" in nome_disc_lower or "portugues" in nome_disc_lower or "lingua portuguesa" in nome_disc_lower:
                        icone_disciplina = "📝"
                    elif "história" in nome_disc_lower or "historia" in nome_disc_lower:
                        icone_disciplina = "📜"
                    elif "geografia" in nome_disc_lower:
                        icone_disciplina = "🌎"
                    elif "inglês" in nome_disc_lower or "ingles" in nome_disc_lower or "lingua inglesa" in nome_disc_lower:
                        icone_disciplina = "🇬🇧"
                    elif "espanhol" in nome_disc_lower:
                        icone_disciplina = "🇪🇸"
                    elif "educação física" in nome_disc_lower or "fisica" in nome_disc_lower:
                        icone_disciplina = "🏃"
                    elif "arte" in nome_disc_lower:
                        icone_disciplina = "🎨"
                    elif "música" in nome_disc_lower or "musica" in nome_disc_lower:
                        icone_disciplina = "🎵"
                    
                    # Nome da disciplina
                    nome_label = tk.Label(header_frame, text=f"{icone_disciplina} {disciplina['nome']}", 
                                        font=("Arial", 10, "bold"), bg=cor_bg, fg="#333")
                    nome_label.pack(side=tk.LEFT, anchor="w")
                    
                    # Adicionar ícone de edição à direita
                    edit_icon = tk.Label(header_frame, text="✏️", bg=cor_bg, fg="#666", cursor="hand2")
                    edit_icon.pack(side=tk.RIGHT, padx=(5, 0))
                    edit_icon.bind("<Button-1>", lambda e, d_id=disciplina["id"], s_id=serie_id, v=disciplina["nota"]: 
                                 self.editar_disciplina_matriz(janela_matriz, d_id, s_id, v, escola_id))
                    
                    # Nota/conceito
                    if disciplina["nota"]:
                        # Tentar extrair a nota numérica (se houver)
                        nota_bg = cor_bg
                        nota_valor = None
                        status_texto = ""
                        
                        try:
                            if '.' in disciplina["nota"]:
                                nota_valor = float(disciplina["nota"].split('\n')[0])
                                if nota_valor < 6.0:
                                    nota_bg = "#FFCDD2"  # Vermelho claro para notas baixas
                                    status_texto = "Abaixo da média"
                                elif nota_valor >= 8.0:
                                    nota_bg = "#C8E6C9"  # Verde claro para notas altas
                                    status_texto = "Ótimo"
                                else:
                                    nota_bg = "#FFF9C4"  # Amarelo claro
                                    status_texto = "Médio"
                            # Para conceitos
                            elif disciplina["nota"].startswith("R"):
                                nota_bg = "#FFCDD2"  # Vermelho claro
                                status_texto = "Reprovado"
                            elif disciplina["nota"].startswith("O") or disciplina["nota"].startswith("B"):
                                nota_bg = "#C8E6C9"  # Verde claro
                                status_texto = "Aprovado"
                        except:
                            pass
                        
                        # Criar frame com a cor de fundo apropriada
                        nota_frame = tk.Frame(disc_frame, bg=nota_bg, padx=5, pady=3)
                        nota_frame.pack(fill="x", pady=(5, 0))
                        
                        # Separar as linhas da nota
                        linhas = disciplina["nota"].split('\n')
                        
                        # Primeira linha (nota principal)
                        if linhas:
                            nota_principal = tk.Label(nota_frame, text=linhas[0], bg=nota_bg, fg="#333", font=("Arial", 11, "bold"))
                            nota_principal.pack(anchor="w")
                        
                        # Linhas adicionais
                        for linha in linhas[1:]:
                            nota_label = tk.Label(nota_frame, text=linha, bg=nota_bg, fg="#333")
                            nota_label.pack(anchor="w")
                        
                        # Adicionar status se tiver
                        if status_texto:
                            status_label = tk.Label(nota_frame, text=status_texto, bg=nota_bg, fg="#555", font=("Arial", 8))
                            status_label.pack(anchor="e", pady=(3, 0))
                    else:
                        # Sem nota
                        sem_nota = tk.Label(disc_frame, text="Sem registro", bg=cor_bg, fg="#999")
                        sem_nota.pack(pady=(5, 0))
                        
                        # Botão para adicionar nota
                        btn_adicionar_nota = tk.Button(
                            disc_frame, 
                            text="+ Adicionar", 
                            bg="#E0E0E0", 
                            fg="#333",
                            relief=tk.FLAT,
                            font=("Arial", 7),
                            command=lambda d_id=disciplina["id"], s_id=serie_id: 
                                self.editar_disciplina_matriz(janela_matriz, d_id, s_id, "", escola_id)
                        )
                        btn_adicionar_nota.pack(pady=(3, 0))
            
            # Configurar o grid para expandir corretamente dentro do cartão
            for i in range(3):  # 3 colunas
                # Verificamos se disciplinas_frame ainda está no escopo atual
                try:
                    disciplinas_frame.grid_columnconfigure(i, weight=1)
                except:
                    pass  # Ignoramos caso a variável não esteja disponível
            
            # Configurar redimensionamento quando a janela mudar de tamanho
            def configurar_canvas_tabela(event):
                canvas_tabela.configure(scrollregion=canvas_tabela.bbox("all"), width=event.width, height=event.height)
            
            def configurar_canvas_cartoes(event):
                canvas_cartoes.configure(scrollregion=canvas_cartoes.bbox("all"), width=event.width)
            
            frame_conteudo_tabela.bind("<Configure>", configurar_canvas_tabela)
            frame_conteudo_cartoes.bind("<Configure>", configurar_canvas_cartoes)
            
            # Configurar o grid para expandir corretamente
            for i in range(len(disciplinas) + 1):
                frame_conteudo_tabela.grid_rowconfigure(i, weight=1)
            
            for i in range(10):  # 9 séries + 1 coluna para nome da disciplina
                frame_conteudo_tabela.grid_columnconfigure(i, weight=1)
            
            # Configurar o grid para os cartões
            frame_conteudo_cartoes.grid_columnconfigure(0, weight=1)
            
            # Adicionar informações de legenda na parte inferior
            frame_legenda = tk.Frame(janela_matriz, bg=self.co9, pady=10)
            frame_legenda.pack(fill=tk.X, side=tk.BOTTOM)
            
            # Legendas para as cores
            tk.Label(frame_legenda, text="Legenda:", font=("Arial", 9, "bold"), bg=self.co9).pack(side=tk.LEFT, padx=10)
            
            frame_amostra1 = tk.Frame(frame_legenda, bg="#FFCDD2", width=20, height=20)
            frame_amostra1.pack(side=tk.LEFT, padx=5)
            tk.Label(frame_legenda, text="Nota Baixa/Reprovação", bg=self.co9).pack(side=tk.LEFT, padx=5)
            
            frame_amostra2 = tk.Frame(frame_legenda, bg="#C8E6C9", width=20, height=20)
            frame_amostra2.pack(side=tk.LEFT, padx=5)
            tk.Label(frame_legenda, text="Nota Alta/Ótimo", bg=self.co9).pack(side=tk.LEFT, padx=5)
            
            # Adicionar botões de ação na parte inferior
            frame_acoes = tk.Frame(janela_matriz, bg=self.co9, pady=10)
            frame_acoes.pack(fill=tk.X, side=tk.BOTTOM, before=frame_legenda)
            
            # Botão para adicionar disciplina
            btn_adicionar = tk.Button(frame_acoes, text="➕ Nova Disciplina", 
                                   command=lambda: self.adicionar_disciplina_matriz(janela_matriz, {}, escola_id),
                                   bg="#4CAF50", fg="white", relief=tk.RAISED, bd=0, padx=15, pady=8)
            btn_adicionar.pack(side=tk.LEFT, padx=10)
            
            # Botão para imprimir/exportar como PDF
            btn_pdf = tk.Button(frame_acoes, text="📄 Exportar PDF", 
                              command=lambda: self.exportar_matriz_pdf(dados_matriz, series_nomes, self.aluno_selecionado.get()),
                              bg="#4CAF50", fg="white", relief=tk.RAISED, bd=0, padx=15, pady=8)
            btn_pdf.pack(side=tk.RIGHT, padx=10)
            
            # Botão para exportar para Excel
            btn_excel = tk.Button(frame_acoes, text="📊 Exportar Excel", 
                               command=lambda: self.exportar_matriz_excel(dados_matriz, series_nomes),
                               bg="#FF9800", fg="white", relief=tk.RAISED, bd=0, padx=15, pady=8)
            btn_excel.pack(side=tk.RIGHT, padx=10)
            
            # Adicionar evento de clique duplo aos cartões para edição
            def ao_clicar_cartao(evento, disciplina_id, serie_id, valor_celula):
                self.editar_disciplina_matriz(janela_matriz, disciplina_id, serie_id, valor_celula, escola_id)
            
            # Para cada cartão, adicionar o evento de clique duplo
            for card_frame in cartoes_criados:
                disciplina_id = card_frame.disciplina_id if hasattr(card_frame, 'disciplina_id') else None
                serie_id = card_frame.serie_id if hasattr(card_frame, 'serie_id') else None
                valor_celula = card_frame.valor_celula if hasattr(card_frame, 'valor_celula') else None
                
                if disciplina_id and serie_id:
                    # Armazenar dados no frame para uso no evento
                    card_frame.bind("<Double-1>", 
                                 lambda e, d_id=disciplina_id, s_id=serie_id, v=valor_celula: 
                                 ao_clicar_cartao(e, d_id, s_id, v))
            
            # Configurar scrollbars para a tabela
            vsb_tabela = ttk.Scrollbar(frame_tabela, orient="vertical", command=tabela.yview)
            hsb_tabela = ttk.Scrollbar(frame_tabela, orient="horizontal", command=tabela.xview)
            tabela.configure(yscrollcommand=vsb_tabela.set, xscrollcommand=hsb_tabela.set)
            
            # Configurar scrollbars para os cartões
            vsb_cartoes = ttk.Scrollbar(frame_cartoes, orient="vertical", command=canvas_cartoes.yview)
            hsb_cartoes = ttk.Scrollbar(frame_cartoes, orient="horizontal", command=canvas_cartoes.xview)
            canvas_cartoes.configure(yscrollcommand=vsb_cartoes.set, xscrollcommand=hsb_cartoes.set)
            
            # Iniciar com o modo de tabela
            frame_tabela.pack(fill=tk.BOTH, expand=True)
            
            # Fechar a conexão com o banco
            cursor.close()
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar matriz: {str(e)}")
            print(f"Erro ao carregar matriz: {str(e)}")

    def exportar_matriz_excel(self, dados_matriz, series_nomes):
        """Exporta a matriz de séries x disciplinas para um arquivo Excel."""
        try:
            import pandas as pd
            from tkinter import filedialog
            import os
            from datetime import datetime
            
            # Perguntar onde salvar o arquivo
            data_atual = datetime.now().strftime("%d-%m-%Y")
            nome_arquivo_sugerido = f"matriz_series_disciplinas_{data_atual}.xlsx"
            
            arquivo = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Arquivos Excel", "*.xlsx")],
                initialfile=nome_arquivo_sugerido
            )
            
            if not arquivo:  # Se o usuário cancelou a operação
                return
                
            # Criar um DataFrame para armazenar os dados
            # Estrutura: Disciplina | Série 3 | Série 4 | ... | Série 11
            disciplinas = []
            for disciplina_id, dados in dados_matriz.items():
                linha = {
                    'Disciplina': dados['nome']
                }
                
                # Adicionar dados de cada série
                for serie_id in range(3, 12):
                    nome_serie = series_nomes.get(serie_id, f"Série {serie_id}")
                    linha[nome_serie] = dados['series'].get(serie_id, "")
                
                disciplinas.append(linha)
            
            # Criar o DataFrame
            df = pd.DataFrame(disciplinas)
            
            # Exportar para Excel
            df.to_excel(arquivo, index=False)
            
            # Mostrar mensagem de sucesso
            self.mostrar_mensagem_temporaria(f"Matriz exportada com sucesso para:\n{arquivo}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar matriz para Excel: {str(e)}")
            print(f"Erro ao exportar matriz para Excel: {str(e)}")

    def adicionar_disciplina_matriz(self, janela_pai, dados_matriz=None, escola_id=None):
        """
        Abre uma janela modal para adicionar uma nova disciplina à matriz.
        
        Parameters:
            janela_pai: Janela pai
            dados_matriz: Dicionário com dados da matriz
            escola_id: ID da escola selecionada
        """
        # Verificar se há um aluno selecionado
        if not hasattr(self, 'aluno_id') or not self.aluno_id:
            messagebox.showwarning("Aviso", "Selecione um aluno primeiro.")
            return
            
        # Verificar se a escola_id foi fornecida
        if not escola_id:
            messagebox.showwarning("Aviso", "ID da escola não fornecido.")
            return
            
        # Criar janela de diálogo
        janela_adicionar = tk.Toplevel(janela_pai)
        janela_adicionar.title("Adicionar Disciplina")
        janela_adicionar.geometry("500x400")
        janela_adicionar.configure(bg=self.co9)
        janela_adicionar.transient(janela_pai)
        janela_adicionar.grab_set()  # Torna a janela modal
        
        # Frame principal
        frame_principal = tk.Frame(janela_adicionar, bg=self.co9, padx=20, pady=20)
        frame_principal.pack(fill=tk.BOTH, expand=True)
        
        # Título
        tk.Label(frame_principal, text="Adicionar Disciplina à Matriz", 
               font=("Arial", 14, "bold"), bg=self.co9, fg=self.co4).pack(pady=(0, 20))
        
        # Frame para os campos
        frame_campos = tk.Frame(frame_principal, bg=self.co9)
        frame_campos.pack(fill=tk.X, pady=10)
        
        # Configurar grid
        for i in range(2):
            frame_campos.columnconfigure(i, weight=1)
        
        # Disciplina
        tk.Label(frame_campos, text="Disciplina:", bg=self.co9, fg=self.co4).grid(row=0, column=0, sticky="w", pady=5)
        disciplina_var = tk.StringVar()
        cb_disciplina = ttk.Combobox(frame_campos, textvariable=disciplina_var, width=30)
        cb_disciplina.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        
        # Se já houver uma disciplina selecionada, configurar o combobox
        if dados_matriz and 'disciplina_id' in dados_matriz:
            disciplina_id = dados_matriz['disciplina_id']
            
            # Conectar ao banco para obter o nome da disciplina
            conn = None
            cursor = None
            try:
                conn = self.validar_conexao_bd()
                if conn is None:
                    return
                cursor = conn.cursor()
                cursor.execute("SELECT nome FROM disciplinas WHERE id = %s", (disciplina_id,))
                resultado = cursor.fetchone()
                nome_disciplina = resultado[0] if resultado else None
                
                if nome_disciplina:
                    disciplina_var.set(f"{disciplina_id} - {nome_disciplina}")
                    # Desabilitar o combobox de disciplina se for uma edição
                    cb_disciplina.configure(state='disabled')
            except Exception as e:
                print(f"Erro ao obter nome da disciplina: {str(e)}")
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
        
        # Série
        tk.Label(frame_campos, text="Série:", bg=self.co9, fg=self.co4).grid(row=1, column=0, sticky="w", pady=5)
        serie_var = tk.StringVar()
        cb_serie = ttk.Combobox(frame_campos, textvariable=serie_var, width=30)
        cb_serie.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        
        # Ano Letivo
        tk.Label(frame_campos, text="Ano Letivo:", bg=self.co9, fg=self.co4).grid(row=2, column=0, sticky="w", pady=5)
        ano_var = tk.StringVar()
        cb_ano = ttk.Combobox(frame_campos, textvariable=ano_var, width=30)
        cb_ano.grid(row=2, column=1, sticky="w", pady=5, padx=5)
        
        # Nota
        tk.Label(frame_campos, text="Nota:", bg=self.co9, fg=self.co4).grid(row=3, column=0, sticky="w", pady=5)
        nota_var = tk.StringVar()
        entrada_nota = ttk.Entry(frame_campos, textvariable=nota_var, width=10)
        entrada_nota.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        
        # Conceito
        tk.Label(frame_campos, text="Conceito:", bg=self.co9, fg=self.co4).grid(row=4, column=0, sticky="w", pady=5)
        conceito_var = tk.StringVar()
        cb_conceito = ttk.Combobox(frame_campos, textvariable=conceito_var, width=10, values=['', 'R', 'B', 'O', 'AD', 'PNAD', 'APNAD', 'RT'])
        cb_conceito.grid(row=4, column=1, sticky="w", pady=5, padx=5)
        
        # Verificar se a coluna carga_horaria existe
        tem_carga_horaria = False
        conn = None
        cursor = None
        try:
            conn = self.validar_conexao_bd()
            if conn is None:
                return
            cursor = conn.cursor()
            cursor.execute("SHOW COLUMNS FROM historico_escolar LIKE 'carga_horaria'")
            tem_carga_horaria = cursor.fetchone() is not None
        except Exception as e:
            print(f"Erro ao verificar coluna carga_horaria: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
        # Se tiver coluna carga_horaria, mostrar campo
        ch_var = tk.StringVar()
        if tem_carga_horaria:
            tk.Label(frame_campos, text="Carga Horária:", bg=self.co9, fg=self.co4).grid(row=5, column=0, sticky="w", pady=5)
            entrada_ch = ttk.Entry(frame_campos, textvariable=ch_var, width=10)
            entrada_ch.grid(row=5, column=1, sticky="w", pady=5, padx=5)
        
        # Carregar dados para os comboboxes
        def carregar_comboboxes():
            conn = None
            cursor = None
            try:
                conn = self.validar_conexao_bd()
                if conn is None:
                    return
                cursor = conn.cursor()
                
                # Carregar disciplinas (apenas da escola selecionada)
                cursor.execute("SELECT id, nome FROM disciplinas WHERE escola_id = %s ORDER BY nome", (escola_id,))
                disciplinas = cursor.fetchall()
                cb_disciplina['values'] = [f"{id} - {nome}" for id, nome in disciplinas]
                
                # Carregar séries
                cursor.execute("SELECT id, nome FROM serie ORDER BY id")
                series = cursor.fetchall()
                cb_serie['values'] = [f"{id} - {nome}" for id, nome in series]
                
                # Carregar anos letivos
                cursor.execute("SELECT id, ano_letivo FROM anosletivos ORDER BY ano_letivo DESC")
                anos = cursor.fetchall()
                cb_ano['values'] = [f"{id} - {ano}" for id, ano in anos]
                
                # Selecionar valores padrão
                if anos and not ano_var.get():
                    cb_ano.current(0)  # Seleciona o primeiro ano
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar dados: {str(e)}")
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
        
        # Carregar dados iniciais
        carregar_comboboxes()
        
        # Frame para os botões
        frame_botoes = tk.Frame(frame_principal, bg=self.co9)
        frame_botoes.pack(fill=tk.X, pady=20)
        
        # Função para salvar disciplina
        def salvar_disciplina():
            # Validar campos obrigatórios
            if not disciplina_var.get():
                messagebox.showwarning("Aviso", "Selecione uma disciplina.")
                return
                
            if not serie_var.get():
                messagebox.showwarning("Aviso", "Selecione uma série.")
                return
                
            if not ano_var.get():
                messagebox.showwarning("Aviso", "Selecione um ano letivo.")
                return
                
            # Checar se pelo menos nota ou conceito está preenchido
            if not nota_var.get() and not conceito_var.get():
                messagebox.showwarning("Aviso", "Preencha pelo menos um dos campos: Nota ou Conceito.")
                return
                
            # Obter IDs
            try:
                disciplina_id = int(disciplina_var.get().split(' - ')[0])
                serie_id = int(serie_var.get().split(' - ')[0])
                ano_letivo_id = int(ano_var.get().split(' - ')[0])
                
                # Converter nota para float se preenchida
                media = None
                if nota_var.get():
                    try:
                        media = float(nota_var.get().replace(',', '.')) * 10  # Multiplicar por 10 para armazenar no formato do banco
                    except ValueError:
                        messagebox.showwarning("Aviso", "A nota deve ser um número válido.")
                        return
                        
                conceito = conceito_var.get() if conceito_var.get() else None
                
                # Verificar se já existe o registro
                conn = None
                cursor = None
                try:
                    conn = self.validar_conexao_bd()
                    if conn is None:
                        return
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT id FROM historico_escolar 
                        WHERE aluno_id = %s AND disciplina_id = %s AND serie_id = %s
                    """, (self.aluno_id, disciplina_id, serie_id))
                    
                    registro_existente = cursor.fetchone()
                    
                    if registro_existente:
                        messagebox.showwarning("Aviso", "Esta disciplina já está registrada para esta série. Edite o registro existente.")
                        return
                    
                    # Inserir novo registro
                    if tem_carga_horaria:
                        carga_horaria = ch_var.get() if ch_var.get() else None
                        cursor.execute("""
                            INSERT INTO historico_escolar 
                            (aluno_id, disciplina_id, serie_id, media, conceito, carga_horaria, ano_letivo_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (self.aluno_id, disciplina_id, serie_id, media, conceito, carga_horaria, ano_letivo_id))
                    else:
                        cursor.execute("""
                            INSERT INTO historico_escolar 
                            (aluno_id, disciplina_id, serie_id, media, conceito, ano_letivo_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (self.aluno_id, disciplina_id, serie_id, media, conceito, ano_letivo_id))
                    
                    conn.commit()
                    
                    # Mensagem de sucesso
                    self.mostrar_mensagem_temporaria("Disciplina adicionada com sucesso!")
                    
                    # Atualizar a visualização
                    self.atualizar_visualizacao_matriz(janela_pai, escola_id=escola_id)
                    
                except Exception as e:
                    if conn:
                        conn.rollback()
                    messagebox.showerror("Erro", f"Erro ao adicionar disciplina: {str(e)}")
                finally:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()
                
            except (ValueError, IndexError):
                messagebox.showwarning("Aviso", "Selecione valores válidos para todos os campos.")
        
        # Botão para salvar
        btn_salvar = tk.Button(frame_botoes, text="Salvar", command=salvar_disciplina,
                             bg="#4CAF50", fg="white", padx=20, pady=5)
        btn_salvar.pack(side=tk.RIGHT, padx=5)
        
        # Botão para cancelar
        btn_cancelar = tk.Button(frame_botoes, text="Cancelar", command=janela_adicionar.destroy,
                               bg="#9E9E9E", fg="white", padx=20, pady=5)
        btn_cancelar.pack(side=tk.RIGHT, padx=5)

    def editar_disciplina_matriz(self, janela_pai, disciplina_id, serie_id, dados_celula, escola_id):
        """
        Abre uma janela modal para editar uma disciplina existente na matriz.
        
        Parameters:
            janela_pai: Janela pai
            disciplina_id: ID da disciplina
            serie_id: ID da série
            dados_celula: Dados atuais da célula
            escola_id: ID da escola selecionada
        """
        # Verificar se a escola_id foi fornecida
        if not escola_id:
            messagebox.showwarning("Aviso", "ID da escola não fornecido.")
            return
            
        # Criar janela de diálogo
        janela_editar = tk.Toplevel(janela_pai)
        janela_editar.title("Editar Disciplina")
        janela_editar.geometry("500x350")
        janela_editar.configure(bg=self.co9)
        janela_editar.transient(janela_pai)
        janela_editar.grab_set()  # Torna a janela modal
        
        # Frame principal
        frame_principal = tk.Frame(janela_editar, bg=self.co9, padx=20, pady=20)
        frame_principal.pack(fill=tk.BOTH, expand=True)
        
        # Título
        tk.Label(frame_principal, text="Editar Disciplina", 
               font=("Arial", 14, "bold"), bg=self.co9, fg=self.co4).pack(pady=(0, 20))
        
        # Verificar se a coluna carga_horaria existe
        conn = None
        cursor = None
        tem_carga_horaria = False
        
        try:
            conn = conectar_bd()
            if not conn:
                return
            cursor = conn.cursor()
            cursor.execute("SHOW COLUMNS FROM historico_escolar LIKE 'carga_horaria'")
            resultado = cursor.fetchone()
            tem_carga_horaria = resultado is not None
        except Exception as e:
            print(f"Erro ao verificar coluna carga_horaria: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
        # Conectar ao banco para obter detalhes da disciplina e série
        conn = None
        cursor = None
        
        disciplina_nome = ""
        serie_nome = ""
        ano_letivo = ""
        registro_id = None
        media = None
        conceito = None
        carga_horaria = None
        ano_letivo_id = None
        
        try:
            conn = conectar_bd()
            if not conn:
                return
            cursor = conn.cursor()
            
            # Obter nome da disciplina
            cursor.execute("SELECT nome FROM disciplinas WHERE id = %s", (disciplina_id,))
            disciplina_resultado = cursor.fetchone()
            disciplina_nome = disciplina_resultado[0] if disciplina_resultado else f"Disciplina {disciplina_id}"
            
            # Obter nome da série
            cursor.execute("SELECT nome FROM serie WHERE id = %s", (serie_id,))
            serie_resultado = cursor.fetchone()
            serie_nome = serie_resultado[0] if serie_resultado else f"Série {serie_id}"
            
            # Construir consulta SQL baseada na existência da coluna carga_horaria
            if tem_carga_horaria:
                sql_query = """
                    SELECT h.id, al.ano_letivo, h.media, h.conceito, h.carga_horaria, h.ano_letivo_id
                    FROM historico_escolar h
                    JOIN anosletivos al ON h.ano_letivo_id = al.id
                    WHERE h.aluno_id = %s AND h.disciplina_id = %s AND h.serie_id = %s
                """
            else:
                sql_query = """
                    SELECT h.id, al.ano_letivo, h.media, h.conceito, NULL as carga_horaria, h.ano_letivo_id
                    FROM historico_escolar h
                    JOIN anosletivos al ON h.ano_letivo_id = al.id
                    WHERE h.aluno_id = %s AND h.disciplina_id = %s AND h.serie_id = %s
                """
            
            # Obter dados do registro
            cursor.execute(sql_query, (self.aluno_id, disciplina_id, serie_id))
            
            registro = cursor.fetchone()
            if registro:
                registro_id = registro[0]
                ano_letivo = registro[1]
                media = registro[2]
                conceito = registro[3]
                carga_horaria = registro[4]
                ano_letivo_id = registro[5]
                
        except Exception as e:
            print(f"Erro ao obter dados para edição: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
        # Frame para os campos
        frame_campos = tk.Frame(frame_principal, bg=self.co9)
        frame_campos.pack(fill=tk.X, pady=10)
        
        # Configurar grid
        for i in range(2):
            frame_campos.columnconfigure(i, weight=1)
        
        # Exibir informações da disciplina (não editáveis)
        tk.Label(frame_campos, text="Disciplina:", bg=self.co9, fg=self.co4).grid(row=0, column=0, sticky="w", pady=5)
        tk.Label(frame_campos, text=self._safe_str_value(disciplina_nome), bg=self.co9, fg=self.co4, font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        tk.Label(frame_campos, text="Série:", bg=self.co9, fg=self.co4).grid(row=1, column=0, sticky="w", pady=5)
        tk.Label(frame_campos, text=self._safe_str_value(serie_nome), bg=self.co9, fg=self.co4, font=("Arial", 10, "bold")).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        tk.Label(frame_campos, text="Ano Letivo:", bg=self.co9, fg=self.co4).grid(row=2, column=0, sticky="w", pady=5)
        ano_var = tk.StringVar(value=self._safe_str_value(ano_letivo))
        cb_ano = ttk.Combobox(frame_campos, textvariable=ano_var, width=20)
        cb_ano.grid(row=2, column=1, sticky="w", pady=5, padx=5)
        
        # Carregar anos letivos
        def carregar_anos():
            conn = None
            cursor = None
            try:
                conn = conectar_bd()
                if not conn:
                    return
                cursor = conn.cursor()
                cursor.execute("SELECT id, ano_letivo FROM anosletivos ORDER BY ano_letivo DESC")
                anos = cursor.fetchall()
                cb_ano['values'] = [f"{id} - {ano}" for id, ano in anos]
                
                # Selecionar o ano atual
                if ano_letivo:
                    for idx, item in enumerate(cb_ano['values']):
                        if str(ano_letivo) in item:
                            cb_ano.current(idx)
                            break
            except Exception as e:
                print(f"Erro ao carregar anos letivos: {str(e)}")
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
        
        carregar_anos()
        
        # Campos editáveis
        tk.Label(frame_campos, text="Nota:", bg=self.co9, fg=self.co4).grid(row=3, column=0, sticky="w", pady=5)
        nota_var = tk.StringVar(value=f"{self._safe_float_value(media)/10:.1f}" if media is not None else "")
        entrada_nota = ttk.Entry(frame_campos, textvariable=nota_var, width=10)
        entrada_nota.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        
        tk.Label(frame_campos, text="Conceito:", bg=self.co9, fg=self.co4).grid(row=4, column=0, sticky="w", pady=5)
        conceito_var = tk.StringVar(value=self._safe_str_value(conceito) if conceito else "")
        cb_conceito = ttk.Combobox(frame_campos, textvariable=conceito_var, width=10, values=['', 'R', 'B', 'O', 'AD', 'PNAD', 'APNAD', 'RT'])
        cb_conceito.grid(row=4, column=1, sticky="w", pady=5, padx=5)
        
        # Se tiver coluna carga_horaria, mostrar campo
        ch_var = tk.StringVar(value=self._safe_str_value(carga_horaria) if carga_horaria else "")
        if tem_carga_horaria:
            tk.Label(frame_campos, text="Carga Horária:", bg=self.co9, fg=self.co4).grid(row=5, column=0, sticky="w", pady=5)
            entrada_ch = ttk.Entry(frame_campos, textvariable=ch_var, width=10)
            entrada_ch.grid(row=5, column=1, sticky="w", pady=5, padx=5)
        
        # Frame para os botões
        frame_botoes = tk.Frame(frame_principal, bg=self.co9)
        frame_botoes.pack(fill=tk.X, pady=20)
        
        # Função para salvar os dados
        def salvar_edicao():
            # Validar campos
            if not registro_id:
                messagebox.showerror("Erro", "Registro não encontrado no banco de dados.")
                return
                
            # Checar se pelo menos nota ou conceito está preenchido
            if not nota_var.get() and not conceito_var.get():
                messagebox.showwarning("Aviso", "Preencha pelo menos um dos campos: Nota ou Conceito.")
                return
                
            try:
                # Processar ano letivo
                ano_selecionado = ano_var.get()
                if not ano_selecionado:
                    messagebox.showwarning("Aviso", "Selecione um ano letivo.")
                    return
                
                ano_letivo_id = int(ano_selecionado.split(' - ')[0])
                
                # Converter nota para float se preenchida
                media = None
                if nota_var.get():
                    try:
                        media = float(nota_var.get().replace(',', '.')) * 10  # Multiplicar por 10 para armazenar no formato do banco
                    except ValueError:
                        messagebox.showwarning("Aviso", "A nota deve ser um número válido.")
                        return
                
                conceito = conceito_var.get() if conceito_var.get() else None
                
                # Atualizar no banco de dados
                conn = None
                cursor = None
                
                try:
                    conn = conectar_bd()
                    if not conn:
                        return
                    cursor = conn.cursor()
                    
                    if tem_carga_horaria:
                        carga_horaria = ch_var.get() if ch_var.get() else None
                        cursor.execute("""
                            UPDATE historico_escolar
                            SET media = %s, conceito = %s, carga_horaria = %s, ano_letivo_id = %s
                            WHERE id = %s
                        """, self._safe_sql_params(media, conceito, carga_horaria, ano_letivo_id, registro_id))
                    else:
                        cursor.execute("""
                            UPDATE historico_escolar
                            SET media = %s, conceito = %s, ano_letivo_id = %s
                            WHERE id = %s
                        """, self._safe_sql_params(media, conceito, ano_letivo_id, registro_id))
                    
                    conn.commit()
                    self.mostrar_mensagem_temporaria("Disciplina atualizada com sucesso!")
                    
                    # Atualizar a visualização
                    self.atualizar_visualizacao_matriz(janela_pai, escola_id=escola_id)
                    
                except Exception as e:
                    if conn:
                        conn.rollback()
                    messagebox.showerror("Erro", f"Erro ao atualizar disciplina: {str(e)}")
                finally:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()
                
            except (ValueError, IndexError):
                messagebox.showwarning("Aviso", "Selecione valores válidos para todos os campos.")
        
        # Função para excluir o registro
        def excluir_registro():
            if not registro_id:
                messagebox.showerror("Erro", "Registro não encontrado no banco de dados.")
                return
                
            # Confirmar exclusão
            confirmar = messagebox.askyesno("Confirmar Exclusão", 
                                           f"Tem certeza que deseja excluir esta disciplina ({disciplina_nome}) da série {serie_nome}?")
            if not confirmar:
                return
                
            # Excluir do banco de dados
            conn = None
            cursor = None
            
            try:
                conn = conectar_bd()
                if not conn:
                    return
                cursor = conn.cursor()
                cursor.execute("DELETE FROM historico_escolar WHERE id = %s", self._safe_sql_params(registro_id))
                conn.commit()
                self.mostrar_mensagem_temporaria("Disciplina excluída com sucesso!")
                
                # Fechar a janela
                janela_editar.destroy()
                
                # Atualizar a visualização
                self.atualizar_visualizacao_matriz(janela_pai, escola_id=escola_id)
                
            except Exception as e:
                if conn:
                    conn.rollback()
                messagebox.showerror("Erro", f"Erro ao excluir disciplina: {str(e)}")
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
        
        # Botão para salvar
        btn_salvar = tk.Button(frame_botoes, text="Salvar", command=salvar_edicao,
                             bg="#4CAF50", fg="white", padx=20, pady=5)
        btn_salvar.pack(side=tk.RIGHT, padx=5)
        
        # Botão para excluir
        btn_excluir = tk.Button(frame_botoes, text="Excluir", command=excluir_registro,
                              bg="#F44336", fg="white", padx=20, pady=5)
        btn_excluir.pack(side=tk.LEFT, padx=5)
        
        # Botão para cancelar
        btn_cancelar = tk.Button(frame_botoes, text="Cancelar", command=janela_editar.destroy,
                               bg="#9E9E9E", fg="white", padx=20, pady=5)
        btn_cancelar.pack(side=tk.RIGHT, padx=5)

    def exportar_matriz_pdf(self, dados_matriz, series_nomes, aluno_nome):
        """Exporta a matriz de séries x disciplinas para um arquivo PDF."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from tkinter import filedialog
            import os
            from datetime import datetime
            
            # Perguntar onde salvar o arquivo
            data_atual = datetime.now().strftime("%d-%m-%Y")
            nome_arquivo_sugerido = f"matriz_series_disciplinas_{data_atual}.pdf"
            
            arquivo = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Arquivos PDF", "*.pdf")],
                initialfile=nome_arquivo_sugerido
            )
            
            if not arquivo:  # Se o usuário cancelou a operação
                return
                
            # Criar o documento PDF
            doc = SimpleDocTemplate(arquivo, pagesize=landscape(A4))
            elementos = []
            
            # Estilos
            estilos = getSampleStyleSheet()
            estilo_titulo = ParagraphStyle(
                'TituloPrincipal',
                parent=estilos['Heading1'],
                fontSize=16,
                alignment=1,  # Centralizado
                spaceAfter=20
            )
            
            estilo_subtitulo = ParagraphStyle(
                'Subtitulo',
                parent=estilos['Heading2'],
                fontSize=12,
                alignment=1,  # Centralizado
                spaceAfter=10
            )
            
            # Título do documento
            elementos.append(Paragraph("MATRIZ DE SÉRIES E DISCIPLINAS", estilo_titulo))
            elementos.append(Paragraph(f"Aluno: {aluno_nome}", estilo_subtitulo))
            elementos.append(Spacer(1, 20))
            
            # Criar dados para a tabela
            # Cabeçalho: Disciplina | Série 3 | Série 4 | ... | Série 11
            cabecalho = ['Disciplina']
            for serie_id in range(3, 12):
                cabecalho.append(series_nomes.get(serie_id, f"Série {serie_id}"))
            
            dados_tabela = [cabecalho]
            
            # Adicionar linhas para cada disciplina
            for disciplina_id, dados in dados_matriz.items():
                linha = [dados['nome']]
                
                for serie_id in range(3, 12):
                    valor = dados['series'].get(serie_id, "")
                    linha.append(valor)
                
                dados_tabela.append(linha)
            
            # Criar tabela
            tabela = Table(dados_tabela, repeatRows=1)
            
            # Estilo da tabela
            estilo_tabela = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),  # Cabeçalho
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                
                ('BACKGROUND', (0, 1), (0, -1), colors.lightblue),  # Coluna de disciplinas
                ('TEXTCOLOR', (0, 1), (0, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Células de dados
                ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (1, 1), (-1, -1), 10),
                
                ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Bordas
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical
            ])
            
            # Aplicar estilo da tabela
            tabela.setStyle(estilo_tabela)
            
            # Adicionar tabela ao documento
            elementos.append(tabela)
            
            # Adicionar rodapé
            elementos.append(Spacer(1, 20))
            estilo_rodape = ParagraphStyle(
                'Rodape',
                parent=estilos['Normal'],
                fontSize=8,
                alignment=1  # Centralizado
            )
            rodape = Paragraph(f"Documento gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", estilo_rodape)
            elementos.append(rodape)
            
            # Gerar o PDF
            doc.build(elementos)
            
            # Mostrar mensagem de sucesso
            self.mostrar_mensagem_temporaria(f"Matriz exportada com sucesso para:\n{arquivo}")
            
            # Abrir o arquivo
            os.startfile(arquivo)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar matriz para PDF: {str(e)}")
            print(f"Erro ao exportar matriz para PDF: {str(e)}")

    def atualizar_visualizacao_matriz(self, janela_matriz, disciplina_id=None, serie_id=None, escola_id=None):
        """
        Atualiza a visualização da matriz após edição, sem precisar reabrir a janela.
        
        Parameters:
            janela_matriz: Janela da matriz
            disciplina_id: ID da disciplina (opcional)
            serie_id: ID da série (opcional)
            escola_id: ID da escola selecionada (opcional)
        """
        try:
            # Fechar a janela atual
            janela_matriz.destroy()
            
            # Reabrir a matriz para atualizar os dados
            if escola_id:
                # Obter o nome da escola para exibição
                conn = None
                cursor = None
                try:
                    conn = conectar_bd()
                    if not conn:
                        return
                    cursor = conn.cursor()
                    cursor.execute("SELECT nome FROM escolas WHERE id = %s", (escola_id,))
                    resultado = cursor.fetchone()
                    escola_nome = resultado[0] if resultado else f"Escola {escola_id}"
                    
                    # Reabrir a matriz com a escola selecionada
                    self.abrir_matriz_com_escola(escola_id, escola_nome)
                except Exception as e:
                    print(f"Erro ao obter nome da escola: {str(e)}")
                    # Tenta reabrir mesmo sem nome da escola
                    self.abrir_matriz_com_escola(escola_id, f"Escola {escola_id}")
                finally:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()
            else:
                # Sem ID da escola, abre a seleção de escola novamente
                self.abrir_matriz_series_disciplinas()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar visualização: {str(e)}")
            print(f"Erro ao atualizar visualização: {str(e)}")

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
                FROM serie 
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
            print(f"Erro ao atualizar disciplinas: {str(e)}")
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

if __name__ == "__main__":
    app = InterfaceHistoricoEscolar()
    app.janela.mainloop() 