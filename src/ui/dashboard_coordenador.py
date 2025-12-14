"""
Dashboard específico para Coordenadores Pedagógicos.

Este módulo fornece uma visão focada em métricas pedagógicas:
- Desempenho acadêmico por turma/disciplina
- Taxa de aprovação/reprovação
- Frequência escolar
- Alertas de alunos em situação crítica

Suporta visualização restrita por série:
- Séries Iniciais (1º ao 5º Ano)
- Séries Finais (6º ao 9º Ano)
"""

from typing import Any, Optional, Dict, List
from threading import Thread
from tkinter import Frame, Label, Button, Toplevel, Scrollbar, Canvas, StringVar
from tkinter.ttk import Progressbar, Treeview, Style, Notebook, Combobox
from src.core.config_logs import get_logger
from db.connection import get_cursor
from src.ui.theme import CO_BG, CO_FG, CO_ACCENT, CO_WARN

logger = get_logger(__name__)

# Constantes para tipos de coordenação
SERIES_INICIAIS = ['1º Ano', '2º Ano', '3º Ano', '4º Ano', '5º Ano', 
                   '1º ano', '2º ano', '3º ano', '4º ano', '5º ano']
SERIES_FINAIS = ['6º Ano', '7º Ano', '8º Ano', '9º Ano',
                 '6º ano', '7º ano', '8º ano', '9º ano']


class ModernStyle:
    """Estilos modernos para o dashboard."""
    
    # Cores principais - Paleta moderna
    BG_DARK = '#1a1d29'          # Fundo principal escuro
    BG_CARD = '#242837'          # Fundo dos cards
    BG_CARD_HOVER = '#2d3246'    # Hover dos cards
    
    # Cores de texto
    TEXT_PRIMARY = '#ffffff'     # Texto principal
    TEXT_SECONDARY = '#a0a5b8'   # Texto secundário
    TEXT_MUTED = '#6b7080'       # Texto apagado
    
    # Cores de destaque
    ACCENT_BLUE = '#4a90d9'      # Azul principal
    ACCENT_PURPLE = '#8b5cf6'    # Roxo
    ACCENT_GREEN = '#22c55e'     # Verde sucesso
    ACCENT_YELLOW = '#eab308'    # Amarelo warning
    ACCENT_RED = '#ef4444'       # Vermelho danger
    ACCENT_CYAN = '#06b6d4'      # Ciano info
    
    # Gradientes simulados (cores sólidas para compatibilidade tk)
    GRADIENT_BLUE = '#3b82f6'
    GRADIENT_PURPLE = '#a855f7'
    GRADIENT_GREEN = '#10b981'
    GRADIENT_ORANGE = '#f97316'
    
    # Bordas e separadores
    BORDER = '#3a3f52'
    
    # Fontes
    FONT_TITLE = ('Segoe UI', 20, 'bold')
    FONT_SUBTITLE = ('Segoe UI', 14, 'bold')
    FONT_HEADING = ('Segoe UI', 12, 'bold')
    FONT_BODY = ('Segoe UI', 11)
    FONT_SMALL = ('Segoe UI', 10)
    FONT_TINY = ('Segoe UI', 9)
    FONT_CARD_VALUE = ('Segoe UI', 28, 'bold')
    FONT_CARD_LABEL = ('Segoe UI', 10)


