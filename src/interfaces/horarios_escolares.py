from src.core.config_logs import get_logger
logger = get_logger(__name__)
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from datetime import datetime
import mysql.connector
from src.core.conexao import conectar_bd
from PIL import ImageTk, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

class InterfaceHorariosEscolares:
    def __init__(self, root=None, janela_principal=None):
        # Armazenar referência à janela principal
        self.janela_principal = janela_principal
        
        # Se root for None, cria uma nova janela
        if root is None:
            self.janela = tk.Toplevel(self.janela_principal)  # Passando o pai corretamente
            self.janela.title("Gerenciamento de Horários Escolares")
            self.janela.geometry("1200x700")
            
            # Garantir que a janela principal existe antes de chamar grab_set
            if self.janela_principal:
                self.janela.transient(self.janela_principal)  # Define a janela principal como proprietária
                self.janela.grab_set()  # Torna a janela modal
                
            self.janela.focus_force()
            
            # Configurar evento de fechamento
            self.janela.protocol("WM_DELETE_WINDOW", self.ao_fechar_janela)
        else:
            self.janela = root

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
        self.criar_interface()
    
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
                    SELECT id, nome FROM series 
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
                    cursor.execute("SELECT id, nome FROM series WHERE id IN (3, 4, 5, 6, 7, 8, 9, 10, 11) ORDER BY id")
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
                cursor.execute("""
                    SELECT id, nome, cargo, polivalente FROM funcionarios 
                    WHERE cargo IN ('Professor@', 'Especialista (Coordenadora)')
                    AND escola_id = 60
                    ORDER BY nome
                """)
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
    
    def criar_interface(self):
        # Criar frames principais
        self.criar_frames()
        
        # Criar título da janela
        self.criar_cabecalho("Gerenciamento de Horários Escolares")
        
        # Criar área de seleção
        self.criar_area_selecao()
        
        # Criar grade de horários
        self.criar_grade_horarios()
        
        # Criar barra de botões
        self.criar_barra_botoes()
    
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
            
        # Título centralizado
        label_titulo = tk.Label(
            self.frame_titulo, 
            text=texto, 
            font=("Arial", 14, "bold"), 
            bg=self.co1, 
            fg=self.co0
        )
        label_titulo.pack(expand=True, fill="both", padx=10, pady=15)
    
    def criar_area_selecao(self):
        # Limpar widgets existentes
        for widget in self.frame_selecao.winfo_children():
            widget.destroy()
        
        # Frame para turno
        frame_turno = tk.Frame(self.frame_selecao, bg=self.co0)
        frame_turno.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(frame_turno, text="Turno:", bg=self.co0, font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.turno_var = tk.StringVar(value=self.turno_atual)
        turno_cb = ttk.Combobox(frame_turno, textvariable=self.turno_var, values=["Matutino", "Vespertino"], width=15, state="readonly")
        turno_cb.pack(side=tk.LEFT)
        turno_cb.bind("<<ComboboxSelected>>", self.atualizar_horarios)
        
        # Frame para série/ano
        frame_serie = tk.Frame(self.frame_selecao, bg=self.co0)
        frame_serie.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(frame_serie, text="Série/Ano:", bg=self.co0, font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Valores vêm do banco de dados
        series_nomes = [serie['nome'] for serie in self.series_dados] if self.series_dados else ["1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano"]
        self.serie_var = tk.StringVar()
        serie_cb = ttk.Combobox(frame_serie, textvariable=self.serie_var, values=series_nomes, width=15, state="readonly")
        serie_cb.pack(side=tk.LEFT)
        serie_cb.bind("<<ComboboxSelected>>", self.carregar_turmas)
        
        # Frame para turma
        frame_turma = tk.Frame(self.frame_selecao, bg=self.co0)
        frame_turma.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(frame_turma, text="Turma:", bg=self.co0, font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.turma_var = tk.StringVar()
        self.turma_cb = ttk.Combobox(frame_turma, textvariable=self.turma_var, width=15, state="readonly")
        self.turma_cb.pack(side=tk.LEFT)
        self.turma_cb.bind("<<ComboboxSelected>>", self.carregar_horarios)
        
        # Frame para professor polivalente
        frame_prof = tk.Frame(self.frame_selecao, bg=self.co0)
        frame_prof.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(frame_prof, text="Professor Polivalente:", bg=self.co0, font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Filtrar apenas professores polivalentes
        profs_polivalentes = [p for p in self.professores if p.get('polivalente') == 'sim']
        profs_nomes = [p['nome'] for p in profs_polivalentes]
        profs_nomes.insert(0, "Selecione...")
        
        self.prof_polivalente_var = tk.StringVar(value="Selecione...")
        self.prof_polivalente_cb = ttk.Combobox(frame_prof, textvariable=self.prof_polivalente_var, 
                                               values=profs_nomes, width=20, state="disabled")  # Inicialmente desabilitado
        self.prof_polivalente_cb.pack(side=tk.LEFT)
        self.prof_polivalente_cb.bind("<<ComboboxSelected>>", self.aplicar_professor_polivalente)
        
        # Frame para dia do professor volante
        frame_volante = tk.Frame(self.frame_selecao, bg=self.co0)
        frame_volante.pack(side=tk.LEFT, padx=10, pady=5)
        
        tk.Label(frame_volante, text="Dia do Professor Volante:", bg=self.co0, font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.dia_volante_var = tk.StringVar(value="Selecione...")
        self.dia_volante_cb = ttk.Combobox(frame_volante, textvariable=self.dia_volante_var, 
                                         values=["Selecione..."] + self.dias_semana, width=15, state="disabled")  # Inicialmente desabilitado
        self.dia_volante_cb.pack(side=tk.LEFT)
        self.dia_volante_cb.bind("<<ComboboxSelected>>", self.aplicar_professor_volante)
        
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
        if serie_num:
            serie_num = int(serie_num)
            if 1 <= serie_num <= 5:
                self.turno_var.set("Matutino")
                self.turno_atual = "Matutino"
                
                # Habilitar opções de professor polivalente (só para 1º ao 5º ano)
                self.prof_polivalente_cb.config(state="readonly")
                self.dia_volante_cb.config(state="readonly")
            elif 6 <= serie_num <= 9:
                self.turno_var.set("Vespertino")
                self.turno_atual = "Vespertino"
                
                # Desabilitar opções de professor polivalente (não aplicável do 6º ao 9º ano)
                self.prof_polivalente_cb.config(state="disabled")
                self.dia_volante_cb.config(state="disabled")
                self.prof_polivalente_var.set("Selecione...")
                self.dia_volante_var.set("Selecione...")
        
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
            
            cursor.execute("""
                SELECT id, nome, serie_id FROM turmas 
                WHERE serie_id = %s 
                AND turno = %s
                AND escola_id = 60
                ORDER BY nome
            """, (serie_id, turno_bd))
            
            turmas = cursor.fetchall()
            
            # Debug
            logger.info(f"Turmas encontradas para série {serie_id}, turno {turno_bd}:")
            for t in turmas:
                logger.info(f"  ID: {t['id']}, Nome: '{t['nome']}', Serie ID: {t['serie_id']}")
            
            if turmas:
                self.turmas_dados = []
                turma_nomes = []
                
                # Gerar nomes para turmas sem nome
                letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                letra_idx = 0
                
                for turma in turmas:
                    # Se o nome da turma estiver vazio, criar um nome temporário
                    if not turma['nome'] or turma['nome'].strip() == '':
                        if letra_idx < len(letras):
                            nome_turma = f"Turma {serie_nome} {letras[letra_idx]}"
                            letra_idx += 1
                        else:
                            nome_turma = f"Turma {serie_nome} {letra_idx - len(letras) + 1}"
                            letra_idx += 1
                            
                        # Guardar o nome temporário e o ID real
                        turma_item = {'id': turma['id'], 'nome': nome_turma, 'nome_temporario': True}
                    else:
                        nome_turma = turma['nome']
                        turma_item = {'id': turma['id'], 'nome': nome_turma, 'nome_temporario': False}
                        
                    self.turmas_dados.append(turma_item)
                    turma_nomes.append(nome_turma)
                    
                self.turma_cb['values'] = turma_nomes
                
                # Selecionar a primeira turma
                if turma_nomes:
                    self.turma_var.set(turma_nomes[0])
                    self.carregar_horarios()
            else:
                # Fallback para turmas fictícias
                turma_nomes = [f"Turma {serie_nome} {letra}" for letra in "ABC"]
                self.turmas_dados = [{'id': None, 'nome': nome, 'nome_temporario': True} for nome in turma_nomes]
                self.turma_cb['values'] = turma_nomes
                
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
        if not turma_nome:
            return
            
        # Encontrar ID da turma selecionada
        self.turma_id = None
        for turma in self.turmas_dados:
            if turma['nome'] == turma_nome:
                self.turma_id = turma['id']
                break
                
        self.turma_atual = turma_nome
        
        # Limpar células existentes
        for celula in self.celulas_horario.values():
            celula.delete(0, tk.END)
            celula.config(bg=self.co0)  # Reset para cor padrão
        
        try:
            # Tentar carregar dados do banco de dados se a turma tiver ID
            if self.turma_id:
                # TODO: Implementar carregamento de horários do banco
                # Por enquanto, usando dados fictícios
                self.carregar_horarios_ficticios()
            else:
                # Se não tiver ID, usar dados fictícios
                self.carregar_horarios_ficticios()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar horários: {str(e)}")
            # Em caso de erro, manter células vazias
    
    def carregar_horarios_ficticios(self):
        """Preenche o horário com dados fictícios para demonstração."""
        # Criar lista simplificada de professores e disciplinas para demonstração
        if self.professores:
            prof_nomes = [p['nome'].split()[0] for p in self.professores[:8]]  # Pegar apenas primeiro nome
        else:
            prof_nomes = ["Ana", "Carlos", "Maria", "Pedro", "Joana", "Roberto", "Lúcia", "Miguel"]
            
        if self.disciplinas:
            disc_nomes = [d['nome'] for d in self.disciplinas[:8]]
        else:
            disc_nomes = ["LÍNGUA PORTUGUESA", "MATEMÁTICA", "CIÊNCIAS", "HISTÓRIA", "GEOGRAFIA", "ARTE", "Ed. Física", "Inglês"]
        
        # Criar combinações de disciplina + professor
        disciplinas_prof = []
        for i in range(min(len(disc_nomes), len(prof_nomes))):
            disciplinas_prof.append(f"{disc_nomes[i]} ({prof_nomes[i]})")
        
        # Preencher com dados aleatórios para demonstração
        import random
        for coord, celula in self.celulas_horario.items():
            row, col = coord
            # Pular células de intervalo
            if (self.turno_atual == "Matutino" and row == 4) or (self.turno_atual == "Vespertino" and row == 4):
                continue
            
            # 20% de chance de ter horário vago
            if random.random() < 0.2:
                celula.insert(0, "<VAGO>")
                celula.config(bg="white")
                continue
                
            # Preencher com disciplina+professor aleatória
            disciplina_prof = random.choice(disciplinas_prof)
            celula.insert(0, disciplina_prof)
            
            # Colorir conforme a disciplina
            disciplina = disciplina_prof.split(" (")[0]
            if "LÍNGUA PORTUGUESA" in disciplina:
                celula.config(bg=self.co4)  # Azul
            elif "MATEMÁTICA" in disciplina:
                celula.config(bg=self.co2)  # Verde
            elif "CIÊNCIAS" in disciplina:
                celula.config(bg=self.co3)  # Rosa
            elif "Ed. Física" in disciplina:
                celula.config(bg=self.co5)  # Laranja
            elif "ARTE" in disciplina:
                celula.config(bg=self.co6)  # Amarelo
            else:
                celula.config(bg=self.co9)  # Azul claro
    
    def atualizar_visualizacao(self, event=None):
        visualizacao = self.visualizacao_var.get()
        if visualizacao == "Turma":
            self.criar_grade_horarios()
        elif visualizacao == "Professor":
            # Implementar visualização por professor
            messagebox.showinfo("Info", "Visualização por professor será implementada")
        elif visualizacao == "Dia da Semana":
            # Implementar visualização por dia da semana
            messagebox.showinfo("Info", "Visualização por dia da semana será implementada")
    
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
                
                # Células para disciplinas
                for col, dia in enumerate(self.dias_semana, 1):
                    celula = tk.Entry(frame_conteudo, width=15, font=("Arial", 10), relief="ridge", 
                                    justify="center", bg=self.co0)
                    celula.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
                    
                    # Armazenar referência da célula
                    self.celulas_horario[(row, col)] = celula
                    
                    # Evento de clique duplo para edição
                    celula.bind("<Double-1>", lambda e, r=row, c=col: self.editar_celula(r, c))
        
        # Configurar redimensionamento
        for i in range(len(horarios) + 1):
            frame_conteudo.grid_rowconfigure(i, weight=1)
        for i in range(len(self.dias_semana) + 1):
            frame_conteudo.grid_columnconfigure(i, weight=1)
    
    def editar_celula(self, row, col):
        celula = self.celulas_horario.get((row, col))
        if not celula:
            return
            
        # Obter horário e dia
        horarios = self.horarios_matutino if self.turno_atual == "Matutino" else self.horarios_vespertino
        horario = horarios[row-1]  # -1 pois o índice da grade começa em 1
        dia = self.dias_semana[col-1]  # -1 pois o índice da grade começa em 1
        
        # Criar janela modal para edição
        janela_edicao = tk.Toplevel(self.janela)
        janela_edicao.title(f"Editar Horário - {dia} {horario}")
        janela_edicao.geometry("450x400")
        janela_edicao.transient(self.janela)
        janela_edicao.grab_set()
        
        janela_edicao.configure(bg=self.co0)
        
        # Centrar na tela
        janela_edicao.geometry("+%d+%d" % (
            self.janela.winfo_rootx() + (self.janela.winfo_width() / 2) - (450 / 2),
            self.janela.winfo_rooty() + (self.janela.winfo_height() / 2) - (400 / 2)))
        
        # Título
        tk.Label(janela_edicao, text=f"Editar Horário - {self.turma_atual}", 
                font=("Arial", 12, "bold"), bg=self.co0).pack(pady=(20, 5))
        
        tk.Label(janela_edicao, text=f"{dia} - {horario}", 
                font=("Arial", 11), bg=self.co0).pack(pady=(0, 20))
        
        # Verificar se é turma de 1º ao 5º ano para mostrar opção de polivalente
        serie_nome = self.serie_var.get()
        serie_num = ''.join(filter(str.isdigit, serie_nome))
        is_polivalente_series = False
        
        if serie_num:
            serie_num = int(serie_num)
            is_polivalente_series = (1 <= serie_num <= 5)
            
        # Tipo de professor
        frame_tipo = tk.Frame(janela_edicao, bg=self.co0)
        frame_tipo.pack(fill="x", padx=20, pady=5)
        
        tk.Label(frame_tipo, text="Tipo de Professor:", bg=self.co0, width=15, anchor="w").pack(side=tk.LEFT)
        
        tipo_var = tk.StringVar(value="Não Polivalente")
        
        # Opção de professor polivalente só disponível para turmas de 1º ao 5º ano
        if is_polivalente_series:
            tipo_rb1 = tk.Radiobutton(frame_tipo, text="Polivalente", variable=tipo_var, value="Polivalente", bg=self.co0)
            tipo_rb1.pack(side=tk.LEFT, padx=(0, 10))
            
            tipo_rb3 = tk.Radiobutton(frame_tipo, text="Professor Volante", variable=tipo_var, value="Volante", bg=self.co0)
            tipo_rb3.pack(side=tk.LEFT, padx=(0, 10))
            
        tipo_rb2 = tk.Radiobutton(frame_tipo, text="Não Polivalente", variable=tipo_var, value="Não Polivalente", bg=self.co0)
        tipo_rb2.pack(side=tk.LEFT)
        
        # Frame para cada tipo de professor (vamos mostrar/esconder conforme seleção)
        # 1. Frame para professor polivalente
        frame_polivalente = tk.Frame(janela_edicao, bg=self.co0)
        
        tk.Label(frame_polivalente, text="Professor:", bg=self.co0, width=15, anchor="w").pack(side=tk.LEFT)
        
        # Filtrar professores polivalentes
        profs_polivalentes = [p['nome'] for p in self.professores if p.get('polivalente') == 'sim']
        if not profs_polivalentes:
            profs_polivalentes = ["Professor 1", "Professor 2"]
            
        prof_pol_var = tk.StringVar()
        prof_pol_cb = ttk.Combobox(frame_polivalente, textvariable=prof_pol_var, 
                                 values=profs_polivalentes, width=25, state="readonly")
        prof_pol_cb.pack(side=tk.LEFT, padx=5)
        
        # 2. Frame para professor não polivalente
        frame_nao_polivalente = tk.Frame(janela_edicao, bg=self.co0)
        
        # 2.1 Disciplina
        frame_disc = tk.Frame(frame_nao_polivalente, bg=self.co0)
        frame_disc.pack(fill="x", pady=5)
        
        tk.Label(frame_disc, text="Disciplina:", bg=self.co0, width=15, anchor="w").pack(side=tk.LEFT)
        
        # Lista de disciplinas do banco de dados
        if self.disciplinas:
            valores_disciplinas = [d['nome'] for d in self.disciplinas]
            valores_disciplinas.append("<VAGO>")
        else:
            valores_disciplinas = ["LÍNGUA PORTUGUESA", "MATEMÁTICA", "CIÊNCIAS", "HISTÓRIA", "GEOGRAFIA", 
                                "ARTE", "Ed. Física", "Inglês", "Espanhol", "Sociologia", 
                                "Filosofia", "Física", "Química", "Biologia", "<VAGO>"]
        
        # Extrair disciplina do valor atual da célula
        celula_valor = celula.get()
        disciplina_atual = celula_valor.split(" (")[0] if " (" in celula_valor else celula_valor
        
        self.disciplina_var = tk.StringVar(value=disciplina_atual)
        disciplina_cb = ttk.Combobox(frame_disc, textvariable=self.disciplina_var, 
                                    values=valores_disciplinas, width=25, state="readonly")
        disciplina_cb.pack(side=tk.LEFT, padx=5)
        
        # 2.2 Professor
        frame_prof = tk.Frame(frame_nao_polivalente, bg=self.co0)
        frame_prof.pack(fill="x", pady=5)
        
        tk.Label(frame_prof, text="Professor:", bg=self.co0, width=15, anchor="w").pack(side=tk.LEFT)
        
        # Filtrar professores não polivalentes
        profs_nao_polivalentes = [p['nome'] for p in self.professores if p.get('polivalente') == 'não']
        if not profs_nao_polivalentes:
            profs_nao_polivalentes = ["Professor A", "Professor B", "Professor C"]
            
        profs_nao_polivalentes.append("<A DEFINIR>")
        
        # Extrair professor do valor atual da célula
        professor_atual = "<A DEFINIR>"
        if " (" in celula_valor and ")" in celula_valor:
            professor_atual = celula_valor.split(" (")[1].rstrip(")")
            # Tentar encontrar o professor completo
            for prof in profs_nao_polivalentes:
                if prof.startswith(professor_atual):
                    professor_atual = prof
                    break
        
        self.professor_var = tk.StringVar(value=professor_atual)
        professor_cb = ttk.Combobox(frame_prof, textvariable=self.professor_var, 
                                  values=profs_nao_polivalentes, width=25, state="readonly")
        professor_cb.pack(side=tk.LEFT, padx=5)
        
        # 3. Frame para professor volante (apenas informativo)
        frame_volante = tk.Frame(janela_edicao, bg=self.co0)
        tk.Label(frame_volante, text="As aulas deste dia serão ministradas pelo professor volante.", 
               bg=self.co0, font=("Arial", 10, "italic")).pack(pady=10)
        
        # Nome personalizado
        frame_custom = tk.Frame(janela_edicao, bg=self.co0)
        frame_custom.pack(fill="x", padx=20, pady=5)
        
        tk.Label(frame_custom, text="Nome personalizado:", bg=self.co0, anchor="w").pack(anchor="w")
        
        self.nome_personalizado_var = tk.StringVar(value=celula_valor if celula_valor != "<VAGO>" else "")
        nome_entry = tk.Entry(frame_custom, textvariable=self.nome_personalizado_var, width=40)
        nome_entry.pack(fill="x", pady=5)
        
        # Função para mostrar/esconder frames conforme tipo selecionado
        def atualizar_visibilidade_frames():
            tipo = tipo_var.get()
            
            # Esconder todos primeiro
            frame_polivalente.pack_forget()
            frame_nao_polivalente.pack_forget()
            frame_volante.pack_forget()
            
            # Mostrar frame apropriado
            if tipo == "Polivalente":
                frame_polivalente.pack(fill="x", padx=20, pady=5)
                self.nome_personalizado_var.set("Aula Regular")
            elif tipo == "Não Polivalente":
                frame_nao_polivalente.pack(fill="x", padx=20, pady=5)
                atualizar_nome_personalizado()
            else:  # Volante
                frame_volante.pack(fill="x", padx=20, pady=5)
                self.nome_personalizado_var.set("Professor Volante")
        
        # Quando o tipo de professor mudar
        tipo_var.trace_add("write", lambda *args: atualizar_visibilidade_frames())
        
        # Quando a disciplina ou professor mudar, atualizar o nome personalizado
        def atualizar_nome_personalizado(*args):
            if tipo_var.get() == "Não Polivalente":
                disciplina = self.disciplina_var.get()
                professor = self.professor_var.get()
                
                if disciplina == "<VAGO>":
                    self.nome_personalizado_var.set("<VAGO>")
                else:
                    if professor != "<A DEFINIR>":
                        # Extrair primeiro nome do professor
                        primeiro_nome = professor.split()[0]
                        self.nome_personalizado_var.set(f"{disciplina} ({primeiro_nome})")
                    else:
                        self.nome_personalizado_var.set(disciplina)
        
        self.disciplina_var.trace_add("write", atualizar_nome_personalizado)
        self.professor_var.trace_add("write", atualizar_nome_personalizado)
        prof_pol_var.trace_add("write", lambda *args: self.nome_personalizado_var.set(f"Aula Regular ({prof_pol_var.get().split()[0]})") if prof_pol_var.get() else None)
        
        # Observações
        frame_obs = tk.Frame(janela_edicao, bg=self.co0)
        frame_obs.pack(fill="x", padx=20, pady=5)
        
        tk.Label(frame_obs, text="Observações:", bg=self.co0, anchor="w").pack(anchor="w")
        
        observacao_text = tk.Text(frame_obs, width=40, height=3)
        observacao_text.pack(fill="x", pady=5)
        
        # Botões
        frame_botoes = tk.Frame(janela_edicao, bg=self.co0)
        frame_botoes.pack(fill="x", padx=20, pady=20)
        
        def salvar():
            # Pegar o texto que será exibido na célula
            texto_celula = self.nome_personalizado_var.get()
            
            if not texto_celula or texto_celula.strip() == "":
                texto_celula = "<VAGO>"
            
            # Atualizar a célula na grade
            celula.delete(0, tk.END)
            celula.insert(0, texto_celula)
            
            # Colorir conforme o tipo de professor
            tipo = tipo_var.get()
            if tipo == "Polivalente":
                celula.config(bg=self.co4)  # Azul para polivalente
            elif tipo == "Volante":
                celula.config(bg=self.co6)  # Amarelo para volante
            else:  # Não Polivalente
                disciplina = self.disciplina_var.get()
                if disciplina == "<VAGO>":
                    celula.config(bg="white")
                elif "LÍNGUA PORTUGUESA" in disciplina:
                    celula.config(bg=self.co4)  # Azul
                elif "MATEMÁTICA" in disciplina:
                    celula.config(bg=self.co2)  # Verde
                elif "CIÊNCIAS" in disciplina:
                    celula.config(bg=self.co3)  # Rosa
                elif "Ed. Física" in disciplina:
                    celula.config(bg=self.co5)  # Laranja
                elif "ARTE" in disciplina:
                    celula.config(bg=self.co6)  # Amarelo
                else:
                    celula.config(bg=self.co9)  # Azul claro
                
            # TODO: Salvar no banco de dados
            # Dados a salvar: turma_id, dia, horario, disciplina_id, professor_id, texto_personalizado
            
            janela_edicao.destroy()
        
        ttk.Button(frame_botoes, text="Cancelar", command=janela_edicao.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(frame_botoes, text="Salvar", command=salvar).pack(side=tk.RIGHT, padx=5)
        
        # Inicializar estado baseado no conteúdo atual da célula
        if "Professor Volante" in celula_valor:
            if is_polivalente_series:  # Só definir como volante se for série válida
                tipo_var.set("Volante")
            else:
                tipo_var.set("Não Polivalente")
        elif "Aula Regular" in celula_valor:
            if is_polivalente_series:  # Só definir como polivalente se for série válida
                tipo_var.set("Polivalente")
                if "(" in celula_valor and ")" in celula_valor:
                    nome_prof = celula_valor.split("(")[1].rstrip(")")
                    for prof in profs_polivalentes:
                        if prof.startswith(nome_prof):
                            prof_pol_var.set(prof)
                            break
            else:
                tipo_var.set("Não Polivalente")
        else:
            tipo_var.set("Não Polivalente")
        
        # Atualizar visibilidade inicial
        atualizar_visibilidade_frames()
    
    def criar_barra_botoes(self):
        # Limpar widgets existentes
        for widget in self.frame_botoes.winfo_children():
            widget.destroy()
        
        # Botões de ação
        ttk.Button(self.frame_botoes, text="Salvar Horários", 
                 command=self.salvar_horarios).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.frame_botoes, text="Imprimir Horários", 
                 command=self.imprimir_horarios).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.frame_botoes, text="Exportar para Excel", 
                 command=self.exportar_excel).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.frame_botoes, text="Preenchimento Automático", 
                 command=self.preencher_automaticamente).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.frame_botoes, text="Limpar Horários", 
                 command=self.limpar_horarios).pack(side=tk.RIGHT, padx=5)
    
    def salvar_horarios(self):
        # Verificar se uma turma está selecionada
        if not self.turma_atual:
            messagebox.showwarning("Atenção", "Selecione uma turma antes de salvar.")
            return
        
        # Coletar todos os dados do horário
        dados_horario = []
        
        # Escolher lista de horários com base no turno
        horarios = self.horarios_matutino if self.turno_atual == "Matutino" else self.horarios_vespertino
        
        for coord, celula in self.celulas_horario.items():
            row, col = coord
            # Pular células de intervalo
            if (self.turno_atual == "Matutino" and row == 4) or (self.turno_atual == "Vespertino" and row == 4):
                continue
                
            # Obter dados da célula
            valor = celula.get()
            horario = horarios[row-1]
            dia = self.dias_semana[col-1]
            
            dados_horario.append({
                'turma_id': self.turma_id,
                'turma_nome': self.turma_atual,
                'dia': dia,
                'horario': horario,
                'valor': valor
            })
        
        # Aqui seria implementada a lógica para salvar no banco de dados
        # Por enquanto, apenas mostrar mensagem de sucesso
        messagebox.showinfo("Sucesso", f"Horários da {self.turma_atual} salvos com sucesso!")
        
        # Para DEBUG: mostrar os dados que seriam salvos
        logger.info("Dados a salvar:")
        for item in dados_horario:
            logger.info(f"  {item['dia']} {item['horario']}: {item['valor']}")
    
    def imprimir_horarios(self):
        # Verificar se uma turma está selecionada
        if not self.turma_atual:
            messagebox.showwarning("Atenção", "Selecione uma turma antes de imprimir.")
            return
        
        # Criar janela modal para opções de impressão
        janela_impressao = tk.Toplevel(self.janela)
        janela_impressao.title("Opções de Impressão")
        janela_impressao.geometry("300x250")
        janela_impressao.transient(self.janela)
        janela_impressao.grab_set()
        janela_impressao.configure(bg=self.co0)
        
        # Centralizar na tela
        janela_impressao.geometry("+%d+%d" % (
            self.janela.winfo_rootx() + (self.janela.winfo_width() / 2) - (300 / 2),
            self.janela.winfo_rooty() + (self.janela.winfo_height() / 2) - (250 / 2)))
        
        tk.Label(janela_impressao, text="Opções de Impressão", 
                font=("Arial", 12, "bold"), bg=self.co0).pack(pady=(20, 10))
        
        # Variáveis para opções
        opcao_var = tk.StringVar(value="turma")
        
        # Opções de impressão
        frame_opcoes = tk.Frame(janela_impressao, bg=self.co0)
        frame_opcoes.pack(fill="x", padx=20, pady=10)
        
        tk.Radiobutton(frame_opcoes, text="Imprimir por Turma", variable=opcao_var, 
                      value="turma", bg=self.co0).pack(anchor="w", pady=2)
        tk.Radiobutton(frame_opcoes, text="Imprimir por Dia", variable=opcao_var, 
                      value="dia", bg=self.co0).pack(anchor="w", pady=2)
        tk.Radiobutton(frame_opcoes, text="Imprimir Semana Completa", variable=opcao_var, 
                      value="semana", bg=self.co0).pack(anchor="w", pady=2)
        
        # Botões
        frame_botoes = tk.Frame(janela_impressao, bg=self.co0)
        frame_botoes.pack(fill="x", padx=20, pady=20)
        
        def gerar_pdf():
            opcao = opcao_var.get()
            
            # Definir nome do arquivo
            caminho = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Salvar Horário como PDF"
            )
            
            if not caminho:
                return
            
            # Chamar função para gerar PDF
            if opcao == "turma":
                self.gerar_pdf_turma(caminho)
            elif opcao == "dia":
                self.gerar_pdf_dia(caminho)
            else:
                self.gerar_pdf_semana(caminho)
                
            janela_impressao.destroy()
        
        ttk.Button(frame_botoes, text="Cancelar", 
                 command=janela_impressao.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(frame_botoes, text="Gerar PDF", 
                 command=gerar_pdf).pack(side=tk.RIGHT, padx=5)
    
    def gerar_pdf_turma(self, caminho):
        # Verificar se uma turma está selecionada
        if not self.turma_atual:
            messagebox.showwarning("Atenção", "Selecione uma turma antes de imprimir.")
            return
            
        # Escolher lista de horários com base no turno
        horarios = self.horarios_matutino if self.turno_atual == "Matutino" else self.horarios_vespertino
        
        # Criar documento PDF
        doc = SimpleDocTemplate(caminho, pagesize=landscape(A4))
        elementos = []
        
        # Estilos
        estilos = getSampleStyleSheet()
        titulo_estilo = estilos['Heading1']
        
        # Título
        elementos.append(Paragraph(f"Horário de Aulas - {self.turma_atual} - {self.turno_atual}", titulo_estilo))
        elementos.append(Spacer(1, 10))
        
        # Criar tabela de dados
        dados = [["Horário"] + self.dias_semana]
        
        for i, horario in enumerate(horarios):
            linha = [horario]
            
            for j, _ in enumerate(self.dias_semana):
                if (i == 3):  # Intervalo
                    linha.append("INTERVALO")
                else:
                    # Pegar valor da célula na interface
                    celula = self.celulas_horario.get((i+1, j+1))
                    if celula:
                        linha.append(celula.get())
                    else:
                        linha.append("")
            
            dados.append(linha)
        
        # Criar tabela
        tabela = Table(dados)
        
        # Estilo da tabela
        estilo_tabela = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.co1),  # Cabeçalho azul
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Texto branco no cabeçalho
            ('BACKGROUND', (0, 1), (0, -1), colors.lightblue),  # Coluna de horários
            ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Bordas
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Centralizar todo o texto
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Centralizar verticalmente
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Negrito no cabeçalho
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),  # Negrito na coluna de horários
        ])
        
        # Estilo específico para linhas de intervalo
        for i, horario in enumerate(horarios):
            if horario in ["10:00-10:20", "15:30-15:50"]:  # Intervalo
                estilo_tabela.add('BACKGROUND', (0, i+1), (-1, i+1), colors.lightgrey)
        
        tabela.setStyle(estilo_tabela)
        elementos.append(tabela)
        
        # Construir PDF
        doc.build(elementos)
        
        messagebox.showinfo("Sucesso", f"Horário da {self.turma_atual} exportado como PDF!")
    
    def gerar_pdf_dia(self, caminho):
        messagebox.showinfo("Em implementação", "Função de geração por dia em desenvolvimento.")
    
    def gerar_pdf_semana(self, caminho):
        messagebox.showinfo("Em implementação", "Função de geração de semana completa em desenvolvimento.")
    
    def exportar_excel(self):
        # Verificar se uma turma está selecionada
        if not self.turma_atual:
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
    
    def preencher_automaticamente(self):
        # Verificar se uma turma está selecionada
        if not self.turma_atual:
            messagebox.showwarning("Atenção", "Selecione uma turma antes de preencher automaticamente.")
            return
        
        # Esta função seria implementada com um algoritmo para distribuir disciplinas
        # automaticamente de acordo com as cargas horárias, professores disponíveis, etc.
        # Por ora, apenas uma mensagem informativa
        messagebox.showinfo("Informação", 
                          "O preenchimento automático levará em conta:\n\n"
                          "- Carga horária de cada disciplina\n"
                          "- Disponibilidade dos professores\n"
                          "- Restrições de sala\n\n"
                          "Esta funcionalidade está em desenvolvimento.")
    
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
            celula.delete(0, tk.END)
            celula.config(bg="white")
    
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

    def aplicar_professor_polivalente(self, event=None):
        """Aplica o professor polivalente selecionado a todos os horários da turma (exceto dia do volante)."""
        professor_nome = self.prof_polivalente_var.get()
        
        if professor_nome == "Selecione..." or not self.turma_atual:
            return
            
        # Obter dia do professor volante (se estiver selecionado)
        dia_volante = self.dia_volante_var.get()
        dia_volante_idx = self.dias_semana.index(dia_volante) + 1 if dia_volante in self.dias_semana else -1
        
        # Obter primeiro nome do professor para exibição na grade
        primeiro_nome = professor_nome.split()[0]
        
        # Percorrer todas as células e atribuir o professor polivalente
        horarios = self.horarios_matutino if self.turno_atual == "Matutino" else self.horarios_vespertino
        
        for coord, celula in self.celulas_horario.items():
            row, col = coord
            
            # Pular células de intervalo
            if (self.turno_atual == "Matutino" and row == 4) or (self.turno_atual == "Vespertino" and row == 4):
                continue
                
            # Pular o dia do professor volante se estiver definido
            if dia_volante_idx > 0 and col == dia_volante_idx:
                continue
                
            # Atribuir disciplina + professor
            disciplina = "Aula Regular"  # Disciplina padrão para polivalentes
            celula.delete(0, tk.END)
            celula.insert(0, f"{disciplina} ({primeiro_nome})")
            celula.config(bg=self.co4)  # Azul para professor polivalente
        
        messagebox.showinfo("Sucesso", f"Professor polivalente {primeiro_nome} aplicado com sucesso à turma {self.turma_atual}.")
    
    def aplicar_professor_volante(self, event=None):
        """Aplica o professor volante ao dia selecionado."""
        dia_volante = self.dia_volante_var.get()
        
        if dia_volante == "Selecione..." or not self.turma_atual:
            return
            
        # Calcular o índice da coluna para o dia selecionado
        dia_idx = self.dias_semana.index(dia_volante) + 1  # +1 porque a coluna 0 é o horário
        
        # Atribuir professor volante a todas as células do dia selecionado
        horarios = self.horarios_matutino if self.turno_atual == "Matutino" else self.horarios_vespertino
        
        for row in range(1, len(horarios) + 1):
            # Pular células de intervalo
            if (self.turno_atual == "Matutino" and row == 4) or (self.turno_atual == "Vespertino" and row == 4):
                continue
                
            # Obter célula
            celula = self.celulas_horario.get((row, dia_idx))
            if celula:
                celula.delete(0, tk.END)
                celula.insert(0, "Professor Volante")
                celula.config(bg=self.co6)  # Amarelo para professor volante
        
        messagebox.showinfo("Sucesso", f"Professor volante aplicado com sucesso ao dia {dia_volante}.")


# Se o arquivo for executado diretamente
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal se executado diretamente
    app = InterfaceHorariosEscolares(janela_principal=root)
    root.mainloop() 