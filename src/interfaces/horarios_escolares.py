from src.core.config_logs import get_logger
logger = get_logger(__name__)
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from datetime import datetime
from src.core.conexao import conectar_bd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, PageBreak, HRFlowable
from src.services.utils.pdf import create_pdf_doc
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os
import tempfile

class InterfaceHorariosEscolares:
    def __init__(self, root=None, janela_principal=None):
        # Armazenar referência à janela principal
        self.janela_principal = janela_principal
        
        logger.info("Iniciando InterfaceHorariosEscolares...")
        logger.info(f"  root={root}, janela_principal={janela_principal}")
        
        if janela_principal:
            logger.info(f"  Estado janela principal: {janela_principal.state()}")
            logger.info(f"  Visível janela principal: {janela_principal.winfo_viewable()}")
        
        # Se root for None, cria uma nova janela
        if root is None:
            logger.info("Criando nova janela Toplevel...")
            self.janela = tk.Toplevel(self.janela_principal)  # Passando o pai corretamente
            self.janela.title("Gerenciamento de Horários Escolares")
            
            # Forçar estado normal ANTES de definir geometria
            self.janela.state('normal')
            self.janela.geometry("1200x700")
            
            # NÃO usar transient inicialmente - vai configurar depois que estiver visível
            self.janela.focus_force()
        else:
            logger.info("Usando root fornecido...")
            self.janela = root
        
        # Configurar evento de fechamento sempre (independente de root)
        self.janela.protocol("WM_DELETE_WINDOW", self.ao_fechar_janela)

        # Definir as cores da interface - mesmas cores da main.py
        self.co0 = "#F5F5F5"  # Branco suave para o fundo
        self.co1 = "#003A70"  # Azul escuro (principal)
        self.co2 = "#77B341"  # Verde
        self.co3 = "#E2418E"  # Rosa/Magenta
        self.co4 = "#4A86E8"  # Azul mais claro
        self.co5 = "#F26A25"  # Laranja
        self.co6 = "#F7B731"  # Amarelo
        self.co7 = "#333333"  # Cinza escuro
        self.co8 = "#BF3036"  # Vermelho
        self.co9 = "#6FA8DC"  # Azul claro
        
        # Configurar a janela
        self.janela.configure(bg=self.co0)
        
        # Dias da semana
        self.dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
        
        # Horários padrão
        self.horarios_matutino = ["07:10-08:00", "08:00-08:50", "08:50-09:40", "09:40-10:00", "10:00-10:50", "10:50-11:40"]
        self.horarios_vespertino = ["13:10-14:00", "14:00-14:50", "14:50-15:40", "15:40-16:00", "16:00-16:50", "16:50-17:40"]
        
        # Armazenar células de horários
        self.celulas_horario = {}
        
        # Turma selecionada atualmente
        self.turma_atual = None
        self.turma_id = None
        self.turno_atual = "Matutino"
        
        # Carregar dados do banco de dados
        self.carregar_dados_iniciais()
        
        # Inicializar interface
        try:
            self.criar_interface()
            
            # Garantir que ESTA janela seja exibida PRIMEIRO
            self.janela.state('normal')  # Garantir que não está minimizada
            self.janela.deiconify()
            self.janela.update_idletasks()  # Processar eventos pendentes
            self.janela.update()  # Forçar atualização completa
            self.janela.lift()
            self.janela.focus_force()
            
            # Força janela no topo temporariamente
            self.janela.attributes('-topmost', True)
            self.janela.after(100, lambda: self.janela.attributes('-topmost', False))
            
            # DEPOIS que a janela estiver visível, ocultar janela principal
            if self.janela_principal:
                logger.info("Ocultando janela principal...")
                self.janela_principal.withdraw()
            
            logger.info(f"✓ Interface de horários escolares criada com sucesso")
            logger.info(f"  Estado da janela: {self.janela.state()}")
            logger.info(f"  Geometria: {self.janela.geometry()}")
            logger.info(f"  Visível: {self.janela.winfo_viewable()}")
            logger.info(f"  Mapeada: {self.janela.winfo_ismapped()}")
        except Exception as e:
            logger.exception(f"Erro ao criar interface de horários escolares: {e}")
            # Se houver erro, restaurar janela principal
            if self.janela_principal:
                self.janela_principal.deiconify()
            raise
    
    def carregar_dados_iniciais(self):
        """Carrega dados iniciais do banco de dados."""
        # Inicializar listas vazias para caso de erro
        self.series_dados = []
        self.professores = []
        self.disciplinas = [
            {'id': 1, 'nome': 'LÍNGUA PORTUGUESA'},
            {'id': 2, 'nome': 'MATEMÁTICA'},
            {'id': 3, 'nome': 'CIÊNCIAS'},
            {'id': 4, 'nome': 'HISTÓRIA'},
            {'id': 5, 'nome': 'GEOGRAFIA'},
            {'id': 6, 'nome': 'ARTE'},
        ]
        
        try:
            # Conectar ao banco de dados
            conn = conectar_bd()
            if not conn:
                messagebox.showwarning("Aviso", "Não foi possível conectar ao banco de dados. Usando dados padrão.")
                return
                
            cursor = conn.cursor(dictionary=True)
            
            # Buscar todas as séries com tratamento de erro
            try:
                # Primeiro vamos listar todos os níveis de ensino disponíveis para debugar
                cursor.execute("SELECT id, nome FROM niveisensino")
                niveis = cursor.fetchall()
                logger.info("Níveis de ensino disponíveis:")
                for nivel in niveis:
                    logger.info(f"  ID: {nivel['id']}, Nome: {nivel['nome']}")
                
                # Agora vamos listar todas as séries
                cursor.execute("SELECT id, nome, nivel_id FROM series")
                todas_series = cursor.fetchall()
                logger.info("\nTodas as séries disponíveis:")
                for serie in todas_series:
                    logger.info(f"  ID: {serie['id']}, Nome: {serie['nome']}, Nível ID: {serie['nivel_id']}")
                
                # Buscar apenas as séries de interesse
                cursor.execute("""
                    SELECT id, nome, nivel_id FROM series 
                    WHERE nivel_id IN (
                        SELECT id FROM niveisensino WHERE nome IN ('Ensino Fundamental I', 'Ensino Fundamental II')
                    )
                    ORDER BY nome
                """)
                self.series_dados = cursor.fetchall()
                logger.info(f"\nSéries específicas carregadas: {len(self.series_dados)}")
                for serie in self.series_dados:
                    logger.info(f"  ID: {serie['id']}, Nome: {serie['nome']}")
                    
                # Se não encontrar nenhuma série, podemos procurar usando IDs específicos baseados na tabela turmas
                if not self.series_dados:
                    # IDs das séries que aparecem na tabela turmas: 3, 4, 5, 6, 7, 8, 9, 10, 11
                    cursor.execute("SELECT id, nome, nivel_id FROM series WHERE id IN (3, 4, 5, 6, 7, 8, 9, 10, 11) ORDER BY id")
                    self.series_dados = cursor.fetchall()
                    logger.info(f"\nSéries por ID específico: {len(self.series_dados)}")
                    for serie in self.series_dados:
                        logger.info(f"  ID: {serie['id']}, Nome: {serie['nome']}")
                
            except Exception as e:
                logger.error(f"Erro ao carregar séries: {str(e)}")
                # Criar séries padrão para fallback
                self.series_dados = [
                    {'id': 3, 'nome': "1º Ano"},
                    {'id': 4, 'nome': "2º Ano"},
                    {'id': 5, 'nome': "3º Ano"},
                    {'id': 6, 'nome': "4º Ano"},
                    {'id': 7, 'nome': "5º Ano"},
                    {'id': 8, 'nome': "6º Ano"},
                    {'id': 9, 'nome': "7º Ano"},
                    {'id': 10, 'nome': "8º Ano"},
                    {'id': 11, 'nome': "9º Ano"}
                ]
            
            # Buscar todos os professores com tratamento de erro
            try:
                # Verificar se a coluna data_saida existe
                cursor.execute("""
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'funcionarios' 
                    AND COLUMN_NAME = 'data_saida'
                """)
                has_data_saida = cursor.fetchone()['COUNT(*)'] > 0
                
                # Construir query baseado na existência da coluna
                if has_data_saida:
                    query = """
                        SELECT id, nome, cargo, polivalente FROM funcionarios 
                        WHERE cargo IN ('Professor@', 'Especialista (Coordenadora)')
                        AND escola_id = 60
                        AND (data_saida IS NULL OR data_saida = '')
                        ORDER BY nome
                    """
                else:
                    query = """
                        SELECT id, nome, cargo, polivalente FROM funcionarios 
                        WHERE cargo IN ('Professor@', 'Especialista (Coordenadora)')
                        AND escola_id = 60
                        ORDER BY nome
                    """
                
                cursor.execute(query)
                self.professores = cursor.fetchall()
                logger.info(f"Professores carregados: {len(self.professores)}")
            except Exception as e:
                logger.error(f"Erro ao carregar professores: {str(e)}")
                # Criar professores padrão para fallback
                self.professores = [
                    {'id': 1, 'nome': 'Ana Maria Silva', 'cargo': 'Professor@', 'polivalente': 'sim'},
                    {'id': 2, 'nome': 'Carlos Santos', 'cargo': 'Professor@', 'polivalente': 'sim'},
                    {'id': 3, 'nome': 'Maria José Oliveira', 'cargo': 'Professor@', 'polivalente': 'não'},
                    {'id': 4, 'nome': 'Pedro Alves Costa', 'cargo': 'Professor@', 'polivalente': 'não'},
                    {'id': 5, 'nome': 'Joana Santos Pereira', 'cargo': 'Professor@', 'polivalente': 'sim'}
                ]
            
            # Buscar todas as disciplinas com tratamento de erro
            try:
                cursor.execute("""
                    SELECT id, nome FROM disciplinas
                    WHERE escola_id = 60
                    ORDER BY nome
                """)
                self.disciplinas = cursor.fetchall()
                logger.info(f"Disciplinas carregadas: {len(self.disciplinas)}")
            except Exception as e:
                logger.error(f"Erro ao carregar disciplinas: {str(e)}")
                # Criar disciplinas padrão para fallback
                self.disciplinas = [
                    {'id': 1, 'nome': 'LÍNGUA PORTUGUESA'},
                    {'id': 2, 'nome': 'MATEMÁTICA'},
                    {'id': 3, 'nome': 'CIÊNCIAS'},
                    {'id': 4, 'nome': 'HISTÓRIA'},
                    {'id': 5, 'nome': 'GEOGRAFIA'},
                    {'id': 6, 'nome': 'ARTE'},
                ]
            
            # Fechar conexão
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro geral ao carregar dados: {str(e)}")
            messagebox.showwarning("Aviso", f"Ocorreu um erro ao carregar dados do banco. Usando dados padrão.")
            # Os dados padrão já foram inicializados
    
    def buscar_disciplinas_por_turma(self, turma_id):
        """Busca disciplinas que têm professores vinculados a uma turma específica.
        
        Estratégia em dois passos:
        1. Busca vínculos diretos com esta turma_id
        2. Se nenhum encontrado, busca pela mesma série em qualquer ano (fallback para
           professores vinculados em anos anteriores, ex: turmas de 2025 para 2026)
        Sempre inclui turma_id=NULL (professor de todas as turmas).
        Agrupa por nome para evitar duplicatas entre níveis.
        """
        try:
            conn = conectar_bd()
            if not conn:
                return []
                
            cursor = conn.cursor(dictionary=True)
            
            # Passo 1: disciplinas com vínculo direto nesta turma
            query_direto = """
                SELECT d.nome, MIN(d.id) as id
                FROM disciplinas d
                INNER JOIN funcionario_disciplinas fd ON d.id = fd.disciplina_id
                WHERE d.escola_id = 60
                AND fd.turma_id = %s
                GROUP BY d.nome
                ORDER BY d.nome
            """
            cursor.execute(query_direto, (turma_id,))
            disciplinas = cursor.fetchall()
            
            if not disciplinas:
                # Passo 2: fallback — mesma série em qualquer ano letivo
                # Cobre professores cujos vínculos ainda apontam para turmas do ano anterior
                query_serie = """
                    SELECT d.nome, MIN(d.id) as id
                    FROM disciplinas d
                    INNER JOIN funcionario_disciplinas fd ON d.id = fd.disciplina_id
                    INNER JOIN turmas t_fd ON fd.turma_id = t_fd.id
                    INNER JOIN turmas t_sel ON t_sel.id = %s
                    WHERE d.escola_id = 60
                    AND t_fd.serie_id = t_sel.serie_id
                    GROUP BY d.nome
                    ORDER BY d.nome
                """
                cursor.execute(query_serie, (turma_id,))
                disciplinas = cursor.fetchall()
            
            # Sempre adicionar disciplinas com turma_id=NULL (professor genérico)
            query_null = """
                SELECT d.nome, MIN(d.id) as id
                FROM disciplinas d
                INNER JOIN funcionario_disciplinas fd ON d.id = fd.disciplina_id
                WHERE d.escola_id = 60
                AND fd.turma_id IS NULL
                GROUP BY d.nome
                ORDER BY d.nome
            """
            cursor.execute(query_null)
            disc_null = cursor.fetchall()
            
            # Mesclar sem duplicar nomes
            nomes_existentes = {d['nome'] for d in disciplinas}
            for d in disc_null:
                if d['nome'] not in nomes_existentes:
                    disciplinas.append(d)
                    nomes_existentes.add(d['nome'])
            
            # Ordenar por nome
            disciplinas.sort(key=lambda x: x['nome'])
            
            cursor.close()
            conn.close()
            
            logger.info(f"Disciplinas encontradas para turma_id={turma_id}: {len(disciplinas)}")
            for disc in disciplinas:
                logger.info(f"  - {disc['nome']} (ID: {disc['id']})")
            
            return disciplinas
            
        except Exception as e:
            logger.error(f"Erro ao buscar disciplinas por turma: {str(e)}")
            return []
    def atualizar_disciplinas_comboboxes(self):
        """Atualiza todos os comboboxes da grade com as disciplinas vinculadas à turma atual."""
        if not self.turma_id:
            logger.warning("Não é possível atualizar comboboxes sem turma_id")
            return
        
        # Buscar disciplinas vinculadas à turma
        disciplinas_turma = self.buscar_disciplinas_por_turma(self.turma_id)
        
        if not disciplinas_turma:
            logger.warning(f"Nenhuma disciplina vinculada à turma {self.turma_id}")
            valores_disciplinas = ["<VAGO>"]
        else:
            # Extrair nomes das disciplinas
            valores_disciplinas = [d['nome'] for d in disciplinas_turma]
            valores_disciplinas.insert(0, "")  # Opção vazia para limpar
            valores_disciplinas.append("<VAGO>")
            logger.info(f"✓ {len(disciplinas_turma)} disciplinas disponíveis para a turma")
        
        logger.info(f"Valores para combobox: {valores_disciplinas}")
        
        # Atualizar todos os comboboxes (exceto intervalos)
        horarios = self.horarios_matutino if self.turno_atual == "Matutino" else self.horarios_vespertino
        for coord, celula in self.celulas_horario.items():
            row, col = coord
            
            # Pular linhas de intervalo
            if horarios[row-1] in ["09:40-10:00", "15:40-16:00"]:
                continue
            
            # Atualizar valores do combobox
            celula['values'] = valores_disciplinas
            logger.info(f"Célula ({row},{col}) atualizada com valores")
        
        logger.info(f"Comboboxes atualizados com {len(valores_disciplinas)} opções de disciplinas")

    def criar_interface(self):
        logger.info("criar_interface: Iniciando criação da interface...")
        # Criar frames principais
        self.criar_frames()
        logger.info("criar_interface: Frames criados")
        
        # Criar título da janela
        self.criar_cabecalho("Gerenciamento de Horários Escolares")
        logger.info("criar_interface: Cabeçalho criado")
        
        # Criar área de seleção
        self.criar_area_selecao()
        logger.info("criar_interface: Área de seleção criada")
        
        # Criar grade de horários
        self.criar_grade_horarios()
        logger.info("criar_interface: Grade de horários criada")
        
        # Criar barra de botões
        self.criar_barra_botoes()
        logger.info("criar_interface: Barra de botões criada")
    
    def criar_frames(self):
        # Frame superior para título
        self.frame_titulo = tk.Frame(self.janela, bg=self.co1, height=70)
        self.frame_titulo.pack(side="top", fill="x")
        
        # Frame para seleções e filtros
        self.frame_selecao = tk.Frame(self.janela, bg=self.co0)
        self.frame_selecao.pack(fill="x", padx=10, pady=5)
        
        # Frame para grade de horários
        self.frame_grade = tk.Frame(self.janela, bg=self.co0)
        self.frame_grade.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Frame para botões de ação
        self.frame_botoes = tk.Frame(self.janela, bg=self.co0)
        self.frame_botoes.pack(fill="x", padx=10, pady=10)
    
    def criar_cabecalho(self, texto):
        # Configurar o frame de título
        for widget in self.frame_titulo.winfo_children():
            widget.destroy()
            
        # Frame interno para organizar título e badge
        frame_header = tk.Frame(self.frame_titulo, bg=self.co1)
        frame_header.pack(expand=True, fill="both")
        
        # Título centralizado
        label_titulo = tk.Label(
            frame_header, 
            text=texto, 
            font=("Arial", 14, "bold"), 
            bg=self.co1, 
            fg=self.co0
        )
        label_titulo.pack(side=tk.LEFT, padx=10, pady=15)
        
        # Badge indicando nova versão com filtro inteligente
        badge_frame = tk.Frame(frame_header, bg=self.co2, relief="raised", bd=2)
        badge_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        tk.Label(badge_frame, text="✨ NOVO: FILTRO INTELIGENTE", 
                font=("Arial", 8, "bold"), bg=self.co2, fg="white", 
                padx=8, pady=2).pack()
    
    def criar_area_selecao(self):
        # Limpar widgets existentes
        for widget in self.frame_selecao.winfo_children():
            widget.destroy()
        
        # Frame para turno
        self.frame_turno_sel = tk.Frame(self.frame_selecao, bg=self.co0)
        self.frame_turno_sel.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(self.frame_turno_sel, text="Turno:", bg=self.co0, font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.turno_var = tk.StringVar(value=self.turno_atual)
        turno_cb = ttk.Combobox(self.frame_turno_sel, textvariable=self.turno_var, values=["Matutino", "Vespertino"], width=15, state="readonly")
        turno_cb.pack(side=tk.LEFT)
        turno_cb.bind("<<ComboboxSelected>>", self.atualizar_horarios)
        
        # Frame para série/ano
        self.frame_serie_sel = tk.Frame(self.frame_selecao, bg=self.co0)
        self.frame_serie_sel.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(self.frame_serie_sel, text="Série/Ano:", bg=self.co0, font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Valores vêm do banco de dados
        series_nomes = [serie['nome'] for serie in self.series_dados] if self.series_dados else ["1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano"]
        self.serie_var = tk.StringVar()
        serie_cb = ttk.Combobox(self.frame_serie_sel, textvariable=self.serie_var, values=series_nomes, width=15, state="readonly")
        serie_cb.pack(side=tk.LEFT)
        serie_cb.bind("<<ComboboxSelected>>", self.carregar_turmas)
        
        # Frame para turma
        self.frame_turma_sel = tk.Frame(self.frame_selecao, bg=self.co0)
        self.frame_turma_sel.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(self.frame_turma_sel, text="Turma:", bg=self.co0, font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.turma_var = tk.StringVar()
        self.turma_cb = ttk.Combobox(self.frame_turma_sel, textvariable=self.turma_var, width=15, state="readonly")
        self.turma_cb.pack(side=tk.LEFT)
        self.turma_cb.bind("<<ComboboxSelected>>", self.carregar_horarios)
        
        # Frame para seleção de professor (oculto até modo Professor ser escolhido)
        self.frame_prof_sel = tk.Frame(self.frame_selecao, bg=self.co0)
        # não chama .pack() aqui
        tk.Label(self.frame_prof_sel, text="Professor:", bg=self.co0,
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.professor_var = tk.StringVar()
        prof_nomes = [p['nome'] for p in (self.professores or [])]
        self.professor_cb = ttk.Combobox(self.frame_prof_sel, textvariable=self.professor_var,
                                         values=prof_nomes, width=28, state="readonly")
        self.professor_cb.pack(side=tk.LEFT)
        self.professor_cb.bind("<<ComboboxSelected>>", self._on_professor_selecionado)

        # Frame para seleção de visualização
        frame_visualizacao = tk.Frame(self.frame_selecao, bg=self.co0)
        frame_visualizacao.pack(side=tk.RIGHT, padx=10, pady=5)
        
        tk.Label(frame_visualizacao, text="Visualizar:", bg=self.co0, font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.visualizacao_var = tk.StringVar(value="Turma")
        visualizacao_cb = ttk.Combobox(frame_visualizacao, textvariable=self.visualizacao_var, 
                                      values=["Turma", "Professor", "Dia da Semana"], width=15, state="readonly")
        visualizacao_cb.pack(side=tk.LEFT)
        visualizacao_cb.bind("<<ComboboxSelected>>", self.atualizar_visualizacao)
    
    def carregar_turmas(self, event=None):
        serie_nome = self.serie_var.get()
        if not serie_nome:
            return
            
        # Definir turno automaticamente baseado na série (1-5 matutino, 6-9 vespertino)
        serie_num = ''.join(filter(str.isdigit, serie_nome))
        turno_anterior = self.turno_atual
        if serie_num:
            serie_num = int(serie_num)
            if 1 <= serie_num <= 5:
                self.turno_var.set("Matutino")
                self.turno_atual = "Matutino"
            elif 6 <= serie_num <= 9:
                self.turno_var.set("Vespertino")
                self.turno_atual = "Vespertino"
        
        # Se o turno mudou, recriar a grade de horários
        if turno_anterior != self.turno_atual:
            self.criar_grade_horarios()
        
        try:
            # Encontrar o id da série
            serie_id = None
            for serie in self.series_dados:
                if serie['nome'] == serie_nome:
                    serie_id = serie['id']
                    break
            
            if not serie_id:
                self.turma_cb['values'] = []
                return
                
            # Buscar turmas no banco de dados
            conn = conectar_bd()
            cursor = conn.cursor(dictionary=True)
            
            # Para simplificar, mapeamos MAT para Matutino e VESP para Vespertino
            turno_bd = "MAT" if self.turno_atual == "Matutino" else "VESP"
            
            # Buscar turmas do ano letivo 2026
            cursor.execute("""
                SELECT t.id, t.nome, t.serie_id 
                FROM turmas t
                INNER JOIN anosletivos al ON t.ano_letivo_id = al.id
                WHERE t.serie_id = %s 
                AND t.turno = %s
                AND t.escola_id = 60
                AND al.ano_letivo = 2026
                ORDER BY t.nome
            """, (serie_id, turno_bd))
            
            turmas = cursor.fetchall()
            
            # Debug
            logger.info(f"Turmas encontradas para série {serie_id}, turno {turno_bd}:")
            for t in turmas:
                logger.info(f"  ID: {t['id']}, Nome: '{t['nome']}', Serie ID: {t['serie_id']}")
            
            if turmas:
                self.turmas_dados = []
                turma_nomes = []
                
                for turma in turmas:
                    # Construir nome completo da turma
                    turma_nome = turma['nome'] if turma['nome'] and turma['nome'].strip() else "Única"
                    
                    # Se tiver apenas uma turma sem nome, não adicionar sufixo
                    if len(turmas) == 1 and turma_nome == "Única":
                        display_nome = serie_nome  # Apenas mostrar o nome da série
                    else:
                        display_nome = f"{serie_nome} {turma_nome}"
                    
                    # Guardar dados da turma
                    turma_item = {'id': turma['id'], 'nome': turma['nome'], 'display': display_nome}
                    self.turmas_dados.append(turma_item)
                    turma_nomes.append(display_nome)
                    
                logger.info(f"✓ Turmas processadas: {turma_nomes}")
                self.turma_cb['values'] = turma_nomes
                
                # Selecionar a primeira turma
                if turma_nomes:
                    self.turma_var.set(turma_nomes[0])
                    self.carregar_horarios()
            else:
                logger.warning(f"⚠️ Nenhuma turma encontrada para série {serie_id}, turno {turno_bd}")
                # Fallback para turmas fictícias
                turma_nomes = [f"Turma {serie_nome}"]
                self.turmas_dados = [{'id': None, 'nome': turma_nomes[0], 'display': turma_nomes[0]}]
                self.turma_cb['values'] = turma_nomes
                self.turma_var.set(turma_nomes[0])
                
            cursor.close()
            conn.close()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar turmas: {str(e)}")
            logger.error(f"Erro detalhado: {str(e)}")
            
            # Fallback para dados fictícios em caso de erro
            turma_nomes = [f"Turma {serie_nome} {letra}" for letra in "ABC"]
            self.turmas_dados = [{'id': None, 'nome': nome, 'nome_temporario': True} for nome in turma_nomes]
            self.turma_cb['values'] = turma_nomes
    
    def carregar_horarios(self, event=None):
        turma_nome = self.turma_var.get()
        # Permitir nome vazio para turmas únicas
        if turma_nome is None:
            return
            
        # Encontrar ID da turma selecionada
        self.turma_id = None
        for turma in self.turmas_dados:
            # Comparar pelo campo display (nome exibido no combobox) ou nome
            if turma.get('display', turma.get('nome', '')) == turma_nome or turma.get('nome', '') == turma_nome:
                self.turma_id = turma['id']
                break
                
        self.turma_atual = turma_nome
        
        # Limpar células existentes
        for celula in self.celulas_horario.values():
            celula.set('')  # Combobox usa set() para definir valor
        
        try:
            # Tentar carregar dados do banco de dados se a turma tiver ID
            if self.turma_id:
                try:
                    conn = conectar_bd()
                    cursor = conn.cursor(dictionary=True)
                    
                    # Verificar se coluna data_saida existe
                    cursor.execute("""
                        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        AND TABLE_NAME = 'funcionarios' 
                        AND COLUMN_NAME = 'data_saida'
                    """)
                    has_data_saida = cursor.fetchone()['COUNT(*)'] > 0
                    
                    # Construir query com filtro de professores ativos
                    if has_data_saida:
                        query = """
                            SELECT h.dia, h.horario, h.valor, h.disciplina_id, h.professor_id
                            FROM horarios_importados h
                            LEFT JOIN funcionarios f ON h.professor_id = f.id
                            WHERE h.turma_id = %s
                            AND h.ano_letivo = 2026
                            AND (h.professor_id IS NULL OR f.data_saida IS NULL OR f.data_saida = '')
                        """
                    else:
                        query = """
                            SELECT dia, horario, valor, disciplina_id, professor_id 
                            FROM horarios_importados 
                            WHERE turma_id = %s AND ano_letivo = 2026
                        """
                    
                    cursor.execute(query, (self.turma_id,))
                    rows = cursor.fetchall()
                    cursor.close()
                    conn.close()

                    # Preencher células com os dados recuperados
                    horarios_lista = self.horarios_matutino if self.turno_atual == "Matutino" else self.horarios_vespertino
                    for item in rows:
                        dia = item.get('dia')
                        horario = item.get('horario')
                        valor = item.get('valor')

                        # localizar coluna pelo dia
                        try:
                            col = self.dias_semana.index(dia) + 1
                        except ValueError:
                            # dia não encontrado na visualização atual
                            continue

                        # localizar linha pelo horário
                        row_index = None
                        if horario in horarios_lista:
                            row_index = horarios_lista.index(horario) + 1
                        else:
                            # Suportar formato "Linha X" do GEDUC
                            if isinstance(horario, str) and horario.startswith('Linha '):
                                try:
                                    num = int(horario.split()[1])
                                    row_index = num
                                except Exception:
                                    row_index = None
                            # suportar horários genéricos R1, R2...
                            elif isinstance(horario, str) and horario.upper().startswith('R'):
                                try:
                                    num = int(horario[1:])
                                    row_index = num
                                except Exception:
                                    row_index = None

                        if row_index is None:
                            continue

                        cel = self.celulas_horario.get((row_index, col))
                        if cel:
                            # Combobox usa set() em vez de delete/insert
                            cel.set(valor)

                except Exception:
                    # Em caso de problema com o banco, cair para dados fictícios
                    self.carregar_horarios_ficticios()
            else:
                # Se não tiver ID, usar dados fictícios
                self.carregar_horarios_ficticios()
            
            # Atualizar comboboxes com disciplinas vinculadas à turma
            self.atualizar_disciplinas_comboboxes()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar horários: {str(e)}")
            # Em caso de erro, manter células vazias
    
    def carregar_horarios_ficticios(self):
        """Limpa todas as células quando não há dados no banco."""
        for coord, celula in self.celulas_horario.items():
            row, col = coord
            celula.set('')
        logger.info("Nenhum horário encontrado no banco para esta turma - células limpas.")

    def atualizar_visualizacao(self, event=None):
        visualizacao = self.visualizacao_var.get()
        _frames_turma = ('frame_turno_sel', 'frame_serie_sel', 'frame_turma_sel')
        if visualizacao == "Turma":
            # Mostrar seletores de turma, ocultar seletor de professor
            for attr in _frames_turma:
                f = getattr(self, attr, None)
                if f:
                    f.pack(side=tk.LEFT, padx=10, pady=5)
            if hasattr(self, 'frame_prof_sel'):
                self.frame_prof_sel.pack_forget()
            self.criar_grade_horarios()
        elif visualizacao == "Professor":
            # Ocultar seletores de turma, mostrar seletor de professor
            for attr in _frames_turma:
                f = getattr(self, attr, None)
                if f:
                    f.pack_forget()
            if hasattr(self, 'frame_prof_sel'):
                self.frame_prof_sel.pack(side=tk.LEFT, padx=10, pady=5)
            self.criar_grade_horarios_professor()
        elif visualizacao == "Dia da Semana":
            messagebox.showinfo("Info", "Visualização por dia da semana será implementada")

    def _on_professor_selecionado(self, event=None):
        self.criar_grade_horarios_professor()

    def _abreviar_disciplina(self, nome):
        """Retorna abreviação compacta do nome da disciplina."""
        _ABREV = {
            'LÍNGUA PORTUGUESA': 'L.PORT', 'LINGUA PORTUGUESA': 'L.PORT',
            'MATEMÁTICA': 'MAT', 'MATEMATICA': 'MAT',
            'CIÊNCIAS': 'CNC', 'CIENCIAS': 'CNC',
            'HISTÓRIA': 'HST', 'HISTORIA': 'HST',
            'GEOGRAFIA': 'GGF',
            'ARTE': 'ARTE',
            'EDUCAÇÃO FÍSICA': 'ED.FÍS', 'EDUCACAO FISICA': 'ED.FÍS',
            'ENSINO RELIGIOSO': 'ENS.REL',
            'INGLÊS': 'INGL', 'INGLES': 'INGL',
            'ESPANHOL': 'ESP',
            'FÍSICA': 'FÍS', 'FISICA': 'FÍS',
            'QUÍMICA': 'QUÍM', 'QUIMICA': 'QUÍM',
            'BIOLOGIA': 'BIO',
            'FILOSOFIA': 'FILOS',
            'SOCIOLOGIA': 'SOCIO',
            'REDAÇÃO': 'RED', 'REDACAO': 'RED',
            '<VAGO>': 'VAGO',
        }
        nome_u = (nome or '').upper().strip()
        if nome_u in _ABREV:
            return _ABREV[nome_u]
        # desconhecida: primeiras 7 letras
        return nome_u[:7] if nome_u else ''

    def criar_grade_horarios_professor(self):
        """Cria grade de leitura com todos os horários do professor selecionado.
        Células preenchidas: '{disc_abrev}\n{série_num}{turma_letra}-{turno_abrev}'
        Células sem aula: 'VAGO'
        """
        for widget in self.frame_grade.winfo_children():
            widget.destroy()

        prof_nome = self.professor_var.get() if hasattr(self, 'professor_var') else ''
        if not prof_nome:
            tk.Label(self.frame_grade, text="Selecione um professor para visualizar os horários.",
                     bg=self.co0, font=("Arial", 12), fg=self.co7).pack(pady=60)
            return

        # Encontrar professor_id
        professor_id = None
        for p in (self.professores or []):
            if p['nome'] == prof_nome:
                professor_id = p['id']
                break
        if not professor_id:
            tk.Label(self.frame_grade, text="Professor não encontrado.",
                     bg=self.co0, font=("Arial", 11), fg=self.co8).pack(pady=40)
            return

        try:
            conn = conectar_bd()
            if not conn:
                return
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT DISTINCT h.dia, h.horario, h.valor,
                       t.nome AS turma_nome, s.nome AS serie_nome, t.turno
                FROM horarios_importados h
                INNER JOIN turmas t ON h.turma_id = t.id
                INNER JOIN series s ON t.serie_id = s.id
                INNER JOIN disciplinas dh ON h.disciplina_id = dh.id
                INNER JOIN disciplinas dfd ON dfd.nome = dh.nome
                INNER JOIN funcionario_disciplinas fd
                    ON fd.disciplina_id = dfd.id
                    AND (fd.turma_id = h.turma_id OR fd.turma_id IS NULL)
                WHERE fd.funcionario_id = %s AND h.ano_letivo = 2026
            """, (professor_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao buscar horários do professor: {e}")
            messagebox.showerror("Erro", f"Erro ao buscar horários:\n{e}")
            return

        # Mapa {(horario, dia): texto_celula}
        _turno_abrev = {'MAT': 'MAT', 'VESP': 'VESP',
                        'Matutino': 'MAT', 'Vespertino': 'VESP'}
        mapa_prof = {}
        for item in rows:
            dia = item['dia']
            horario = item['horario']
            disc = self._abreviar_disciplina(item['valor'])
            digits = ''.join(c for c in (item['serie_nome'] or '') if c.isdigit())
            serie_num = digits[:1] if digits else '?'
            turma_letra = (item['turma_nome'] or '').strip().upper()
            turno_ab = _turno_abrev.get((item['turno'] or '').strip(), '')
            turma_info = f"{serie_num}{turma_letra}-{turno_ab}"
            mapa_prof[(horario, dia)] = f"{disc}\n{turma_info}"

        # Canvas + scrollbars
        canvas = tk.Canvas(self.frame_grade, bg=self.co0)
        scrollbar = ttk.Scrollbar(self.frame_grade, orient="vertical", command=canvas.yview)
        scrollbar_h = ttk.Scrollbar(self.frame_grade, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_h.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        scrollbar.pack(side="right", fill="y")
        scrollbar_h.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)

        frame_c = tk.Frame(canvas, bg=self.co0)
        canvas.create_window((0, 0), window=frame_c, anchor="nw")

        # Cabeçalho
        tk.Label(frame_c, text="Horário", bg=self.co1, fg=self.co0,
                 font=("Arial", 10, "bold"), width=13, relief="ridge", pady=5
                 ).grid(row=0, column=0, sticky="nsew")
        for col, dia in enumerate(self.dias_semana, 1):
            tk.Label(frame_c, text=dia, bg=self.co1, fg=self.co0,
                     font=("Arial", 10, "bold"), width=18, relief="ridge", pady=5
                     ).grid(row=0, column=col, sticky="nsew")

        todos_horarios = self.horarios_matutino + self.horarios_vespertino
        grid_row = 1
        turno_bloco = None
        for horario in todos_horarios:
            bloco = "MAT" if horario in self.horarios_matutino else "VESP"

            # Separador visual entre matutino e vespertino
            if turno_bloco is not None and bloco != turno_bloco:
                sep = tk.Frame(frame_c, bg=self.co9, height=3)
                sep.grid(row=grid_row, column=0, columnspan=6, sticky="ew")
                grid_row += 1
            turno_bloco = bloco

            # Linha de intervalo
            if horario in ("09:40-10:00", "15:40-16:00"):
                tk.Label(frame_c, text="INTERVALO", bg=self.co6, fg=self.co7,
                         font=("Arial", 10, "bold"), width=13, relief="ridge", pady=4
                         ).grid(row=grid_row, column=0, sticky="nsew")
                tk.Label(frame_c, text="INTERVALO", bg=self.co6, fg=self.co7,
                         font=("Arial", 10, "bold"), relief="ridge", pady=4
                         ).grid(row=grid_row, column=1, columnspan=5, sticky="nsew")
            else:
                tk.Label(frame_c, text=horario, bg=self.co4, fg=self.co0,
                         font=("Arial", 10), width=13, relief="ridge", pady=4
                         ).grid(row=grid_row, column=0, sticky="nsew")
                for col, dia in enumerate(self.dias_semana, 1):
                    texto = mapa_prof.get((horario, dia), "VAGO")
                    preenchido = texto != "VAGO"
                    bg = self.co2 if preenchido else "#EFEFEF"
                    fg = "white" if preenchido else "#999999"
                    fnt = ("Arial", 9, "bold") if preenchido else ("Arial", 9)
                    tk.Label(frame_c, text=texto, bg=bg, fg=fg,
                             font=fnt, width=18, relief="ridge",
                             pady=4, justify="center", wraplength=130
                             ).grid(row=grid_row, column=col, sticky="nsew")
            grid_row += 1

        for i in range(grid_row):
            frame_c.grid_rowconfigure(i, weight=1)
        for i in range(len(self.dias_semana) + 1):
            frame_c.grid_columnconfigure(i, weight=1)

    def atualizar_horarios(self, event=None):
        self.turno_atual = self.turno_var.get()
        self.criar_grade_horarios()
    
    def criar_grade_horarios(self):
        # Limpar widgets existentes
        for widget in self.frame_grade.winfo_children():
            widget.destroy()
        
        # Criar canvas com scrollbar
        canvas = tk.Canvas(self.frame_grade, bg=self.co0)
        scrollbar = ttk.Scrollbar(self.frame_grade, orient="vertical", command=canvas.yview)
        scrollbar_h = ttk.Scrollbar(self.frame_grade, orient="horizontal", command=canvas.xview)
        
        # Configurar o canvas
        canvas.configure(yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_h.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Posicionar scrollbars e canvas
        scrollbar.pack(side="right", fill="y")
        scrollbar_h.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Frame interno para conteúdo
        frame_conteudo = tk.Frame(canvas, bg=self.co0)
        canvas.create_window((0, 0), window=frame_conteudo, anchor="nw")
        
        # Escolher lista de horários com base no turno
        horarios = self.horarios_matutino if self.turno_atual == "Matutino" else self.horarios_vespertino
        
        # Criar cabeçalho (dias da semana)
        tk.Label(frame_conteudo, text="Horário", bg=self.co1, fg=self.co0, 
                font=("Arial", 10, "bold"), width=12, relief="ridge", pady=5).grid(row=0, column=0, sticky="nsew")
        
        for col, dia in enumerate(self.dias_semana, 1):
            tk.Label(frame_conteudo, text=dia, bg=self.co1, fg=self.co0, 
                    font=("Arial", 10, "bold"), width=15, relief="ridge", pady=5).grid(row=0, column=col, sticky="nsew")
        
        # Criar linhas de horários
        self.celulas_horario = {}
        for row, horario in enumerate(horarios, 1):
            # Horário na primeira coluna
            if horario in ["09:40-10:00", "15:40-16:00"]:  # Intervalo
                bg_color = self.co6  # Amarelo para intervalo
                texto = "INTERVALO"
                tk.Label(frame_conteudo, text=texto, bg=bg_color, fg=self.co7, 
                        font=("Arial", 10, "bold"), width=12, relief="ridge", pady=5).grid(
                        row=row, column=0, sticky="nsew")
                
                # Criar célula que ocupa todos os dias para o intervalo
                texto_intervalo = tk.Label(frame_conteudo, text="INTERVALO", bg=bg_color, fg=self.co7, 
                                        font=("Arial", 10, "bold"), relief="ridge", pady=5)
                texto_intervalo.grid(row=row, column=1, columnspan=5, sticky="nsew")
            else:
                tk.Label(frame_conteudo, text=horario, bg=self.co4, fg=self.co0, 
                        font=("Arial", 10), width=12, relief="ridge", pady=5).grid(
                        row=row, column=0, sticky="nsew")
                
                # Células para disciplinas (comboboxes) - CORRIGIDO
                for col, dia in enumerate(self.dias_semana, 1):
                    # Criar combobox SEM opções de cor
                    celula = ttk.Combobox(frame_conteudo, width=30, font=("Arial", 10), 
                                        justify="center", state="readonly")
                    celula.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
                    
                    # Armazenar referência da célula
                    self.celulas_horario[(row, col)] = celula
                    
                    # Evento de seleção para auto-salvar
                    celula.bind("<<ComboboxSelected>>", lambda e, r=row, c=col: self.salvar_celula_horario(r, c))
        
        # Configurar redimensionamento
        for i in range(len(horarios) + 1):
            frame_conteudo.grid_rowconfigure(i, weight=1)
        for i in range(len(self.dias_semana) + 1):
            frame_conteudo.grid_columnconfigure(i, weight=1)
        
        # Atualizar comboboxes com disciplinas da turma
        self.atualizar_disciplinas_comboboxes()

    def criar_barra_botoes(self):
        # Limpar widgets existentes
        for widget in self.frame_botoes.winfo_children():
            widget.destroy()
        
        # Botões de ação
        ttk.Button(self.frame_botoes, text="💾 Salvar Horários", 
                 command=self.salvar_horarios).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.frame_botoes, text="🌐 Importar do GEDUC", 
                 command=self.importar_geduc).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.frame_botoes, text="🖨️ Imprimir Horários", 
                 command=self.imprimir_horarios).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.frame_botoes, text="📊 Exportar para Excel", 
                 command=self.exportar_excel).pack(side=tk.LEFT, padx=5)
    
    def salvar_horarios(self):
        """Salva todos os horários da turma no banco de dados."""
        if not self.turma_atual:
            messagebox.showwarning("Atenção", "Selecione uma turma antes de salvar.")
            return
        if not self.turma_id:
            messagebox.showerror("Erro", "ID da turma não encontrado.")
            return

        horarios = self.horarios_matutino if self.turno_atual == "Matutino" else self.horarios_vespertino
        disc_por_nome = {d['nome']: d['id'] for d in (self.disciplinas or [])}
        rows_salvos = 0

        try:
            conn = conectar_bd()
            if not conn:
                messagebox.showerror("Erro", "Falha ao conectar ao banco de dados.")
                return

            cursor = conn.cursor()

            for coord, celula in self.celulas_horario.items():
                row, col = coord
                if row == 4:  # Intervalo
                    continue
                valor = celula.get().strip()
                horario = horarios[row - 1]
                dia = self.dias_semana[col - 1]
                disciplina_id = disc_por_nome.get(valor)

                if not valor:
                    cursor.execute(
                        "DELETE FROM horarios_importados WHERE turma_id=%s AND dia=%s AND horario=%s AND ano_letivo=2026",
                        (self.turma_id, dia, horario)
                    )
                else:
                    cursor.execute("""
                        INSERT INTO horarios_importados (turma_id, dia, horario, valor, disciplina_id, professor_id, ano_letivo)
                        VALUES (%s, %s, %s, %s, %s, NULL, 2026)
                        ON DUPLICATE KEY UPDATE valor=VALUES(valor), disciplina_id=VALUES(disciplina_id)
                    """, (self.turma_id, dia, horario, valor, disciplina_id))
                    rows_salvos += 1

            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo("Sucesso", f"Horários da {self.turma_atual} salvos!\n{rows_salvos} célula(s) salva(s).")
            logger.info(f"Horários salvos: turma={self.turma_atual}, células={rows_salvos}")

        except Exception as e:
            logger.error(f"Erro ao salvar horários: {e}", exc_info=True)
            messagebox.showerror("Erro", f"Erro ao salvar horários:\n{str(e)}")

    def salvar_celula_horario(self, row, col):
        """Salva uma célula individual de horário no banco de dados."""
        if not self.turma_id:
            logger.warning("Tentativa de salvar sem turma selecionada")
            return
        
        # Obter dados da célula
        celula = self.celulas_horario.get((row, col))
        if not celula:
            return
        
        # Obter valor selecionado (nome da disciplina)
        valor = celula.get()
        if not valor or valor == "":
            # Célula vazia - deletar do banco se existir
            try:
                conn = conectar_bd()
                if conn:
                    cursor = conn.cursor()
                    horarios = self.horarios_matutino if self.turno_atual == "Matutino" else self.horarios_vespertino
                    horario = horarios[row-1]
                    dia = self.dias_semana[col-1]
                    
                    query = """
                        DELETE FROM horarios_importados 
                        WHERE turma_id = %s AND dia = %s AND horario = %s AND ano_letivo = 2026
                    """
                    cursor.execute(query, (self.turma_id, dia, horario))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    logger.info(f"Horário removido: {dia} {horario}")
            except Exception as e:
                logger.error(f"Erro ao remover horário: {e}")
            return
        
        # Buscar disciplina_id pelo nome
        disciplina_id = None
        for disc in self.disciplinas:
            if disc['nome'] == valor:
                disciplina_id = disc['id']
                break
        
        # Preparar dados para salvar
        horarios = self.horarios_matutino if self.turno_atual == "Matutino" else self.horarios_vespertino
        horario = horarios[row-1]
        dia = self.dias_semana[col-1]
        
        # Salvar no banco usando upsert
        try:
            conn = conectar_bd()
            if not conn:
                logger.error("Falha ao conectar ao banco")
                return
            
            cursor = conn.cursor()
            
            # Usar INSERT ... ON DUPLICATE KEY UPDATE
            query = """
                INSERT INTO horarios_importados 
                (turma_id, dia, horario, valor, disciplina_id, professor_id, ano_letivo)
                VALUES (%s, %s, %s, %s, %s, NULL, 2026)
                ON DUPLICATE KEY UPDATE
                valor = VALUES(valor),
                disciplina_id = VALUES(disciplina_id)
            """
            
            cursor.execute(query, (self.turma_id, dia, horario, valor, disciplina_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✓ Horário salvo: {dia} {horario} = {valor}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar célula: {e}", exc_info=True)
    
    def imprimir_horarios(self):
        """Abre modal com as 3 opções de impressão."""
        if self.turma_atual is None:
            messagebox.showwarning("Atenção", "Selecione uma turma antes de imprimir.")
            return

        modal = tk.Toplevel(self.janela)
        modal.title("Opções de Impressão")
        modal.geometry("450x310")
        modal.transient(self.janela)
        modal.grab_set()
        modal.configure(bg=self.co0)
        modal.resizable(False, False)

        modal.update_idletasks()
        x = self.janela.winfo_rootx() + self.janela.winfo_width() // 2 - 225
        y = self.janela.winfo_rooty() + self.janela.winfo_height() // 2 - 155
        modal.geometry(f"+{x}+{y}")

        tk.Label(modal, text="🖨️  Opções de Impressão",
                 font=("Arial", 13, "bold"), bg=self.co0, fg=self.co1).pack(pady=(18, 10))

        opcao_var = tk.StringVar(value="cartaz")
        frame_opcoes = tk.Frame(modal, bg=self.co0)
        frame_opcoes.pack(fill="x", padx=30, pady=2)

        serie_nome = self.serie_var.get() if hasattr(self, 'serie_var') else ""
        opcoes = [
            ("cartaz",
             "📋  Cartaz da turma",
             f"Folha A4 paisagem completa — {serie_nome} {self.turma_atual} ({self.turno_atual})"),
            ("alunos",
             "🗂️   Mini-horários para alunos",
             "PDF com 3 páginas idênticas — ao imprimir, selecione \"3 páginas por folha\" para recortar"),
            ("coordenacao",
             "📚  Todas as turmas — coordenação/gestão",
             "Um cartaz por turma, todas as turmas reunidas em um único PDF"),
        ]

        for val, titulo, descricao in opcoes:
            fr = tk.Frame(frame_opcoes, bg=self.co0)
            fr.pack(fill="x", pady=4)
            tk.Radiobutton(fr, text=titulo, variable=opcao_var, value=val,
                           bg=self.co0, font=("Arial", 10, "bold"),
                           activebackground=self.co0).pack(anchor="w")
            tk.Label(fr, text=f"    {descricao}", bg=self.co0,
                     font=("Arial", 8), fg=self.co7).pack(anchor="w")

        frame_botoes = tk.Frame(modal, bg=self.co0)
        frame_botoes.pack(fill="x", padx=20, pady=(14, 18))

        def gerar():
            opcao = opcao_var.get()
            modal.destroy()
            if opcao == "cartaz":
                self.gerar_pdf_turma(modo="cartaz")
            elif opcao == "alunos":
                self.gerar_pdf_turma(modo="alunos")
            else:
                self.gerar_pdf_todas_turmas()

        ttk.Button(frame_botoes, text="Cancelar", command=modal.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(frame_botoes, text="Gerar PDF", command=gerar).pack(side=tk.RIGHT, padx=5)
    
    # ──────────────────────────────────────────────────────────────────────────
    # Helpers de geração de PDF
    # ──────────────────────────────────────────────────────────────────────────

    def _buscar_mapa_horarios(self, turma_id, horarios_lista):
        """Consulta o banco e retorna (mapa, cores_professor).
        mapa: {(row_idx, col_idx): {'valor': str, 'professor_id': int|None}}
        cores_professor: {professor_id: Color}
        """
        mapa = {}
        cores_professor = {}
        _paleta = [
            colors.Color(0.80, 0.90, 1.00),
            colors.Color(1.00, 0.90, 0.80),
            colors.Color(0.88, 1.00, 0.80),
            colors.Color(1.00, 0.80, 0.90),
            colors.Color(0.95, 0.95, 0.78),
            colors.Color(0.90, 0.80, 1.00),
            colors.Color(0.80, 1.00, 0.90),
            colors.Color(1.00, 0.85, 0.85),
            colors.Color(0.85, 0.95, 1.00),
            colors.Color(0.95, 0.90, 1.00),
        ]
        try:
            conn = conectar_bd()
            if not conn:
                return mapa, cores_professor
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT h.dia, h.horario, h.valor, h.professor_id
                FROM horarios_importados h
                WHERE h.turma_id = %s AND h.ano_letivo = 2026
            """, (turma_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            prof_ids = sorted({r['professor_id'] for r in rows if r.get('professor_id')})
            cores_professor = {pid: _paleta[i % len(_paleta)] for i, pid in enumerate(prof_ids)}

            for item in rows:
                try:
                    col = self.dias_semana.index(item['dia'])
                except ValueError:
                    continue
                if item['horario'] not in horarios_lista:
                    continue
                row_idx = horarios_lista.index(item['horario'])
                mapa[(row_idx, col)] = {
                    'valor': item['valor'] or '',
                    'professor_id': item.get('professor_id'),
                }
        except Exception as e:
            logger.error(f"Erro em _buscar_mapa_horarios: {e}")
        return mapa, cores_professor

    def _build_tabela_horario(self, mapa, horarios_lista, col_widths,
                               font_size=9, row_height=None, colunas_negrito=None):
        """Constrói e retorna um Table de horários sem coluna de horário e sem linha de intervalo.
        col_widths deve ter len(dias_semana) elementos.
        colunas_negrito: lista de col_idx (0-based) que aparecem em negrito (ex.: Ensino Religioso).
        Células usam Paragraph para quebra de linha automática por palavra.
        """
        IDX_INTERVALO = 3  # índice 0-based da linha de intervalo

        # Estilos de parágrafo para células (fonte controlada pelo Paragraph, não pelo TableStyle)
        base = ParagraphStyle(
            '_CelBase',
            fontName='Helvetica', fontSize=font_size,
            leading=font_size * 1.25, alignment=1,
            wordWrap='LTR',
        )
        base_bold = ParagraphStyle(
            '_CelBold',
            fontName='Helvetica-Bold', fontSize=font_size,
            leading=font_size * 1.25, alignment=1,
            wordWrap='LTR',
        )
        header_style = ParagraphStyle(
            '_CelHeader',
            fontName='Helvetica-Bold', fontSize=font_size,
            leading=font_size * 1.25, alignment=1,
            wordWrap='LTR',
        )

        negrito_set = set(colunas_negrito or [])

        # Cabeçalho: apenas os dias da semana
        dados = [[Paragraph(d, header_style) for d in self.dias_semana]]

        # row_map: original_row_idx → índice na tabela (1-based, 0 = cabeçalho)
        row_map = {}
        table_row = 1
        for i in range(len(horarios_lista)):
            if i == IDX_INTERVALO:
                continue
            linha = []
            for j in range(len(self.dias_semana)):
                d = mapa.get((i, j))
                valor = d['valor'] if d else ""
                st = base_bold if j in negrito_set else base
                linha.append(Paragraph(valor, st))
            dados.append(linha)
            row_map[i] = table_row
            table_row += 1

        row_heights_arg = [row_height] * len(dados) if row_height else None
        tabela = Table(dados, colWidths=col_widths, rowHeights=row_heights_arg)

        estilo = TableStyle([
            ("BACKGROUND", (0, 0), (-1,  0), colors.HexColor("#E8E8E8")),
            ("GRID",       (0, 0), (-1, -1), 0.8, colors.HexColor("#555555")),
            ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ])

        # Destaque suave por professor
        for (row_idx, col_idx), d in mapa.items():
            if row_idx == IDX_INTERVALO:
                continue
            if d.get("professor_id") and row_idx in row_map:
                t_row = row_map[row_idx]
                estilo.add("BACKGROUND",
                           (col_idx, t_row),
                           (col_idx, t_row),
                           colors.Color(0.87, 0.95, 1.0))

        tabela.setStyle(estilo)
        return tabela

    def _elementos_cartaz(self, mapa, horarios_lista, titulo_str, estilos,
                           nota_rodape="Ano Letivo 2026", colunas_negrito=None):
        """Retorna lista de Flowables para um cartaz A4 paisagem."""
        # Margens default de create_pdf_doc: left=36, right=18
        usable_w = landscape(A4)[0] - 36 - 18  # ≈ 788pt

        estilo_titulo = ParagraphStyle(
            'CartazTitulo', parent=estilos['Normal'],
            fontSize=16, fontName='Helvetica-Bold',
            leading=22, alignment=1, textColor=colors.HexColor("#1A1A1A"),
        )
        estilo_rodape = ParagraphStyle(
            'CartazRodape', parent=estilos['Normal'],
            fontSize=8, alignment=1, textColor=colors.HexColor("#666666"),
        )

        # Sem coluna de horários — divide a largura igualmente pelos dias
        col_widths = [usable_w / len(self.dias_semana)] * len(self.dias_semana)

        tabela = self._build_tabela_horario(
            mapa, horarios_lista, col_widths, font_size=19, row_height=72,
            colunas_negrito=colunas_negrito,
        )

        return [
            Paragraph(titulo_str, estilo_titulo),
            HRFlowable(width=usable_w, thickness=1.2, color=colors.HexColor("#333333"),
                       spaceAfter=6),
            tabela,
            Spacer(1, 8),
            Paragraph(nota_rodape, estilo_rodape),
        ]

    def gerar_pdf_turma(self, modo='cartaz'):
        """Gera PDF do horário da turma atual.
        modo: 'cartaz' – A4 paisagem, folha inteira para afixar
              'alunos'  – A4 retrato, 3 cópias recortáveis
        """
        if self.turma_atual is None:
            messagebox.showwarning("Atenção", "Selecione uma turma antes de imprimir.")
            return
        if not self.turma_id:
            messagebox.showerror("Erro", "ID da turma não encontrado.")
            return

        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            caminho = temp_file.name
            temp_file.close()

            horarios = self.horarios_matutino if self.turno_atual == "Matutino" else self.horarios_vespertino
            mapa, _ = self._buscar_mapa_horarios(self.turma_id, horarios)

            serie_nome = self.serie_var.get() if hasattr(self, 'serie_var') else ""
            # turma_atual já contém o display completo (ex.: "1º Ano A");
            # se a turma não tiver letra/nome, turma_atual == serie_nome.
            titulo_str = f"Horário de Aulas — {self.turma_atual or serie_nome} — {self.turno_atual}"
            estilos = getSampleStyleSheet()

            # Para Fundamental I (1º-5º ano): destaca coluna de Ensino Religioso em negrito
            _serie_digits = ''.join(c for c in (serie_nome or '') if c.isdigit())
            _serie_num = int(_serie_digits[0]) if _serie_digits else 0
            colunas_negrito = sorted({
                col for (_, col), d in mapa.items()
                if 'ENSINO RELIGIOSO' in (d.get('valor') or '').upper()
            }) if 1 <= _serie_num <= 5 else None

            if modo == 'alunos':
                self._gerar_pdf_alunos(caminho, mapa, horarios, titulo_str, estilos,
                                       colunas_negrito=colunas_negrito)
            else:
                nota = (f"Ano Letivo 2026  ·  "
                        f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                doc = create_pdf_doc(caminho, pagesize=landscape(A4))
                doc.build(self._elementos_cartaz(mapa, horarios, titulo_str, estilos,
                                                 nota_rodape=nota,
                                                 colunas_negrito=colunas_negrito))
            os.startfile(caminho)

        except Exception as e:
            logger.exception("Erro ao gerar PDF da turma")
            messagebox.showerror("Erro", f"Erro ao gerar PDF:\n{str(e)}")

    def _gerar_pdf_alunos(self, caminho, mapa, horarios_lista, titulo_str, estilos,
                          colunas_negrito=None):
        """Gera PDF com 3 páginas idênticas do horário (mesmo layout do cartaz).
        Ao imprimir, selecionar '3 páginas por folha' para obter 3 cópias recortáveis por A4.
        """
        nota = f"Ano Letivo 2026  ·  Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        doc = create_pdf_doc(caminho, pagesize=landscape(A4))
        elementos = []
        for i in range(3):
            if i > 0:
                elementos.append(PageBreak())
            elementos += self._elementos_cartaz(mapa, horarios_lista, titulo_str, estilos,
                                                nota_rodape=nota,
                                                colunas_negrito=colunas_negrito)
        doc.build(elementos)

    def gerar_pdf_todas_turmas(self):
        """Gera PDF com cartaz de horários das turmas do mesmo nível da turma selecionada.
        Uma página por turma, em A4 paisagem — para uso da coordenação/gestão.
        """
        # Descobrir nivel_id da série selecionada
        serie_nome_sel = self.serie_var.get() if hasattr(self, 'serie_var') else ""
        nivel_id_sel = None
        for s in (self.series_dados or []):
            if s['nome'] == serie_nome_sel:
                nivel_id_sel = s.get('nivel_id')
                break

        try:
            conn = conectar_bd()
            if not conn:
                messagebox.showerror("Erro", "Falha ao conectar ao banco de dados.")
                return
            cursor = conn.cursor(dictionary=True)

            if nivel_id_sel:
                cursor.execute("""
                    SELECT t.id, t.nome, t.turno, s.nome AS serie_nome, s.nivel_id
                    FROM turmas t
                    INNER JOIN series s ON t.serie_id = s.id
                    INNER JOIN anosletivos al ON t.ano_letivo_id = al.id
                    WHERE t.escola_id = 60 AND al.ano_letivo = 2026
                      AND s.nivel_id = %s
                    ORDER BY s.nome, t.nome
                """, (nivel_id_sel,))
            else:
                cursor.execute("""
                    SELECT t.id, t.nome, t.turno, s.nome AS serie_nome, s.nivel_id
                    FROM turmas t
                    INNER JOIN series s ON t.serie_id = s.id
                    INNER JOIN anosletivos al ON t.ano_letivo_id = al.id
                    WHERE t.escola_id = 60 AND al.ano_letivo = 2026
                    ORDER BY s.nivel_id, s.nome, t.nome
                """)
            turmas = cursor.fetchall()
            cursor.close()
            conn.close()

            if not turmas:
                messagebox.showwarning("Atenção", "Nenhuma turma encontrada para 2026.")
                return

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            caminho = temp_file.name
            temp_file.close()

            estilos = getSampleStyleSheet()
            doc = create_pdf_doc(caminho, pagesize=landscape(A4))
            elementos = []
            data_geracao = datetime.now().strftime('%d/%m/%Y')

            # Mapeamento turno banco → label legível e lista de horários
            _turno_map = {
                'MAT':  ('Matutino',   self.horarios_matutino),
                'VESP': ('Vespertino', self.horarios_vespertino),
                # fallback para valores já legíveis (caso algum registro use o nome completo)
                'Matutino':   ('Matutino',   self.horarios_matutino),
                'Vespertino': ('Vespertino', self.horarios_vespertino),
            }

            for idx, turma in enumerate(turmas):
                if idx > 0:
                    elementos.append(PageBreak())

                turno_raw = (turma.get('turno') or 'MAT').strip()
                turno_label, horarios_lista = _turno_map.get(
                    turno_raw, ('Matutino', self.horarios_matutino)
                )

                turma_nome = (turma['nome'] or '').strip()
                serie_nome = turma.get('serie_nome', '')
                turma_display = f"{serie_nome} {turma_nome}".strip() if turma_nome else serie_nome
                titulo_str = f"Horário de Aulas — {turma_display} — {turno_label}"

                mapa, _ = self._buscar_mapa_horarios(turma['id'], horarios_lista)

                # Fundamental I (nivel_id=2, 1º-5º ano): negrito na coluna Ensino Religioso
                if turma.get('nivel_id') == 2:
                    colunas_negrito = sorted({
                        col for (_, col), d in mapa.items()
                        if 'ENSINO RELIGIOSO' in (d.get('valor') or '').upper()
                    })
                else:
                    colunas_negrito = None

                nota = (f"Turma {idx + 1} de {len(turmas)}  ·  "
                        f"Ano Letivo 2026  ·  Gerado em {data_geracao}")
                elementos += self._elementos_cartaz(
                    mapa, horarios_lista, titulo_str, estilos, nota_rodape=nota,
                    colunas_negrito=colunas_negrito,
                )

            doc.build(elementos)
            os.startfile(caminho)

        except Exception as e:
            logger.exception("Erro ao gerar PDF de todas as turmas")
            messagebox.showerror("Erro", f"Erro ao gerar PDF:\n{str(e)}")

    def gerar_pdf_professor(self):
        """Gera PDF com horário de um professor específico"""
        try:
            # Criar arquivo temporário
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            caminho = temp_file.name
            temp_file.close()
            # Criar janela para selecionar professor
            janela_prof = tk.Toplevel(self.janela)
            janela_prof.title("Selecionar Professor")
            janela_prof.geometry("400x200")
            janela_prof.transient(self.janela)
            janela_prof.grab_set()
            janela_prof.configure(bg=self.co0)
            
            # Centralizar
            janela_prof.update_idletasks()
            x = (janela_prof.winfo_screenwidth() // 2) - 200
            y = (janela_prof.winfo_screenheight() // 2) - 100
            janela_prof.geometry(f'400x200+{x}+{y}')
            
            tk.Label(janela_prof, text="Selecione o Professor:", 
                    font=("Arial", 12, "bold"), bg=self.co0).pack(pady=(20, 10))
            
            # ComboBox de professores
            professor_var = tk.StringVar()
            professor_cb = ttk.Combobox(janela_prof, textvariable=professor_var, 
                                       width=40, state="readonly")
            professor_cb.pack(pady=10)
            
            # Buscar professores do banco
            conn = conectar_bd()
            cursor = conn.cursor(dictionary=True)
            
            # Verificar se a coluna data_saida existe
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'funcionarios' 
                AND COLUMN_NAME = 'data_saida'
            """)
            has_data_saida = cursor.fetchone()['COUNT(*)'] > 0
            
            # Construir query baseado na existência da coluna
            if has_data_saida:
                query = """
                    SELECT DISTINCT f.id, f.nome 
                    FROM funcionarios f
                    INNER JOIN horarios_importados h ON f.id = h.professor_id
                    WHERE f.escola_id = 60
                    AND h.ano_letivo = 2026
                    AND (f.data_saida IS NULL OR f.data_saida = '')
                    ORDER BY f.nome
                """
            else:
                query = """
                    SELECT DISTINCT f.id, f.nome 
                    FROM funcionarios f
                    INNER JOIN horarios_importados h ON f.id = h.professor_id
                    WHERE f.escola_id = 60
                    AND h.ano_letivo = 2026
                    ORDER BY f.nome
                """
            
            cursor.execute(query)
            professores = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not professores:
                messagebox.showwarning("Atenção", "Nenhum professor encontrado com horários cadastrados.")
                janela_prof.destroy()
                return
            
            # Mapear nomes para IDs
            prof_map = {prof['nome']: prof['id'] for prof in professores}
            professor_cb['values'] = list(prof_map.keys())
            professor_cb.current(0)
            
            professor_selecionado = {'id': None, 'nome': None}
            
            def confirmar():
                nome = professor_var.get()
                if nome:
                    professor_selecionado['id'] = prof_map[nome]
                    professor_selecionado['nome'] = nome
                    janela_prof.destroy()
            
            def cancelar():
                janela_prof.destroy()
            
            # Botões
            frame_botoes = tk.Frame(janela_prof, bg=self.co0)
            frame_botoes.pack(pady=20)
            
            ttk.Button(frame_botoes, text="Cancelar", 
                      command=cancelar).pack(side=tk.LEFT, padx=5)
            ttk.Button(frame_botoes, text="Confirmar", 
                      command=confirmar).pack(side=tk.RIGHT, padx=5)
            
            # Aguardar fechamento da janela
            self.janela.wait_window(janela_prof)
            
            if not professor_selecionado['id']:
                return
            
            # Buscar horários do professor (já filtrado na seleção, mas garantir)
            conn = conectar_bd()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT DISTINCT h.dia, h.horario, h.valor, t.nome as turma_nome, s.nome as serie_nome,
                       dh.nome as disciplina_nome
                FROM horarios_importados h
                LEFT JOIN turmas t ON h.turma_id = t.id
                LEFT JOIN series s ON t.serie_id = s.id
                INNER JOIN disciplinas dh ON h.disciplina_id = dh.id
                INNER JOIN disciplinas dfd ON dfd.nome = dh.nome
                INNER JOIN funcionario_disciplinas fd
                    ON fd.disciplina_id = dfd.id
                    AND (fd.turma_id = h.turma_id OR fd.turma_id IS NULL)
                WHERE fd.funcionario_id = %s AND h.ano_letivo = 2026
                ORDER BY h.dia, h.horario
            """, (professor_selecionado['id'],))
            horarios_prof = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not horarios_prof:
                messagebox.showwarning("Atenção", 
                    f"Nenhum horário encontrado para o professor {professor_selecionado['nome']}.")
                return
            
            # Determinar turno predominante (matutino ou vespertino)
            horarios_matutino_count = sum(1 for h in horarios_prof if h['horario'] in self.horarios_matutino)
            horarios_vespertino_count = sum(1 for h in horarios_prof if h['horario'] in self.horarios_vespertino)
            
            if horarios_vespertino_count > horarios_matutino_count:
                horarios_lista = self.horarios_vespertino
                turno = "Vespertino"
            else:
                horarios_lista = self.horarios_matutino
                turno = "Matutino"
            
            # Criar documento PDF em modo paisagem
            doc = create_pdf_doc(caminho, pagesize=landscape(A4))
            elementos = []
            
            # Estilos
            estilos = getSampleStyleSheet()
            titulo_estilo = estilos['Heading1']
            
            # Título
            elementos.append(Paragraph(
                f"Horário de Aulas - Professor(a): {professor_selecionado['nome']}", 
                titulo_estilo))
            elementos.append(Spacer(1, 12))
            
            # Criar tabela de dados
            dados = [["Horário"] + self.dias_semana]
            
            # Mapear horários para grid
            mapa_horarios = {}
            for item in horarios_prof:
                dia = item['dia']
                horario = item['horario']
                
                # Localizar coluna pelo dia
                try:
                    col = self.dias_semana.index(dia)
                except ValueError:
                    continue
                
                # Localizar linha pelo horário
                row_index = None
                if horario in horarios_lista:
                    row_index = horarios_lista.index(horario)
                elif isinstance(horario, str) and horario.startswith('Linha '):
                    try:
                        num = int(horario.split()[1])
                        row_index = num - 1
                    except:
                        continue
                
                if row_index is not None:
                    # Montar texto da célula
                    turma_nome = item.get('turma_nome') or ''
                    serie_nome = item.get('serie_nome') or ''
                    disciplina = item.get('disciplina_nome') or item.get('valor') or ''
                    
                    # Formato: SÉRIE - TURMA\nDISCIPLINA
                    if turma_nome:
                        texto = f"{serie_nome} - {turma_nome}\n{disciplina}"
                    else:
                        texto = f"{serie_nome}\n{disciplina}"
                    
                    mapa_horarios[(row_index, col)] = texto
            
            # Preencher dados da tabela
            for i, horario in enumerate(horarios_lista):
                linha = [horario]
                
                for j in range(len(self.dias_semana)):
                    texto = mapa_horarios.get((i, j), "")
                    linha.append(texto)
                
                dados.append(linha)
            
            # Criar tabela com larguras ajustadas
            largura_col_horario = 70
            largura_col_dia = (landscape(A4)[0] - largura_col_horario - 40) / len(self.dias_semana)
            col_widths = [largura_col_horario] + [largura_col_dia] * len(self.dias_semana)
            
            tabela = Table(dados, colWidths=col_widths)
            
            # Estilo base da tabela
            estilo_tabela = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),  # Cabeçalho azul escuro
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Texto branco no cabeçalho
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#BDC3C7')),  # Coluna de horários cinza
                ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Bordas
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Centralizar todo o texto
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Centralizar verticalmente
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Negrito no cabeçalho
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),  # Negrito na coluna de horários
                ('FONTSIZE', (0, 0), (-1, -1), 8),  # Tamanho da fonte
            ])
            
            # Colorir células com aulas (azul claro)
            for i in range(len(horarios_lista)):
                for j in range(len(self.dias_semana)):
                    if mapa_horarios.get((i, j)):
                        estilo_tabela.add('BACKGROUND', (j+1, i+1), (j+1, i+1), 
                                        colors.Color(0.8, 0.9, 1.0))
            
            # Estilo específico para linha de intervalo (linha 4)
            linha_intervalo = 3  # Índice 3 = linha 4
            if linha_intervalo < len(horarios_lista):
                estilo_tabela.add('BACKGROUND', (1, linha_intervalo+1), (-1, linha_intervalo+1), 
                                colors.HexColor('#F39C12'))
                estilo_tabela.add('TEXTCOLOR', (1, linha_intervalo+1), (-1, linha_intervalo+1), 
                                colors.white)
                estilo_tabela.add('FONTNAME', (1, linha_intervalo+1), (-1, linha_intervalo+1), 
                                'Helvetica-Bold')
            
            tabela.setStyle(estilo_tabela)
            elementos.append(tabela)
            
            # Adicionar informações adicionais
            elementos.append(Spacer(1, 20))
            total_aulas = len(horarios_prof)
            elementos.append(Paragraph(
                f"<b>Total de aulas semanais:</b> {total_aulas} | <b>Turno:</b> {turno}", 
                estilos['Normal']))
            
            # Construir PDF
            doc.build(elementos)
            
            # Abrir PDF automaticamente
            try:
                os.startfile(caminho)
            except AttributeError:
                # Em sistemas não-Windows
                import subprocess
                subprocess.run(['xdg-open', caminho])
            
        except Exception as e:
            logger.exception("Erro ao gerar PDF do professor")
            messagebox.showerror("Erro", f"Erro ao gerar PDF:\n{str(e)}")
    
    def exportar_excel(self):
        # Verificar se uma turma está selecionada
        if self.turma_atual is None:
            messagebox.showwarning("Atenção", "Selecione uma turma antes de exportar.")
            return
            
        # Escolher lista de horários com base no turno
        horarios = self.horarios_matutino if self.turno_atual == "Matutino" else self.horarios_vespertino
        
        # Criar dataframe para exportação
        dados = []
        
        for i, horario in enumerate(horarios):
            linha = [horario]
            
            for j, _ in enumerate(self.dias_semana):
                celula = self.celulas_horario.get((i+1, j+1))
                if celula:
                    linha.append(celula.get())
                else:
                    linha.append("")
            
            dados.append(linha)
        
        # Criar DataFrame
        df = pd.DataFrame(dados, columns=["Horário"] + self.dias_semana)
        
        # Solicitar local para salvar
        caminho = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Exportar Horário para Excel"
        )
        
        if not caminho:
            return
            
        # Exportar para Excel
        df.to_excel(caminho, sheet_name=f"{self.turma_atual}", index=False)
        messagebox.showinfo("Sucesso", f"Horário da {self.turma_atual} exportado para Excel!")
    
    def limpar_horarios(self):
        # Verificar se uma turma está selecionada
        if not self.turma_atual:
            messagebox.showwarning("Atenção", "Selecione uma turma antes de limpar.")
            return
            
        # Confirmar ação
        confirmacao = messagebox.askyesno("Confirmar", 
                                        f"Tem certeza que deseja limpar o horário da {self.turma_atual}?")
        if not confirmacao:
            return
            
        # Limpar células
        for celula in self.celulas_horario.values():
            celula.set('')  # Combobox usa set() para definir valor
    
    def ao_fechar_janela(self):
        # Perguntar se deseja salvar alterações
        if self.turma_atual:
            resposta = messagebox.askyesnocancel("Salvar Alterações", 
                                               "Deseja salvar as alterações antes de fechar?")
            if resposta is None:  # Cancelar
                return
            elif resposta:  # Yes
                self.salvar_horarios()
        
        # Se a janela principal foi fornecida, mostrá-la novamente
        if self.janela_principal:
            self.janela_principal.deiconify()
        
        # Fechar esta janela
        self.janela.destroy()

    def importar_geduc(self):
        """Importa horários do GEDUC para a turma selecionada"""
        try:
            # Verificar se turma está selecionada (verificar apenas ID pois nome pode ser vazio)
            if not self.turma_id:
                messagebox.showwarning("Atenção", "Selecione uma turma antes de importar do GEDUC.")
                return
            
            # Importar módulos necessários
            import threading
            from src.importadores.geduc import AutomacaoGEDUC
            from src.core import config
            
            # Solicitar credenciais
            credenciais = self._solicitar_credenciais_geduc()
            if not credenciais:
                return
            
            # Construir nome para busca no GEDUC
            serie_nome = self.serie_var.get()
            turma_completa = self.turma_var.get()
            
            # Log para debug
            logger.info(f"DEBUG: serie_nome = '{serie_nome}'")
            logger.info(f"DEBUG: turma_completa = '{turma_completa}'")
            logger.info(f"DEBUG: turma_id = {self.turma_id}")
            
            # Buscar turno diretamente do banco de dados
            turno_bd = ""
            try:
                conn = conectar_bd()
                cursor = conn.cursor()
                cursor.execute("SELECT turno FROM turmas WHERE id = %s", (self.turma_id,))
                resultado = cursor.fetchone()
                if resultado:
                    turno_bd = resultado[0] if resultado[0] else ""
                    logger.info(f"DEBUG: turno do BD = '{turno_bd}'")
                cursor.close()
                conn.close()
            except Exception as e:
                logger.warning(f"Erro ao buscar turno: {e}")
            
            # Extrair apenas a letra da turma (A, B, C, etc)
            # Remove "Turma", nome da série e espaços extras
            turma_letra = ""
            if turma_completa and turma_completa.strip():
                # Remover "Turma " do início
                temp = turma_completa.replace("Turma ", "").strip()
                # Remover o nome da série
                temp = temp.replace(serie_nome, "").strip()
                # O que sobrar deve ser apenas a letra (A, B, C) ou vazio
                if temp and len(temp) <= 3:  # Letras geralmente têm 1-3 caracteres
                    turma_letra = temp.upper()
                logger.info(f"DEBUG: turma_letra extraída = '{turma_letra}'")
            
            # Construir nome no formato do GEDUC
            # Formato: "{SERIE}-{TURNO}" ou "{SERIE}-{TURNO} - {LETRA}"
            # Exemplos:
            # - Sem letra: "1º ANO-MATU"
            # - Com letra: "6º ANO-VESP - A"
            
            # Converter turno para abreviação
            turno_abrev = ""
            if turno_bd:
                if "MAT" in turno_bd.upper():
                    turno_abrev = "MATU"
                elif "VESP" in turno_bd.upper():
                    turno_abrev = "VESP"
                elif "NOT" in turno_bd.upper():
                    turno_abrev = "NOTU"
                else:
                    turno_abrev = turno_bd[:4].upper()
                logger.info(f"DEBUG: turno_abrev = '{turno_abrev}'")
            
            # Construir nome: {SERIE}-{TURNO}
            serie_upper = serie_nome.upper()
            if turno_abrev:
                nome_busca_geduc = f"{serie_upper}-{turno_abrev}"
            else:
                nome_busca_geduc = serie_upper
            
            # Adicionar letra se houver: {SERIE}-{TURNO} - {LETRA}
            if turma_letra:
                nome_busca_geduc = f"{nome_busca_geduc} - {turma_letra}"
            
            logger.info(f"DEBUG: nome_busca_geduc final = '{nome_busca_geduc}'")


            
            # Criar janela de progresso
            janela_progresso = tk.Toplevel(self.janela)
            janela_progresso.title("Importando do GEDUC")
            janela_progresso.geometry("500x300")
            janela_progresso.transient(self.janela)
            janela_progresso.grab_set()
            janela_progresso.configure(bg=self.co0)
            
            # Centralizar
            janela_progresso.update_idletasks()
            x = (janela_progresso.winfo_screenwidth() // 2) - 250
            y = (janela_progresso.winfo_screenheight() // 2) - 150
            janela_progresso.geometry(f'500x300+{x}+{y}')
            
            # Texto de progresso
            texto_progresso = tk.Text(janela_progresso, height=15, width=60, bg=self.co0)
            texto_progresso.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Barra de progresso
            barra = ttk.Progressbar(janela_progresso, mode='indeterminate')
            barra.pack(fill=tk.X, padx=10, pady=5)
            barra.start()
            
            def adicionar_log(msg):
                texto_progresso.insert(tk.END, msg + "\n")
                texto_progresso.see(tk.END)
                texto_progresso.update()
            
            def executar_importacao():
                automacao = None
                try:
                    adicionar_log("🌐 Iniciando importação do GEDUC...")
                    adicionar_log(f"📚 Turma: {nome_busca_geduc}")
                    adicionar_log("")
                    
                    # Inicializar automação
                    adicionar_log("→ Iniciando navegador...")
                    automacao = AutomacaoGEDUC(headless=False)
                    
                    if not automacao.iniciar_navegador():
                        adicionar_log("✗ Erro ao iniciar navegador")
                        messagebox.showerror("Erro", "Não foi possível iniciar o navegador.", parent=janela_progresso)
                        return
                    
                    adicionar_log("✓ Navegador iniciado")
                    adicionar_log("")
                    
                    # Fazer login
                    adicionar_log("→ Fazendo login...")
                    adicionar_log("  ⚠️ Resolva o reCAPTCHA manualmente no navegador!")
                    
                    if not automacao.fazer_login(credenciais['usuario'], credenciais['senha'], timeout_recaptcha=120):
                        adicionar_log("✗ Erro no login")
                        messagebox.showerror("Erro", "Não foi possível fazer login no GEDUC.", parent=janela_progresso)
                        return
                    
                    adicionar_log("✓ Login realizado com sucesso")
                    adicionar_log("")
                    
                    # Mudar ano letivo
                    ano_letivo = credenciais.get('ano_letivo', 2025)
                    adicionar_log(f"→ Mudando para ano letivo {ano_letivo}...")
                    
                    if not automacao.mudar_ano_letivo(ano_letivo):
                        adicionar_log(f"⚠️ Não foi possível mudar para {ano_letivo}, continuando...")
                    else:
                        adicionar_log(f"✓ Ano letivo alterado para {ano_letivo}")
                    
                    adicionar_log("")
                    
                    # Extrair horários
                    adicionar_log(f"→ Buscando horários da turma '{nome_busca_geduc}'...")
                    dados_horario = automacao.extrair_horario_turma(nome_busca_geduc)
                    
                    if not dados_horario:
                        adicionar_log("✗ Não foi possível extrair horários")
                        messagebox.showwarning("Atenção", f"Turma '{nome_busca_geduc}' não encontrada no GEDUC.", parent=janela_progresso)
                        return
                    
                    adicionar_log(f"✓ Extraídos {len(dados_horario.get('horarios', []))} horários")
                    adicionar_log("")
                    
                    # Salvar no banco de dados
                    adicionar_log("→ Salvando no banco de dados...")
                    sucesso = self._salvar_horarios_geduc_bd(dados_horario, adicionar_log)
                    
                    if sucesso:
                        adicionar_log("")
                        adicionar_log("="*50)
                        adicionar_log("✓ IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
                        adicionar_log("="*50)
                        
                        # Recarregar horários na interface
                        self.janela.after(0, self.carregar_horarios)
                        
                        messagebox.showinfo("Sucesso", 
                            f"Horários importados com sucesso!\n\n"
                            f"Total: {len(dados_horario.get('horarios', []))} horários", 
                            parent=janela_progresso)
                    else:
                        adicionar_log("✗ Erro ao salvar no banco de dados")
                        messagebox.showerror("Erro", "Erro ao salvar horários no banco de dados.", parent=janela_progresso)
                    
                except Exception as e:
                    adicionar_log(f"\n✗ ERRO: {e}")
                    logger.exception("Erro na importação do GEDUC")
                    messagebox.showerror("Erro", f"Erro durante importação:\n{str(e)}", parent=janela_progresso)
                
                finally:
                    if automacao:
                        adicionar_log("\n→ Fechando navegador...")
                        automacao.fechar()
                    
                    # Verificar se a janela ainda existe antes de parar o progressbar
                    try:
                        if janela_progresso.winfo_exists():
                            barra.stop()
                    except:
                        pass
            
            # Executar em thread
            thread = threading.Thread(target=executar_importacao, daemon=True)
            thread.start()
            
        except Exception as e:
            logger.exception("Erro ao importar do GEDUC")
            messagebox.showerror("Erro", f"Erro ao iniciar importação:\n{str(e)}")
    
    def _solicitar_credenciais_geduc(self):
        """Solicita credenciais do GEDUC ao usuário"""
        from src.core import config
        
        janela_cred = tk.Toplevel(self.janela)
        janela_cred.title("Credenciais GEDUC")
        janela_cred.geometry("400x270")
        janela_cred.resizable(False, False)
        janela_cred.grab_set()
        janela_cred.configure(bg=self.co0)
        
        # Centralizar
        janela_cred.update_idletasks()
        x = (janela_cred.winfo_screenwidth() // 2) - 200
        y = (janela_cred.winfo_screenheight() // 2) - 135
        janela_cred.geometry(f'400x270+{x}+{y}')
        
        # Variáveis
        usuario_var = tk.StringVar(value=getattr(config, 'GEDUC_DEFAULT_USER', ''))
        senha_var = tk.StringVar(value=getattr(config, 'GEDUC_DEFAULT_PASS', ''))
        ano_var = tk.StringVar(value='2025')  # Ano padrão
        resultado = {'credenciais': None}
        
        # Campos
        tk.Label(janela_cred, text="Usuário GEDUC:", bg=self.co0, font=("Arial", 10)).pack(pady=(20, 5))
        entry_usuario = tk.Entry(janela_cred, textvariable=usuario_var, width=30, font=("Arial", 10))
        entry_usuario.pack(pady=5)
        
        tk.Label(janela_cred, text="Senha:", bg=self.co0, font=("Arial", 10)).pack(pady=(10, 5))
        entry_senha = tk.Entry(janela_cred, textvariable=senha_var, show="*", width=30, font=("Arial", 10))
        entry_senha.pack(pady=5)
        
        tk.Label(janela_cred, text="Ano Letivo:", bg=self.co0, font=("Arial", 10)).pack(pady=(10, 5))
        frame_ano = tk.Frame(janela_cred, bg=self.co0)
        frame_ano.pack(pady=5)
        
        anos_disponiveis = ['2024', '2025', '2026']
        ano_cb = ttk.Combobox(frame_ano, textvariable=ano_var, values=anos_disponiveis, 
                              width=28, state="readonly", font=("Arial", 10))
        ano_cb.pack()
        
        def confirmar():
            if not usuario_var.get() or not senha_var.get():
                messagebox.showwarning("Atenção", "Preencha usuário e senha!", parent=janela_cred)
                return
            
            resultado['credenciais'] = {
                'usuario': usuario_var.get(),
                'senha': senha_var.get(),
                'ano_letivo': int(ano_var.get())
            }
            janela_cred.destroy()
        
        def cancelar():
            janela_cred.destroy()
        
        # Botões
        frame_botoes = tk.Frame(janela_cred, bg=self.co0)
        frame_botoes.pack(pady=15)
        
        ttk.Button(frame_botoes, text="Confirmar", command=confirmar).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botoes, text="Cancelar", command=cancelar).pack(side=tk.LEFT, padx=5)
        
        # Enter para confirmar
        entry_senha.bind('<Return>', lambda e: confirmar())
        
        # Aguardar janela fechar
        janela_cred.wait_window()
        
        return resultado['credenciais']
        janela_cred.grab_set()
        janela_cred.configure(bg=self.co0)
        
        # Centralizar
        janela_cred.update_idletasks()
        x = (janela_cred.winfo_screenwidth() // 2) - 200
        y = (janela_cred.winfo_screenheight() // 2) - 100
        janela_cred.geometry(f'400x200+{x}+{y}')
        
        # Variáveis
        usuario_var = tk.StringVar(value=getattr(config, 'GEDUC_DEFAULT_USER', ''))
        senha_var = tk.StringVar(value=getattr(config, 'GEDUC_DEFAULT_PASS', ''))
        resultado = {'credenciais': None}
        
        # Campos
        tk.Label(janela_cred, text="Usuário GEDUC:", bg=self.co0, font=("Arial", 10)).pack(pady=(20, 5))
        entry_usuario = tk.Entry(janela_cred, textvariable=usuario_var, width=30, font=("Arial", 10))
        entry_usuario.pack(pady=5)
        
        tk.Label(janela_cred, text="Senha:", bg=self.co0, font=("Arial", 10)).pack(pady=(10, 5))
        entry_senha = tk.Entry(janela_cred, textvariable=senha_var, show="*", width=30, font=("Arial", 10))
        entry_senha.pack(pady=5)
        
        def confirmar():
            if not usuario_var.get() or not senha_var.get():
                messagebox.showwarning("Atenção", "Preencha usuário e senha!", parent=janela_cred)
                return
            
            resultado['credenciais'] = {
                'usuario': usuario_var.get(),
                'senha': senha_var.get()
            }
            janela_cred.destroy()
        
        def cancelar():
            janela_cred.destroy()
        
        # Botões
        frame_botoes = tk.Frame(janela_cred, bg=self.co0)
        frame_botoes.pack(pady=20)
        
        ttk.Button(frame_botoes, text="Confirmar", command=confirmar).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botoes, text="Cancelar", command=cancelar).pack(side=tk.LEFT, padx=5)
        
        # Enter para confirmar
        entry_senha.bind('<Return>', lambda e: confirmar())
        
        # Aguardar janela fechar
        janela_cred.wait_window()
        
        return resultado['credenciais']
    
    def _garantir_tabela_horarios(self):
        """Garante que a tabela horarios_importados existe no banco de dados"""
        try:
            conn = conectar_bd()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Criar tabela se não existir
            sql = """
            CREATE TABLE IF NOT EXISTS horarios_importados (
              id INT AUTO_INCREMENT PRIMARY KEY,
              turma_id INT NOT NULL,
              dia VARCHAR(32) NOT NULL,
              horario VARCHAR(32) NOT NULL,
              valor TEXT NOT NULL,
              disciplina_id INT NULL,
              professor_id INT NULL,
              geduc_turma_id INT NULL,
              ano_letivo INT NOT NULL DEFAULT 2026,
              UNIQUE KEY ux_horario_turma (turma_id, dia, horario, ano_letivo)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(sql)
            
            # Adicionar coluna ano_letivo se não existir (para tabelas antigas)
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'horarios_importados' 
                    AND COLUMN_NAME = 'ano_letivo'
                """)
                
                if cursor.fetchone()[0] == 0:
                    logger.info("Adicionando coluna ano_letivo à tabela horarios_importados...")
                    cursor.execute("""
                        ALTER TABLE horarios_importados 
                        ADD COLUMN ano_letivo INT NOT NULL DEFAULT 2026
                    """)
                    
                    # Atualizar horários existentes para serem de 2025
                    cursor.execute("""
                        UPDATE horarios_importados 
                        SET ano_letivo = 2025 
                        WHERE ano_letivo = 2026
                    """)
                    
                    # Recriar índice único incluindo ano_letivo
                    cursor.execute("DROP INDEX ux_horario_turma ON horarios_importados")
                    cursor.execute("""
                        CREATE UNIQUE INDEX ux_horario_turma 
                        ON horarios_importados(turma_id, dia, horario, ano_letivo)
                    """)
                    
                    logger.info("Coluna ano_letivo adicionada e horários antigos marcados como 2025")
            except Exception as e:
                logger.warning(f"Aviso ao adicionar coluna ano_letivo: {e}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("Tabela horarios_importados verificada/criada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar tabela horarios_importados: {e}")
            return False
    
    def _salvar_horarios_geduc_bd(self, dados_horario, log_callback=None):
        """Salva horários extraídos do GEDUC no banco de dados"""
        try:
            # Garantir que a tabela existe antes de tentar salvar
            if not self._garantir_tabela_horarios():
                if log_callback:
                    log_callback("  ✗ Erro ao verificar/criar tabela no banco de dados")
                return False
            
            if log_callback:
                log_callback("  ✓ Tabela horarios_importados verificada")
            
            conn = conectar_bd()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            horarios = dados_horario.get('horarios', [])
            turma_id_geduc = dados_horario.get('turma_id')
            
            if log_callback:
                log_callback(f"  → Processando {len(horarios)} horários...")
            
            # Buscar nivel_id da turma para filtrar disciplinas corretas
            nivel_id = None
            escola_id = 60  # ID da escola
            
            cursor.execute("""
                SELECT s.nivel_id 
                FROM turmas t
                JOIN series s ON t.serie_id = s.id
                WHERE t.id = %s
            """, (self.turma_id,))
            resultado_nivel = cursor.fetchone()
            if resultado_nivel:
                nivel_id = resultado_nivel[0]
            
            salvos = 0
            
            for horario in horarios:
                dia = horario['dia']
                hora = horario['horario']
                disciplina_nome = horario['disciplina']
                professor_nome = horario.get('professor')
                
                # Ajustar linha para o intervalo (linha 4 é intervalo)
                # GEDUC Linha 1-3 → Local Linha 1-3
                # GEDUC Linha 4+ → Local Linha 5+ (pula linha 4 que é intervalo)
                if hora.startswith('Linha '):
                    try:
                        num_linha = int(hora.split()[1])
                        if num_linha >= 4:
                            # Desloca linhas 4, 5, 6... para 5, 6, 7...
                            num_linha += 1
                        hora = f'Linha {num_linha}'
                    except:
                        pass  # Se não conseguir converter, mantém original
                
                # Buscar ID da disciplina com escola_id e nivel_id corretos
                disciplina_id = None
                if nivel_id:
                    cursor.execute(
                        "SELECT id FROM disciplinas WHERE nome LIKE %s AND escola_id = %s AND nivel_id = %s LIMIT 1", 
                        (f"%{disciplina_nome}%", escola_id, nivel_id)
                    )
                else:
                    cursor.execute(
                        "SELECT id FROM disciplinas WHERE nome LIKE %s AND escola_id = %s LIMIT 1", 
                        (f"%{disciplina_nome}%", escola_id)
                    )
                resultado_disc = cursor.fetchone()
                if resultado_disc:
                    disciplina_id = resultado_disc[0]
                
                # Buscar ID do professor (funcionario_id) da tabela funcionario_disciplinas
                # baseado na disciplina_id e turma_id
                professor_id = None
                if disciplina_id:
                    cursor.execute(
                        "SELECT funcionario_id FROM funcionario_disciplinas WHERE disciplina_id = %s AND turma_id = %s LIMIT 1", 
                        (disciplina_id, self.turma_id)
                    )
                    resultado_prof = cursor.fetchone()
                    if resultado_prof:
                        professor_id = resultado_prof[0]
                
                # Valor combinado para exibição
                valor = disciplina_nome
                if professor_nome:
                    valor = f"{disciplina_nome}\n{professor_nome}"
                
                # Inserir ou atualizar horário
                sql = """
                    INSERT INTO horarios_importados 
                    (turma_id, dia, horario, valor, disciplina_id, professor_id, geduc_turma_id, ano_letivo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 2026)
                    ON DUPLICATE KEY UPDATE
                    valor = VALUES(valor),
                    disciplina_id = VALUES(disciplina_id),
                    professor_id = VALUES(professor_id),
                    geduc_turma_id = VALUES(geduc_turma_id)
                """
                
                cursor.execute(sql, (
                    self.turma_id,
                    dia,
                    hora,
                    valor,
                    disciplina_id,
                    professor_id,
                    turma_id_geduc
                ))
                
                salvos += 1
            
            conn.commit()
            
            if log_callback:
                log_callback(f"  ✓ {salvos} horários salvos no banco de dados")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.exception("Erro ao salvar horários no BD")
            if log_callback:
                log_callback(f"  ✗ Erro: {str(e)}")
            return False


# Se o arquivo for executado diretamente
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal se executado diretamente
    app = InterfaceHorariosEscolares(janela_principal=root)
    root.mainloop() 