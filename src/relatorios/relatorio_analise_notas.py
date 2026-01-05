from src.core.config_logs import get_logger
logger = get_logger(__name__)
"""
Relatório Estatístico de Análise de Notas
Gera análises detalhadas com gráficos, pendências e estatísticas
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont
from src.core.conexao import conectar_bd
from src.core.config import ANO_LETIVO_ATUAL
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime
from typing import Any, cast

class RelatorioAnaliseNotas:
    def __init__(self, root=None, janela_principal=None):
        """Inicializa a interface de relatório de análise de notas"""
        self.janela_principal = janela_principal
        
        # Se root for None, cria uma nova janela
        if root is None:
            self.janela = tk.Toplevel()
            self.janela.title("Relatório Estatístico de Análise de Notas")
            self.janela.geometry("1200x800")
            self.janela.grab_set()
            self.janela.focus_force()
            
            # Configurar evento de fechamento
            self.janela.protocol("WM_DELETE_WINDOW", self.ao_fechar_janela)
        else:
            self.janela = root
        
        # Cores (mesmas do sistema)
        self.co0 = "#F5F5F5"  # Branco suave
        self.co1 = "#003A70"  # Azul escuro
        self.co2 = "#77B341"  # Verde
        self.co3 = "#E2418E"  # Rosa/Magenta
        self.co4 = "#4A86E8"  # Azul claro
        self.co7 = "#333333"  # Cinza escuro
        self.co8 = "#BF3036"  # Vermelho
        
        self.janela.configure(bg=self.co0)
        
        # Obter ano letivo atual
        # Inicializar dados para satisfazer o analisador estático
        self.dados: dict = {}

        self.ano_letivo_atual = self.obter_ano_letivo_atual()
        
        if self.ano_letivo_atual:
            self.criar_interface()
        else:
            messagebox.showerror("Erro", "Não foi possível obter o ano letivo.")
            self.janela.destroy()
    
    def obter_ano_letivo_atual(self):
        """
        Obtém o ID do ano letivo atual.
        Usa a configuração ANO_LETIVO_ATUAL e verifica se ainda está ativo.
        """
        try:
            conn: Any = conectar_bd()
            cursor = cast(Any, conn).cursor()
            
            # Primeiro, busca o ano letivo configurado
            cursor.execute("SELECT id, data_fim FROM anosletivos WHERE ano_letivo = %s", (ANO_LETIVO_ATUAL,))
            resultado = cursor.fetchone()
            
            # Se encontrou, verifica se ainda está ativo
            if resultado:
                ano_id = resultado[0]
                data_fim = resultado[1]
                
                # Se não tem data_fim OU se ainda não passou, usa este ano
                if data_fim is None:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()
                    return ano_id
                
                cursor.execute("SELECT CURDATE() <= %s as ainda_ativo", (data_fim,))
                ainda_ativo = cursor.fetchone()
                if ainda_ativo and ainda_ativo[0]:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()
                    return ano_id
            
            # Se o ano configurado já encerrou, busca o próximo ano ativo
            cursor.execute("""
                SELECT id FROM anosletivos 
                WHERE CURDATE() BETWEEN data_inicio AND data_fim
                ORDER BY ano_letivo DESC 
                LIMIT 1
            """)
            resultado = cursor.fetchone()
            
            # Fallback: ano letivo mais recente
            if not resultado:
                cursor.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                resultado = cursor.fetchone()
            
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            
            return resultado[0] if resultado else None
            
        except Exception as e:
            logger.error(f"Erro ao obter ano letivo: {e}")
            return None
    
    def criar_interface(self):
        """Cria a interface gráfica"""
        # Frame superior - Título
        frame_titulo = tk.Frame(self.janela, bg=self.co1, height=60)
        frame_titulo.pack(fill="x", side="top")
        frame_titulo.pack_propagate(False)
        
        tk.Label(
            frame_titulo,
            text="📊 Relatório Estatístico de Análise de Notas",
            font=("Arial", 16, "bold"),
            bg=self.co1,
            fg="white"
        ).pack(pady=15)
        
        # Frame de seleção
        frame_selecao = tk.LabelFrame(
            self.janela,
            text="Filtros de Busca",
            font=("Arial", 11, "bold"),
            bg=self.co0,
            fg=self.co1
        )
        frame_selecao.pack(fill="x", padx=10, pady=10)
        
        # Grid de seleções
        frame_grid = tk.Frame(frame_selecao, bg=self.co0)
        frame_grid.pack(fill="x", padx=10, pady=10)
        
        for i in range(4):
            frame_grid.columnconfigure(i, weight=1)
        
        # Nível de Ensino
        tk.Label(frame_grid, text="Nível:", bg=self.co0, font=("Arial", 10)).grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.cb_nivel = ttk.Combobox(frame_grid, width=25, state="readonly")
        self.cb_nivel.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.cb_nivel.bind("<<ComboboxSelected>>", self.carregar_series)
        
        # Série
        tk.Label(frame_grid, text="Série:", bg=self.co0, font=("Arial", 10)).grid(
            row=0, column=1, padx=5, pady=5, sticky="w"
        )
        self.cb_serie = ttk.Combobox(frame_grid, width=25, state="readonly")
        self.cb_serie.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.cb_serie.bind("<<ComboboxSelected>>", self.carregar_turmas)
        
        # Turma
        tk.Label(frame_grid, text="Turma:", bg=self.co0, font=("Arial", 10)).grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        self.cb_turma = ttk.Combobox(frame_grid, width=25, state="readonly")
        self.cb_turma.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        
        # Bimestre
        tk.Label(frame_grid, text="Bimestre:", bg=self.co0, font=("Arial", 10)).grid(
            row=0, column=3, padx=5, pady=5, sticky="w"
        )
        self.cb_bimestre = ttk.Combobox(
            frame_grid,
            width=15,
            state="readonly",
            values=["Todos", "1º bimestre", "2º bimestre", "3º bimestre", "4º bimestre"]
        )
        self.cb_bimestre.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        self.cb_bimestre.current(0)
        
        # Botão gerar relatório
        tk.Button(
            frame_selecao,
            text="🔍 Gerar Relatório",
            command=self.gerar_relatorio,
            bg=self.co2,
            fg="white",
            font=("Arial", 11, "bold"),
            height=2,
            cursor="hand2"
        ).pack(pady=10, padx=10, fill="x")
        
        # Frame principal - Notebook com abas
        self.notebook = ttk.Notebook(self.janela)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Aba 1: Visão Geral
        self.aba_visao_geral = tk.Frame(self.notebook, bg=self.co0)
        self.notebook.add(self.aba_visao_geral, text="📊 Visão Geral")
        
        # Aba 2: Análise por Disciplina
        self.aba_disciplinas = tk.Frame(self.notebook, bg=self.co0)
        self.notebook.add(self.aba_disciplinas, text="📚 Por Disciplina")
        
        # Aba 3: Pendências
        self.aba_pendencias = tk.Frame(self.notebook, bg=self.co0)
        self.notebook.add(self.aba_pendencias, text="⚠️ Pendências")
        
        # Aba 4: Ranking
        self.aba_ranking = tk.Frame(self.notebook, bg=self.co0)
        self.notebook.add(self.aba_ranking, text="🏆 Rankings")
        
        # Carregar dados iniciais
        self.carregar_niveis()
    
    def carregar_niveis(self):
        """Carrega níveis de ensino"""
        try:
            conn: Any = conectar_bd()
            cursor = cast(Any, conn).cursor()
            cursor.execute("SELECT id, nome FROM niveisensino ORDER BY nome")
            niveis = cursor.fetchall()
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            
            self.niveis_map = {nivel[1]: nivel[0] for nivel in niveis}
            self.cb_nivel['values'] = list(self.niveis_map.keys())
            
            if self.cb_nivel['values']:
                self.cb_nivel.current(0)
                self.carregar_series()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar níveis: {e}")
    
    def carregar_series(self, event=None):
        """Carrega séries do nível selecionado"""
        if not self.cb_nivel.get():
            return
        
        nivel_id = self.niveis_map.get(self.cb_nivel.get())
        
        try:
            conn: Any = conectar_bd()
            cursor = cast(Any, conn).cursor()
            cursor.execute(
                "SELECT id, nome FROM series WHERE nivel_id = %s ORDER BY nome",
                (nivel_id,)
            )
            series = cursor.fetchall()
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            
            self.series_map = {serie[1]: serie[0] for serie in series}
            self.cb_serie['values'] = list(self.series_map.keys())
            
            if self.cb_serie['values']:
                self.cb_serie.current(0)
                self.carregar_turmas()
            else:
                self.cb_serie.set("")
                self.cb_turma.set("")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar séries: {e}")
    
    def carregar_turmas(self, event=None):
        """Carrega turmas da série selecionada"""
        if not self.cb_serie.get():
            return
        
        serie_id = self.series_map.get(self.cb_serie.get())
        
        try:
            conn: Any = conectar_bd()
            cursor = cast(Any, conn).cursor()
            cursor.execute("""
                SELECT t.id, CONCAT(t.nome, ' - ', t.turno) AS turma_nome 
                FROM turmas t 
                WHERE t.serie_id = %s AND t.ano_letivo_id = %s
                ORDER BY t.nome
            """, (serie_id, self.ano_letivo_atual))
            turmas = cursor.fetchall()
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            
            self.turmas_map = {turma[1]: turma[0] for turma in turmas}
            self.cb_turma['values'] = ["Todas"] + list(self.turmas_map.keys())
            
            if self.cb_turma['values']:
                self.cb_turma.current(0)
            else:
                self.cb_turma.set("")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar turmas: {e}")
    
    def gerar_relatorio(self):
        """Gera o relatório completo"""
        # Validações
        if not self.cb_nivel.get():
            messagebox.showwarning("Aviso", "Selecione um nível de ensino!")
            return
        
        if not self.cb_serie.get():
            messagebox.showwarning("Aviso", "Selecione uma série!")
            return
        
        if not self.cb_turma.get():
            messagebox.showwarning("Aviso", "Selecione uma turma!")
            return
        
        # Buscar dados (atribuir apenas se houver resultado válido)
        _dados = self.buscar_dados_relatorio()
        if not _dados or not _dados.get('notas'):
            messagebox.showinfo("Informação", "Não há dados de notas para os filtros selecionados.")
            return
        self.dados = _dados
        
        # Gerar cada aba
        self.gerar_visao_geral()
        self.gerar_analise_disciplinas()
        self.gerar_pendencias()
        self.gerar_rankings()
        
        messagebox.showinfo("Sucesso", "Relatório gerado com sucesso!")
    
    def buscar_dados_relatorio(self):
        """Busca todos os dados necessários para o relatório"""
        try:
            conn: Any = conectar_bd()
            cursor = cast(Any, conn).cursor()
            
            # Montar filtros
            serie_id = self.series_map.get(self.cb_serie.get())
            turma_selecionada = self.cb_turma.get()
            bimestre_selecionado = self.cb_bimestre.get()
            
            # Query base
            query = """
                SELECT 
                    a.id as aluno_id,
                    a.nome as aluno_nome,
                    d.id as disciplina_id,
                    d.nome as disciplina_nome,
                    n.bimestre,
                    n.nota,
                    t.id as turma_id,
                    CONCAT(t.nome, ' - ', t.turno) as turma_nome
                FROM notas n
                JOIN alunos a ON n.aluno_id = a.id
                JOIN disciplinas d ON n.disciplina_id = d.id
                JOIN matriculas m ON a.id = m.aluno_id
                JOIN turmas t ON m.turma_id = t.id
                WHERE t.serie_id = %s 
                AND n.ano_letivo_id = %s
                AND m.ano_letivo_id = %s
                AND m.status IN ('Ativo', 'Transferido')
            """
            
            params = [serie_id, self.ano_letivo_atual, self.ano_letivo_atual]
            
            # Filtro de turma
            if turma_selecionada != "Todas":
                turma_id = self.turmas_map.get(turma_selecionada)
                query += " AND t.id = %s"
                params.append(turma_id)
            
            # Filtro de bimestre
            if bimestre_selecionado != "Todos":
                query += " AND n.bimestre = %s"
                params.append(bimestre_selecionado)
            
            query += " ORDER BY a.nome, d.nome, n.bimestre"
            
            cursor.execute(query, params)
            notas = cursor.fetchall()
            
            # Buscar TODAS as combinações aluno-disciplina (igual ao relatorio_pendencias.py)
            # Depois processamos no Python para identificar pendências
            query_pendencias = """
                SELECT 
                    a.id as aluno_id,
                    a.nome as aluno_nome,
                    t.id as turma_id,
                    CONCAT(t.nome, ' - ', t.turno) as turma_nome,
                    d.id as disciplina_id,
                    d.nome as disciplina_nome,
                    n.nota
                FROM alunos a
                JOIN matriculas m ON a.id = m.aluno_id
                JOIN turmas t ON m.turma_id = t.id
                JOIN series s ON t.serie_id = s.id
                CROSS JOIN disciplinas d
                LEFT JOIN notas n ON a.id = n.aluno_id 
                    AND d.id = n.disciplina_id 
            """
            
            params_pend = []
            
            # Adicionar filtro de bimestre no LEFT JOIN se necessário
            if bimestre_selecionado != "Todos":
                query_pendencias += " AND n.bimestre = %s"
                params_pend.append(bimestre_selecionado)
            
            query_pendencias += " AND n.ano_letivo_id = %s"
            params_pend.append(self.ano_letivo_atual)
            
            # Adicionar WHERE para filtros
            query_pendencias += """
                WHERE t.serie_id = %s
                AND m.ano_letivo_id = %s
                AND m.status = 'Ativo'
                AND a.escola_id = 60
                AND d.escola_id = 60
                AND d.nivel_id = s.nivel_id
            """
            params_pend.extend([serie_id, self.ano_letivo_atual])
            
            # Filtro de turma para pendências
            if turma_selecionada != "Todas":
                turma_id = self.turmas_map.get(turma_selecionada)
                query_pendencias += " AND t.id = %s"
                params_pend.append(turma_id)
            
            query_pendencias += " ORDER BY a.nome, d.nome"
            
            cursor.execute(query_pendencias, params_pend)
            dados_completos = cursor.fetchall()
            
            # Processar pendências no Python (igual ao relatorio_pendencias.py)
            # Mostrar TODAS as pendências (inclusive alunos sem nenhuma nota)
            pendencias = []
            for registro in dados_completos:
                # Se nota é None, é pendência
                if registro[6] is None:  # nota
                    pendencias.append(registro)
            
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            
            return {
                'notas': notas,
                'pendencias': pendencias
            }
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar dados: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def gerar_visao_geral(self):
        """Gera a aba de visão geral com estatísticas e gráficos"""
        if not getattr(self, 'dados', None):
            return
        # Limpar aba
        for widget in self.aba_visao_geral.winfo_children():
            widget.destroy()
        
        # Frame superior com estatísticas gerais
        frame_stats = tk.LabelFrame(
            self.aba_visao_geral,
            text="Estatísticas Gerais",
            font=("Arial", 10, "bold"),
            bg=self.co0
        )
        frame_stats.pack(fill="x", padx=10, pady=5)
        
        # Calcular estatísticas
        notas = [float(n[5]) for n in self.dados['notas'] if n[5] is not None]
        
        if notas:
            # Calcular média por aluno para determinar aprovados/reprovados
            alunos_medias = {}
            for nota in self.dados['notas']:
                aluno_id = nota[0]
                nota_valor = float(nota[5]) if nota[5] is not None else None
                
                if aluno_id not in alunos_medias:
                    alunos_medias[aluno_id] = []
                
                if nota_valor is not None:
                    alunos_medias[aluno_id].append(nota_valor)
            
            # Calcular quantos alunos estão aprovados/reprovados
            aprovados = 0
            reprovados = 0
            for aluno_id, notas_aluno in alunos_medias.items():
                if notas_aluno:
                    media_aluno = np.mean(notas_aluno)
                    if media_aluno >= 60:
                        aprovados += 1
                    else:
                        reprovados += 1
            
            # Forçar tipos float para satisfazer o analisador estático
            media_geral = float(np.mean(notas))
            maior_nota = float(np.max(notas))
            menor_nota = float(np.min(notas))
            desvio_padrao = float(np.std(notas))

            stats = {
                'total_notas': len(notas),
                'media_geral': media_geral,
                'maior_nota': maior_nota,
                'menor_nota': menor_nota,
                'desvio_padrao': desvio_padrao,
                'aprovados': aprovados,
                'reprovados': reprovados,
                'notas_vazias': len(self.dados['pendencias']),
                'total_alunos': len(alunos_medias)
            }
            
            # Grid de estatísticas
            frame_grid = tk.Frame(frame_stats, bg=self.co0)
            frame_grid.pack(fill="x", padx=5, pady=5)
            
            for i in range(4):
                frame_grid.columnconfigure(i, weight=1)
            
            # Criar cards de estatísticas
            self.criar_card_stat(frame_grid, "� Total de Alunos", stats['total_alunos'], 0, 0, self.co1)
            self.criar_card_stat(frame_grid, "�📝 Total de Notas", stats['total_notas'], 0, 1)
            self.criar_card_stat(frame_grid, "📊 Média Geral", f"{stats['media_geral']:.1f}", 0, 2, 
                               self.co2 if stats['media_geral'] >= 60 else self.co8)
            self.criar_card_stat(frame_grid, "📉 Desvio Padrão", f"{stats['desvio_padrao']:.2f}", 0, 3)
            
            self.criar_card_stat(frame_grid, "✅ Alunos Aprovados", stats['aprovados'], 1, 0, self.co2)
            self.criar_card_stat(frame_grid, "❌ Alunos Reprovados", stats['reprovados'], 1, 1, self.co8)
            self.criar_card_stat(frame_grid, "⬆️ Maior Nota", f"{stats['maior_nota']:.1f}", 1, 2)
            self.criar_card_stat(frame_grid, "⬇️ Menor Nota", f"{stats['menor_nota']:.1f}", 1, 3)
            
            # Terceira linha com pendências
            self.criar_card_stat(frame_grid, "⚠️ Notas Pendentes", stats['notas_vazias'], 2, 0, self.co3)
        
        # Frame de gráficos
        frame_graficos = tk.Frame(self.aba_visao_geral, bg=self.co0)
        frame_graficos.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Criar figura com subplots
        fig = Figure(figsize=(14, 8), facecolor=self.co0)
        
        # Gráfico 1: Histograma de distribuição de notas
        ax1 = fig.add_subplot(121)
        ax1.hist(notas, bins=20, color=self.co4, alpha=0.7, edgecolor='black')
        ax1.axvline(60, color=self.co8, linestyle='--', linewidth=2, label='Média mínima (60)')
        ax1.axvline(stats['media_geral'], color=self.co2, linestyle='--', linewidth=2, label=f'Média da turma ({stats['media_geral']:.1f})')
        ax1.set_xlabel('Notas', fontsize=10)
        ax1.set_ylabel('Frequência', fontsize=10)
        ax1.set_title('Distribuição de Notas', fontsize=12, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Gráfico 2: Pizza de aprovação/reprovação (por ALUNOS)
        ax2 = fig.add_subplot(122)
        labels = [f'Aprovados (≥60)\n{stats["aprovados"]} alunos', 
                  f'Reprovados (<60)\n{stats["reprovados"]} alunos']
        sizes = [stats['aprovados'], stats['reprovados']]
        colors = [self.co2, self.co8]
        explode = (0.1, 0)
        
        ax2.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
               shadow=True, startangle=90)
        ax2.set_title('Taxa de Aprovação por Aluno', fontsize=12, fontweight='bold')
        
        # Adicionar canvas ao frame
        canvas = FigureCanvasTkAgg(fig, frame_graficos)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def criar_card_stat(self, parent, titulo, valor, linha, coluna, cor=None):
        """Cria um card de estatística"""
        cor = cor or self.co4
        
        frame = tk.Frame(parent, bg="white", relief="solid", borderwidth=1)
        frame.grid(row=linha, column=coluna, padx=3, pady=3, sticky="ew")
        
        tk.Label(
            frame,
            text=titulo,
            font=("Arial", 8),
            bg="white",
            fg=self.co7
        ).pack(pady=(5, 2))
        
        tk.Label(
            frame,
            text=str(valor),
            font=("Arial", 14, "bold"),
            bg="white",
            fg=cor
        ).pack(pady=(2, 5))
    
    def gerar_analise_disciplinas(self):
        """Gera análise detalhada por disciplina"""
        if not getattr(self, 'dados', None):
            return
        # Limpar aba
        for widget in self.aba_disciplinas.winfo_children():
            widget.destroy()
        
        # Agrupar notas por disciplina
        disciplinas_dict = {}
        for nota in self.dados['notas']:
            disc_id = nota[2]
            disc_nome = nota[3]
            nota_valor = float(nota[5]) if nota[5] is not None else None
            
            if disc_nome not in disciplinas_dict:
                disciplinas_dict[disc_nome] = []
            
            if nota_valor is not None:
                disciplinas_dict[disc_nome].append(nota_valor)
        
        # Criar scrollable frame
        canvas = tk.Canvas(self.aba_disciplinas, bg=self.co0)
        scrollbar = tk.Scrollbar(self.aba_disciplinas, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.co0)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Criar análise para cada disciplina
        for disc_nome, notas_disc in sorted(disciplinas_dict.items()):
            if notas_disc:
                self.criar_card_disciplina(scrollable_frame, disc_nome, notas_disc)
    
    def criar_card_disciplina(self, parent, disciplina, notas):
        """Cria um card com análise de uma disciplina"""
        # Calcular estatísticas
        media = np.mean(notas)
        maior = np.max(notas)
        menor = np.min(notas)
        aprovados = sum(1 for n in notas if n >= 60)
        reprovados = sum(1 for n in notas if n < 60)
        
        # Frame principal
        frame = tk.LabelFrame(
            parent,
            text=f"📚 {disciplina}",
            font=("Arial", 10, "bold"),
            bg="white",
            fg=self.co1
        )
        frame.pack(fill="x", padx=10, pady=5)
        
        # Frame de estatísticas
        frame_stats = tk.Frame(frame, bg="white")
        frame_stats.pack(fill="x", padx=10, pady=10)
        
        for i in range(5):
            frame_stats.columnconfigure(i, weight=1)
        
        # Labels de estatísticas
        stats_info = [
            ("Média", f"{media:.1f}", self.co2 if media >= 60 else self.co8),
            ("Maior", f"{maior:.1f}", self.co4),
            ("Menor", f"{menor:.1f}", self.co4),
            ("Aprovados", aprovados, self.co2),
            ("Reprovados", reprovados, self.co8)
        ]
        
        for i, (label, valor, cor) in enumerate(stats_info):
            frame_col = tk.Frame(frame_stats, bg="white")
            frame_col.grid(row=0, column=i, padx=5)
            
            tk.Label(
                frame_col,
                text=label,
                font=("Arial", 8),
                bg="white",
                fg=self.co7
            ).pack()
            
            tk.Label(
                frame_col,
                text=str(valor),
                font=("Arial", 12, "bold"),
                bg="white",
                fg=cor
            ).pack()
    
    def gerar_pendencias(self):
        """Gera aba com pendências (notas vazias, abaixo da média, etc.)"""
        # Limpar aba
        for widget in self.aba_pendencias.winfo_children():
            widget.destroy()
        
        # Criar notebook interno
        notebook_pend = ttk.Notebook(self.aba_pendencias)
        notebook_pend.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Sub-aba 1: Notas Vazias
        aba_vazias = tk.Frame(notebook_pend, bg=self.co0)
        notebook_pend.add(aba_vazias, text="📝 Notas Vazias")
        self.criar_lista_pendencias_vazias(aba_vazias)
        
        # Sub-aba 2: Abaixo da Média
        aba_baixas = tk.Frame(notebook_pend, bg=self.co0)
        notebook_pend.add(aba_baixas, text="📉 Abaixo da Média (< 60)")
        self.criar_lista_notas_baixas(aba_baixas)
        
        # Sub-aba 3: Em Recuperação
        aba_recuperacao = tk.Frame(notebook_pend, bg=self.co0)
        notebook_pend.add(aba_recuperacao, text="⚠️ Risco de Reprovação")
        self.criar_lista_risco_reprovacao(aba_recuperacao)
    
    def criar_lista_pendencias_vazias(self, parent):
        """Cria lista de alunos com notas vazias"""
        if not getattr(self, 'dados', None):
            return
        # Frame com scrollbar
        frame = tk.Frame(parent, bg=self.co0)
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Treeview
        colunas = ("aluno", "turma", "disciplina")
        tree = ttk.Treeview(frame, columns=colunas, show="headings", height=20)
        
        tree.heading("aluno", text="Aluno")
        tree.heading("turma", text="Turma")
        tree.heading("disciplina", text="Disciplina")
        
        tree.column("aluno", width=300)
        tree.column("turma", width=150)
        tree.column("disciplina", width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Preencher dados
        for pend in self.dados['pendencias']:
            tree.insert("", "end", values=(pend[1], pend[3], pend[5]))
        
        # Label com total
        tk.Label(
            parent,
            text=f"Total de pendências: {len(self.dados['pendencias'])}",
            font=("Arial", 10, "bold"),
            bg=self.co0,
            fg=self.co8
        ).pack(pady=5)
    
    def criar_lista_notas_baixas(self, parent):
        """Cria lista de alunos com notas abaixo de 60"""
        if not getattr(self, 'dados', None):
            return
        # Frame com scrollbar
        frame = tk.Frame(parent, bg=self.co0)
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Treeview
        colunas = ("aluno", "turma", "disciplina", "bimestre", "nota")
        tree = ttk.Treeview(frame, columns=colunas, show="headings", height=20)
        
        tree.heading("aluno", text="Aluno")
        tree.heading("turma", text="Turma")
        tree.heading("disciplina", text="Disciplina")
        tree.heading("bimestre", text="Bimestre")
        tree.heading("nota", text="Nota")
        
        tree.column("aluno", width=250)
        tree.column("turma", width=120)
        tree.column("disciplina", width=180)
        tree.column("bimestre", width=100)
        tree.column("nota", width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Preencher dados - notas < 60
        count = 0
        for nota in self.dados['notas']:
            if nota[5] is not None and float(nota[5]) < 60:
                tree.insert("", "end", values=(
                    nota[1],  # aluno
                    nota[7],  # turma
                    nota[3],  # disciplina
                    nota[4],  # bimestre
                    f"{float(nota[5]):.1f}"  # nota
                ))
                count += 1
        
        # Label com total
        tk.Label(
            parent,
            text=f"Total de notas abaixo da média: {count}",
            font=("Arial", 10, "bold"),
            bg=self.co0,
            fg=self.co8
        ).pack(pady=5)
    
    def criar_lista_risco_reprovacao(self, parent):
        """Cria lista de alunos em risco de reprovação (múltiplas notas baixas)"""
        if not getattr(self, 'dados', None):
            return
        # Frame com scrollbar
        frame = tk.Frame(parent, bg=self.co0)
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Treeview
        colunas = ("aluno", "turma", "disciplinas_risco", "media_geral")
        tree = ttk.Treeview(frame, columns=colunas, show="headings", height=20)
        
        tree.heading("aluno", text="Aluno")
        tree.heading("turma", text="Turma")
        tree.heading("disciplinas_risco", text="Disciplinas em Risco")
        tree.heading("media_geral", text="Média Geral")
        
        tree.column("aluno", width=300)
        tree.column("turma", width=150)
        tree.column("disciplinas_risco", width=100, anchor="center")
        tree.column("media_geral", width=100, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Agrupar por aluno
        alunos_dict = {}
        for nota in self.dados['notas']:
            aluno_id = nota[0]
            aluno_nome = nota[1]
            turma_nome = nota[7]
            nota_valor = float(nota[5]) if nota[5] is not None else None
            
            if aluno_id not in alunos_dict:
                alunos_dict[aluno_id] = {
                    'nome': aluno_nome,
                    'turma': turma_nome,
                    'notas': [],
                    'disc_risco': 0
                }
            
            if nota_valor is not None:
                alunos_dict[aluno_id]['notas'].append(nota_valor)
                if nota_valor < 60:
                    alunos_dict[aluno_id]['disc_risco'] += 1
        
        # Filtrar alunos com 2 ou mais disciplinas em risco
        count = 0
        for aluno_id, dados in alunos_dict.items():
            if dados['disc_risco'] >= 2:
                media_geral = np.mean(dados['notas']) if dados['notas'] else 0
                tree.insert("", "end", values=(
                    dados['nome'],
                    dados['turma'],
                    dados['disc_risco'],
                    f"{media_geral:.1f}"
                ))
                count += 1
        
        # Label com total
        tk.Label(
            parent,
            text=f"Total de alunos em risco (≥2 disciplinas < 60): {count}",
            font=("Arial", 10, "bold"),
            bg=self.co0,
            fg=self.co8
        ).pack(pady=5)
    
    def gerar_rankings(self):
        """Gera rankings de melhores e piores desempenhos"""
        if not getattr(self, 'dados', None):
            return
        # Limpar aba
        for widget in self.aba_ranking.winfo_children():
            widget.destroy()
        
        # Calcular médias por aluno
        alunos_medias = {}
        for nota in self.dados['notas']:
            aluno_id = nota[0]
            aluno_nome = nota[1]
            turma_nome = nota[7]
            nota_valor = float(nota[5]) if nota[5] is not None else None
            
            if aluno_id not in alunos_medias:
                alunos_medias[aluno_id] = {
                    'nome': aluno_nome,
                    'turma': turma_nome,
                    'notas': []
                }
            
            if nota_valor is not None:
                alunos_medias[aluno_id]['notas'].append(nota_valor)
        
        # Calcular média de cada aluno
        for aluno_id in alunos_medias:
            notas = alunos_medias[aluno_id]['notas']
            alunos_medias[aluno_id]['media'] = np.mean(notas) if notas else 0
        
        # Ordenar por média
        ranking = sorted(
            alunos_medias.items(),
            key=lambda x: x[1]['media'],
            reverse=True
        )
        
        # Frame principal com dois frames lado a lado
        frame_principal = tk.Frame(self.aba_ranking, bg=self.co0)
        frame_principal.pack(fill="both", expand=True, padx=5, pady=5)
        
        frame_principal.columnconfigure(0, weight=1)
        frame_principal.columnconfigure(1, weight=1)
        
        # TOP 10 - Melhores
        frame_top10 = tk.LabelFrame(
            frame_principal,
            text="🏆 TOP 10 - Melhores Médias",
            font=("Arial", 11, "bold"),
            bg=self.co0,
            fg=self.co2
        )
        frame_top10.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.criar_lista_ranking(frame_top10, ranking[:10], True)
        
        # TOP 10 - Piores (precisam de atenção)
        frame_bottom10 = tk.LabelFrame(
            frame_principal,
            text="⚠️ Necessitam Atenção - 10 Menores Médias",
            font=("Arial", 11, "bold"),
            bg=self.co0,
            fg=self.co8
        )
        frame_bottom10.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.criar_lista_ranking(frame_bottom10, list(reversed(ranking[-10:])), False)
    
    def criar_lista_ranking(self, parent, ranking, is_top):
        """Cria lista de ranking"""
        # Treeview
        colunas = ("pos", "aluno", "turma", "media")
        tree = ttk.Treeview(parent, columns=colunas, show="headings", height=10)
        
        tree.heading("pos", text="Pos")
        tree.heading("aluno", text="Aluno")
        tree.heading("turma", text="Turma")
        tree.heading("media", text="Média")
        
        tree.column("pos", width=50, anchor="center")
        tree.column("aluno", width=250)
        tree.column("turma", width=120)
        tree.column("media", width=80, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        # Preencher dados
        for i, (aluno_id, dados) in enumerate(ranking, 1):
            pos = f"{i}º"
            if is_top and i <= 3:
                # Adicionar emoji de medalha para top 3
                medals = ["🥇", "🥈", "🥉"]
                pos = f"{medals[i-1]} {i}º"
            
            tree.insert("", "end", values=(
                pos,
                dados['nome'],
                dados['turma'],
                f"{dados['media']:.1f}"
            ))
    
    def ao_fechar_janela(self):
        """Executa ao fechar a janela"""
        if self.janela_principal:
            self.janela_principal.deiconify()
        self.janela.destroy()


def abrir_relatorio_analise_notas(janela_principal=None):
    """Função para abrir a interface de relatório"""
    if janela_principal:
        janela_principal.withdraw()
    
    janela = tk.Toplevel()
    app = RelatorioAnaliseNotas(janela, janela_principal)
    
    # Configurar fechamento
    def ao_fechar():
        if janela_principal:
            janela_principal.deiconify()
        janela.destroy()
    
    janela.protocol("WM_DELETE_WINDOW", ao_fechar)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_relatorio_analise_notas()
    root.mainloop()