class DashboardCoordenador:
    """
    Dashboard específico para coordenadores pedagógicos.
    
    Foco: métricas pedagógicas e acompanhamento de desempenho.
    Suporta visualização filtrada por tipo de série (iniciais/finais).
    """
    
    def __init__(self, janela, db_service, frame_getter, escola_id: int = 60, 
                 ano_letivo: Optional[str] = None, co_bg=None, co_fg=None, co_accent=None,
                 series_permitidas: Optional[list] = None,
                 tipo_coordenacao: Optional[str] = None):
        """
        Inicializa o dashboard do coordenador.
        
        Args:
            janela: Janela principal Tk
            db_service: Serviço de banco de dados
            frame_getter: Função que retorna o frame onde o dashboard será renderizado
            escola_id: ID da escola
            ano_letivo: Ano letivo atual
            co_bg: Cor de fundo (opcional, usa tema moderno se não especificado)
            co_fg: Cor de texto (opcional)
            co_accent: Cor de destaque (opcional)
            series_permitidas: Lista de nomes de séries permitidas para este coordenador
            tipo_coordenacao: 'iniciais', 'finais' ou None para todas
        """
        self.janela = janela
        self.db_service = db_service
        self.frame_getter = frame_getter
        self.escola_id = escola_id
        self.ano_letivo = ano_letivo
        self._worker_token = 0
        
        # Usar tema moderno por padrão
        self.style = ModernStyle()
        self.co_bg = co_bg or self.style.BG_DARK
        self.co_fg = co_fg or self.style.TEXT_PRIMARY
        self.co_accent = co_accent or self.style.ACCENT_BLUE
        
        # Configuração de séries permitidas
        self.tipo_coordenacao = tipo_coordenacao
        if series_permitidas:
            self.series_permitidas = series_permitidas
        elif tipo_coordenacao == 'iniciais':
            self.series_permitidas = SERIES_INICIAIS
        elif tipo_coordenacao == 'finais':
            self.series_permitidas = SERIES_FINAIS
        else:
            self.series_permitidas = None  # Todas as séries
        
        # Determinar título do dashboard
        self._titulo_dashboard = self._get_titulo_dashboard()
        
        # Configurar estilos ttk
        self._configurar_estilos()
    
    def _get_titulo_dashboard(self) -> str:
        """Retorna o título apropriado baseado no tipo de coordenação."""
        if self.tipo_coordenacao == 'iniciais':
            return "📊 Dashboard Pedagógico - Séries Iniciais (1º ao 5º Ano)"
        elif self.tipo_coordenacao == 'finais':
            return "📊 Dashboard Pedagógico - Séries Finais (6º ao 9º Ano)"
        elif self.series_permitidas:
            return "📊 Dashboard Pedagógico - Coordenação"
        else:
            return "📊 Dashboard Pedagógico - Visão Geral"
    
    def _configurar_estilos(self):
        """Configura estilos ttk modernos."""
        style = Style()
        
        # Estilo para Treeview moderna
        style.configure(
            "Modern.Treeview",
            background=self.style.BG_CARD,
            foreground=self.style.TEXT_PRIMARY,
            fieldbackground=self.style.BG_CARD,
            rowheight=32,
            font=self.style.FONT_BODY
        )
        style.configure(
            "Modern.Treeview.Heading",
            background=self.style.BG_DARK,
            foreground=self.style.ACCENT_BLUE,
            font=self.style.FONT_HEADING,
            relief='flat'
        )
        style.map(
            "Modern.Treeview",
            background=[('selected', self.style.ACCENT_BLUE)],
            foreground=[('selected', self.style.TEXT_PRIMARY)]
        )
        
        # Estilo para Progressbar moderna
        style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor=self.style.BG_CARD,
            background=self.style.ACCENT_BLUE,
            thickness=8
        )
        
        # Estilo para Notebook
        style.configure(
            "Modern.TNotebook",
            background=self.style.BG_DARK,
            borderwidth=0
        )
        style.configure(
            "Modern.TNotebook.Tab",
            background=self.style.BG_CARD,
            foreground=self.style.TEXT_SECONDARY,
            padding=[15, 8],
            font=self.style.FONT_BODY
        )
        style.map(
            "Modern.TNotebook.Tab",
            background=[('selected', self.style.ACCENT_BLUE)],
            foreground=[('selected', self.style.TEXT_PRIMARY)]
        )
        
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
            
        # Frame principal do dashboard com fundo moderno
        dashboard_frame = Frame(frame_tabela, bg=self.co_bg)
        dashboard_frame.pack(fill='both', expand=True)
        
        # Header do dashboard
        self._criar_header(dashboard_frame)
        
        # Loading indicator moderno
        loading_frame = Frame(dashboard_frame, bg=self.co_bg)
        loading_frame.pack(fill='both', expand=True)
        
        # Container centralizado para loading
        loading_container = Frame(loading_frame, bg=self.style.BG_CARD, padx=40, pady=30)
        loading_container.place(relx=0.5, rely=0.4, anchor='center')
        
        Label(
            loading_container,
            text="🔄",
            font=('Segoe UI', 32),
            bg=self.style.BG_CARD,
            fg=self.style.ACCENT_BLUE
        ).pack(pady=(0, 10))
        
        Label(
            loading_container,
            text="Carregando dados pedagógicos...",
            font=self.style.FONT_BODY,
            bg=self.style.BG_CARD,
            fg=self.style.TEXT_SECONDARY
        ).pack(pady=(0, 15))
        
        progress = Progressbar(
            loading_container, 
            mode='indeterminate', 
            length=250,
            style="Modern.Horizontal.TProgressbar"
        )
        progress.pack(pady=5)
        progress.start(15)
        
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
                        self._mostrar_erro(dashboard_frame, "Não foi possível carregar os dados pedagógicos.")
                
                self.janela.after(0, _atualizar_ui)
                
            except Exception as e:
                logger.exception(f"Erro no worker do dashboard coordenador: {e}")
        
        Thread(target=_worker, daemon=True).start()
    
    def _criar_header(self, parent: Frame):
        """Cria o header moderno do dashboard."""
        header_frame = Frame(parent, bg=self.co_bg, pady=15)
        header_frame.pack(fill='x', padx=20)
        
        # Lado esquerdo - Título
        left_frame = Frame(header_frame, bg=self.co_bg)
        left_frame.pack(side='left', fill='y')
        
        Label(
            left_frame, 
            text=self._titulo_dashboard,
            font=self.style.FONT_TITLE,
            bg=self.co_bg,
            fg=self.co_fg
        ).pack(anchor='w')
        
        # Badge indicando tipo de coordenação
        if self.tipo_coordenacao:
            badge_color = self.style.ACCENT_PURPLE if self.tipo_coordenacao == 'iniciais' else self.style.ACCENT_CYAN
            badge_text = "1º ao 5º Ano" if self.tipo_coordenacao == 'iniciais' else "6º ao 9º Ano"
            
            badge_frame = Frame(left_frame, bg=badge_color, padx=10, pady=3)
            badge_frame.pack(anchor='w', pady=(8, 0))
            
            Label(
                badge_frame,
                text=f"🎯 {badge_text}",
                font=self.style.FONT_SMALL,
                bg=badge_color,
                fg='white'
            ).pack()
        
        # Lado direito - Info do ano letivo
        right_frame = Frame(header_frame, bg=self.co_bg)
        right_frame.pack(side='right', fill='y')
        
        Label(
            right_frame,
            text=f"📅 Ano Letivo: {self.ano_letivo or 'Atual'}",
            font=self.style.FONT_BODY,
            bg=self.co_bg,
            fg=self.style.TEXT_SECONDARY
        ).pack(anchor='e')
    
    def _mostrar_erro(self, parent: Frame, mensagem: str):
        """Mostra mensagem de erro estilizada."""
        erro_frame = Frame(parent, bg=self.style.BG_CARD, padx=30, pady=20)
        erro_frame.place(relx=0.5, rely=0.4, anchor='center')
        
        Label(
            erro_frame,
            text="⚠️",
            font=('Segoe UI', 40),
            bg=self.style.BG_CARD,
            fg=self.style.ACCENT_RED
        ).pack(pady=(0, 10))
        
        Label(
            erro_frame,
            text=mensagem,
            font=self.style.FONT_BODY,
            bg=self.style.BG_CARD,
            fg=self.style.TEXT_SECONDARY
        ).pack()
    
    def _filtrar_por_series(self, dados_lista: List[Dict], campo_serie: str = 'serie') -> List[Dict]:
        """Filtra dados para mostrar apenas séries permitidas."""
        if not self.series_permitidas:
            return dados_lista
        
        return [
            item for item in dados_lista
            if self._serie_permitida(
                item.get(campo_serie) if isinstance(item, dict) else item[0]
            )
        ]
    
    def _serie_permitida(self, nome_serie: Optional[str]) -> bool:
        """Verifica se uma série está na lista de permitidas."""
        if not self.series_permitidas:
            return True
        if not nome_serie:
            return False
        
        nome_lower = nome_serie.lower().strip()
        for serie in self.series_permitidas:
            if serie.lower().strip() in nome_lower or nome_lower in serie.lower().strip():
                return True
        return False
    
    def _buscar_dados_pedagogicos(self) -> Optional[Dict]:
        """Busca todos os dados pedagógicos necessários para o dashboard."""
        try:
            dados = {}
            
            # Construir cláusula de filtro de séries
            filtro_series_sql = ""
            if self.series_permitidas:
                placeholders = ', '.join(['%s'] * len(self.series_permitidas))
                filtro_series_sql = f" AND s.nome IN ({placeholders})"
            
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
                
                # Parâmetros base
                params_base = [self.ano_letivo, self.escola_id]
                params_com_series = params_base + (self.series_permitidas if self.series_permitidas else [])
                
                # 1. Média geral por disciplina (filtrada por série)
                query_disciplinas = f"""
                    SELECT d.nome AS disciplina,
                           ROUND(AVG(n.nota), 2) AS media,
                           COUNT(DISTINCT n.aluno_id) AS total_alunos
                    FROM notas n
                    JOIN disciplinas d ON n.disciplina_id = d.id
                    JOIN matriculas m ON n.aluno_id = m.aluno_id 
                        AND n.ano_letivo_id = m.ano_letivo_id
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN series s ON t.serie_id = s.id
                    JOIN alunos a ON n.aluno_id = a.id
                    WHERE n.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                      {filtro_series_sql}
                    GROUP BY d.id, d.nome
                    ORDER BY media DESC
                """
                cursor.execute(query_disciplinas, params_com_series)
                dados['medias_disciplinas'] = cursor.fetchall() or []
                
                # 2. Desempenho por série (filtrado)
                query_series = f"""
                    SELECT 
                        s.nome AS serie,
                        ROUND(AVG(n.nota), 2) AS media,
                        COUNT(DISTINCT m.aluno_id) AS total_alunos
                    FROM matriculas m
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN series s ON t.serie_id = s.id
                    JOIN alunos a ON m.aluno_id = a.id
                    LEFT JOIN notas n ON m.aluno_id = n.aluno_id 
                        AND m.ano_letivo_id = n.ano_letivo_id
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                      {filtro_series_sql}
                    GROUP BY s.id, s.nome
                    ORDER BY s.nome
                """
                cursor.execute(query_series, params_com_series)
                dados['desempenho_series'] = cursor.fetchall() or []
                
                # 3. Alunos com baixo desempenho (média < 6.0) - filtrado
                query_baixo_desemp = f"""
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
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                      {filtro_series_sql}
                    GROUP BY a.id, a.nome, s.nome, t.nome
                    HAVING media_geral < 6.0
                    ORDER BY media_geral ASC
                    LIMIT 20
                """
                cursor.execute(query_baixo_desemp, params_com_series)
                dados['alunos_baixo_desempenho'] = cursor.fetchall() or []
                
                # 4. Alunos com baixa frequência (> 40 faltas) - filtrado
                query_baixa_freq = f"""
                    SELECT 
                        a.nome AS aluno,
                        s.nome AS serie,
                        t.nome AS turma,
                        COALESCE(SUM(fb.faltas), 0) AS total_faltas
                    FROM alunos a
                    JOIN matriculas m ON a.id = m.aluno_id
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN series s ON t.serie_id = s.id
                    LEFT JOIN faltas_bimestrais fb ON a.id = fb.aluno_id 
                        AND fb.ano_letivo_id = m.ano_letivo_id
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                      {filtro_series_sql}
                    GROUP BY a.id, a.nome, s.nome, t.nome
                    HAVING total_faltas > 40
                    ORDER BY total_faltas DESC
                    LIMIT 20
                """
                cursor.execute(query_baixa_freq, params_com_series)
                dados['alunos_baixa_frequencia'] = cursor.fetchall() or []
                
                # 5. Turmas com notas pendentes - filtrado
                query_pendencias = f"""
                    SELECT 
                        s.nome AS serie,
                        t.nome AS turma,
                        d.nome AS disciplina,
                        COUNT(DISTINCT m.aluno_id) AS alunos_sem_nota
                    FROM matriculas m
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN series s ON t.serie_id = s.id
                    JOIN alunos a ON m.aluno_id = a.id
                    CROSS JOIN disciplinas d
                    LEFT JOIN notas n ON m.aluno_id = n.aluno_id 
                        AND n.disciplina_id = d.id 
                        AND n.ano_letivo_id = m.ano_letivo_id
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                      AND n.id IS NULL
                      {filtro_series_sql}
                    GROUP BY s.id, s.nome, t.id, t.nome, d.id, d.nome
                    HAVING alunos_sem_nota > 0
                    ORDER BY s.nome, t.nome, d.nome
                    LIMIT 30
                """
                cursor.execute(query_pendencias, params_com_series)
                dados['turmas_pendencias'] = cursor.fetchall() or []
                
                # 6. Totalizadores - filtrado
                query_totais = f"""
                    SELECT 
                        COUNT(DISTINCT m.aluno_id) AS total_alunos,
                        COUNT(DISTINCT t.id) AS total_turmas
                    FROM matriculas m
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN series s ON t.serie_id = s.id
                    JOIN alunos a ON m.aluno_id = a.id
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                      {filtro_series_sql}
                """
                cursor.execute(query_totais, params_com_series)
                totais = cursor.fetchone()
                dados['total_alunos'] = totais['total_alunos'] if totais else 0
                dados['total_turmas'] = totais['total_turmas'] if totais else 0
                
                # Média geral (filtrada)
                query_media = f"""
                    SELECT ROUND(AVG(n.nota), 2) AS media_geral
                    FROM notas n
                    JOIN matriculas m ON n.aluno_id = m.aluno_id 
                        AND n.ano_letivo_id = m.ano_letivo_id
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN series s ON t.serie_id = s.id
                    JOIN alunos a ON n.aluno_id = a.id
                    WHERE n.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                      {filtro_series_sql}
                """
                cursor.execute(query_media, params_com_series)
                media = cursor.fetchone()
                dados['media_geral'] = media['media_geral'] if media and media['media_geral'] else 0
                
                # Estatísticas adicionais para o dashboard moderno
                # Total de disciplinas com aulas
                cursor.execute("""
                    SELECT COUNT(DISTINCT d.id) AS total_disciplinas
                    FROM disciplinas d
                    JOIN notas n ON d.id = n.disciplina_id
                    WHERE n.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                """, (self.ano_letivo,))
                disc_result = cursor.fetchone()
                dados['total_disciplinas'] = disc_result['total_disciplinas'] if disc_result else 0
                
                return dados
                
        except Exception as e:
            logger.exception(f"Erro ao buscar dados pedagógicos: {e}")
            return None
    
    def _renderizar_dashboard(self, parent_frame: Frame, dados: Dict):
        """Renderiza o dashboard moderno com os dados obtidos."""
        
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
        
        # Expande o frame interno para preencher o canvas
        def _configure_scroll(event):
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)
        canvas.bind("<Configure>", _configure_scroll)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Padding interno
        content_frame = Frame(scrollable_frame, bg=self.co_bg, padx=20, pady=10)
        content_frame.pack(fill='both', expand=True)
        
        # === SEÇÃO 1: CARDS DE RESUMO MODERNOS ===
        self._criar_cards_resumo_moderno(content_frame, dados)
        
        # === SEÇÃO 2: GRID DE DUAS COLUNAS ===
        grid_frame = Frame(content_frame, bg=self.co_bg)
        grid_frame.pack(fill='x', pady=(20, 0))
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
        
        # Coluna esquerda - Desempenho por Série
        self._criar_secao_series_moderna(grid_frame, dados.get('desempenho_series', []), row=0, col=0)
        
        # Coluna direita - Desempenho por Disciplina
        self._criar_secao_disciplinas_moderna(grid_frame, dados.get('medias_disciplinas', []), row=0, col=1)
        
        # === SEÇÃO 3: ALERTAS MODERNOS ===
        self._criar_secao_alertas_moderna(content_frame, dados)
        
        # === SEÇÃO 4: PENDÊNCIAS ===
        if dados.get('turmas_pendencias'):
            self._criar_secao_pendencias_moderna(content_frame, dados.get('turmas_pendencias', []))
        
    def _criar_cards_resumo_moderno(self, parent: Frame, dados: Dict):
        """Cria cards de resumo modernos no topo do dashboard."""
        cards_frame = Frame(parent, bg=self.co_bg)
        cards_frame.pack(fill='x', pady=(0, 10))
        
        # Configurar grid para 4 cards
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1, uniform='cards')
        
        # Card 1: Total de Alunos
        self._criar_card_moderno(
            cards_frame, 0,
            icon="👥",
            titulo="Alunos Ativos",
            valor=str(dados.get('total_alunos', 0)),
            cor_accent=self.style.GRADIENT_BLUE,
            subtitulo="matriculados"
        )
        
        # Card 2: Total de Turmas
        self._criar_card_moderno(
            cards_frame, 1,
            icon="📚",
            titulo="Turmas",
            valor=str(dados.get('total_turmas', 0)),
            cor_accent=self.style.GRADIENT_PURPLE,
            subtitulo="em funcionamento"
        )
        
        # Card 3: Média Geral
        media = dados.get('media_geral', 0) or 0
        cor_media = self.style.ACCENT_GREEN if media >= 7 else (self.style.ACCENT_YELLOW if media >= 5 else self.style.ACCENT_RED)
        self._criar_card_moderno(
            cards_frame, 2,
            icon="📊",
            titulo="Média Geral",
            valor=f"{media:.1f}" if media else "N/A",
            cor_accent=cor_media,
            subtitulo="desempenho escolar"
        )
        
        # Card 4: Alunos em Alerta
        total_alertas = len(dados.get('alunos_baixo_desempenho', [])) + len(dados.get('alunos_baixa_frequencia', []))
        cor_alertas = self.style.ACCENT_RED if total_alertas > 10 else (self.style.ACCENT_YELLOW if total_alertas > 0 else self.style.ACCENT_GREEN)
        self._criar_card_moderno(
            cards_frame, 3,
            icon="⚠️",
            titulo="Em Alerta",
            valor=str(total_alertas),
            cor_accent=cor_alertas,
            subtitulo="necessitam atenção"
        )
    
    def _criar_card_moderno(self, parent: Frame, col: int, icon: str, titulo: str, 
                            valor: str, cor_accent: str, subtitulo: str = ""):
        """Cria um card moderno com design elegante."""
        # Card container com borda colorida na esquerda
        card_outer = Frame(parent, bg=self.style.BG_CARD, padx=2, pady=2)
        card_outer.grid(row=0, column=col, padx=8, pady=5, sticky='nsew')
        
        # Barra colorida lateral
        accent_bar = Frame(card_outer, bg=cor_accent, width=4)
        accent_bar.pack(side='left', fill='y')
        
        # Conteúdo do card
        card_content = Frame(card_outer, bg=self.style.BG_CARD, padx=15, pady=15)
        card_content.pack(side='left', fill='both', expand=True)
        
        # Header com ícone
        header = Frame(card_content, bg=self.style.BG_CARD)
        header.pack(fill='x')
        
        Label(
            header,
            text=icon,
            font=('Segoe UI', 18),
            bg=self.style.BG_CARD,
            fg=cor_accent
        ).pack(side='left')
        
        Label(
            header,
            text=titulo,
            font=self.style.FONT_SMALL,
            bg=self.style.BG_CARD,
            fg=self.style.TEXT_SECONDARY
        ).pack(side='left', padx=(8, 0))
        
        # Valor principal
        Label(
            card_content,
            text=valor,
            font=self.style.FONT_CARD_VALUE,
            bg=self.style.BG_CARD,
            fg=self.style.TEXT_PRIMARY
        ).pack(anchor='w', pady=(8, 2))
        
        # Subtítulo
        if subtitulo:
            Label(
                card_content,
                text=subtitulo,
                font=self.style.FONT_TINY,
                bg=self.style.BG_CARD,
                fg=self.style.TEXT_MUTED
            ).pack(anchor='w')

    def _criar_secao_series_moderna(self, parent: Frame, series_data: List[Dict], row: int, col: int):
        """Renderiza a seção de desempenho por série com visual moderno."""
        # Container da seção
        sec_frame = Frame(parent, bg=self.style.BG_CARD, padx=15, pady=15)
        sec_frame.grid(row=row, column=col, padx=(0, 10), pady=5, sticky='nsew')
        
        # Header da seção
        header_frame = Frame(sec_frame, bg=self.style.BG_CARD)
        header_frame.pack(fill='x', pady=(0, 15))
        
        Label(
            header_frame,
            text="📚",
            font=('Segoe UI', 16),
            bg=self.style.BG_CARD,
            fg=self.style.ACCENT_PURPLE
        ).pack(side='left')
        
        Label(
            header_frame,
            text="Desempenho por Série",
            font=self.style.FONT_SUBTITLE,
            bg=self.style.BG_CARD,
            fg=self.style.TEXT_PRIMARY
        ).pack(side='left', padx=(8, 0))
        
        # Lista de séries com barras de progresso
        if series_data:
            max_media = max((float(s.get('media') or s[1] or 0) if isinstance(s, dict) else float(s[1] or 0)) for s in series_data) or 10
            
            for row_data in series_data:
                if isinstance(row_data, dict):
                    serie = row_data.get('serie', 'N/A')
                    media = float(row_data.get('media') or 0)
                    total = row_data.get('total_alunos', 0)
                else:
                    serie, media, total = row_data[0], float(row_data[1] or 0), row_data[2]
                
                self._criar_barra_metrica(sec_frame, serie, media, max_media, f"{total} alunos")
        else:
            Label(
                sec_frame,
                text="Nenhum dado disponível",
                font=self.style.FONT_BODY,
                bg=self.style.BG_CARD,
                fg=self.style.TEXT_MUTED
            ).pack(pady=20)

    def _criar_secao_disciplinas_moderna(self, parent: Frame, medias: List[Dict], row: int, col: int):
        """Renderiza a seção de desempenho por disciplina com visual moderno."""
        # Container da seção
        sec_frame = Frame(parent, bg=self.style.BG_CARD, padx=15, pady=15)
        sec_frame.grid(row=row, column=col, padx=(10, 0), pady=5, sticky='nsew')
        
        # Header da seção
        header_frame = Frame(sec_frame, bg=self.style.BG_CARD)
        header_frame.pack(fill='x', pady=(0, 15))
        
        Label(
            header_frame,
            text="📌",
            font=('Segoe UI', 16),
            bg=self.style.BG_CARD,
            fg=self.style.ACCENT_BLUE
        ).pack(side='left')
        
        Label(
            header_frame,
            text="Desempenho por Disciplina",
            font=self.style.FONT_SUBTITLE,
            bg=self.style.BG_CARD,
            fg=self.style.TEXT_PRIMARY
        ).pack(side='left', padx=(8, 0))
        
        # Lista de disciplinas (top 8)
        if medias:
            max_media = max((float(d.get('media') or d[1] or 0) if isinstance(d, dict) else float(d[1] or 0)) for d in medias[:8]) or 10
            
            for row_data in medias[:8]:
                if isinstance(row_data, dict):
                    disc = row_data.get('disciplina', 'N/A')
                    media = float(row_data.get('media') or 0)
                    total = row_data.get('total_alunos', 0)
                else:
                    disc, media, total = row_data[0], float(row_data[1] or 0), row_data[2]
                
                # Truncar nome da disciplina se muito longo
                disc_display = disc[:25] + "..." if len(disc) > 25 else disc
                self._criar_barra_metrica(sec_frame, disc_display, media, max_media, f"{total} alunos", cor=self.style.ACCENT_BLUE)
        else:
            Label(
                sec_frame,
                text="Nenhum dado disponível",
                font=self.style.FONT_BODY,
                bg=self.style.BG_CARD,
                fg=self.style.TEXT_MUTED
            ).pack(pady=20)

    def _criar_barra_metrica(self, parent: Frame, label: str, valor: float, max_valor: float, 
                             info_extra: str = "", cor: Optional[str] = None):
        """Cria uma barra de métrica visual moderna."""
        if cor is None:
            # Cor baseada no valor (assumindo escala de notas 0-10)
            if valor >= 7:
                cor = self.style.ACCENT_GREEN
            elif valor >= 5:
                cor = self.style.ACCENT_YELLOW
            else:
                cor = self.style.ACCENT_RED
        
        item_frame = Frame(parent, bg=self.style.BG_CARD)
        item_frame.pack(fill='x', pady=4)
        
        # Linha superior: label e valor
        top_frame = Frame(item_frame, bg=self.style.BG_CARD)
        top_frame.pack(fill='x')
        
        Label(
            top_frame,
            text=label,
            font=self.style.FONT_SMALL,
            bg=self.style.BG_CARD,
            fg=self.style.TEXT_PRIMARY,
            anchor='w'
        ).pack(side='left')
        
        Label(
            top_frame,
            text=f"{valor:.1f}",
            font=self.style.FONT_HEADING,
            bg=self.style.BG_CARD,
            fg=cor
        ).pack(side='right')
        
        # Barra de progresso visual
        bar_bg = Frame(item_frame, bg=self.style.BORDER, height=6)
        bar_bg.pack(fill='x', pady=(2, 0))
        
        # Calcular largura da barra (proporção do máximo)
        percentual = min((valor / max_valor) * 100 if max_valor > 0 else 0, 100)
        
        bar_fill = Frame(bar_bg, bg=cor, height=6)
        bar_fill.place(relwidth=percentual/100, relheight=1)
        
        # Info extra
        if info_extra:
            Label(
                item_frame,
                text=info_extra,
                font=self.style.FONT_TINY,
                bg=self.style.BG_CARD,
                fg=self.style.TEXT_MUTED
            ).pack(anchor='e')

    def _criar_secao_alertas_moderna(self, parent: Frame, dados: Dict):
        """Renderiza a seção de alertas com visual moderno."""
        alertas_container = Frame(parent, bg=self.co_bg)
        alertas_container.pack(fill='x', pady=(20, 0))
        alertas_container.grid_columnconfigure(0, weight=1)
        alertas_container.grid_columnconfigure(1, weight=1)
        
        # Card de Baixo Desempenho
        baixo_desemp_frame = Frame(alertas_container, bg=self.style.BG_CARD, padx=15, pady=15)
        baixo_desemp_frame.grid(row=0, column=0, padx=(0, 10), pady=5, sticky='nsew')
        
        # Header com badge vermelho
        header_bd = Frame(baixo_desemp_frame, bg=self.style.BG_CARD)
        header_bd.pack(fill='x', pady=(0, 12))
        
        Label(
            header_bd,
            text="📉",
            font=('Segoe UI', 16),
            bg=self.style.BG_CARD,
            fg=self.style.ACCENT_RED
        ).pack(side='left')
        
        Label(
            header_bd,
            text="Baixo Desempenho",
            font=self.style.FONT_SUBTITLE,
            bg=self.style.BG_CARD,
            fg=self.style.TEXT_PRIMARY
        ).pack(side='left', padx=(8, 0))
        
        # Badge com contagem
        alunos_baixo = dados.get('alunos_baixo_desempenho', [])
        badge_bd = Frame(header_bd, bg=self.style.ACCENT_RED, padx=8, pady=2)
        badge_bd.pack(side='right')
        Label(
            badge_bd,
            text=str(len(alunos_baixo)),
            font=self.style.FONT_SMALL,
            bg=self.style.ACCENT_RED,
            fg='white'
        ).pack()
        
        # Subtítulo explicativo
        Label(
            baixo_desemp_frame,
            text="Alunos com média inferior a 6.0",
            font=self.style.FONT_TINY,
            bg=self.style.BG_CARD,
            fg=self.style.TEXT_MUTED
        ).pack(anchor='w', pady=(0, 10))
        
        # Lista de alunos
        if alunos_baixo:
            for aluno in alunos_baixo[:8]:
                nome = aluno['aluno'] if isinstance(aluno, dict) else aluno[0]
                serie = aluno['serie'] if isinstance(aluno, dict) else aluno[1]
                turma = aluno['turma'] if isinstance(aluno, dict) else aluno[2]
                media = aluno['media_geral'] if isinstance(aluno, dict) else aluno[3]
                
                self._criar_item_alerta(baixo_desemp_frame, nome, f"{serie} {turma}", f"Média: {media:.1f}", self.style.ACCENT_RED)
        else:
            self._criar_mensagem_vazia(baixo_desemp_frame, "✅ Nenhum aluno nesta situação")
        
        # Card de Baixa Frequência
        baixa_freq_frame = Frame(alertas_container, bg=self.style.BG_CARD, padx=15, pady=15)
        baixa_freq_frame.grid(row=0, column=1, padx=(10, 0), pady=5, sticky='nsew')
        
        # Header com badge amarelo
        header_bf = Frame(baixa_freq_frame, bg=self.style.BG_CARD)
        header_bf.pack(fill='x', pady=(0, 12))
        
        Label(
            header_bf,
            text="📅",
            font=('Segoe UI', 16),
            bg=self.style.BG_CARD,
            fg=self.style.ACCENT_YELLOW
        ).pack(side='left')
        
        Label(
            header_bf,
            text="Excesso de Faltas",
            font=self.style.FONT_SUBTITLE,
            bg=self.style.BG_CARD,
            fg=self.style.TEXT_PRIMARY
        ).pack(side='left', padx=(8, 0))
        
        alunos_freq = dados.get('alunos_baixa_frequencia', [])
        badge_bf = Frame(header_bf, bg=self.style.ACCENT_YELLOW, padx=8, pady=2)
        badge_bf.pack(side='right')
        Label(
            badge_bf,
            text=str(len(alunos_freq)),
            font=self.style.FONT_SMALL,
            bg=self.style.ACCENT_YELLOW,
            fg=self.style.BG_DARK
        ).pack()
        
        # Subtítulo
        Label(
            baixa_freq_frame,
            text="Alunos com mais de 40 faltas",
            font=self.style.FONT_TINY,
            bg=self.style.BG_CARD,
            fg=self.style.TEXT_MUTED
        ).pack(anchor='w', pady=(0, 10))
        
        # Lista de alunos
        if alunos_freq:
            for aluno in alunos_freq[:8]:
                nome = aluno['aluno'] if isinstance(aluno, dict) else aluno[0]
                serie = aluno['serie'] if isinstance(aluno, dict) else aluno[1]
                turma = aluno['turma'] if isinstance(aluno, dict) else aluno[2]
                faltas = aluno['total_faltas'] if isinstance(aluno, dict) else aluno[3]
                
                self._criar_item_alerta(baixa_freq_frame, nome, f"{serie} {turma}", f"{int(faltas)} faltas", self.style.ACCENT_YELLOW)
        else:
            self._criar_mensagem_vazia(baixa_freq_frame, "✅ Nenhum aluno nesta situação")

    def _criar_item_alerta(self, parent: Frame, nome: str, local: str, info: str, cor: str):
        """Cria um item de alerta individual."""
        item = Frame(parent, bg=self.style.BG_CARD_HOVER, padx=10, pady=6)
        item.pack(fill='x', pady=2)
        
        # Indicador colorido
        indicator = Frame(item, bg=cor, width=3)
        indicator.pack(side='left', fill='y', padx=(0, 10))
        
        # Conteúdo
        content = Frame(item, bg=self.style.BG_CARD_HOVER)
        content.pack(side='left', fill='x', expand=True)
        
        # Nome do aluno (truncado)
        nome_display = nome[:22] + "..." if len(nome) > 22 else nome
        Label(
            content,
            text=nome_display,
            font=self.style.FONT_SMALL,
            bg=self.style.BG_CARD_HOVER,
            fg=self.style.TEXT_PRIMARY,
            anchor='w'
        ).pack(anchor='w')
        
        # Local (série e turma)
        Label(
            content,
            text=local,
            font=self.style.FONT_TINY,
            bg=self.style.BG_CARD_HOVER,
            fg=self.style.TEXT_MUTED,
            anchor='w'
        ).pack(anchor='w')
        
        # Info (média ou faltas)
        Label(
            item,
            text=info,
            font=self.style.FONT_SMALL,
            bg=self.style.BG_CARD_HOVER,
            fg=cor
        ).pack(side='right')

    def _criar_mensagem_vazia(self, parent: Frame, mensagem: str):
        """Cria uma mensagem para quando não há dados."""
        empty_frame = Frame(parent, bg=self.style.BG_CARD_HOVER, padx=15, pady=20)
        empty_frame.pack(fill='x', pady=5)
        
        Label(
            empty_frame,
            text=mensagem,
            font=self.style.FONT_BODY,
            bg=self.style.BG_CARD_HOVER,
            fg=self.style.ACCENT_GREEN
        ).pack()

    def _criar_secao_pendencias_moderna(self, parent: Frame, pendencias: List[Dict]):
        """Renderiza a seção de pendências de notas com visual moderno."""
        pend_frame = Frame(parent, bg=self.style.BG_CARD, padx=15, pady=15)
        pend_frame.pack(fill='x', pady=(20, 10))
        
        # Header
        header = Frame(pend_frame, bg=self.style.BG_CARD)
        header.pack(fill='x', pady=(0, 12))
        
        Label(
            header,
            text="📝",
            font=('Segoe UI', 16),
            bg=self.style.BG_CARD,
            fg=self.style.ACCENT_CYAN
        ).pack(side='left')
        
        Label(
            header,
            text="Notas Pendentes",
            font=self.style.FONT_SUBTITLE,
            bg=self.style.BG_CARD,
            fg=self.style.TEXT_PRIMARY
        ).pack(side='left', padx=(8, 0))
        
        # Badge com total
        badge = Frame(header, bg=self.style.ACCENT_CYAN, padx=8, pady=2)
        badge.pack(side='right')
        Label(
            badge,
            text=f"{len(pendencias)} registros",
            font=self.style.FONT_SMALL,
            bg=self.style.ACCENT_CYAN,
            fg=self.style.BG_DARK
        ).pack()
        
        # Subtítulo
        Label(
            pend_frame,
            text="Turmas com alunos sem notas lançadas",
            font=self.style.FONT_TINY,
            bg=self.style.BG_CARD,
            fg=self.style.TEXT_MUTED
        ).pack(anchor='w', pady=(0, 10))
        
        # Grid de pendências
        grid_frame = Frame(pend_frame, bg=self.style.BG_CARD)
        grid_frame.pack(fill='x')
        
        # Criar duas colunas
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
        
        for idx, pend in enumerate(pendencias[:10]):
            serie = pend['serie'] if isinstance(pend, dict) else pend[0]
            turma = pend['turma'] if isinstance(pend, dict) else pend[1]
            disc = pend['disciplina'] if isinstance(pend, dict) else pend[2]
            qtd = pend['alunos_sem_nota'] if isinstance(pend, dict) else pend[3]
            
            item = Frame(grid_frame, bg=self.style.BG_CARD_HOVER, padx=10, pady=6)
            item.grid(row=idx // 2, column=idx % 2, padx=3, pady=2, sticky='ew')
            
            # Truncar disciplina se necessário
            disc_display = disc[:18] + "..." if len(disc) > 18 else disc
            
            Label(
                item,
                text=f"{serie} {turma}",
                font=self.style.FONT_SMALL,
                bg=self.style.BG_CARD_HOVER,
                fg=self.style.TEXT_PRIMARY
            ).pack(anchor='w')
            
            info_frame = Frame(item, bg=self.style.BG_CARD_HOVER)
            info_frame.pack(fill='x')
            
            Label(
                info_frame,
                text=disc_display,
                font=self.style.FONT_TINY,
                bg=self.style.BG_CARD_HOVER,
                fg=self.style.TEXT_MUTED
            ).pack(side='left')
            
            Label(
                info_frame,
                text=f"{qtd} alunos",
                font=self.style.FONT_TINY,
                bg=self.style.BG_CARD_HOVER,
                fg=self.style.ACCENT_CYAN
            ).pack(side='right')


# Funções auxiliares para criação rápida de dashboards por tipo
def criar_dashboard_series_iniciais(janela, db_service, frame_getter, escola_id: int = 60,
                                    ano_letivo: Optional[str] = None) -> DashboardCoordenador:
    """
    Cria um dashboard configurado para coordenador de séries iniciais (1º ao 5º Ano).
    
    Args:
        janela: Janela principal Tk
        db_service: Serviço de banco de dados
        frame_getter: Função que retorna o frame onde o dashboard será renderizado
        escola_id: ID da escola
        ano_letivo: Ano letivo atual
        
    Returns:
        Instância de DashboardCoordenador configurada para séries iniciais
    """
    return DashboardCoordenador(
        janela=janela,
        db_service=db_service,
        frame_getter=frame_getter,
        escola_id=escola_id,
        ano_letivo=ano_letivo,
        tipo_coordenacao='iniciais'
    )


def criar_dashboard_series_finais(janela, db_service, frame_getter, escola_id: int = 60,
                                  ano_letivo: Optional[str] = None) -> DashboardCoordenador:
    """
    Cria um dashboard configurado para coordenador de séries finais (6º ao 9º Ano).
    
    Args:
        janela: Janela principal Tk
        db_service: Serviço de banco de dados
        frame_getter: Função que retorna o frame onde o dashboard será renderizado
        escola_id: ID da escola
        ano_letivo: Ano letivo atual
        
    Returns:
        Instância de DashboardCoordenador configurada para séries finais
    """
    return DashboardCoordenador(
        janela=janela,
        db_service=db_service,
        frame_getter=frame_getter,
        escola_id=escola_id,
        ano_letivo=ano_letivo,
        tipo_coordenacao='finais'
    )
