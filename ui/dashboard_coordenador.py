"""
Dashboard específico para Coordenadores Pedagógicos.

Este módulo fornece uma visão focada em métricas pedagógicas:
- Desempenho acadêmico por turma/disciplina
- Taxa de aprovação/reprovação
- Frequência escolar
- Alertas de alunos em situação crítica
"""

from typing import Any, Optional, Dict, List
from threading import Thread
from tkinter import Frame, Label, Button, Toplevel, Scrollbar, Canvas
from tkinter.ttk import Progressbar, Treeview, Style
from config_logs import get_logger
from db.connection import get_cursor
from ui.theme import CO_BG, CO_FG, CO_ACCENT, CO_WARN

logger = get_logger(__name__)


class DashboardCoordenador:
    """
    Dashboard específico para coordenadores pedagógicos.
    
    Foco: métricas pedagógicas e acompanhamento de desempenho.
    """
    
    def __init__(self, janela, db_service, frame_getter, escola_id: int = 60, 
                 ano_letivo: Optional[str] = None, co_bg=CO_BG, co_fg=CO_FG, co_accent=CO_ACCENT):
        """
        Inicializa o dashboard do coordenador.
        
        Args:
            janela: Janela principal Tk
            db_service: Serviço de banco de dados
            frame_getter: Função que retorna o frame onde o dashboard será renderizado
            escola_id: ID da escola
            ano_letivo: Ano letivo atual
        """
        self.janela = janela
        self.db_service = db_service
        self.frame_getter = frame_getter
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
        
    def criar_dashboard(self):
        """Cria o dashboard do coordenador dentro do frame_tabela."""
        try:
            frame_tabela = self.frame_getter()
        except Exception:
            frame_tabela = None
            
        if frame_tabela is None:
            logger.warning("Frame de tabela não disponível para dashboard coordenador")
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
            text="📊 Dashboard Pedagógico - Coordenação",
            font=('Calibri', 18, 'bold'),
            bg=self.co_bg,
            fg=self.co_fg
        ).pack(side='left')
        
        # Loading indicator
        loading_frame = Frame(dashboard_frame, bg=self.co_bg)
        loading_frame.pack(fill='both', expand=True)
        
        Label(
            loading_frame,
            text="Carregando dados pedagógicos...",
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
                dados = self._buscar_dados_pedagogicos()
                
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
                            text="Não foi possível carregar os dados pedagógicos.",
                            font=('Calibri', 12),
                            bg=self.co_bg,
                            fg=self.co_danger
                        ).pack(pady=50)
                
                self.janela.after(0, _atualizar_ui)
                
            except Exception as e:
                logger.exception(f"Erro no worker do dashboard coordenador: {e}")
        
        Thread(target=_worker, daemon=True).start()
    
    def _buscar_dados_pedagogicos(self) -> Optional[Dict]:
        """Busca todos os dados pedagógicos necessários para o dashboard."""
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
                
                # 1. Média geral por disciplina
                cursor.execute("""
                    SELECT d.nome AS disciplina,
                           ROUND(AVG(n.nota), 2) AS media,
                           COUNT(DISTINCT n.aluno_id) AS total_alunos
                    FROM notas n
                    JOIN disciplinas d ON n.disciplina_id = d.id
                    JOIN matriculas m ON n.aluno_id = m.aluno_id 
                        AND n.ano_letivo_id = m.ano_letivo_id
                    JOIN alunos a ON n.aluno_id = a.id
                    WHERE n.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                    GROUP BY d.id, d.nome
                    ORDER BY media DESC
                """, (self.ano_letivo, self.escola_id))
                dados['medias_disciplinas'] = cursor.fetchall() or []
                
                # 2. Desempenho por série (média e frequência)
                cursor.execute("""
                    SELECT 
                        s.nome AS serie,
                        ROUND(AVG(n.nota), 2) AS media,
                        COUNT(DISTINCT m.aluno_id) AS total_alunos
                    FROM matriculas m
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN serie s ON t.serie_id = s.id
                    JOIN alunos a ON m.aluno_id = a.id
                    LEFT JOIN notas n ON m.aluno_id = n.aluno_id 
                        AND m.ano_letivo_id = n.ano_letivo_id
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                    GROUP BY s.id, s.nome
                    ORDER BY s.nome
                """, (self.ano_letivo, self.escola_id))
                dados['desempenho_series'] = cursor.fetchall() or []
                
                # 3. Alunos com baixo desempenho (média < 6.0)
                cursor.execute("""
                    SELECT 
                        a.nome AS aluno,
                        s.nome AS serie,
                        t.nome AS turma,
                        ROUND(AVG(n.nota), 2) AS media_geral
                    FROM alunos a
                    JOIN matriculas m ON a.id = m.aluno_id
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN serie s ON t.serie_id = s.id
                    JOIN notas n ON a.id = n.aluno_id AND n.ano_letivo_id = m.ano_letivo_id
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                    GROUP BY a.id, a.nome, s.nome, t.nome
                    HAVING media_geral < 6.0
                    ORDER BY media_geral ASC
                    LIMIT 20
                """, (self.ano_letivo, self.escola_id))
                dados['alunos_baixo_desempenho'] = cursor.fetchall() or []
                
                # 4. Alunos com baixa frequência (< 75%)
                cursor.execute("""
                    SELECT 
                        a.nome AS aluno,
                        s.nome AS serie,
                        t.nome AS turma,
                        COALESCE(SUM(fb.faltas), 0) AS total_faltas
                    FROM alunos a
                    JOIN matriculas m ON a.id = m.aluno_id
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN serie s ON t.serie_id = s.id
                    LEFT JOIN faltas_bimestrais fb ON a.id = fb.aluno_id 
                        AND fb.ano_letivo_id = m.ano_letivo_id
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                    GROUP BY a.id, a.nome, s.nome, t.nome
                    HAVING total_faltas > 40
                    ORDER BY total_faltas DESC
                    LIMIT 20
                """, (self.ano_letivo, self.escola_id))
                dados['alunos_baixa_frequencia'] = cursor.fetchall() or []
                
                # 5. Turmas com notas pendentes
                cursor.execute("""
                    SELECT 
                        s.nome AS serie,
                        t.nome AS turma,
                        d.nome AS disciplina,
                        COUNT(DISTINCT m.aluno_id) AS alunos_sem_nota
                    FROM matriculas m
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN serie s ON t.serie_id = s.id
                    JOIN alunos a ON m.aluno_id = a.id
                    CROSS JOIN disciplinas d
                    LEFT JOIN notas n ON m.aluno_id = n.aluno_id 
                        AND n.disciplina_id = d.id 
                        AND n.ano_letivo_id = m.ano_letivo_id
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                      AND n.id IS NULL
                    GROUP BY s.id, s.nome, t.id, t.nome, d.id, d.nome
                    HAVING alunos_sem_nota > 0
                    ORDER BY s.nome, t.nome, d.nome
                    LIMIT 30
                """, (self.ano_letivo, self.escola_id))
                dados['turmas_pendencias'] = cursor.fetchall() or []
                
                # 6. Totalizadores
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT m.aluno_id) AS total_alunos,
                        COUNT(DISTINCT t.id) AS total_turmas
                    FROM matriculas m
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN alunos a ON m.aluno_id = a.id
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                """, (self.ano_letivo, self.escola_id))
                totais = cursor.fetchone()
                dados['total_alunos'] = totais['total_alunos'] if totais else 0
                dados['total_turmas'] = totais['total_turmas'] if totais else 0
                
                # Média geral da escola
                cursor.execute("""
                    SELECT ROUND(AVG(n.nota), 2) AS media_geral
                    FROM notas n
                    JOIN matriculas m ON n.aluno_id = m.aluno_id 
                        AND n.ano_letivo_id = m.ano_letivo_id
                    JOIN alunos a ON n.aluno_id = a.id
                    WHERE n.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                """, (self.ano_letivo, self.escola_id))
                media = cursor.fetchone()
                dados['media_geral'] = media['media_geral'] if media and media['media_geral'] else 0
                
                return dados
                
        except Exception as e:
            logger.exception(f"Erro ao buscar dados pedagógicos: {e}")
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
        
        # Bind do scroll do mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # === SEÇÃO 1: CARDS DE RESUMO ===
        self._criar_cards_resumo(scrollable_frame, dados)
        
        # === SEÇÃO 2: DESEMPENHO POR DISCIPLINA ===
        self._criar_secao_disciplinas(scrollable_frame, dados.get('medias_disciplinas', []))
        
        # === SEÇÃO 3: DESEMPENHO POR SÉRIE ===
        self._criar_secao_series(scrollable_frame, dados.get('desempenho_series', []))
        
        # === SEÇÃO 4: ALERTAS ===
        self._criar_secao_alertas(scrollable_frame, dados)
        
    def _criar_cards_resumo(self, parent: Frame, dados: Dict):
        """Cria cards de resumo no topo do dashboard."""
        cards_frame = Frame(parent, bg=self.co_bg)
        cards_frame.pack(fill='x', pady=(0, 20))
        
        # Configurar grid
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1)
        
        # Card 1: Total de Alunos
        self._criar_card(
            cards_frame, 0, 
            "👥 Alunos Ativos",
            str(dados.get('total_alunos', 0)),
            self.co_info
        )
        
        # Card 2: Total de Turmas
        self._criar_card(
            cards_frame, 1,
            "📚 Turmas",
            str(dados.get('total_turmas', 0)),
            self.co_success
        )
        
        # Card 3: Média Geral
        media = dados.get('media_geral', 0)
        cor_media = self.co_success if media >= 7 else (self.co_warning if media >= 5 else self.co_danger)
        self._criar_card(
            cards_frame, 2,
            "📊 Média Geral",
            f"{media:.1f}" if media else "N/A",
            cor_media
        )
        
        # Card 4: Alunos em Alerta
        total_alertas = len(dados.get('alunos_baixo_desempenho', [])) + len(dados.get('alunos_baixa_frequencia', []))
        self._criar_card(
            cards_frame, 3,
            "⚠️ Em Alerta",
            str(total_alertas),
            self.co_danger if total_alertas > 10 else self.co_warning
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
    
    def _criar_secao_disciplinas(self, parent: Frame, disciplinas: List):
        """Cria seção de médias por disciplina."""
        frame = Frame(parent, bg=self.co_bg)
        frame.pack(fill='x', pady=10)
        
        Label(
            frame,
            text="📖 Média por Disciplina",
            font=('Calibri', 14, 'bold'),
            bg=self.co_bg,
            fg=self.co_fg
        ).pack(anchor='w', pady=(0, 10))
        
        if not disciplinas:
            Label(
                frame,
                text="Nenhuma nota lançada ainda.",
                font=('Calibri', 11),
                bg=self.co_bg,
                fg=self.co_fg
            ).pack(anchor='w')
            return
        
        # Grid de disciplinas
        grid_frame = Frame(frame, bg=self.co_bg)
        grid_frame.pack(fill='x')
        
        for i, disc in enumerate(disciplinas[:12]):  # Limitar a 12 disciplinas
            nome = disc['disciplina'] if isinstance(disc, dict) else disc[0]
            media = disc['media'] if isinstance(disc, dict) else disc[1]
            
            col = i % 4
            row = i // 4
            
            # Determinar cor baseada na média
            if media >= 7:
                cor = self.co_success
            elif media >= 5:
                cor = self.co_warning
            else:
                cor = self.co_danger
            
            item_frame = Frame(grid_frame, bg='#FFFFFF', padx=10, pady=8)
            item_frame.grid(row=row, column=col, padx=3, pady=3, sticky='nsew')
            
            Label(
                item_frame,
                text=nome[:20] + ('...' if len(nome) > 20 else ''),
                font=('Calibri', 10),
                bg='#FFFFFF',
                fg='#333333'
            ).pack(anchor='w')
            
            Label(
                item_frame,
                text=f"{media:.1f}" if media else "N/A",
                font=('Calibri', 16, 'bold'),
                bg='#FFFFFF',
                fg=cor
            ).pack(anchor='w')
        
        for i in range(4):
            grid_frame.grid_columnconfigure(i, weight=1)
    
    def _criar_secao_series(self, parent: Frame, series: List):
        """Cria seção de desempenho por série."""
        frame = Frame(parent, bg=self.co_bg)
        frame.pack(fill='x', pady=10)
        
        Label(
            frame,
            text="🎓 Desempenho por Série",
            font=('Calibri', 14, 'bold'),
            bg=self.co_bg,
            fg=self.co_fg
        ).pack(anchor='w', pady=(0, 10))
        
        if not series:
            Label(
                frame,
                text="Nenhum dado disponível.",
                font=('Calibri', 11),
                bg=self.co_bg,
                fg=self.co_fg
            ).pack(anchor='w')
            return
        
        # Barra horizontal para cada série
        for item in series:
            nome = item['serie'] if isinstance(item, dict) else item[0]
            media = item['media'] if isinstance(item, dict) else item[1]
            total = item['total_alunos'] if isinstance(item, dict) else item[2]
            
            if media is None:
                media = 0
            
            row_frame = Frame(frame, bg='#FFFFFF', padx=10, pady=5)
            row_frame.pack(fill='x', pady=2)
            
            # Nome da série
            Label(
                row_frame,
                text=f"{nome} ({total} alunos)",
                font=('Calibri', 10),
                bg='#FFFFFF',
                fg='#333333',
                width=25,
                anchor='w'
            ).pack(side='left')
            
            # Barra de progresso visual
            bar_frame = Frame(row_frame, bg='#E0E0E0', height=20, width=200)
            bar_frame.pack(side='left', padx=10)
            bar_frame.pack_propagate(False)
            
            # Calcular largura da barra (média 0-10 -> 0-200px)
            largura = int(media * 20) if media else 0
            cor_barra = self.co_success if media >= 7 else (self.co_warning if media >= 5 else self.co_danger)
            
            barra = Frame(bar_frame, bg=cor_barra, height=20, width=largura)
            barra.place(x=0, y=0)
            
            # Valor da média
            Label(
                row_frame,
                text=f"{media:.1f}" if media else "N/A",
                font=('Calibri', 11, 'bold'),
                bg='#FFFFFF',
                fg=cor_barra,
                width=5
            ).pack(side='left')
    
    def _criar_secao_alertas(self, parent: Frame, dados: Dict):
        """Cria seção de alertas com alunos em situação crítica."""
        frame = Frame(parent, bg=self.co_bg)
        frame.pack(fill='x', pady=10)
        
        Label(
            frame,
            text="⚠️ Alertas - Alunos que Precisam de Atenção",
            font=('Calibri', 14, 'bold'),
            bg=self.co_bg,
            fg=self.co_danger
        ).pack(anchor='w', pady=(0, 10))
        
        # Frame para as duas listas lado a lado
        alertas_frame = Frame(frame, bg=self.co_bg)
        alertas_frame.pack(fill='x')
        
        alertas_frame.grid_columnconfigure(0, weight=1)
        alertas_frame.grid_columnconfigure(1, weight=1)
        
        # Lista de baixo desempenho
        baixo_desemp_frame = Frame(alertas_frame, bg='#FFF5F5', padx=10, pady=10)
        baixo_desemp_frame.grid(row=0, column=0, padx=5, sticky='nsew')
        
        Label(
            baixo_desemp_frame,
            text="📉 Baixo Desempenho (média < 6.0)",
            font=('Calibri', 11, 'bold'),
            bg='#FFF5F5',
            fg=self.co_danger
        ).pack(anchor='w', pady=(0, 5))
        
        alunos_baixo = dados.get('alunos_baixo_desempenho', [])
        if alunos_baixo:
            for aluno in alunos_baixo[:10]:
                nome = aluno['aluno'] if isinstance(aluno, dict) else aluno[0]
                serie = aluno['serie'] if isinstance(aluno, dict) else aluno[1]
                turma = aluno['turma'] if isinstance(aluno, dict) else aluno[2]
                media = aluno['media_geral'] if isinstance(aluno, dict) else aluno[3]
                
                Label(
                    baixo_desemp_frame,
                    text=f"• {nome[:25]}... - {serie} {turma} - Média: {media:.1f}",
                    font=('Calibri', 9),
                    bg='#FFF5F5',
                    fg='#333333',
                    anchor='w'
                ).pack(anchor='w')
        else:
            Label(
                baixo_desemp_frame,
                text="✅ Nenhum aluno nesta situação",
                font=('Calibri', 10),
                bg='#FFF5F5',
                fg=self.co_success
            ).pack(anchor='w')
        
        # Lista de baixa frequência
        baixa_freq_frame = Frame(alertas_frame, bg='#FFF9E6', padx=10, pady=10)
        baixa_freq_frame.grid(row=0, column=1, padx=5, sticky='nsew')
        
        Label(
            baixa_freq_frame,
            text="📅 Muitas Faltas (> 40 faltas)",
            font=('Calibri', 11, 'bold'),
            bg='#FFF9E6',
            fg=self.co_warning
        ).pack(anchor='w', pady=(0, 5))
        
        alunos_freq = dados.get('alunos_baixa_frequencia', [])
        if alunos_freq:
            for aluno in alunos_freq[:10]:
                nome = aluno['aluno'] if isinstance(aluno, dict) else aluno[0]
                serie = aluno['serie'] if isinstance(aluno, dict) else aluno[1]
                turma = aluno['turma'] if isinstance(aluno, dict) else aluno[2]
                faltas = aluno['total_faltas'] if isinstance(aluno, dict) else aluno[3]
                
                Label(
                    baixa_freq_frame,
                    text=f"• {nome[:25]}... - {serie} {turma} - {int(faltas)} faltas",
                    font=('Calibri', 9),
                    bg='#FFF9E6',
                    fg='#333333',
                    anchor='w'
                ).pack(anchor='w')
        else:
            Label(
                baixa_freq_frame,
                text="✅ Nenhum aluno nesta situação",
                font=('Calibri', 10),
                bg='#FFF9E6',
                fg=self.co_success
            ).pack(anchor='w')
        
        # Seção de pendências de notas
        pendencias = dados.get('turmas_pendencias', [])
        if pendencias:
            pend_frame = Frame(frame, bg='#F0F4FF', padx=10, pady=10)
            pend_frame.pack(fill='x', pady=(10, 0))
            
            Label(
                pend_frame,
                text=f"📝 Turmas com Notas Pendentes ({len(pendencias)} registros)",
                font=('Calibri', 11, 'bold'),
                bg='#F0F4FF',
                fg=self.co_info
            ).pack(anchor='w', pady=(0, 5))
            
            for pend in pendencias[:8]:
                serie = pend['serie'] if isinstance(pend, dict) else pend[0]
                turma = pend['turma'] if isinstance(pend, dict) else pend[1]
                disc = pend['disciplina'] if isinstance(pend, dict) else pend[2]
                qtd = pend['alunos_sem_nota'] if isinstance(pend, dict) else pend[3]
                
                Label(
                    pend_frame,
                    text=f"• {serie} {turma} - {disc}: {qtd} alunos sem nota",
                    font=('Calibri', 9),
                    bg='#F0F4FF',
                    fg='#333333'
                ).pack(anchor='w')
