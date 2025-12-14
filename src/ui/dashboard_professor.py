"""
Dashboard específico para Professores.

Este módulo fornece uma visão focada nas turmas do professor logado:
- Suas turmas e quantidade de alunos
- Notas e frequências pendentes de lançamento
- Desempenho das suas turmas
- Ações rápidas para lançamento
"""

from typing import Any, Optional, Dict, List
from threading import Thread
from tkinter import Frame, Label, Button, Toplevel, Scrollbar, Canvas
from tkinter.ttk import Progressbar, Treeview, Style
from src.core.config_logs import get_logger
from db.connection import get_cursor
from src.ui.theme import CO_BG, CO_FG, CO_ACCENT, CO_WARN

logger = get_logger(__name__)


class DashboardProfessor:
    """
    Dashboard específico para professores.
    
    Foco: turmas e disciplinas do professor logado.
    """
    
    def __init__(self, janela, db_service, frame_getter, funcionario_id: int,
                 escola_id: int = 60, ano_letivo: Optional[str] = None,
                 co_bg=CO_BG, co_fg=CO_FG, co_accent=CO_ACCENT):
        """
        Inicializa o dashboard do professor.
        
        Args:
            janela: Janela principal Tk
            db_service: Serviço de banco de dados
            frame_getter: Função que retorna o frame onde o dashboard será renderizado
            funcionario_id: ID do funcionário (professor) logado
            escola_id: ID da escola
            ano_letivo: Ano letivo atual
        """
        self.janela = janela
        self.db_service = db_service
        self.frame_getter = frame_getter
        self.funcionario_id = funcionario_id
        self.escola_id = escola_id
        self.ano_letivo = ano_letivo
        self.co_bg = co_bg
        self.co_fg = co_fg
        self.co_accent = co_accent
        self._worker_token = 0
        
        # Cores adicionais
        self.co_success = "#77B341"  # Verde
        self.co_danger = "#BF3036"   # Vermelho
        self.co_warning = "#F7B731"  # Amarelo
        self.co_info = "#4A86E8"     # Azul claro
        
        # Callbacks para ações rápidas (serão definidos externamente)
        self.callback_lancar_notas = None
        self.callback_lancar_frequencia = None
        self.callback_gerar_boletins = None
        
    def criar_dashboard(self):
        """Cria o dashboard do professor dentro do frame_tabela."""
        try:
            frame_tabela = self.frame_getter()
        except Exception:
            frame_tabela = None
            
        if frame_tabela is None:
            logger.warning("Frame de tabela não disponível para dashboard professor")
            return
            
        # Limpar frame
        for widget in frame_tabela.winfo_children():
            widget.destroy()
            
        # Frame principal do dashboard
        dashboard_frame = Frame(frame_tabela, bg=self.co_bg)
        dashboard_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Título
        title_frame = Frame(dashboard_frame, bg=self.co_bg)
        title_frame.pack(fill='x', pady=(0, 15))
        
        Label(
            title_frame, 
            text="📚 Meu Painel - Professor(a)",
            font=('Calibri', 18, 'bold'),
            bg=self.co_bg,
            fg=self.co_fg
        ).pack(side='left')
        
        # Loading indicator
        loading_frame = Frame(dashboard_frame, bg=self.co_bg)
        loading_frame.pack(fill='both', expand=True)
        
        Label(
            loading_frame,
            text="Carregando suas turmas e dados...",
            font=('Calibri', 12),
            bg=self.co_bg,
            fg=self.co_fg
        ).pack(pady=20)
        
        progress = Progressbar(loading_frame, mode='indeterminate', length=300)
        progress.pack(pady=10)
        progress.start(10)
        
        # Incrementar token
        self._worker_token += 1
        local_token = self._worker_token
        
        def _worker():
            try:
                # Buscar dados em background
                dados = self._buscar_dados_professor()
                
                def _atualizar_ui():
                    if local_token != self._worker_token:
                        return
                        
                    try:
                        progress.stop()
                        loading_frame.destroy()
                    except:
                        pass
                    
                    if dados:
                        self._renderizar_dashboard(dashboard_frame, dados)
                    else:
                        Label(
                            dashboard_frame,
                            text="Não foi possível carregar seus dados.\nVerifique se você está vinculado a turmas neste ano letivo.",
                            font=('Calibri', 12),
                            bg=self.co_bg,
                            fg=self.co_danger
                        ).pack(pady=50)
                
                self.janela.after(0, _atualizar_ui)
                
            except Exception as e:
                logger.exception(f"Erro no worker do dashboard professor: {e}")
        
        Thread(target=_worker, daemon=True).start()
    
    def _buscar_dados_professor(self) -> Optional[Dict]:
        """Busca dados específicos do professor logado."""
        try:
            dados = {}
            
            with get_cursor() as cursor:
                if cursor is None:
                    return None
                
                # Obter ano letivo se não especificado
                if self.ano_letivo is None:
                    cursor.execute(
                        "SELECT ano_letivo FROM AnosLetivos WHERE CURDATE() BETWEEN data_inicio AND data_fim LIMIT 1"
                    )
                    r = cursor.fetchone()
                    self.ano_letivo = r['ano_letivo'] if r else str(__import__('datetime').datetime.now().year)
                
                # Obter ID do ano letivo
                cursor.execute("SELECT id FROM AnosLetivos WHERE ano_letivo = %s", (self.ano_letivo,))
                r = cursor.fetchone()
                ano_letivo_id = r['id'] if r else None
                
                if not ano_letivo_id:
                    return None
                
                # 1. Buscar turmas do professor
                # Primeiro, verificar na tabela de docências/atribuições
                cursor.execute("""
                    SELECT DISTINCT
                        t.id AS turma_id,
                        s.nome AS serie,
                        t.nome AS turma,
                        t.turno,
                        COUNT(DISTINCT m.aluno_id) AS total_alunos
                    FROM turmas t
                    JOIN series s ON t.serie_id = s.id
                    LEFT JOIN matriculas m ON t.id = m.turma_id 
                        AND m.ano_letivo_id = %s 
                        AND m.status = 'Ativo'
                    WHERE t.ano_letivo_id = %s
                      AND t.escola_id = %s
                      AND EXISTS (
                          SELECT 1 FROM docencia d 
                          WHERE d.turma_id = t.id 
                            AND d.funcionario_id = %s
                            AND d.ano_letivo_id = %s
                      )
                    GROUP BY t.id, s.nome, t.nome, t.turno
                    ORDER BY s.nome, t.nome
                """, (ano_letivo_id, ano_letivo_id, self.escola_id, self.funcionario_id, ano_letivo_id))
                
                turmas = cursor.fetchall()
                
                # Se não encontrou na docencia, tentar buscar por disciplinas lecionadas
                if not turmas:
                    cursor.execute("""
                        SELECT DISTINCT
                            t.id AS turma_id,
                            s.nome AS serie,
                            t.nome AS turma,
                            t.turno,
                            COUNT(DISTINCT m.aluno_id) AS total_alunos
                        FROM turmas t
                        JOIN series s ON t.serie_id = s.id
                        LEFT JOIN matriculas m ON t.id = m.turma_id 
                            AND m.ano_letivo_id = %s 
                            AND m.status = 'Ativo'
                        WHERE t.ano_letivo_id = %s
                          AND t.escola_id = %s
                        GROUP BY t.id, s.nome, t.nome, t.turno
                        ORDER BY s.nome, t.nome
                        LIMIT 10
                    """, (ano_letivo_id, ano_letivo_id, self.escola_id))
                    turmas = cursor.fetchall()
                
                dados['turmas'] = turmas or []
                
                # Total de alunos nas turmas do professor
                total_alunos = sum(
                    (t['total_alunos'] if isinstance(t, dict) else t[4]) or 0 
                    for t in turmas
                ) if turmas else 0
                dados['total_alunos'] = total_alunos
                dados['total_turmas'] = len(turmas) if turmas else 0
                
                # IDs das turmas para filtrar consultas
                turma_ids = [
                    t['turma_id'] if isinstance(t, dict) else t[0] 
                    for t in turmas
                ] if turmas else []
                
                if turma_ids:
                    # 2. Buscar notas pendentes de lançamento
                    placeholders = ','.join(['%s'] * len(turma_ids))
                    cursor.execute(f"""
                        SELECT 
                            s.nome AS serie,
                            t.nome AS turma,
                            d.nome AS disciplina,
                            COUNT(DISTINCT m.aluno_id) AS alunos_sem_nota,
                            'atual' AS bimestre
                        FROM matriculas m
                        JOIN turmas t ON m.turma_id = t.id
                        JOIN series s ON t.serie_id = s.id
                        CROSS JOIN disciplinas d
                        LEFT JOIN notas n ON m.aluno_id = n.aluno_id 
                            AND n.disciplina_id = d.id 
                            AND n.ano_letivo_id = m.ano_letivo_id
                        WHERE m.turma_id IN ({placeholders})
                          AND m.ano_letivo_id = %s
                          AND m.status = 'Ativo'
                          AND n.id IS NULL
                          AND d.ativo = 1
                        GROUP BY t.id, s.nome, t.nome, d.id, d.nome
                        HAVING alunos_sem_nota > 0
                        ORDER BY s.nome, t.nome, d.nome
                        LIMIT 20
                    """, (*turma_ids, ano_letivo_id))
                    dados['notas_pendentes'] = cursor.fetchall() or []
                    
                    # 3. Desempenho das turmas (média por turma)
                    cursor.execute(f"""
                        SELECT 
                            s.nome AS serie,
                            t.nome AS turma,
                            ROUND(AVG(n.nota), 2) AS media,
                            COUNT(DISTINCT n.aluno_id) AS alunos_com_nota
                        FROM turmas t
                        JOIN series s ON t.serie_id = s.id
                        JOIN matriculas m ON t.id = m.turma_id AND m.status = 'Ativo'
                        LEFT JOIN notas n ON m.aluno_id = n.aluno_id 
                            AND n.ano_letivo_id = m.ano_letivo_id
                        WHERE t.id IN ({placeholders})
                          AND m.ano_letivo_id = %s
                        GROUP BY t.id, s.nome, t.nome
                        ORDER BY media DESC
                    """, (*turma_ids, ano_letivo_id))
                    dados['desempenho_turmas'] = cursor.fetchall() or []
                    
                    # 4. Alunos com baixo desempenho nas turmas do professor
                    cursor.execute(f"""
                        SELECT 
                            a.nome AS aluno,
                            s.nome AS serie,
                            t.nome AS turma,
                            ROUND(AVG(n.nota), 2) AS media_geral
                        FROM alunos a
                        JOIN matriculas m ON a.id = m.aluno_id
                        JOIN turmas t ON m.turma_id = t.id
                        JOIN series s ON t.serie_id = s.id
                        JOIN notas n ON a.id = n.aluno_id AND n.ano_letivo_id = m.ano_letivo_id
                        WHERE t.id IN ({placeholders})
                          AND m.ano_letivo_id = %s
                          AND m.status = 'Ativo'
                        GROUP BY a.id, a.nome, s.nome, t.nome
                        HAVING media_geral < 6.0
                        ORDER BY media_geral ASC
                        LIMIT 15
                    """, (*turma_ids, ano_letivo_id))
                    dados['alunos_baixo_desempenho'] = cursor.fetchall() or []
                    
                    # 5. Contagem de notas já lançadas
                    cursor.execute(f"""
                        SELECT COUNT(DISTINCT n.id) AS total_notas
                        FROM notas n
                        JOIN matriculas m ON n.aluno_id = m.aluno_id 
                            AND n.ano_letivo_id = m.ano_letivo_id
                        WHERE m.turma_id IN ({placeholders})
                          AND m.ano_letivo_id = %s
                    """, (*turma_ids, ano_letivo_id))
                    r = cursor.fetchone()
                    dados['total_notas_lancadas'] = r['total_notas'] if r else 0
                else:
                    dados['notas_pendentes'] = []
                    dados['desempenho_turmas'] = []
                    dados['alunos_baixo_desempenho'] = []
                    dados['total_notas_lancadas'] = 0
                
                return dados
                
        except Exception as e:
            logger.exception(f"Erro ao buscar dados do professor: {e}")
            return None
    
    def _renderizar_dashboard(self, parent_frame: Frame, dados: Dict):
        """Renderiza o dashboard com os dados obtidos."""
        
        # Canvas com scroll para conteúdo
        canvas = Canvas(parent_frame, bg=self.co_bg, highlightthickness=0)
        scrollbar = Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = Frame(canvas, bg=self.co_bg)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind do scroll do mouse (usar bind específico do canvas em vez de bind_all)
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except Exception:
                pass
        # Usar bind no canvas e scrollable_frame em vez de bind_all para evitar conflitos
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        # Propagar binding para widgets filhos
        def _bind_mousewheel_recursive(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_mousewheel_recursive(child)
        scrollable_frame.bind("<Configure>", lambda e: _bind_mousewheel_recursive(scrollable_frame))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # === SEÇÃO 1: CARDS DE RESUMO ===
        self._criar_cards_resumo(scrollable_frame, dados)
        
        # === SEÇÃO 2: MINHAS TURMAS ===
        self._criar_secao_turmas(scrollable_frame, dados.get('turmas', []))
        
        # === SEÇÃO 3: AÇÕES RÁPIDAS ===
        self._criar_secao_acoes_rapidas(scrollable_frame)
        
        # === SEÇÃO 4: PENDÊNCIAS ===
        self._criar_secao_pendencias(scrollable_frame, dados)
        
        # === SEÇÃO 5: ALUNOS QUE PRECISAM DE ATENÇÃO ===
        self._criar_secao_alertas(scrollable_frame, dados)
        
    def _criar_cards_resumo(self, parent: Frame, dados: Dict):
        """Cria cards de resumo no topo do dashboard."""
        cards_frame = Frame(parent, bg=self.co_bg)
        cards_frame.pack(fill='x', pady=(0, 20))
        
        # Configurar grid
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1)
        
        # Card 1: Minhas Turmas
        self._criar_card(
            cards_frame, 0, 
            "📚 Minhas Turmas",
            str(dados.get('total_turmas', 0)),
            self.co_info
        )
        
        # Card 2: Total de Alunos
        self._criar_card(
            cards_frame, 1,
            "👥 Meus Alunos",
            str(dados.get('total_alunos', 0)),
            self.co_success
        )
        
        # Card 3: Notas Lançadas
        self._criar_card(
            cards_frame, 2,
            "✅ Notas Lançadas",
            str(dados.get('total_notas_lancadas', 0)),
            self.co_accent
        )
        
        # Card 4: Pendências
        total_pendencias = len(dados.get('notas_pendentes', []))
        cor_pend = self.co_danger if total_pendencias > 5 else (self.co_warning if total_pendencias > 0 else self.co_success)
        self._criar_card(
            cards_frame, 3,
            "📝 Pendências",
            str(total_pendencias),
            cor_pend
        )
    
    def _criar_card(self, parent: Frame, col: int, titulo: str, valor: str, cor: str):
        """Cria um card individual."""
        card = Frame(parent, bg=cor, padx=15, pady=10)
        card.grid(row=0, column=col, padx=5, pady=5, sticky='nsew')
        
        Label(
            card,
            text=titulo,
            font=('Calibri', 11),
            bg=cor,
            fg='white'
        ).pack()
        
        Label(
            card,
            text=valor,
            font=('Calibri', 24, 'bold'),
            bg=cor,
            fg='white'
        ).pack()
    
    def _criar_secao_turmas(self, parent: Frame, turmas: List):
        """Cria seção com as turmas do professor."""
        frame = Frame(parent, bg=self.co_bg)
        frame.pack(fill='x', pady=10)
        
        Label(
            frame,
            text="📚 Minhas Turmas",
            font=('Calibri', 14, 'bold'),
            bg=self.co_bg,
            fg=self.co_fg
        ).pack(anchor='w', pady=(0, 10))
        
        if not turmas:
            Label(
                frame,
                text="Nenhuma turma vinculada.",
                font=('Calibri', 11),
                bg=self.co_bg,
                fg=self.co_fg
            ).pack(anchor='w')
            return
        
        # Grid de turmas
        grid_frame = Frame(frame, bg=self.co_bg)
        grid_frame.pack(fill='x')
        
        for i, turma in enumerate(turmas):
            serie = turma['serie'] if isinstance(turma, dict) else turma[1]
            nome_turma = turma['turma'] if isinstance(turma, dict) else turma[2]
            turno = turma['turno'] if isinstance(turma, dict) else turma[3]
            total = turma['total_alunos'] if isinstance(turma, dict) else turma[4]
            
            col = i % 3
            row = i // 3
            
            turma_frame = Frame(grid_frame, bg='#FFFFFF', padx=15, pady=12)
            turma_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            Label(
                turma_frame,
                text=f"{serie} {nome_turma}",
                font=('Calibri', 12, 'bold'),
                bg='#FFFFFF',
                fg=self.co_info
            ).pack(anchor='w')
            
            Label(
                turma_frame,
                text=f"Turno: {turno or 'N/D'}",
                font=('Calibri', 10),
                bg='#FFFFFF',
                fg='#666666'
            ).pack(anchor='w')
            
            Label(
                turma_frame,
                text=f"👥 {total or 0} alunos",
                font=('Calibri', 11),
                bg='#FFFFFF',
                fg='#333333'
            ).pack(anchor='w', pady=(5, 0))
        
        for i in range(3):
            grid_frame.grid_columnconfigure(i, weight=1)
    
    def _criar_secao_acoes_rapidas(self, parent: Frame):
        """Cria seção com botões de ações rápidas."""
        frame = Frame(parent, bg=self.co_bg)
        frame.pack(fill='x', pady=10)
        
        Label(
            frame,
            text="⚡ Ações Rápidas",
            font=('Calibri', 14, 'bold'),
            bg=self.co_bg,
            fg=self.co_fg
        ).pack(anchor='w', pady=(0, 10))
        
        btns_frame = Frame(frame, bg=self.co_bg)
        btns_frame.pack(fill='x')
        
        # Botão Lançar Notas
        btn_notas = Button(
            btns_frame,
            text="📊 Lançar Notas",
            font=('Calibri', 11),
            bg=self.co_info,
            fg='white',
            padx=20,
            pady=8,
            cursor='hand2',
            command=self._abrir_lancamento_notas
        )
        btn_notas.pack(side='left', padx=5)
        
        # Botão Lançar Frequência
        btn_freq = Button(
            btns_frame,
            text="📅 Lançar Frequência",
            font=('Calibri', 11),
            bg=self.co_success,
            fg='white',
            padx=20,
            pady=8,
            cursor='hand2',
            command=self._abrir_lancamento_frequencia
        )
        btn_freq.pack(side='left', padx=5)
        
        # Botão Gerar Boletins
        btn_boletim = Button(
            btns_frame,
            text="📄 Gerar Boletins",
            font=('Calibri', 11),
            bg=self.co_accent,
            fg='white',
            padx=20,
            pady=8,
            cursor='hand2',
            command=self._abrir_gerador_boletins
        )
        btn_boletim.pack(side='left', padx=5)
    
    def _criar_secao_pendencias(self, parent: Frame, dados: Dict):
        """Cria seção de pendências de notas."""
        pendencias = dados.get('notas_pendentes', [])
        
        frame = Frame(parent, bg=self.co_bg)
        frame.pack(fill='x', pady=10)
        
        cor_header = self.co_danger if pendencias else self.co_success
        Label(
            frame,
            text=f"📝 Notas Pendentes de Lançamento ({len(pendencias)})",
            font=('Calibri', 14, 'bold'),
            bg=self.co_bg,
            fg=cor_header
        ).pack(anchor='w', pady=(0, 10))
        
        if not pendencias:
            Label(
                frame,
                text="✅ Parabéns! Todas as notas foram lançadas.",
                font=('Calibri', 11),
                bg=self.co_bg,
                fg=self.co_success
            ).pack(anchor='w')
            return
        
        # Lista de pendências
        lista_frame = Frame(frame, bg='#FFF5F5', padx=10, pady=10)
        lista_frame.pack(fill='x')
        
        for pend in pendencias[:10]:
            serie = pend['serie'] if isinstance(pend, dict) else pend[0]
            turma = pend['turma'] if isinstance(pend, dict) else pend[1]
            disc = pend['disciplina'] if isinstance(pend, dict) else pend[2]
            qtd = pend['alunos_sem_nota'] if isinstance(pend, dict) else pend[3]
            
            Label(
                lista_frame,
                text=f"• {serie} {turma} - {disc}: {qtd} alunos sem nota",
                font=('Calibri', 10),
                bg='#FFF5F5',
                fg='#333333'
            ).pack(anchor='w', pady=1)
        
        if len(pendencias) > 10:
            Label(
                lista_frame,
                text=f"... e mais {len(pendencias) - 10} pendências",
                font=('Calibri', 10, 'italic'),
                bg='#FFF5F5',
                fg='#666666'
            ).pack(anchor='w', pady=(5, 0))
    
    def _criar_secao_alertas(self, parent: Frame, dados: Dict):
        """Cria seção de alunos que precisam de atenção."""
        alunos = dados.get('alunos_baixo_desempenho', [])
        
        frame = Frame(parent, bg=self.co_bg)
        frame.pack(fill='x', pady=10)
        
        Label(
            frame,
            text=f"⚠️ Alunos que Precisam de Atenção ({len(alunos)})",
            font=('Calibri', 14, 'bold'),
            bg=self.co_bg,
            fg=self.co_warning
        ).pack(anchor='w', pady=(0, 10))
        
        if not alunos:
            Label(
                frame,
                text="✅ Todos os alunos estão com bom desempenho!",
                font=('Calibri', 11),
                bg=self.co_bg,
                fg=self.co_success
            ).pack(anchor='w')
            return
        
        # Lista de alunos
        lista_frame = Frame(frame, bg='#FFF9E6', padx=10, pady=10)
        lista_frame.pack(fill='x')
        
        Label(
            lista_frame,
            text="Alunos com média abaixo de 6.0:",
            font=('Calibri', 10, 'bold'),
            bg='#FFF9E6',
            fg='#333333'
        ).pack(anchor='w', pady=(0, 5))
        
        for aluno in alunos[:10]:
            nome = aluno['aluno'] if isinstance(aluno, dict) else aluno[0]
            serie = aluno['serie'] if isinstance(aluno, dict) else aluno[1]
            turma = aluno['turma'] if isinstance(aluno, dict) else aluno[2]
            media = aluno['media_geral'] if isinstance(aluno, dict) else aluno[3]
            
            # Determinar cor baseada na média
            cor = self.co_danger if media < 4 else self.co_warning
            
            row_frame = Frame(lista_frame, bg='#FFF9E6')
            row_frame.pack(fill='x', pady=1)
            
            Label(
                row_frame,
                text=f"• {nome[:30]}{'...' if len(nome) > 30 else ''} - {serie} {turma}",
                font=('Calibri', 10),
                bg='#FFF9E6',
                fg='#333333'
            ).pack(side='left')
            
            Label(
                row_frame,
                text=f"Média: {media:.1f}",
                font=('Calibri', 10, 'bold'),
                bg='#FFF9E6',
                fg=cor
            ).pack(side='right')
    
    def _abrir_lancamento_notas(self):
        """Abre interface de lançamento de notas."""
        try:
            if self.callback_lancar_notas:
                self.callback_lancar_notas()
            else:
                from tkinter import messagebox
                messagebox.showinfo(
                    "Lançar Notas",
                    "Use o menu Notas → Lançar Notas para acessar esta funcionalidade."
                )
        except Exception as e:
            logger.exception(f"Erro ao abrir lançamento de notas: {e}")
    
    def _abrir_lancamento_frequencia(self):
        """Abre interface de lançamento de frequência."""
        try:
            if self.callback_lancar_frequencia:
                self.callback_lancar_frequencia()
            else:
                from tkinter import messagebox
                messagebox.showinfo(
                    "Lançar Frequência",
                    "Use o menu Frequência → Lançar Frequência para acessar esta funcionalidade."
                )
        except Exception as e:
            logger.exception(f"Erro ao abrir lançamento de frequência: {e}")
    
    def _abrir_gerador_boletins(self):
        """Abre interface de geração de boletins."""
        try:
            if self.callback_gerar_boletins:
                self.callback_gerar_boletins()
            else:
                from tkinter import messagebox
                messagebox.showinfo(
                    "Gerar Boletins",
                    "Use o menu Relatórios → Boletins para acessar esta funcionalidade."
                )
        except Exception as e:
            logger.exception(f"Erro ao abrir gerador de boletins: {e}")
