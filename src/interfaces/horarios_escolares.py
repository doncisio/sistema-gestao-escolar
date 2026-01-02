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
import json
import os
import tempfile
from pathlib import Path
import unicodedata
import re
from src.importers.geduc_horarios import parse_horario_por_turma

class InterfaceHorariosEscolares:
    def __init__(self, root=None, janela_principal=None):
        # Armazenar referência à janela principal
        self.janela_principal = janela_principal
        
        # Esconder janela principal quando abrir horários
        if self.janela_principal:
            self.janela_principal.withdraw()
        
        # Se root for None, cria uma nova janela
        if root is None:
            self.janela = tk.Toplevel(self.janela_principal)  # Passando o pai corretamente
            self.janela.title("Gerenciamento de Horários Escolares")
            self.janela.geometry("1200x700")
            
            # Garantir que a janela principal existe antes de chamar grab_set
            if self.janela_principal:
                self.janela.transient(self.janela_principal)  # Define a janela principal como proprietária
                # Não usar grab_set para permitir fechar corretamente
                
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
    
    def carregar_mapeamentos(self):
        """Carrega mapeamentos locais (sinônimos) de arquivo JSON em historic_geduc_imports."""
        self.mapeamentos = {'disciplinas': {}, 'professores': {}}

        try:
            path = Path(r'c:/gestao/historico_geduc_imports/mapeamentos_horarios.json')
            if not path.exists():
                return

            txt = path.read_text(encoding='utf-8')
            try:
                data = json.loads(txt)
            except Exception as e:
                logger.warning(f'Falha ao decodificar JSON de mapeamentos: {e}')
                return

            if not isinstance(data, dict):
                logger.warning('Arquivo de mapeamentos não contém um objeto JSON válido (esperado dict). Ignorando.')
                return

            # Normalização de chaves para permitir matching consistente
            def _norm_key(s: str) -> str:
                if not s:
                    return ''
                s = s.strip()
                s = unicodedata.normalize('NFKD', s)
                s = ''.join(c for c in s if not unicodedata.combining(c))
                s = re.sub(r'[^0-9A-Za-z\s]', ' ', s)
                s = re.sub(r'\s+', ' ', s)
                return s.strip().upper()

            # Processar disciplinas
            raw_disc = data.get('disciplinas') or {}
            if isinstance(raw_disc, dict):
                for k, v in raw_disc.items():
                    key = _norm_key(k)
                    if not key:
                        continue
                    try:
                        val = int(v)
                    except Exception:
                        val = v
                    self.mapeamentos.setdefault('disciplinas', {})[key] = val
            else:
                logger.warning('Campo "disciplinas" em mapeamentos não é um objeto; ignorado.')

            # Processar professores
            raw_prof = data.get('professores') or {}
            if isinstance(raw_prof, dict):
                for k, v in raw_prof.items():
                    key = _norm_key(k)
                    if not key:
                        continue
                    try:
                        val = int(v)
                    except Exception:
                        val = v
                    self.mapeamentos.setdefault('professores', {})[key] = val
            else:
                logger.warning('Campo "professores" em mapeamentos não é um objeto; ignorado.')

        except Exception as e:
            logger.warning(f'Falha ao carregar mapeamentos locais: {e}')

    def salvar_mapeamentos(self):
        """Salva mapeamentos locais em arquivo JSON."""
        try:
            path = Path(r'c:/gestao/historico_geduc_imports')
            path.mkdir(parents=True, exist_ok=True)
            f = path / 'mapeamentos_horarios.json'
            f.write_text(json.dumps(self.mapeamentos, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e:
            logger.warning(f'Erro ao salvar mapeamentos locais: {e}')

    def revisar_nao_mapeados(self, nao_mapeados):
        """Abre janela modal para revisão manual de não-mapeados.
        nao_mapeados: lista de dicts com keys row, col, dia, horario, valor
        """
        if not nao_mapeados:
            return

        modal = tk.Toplevel(self.janela)
        modal.title('Revisar não mapeados')
        modal.geometry('700x500')
        modal.transient(self.janela)
        modal.grab_set()
        modal.configure(bg=self.co0)

        canvas = tk.Canvas(modal, bg=self.co0)
        scrollbar = ttk.Scrollbar(modal, orient='vertical', command=canvas.yview)
        frame = tk.Frame(canvas, bg=self.co0)
        canvas.create_window((0, 0), window=frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Preparar listas para Comboboxes
        disc_names = [d['nome'] for d in (self.disciplinas or []) if isinstance(d, dict)]
        prof_names = [p['nome'] for p in (self.professores or []) if isinstance(p, dict)]
        if '<A DEFINIR>' not in prof_names:
            prof_names.append('<A DEFINIR>')

        entries = []

        def on_frame_config(event):
            canvas.configure(scrollregion=canvas.bbox('all'))

        frame.bind('<Configure>', on_frame_config)

        for idx, item in enumerate(nao_mapeados):
            fr = tk.Frame(frame, bg=self.co0, relief='groove', bd=1)
            fr.pack(fill='x', padx=8, pady=6)

            tk.Label(fr, text=f"{item['dia']} {item['horario']}", bg=self.co0, width=20, anchor='w').pack(side='left', padx=5)
            tk.Label(fr, text=item['valor'], bg=self.co0, width=40, anchor='w').pack(side='left', padx=5)

            disc_var = tk.StringVar()
            prof_var = tk.StringVar()

            disc_cb = ttk.Combobox(fr, textvariable=disc_var, values=[''] + disc_names, width=30)
            disc_cb.pack(side='left', padx=5)
            prof_cb = ttk.Combobox(fr, textvariable=prof_var, values=[''] + prof_names, width=25)
            prof_cb.pack(side='left', padx=5)

            entries.append((item, disc_cb, prof_cb))

        def aplicar():
            # aplicar mapeamentos selecionados às células
            import unicodedata

            def _norm(s: str) -> str:
                if not s:
                    return ''
                s = s.strip()
                s = unicodedata.normalize('NFKD', s)
                s = ''.join(c for c in s if not unicodedata.combining(c))
                s = re.sub(r'[^0-9A-Za-z\s]', ' ', s)
                s = re.sub(r'\s+', ' ', s)
                return s.strip().upper()

            for item, disc_cb, prof_cb in entries:
                sel_disc = disc_cb.get().strip()
                sel_prof = prof_cb.get().strip()

                row = item['row']
                col = item['col']
                cel = self.celulas_horario.get((row, col))
                if not cel:
                    continue

                # Atualizar texto da célula conforme seleção
                if sel_disc and sel_prof and sel_prof != '<A DEFINIR>':
                    primeiro = sel_prof.split()[0]
                    novo_texto = f"{sel_disc} ({primeiro})"
                elif sel_disc:
                    novo_texto = sel_disc
                elif sel_prof and sel_prof != '<A DEFINIR>':
                    novo_texto = sel_prof
                else:
                    novo_texto = item['valor']

                cel.delete(0, tk.END)
                cel.insert(0, novo_texto)

                # armazenar mapeamento local para futuras correspondências
                if sel_disc:
                    key = _norm(item['valor'])
                    if key:
                        # encontrar disciplina id
                        for d in (self.disciplinas or []):
                            if isinstance(d, dict) and d.get('nome') == sel_disc:
                                self.mapeamentos.setdefault('disciplinas', {})[key] = d.get('id')
                                break
                if sel_prof and sel_prof != '<A DEFINIR>':
                    keyp = _norm(sel_prof)
                    if keyp:
                        for p in (self.professores or []):
                            if isinstance(p, dict) and p.get('nome') == sel_prof:
                                self.mapeamentos.setdefault('professores', {})[keyp] = p.get('id')
                                break

            # salvar mapeamentos locais e fechar modal
            try:
                self.salvar_mapeamentos()
            except Exception:
                pass

            modal.destroy()

        btn_frame = tk.Frame(modal, bg=self.co0)
        btn_frame.pack(fill='x', pady=8)
        ttk.Button(btn_frame, text='Cancelar', command=modal.destroy).pack(side='right', padx=5)
        ttk.Button(btn_frame, text='Aplicar e Salvar', command=aplicar).pack(side='right', padx=5)

    
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
                
                # Se há apenas uma turma e ela não tem nome, mostrar apenas a série
                # Se há múltiplas turmas, gerar letras (A, B, C...)
                letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                
                for idx, turma in enumerate(turmas):
                    # Se o nome da turma estiver vazio
                    if not turma['nome'] or turma['nome'].strip() == '':
                        # Se é a única turma, usar nome vazio
                        if len(turmas) == 1:
                            nome_turma = ""
                        else:
                            # Se há múltiplas turmas, usar letra
                            nome_turma = letras[idx] if idx < len(letras) else str(idx + 1)
                    else:
                        # Usar o nome do banco de dados
                        nome_turma = turma['nome']
                        
                    # Guardar dados da turma
                    turma_item = {'id': turma['id'], 'nome': nome_turma}
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
                self.turmas_dados = [{'id': None, 'nome': nome} for nome in turma_nomes]
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
        # Permitir nome vazio para turmas únicas
        if turma_nome is None:
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
                try:
                    conn = conectar_bd()
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(
                        "SELECT dia, horario, valor, disciplina_id, professor_id "
                        "FROM horarios_importados WHERE turma_id = %s",
                        (self.turma_id,)
                    )
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
                            cel.delete(0, tk.END)
                            cel.insert(0, valor)
                            cel.config(bg=self.co4)

                except Exception:
                    # Em caso de problema com o banco, cair para dados fictícios
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
        ttk.Button(self.frame_botoes, text="💾 Salvar Horários", 
                 command=self.salvar_horarios).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.frame_botoes, text="🌐 Importar do GEDUC", 
                 command=self.importar_geduc).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.frame_botoes, text="🖨️ Imprimir Horários", 
                 command=self.imprimir_horarios).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.frame_botoes, text="📊 Exportar para Excel", 
                 command=self.exportar_excel).pack(side=tk.LEFT, padx=5)
    
    def salvar_horarios(self):
        """Salva os horários da turma atual no banco de dados usando upsert."""
        # Verificar se uma turma está selecionada
        if not self.turma_atual:
            messagebox.showwarning("Atenção", "Selecione uma turma antes de salvar.")
            return
        
        if not self.turma_id:
            messagebox.showerror("Erro", "ID da turma não encontrado.")
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
        
        # Carregar mapeamentos locais (se ainda não carregados)
        try:
            self.carregar_mapeamentos()
        except Exception as e:
            logger.warning(f"Falha ao carregar mapeamentos: {e}")
            self.mapeamentos = {'disciplinas': {}, 'professores': {}}

        # Usar utilitário de mapeamento para construir lista de persistência
        from src.utils.horarios_mapper import mapear_disc_prof
        
        rows_to_persist = []
        nao_mapeados = []
        
        for item in dados_horario:
            valor = (item.get('valor') or '').strip()
            
            # Pular células vazias
            if not valor:
                continue
            
            # Mapear usando o utilitário
            disc_id, prof_id = mapear_disc_prof(
                valor,
                self.disciplinas,
                self.professores,
                self.mapeamentos
            )
            
            # Registrar valores não mapeados para revisão
            if not disc_id and not prof_id:
                nao_mapeados.append({
                    'dia': item['dia'],
                    'horario': item['horario'],
                    'valor': valor
                })
            
            rows_to_persist.append({
                'turma_id': item.get('turma_id'),
                'dia': item.get('dia'),
                'horario': item.get('horario'),
                'valor': valor,
                'disciplina_id': disc_id,
                'professor_id': prof_id,
            })
        
        # Validar antes de persistir
        if not rows_to_persist:
            messagebox.showwarning("Atenção", "Nenhum horário para salvar (todas as células estão vazias).")
            return
        
        # Alertar sobre valores não mapeados
        if nao_mapeados:
            msg = f"Atenção: {len(nao_mapeados)} valor(es) não foram mapeados para disciplina/professor:\n\n"
            for nm in nao_mapeados[:5]:  # Mostrar apenas os primeiros 5
                msg += f"• {nm['dia']} {nm['horario']}: {nm['valor']}\n"
            if len(nao_mapeados) > 5:
                msg += f"... e mais {len(nao_mapeados) - 5} outros.\n"
            msg += "\nDeseja continuar mesmo assim?"
            
            if not messagebox.askyesno("Valores não mapeados", msg):
                return
        
        # Persistir usando upsert
        try:
            from src.utils.horarios_persistence import upsert_horarios
            inserted = upsert_horarios(rows_to_persist)
            
            msg = f"Horários da {self.turma_atual} salvos com sucesso!\n\n"
            msg += f"• Total de linhas: {inserted}\n"
            if nao_mapeados:
                msg += f"• Não mapeados: {len(nao_mapeados)}\n"
            
            messagebox.showinfo("Sucesso", msg)
            
            # Log detalhado
            logger.info(f"Horários salvos para turma {self.turma_atual} (ID={self.turma_id})")
            logger.info(f"Total de linhas: {inserted}, Não mapeados: {len(nao_mapeados)}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar horários: {e}", exc_info=True)
            messagebox.showerror("Erro", f"Erro ao salvar horários:\n{str(e)}")
    
    def imprimir_horarios(self):
        # Verificar se uma turma está selecionada
        if self.turma_atual is None:
            messagebox.showwarning("Atenção", "Selecione uma turma antes de imprimir.")
            return
        
        # Criar janela modal para opções de impressão
        janela_impressao = tk.Toplevel(self.janela)
        janela_impressao.title("Opções de Impressão")
        janela_impressao.geometry("300x180")
        janela_impressao.transient(self.janela)
        janela_impressao.grab_set()
        janela_impressao.configure(bg=self.co0)
        
        # Centralizar na tela
        janela_impressao.geometry("+%d+%d" % (
            self.janela.winfo_rootx() + (self.janela.winfo_width() / 2) - (300 / 2),
            self.janela.winfo_rooty() + (self.janela.winfo_height() / 2) - (90 / 2)))
        
        tk.Label(janela_impressao, text="Opções de Impressão", 
                font=("Arial", 12, "bold"), bg=self.co0).pack(pady=(20, 10))
        
        # Variáveis para opções
        opcao_var = tk.StringVar(value="turma")
        
        # Opções de impressão
        frame_opcoes = tk.Frame(janela_impressao, bg=self.co0)
        frame_opcoes.pack(fill="x", padx=20, pady=10)
        
        tk.Radiobutton(frame_opcoes, text="Imprimir por Turma", variable=opcao_var, 
                      value="turma", bg=self.co0).pack(anchor="w", pady=2)
        tk.Radiobutton(frame_opcoes, text="Imprimir por Professor", variable=opcao_var, 
                      value="professor", bg=self.co0).pack(anchor="w", pady=2)
        
        # Botões
        frame_botoes = tk.Frame(janela_impressao, bg=self.co0)
        frame_botoes.pack(fill="x", padx=20, pady=20)
        
        def gerar_pdf():
            opcao = opcao_var.get()
            janela_impressao.destroy()
            
            # Chamar função para gerar PDF (agora sem caminho)
            if opcao == "turma":
                self.gerar_pdf_turma()
            elif opcao == "professor":
                self.gerar_pdf_professor()
            else:
                self.gerar_pdf_turma()
        
        ttk.Button(frame_botoes, text="Cancelar", 
                 command=janela_impressao.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(frame_botoes, text="Gerar PDF", 
                 command=gerar_pdf).pack(side=tk.RIGHT, padx=5)
    
    def gerar_pdf_turma(self):
        # Verificar se uma turma está selecionada
        if self.turma_atual is None:
            messagebox.showwarning("Atenção", "Selecione uma turma antes de imprimir.")
            return
        
        try:
            # Criar arquivo temporário
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            caminho = temp_file.name
            temp_file.close()
            # Escolher lista de horários com base no turno
            horarios = self.horarios_matutino if self.turno_atual == "Matutino" else self.horarios_vespertino
            
            # Buscar dados do banco de dados com informações de professor
            conn = conectar_bd()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT h.dia, h.horario, h.valor, h.professor_id, f.nome as professor_nome
                FROM horarios_importados h
                LEFT JOIN funcionarios f ON h.professor_id = f.id
                WHERE h.turma_id = %s
            """, (self.turma_id,))
            horarios_bd = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Mapear professores para cores
            professores_unicos = set()
            for item in horarios_bd:
                if item.get('professor_id'):
                    professores_unicos.add(item['professor_id'])
            
            # Definir paleta de cores para professores
            cores_disponiveis = [
                colors.Color(0.8, 0.9, 1.0),      # Azul claro
                colors.Color(1.0, 0.9, 0.8),      # Laranja claro
                colors.Color(0.9, 1.0, 0.8),      # Verde claro
                colors.Color(1.0, 0.8, 0.9),      # Rosa claro
                colors.Color(0.95, 0.95, 0.8),    # Amarelo claro
                colors.Color(0.9, 0.8, 1.0),      # Roxo claro
                colors.Color(0.8, 1.0, 0.9),      # Verde água claro
                colors.Color(1.0, 0.85, 0.85),    # Vermelho claro
                colors.Color(0.85, 0.95, 1.0),    # Azul céu
                colors.Color(0.95, 0.9, 1.0),     # Lavanda
            ]
            
            cores_professor = {}
            for idx, prof_id in enumerate(sorted(professores_unicos)):
                cores_professor[prof_id] = cores_disponiveis[idx % len(cores_disponiveis)]
            
            # Criar documento PDF em modo paisagem
            doc = SimpleDocTemplate(caminho, pagesize=landscape(A4))
            elementos = []
            
            # Estilos
            estilos = getSampleStyleSheet()
            titulo_estilo = estilos['Heading1']
            
            # Obter nome da série
            serie_nome = self.serie_var.get() if hasattr(self, 'serie_var') else ""
            turma_display = f"{serie_nome} - {self.turma_atual}" if self.turma_atual else serie_nome
            
            # Título
            elementos.append(Paragraph(f"Horário de Aulas - {turma_display} - {self.turno_atual}", titulo_estilo))
            elementos.append(Spacer(1, 12))
            
            # Criar tabela de dados
            dados = [["Horário"] + self.dias_semana]
            
            # Mapear horários do banco para posições na tabela
            mapa_horarios = {}
            for item in horarios_bd:
                dia = item['dia']
                horario = item['horario']
                valor = item['valor']
                professor_id = item.get('professor_id')
                
                # Localizar coluna pelo dia
                try:
                    col = self.dias_semana.index(dia)
                except ValueError:
                    continue
                
                # Localizar linha pelo horário
                row_index = None
                if horario in horarios:
                    row_index = horarios.index(horario)
                elif isinstance(horario, str) and horario.startswith('Linha '):
                    try:
                        num = int(horario.split()[1])
                        row_index = num - 1
                    except:
                        continue
                
                if row_index is not None:
                    mapa_horarios[(row_index, col)] = {
                        'valor': valor,
                        'professor_id': professor_id
                    }
            
            # Preencher dados da tabela
            for i, horario in enumerate(horarios):
                linha = [horario]
                
                for j in range(len(self.dias_semana)):
                    dados_celula = mapa_horarios.get((i, j))
                    if dados_celula:
                        linha.append(dados_celula['valor'] or "")
                    else:
                        linha.append("")
                
                dados.append(linha)
            
            # Criar tabela com larguras de coluna ajustadas
            largura_col_horario = 80
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
                ('FONTSIZE', (0, 0), (-1, -1), 9),  # Tamanho da fonte
            ])
            
            # Aplicar cores por professor nas células
            for i in range(len(horarios)):
                for j in range(len(self.dias_semana)):
                    dados_celula = mapa_horarios.get((i, j))
                    if dados_celula and dados_celula['professor_id']:
                        cor = cores_professor.get(dados_celula['professor_id'], colors.white)
                        estilo_tabela.add('BACKGROUND', (j+1, i+1), (j+1, i+1), cor)
            
            # Estilo específico para linha de intervalo (linha 4)
            linha_intervalo = 3  # Índice 3 = linha 4
            if linha_intervalo < len(horarios):
                estilo_tabela.add('BACKGROUND', (1, linha_intervalo+1), (-1, linha_intervalo+1), colors.HexColor('#F39C12'))
                estilo_tabela.add('TEXTCOLOR', (1, linha_intervalo+1), (-1, linha_intervalo+1), colors.white)
                estilo_tabela.add('FONTNAME', (1, linha_intervalo+1), (-1, linha_intervalo+1), 'Helvetica-Bold')
            
            tabela.setStyle(estilo_tabela)
            elementos.append(tabela)
            
            # Adicionar legenda de professores
            if cores_professor:
                elementos.append(Spacer(1, 20))
                elementos.append(Paragraph("<b>Legenda de Professores:</b>", estilos['Normal']))
                elementos.append(Spacer(1, 8))
                
                # Buscar nomes dos professores
                conn = conectar_bd()
                cursor = conn.cursor(dictionary=True)
                prof_ids = list(cores_professor.keys())
                if prof_ids:
                    placeholders = ','.join(['%s'] * len(prof_ids))
                    cursor.execute(f"SELECT id, nome FROM funcionarios WHERE id IN ({placeholders})", prof_ids)
                    professores_info = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    
                    # Criar mini-tabela de legenda
                    dados_legenda = []
                    for prof in sorted(professores_info, key=lambda x: x['nome']):
                        dados_legenda.append([prof['nome'], ""])
                    
                    if dados_legenda:
                        tabela_legenda = Table(dados_legenda, colWidths=[200, 30])
                        estilo_legenda = TableStyle([
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ])
                        
                        # Aplicar cores na legenda
                        for idx, prof in enumerate(sorted(professores_info, key=lambda x: x['nome'])):
                            cor = cores_professor.get(prof['id'], colors.white)
                            estilo_legenda.add('BACKGROUND', (1, idx), (1, idx), cor)
                        
                        tabela_legenda.setStyle(estilo_legenda)
                        elementos.append(tabela_legenda)
            
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
            logger.exception("Erro ao gerar PDF da turma")
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
            cursor.execute("""
                SELECT DISTINCT f.id, f.nome 
                FROM funcionarios f
                INNER JOIN horarios_importados h ON f.id = h.professor_id
                WHERE f.escola_id = 60
                ORDER BY f.nome
            """)
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
            
            # Buscar horários do professor
            conn = conectar_bd()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT h.dia, h.horario, h.valor, t.nome as turma_nome, s.nome as serie_nome,
                       d.nome as disciplina_nome
                FROM horarios_importados h
                LEFT JOIN turmas t ON h.turma_id = t.id
                LEFT JOIN series s ON t.serie_id = s.id
                LEFT JOIN disciplinas d ON h.disciplina_id = d.id
                WHERE h.professor_id = %s
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
            doc = SimpleDocTemplate(caminho, pagesize=landscape(A4))
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
    
    def gerar_pdf_dia(self, caminho):
        messagebox.showinfo("Em implementação", "Função de geração por dia em desenvolvimento.")
    
    def gerar_pdf_semana(self, caminho):
        messagebox.showinfo("Em implementação", "Função de geração de semana completa em desenvolvimento.")
    
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
              UNIQUE KEY ux_horario_turma (turma_id, dia, horario)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            
            cursor.execute(sql)
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
                    (turma_id, dia, horario, valor, disciplina_id, professor_id, geduc_turma_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
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