"""
Interface de Cadastro e Edição de Faltas de Funcionários.

Permite registrar faltas (F), faltas justificadas (FJ) e observações
para os funcionários por mês/ano. O campo P (presença) é calculado
automaticamente: P = Total de Dias do Mês - (F + FJ)
"""

from config_logs import get_logger
logger = get_logger(__name__)
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import calendar
from conexao import conectar_bd
from db.connection import get_connection, get_cursor
from typing import Any, cast, Dict, Optional


class InterfaceCadastroEdicaoFaltas:
    def __init__(self, root=None, janela_principal=None, escola_id: int = 60):
        self.janela_principal = janela_principal
        self.escola_id = escola_id

        if root is None:
            self.janela = tk.Toplevel()
            self.janela.title("Cadastro/Edição de Faltas de Funcionários")
            self.janela.geometry("950x650")
            self.janela.grab_set()
            self.janela.focus_force()
            self.janela.protocol("WM_DELETE_WINDOW", self.ao_fechar_janela)
        else:
            self.janela = root

        # Cores alinhadas ao main.py
        self.co0 = "#F5F5F5"  # Fundo claro
        self.co1 = "#003A70"  # Azul escuro (cabeçalho)
        self.co2 = "#77B341"  # Verde (sucesso)
        self.co3 = "#E2418E"  # Rosa/Magenta
        self.co4 = "#4A86E8"  # Azul claro (botões)
        self.co7 = "#333333"  # Cinza escuro (texto)
        self.co8 = "#BF3036"  # Vermelho (erro)
        self.co9 = "#999999"  # Cinza claro

        self.janela.configure(bg=self.co0)

        # Estado
        hoje = datetime.today()
        self.mes = tk.IntVar(value=hoje.month)
        self.ano = tk.IntVar(value=hoje.year)
        
        # Dicionário para armazenar inputs: {func_id: {"p": Entry, "f": Entry, "fj": Entry, "obs": Entry}}
        self.inputs_por_id: Dict[int, Dict[str, tk.Entry]] = {}
        
        # Dados dos funcionários
        self.funcionarios_data: list = []

        # Construção UI
        self.criar_frames()
        self.criar_cabecalho("Cadastro e Edição de Faltas - Funcionários")
        self.criar_filtros()
        self.criar_area_tabela()
        self.criar_botoes()

        # Carregar dados iniciais
        self.carregar_funcionarios()
        self.atualizar_dias_letivos()

    def criar_frames(self):
        """Cria os frames principais da interface."""
        # Frame superior para título
        self.frame_titulo = tk.Frame(self.janela, bg=self.co1)
        self.frame_titulo.pack(side="top", fill="x")

        # Frame para filtros (mês/ano)
        self.frame_filtros = tk.Frame(self.janela, bg=self.co0)
        self.frame_filtros.pack(fill="x", padx=10, pady=8)

        # Frame para tabela de funcionários
        self.frame_tabela = tk.Frame(self.janela, bg=self.co0)
        self.frame_tabela.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame para botões
        self.frame_botoes = tk.Frame(self.janela, bg=self.co0)
        self.frame_botoes.pack(fill="x", padx=10, pady=10)

    def criar_cabecalho(self, titulo: str):
        """Cria o cabeçalho com título."""
        for w in self.frame_titulo.winfo_children():
            w.destroy()
        tk.Label(
            self.frame_titulo, text=titulo, 
            font=("Arial", 14, "bold"), bg=self.co1, fg="white"
        ).pack(fill="x", padx=10, pady=10)

    def criar_filtros(self):
        """Cria a área de filtros (mês/ano) e informações."""
        # Linha 1: Filtros
        tk.Label(self.frame_filtros, text="Mês:", bg=self.co0, font=("Arial", 10)).grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        sp_mes = ttk.Spinbox(
            self.frame_filtros, from_=1, to=12, width=5, 
            textvariable=self.mes, command=self.atualizar_dias_letivos
        )
        sp_mes.grid(row=0, column=1, sticky="w")

        tk.Label(self.frame_filtros, text="Ano:", bg=self.co0, font=("Arial", 10)).grid(
            row=0, column=2, padx=10, pady=5, sticky="w"
        )
        sp_ano = ttk.Spinbox(
            self.frame_filtros, from_=2020, to=2100, width=7, 
            textvariable=self.ano, command=self.atualizar_dias_letivos
        )
        sp_ano.grid(row=0, column=3, sticky="w")

        btn_carregar = tk.Button(
            self.frame_filtros, text="🔄 Carregar", 
            command=lambda: [self.carregar_funcionarios(), self.atualizar_dias_letivos()],
            bg=self.co4, fg="white", font=("Arial", 10, "bold")
        )
        btn_carregar.grid(row=0, column=4, padx=10)
        
        self.lbl_dias = tk.Label(
            self.frame_filtros, text="Dias letivos: --", 
            bg=self.co0, fg=self.co7, font=("Arial", 10, "bold")
        )
        self.lbl_dias.grid(row=0, column=5, padx=10, sticky="w")
        
        # Linha 2: Legenda explicativa
        tk.Label(
            self.frame_filtros, 
            text="💡 P (Presença) é calculado automaticamente: P = Total de Dias do Mês - (F + FJ)", 
            bg=self.co0, fg="#0066CC", font=("Arial", 9, "italic")
        ).grid(row=1, column=0, columnspan=6, padx=5, pady=5, sticky="w")

    def criar_area_tabela(self):
        """Cria a área da tabela com scroll para os funcionários."""
        # Limpar frame
        for widget in self.frame_tabela.winfo_children():
            widget.destroy()
        
        # Canvas com scrollbar para permitir scroll dos funcionários
        self.canvas = tk.Canvas(self.frame_tabela, bg=self.co0, highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.canvas.yview)
        scrollbar_x = ttk.Scrollbar(self.frame_tabela, orient="horizontal", command=self.canvas.xview)
        
        self.frame_scroll = tk.Frame(self.canvas, bg=self.co0)
        
        self.frame_scroll.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.frame_scroll, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Configurar scroll com mousewheel
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Layout
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")

    def criar_cabecalho_tabela(self):
        """Cria o cabeçalho da tabela de funcionários."""
        headers = [
            ("Nº", 50),
            ("Matrícula", 100),
            ("Nome do Funcionário", 300),
            ("P (Auto)", 70),
            ("F", 70),
            ("FJ", 70),
            ("Observação", 200)
        ]
        
        for col, (text, width) in enumerate(headers):
            lbl = tk.Label(
                self.frame_scroll, text=text, font=("Arial", 10, "bold"),
                bg=self.co1, fg="white", padx=5, pady=8, width=width//8
            )
            lbl.grid(row=0, column=col, sticky="ew", padx=1, pady=1)
        
        # Configurar larguras das colunas
        self.frame_scroll.columnconfigure(0, minsize=50)   # Nº
        self.frame_scroll.columnconfigure(1, minsize=100)  # Matrícula
        self.frame_scroll.columnconfigure(2, minsize=300)  # Nome
        self.frame_scroll.columnconfigure(3, minsize=70)   # P
        self.frame_scroll.columnconfigure(4, minsize=70)   # F
        self.frame_scroll.columnconfigure(5, minsize=70)   # FJ
        self.frame_scroll.columnconfigure(6, minsize=200)  # Obs

    def criar_botoes(self):
        """Cria os botões de ação."""
        btn_salvar = tk.Button(
            self.frame_botoes, text="💾 Salvar", 
            command=self.salvar,
            bg=self.co2, fg="white", font=("Arial", 10, "bold"),
            width=12
        )
        btn_salvar.pack(side="right", padx=5)
        
        btn_limpar = tk.Button(
            self.frame_botoes, text="🧹 Limpar", 
            command=self.limpar_campos,
            bg=self.co9, fg="white", font=("Arial", 10, "bold"),
            width=12
        )
        btn_limpar.pack(side="right", padx=5)

    def atualizar_dias_letivos(self):
        """Atualiza o label com os dias letivos do mês/ano selecionado."""
        try:
            with get_cursor() as cur:
                cur.execute(
                    """
                    SELECT dias_letivos FROM dias_letivos_mensais
                    WHERE ano_letivo = %s AND mes = %s
                    """,
                    (int(self.ano.get()), int(self.mes.get())),
                )
                row = cur.fetchone()
                valor = row[0] if row else None
                texto = f"Dias letivos: {valor}" if valor is not None else "Dias letivos: --"
                if hasattr(self, 'lbl_dias') and self.lbl_dias.winfo_exists():
                    self.lbl_dias.config(text=texto)
        except Exception:
            if hasattr(self, 'lbl_dias') and self.lbl_dias.winfo_exists():
                self.lbl_dias.config(text="Dias letivos: --")

    def garantir_tabela(self, conn):
        """Garante que a tabela de faltas existe no banco de dados."""
        cur = cast(Any, conn).cursor()
        cast(Any, cur).execute(
            """
            CREATE TABLE IF NOT EXISTS funcionario_faltas_mensal (
                id INT AUTO_INCREMENT PRIMARY KEY,
                funcionario_id INT NOT NULL,
                ano INT NOT NULL,
                mes INT NOT NULL,
                p VARCHAR(10) NULL,
                f VARCHAR(10) NULL,
                fj VARCHAR(10) NULL,
                observacao VARCHAR(255) NULL,
                UNIQUE KEY uniq_func_ano_mes (funcionario_id, ano, mes)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        cast(Any, cur).close()

    def carregar_funcionarios(self):
        """Carrega os funcionários e suas faltas na interface."""
        try:
            with get_connection() as conn:
                self.garantir_tabela(conn)
                cur = cast(Any, conn).cursor(dictionary=True)

                cur.execute(
                    """
                    SELECT f.id, f.matricula, f.nome
                    FROM Funcionarios f
                    WHERE f.escola_id = %s
                    ORDER BY f.nome
                    """,
                    (self.escola_id,),
                )
                funcionarios = cur.fetchall()
                self.funcionarios_data = funcionarios

                # Carregar faltas existentes do mês/ano selecionados
                cur.execute(
                    """
                    SELECT funcionario_id, p, f, fj, observacao
                    FROM funcionario_faltas_mensal
                    WHERE ano = %s AND mes = %s
                    """,
                    (self.ano.get(), self.mes.get()),
                )
                regs = {r["funcionario_id"]: r for r in cur.fetchall()}

                try:
                    cur.close()
                except Exception:
                    pass

            # Reconstruir a área da tabela
            self.criar_area_tabela()
            self.criar_cabecalho_tabela()
            self.inputs_por_id.clear()

            # Inserir linhas para cada funcionário
            for idx, func in enumerate(funcionarios, start=1):
                func_id = func["id"]
                matricula = func.get("matricula", "")
                nome = func["nome"]
                
                # Obter dados existentes
                reg = regs.get(func_id)
                p_val = str(reg.get("p", "")) if reg and reg.get("p") else ""
                f_val = str(reg.get("f", "")) if reg and reg.get("f") else ""
                fj_val = str(reg.get("fj", "")) if reg and reg.get("fj") else ""
                obs_val = str(reg.get("observacao", "")) if reg and reg.get("observacao") else ""
                
                row = idx  # Linha na grid (0 é o cabeçalho)
                
                # Cor alternada para linhas
                bg_color = "#FFFFFF" if idx % 2 == 1 else "#F0F0F0"
                
                # Coluna 0: Número
                lbl_num = tk.Label(
                    self.frame_scroll, text=str(idx), 
                    bg=bg_color, font=("Arial", 9), 
                    anchor="center", padx=5, pady=4
                )
                lbl_num.grid(row=row, column=0, sticky="ew", padx=1, pady=1)
                
                # Coluna 1: Matrícula
                lbl_mat = tk.Label(
                    self.frame_scroll, text=matricula, 
                    bg=bg_color, font=("Arial", 9), 
                    anchor="center", padx=5, pady=4
                )
                lbl_mat.grid(row=row, column=1, sticky="ew", padx=1, pady=1)
                
                # Coluna 2: Nome
                lbl_nome = tk.Label(
                    self.frame_scroll, text=nome, 
                    bg=bg_color, font=("Arial", 9), 
                    anchor="w", padx=5, pady=4
                )
                lbl_nome.grid(row=row, column=2, sticky="ew", padx=1, pady=1)
                
                # Coluna 3: P (readonly - calculado automaticamente)
                entrada_p = tk.Entry(
                    self.frame_scroll, width=8, justify="center", 
                    state="readonly", readonlybackground="#E0E0E0", fg="#666666",
                    font=("Arial", 9)
                )
                entrada_p.grid(row=row, column=3, sticky="ew", padx=2, pady=2)
                if p_val:
                    entrada_p.config(state="normal")
                    entrada_p.insert(0, p_val)
                    entrada_p.config(state="readonly")
                
                # Coluna 4: F (editável)
                entrada_f = tk.Entry(
                    self.frame_scroll, width=8, justify="center",
                    font=("Arial", 9)
                )
                entrada_f.grid(row=row, column=4, sticky="ew", padx=2, pady=2)
                if f_val:
                    entrada_f.insert(0, f_val)
                
                # Coluna 5: FJ (editável)
                entrada_fj = tk.Entry(
                    self.frame_scroll, width=8, justify="center",
                    font=("Arial", 9)
                )
                entrada_fj.grid(row=row, column=5, sticky="ew", padx=2, pady=2)
                if fj_val:
                    entrada_fj.insert(0, fj_val)
                
                # Coluna 6: Observação (editável)
                entrada_obs = tk.Entry(
                    self.frame_scroll, width=25, font=("Arial", 9)
                )
                entrada_obs.grid(row=row, column=6, sticky="ew", padx=2, pady=2)
                if obs_val:
                    entrada_obs.insert(0, obs_val)
                
                # Guardar referências
                self.inputs_por_id[func_id] = {
                    "p": entrada_p,
                    "f": entrada_f,
                    "fj": entrada_fj,
                    "obs": entrada_obs,
                }
                
                # Bind para calcular P automaticamente ao digitar F ou FJ
                entrada_f.bind("<KeyRelease>", lambda e, fid=func_id: self._calcular_presenca(fid))
                entrada_fj.bind("<KeyRelease>", lambda e, fid=func_id: self._calcular_presenca(fid))

            # Atualizar scroll region após adicionar todos os widgets
            self.frame_scroll.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar funcionários: {e}")

    def _calcular_presenca(self, func_id):
        """Calcula automaticamente P = total_dias_mes - (F + FJ)"""
        try:
            # Obter total de dias do mês corrente
            total_dias_mes = calendar.monthrange(int(self.ano.get()), int(self.mes.get()))[1]
            
            # Obter valores de F e FJ
            campos = self.inputs_por_id.get(func_id)
            if not campos:
                return
            
            f_texto = campos["f"].get().strip()
            fj_texto = campos["fj"].get().strip()
            
            # Converter para número
            f = 0
            fj = 0
            
            if f_texto:
                try:
                    f = int(f_texto)
                    if f < 0:
                        f = 0
                except ValueError:
                    f = 0
            
            if fj_texto:
                try:
                    fj = int(fj_texto)
                    if fj < 0:
                        fj = 0
                except ValueError:
                    fj = 0
            
            # Calcular P
            total_faltas = f + fj
            if total_faltas > total_dias_mes:
                # Se exceder, limitar ao máximo
                p = 0
            else:
                p = total_dias_mes - total_faltas
            
            # Atualizar campo P (precisa mudar estado temporariamente)
            entrada_p = campos["p"]
            entrada_p.config(state="normal")
            entrada_p.delete(0, tk.END)
            entrada_p.insert(0, str(p))
            entrada_p.config(state="readonly")
            
        except Exception as e:
            logger.error(f"Erro ao calcular presença: {e}")

    def salvar(self):
        try:
            with get_connection() as conn:
                self.garantir_tabela(conn)
                cur = cast(Any, conn).cursor()
                ano = int(self.ano.get())
                mes = int(self.mes.get())

                # Total de dias do mês corrente (calendário)
                total_dias_mes = calendar.monthrange(ano, mes)[1]

                # Obter observações já salvas para preservar quando não for informado
                cur_exist = cast(Any, conn).cursor(dictionary=True)
                cur_exist.execute(
                    """
                    SELECT funcionario_id, observacao
                    FROM funcionario_faltas_mensal
                    WHERE ano = %s AND mes = %s
                    """,
                    (ano, mes),
                )
                obs_existente_map = {r["funcionario_id"]: r.get("observacao") for r in cur_exist.fetchall()}
                try:
                    cur_exist.close()
                except Exception:
                    pass

                inseridos = 0
                atualizados = 0
                erros = []

                for func_id, campos in self.inputs_por_id.items():
                    # Obter valores dos campos (não usar mais P do usuário, será calculado)
                    f_texto = campos["f"].get().strip()
                    fj_texto = campos["fj"].get().strip()
                    obs = campos["obs"].get().strip()

                    # Valores padrão: F = 0, FJ = 0
                    f = 0
                    fj = 0

                    # Converter F para número
                    if f_texto:
                        try:
                            f = int(f_texto)
                            if f < 0:
                                erros.append(f"Funcionário ID {func_id}: Faltas não podem ser negativas")
                                continue
                        except ValueError:
                            erros.append(f"Funcionário ID {func_id}: Valor inválido para Faltas: '{f_texto}'")
                            continue

                    # Converter FJ para número
                    if fj_texto:
                        try:
                            fj = int(fj_texto)
                            if fj < 0:
                                erros.append(f"Funcionário ID {func_id}: Faltas justificadas não podem ser negativas")
                                continue
                        except ValueError:
                            erros.append(f"Funcionário ID {func_id}: Valor inválido para Faltas Justificadas: '{fj_texto}'")
                            continue

                    # Validar: F + FJ não pode exceder total de dias do mês
                    total_faltas = f + fj
                    if total_faltas > total_dias_mes:
                        erros.append(f"Funcionário ID {func_id}: Total de faltas ({total_faltas}) excede os dias do mês ({total_dias_mes})")
                        continue

                    # CALCULAR P automaticamente: P = total_dias_mes - (F + FJ)
                    p = total_dias_mes - total_faltas

                    # Se observação estiver vazia, salvar como NULL (permitir apagar)
                    obs_final = obs if obs else None

                    # Upsert
                    cast(Any, cur).execute(
                        """
                        INSERT INTO funcionario_faltas_mensal (funcionario_id, ano, mes, p, f, fj, observacao)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE p=VALUES(p), f=VALUES(f), fj=VALUES(fj), observacao=VALUES(observacao)
                        """,
                        (func_id, ano, mes, p, f, fj, obs_final),
                    )
                    if cur.rowcount == 1:
                        inseridos += 1
                    else:
                        atualizados += 1

                try:
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
                try:
                    cur.close()
                except Exception:
                    pass
            
            # Exibir resultado
            mensagem = f"Faltas salvas com sucesso!\n\nInseridos: {inseridos}\nAtualizados: {atualizados}"
            if erros:
                mensagem += f"\n\n⚠️ Erros encontrados ({len(erros)}):\n" + "\n".join(erros[:5])
                if len(erros) > 5:
                    mensagem += f"\n... e mais {len(erros) - 5} erro(s)"
                messagebox.showwarning("Concluído com Avisos", mensagem)
            else:
                messagebox.showinfo("Sucesso", mensagem)
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar faltas: {e}")

    def limpar_campos(self):
        for c in self.inputs_por_id.values():
            # Limpar F, FJ e Obs (P é readonly e será recalculado automaticamente)
            c["f"].delete(0, tk.END)
            c["fj"].delete(0, tk.END)
            c["obs"].delete(0, tk.END)
            
            # Limpar P também (precisa mudar estado temporariamente)
            c["p"].config(state="normal")
            c["p"].delete(0, tk.END)
            c["p"].config(state="readonly")

    def ao_fechar_janela(self):
        try:
            if self.janela_principal:
                self.janela_principal.deiconify()
            self.janela.destroy()
        except Exception:
            pass


def abrir_interface_faltas(janela_principal=None):
    try:
        if janela_principal:
            janela_principal.withdraw()
        return InterfaceCadastroEdicaoFaltas(janela_principal=janela_principal)
    except Exception as e:
        if janela_principal:
            janela_principal.deiconify()
        messagebox.showerror("Erro", f"Erro ao abrir interface de faltas: {e}")
        return None

