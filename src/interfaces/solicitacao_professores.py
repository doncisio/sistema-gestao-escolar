import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import platform
import os

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white
from src.core.conexao import conectar_bd
from reportlab.lib.utils import ImageReader
from typing import Any, cast


class InterfaceSolicitacaoProfessores:
    def __init__(self, root=None, janela_principal=None):
        self.janela_principal = janela_principal

        if root is None:
            self.janela = tk.Toplevel()
            self.janela.title("Solicitação de Professores e Coordenadores")
            self.janela.geometry("840x620")
            self.janela.grab_set()
            self.janela.focus_force()
            self.janela.protocol("WM_DELETE_WINDOW", self.ao_fechar_janela)
        else:
            self.janela = root

        # Cores alinhadas ao projeto
        self.co0 = "#F5F5F5"
        self.co1 = "#003A70"
        self.co2 = "#77B341"
        self.co3 = "#E2418E"
        self.co7 = "#333333"
        self.co9 = "#999999"

        self.janela.configure(bg=self.co0)

        # Estado
        hoje = datetime.today()
        self.data_solicitacao = tk.StringVar(value=hoje.strftime("%d/%m/%Y"))
        self.unidade_escolar = tk.StringVar()
        self.solicitante = tk.StringVar()
        self.telefone = tk.StringVar()
        self.tipo_solicitacao = tk.StringVar(value="Professor")
        self.disciplina = tk.StringVar()
        self.turno = tk.StringVar(value="Matutino")
        self.carga_horaria = tk.StringVar()
        self.justificativa = tk.StringVar()
        self.tipo_movimento = tk.StringVar(value="Lotação")  # Lotação ou Relotação
        self.nivel_ensino = tk.StringVar(value="")  # removido do formulário
        self.motivo = tk.StringVar()
        self.supervisao = tk.StringVar()
        self.componente = tk.StringVar()
        self.turmas_selecionadas = []  # lista de ids/nome de turmas

        # Listas completas de opções
        self.todas_supervisoes = [
            "EDUCAÇÃO INFANTIL", "ANOS INICIAIS", "ANOS FINAIS", "TEMPO INTEGRAL", "EJAI", "GESTÃO ESCOLAR"
        ]
        
        self.todos_componentes = [
            "EDUCAÇÃO INFANTIL", "ANOS INICIAIS 1º AO 5º ANO", "PORTUGUÊS", "MATEMÁTICA", "HISTÓRIA",
            "GEOGRAFIA", "CIÊNCIAS", "ARTES", "ENSINO RELIGIOSO", "FILOSOFIA", "INGLÊS",
            "INTERPRETE DE LIBRAS", "PROFESSOR DE LIBRAS", "PROJETO DE VIDA", "EDUCAÇÃO FÍSICA",
            "LITERATURA", "COORDENADOR PEDAGÓGICO"
        ]

        # Turmas organizadas por categoria
        self.todas_turmas = [
            "CRECHE I", "CRECHE II", "CRECHE III",
            "CRECHE II A", "CRECHE II B", "CRECHE II C", "CRECHE II D", "CRECHE II E",
            "CRECHE III A", "CRECHE III B", "CRECHE III C", "CRECHE III D",
            "INFANTIL I", "INFANTIL II",
            "INFANTIL I A", "INFANTIL I B", "INFANTIL I C",
            "INFANTIL II A", "INFANTIL II B", "INFANTIL II C",
        ]
        # Adicionar 1º ao 9º ANO
        for serie in range(1, 10):
            self.todas_turmas.append(f"{serie}º ANO")
        # Adicionar 1º ao 9º ANO A..E
        for serie in range(1, 10):
            for letra in ["A", "B", "C", "D", "E"]:
                self.todas_turmas.append(f"{serie}º ANO {letra}")

        # Pré-preencher unidade escolar a partir do banco (escola_id=60)
        try:
            nome_escola_padrao = self._obter_nome_escola(60)
            if isinstance(nome_escola_padrao, str) and nome_escola_padrao.strip():
                self.unidade_escolar.set(nome_escola_padrao)
        except Exception:
            pass

        # Construção UI
        self.criar_frames()
        self.criar_cabecalho("Serviços • Solicitação de Professores e Coordenadores")
        self.criar_formulario()
        self.criar_botoes()

        # Configurar bindings para validação em cadeia
        self.tipo_solicitacao.trace('w', self.validar_cadeia_tipo_solicitacao)
        self.supervisao.trace('w', self.validar_cadeia_supervisao)

    def ao_fechar_janela(self):
        try:
            if self.janela_principal:
                self.janela_principal.deiconify()
        finally:
            self.janela.destroy()

    def criar_frames(self):
        self.frame_titulo = tk.Frame(self.janela, height=60, bg=self.co1)
        self.frame_titulo.pack(fill=tk.X)

        # Área de formulário com rolagem para garantir visibilidade
        self.frame_form = tk.Frame(self.janela, bg=self.co0)
        self.frame_form.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
        self.canvas_form = tk.Canvas(self.frame_form, bg=self.co0, highlightthickness=0)
        self.scrollbar_form = ttk.Scrollbar(self.frame_form, orient=tk.VERTICAL, command=self.canvas_form.yview)
        self.canvas_form.configure(yscrollcommand=self.scrollbar_form.set)
        self.canvas_form.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar_form.pack(side=tk.RIGHT, fill=tk.Y)
        self.form_area = tk.Frame(self.canvas_form, bg=self.co0)
        self.canvas_form.create_window((0, 0), window=self.form_area, anchor="nw")
        self.form_area.bind("<Configure>", lambda e: self.canvas_form.configure(scrollregion=self.canvas_form.bbox("all")))
        def _resize_canvas(event):
            try:
                self.canvas_form.itemconfig(1, width=event.width)
            except Exception:
                pass
        self.canvas_form.bind('<Configure>', _resize_canvas)
        # Configurar grade 2xN (rótulo, entrada) x 2 colunas lógicas
        for c in (1, 3):
            self.form_area.grid_columnconfigure(c, weight=1)

        self.frame_botoes = tk.Frame(self.janela, bg=self.co0)
        self.frame_botoes.pack(fill=tk.X, padx=16, pady=12)

    def criar_cabecalho(self, titulo):
        label = tk.Label(self.frame_titulo, text=titulo, bg=self.co1, fg=self.co0, font=("Ivy", 16, "bold"))
        label.pack(side=tk.LEFT, padx=16, pady=14)

    def _linha_grid(self, row_idx, col_block, texto, widget):
        col_label = 0 if col_block == 0 else 2
        col_input = col_label + 1
        lbl = tk.Label(self.form_area, text=texto, anchor=tk.W, bg=self.co0, fg=self.co7)
        lbl.grid(row=row_idx, column=col_label, sticky=tk.W, padx=(0,8), pady=4)
        widget.grid(row=row_idx, column=col_input, sticky=tk.EW, pady=4)

    def criar_formulario(self):
        entrada_larga = 44

        row = 0
        e_data = tk.Entry(self.form_area, textvariable=self.data_solicitacao, width=20)
        self._linha_grid(row, 0, "Data da solicitação:", e_data)
        row += 1
        e_unidade = tk.Entry(self.form_area, textvariable=self.unidade_escolar)
        self._linha_grid(row, 0, "Unidade escolar:", e_unidade)
        row += 1
        # (Solicitante, Telefone e E-mail removidos do formulário)
        cb_tipo = ttk.Combobox(self.form_area, textvariable=self.tipo_solicitacao, state="readonly",
                               values=["Professor", "Coordenador"], width=20)
        self._linha_grid(row, 0, "Tipo de solicitação:", cb_tipo)
        row += 1

        # Supervisão e Componente Curricular
        self.cb_superv = ttk.Combobox(self.form_area, textvariable=self.supervisao, state="readonly",
                                 values=self.todas_supervisoes, width=28)
        self._linha_grid(row, 1, "Supervisão:", self.cb_superv)
        row += 1

        self.cb_comp = ttk.Combobox(self.form_area, textvariable=self.componente, state="readonly",
                               values=self.todos_componentes, width=28)
        self._linha_grid(row, 1, "Componente Curricular:", self.cb_comp)
        row += 1

        # (Disciplina/Área removido do formulário) — usaremos Componente Curricular

        cb_turno = ttk.Combobox(self.form_area, textvariable=self.turno, state="readonly",
                                values=["Matutino", "Vespertino", "Noturno", "Integral"], width=20)
        self._linha_grid(row, 1, "Turno:", cb_turno)
        row += 1

        e_carga = tk.Entry(self.form_area, textvariable=self.carga_horaria, width=20)
        self._linha_grid(row, 1, "Carga horária semanal:", e_carga)
        row += 1

        # (Justificativa/Observações removido do formulário)

        cb_mov = ttk.Combobox(self.form_area, textvariable=self.tipo_movimento, state="readonly",
                               values=["Lotação", "Relotação"], width=20)
        self._linha_grid(row, 1, "Tipo do movimento:", cb_mov)
        row += 1

        # (Nível de ensino removido do formulário) — inferido via Supervisão/Componente

        e_motivo = tk.Entry(self.form_area, textvariable=self.motivo)
        self._linha_grid(row, 1, "Motivo (afastamento, licença, etc.):", e_motivo)
        row += 1

        # Seleção múltipla de turmas (lista do banco) - ocupa a linha toda
        tk.Label(self.form_area, text="Turmas (selecione uma ou mais):", bg=self.co0, fg=self.co7).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=(8,4))
        row += 1
        self.lista_turmas = tk.Listbox(self.form_area, selectmode=tk.MULTIPLE, height=6)
        self.lista_turmas.grid(row=row, column=0, columnspan=4, sticky=tk.EW)
        row += 1
        self._carregar_todas_turmas()

    def validar_cadeia_tipo_solicitacao(self, *args):
        """Validação em cadeia quando o tipo de solicitação é alterado"""
        tipo = self.tipo_solicitacao.get()
        
        if tipo == "Coordenador":
            # Somente GESTÃO ESCOLAR em Supervisão
            self.cb_superv.configure(values=["GESTÃO ESCOLAR"])
            self.supervisao.set("GESTÃO ESCOLAR")
            
            # Somente COORDENADOR PEDAGÓGICO em Componente
            self.cb_comp.configure(values=["COORDENADOR PEDAGÓGICO"])
            self.componente.set("COORDENADOR PEDAGÓGICO")
            
            # Limpar e desabilitar turmas
            self.lista_turmas.delete(0, tk.END)
            self.lista_turmas.configure(state=tk.DISABLED)
            
        elif tipo == "Professor":
            # Todas as supervisões exceto GESTÃO ESCOLAR
            supervisoes_prof = [s for s in self.todas_supervisoes if s != "GESTÃO ESCOLAR"]
            self.cb_superv.configure(values=supervisoes_prof)
            self.supervisao.set("")
            
            # Todos os componentes exceto COORDENADOR PEDAGÓGICO
            componentes_prof = [c for c in self.todos_componentes if c != "COORDENADOR PEDAGÓGICO"]
            self.cb_comp.configure(values=componentes_prof)
            self.componente.set("")
            
            # Habilitar e carregar todas as turmas
            self.lista_turmas.configure(state=tk.NORMAL)
            self._carregar_todas_turmas()
            
        # Disparar validação da supervisão se já tiver valor
        if self.supervisao.get():
            self.validar_cadeia_supervisao()
    
    def _filtrar_turmas_por_serie(self, series_min, series_max):
        """Filtra turmas por faixa de série (1-9)"""
        turmas_filtradas = []
        for turma in self.todas_turmas:
            # Verifica se a turma contém alguma das séries no intervalo
            for serie in range(series_min, series_max + 1):
                padrao = f"{serie}º ANO"
                if padrao in turma:
                    turmas_filtradas.append(turma)
                    break
        return turmas_filtradas

    def validar_cadeia_supervisao(self, *args):
        """Validação em cadeia quando a supervisão é alterada"""
        if self.tipo_solicitacao.get() == "Coordenador":
            return  # Coordenador já tem regras específicas
            
        supervisao = self.supervisao.get()
        
        if supervisao == "EDUCAÇÃO INFANTIL":
            # Somente EDUCAÇÃO INFANTIL em Componente
            self.cb_comp.configure(values=["EDUCAÇÃO INFANTIL"])
            self.componente.set("EDUCAÇÃO INFANTIL")
            
            # Somente turmas de CRECHE e INFANTIL
            turmas_infantil = [t for t in self.todas_turmas 
                            if t.startswith(('CRECHE', 'INFANTIL'))]
            self._carregar_turmas_especificas(turmas_infantil)
            
        elif supervisao == "ANOS INICIAIS":
            # Somente ANOS INICIAIS em Componente
            self.cb_comp.configure(values=["ANOS INICIAIS 1º AO 5º ANO"])
            self.componente.set("ANOS INICIAIS 1º AO 5º ANO")
            
            # Somente turmas do 1º ao 5º ANO
            turmas_iniciais = self._filtrar_turmas_por_serie(1, 5)
            self._carregar_turmas_especificas(turmas_iniciais)
            
        elif supervisao == "ANOS FINAIS":
            # Todos os componentes exceto infantil, anos iniciais e coordenador
            componentes_excluir = [
                "EDUCAÇÃO INFANTIL", 
                "ANOS INICIAIS 1º AO 5º ANO", 
                "COORDENADOR PEDAGÓGICO"
            ]
            componentes_finais = [c for c in self.todos_componentes 
                                if c not in componentes_excluir]
            self.cb_comp.configure(values=componentes_finais)
            self.componente.set("")
            
            # Somente turmas do 6º ao 9º ANO
            turmas_finais = self._filtrar_turmas_por_serie(6, 9)
            self._carregar_turmas_especificas(turmas_finais)
            
        else:  # TEMPO INTEGRAL, EJAI
            # Todos os componentes exceto coordenador
            componentes_geral = [c for c in self.todos_componentes 
                            if c != "COORDENADOR PEDAGÓGICO"]
            self.cb_comp.configure(values=componentes_geral)
            self.componente.set("")
            
            # Todas as turmas
            self._carregar_todas_turmas()

    def _carregar_todas_turmas(self):
        """Carrega todas as turmas disponíveis"""
        self._carregar_turmas_especificas(self.todas_turmas)

    def _carregar_turmas_especificas(self, turmas):
        """Carrega uma lista específica de turmas na listbox"""
        self.lista_turmas.delete(0, tk.END)
        for turma in turmas:
            self.lista_turmas.insert(tk.END, turma)
        # Armazena a lista atualmente exibida para mapear corretamente as seleções no PDF
        try:
            self._turmas_exibidas = list(turmas)
        except Exception:
            self._turmas_exibidas = turmas

    def validar(self):
        obrigatorios = [
            (self.unidade_escolar.get(), "Unidade escolar"),
            (self.tipo_solicitacao.get(), "Tipo de solicitação"),
            (self.turno.get(), "Turno"),
            (self.tipo_movimento.get(), "Tipo do movimento"),
            (self.supervisao.get(), "Supervisão"),
            (self.componente.get(), "Componente Curricular"),
            (self.motivo.get(), "Motivo"),
        ]
        for valor, nome in obrigatorios:
            if not valor.strip():
                messagebox.showwarning("Atenção", f"Preencha o campo: {nome}")
                return False
        
        # Validação específica para turmas - não obrigatório para coordenador
        if self.tipo_solicitacao.get() == "Professor":
            if not self.lista_turmas.curselection():
                messagebox.showwarning("Atenção", "Selecione pelo menos uma turma para Professor")
                return False
                
        return True

    def _resolver_logo_path(self) -> str | None:
        try:
            base_dir = os.path.dirname(__file__)
            candidatos = [
                os.path.join(base_dir, 'assets', 'images', 'logopacosemed.png'),
                os.path.join(base_dir, 'logopacosemed.png'),
            ]
            for caminho in candidatos:
                if os.path.isfile(caminho):
                    return caminho
            messagebox.showwarning(
                "Aviso",
                "Imagem do cabeçalho não encontrada (logopacosemed.png).\n"
                "Coloque o arquivo em assets/images/ ou na raiz do projeto."
            )
            return None
        except Exception:
            return None

    def _obter_nome_escola(self, escola_id: int = 60) -> str:
        try:
            conn = conectar_bd()
            if not conn:
                return f"Escola ID {escola_id}"
            try:
                cur = cast(Any, conn).cursor()
                cur.execute("SELECT nome FROM escolas WHERE id = %s", (escola_id,))
                row = cur.fetchone()
                if row:
                    if isinstance(row, tuple):
                        return str(row[0])
                    if isinstance(row, dict) and 'nome' in row:
                        return str(row['nome'])
                return f"Escola ID {escola_id}"
            finally:
                try:
                    cast(Any, conn).close()
                except Exception:
                    pass
        except Exception:
            return f"Escola ID {escola_id}"

    def _obter_emails_setores(self) -> list[tuple[str, str]]:
        """Retorna lista de tuplas (nome_setor, email_principal) a partir da tabela setores_semed."""
        resultados = []
        try:
            conn = conectar_bd()
            if not conn:
                return []
            try:
                cur = cast(Any, conn).cursor()
                cur.execute("SELECT nome_setor, email_principal FROM setores_semed")
                rows = cur.fetchall() or []
                for r in rows:
                    try:
                        if isinstance(r, dict):
                            resultados.append((str(r.get('nome_setor', '')).strip(), str(r.get('email_principal', '')).strip()))
                        else:
                            resultados.append((str(r[0]).strip(), str(r[1]).strip()))
                    except Exception:
                        continue
            finally:
                try:
                    cast(Any, conn).close()
                except Exception:
                    pass
        except Exception:
            pass
        # Filtrar vazios e duplicados
        vistos = set()
        filtrados = []
        for nome, email in resultados:
            if not nome or not email:
                continue
            chave = (nome.lower(), email.lower())
            if chave in vistos:
                continue
            vistos.add(chave)
            filtrados.append((nome, email))
        return filtrados

    def _mapear_setores_por_supervisao(self, supervisao: str) -> list[str]:
        """Retorna nomes dos setores padrão para a supervisão selecionada, sempre adicionando Mapeamento Escolar e RH."""
        s = (supervisao or '').strip().upper()
        mapa = {
            'EDUCAÇÃO INFANTIL': ['Educação Infantil'],
            'ANOS INICIAIS': ['Anos Iniciais'],
            'ANOS FINAIS': ['Anos Finais'],
            'TEMPO INTEGRAL': ['Tempo Integral'],
            'EJAI': ['EJAI'],
            'GESTÃO ESCOLAR': ['Gestão Escolar'],
        }
        destinos = list(mapa.get(s, []))
        # Sempre incluir mapeamento e RH
        destinos.extend(['Mapeamento Escolar', 'RH', 'Recursos Humanos', 'RH da Semed'])
        # Normalizar e remover duplicados preservando ordem
        vistos = set()
        finais = []
        for nome in destinos:
            k = nome.strip().lower()
            if k and k not in vistos:
                vistos.add(k)
                finais.append(nome)
        return finais

    def _abrir_dialogo_emails(self, caminho_pdf: str):
        """Abre diálogo para seleção de e-mails dos setores e ações de envio/cópia."""
        setores = self._obter_emails_setores()
        if not setores:
            messagebox.showwarning("Atenção", "Não foi possível carregar e-mails dos setores (tabela setores_semed).")
            return

        # Definir seleção padrão com base na supervisão
        nomes_preferidos = self._mapear_setores_por_supervisao(self.supervisao.get())
        nomes_preferidos_lc = set(n.lower() for n in nomes_preferidos)

        dlg = tk.Toplevel(self.janela)
        dlg.title("Enviar por e-mail - Setores SEMED")
        dlg.geometry("520x420")
        dlg.transient(self.janela)
        dlg.grab_set()

        frame = tk.Frame(dlg, padx=12, pady=12)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Selecione os e-mails de destino:").pack(anchor=tk.W)

        area = tk.Frame(frame)
        # Mantém altura controlada para a lista de e-mails, garantindo visibilidade dos botões
        area.pack(fill=tk.BOTH, expand=False, pady=(6, 8))

        canvas = tk.Canvas(area, highlightthickness=0)
        vs = ttk.Scrollbar(area, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor='nw')
        canvas.configure(yscrollcommand=vs.set)
        # Define uma altura fixa para a área rolável para não ocupar a janela inteira
        try:
            canvas.configure(height=220)
        except Exception:
            pass
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        vs.pack(side=tk.RIGHT, fill=tk.Y)

        vars_checks: list[tuple[tk.BooleanVar, str, str]] = []
        for nome, email in setores:
            var = tk.BooleanVar(value=(nome.strip().lower() in nomes_preferidos_lc))
            chk = tk.Checkbutton(inner, text=f"{nome}  <{email}>", variable=var, anchor='w', justify='left')
            chk.pack(fill=tk.X, anchor=tk.W)
            vars_checks.append((var, nome, email))

        # Mensagem de atenção piscando logo abaixo da lista de e-mails
        atencao_lbl = tk.Label(frame,
                               text="Atenção: imprimir o arquivo e depois escanear o arquivo assinado para ser anexado ao email",
                               fg="#C62828", font=("Ivy", 11, "bold"), justify='left', anchor='w', wraplength=480)
        atencao_lbl.pack(fill=tk.X, pady=(4, 4))

        def _piscar():
            try:
                cor_atual = atencao_lbl.cget('fg')
                nova_cor = self.co0 if cor_atual == "#C62828" else "#C62828"
                atencao_lbl.configure(fg=nova_cor)
            finally:
                atencao_lbl.after(600, _piscar)

        _piscar()

        # Ajuste dinâmico do wrap conforme largura do frame
        def _ajustar_wrap(event=None):
            try:
                largura = max(200, frame.winfo_width() - 24)
                atencao_lbl.configure(wraplength=largura)
            except Exception:
                pass

        frame.bind('<Configure>', _ajustar_wrap)
        _ajustar_wrap()

        info = tk.Label(frame, fg="#555", justify='left', wraplength=480,
                        text="Ao clicar em 'Abrir no e-mail', será aberta uma nova mensagem no Gmail com destinatários, assunto e corpo preenchidos (sem anexos).")
        info.pack(fill=tk.X, pady=(4, 8))

        btns = tk.Frame(frame)
        btns.pack(fill=tk.X)

        def coletar_emails():
            selecionados = [email for var, _, email in vars_checks if var.get() and email]
            return selecionados

        def copiar_emails():
            emails = coletar_emails()
            if not emails:
                messagebox.showwarning("Atenção", "Selecione ao menos um e-mail.")
                return
            try:
                dlg.clipboard_clear()
                dlg.clipboard_append(",".join(emails))
                dlg.update()
                messagebox.showinfo("Pronto", "E-mails copiados para a área de transferência.")
            except Exception:
                pass

        def abrir_mailto():
            emails = coletar_emails()
            if not emails:
                messagebox.showwarning("Atenção", "Selecione ao menos um e-mail.")
                return
            assunto = "Solicitação de Professores/Coordenadores"
            corpo = "Prezados(as),\n\nSegue solicitação para ciência e providências.\n\nAtenciosamente."
            # Abrir Gmail com composição pré-preenchida (sem anexos)
            to = ",".join(emails)
            try:
                from urllib.parse import quote
                gmail_url = (
                    "https://mail.google.com/mail/u/0/?view=cm&fs=1"
                    f"&to={quote(to)}&su={quote(assunto)}&body={quote(corpo)}"
                )
            except Exception:
                gmail_url = f"https://mail.google.com/mail/u/0/?view=cm&fs=1&to={to}"
            try:
                if platform.system() == "Windows":
                    os.startfile(gmail_url)
                elif platform.system() == "Darwin":
                    os.system(f"open '{gmail_url}'")
                else:
                    os.system(f"xdg-open '{gmail_url}'")
            except Exception:
                pass

        tk.Button(btns, text="Copiar e-mails", command=copiar_emails).pack(side=tk.LEFT)
        tk.Button(btns, text="Abrir no e-mail", command=abrir_mailto).pack(side=tk.LEFT, padx=6)
        tk.Button(btns, text="Fechar", command=dlg.destroy).pack(side=tk.RIGHT)

    def _montar_elementos_pdf(self):
        estilos = getSampleStyleSheet()
        titulo = ParagraphStyle('Titulo', parent=estilos['Heading1'], fontSize=12, alignment=0)
        sub = ParagraphStyle('Sub', parent=estilos['Heading2'], fontSize=11, alignment=1)
        label = ParagraphStyle('Label', parent=estilos['Normal'], fontSize=10)

        elementos = []
        # Cabeçalho com logotipo à esquerda e textos centralizados à direita
        logo_path = self._resolver_logo_path()

        try:
            if logo_path:
                img_logo = Image(logo_path)
                # Redimensionar proporcionalmente para caber em uma área máxima (mantém proporções originais)
                img_logo._restrictSize(1.8 * inch, 1.0 * inch)  # type: ignore[attr-defined]
            else:
                img_logo = Spacer(1.0 * inch, 1.0 * inch)
        except Exception:
            img_logo = Spacer(1.0 * inch, 1.0 * inch)

        # Buscar nome real da escola (escola_id = 60)
        nome_escola = self._obter_nome_escola(60)
        nome_escola = nome_escola.upper() if isinstance(nome_escola, str) else nome_escola

        cabecalho_texto = (
            f"<b>SOLICITAÇÃO DE PROFESSOR</b><br/>"
            f"MAPEAMENTO - SEMED<br/>"
            f"{nome_escola}<br/>"
            f"<b>ASSUNTO: SOLICITAÇÃO DE PROFESSOR</b>"
        )
        bloco_texto = Paragraph(cabecalho_texto, titulo)

        # Dispor imagem e texto centralizados em uma única coluna
        header_table = Table([[img_logo], [bloco_texto]])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # imagem
            ('ALIGN', (0, 1), (0, 1), 'LEFT'),    # texto
        ]))

        elementos.append(header_table)
        elementos.append(Spacer(1, 0.25 * inch))

        # Parágrafo justificativo antes da tabela
        nome_escola_par = nome_escola  # já em maiúsculas
        texto_mov = (self.tipo_movimento.get() or "").lower()
        componente_sel = (self.componente.get() or "").strip()
        texto_disc = componente_sel or "__________"
        texto_motivo = self.motivo.get() or "__________"

        # Derivar texto_nivel a partir do componente quando necessário
        if componente_sel.upper() in ("EDUCAÇÃO INFANTIL", "ANOS INICIAIS 1º AO 5º ANO"):
            texto_nivel = componente_sel.lower()
        else:
            texto_nivel = (self.nivel_ensino.get() or "").lower()

        if componente_sel.upper() == "COORDENADOR PEDAGÓGICO":
            paragrafo_contexto = (
                f"Prezados, considerando a necessidade de garantir a continuidade e qualidade do processo de ensino-aprendizagem na {nome_escola_par}, "
                f"solicitamos a {texto_mov} de coordenador(a) pedagógico, devido a {texto_motivo}."
            )
        elif componente_sel.upper() in ("EDUCAÇÃO INFANTIL", "ANOS INICIAIS 1º AO 5º ANO"):
            paragrafo_contexto = (
                f"Prezados, considerando a necessidade de garantir a continuidade e qualidade do processo de ensino-aprendizagem na {nome_escola_par}, "
                f"solicitamos a {texto_mov} de professor(a) {texto_nivel}, devido a {texto_motivo}."
            )
        else:
            paragrafo_contexto = (
                f"Prezados, considerando a necessidade de garantir a continuidade e qualidade do processo de ensino-aprendizagem na {nome_escola_par}, "
                f"solicitamos a {texto_mov} de professor(a) {texto_nivel} para a disciplina de {texto_disc}, devido a {texto_motivo}."
            )
        estilo_justificado = ParagraphStyle('Justificado', parent=estilos['Normal'], alignment=4)
        elementos.append(Paragraph(paragrafo_contexto, estilo_justificado))
        elementos.append(Spacer(1, 0.25 * inch))

        # Coletar turmas selecionadas usando a lista atualmente exibida
        try:
            if str(self.lista_turmas['state']) == str(tk.DISABLED):
                turmas_texto = ""
            else:
                indices = list(self.lista_turmas.curselection())
                base_lista = getattr(self, '_turmas_exibidas', self.todas_turmas)
                turmas_sel = []
                for idx in indices:
                    if 0 <= idx < len(base_lista):
                        turmas_sel.append(str(base_lista[idx]))
                turmas_texto = ", ".join(turmas_sel) if turmas_sel else ""
        except Exception:
            turmas_texto = ""

        dados = [
            [Paragraph("Data da Necessidade:", label), self.data_solicitacao.get()],
            [Paragraph("Supervisão:", label), self.supervisao.get()],
            [Paragraph("Componente Curricular:", label), self.componente.get()],
            [Paragraph("Carga Horária:", label), self.carga_horaria.get()],
            [Paragraph("Turma:", label), turmas_texto],
            [Paragraph("Turno:", label), self.turno.get()],
            [Paragraph("Motivo da solicitação:", label), self.motivo.get()],
        ]

        tabela = Table(dados, colWidths=[2.5 * inch, 4.5 * inch])
        tabela.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('BACKGROUND', (0, 0), (-1, -1), white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elementos.append(tabela)
        elementos.append(Spacer(1, 0.15 * inch))
        # Data da solicitação (direita) no formato "Paço do Lumiar - MA, {dia} de {mês} de {ano}"
        from src.utils.dates import formatar_data_extenso

        def formatar_data_pt(data_str: str) -> str:
            try:
                dt = datetime.strptime(data_str, "%d/%m/%Y")
            except Exception:
                try:
                    dt = datetime.strptime(data_str, "%d-%m-%Y")
                except Exception:
                    dt = datetime.today()
            return f"Paço do Lumiar - MA, {formatar_data_extenso(dt)}"

        data_formatada = formatar_data_pt(self.data_solicitacao.get())
        elementos.append(Paragraph(data_formatada, ParagraphStyle('DataRight', parent=estilos['Normal'], alignment=2)))
        elementos.append(Spacer(1, 0.35 * inch))

        # Tabela de rodapé anterior removida conforme solicitado

        # Assinatura do Gestor Geral (linha e rótulo), centralizado
        elementos.append(Spacer(1, 0.5 * inch))
        assinatura_table = Table([
            [""],
            ["GESTOR GERAL"],
        ], colWidths=[4.5 * inch])
        assinatura_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LINEABOVE', (0, 1), (0, 1), 0.8, black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elementos.append(assinatura_table)

        return elementos

    def gerar_pdf(self):
        if not self.validar():
            return

        sugestao = f"Solicitacao_Prof_Coord_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        caminho = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf")],
            initialfile=sugestao
        )
        if not caminho:
            return

        try:
            doc = SimpleDocTemplate(caminho, pagesize=A4,
                                    leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)

            # Resolver imagem de rodapé (tenta assets/images e raiz)
            def _resolver_img_rodape() -> str | None:
                base_dir = os.path.dirname(__file__)
                candidatos = [
                    os.path.join(base_dir, 'assets', 'images', 'img18.jpg'),
                    os.path.join(base_dir, 'img18.jpg'),
                ]
                for p in candidatos:
                    if os.path.isfile(p):
                        return p
                return None

            img_rodape_path = _resolver_img_rodape()

            def desenhar_rodape(canvas, doc):
                try:
                    if not img_rodape_path:
                        return
                    reader = ImageReader(img_rodape_path)
                    iw, ih = reader.getSize()
                    pg_w, pg_h = doc.pagesize
                    scale = 0.3  # usa tamanho original ou scale maior se quiser ampliar

                    sw = iw * scale
                    sh = ih * scale

                    x = (pg_w - sw) / 2  # centraliza na largura da página
                    y = 0  # posição no rodapé

                    canvas.drawImage(reader, x, y, width=sw, height=sh, preserveAspectRatio=True, mask='auto')
                except Exception:
                    pass

            elementos = self._montar_elementos_pdf()
            doc.build(elementos, onFirstPage=desenhar_rodape, onLaterPages=desenhar_rodape)
            # Abrir automaticamente no app padrão do SO
            try:
                if platform.system() == "Windows":
                    os.startfile(caminho)
                elif platform.system() == "Darwin":
                    os.system(f"open '{caminho}'")
                else:
                    os.system(f"xdg-open '{caminho}'")
            except Exception:
                pass

            # Após abrir o arquivo, oferecer envio por e-mail
            try:
                self._abrir_dialogo_emails(caminho)
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar PDF: {e}")

    def criar_botoes(self):
        btn_cancelar = tk.Button(self.frame_botoes, text="Cancelar", command=self.ao_fechar_janela,
                                 bg=self.co9, fg="white", padx=16, pady=6)
        btn_cancelar.pack(side=tk.RIGHT, padx=6)

        btn_pdf = tk.Button(self.frame_botoes, text="Gerar PDF", command=self.gerar_pdf,
                            bg=self.co2, fg="white", padx=16, pady=6)
        btn_pdf.pack(side=tk.RIGHT, padx=6)


def abrir_interface_solicitacao(janela_principal=None):
    # Esconde a janela principal e abre como modal
    if janela_principal:
        try:
            janela_principal.withdraw()
        except Exception:
            pass

    def ao_fechar_local():
        if janela_principal:
            try:
                janela_principal.deiconify()
            except Exception:
                pass
        janela_local.destroy()

    janela_local = tk.Toplevel()
    janela_local.title("Solicitação de Professores e Coordenadores")
    janela_local.geometry("840x620")
    janela_local.grab_set()
    janela_local.focus_force()
    janela_local.protocol("WM_DELETE_WINDOW", ao_fechar_local)

    InterfaceSolicitacaoProfessores(root=janela_local, janela_principal=janela_principal)