"""
Interface Principal do Banco de Questões BNCC.

Janela principal que integra todas as funcionalidades do banco de questões.
"""

from config_logs import get_logger
logger = get_logger(__name__)
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import config

from config import perfis_habilitados
from auth.usuario_logado import UsuarioLogado


class InterfaceBancoQuestoes:
    """Interface principal do Banco de Questões BNCC."""
    
    def __init__(self, root=None, janela_principal=None):
        """
        Inicializa a interface principal do banco de questões.
        
        Args:
            root: Janela Tk/Toplevel existente ou None para criar nova
            janela_principal: Referência à janela principal da aplicação
        """
        self.janela_principal = janela_principal
        
        if root is None:
            self.janela = tk.Toplevel()
            self.janela.title("Banco de Questões BNCC")
            self.janela.geometry("1100x700")
            self.janela.grab_set()
            self.janela.focus_force()
            self.janela.protocol("WM_DELETE_WINDOW", self.ao_fechar_janela)
        else:
            self.janela = root

        # Cores padrão do sistema
        self.co0 = "#F5F5F5"
        self.co1 = "#003A70"
        self.co2 = "#77B341"
        self.co3 = "#E2418E"
        self.co4 = "#4A86E8"
        self.co7 = "#333333"
        self.co8 = "#BF3036"
        self.co9 = "#999999"
        
        self.janela.configure(bg=self.co0)
        
        # Verificar perfil do usuário
        self.perfil = None
        self.funcionario_id = None
        if perfis_habilitados():
            self.perfil = UsuarioLogado.get_perfil()
            self.funcionario_id = UsuarioLogado.get_funcionario_id()
        
        self.criar_interface()
    
    def ao_fechar_janela(self):
        """Trata o evento de fechamento da janela."""
        if self.janela_principal:
            self.janela_principal.deiconify()
        self.janela.destroy()
    
    def criar_interface(self):
        """Cria a interface principal com abas."""
        # Frame de título
        self.frame_titulo = tk.Frame(self.janela, bg=self.co1)
        self.frame_titulo.pack(side="top", fill="x")
        
        tk.Label(
            self.frame_titulo,
            text="📚 Banco de Questões BNCC",
            font=("Arial", 16, "bold"),
            bg=self.co1, fg="white"
        ).pack(fill="x", padx=10, pady=10)
        
        # Notebook (abas)
        self.notebook = ttk.Notebook(self.janela)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Aba 1: Buscar Questões
        self.frame_busca = tk.Frame(self.notebook, bg=self.co0)
        self.notebook.add(self.frame_busca, text="🔍 Buscar Questões")
        self.criar_aba_busca()
        
        # Aba 2: Cadastrar Questão (apenas se tem permissão)
        if self._pode_criar_questao():
            self.frame_cadastro = tk.Frame(self.notebook, bg=self.co0)
            self.notebook.add(self.frame_cadastro, text="➕ Nova Questão")
            self.criar_aba_cadastro()
        
        # Aba 3: Montar Avaliação
        if self._pode_criar_avaliacao():
            self.frame_avaliacao = tk.Frame(self.notebook, bg=self.co0)
            self.notebook.add(self.frame_avaliacao, text="📝 Montar Avaliação")
            self.criar_aba_avaliacao()
        
        # Aba 4: Minhas Questões (professor vê apenas suas)
        self.frame_minhas = tk.Frame(self.notebook, bg=self.co0)
        self.notebook.add(self.frame_minhas, text="📋 Minhas Questões")
        self.criar_aba_minhas_questoes()
        
        # Aba 5: Estatísticas (apenas coordenador/admin)
        if self.perfil in ['administrador', 'coordenador']:
            self.frame_estatisticas = tk.Frame(self.notebook, bg=self.co0)
            self.notebook.add(self.frame_estatisticas, text="📊 Estatísticas")
            self.criar_aba_estatisticas()
    
    def _pode_criar_questao(self) -> bool:
        """Verifica se o usuário pode criar questões."""
        if not perfis_habilitados():
            return True
        return self.perfil in ['administrador', 'coordenador', 'professor']
    
    def _pode_criar_avaliacao(self) -> bool:
        """Verifica se o usuário pode criar avaliações."""
        if not perfis_habilitados():
            return True
        return self.perfil in ['administrador', 'coordenador', 'professor']
    
    # =========================================================================
    # ABA: BUSCAR QUESTÕES
    # =========================================================================
    
    def criar_aba_busca(self):
        """Cria a aba de busca de questões."""
        # Frame de filtros
        frame_filtros = tk.LabelFrame(
            self.frame_busca, text="Filtros de Busca",
            bg=self.co0, font=("Arial", 10, "bold")
        )
        frame_filtros.pack(fill="x", padx=10, pady=10)
        
        # Linha 1: Componente e Ano
        tk.Label(frame_filtros, text="Componente:", bg=self.co0).grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.cb_componente = ttk.Combobox(frame_filtros, width=25, state="readonly")
        self.cb_componente['values'] = [
            "Todos", "Língua Portuguesa", "Matemática", "Ciências",
            "Geografia", "História", "Arte", "Educação Física",
            "Língua Inglesa", "Ensino Religioso"
        ]
        self.cb_componente.current(0)
        self.cb_componente.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        tk.Label(frame_filtros, text="Ano:", bg=self.co0).grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        self.cb_ano = ttk.Combobox(frame_filtros, width=15, state="readonly")
        self.cb_ano['values'] = [
            "Todos", "1º ano", "2º ano", "3º ano", "4º ano", "5º ano",
            "6º ano", "7º ano", "8º ano", "9º ano"
        ]
        self.cb_ano.current(0)
        self.cb_ano.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Linha 2: Dificuldade e Tipo
        tk.Label(frame_filtros, text="Dificuldade:", bg=self.co0).grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        self.cb_dificuldade = ttk.Combobox(frame_filtros, width=15, state="readonly")
        self.cb_dificuldade['values'] = ["Todas", "Fácil", "Média", "Difícil"]
        self.cb_dificuldade.current(0)
        self.cb_dificuldade.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        tk.Label(frame_filtros, text="Tipo:", bg=self.co0).grid(
            row=1, column=2, padx=5, pady=5, sticky="w"
        )
        self.cb_tipo = ttk.Combobox(frame_filtros, width=20, state="readonly")
        self.cb_tipo['values'] = [
            "Todos", "Múltipla Escolha", "Dissertativa", "V/F"
        ]
        self.cb_tipo.current(0)
        self.cb_tipo.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Linha 3: Habilidade BNCC e texto
        tk.Label(frame_filtros, text="Habilidade BNCC:", bg=self.co0).grid(
            row=2, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_habilidade = ttk.Entry(frame_filtros, width=20)
        self.entry_habilidade.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        tk.Label(frame_filtros, text="Texto (busca):", bg=self.co0).grid(
            row=2, column=2, padx=5, pady=5, sticky="w"
        )
        self.entry_texto = ttk.Entry(frame_filtros, width=30)
        self.entry_texto.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        
        # Botão buscar
        btn_buscar = tk.Button(
            frame_filtros, text="🔍 Buscar",
            command=self.buscar_questoes,
            bg=self.co4, fg="white", font=("Arial", 10, "bold")
        )
        btn_buscar.grid(row=2, column=4, padx=10, pady=5)
        
        # Frame de resultados
        frame_resultados = tk.LabelFrame(
            self.frame_busca, text="Resultados",
            bg=self.co0, font=("Arial", 10, "bold")
        )
        frame_resultados.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview para resultados
        colunas = ("id", "componente", "ano", "habilidade", "tipo", "dificuldade", "status")
        self.tree_busca = ttk.Treeview(
            frame_resultados, columns=colunas, show="headings", height=15
        )
        
        self.tree_busca.heading("id", text="ID")
        self.tree_busca.heading("componente", text="Componente")
        self.tree_busca.heading("ano", text="Ano")
        self.tree_busca.heading("habilidade", text="Habilidade")
        self.tree_busca.heading("tipo", text="Tipo")
        self.tree_busca.heading("dificuldade", text="Dificuldade")
        self.tree_busca.heading("status", text="Status")
        
        self.tree_busca.column("id", width=50)
        self.tree_busca.column("componente", width=150)
        self.tree_busca.column("ano", width=80)
        self.tree_busca.column("habilidade", width=100)
        self.tree_busca.column("tipo", width=120)
        self.tree_busca.column("dificuldade", width=80)
        self.tree_busca.column("status", width=80)
        
        scrollbar = ttk.Scrollbar(frame_resultados, orient="vertical", command=self.tree_busca.yview)
        self.tree_busca.configure(yscrollcommand=scrollbar.set)
        
        self.tree_busca.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind duplo clique para ver detalhes
        self.tree_busca.bind("<Double-1>", self.ver_questao_selecionada)
        
        # Frame de ações
        frame_acoes = tk.Frame(self.frame_busca, bg=self.co0)
        frame_acoes.pack(fill="x", padx=10, pady=5)
        
        tk.Button(
            frame_acoes, text="👁️ Ver Detalhes",
            command=self.ver_questao_selecionada,
            bg=self.co4, fg="white"
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_acoes, text="⭐ Favoritar",
            command=self.favoritar_questao,
            bg=self.co2, fg="white"
        ).pack(side="left", padx=5)
        
        if self._pode_criar_avaliacao():
            tk.Button(
                frame_acoes, text="➕ Adicionar à Avaliação",
                command=self.adicionar_avaliacao,
                bg=self.co3, fg="white"
            ).pack(side="left", padx=5)
    
    def buscar_questoes(self):
        """Executa a busca de questões."""
        from banco_questoes.services import QuestaoService
        from banco_questoes.models import FiltroQuestoes, ComponenteCurricular, AnoEscolar, DificuldadeQuestao, TipoQuestao, StatusQuestao
        
        # Limpar resultados anteriores
        for item in self.tree_busca.get_children():
            self.tree_busca.delete(item)
        
        # Montar filtros
        filtros = FiltroQuestoes()
        
        if self.cb_componente.get() != "Todos":
            try:
                filtros.componente_curricular = ComponenteCurricular(self.cb_componente.get())
            except ValueError:
                pass
        
        if self.cb_ano.get() != "Todos":
            try:
                filtros.ano_escolar = AnoEscolar(self.cb_ano.get())
            except ValueError:
                pass
        
        if self.cb_dificuldade.get() != "Todas":
            mapa_dif = {"Fácil": "facil", "Média": "media", "Difícil": "dificil"}
            val = mapa_dif.get(self.cb_dificuldade.get())
            if val:
                try:
                    filtros.dificuldade = DificuldadeQuestao(val)
                except ValueError:
                    pass
        
        if self.cb_tipo.get() != "Todos":
            mapa_tipo = {
                "Múltipla Escolha": "multipla_escolha",
                "Dissertativa": "dissertativa",
                "V/F": "verdadeiro_falso"
            }
            val = mapa_tipo.get(self.cb_tipo.get())
            if val:
                try:
                    filtros.tipo = TipoQuestao(val)
                except ValueError:
                    pass
        
        habilidade = self.entry_habilidade.get().strip()
        if habilidade:
            filtros.habilidade_bncc = habilidade
        
        texto = self.entry_texto.get().strip()
        if texto:
            filtros.texto_busca = texto
        
        try:
            questoes, total = QuestaoService.buscar(filtros, limite=100)
            
            for q in questoes:
                self.tree_busca.insert("", "end", values=(
                    q.id,
                    q.componente_curricular.value if q.componente_curricular else '',
                    q.ano_escolar.value if q.ano_escolar else '',
                    q.habilidade_bncc_codigo or '',
                    q.tipo.value if q.tipo else '',
                    q.dificuldade.value if q.dificuldade else '',
                    q.status.value if q.status else ''
                ))
            
            if not questoes:
                messagebox.showinfo("Busca", "Nenhuma questão encontrada com os filtros selecionados.")
                
        except Exception as e:
            logger.error(f"Erro na busca de questões: {e}")
            messagebox.showerror("Erro", f"Erro ao buscar questões: {e}")
    
    def ver_questao_selecionada(self, event=None):
        """Abre detalhes da questão selecionada."""
        selecao = self.tree_busca.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione uma questão para ver os detalhes.")
            return
        
        item = self.tree_busca.item(selecao[0])
        questao_id = int(item['values'][0])
        
        # Abrir janela de detalhes
        self.abrir_detalhes_questao(questao_id)
    
    def favoritar_questao(self):
        """Adiciona questão aos favoritos."""
        selecao = self.tree_busca.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione uma questão para favoritar.")
            return
        
        if not self.funcionario_id:
            messagebox.showwarning("Aviso", "É necessário estar logado para favoritar.")
            return
        
        item = self.tree_busca.item(selecao[0])
        questao_id = int(item['values'][0])
        
        try:
            from banco_questoes.services import QuestaoService
            sucesso = QuestaoService.favoritar(questao_id, self.funcionario_id)
            if sucesso:
                messagebox.showinfo("Sucesso", "Questão adicionada aos favoritos!")
            else:
                messagebox.showwarning("Aviso", "Não foi possível favoritar a questão.")
        except Exception as e:
            logger.error(f"Erro ao favoritar: {e}")
            messagebox.showerror("Erro", f"Erro ao favoritar questão: {e}")
    
    def adicionar_avaliacao(self):
        """Adiciona questão à avaliação em construção."""
        selecao = self.tree_busca.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione uma questão para adicionar.")
            return
        
        item = self.tree_busca.item(selecao[0])
        questao_id = int(item['values'][0])
        
        # Mudar para aba de avaliação e adicionar
        if hasattr(self, 'frame_avaliacao'):
            self.notebook.select(self.frame_avaliacao)
            self.adicionar_questao_avaliacao(questao_id)
        else:
            messagebox.showwarning("Aviso", "Você não tem permissão para criar avaliações.")
    
    def abrir_detalhes_questao(self, questao_id: int):
        """Abre janela com detalhes da questão."""
        from banco_questoes.services import QuestaoService
        
        try:
            questao = QuestaoService.buscar_por_id(questao_id)
            
            if not questao:
                messagebox.showerror("Erro", "Questão não encontrada.")
                return
            
            # Criar janela de detalhes
            janela_detalhes = tk.Toplevel(self.janela)
            janela_detalhes.title(f"Questão #{questao_id}")
            janela_detalhes.geometry("700x500")
            janela_detalhes.grab_set()
            
            # Frame principal
            frame = tk.Frame(janela_detalhes, bg=self.co0)
            frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Informações
            info_text = f"""
Componente: {questao.componente_curricular.value if questao.componente_curricular else ''}
Ano: {questao.ano_escolar.value if questao.ano_escolar else ''}
Habilidade BNCC: {questao.habilidade_bncc_codigo or ''}
Tipo: {questao.tipo.value if questao.tipo else ''}
Dificuldade: {questao.dificuldade.value if questao.dificuldade else ''}
Status: {questao.status.value if questao.status else ''}

ENUNCIADO:
{questao.enunciado or ''}
"""
            
            if questao.texto_apoio:
                info_text += f"\n\nTEXTO DE APOIO:\n{questao.texto_apoio}"
            
            if questao.gabarito_letra:
                info_text += f"\n\nGABARITO: {questao.gabarito_letra}"
            
            if questao.alternativas:
                info_text += "\n\nALTERNATIVAS:"
                for alt in questao.alternativas:
                    marca = "✓" if alt.correta else " "
                    info_text += f"\n  {alt.letra}) [{marca}] {alt.texto}"
            
            text_widget = tk.Text(frame, wrap="word", font=("Arial", 10))
            text_widget.insert("1.0", info_text)
            text_widget.config(state="disabled")
            text_widget.pack(fill="both", expand=True)
            
            # Botão fechar
            tk.Button(
                frame, text="Fechar", command=janela_detalhes.destroy,
                bg=self.co9, fg="white"
            ).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Erro ao abrir detalhes: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar questão: {e}")
    
    # =========================================================================
    # ABA: CADASTRAR QUESTÃO
    # =========================================================================
    
    def criar_aba_cadastro(self):
        """Cria a aba de cadastro de nova questão."""
        # Frame com scroll
        canvas = tk.Canvas(self.frame_cadastro, bg=self.co0)
        scrollbar = ttk.Scrollbar(self.frame_cadastro, orient="vertical", command=canvas.yview)
        frame_scroll = tk.Frame(canvas, bg=self.co0)
        
        frame_scroll.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=frame_scroll, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Seção: Dados básicos
        frame_dados = tk.LabelFrame(
            frame_scroll, text="Dados da Questão",
            bg=self.co0, font=("Arial", 10, "bold")
        )
        frame_dados.pack(fill="x", padx=10, pady=10)
        
        # Componente
        tk.Label(frame_dados, text="Componente Curricular:*", bg=self.co0).grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.cad_componente = ttk.Combobox(frame_dados, width=25, state="readonly")
        self.cad_componente['values'] = [
            "Língua Portuguesa", "Matemática", "Ciências",
            "Geografia", "História", "Arte", "Educação Física",
            "Língua Inglesa", "Ensino Religioso"
        ]
        self.cad_componente.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Ano
        tk.Label(frame_dados, text="Ano Escolar:*", bg=self.co0).grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        self.cad_ano = ttk.Combobox(frame_dados, width=15, state="readonly")
        self.cad_ano['values'] = [
            "1º ano", "2º ano", "3º ano", "4º ano", "5º ano",
            "6º ano", "7º ano", "8º ano", "9º ano"
        ]
        self.cad_ano.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Habilidade BNCC
        tk.Label(frame_dados, text="Habilidade BNCC:*", bg=self.co0).grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        self.cad_habilidade = ttk.Entry(frame_dados, width=20)
        self.cad_habilidade.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        tk.Label(frame_dados, text="Ex: EF07MA02", bg=self.co0, fg=self.co9).grid(
            row=1, column=2, padx=5, pady=5, sticky="w"
        )
        
        # Tipo
        tk.Label(frame_dados, text="Tipo:*", bg=self.co0).grid(
            row=2, column=0, padx=5, pady=5, sticky="w"
        )
        self.cad_tipo = ttk.Combobox(frame_dados, width=20, state="readonly")
        self.cad_tipo['values'] = [
            "multipla_escolha", "dissertativa", "verdadeiro_falso"
        ]
        self.cad_tipo.current(0)
        self.cad_tipo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.cad_tipo.bind("<<ComboboxSelected>>", self.atualizar_campos_tipo)
        
        # Dificuldade
        tk.Label(frame_dados, text="Dificuldade:*", bg=self.co0).grid(
            row=2, column=2, padx=5, pady=5, sticky="w"
        )
        self.cad_dificuldade = ttk.Combobox(frame_dados, width=15, state="readonly")
        self.cad_dificuldade['values'] = ["facil", "media", "dificil"]
        self.cad_dificuldade.current(1)
        self.cad_dificuldade.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        
        # Seção: Enunciado
        frame_enunciado = tk.LabelFrame(
            frame_scroll, text="Enunciado*",
            bg=self.co0, font=("Arial", 10, "bold")
        )
        frame_enunciado.pack(fill="x", padx=10, pady=10)
        
        self.cad_enunciado = tk.Text(frame_enunciado, height=5, wrap="word")
        self.cad_enunciado.pack(fill="x", padx=5, pady=5)
        
        # Seção: Texto de apoio (opcional)
        frame_apoio = tk.LabelFrame(
            frame_scroll, text="Texto de Apoio (opcional)",
            bg=self.co0, font=("Arial", 10, "bold")
        )
        frame_apoio.pack(fill="x", padx=10, pady=10)
        
        self.cad_texto_apoio = tk.Text(frame_apoio, height=3, wrap="word")
        self.cad_texto_apoio.pack(fill="x", padx=5, pady=5)
        
        # Seção: Alternativas (para múltipla escolha)
        self.frame_alternativas = tk.LabelFrame(
            frame_scroll, text="Alternativas",
            bg=self.co0, font=("Arial", 10, "bold")
        )
        self.frame_alternativas.pack(fill="x", padx=10, pady=10)
        
        self.criar_campos_alternativas()
        
        # Seção: Gabarito dissertativa
        self.frame_gabarito_diss = tk.LabelFrame(
            frame_scroll, text="Gabarito / Resposta Esperada",
            bg=self.co0, font=("Arial", 10, "bold")
        )
        self.frame_gabarito_diss.pack(fill="x", padx=10, pady=10)
        self.frame_gabarito_diss.pack_forget()  # Esconder inicialmente
        
        self.cad_gabarito_diss = tk.Text(self.frame_gabarito_diss, height=3, wrap="word")
        self.cad_gabarito_diss.pack(fill="x", padx=5, pady=5)
        
        # Botões
        frame_botoes = tk.Frame(frame_scroll, bg=self.co0)
        frame_botoes.pack(fill="x", padx=10, pady=20)
        
        tk.Button(
            frame_botoes, text="💾 Salvar como Rascunho",
            command=lambda: self.salvar_questao("rascunho"),
            bg=self.co9, fg="white", font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_botoes, text="✅ Salvar e Enviar para Revisão",
            command=lambda: self.salvar_questao("revisao"),
            bg=self.co2, fg="white", font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_botoes, text="🧹 Limpar Campos",
            command=self.limpar_campos_cadastro,
            bg=self.co8, fg="white", font=("Arial", 10, "bold")
        ).pack(side="right", padx=5)
    
    def criar_campos_alternativas(self):
        """Cria os campos para alternativas de múltipla escolha."""
        self.cad_alternativas = {}
        self.var_gabarito = tk.StringVar(value="A")
        
        for letra in ["A", "B", "C", "D", "E"]:
            frame_alt = tk.Frame(self.frame_alternativas, bg=self.co0)
            frame_alt.pack(fill="x", padx=5, pady=2)
            
            rb = tk.Radiobutton(
                frame_alt, text=f"{letra})", variable=self.var_gabarito,
                value=letra, bg=self.co0
            )
            rb.pack(side="left")
            
            entry = ttk.Entry(frame_alt, width=70)
            entry.pack(side="left", fill="x", expand=True, padx=5)
            
            self.cad_alternativas[letra] = entry
        
        tk.Label(
            self.frame_alternativas,
            text="Selecione o botão da alternativa correta",
            bg=self.co0, fg=self.co9, font=("Arial", 9, "italic")
        ).pack(pady=5)
    
    def atualizar_campos_tipo(self, event=None):
        """Atualiza campos visíveis baseado no tipo de questão."""
        tipo = self.cad_tipo.get()
        
        if tipo == "multipla_escolha":
            self.frame_alternativas.pack(fill="x", padx=10, pady=10)
            self.frame_gabarito_diss.pack_forget()
        elif tipo == "dissertativa":
            self.frame_alternativas.pack_forget()
            self.frame_gabarito_diss.pack(fill="x", padx=10, pady=10)
        else:
            self.frame_alternativas.pack_forget()
            self.frame_gabarito_diss.pack_forget()
    
    def salvar_questao(self, status: str):
        """Salva a questão no banco de dados."""
        from banco_questoes.services import QuestaoService
        from banco_questoes.models import (
            Questao, QuestaoAlternativa, ComponenteCurricular, AnoEscolar,
            TipoQuestao, DificuldadeQuestao, StatusQuestao, VisibilidadeQuestao
        )
        
        # Validar campos obrigatórios
        if not self.cad_componente.get():
            messagebox.showwarning("Aviso", "Selecione o componente curricular.")
            return
        
        if not self.cad_ano.get():
            messagebox.showwarning("Aviso", "Selecione o ano escolar.")
            return
        
        if not self.cad_habilidade.get().strip():
            messagebox.showwarning("Aviso", "Informe a habilidade BNCC.")
            return
        
        enunciado = self.cad_enunciado.get("1.0", "end").strip()
        if not enunciado:
            messagebox.showwarning("Aviso", "Informe o enunciado da questão.")
            return
        
        if not self.funcionario_id:
            messagebox.showwarning("Aviso", "É necessário estar logado para salvar questões.")
            return
        
        try:
            # Mapear status
            status_map = {
                'rascunho': StatusQuestao.RASCUNHO,
                'revisao': StatusQuestao.REVISAO
            }
            
            # Criar objeto Questao
            questao = Questao(
                componente_curricular=ComponenteCurricular(self.cad_componente.get()),
                ano_escolar=AnoEscolar(self.cad_ano.get()),
                habilidade_bncc_codigo=self.cad_habilidade.get().strip().upper(),
                tipo=TipoQuestao(self.cad_tipo.get()),
                dificuldade=DificuldadeQuestao(self.cad_dificuldade.get()),
                enunciado=enunciado,
                texto_apoio=self.cad_texto_apoio.get("1.0", "end").strip() or None,
                status=status_map.get(status, StatusQuestao.RASCUNHO),
                visibilidade=VisibilidadeQuestao.ESCOLA,
                autor_id=self.funcionario_id,
                escola_id=config.ESCOLA_ID
            )
            
            # Gabarito para múltipla escolha
            if self.cad_tipo.get() == "multipla_escolha":
                questao.gabarito_letra = self.var_gabarito.get()
                
                # Coletar alternativas
                alternativas = []
                for letra, entry in self.cad_alternativas.items():
                    texto = entry.get().strip()
                    if texto:
                        alt = QuestaoAlternativa(
                            letra=letra,
                            texto=texto,
                            correta=(letra == self.var_gabarito.get()),
                            ordem=ord(letra) - ord('A') + 1
                        )
                        alternativas.append(alt)
                
                if len(alternativas) < 2:
                    messagebox.showwarning("Aviso", "Informe pelo menos 2 alternativas.")
                    return
                
                questao.alternativas = alternativas
            
            # Gabarito para dissertativa
            elif self.cad_tipo.get() == "dissertativa":
                questao.gabarito_dissertativa = self.cad_gabarito_diss.get("1.0", "end").strip()
            
            questao_id = QuestaoService.criar(questao)
            
            if questao_id:
                messagebox.showinfo(
                    "Sucesso",
                    f"Questão #{questao_id} salva com sucesso!\nStatus: {status}"
                )
                self.limpar_campos_cadastro()
            else:
                messagebox.showerror("Erro", "Não foi possível salvar a questão.")
            
        except Exception as e:
            logger.error(f"Erro ao salvar questão: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar questão: {e}")
    
    def limpar_campos_cadastro(self):
        """Limpa todos os campos do cadastro."""
        self.cad_componente.set("")
        self.cad_ano.set("")
        self.cad_habilidade.delete(0, "end")
        self.cad_tipo.current(0)
        self.cad_dificuldade.current(1)
        self.cad_enunciado.delete("1.0", "end")
        self.cad_texto_apoio.delete("1.0", "end")
        self.cad_gabarito_diss.delete("1.0", "end")
        
        for entry in self.cad_alternativas.values():
            entry.delete(0, "end")
        
        self.var_gabarito.set("A")
        self.atualizar_campos_tipo()
    
    # =========================================================================
    # ABA: MONTAR AVALIAÇÃO
    # =========================================================================
    
    def criar_aba_avaliacao(self):
        """Cria a aba de montagem de avaliação."""
        # Frame esquerdo - dados da avaliação
        frame_esq = tk.Frame(self.frame_avaliacao, bg=self.co0, width=400)
        frame_esq.pack(side="left", fill="y", padx=10, pady=10)
        frame_esq.pack_propagate(False)
        
        # Dados da avaliação
        frame_dados = tk.LabelFrame(
            frame_esq, text="Dados da Avaliação",
            bg=self.co0, font=("Arial", 10, "bold")
        )
        frame_dados.pack(fill="x", pady=5)
        
        tk.Label(frame_dados, text="Título:*", bg=self.co0).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.aval_titulo = ttk.Entry(frame_dados, width=30)
        self.aval_titulo.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(frame_dados, text="Componente:*", bg=self.co0).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.aval_componente = ttk.Combobox(frame_dados, width=25, state="readonly")
        self.aval_componente['values'] = [
            "Língua Portuguesa", "Matemática", "Ciências",
            "Geografia", "História", "Arte", "Educação Física",
            "Língua Inglesa", "Ensino Religioso"
        ]
        self.aval_componente.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(frame_dados, text="Ano:*", bg=self.co0).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.aval_ano = ttk.Combobox(frame_dados, width=15, state="readonly")
        self.aval_ano['values'] = [
            "1º ano", "2º ano", "3º ano", "4º ano", "5º ano",
            "6º ano", "7º ano", "8º ano", "9º ano"
        ]
        self.aval_ano.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        tk.Label(frame_dados, text="Bimestre:", bg=self.co0).grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.aval_bimestre = ttk.Combobox(frame_dados, width=15, state="readonly")
        self.aval_bimestre['values'] = ["1º bimestre", "2º bimestre", "3º bimestre", "4º bimestre"]
        self.aval_bimestre.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        tk.Label(frame_dados, text="Tipo:*", bg=self.co0).grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.aval_tipo = ttk.Combobox(frame_dados, width=20, state="readonly")
        self.aval_tipo['values'] = [
            "diagnostica", "formativa", "somativa", "recuperacao", "simulado", "exercicio"
        ]
        self.aval_tipo.current(2)
        self.aval_tipo.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        # Frame direito - questões selecionadas
        frame_dir = tk.Frame(self.frame_avaliacao, bg=self.co0)
        frame_dir.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        frame_questoes = tk.LabelFrame(
            frame_dir, text="Questões da Avaliação",
            bg=self.co0, font=("Arial", 10, "bold")
        )
        frame_questoes.pack(fill="both", expand=True)
        
        # Lista de questões na avaliação
        self.questoes_avaliacao = []  # Lista de IDs
        
        colunas = ("ordem", "id", "habilidade", "tipo", "pontos")
        self.tree_avaliacao = ttk.Treeview(
            frame_questoes, columns=colunas, show="headings", height=12
        )
        
        self.tree_avaliacao.heading("ordem", text="#")
        self.tree_avaliacao.heading("id", text="ID")
        self.tree_avaliacao.heading("habilidade", text="Habilidade")
        self.tree_avaliacao.heading("tipo", text="Tipo")
        self.tree_avaliacao.heading("pontos", text="Pontos")
        
        self.tree_avaliacao.column("ordem", width=40)
        self.tree_avaliacao.column("id", width=60)
        self.tree_avaliacao.column("habilidade", width=100)
        self.tree_avaliacao.column("tipo", width=120)
        self.tree_avaliacao.column("pontos", width=70)
        
        self.tree_avaliacao.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Botões de ação
        frame_btns = tk.Frame(frame_questoes, bg=self.co0)
        frame_btns.pack(fill="x", padx=5, pady=5)
        
        tk.Button(
            frame_btns, text="🗑️ Remover", command=self.remover_questao_avaliacao,
            bg=self.co8, fg="white"
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_btns, text="⬆️ Subir", command=lambda: self.mover_questao(-1),
            bg=self.co9, fg="white"
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_btns, text="⬇️ Descer", command=lambda: self.mover_questao(1),
            bg=self.co9, fg="white"
        ).pack(side="left", padx=5)
        
        # Total de pontos
        frame_total = tk.Frame(frame_dir, bg=self.co0)
        frame_total.pack(fill="x", pady=5)
        
        tk.Label(frame_total, text="Total de Questões:", bg=self.co0).pack(side="left", padx=5)
        self.lbl_total_questoes = tk.Label(frame_total, text="0", bg=self.co0, font=("Arial", 10, "bold"))
        self.lbl_total_questoes.pack(side="left")
        
        tk.Label(frame_total, text="  |  Total de Pontos:", bg=self.co0).pack(side="left", padx=5)
        self.lbl_total_pontos = tk.Label(frame_total, text="0.0", bg=self.co0, font=("Arial", 10, "bold"))
        self.lbl_total_pontos.pack(side="left")
        
        # Botões finais
        frame_final = tk.Frame(frame_dir, bg=self.co0)
        frame_final.pack(fill="x", pady=10)
        
        tk.Button(
            frame_final, text="💾 Salvar Avaliação",
            command=self.salvar_avaliacao,
            bg=self.co2, fg="white", font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_final, text="🖨️ Gerar PDF",
            command=self.gerar_pdf_avaliacao,
            bg=self.co4, fg="white", font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)
    
    def adicionar_questao_avaliacao(self, questao_id: int):
        """Adiciona uma questão à avaliação."""
        if questao_id in self.questoes_avaliacao:
            messagebox.showinfo("Aviso", "Esta questão já está na avaliação.")
            return
        
        try:
            from banco_questoes.services import QuestaoService
            questao = QuestaoService.buscar_por_id(questao_id)
            
            if not questao:
                messagebox.showerror("Erro", "Questão não encontrada.")
                return
            
            self.questoes_avaliacao.append(questao_id)
            
            ordem = len(self.questoes_avaliacao)
            self.tree_avaliacao.insert("", "end", values=(
                ordem,
                questao_id,
                questao.habilidade_bncc_codigo or '',
                questao.tipo.value if questao.tipo else '',
                "1.0"  # Pontuação padrão
            ))
            
            self.atualizar_totais_avaliacao()
            messagebox.showinfo("Sucesso", f"Questão #{questao_id} adicionada!")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar questão: {e}")
            messagebox.showerror("Erro", f"Erro ao adicionar questão: {e}")
    
    def remover_questao_avaliacao(self):
        """Remove questão selecionada da avaliação."""
        selecao = self.tree_avaliacao.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione uma questão para remover.")
            return
        
        item = self.tree_avaliacao.item(selecao[0])
        questao_id = item['values'][1]
        
        self.questoes_avaliacao.remove(questao_id)
        self.tree_avaliacao.delete(selecao[0])
        
        # Renumerar
        for i, item_id in enumerate(self.tree_avaliacao.get_children(), 1):
            valores = list(self.tree_avaliacao.item(item_id)['values'])
            valores[0] = str(i)
            self.tree_avaliacao.item(item_id, values=valores)
        
        self.atualizar_totais_avaliacao()
    
    def mover_questao(self, direcao: int):
        """Move questão para cima (-1) ou para baixo (+1)."""
        selecao = self.tree_avaliacao.selection()
        if not selecao:
            return
        
        item_id = selecao[0]
        index = self.tree_avaliacao.index(item_id)
        novo_index = index + direcao
        
        if novo_index < 0 or novo_index >= len(self.tree_avaliacao.get_children()):
            return
        
        self.tree_avaliacao.move(item_id, "", novo_index)
        
        # Renumerar
        for i, item in enumerate(self.tree_avaliacao.get_children(), 1):
            valores = list(self.tree_avaliacao.item(item)['values'])
            valores[0] = str(i)
            self.tree_avaliacao.item(item, values=valores)
    
    def atualizar_totais_avaliacao(self):
        """Atualiza totais de questões e pontos."""
        total_questoes = len(self.questoes_avaliacao)
        total_pontos = total_questoes * 1.0  # Pontuação fixa por enquanto
        
        self.lbl_total_questoes.config(text=str(total_questoes))
        self.lbl_total_pontos.config(text=f"{total_pontos:.1f}")
    
    def salvar_avaliacao(self):
        """Salva a avaliação no banco de dados."""
        from banco_questoes.services import AvaliacaoService
        from banco_questoes.models import Avaliacao, ComponenteCurricular, AnoEscolar, TipoAvaliacao, StatusAvaliacao
        
        if not self.aval_titulo.get().strip():
            messagebox.showwarning("Aviso", "Informe o título da avaliação.")
            return
        
        if not self.aval_componente.get():
            messagebox.showwarning("Aviso", "Selecione o componente curricular.")
            return
        
        if not self.aval_ano.get():
            messagebox.showwarning("Aviso", "Selecione o ano escolar.")
            return
        
        if not self.questoes_avaliacao:
            messagebox.showwarning("Aviso", "Adicione pelo menos uma questão.")
            return
        
        if not self.funcionario_id:
            messagebox.showwarning("Aviso", "É necessário estar logado.")
            return
        
        try:
            # Bimestre como string (ex: "1" ou "1º bimestre")
            bimestre = self.aval_bimestre.get() if self.aval_bimestre.get() else None
            
            avaliacao = Avaliacao(
                titulo=self.aval_titulo.get().strip(),
                componente_curricular=ComponenteCurricular(self.aval_componente.get()),
                ano_escolar=AnoEscolar(self.aval_ano.get()),
                bimestre=bimestre,
                tipo=TipoAvaliacao(self.aval_tipo.get()),
                professor_id=self.funcionario_id,
                escola_id=config.ESCOLA_ID,
                status=StatusAvaliacao.RASCUNHO
            )
            
            avaliacao_id = AvaliacaoService.criar(avaliacao)
            
            if avaliacao_id:
                # Adicionar questões à avaliação
                for ordem, questao_id in enumerate(self.questoes_avaliacao, 1):
                    AvaliacaoService.adicionar_questao(avaliacao_id, questao_id, ordem=ordem, pontuacao=1.0)
                
                messagebox.showinfo(
                    "Sucesso",
                    f"Avaliação #{avaliacao_id} salva com sucesso!\n"
                    f"{len(self.questoes_avaliacao)} questões adicionadas."
                )
            else:
                messagebox.showerror("Erro", "Não foi possível salvar a avaliação.")
            
        except Exception as e:
            logger.error(f"Erro ao salvar avaliação: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar avaliação: {e}")
    
    def gerar_pdf_avaliacao(self):
        """Gera PDF da avaliação."""
        messagebox.showinfo(
            "Em desenvolvimento",
            "A geração de PDF será implementada em breve.\n"
            "Por enquanto, salve a avaliação para consultar depois."
        )
    
    # =========================================================================
    # ABA: MINHAS QUESTÕES
    # =========================================================================
    
    def criar_aba_minhas_questoes(self):
        """Cria a aba de questões do usuário."""
        # Botão atualizar
        frame_top = tk.Frame(self.frame_minhas, bg=self.co0)
        frame_top.pack(fill="x", padx=10, pady=10)
        
        tk.Button(
            frame_top, text="🔄 Atualizar Lista",
            command=self.carregar_minhas_questoes,
            bg=self.co4, fg="white"
        ).pack(side="left")
        
        # Treeview
        frame_tree = tk.Frame(self.frame_minhas, bg=self.co0)
        frame_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        colunas = ("id", "componente", "ano", "habilidade", "tipo", "status", "data")
        self.tree_minhas = ttk.Treeview(
            frame_tree, columns=colunas, show="headings", height=15
        )
        
        self.tree_minhas.heading("id", text="ID")
        self.tree_minhas.heading("componente", text="Componente")
        self.tree_minhas.heading("ano", text="Ano")
        self.tree_minhas.heading("habilidade", text="Habilidade")
        self.tree_minhas.heading("tipo", text="Tipo")
        self.tree_minhas.heading("status", text="Status")
        self.tree_minhas.heading("data", text="Criada em")
        
        self.tree_minhas.column("id", width=50)
        self.tree_minhas.column("componente", width=130)
        self.tree_minhas.column("ano", width=70)
        self.tree_minhas.column("habilidade", width=100)
        self.tree_minhas.column("tipo", width=110)
        self.tree_minhas.column("status", width=80)
        self.tree_minhas.column("data", width=100)
        
        scrollbar = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree_minhas.yview)
        self.tree_minhas.configure(yscrollcommand=scrollbar.set)
        
        self.tree_minhas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Botões de ação
        frame_acoes = tk.Frame(self.frame_minhas, bg=self.co0)
        frame_acoes.pack(fill="x", padx=10, pady=5)
        
        tk.Button(
            frame_acoes, text="✏️ Editar",
            command=self.editar_minha_questao,
            bg=self.co4, fg="white"
        ).pack(side="left", padx=5)
        
        tk.Button(
            frame_acoes, text="🗑️ Excluir",
            command=self.excluir_minha_questao,
            bg=self.co8, fg="white"
        ).pack(side="left", padx=5)
        
        # Carregar automaticamente
        self.janela.after(500, self.carregar_minhas_questoes)
    
    def carregar_minhas_questoes(self):
        """Carrega as questões do usuário logado."""
        from banco_questoes.services import QuestaoService
        from banco_questoes.models import FiltroQuestoes
        
        # Limpar
        for item in self.tree_minhas.get_children():
            self.tree_minhas.delete(item)
        
        if not self.funcionario_id:
            return
        
        try:
            filtros = FiltroQuestoes(autor_id=self.funcionario_id)
            questoes, _ = QuestaoService.buscar(filtros, limite=100)
            
            for q in questoes:
                data_str = ''
                if q.created_at:
                    data_str = q.created_at.strftime('%Y-%m-%d') if hasattr(q.created_at, 'strftime') else str(q.created_at)[:10]
                
                self.tree_minhas.insert("", "end", values=(
                    q.id,
                    q.componente_curricular.value if q.componente_curricular else '',
                    q.ano_escolar.value if q.ano_escolar else '',
                    q.habilidade_bncc_codigo or '',
                    q.tipo.value if q.tipo else '',
                    q.status.value if q.status else '',
                    data_str
                ))
                
        except Exception as e:
            logger.error(f"Erro ao carregar questões: {e}")
    
    def editar_minha_questao(self):
        """Abre questão para edição."""
        selecao = self.tree_minhas.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione uma questão para editar.")
            return
        
        item = self.tree_minhas.item(selecao[0])
        questao_id = item['values'][0]
        
        messagebox.showinfo(
            "Em desenvolvimento",
            f"Edição da questão #{questao_id} será implementada em breve."
        )
    
    def excluir_minha_questao(self):
        """Exclui a questão selecionada."""
        selecao = self.tree_minhas.selection()
        if not selecao:
            messagebox.showwarning("Aviso", "Selecione uma questão para excluir.")
            return
        
        item = self.tree_minhas.item(selecao[0])
        questao_id = int(item['values'][0])
        
        if not messagebox.askyesno("Confirmar", f"Deseja realmente excluir a questão #{questao_id}?"):
            return
        
        try:
            from banco_questoes.services import QuestaoService
            sucesso = QuestaoService.excluir(questao_id)
            
            if sucesso:
                self.tree_minhas.delete(selecao[0])
                messagebox.showinfo("Sucesso", "Questão excluída com sucesso!")
            else:
                messagebox.showwarning(
                    "Aviso", 
                    "Não foi possível excluir a questão.\n"
                    "Ela pode estar sendo usada em alguma avaliação."
                )
            
        except Exception as e:
            logger.error(f"Erro ao excluir: {e}")
            messagebox.showerror("Erro", f"Erro ao excluir questão: {e}")
    
    # =========================================================================
    # ABA: ESTATÍSTICAS
    # =========================================================================
    
    def criar_aba_estatisticas(self):
        """Cria a aba de estatísticas (admin/coordenador)."""
        tk.Label(
            self.frame_estatisticas,
            text="📊 Estatísticas do Banco de Questões",
            font=("Arial", 14, "bold"),
            bg=self.co0
        ).pack(pady=20)
        
        frame_stats = tk.Frame(self.frame_estatisticas, bg=self.co0)
        frame_stats.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Placeholder - estatísticas serão carregadas aqui
        self.lbl_stats = tk.Label(
            frame_stats,
            text="Carregando estatísticas...",
            bg=self.co0, font=("Arial", 11)
        )
        self.lbl_stats.pack(pady=20)
        
        tk.Button(
            frame_stats, text="🔄 Atualizar Estatísticas",
            command=self.carregar_estatisticas,
            bg=self.co4, fg="white"
        ).pack(pady=10)
        
        self.janela.after(500, self.carregar_estatisticas)
    
    def carregar_estatisticas(self):
        """Carrega estatísticas do banco de questões."""
        try:
            from conexao import conectar_bd
            conn = conectar_bd()
            if not conn:
                self.lbl_stats.config(text="Erro: Não foi possível conectar ao banco de dados.")
                return
                
            cursor = conn.cursor(dictionary=True)
            
            # Total de questões
            cursor.execute("SELECT COUNT(*) as total FROM questoes")
            row = cursor.fetchone()
            if row:
                if isinstance(row, dict):
                    total = row['total'] if 'total' in row else 0
                else:
                    try:
                        total = row[0]
                    except Exception:
                        total = 0
            else:
                total = 0
            
            # Por status
            cursor.execute("""
                SELECT status, COUNT(*) as qtd 
                FROM questoes 
                GROUP BY status
            """)
            por_status = cursor.fetchall()
            
            # Por componente
            cursor.execute("""
                SELECT componente_curricular, COUNT(*) as qtd 
                FROM questoes 
                GROUP BY componente_curricular
                ORDER BY qtd DESC
            """)
            por_componente = cursor.fetchall()
            
            # Total de avaliações
            cursor.execute("SELECT COUNT(*) as total FROM avaliacoes")
            row_aval = cursor.fetchone()
            if row_aval:
                if isinstance(row_aval, dict):
                    total_aval = row_aval['total'] if 'total' in row_aval else 0
                else:
                    try:
                        total_aval = row_aval[0]
                    except Exception:
                        total_aval = 0
            else:
                total_aval = 0
            
            cursor.close()
            conn.close()
            
            # Montar texto
            texto = f"""
TOTAL DE QUESTÕES: {total}

POR STATUS:
"""
            for s in por_status:
                if isinstance(s, dict):
                    status = s.get('status', 'N/A')
                    qtd = s.get('qtd', 0)
                else:
                    # row tuple (status, qtd)
                    status = s[0] if len(s) > 0 else 'N/A'
                    qtd = s[1] if len(s) > 1 else 0
                texto += f"  • {status}: {qtd}\n"
            
            texto += "\nPOR COMPONENTE CURRICULAR:\n"
            for c in por_componente:
                if isinstance(c, dict):
                    comp = c.get('componente_curricular', 'N/A')
                    qtdc = c.get('qtd', 0)
                else:
                    comp = c[0] if len(c) > 0 else 'N/A'
                    qtdc = c[1] if len(c) > 1 else 0
                texto += f"  • {comp}: {qtdc}\n"
            
            texto += f"\nTOTAL DE AVALIAÇÕES: {total_aval}"
            
            self.lbl_stats.config(text=texto)
            
        except Exception as e:
            logger.error(f"Erro ao carregar estatísticas: {e}")
            self.lbl_stats.config(text=f"Erro ao carregar: {e}")


def abrir_banco_questoes(janela_principal=None):
    """
    Função auxiliar para abrir o banco de questões.
    
    Args:
        janela_principal: Referência à janela principal (opcional)
    """
    try:
        interface = InterfaceBancoQuestoes(janela_principal=janela_principal)
        return interface
    except Exception as e:
        logger.error(f"Erro ao abrir banco de questões: {e}")
        messagebox.showerror("Erro", f"Não foi possível abrir o banco de questões: {e}")
        return None
