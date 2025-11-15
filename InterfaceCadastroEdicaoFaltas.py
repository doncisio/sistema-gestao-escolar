import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import calendar
from conexao import conectar_bd
from typing import Any, cast


class InterfaceCadastroEdicaoFaltas:
    def __init__(self, root=None, janela_principal=None, escola_id: int = 60):
        self.janela_principal = janela_principal
        self.escola_id = escola_id

        if root is None:
            self.janela = tk.Toplevel()
            self.janela.title("Cadastro/Edição de Faltas de Funcionários")
            self.janela.geometry("900x580")
            self.janela.grab_set()
            self.janela.focus_force()
            self.janela.protocol("WM_DELETE_WINDOW", self.ao_fechar_janela)
        else:
            self.janela = root

        # Cores alinhadas ao main.py
        self.co0 = "#F5F5F5"
        self.co1 = "#003A70"
        self.co2 = "#77B341"
        self.co3 = "#E2418E"
        self.co4 = "#4A86E8"
        self.co7 = "#333333"
        self.co8 = "#BF3036"
        self.co9 = "#999999"

        self.janela.configure(bg=self.co0)

        # Estado
        hoje = datetime.today()
        self.mes = tk.IntVar(value=hoje.month)
        self.ano = tk.IntVar(value=hoje.year)
        self._ajuste_agendado = None

        # Construção UI
        self.criar_frames()
        self.criar_cabecalho("Cadastro e Edição de Faltas - Funcionários")
        self.criar_filtros()
        self.criar_tabela()
        self.criar_botoes()

        # Carregar dados iniciais
        self.carregar_funcionarios()
        self.atualizar_dias_letivos()

    # --- UI ---
    def criar_frames(self):
        self.frame_titulo = tk.Frame(self.janela, bg=self.co1)
        self.frame_titulo.pack(side="top", fill="x")

        self.frame_filtros = tk.Frame(self.janela, bg=self.co0)
        self.frame_filtros.pack(fill="x", padx=10, pady=8)

        self.frame_tabela = tk.Frame(self.janela, bg=self.co0)
        self.frame_tabela.pack(fill="both", expand=True, padx=10, pady=5)

        self.frame_botoes = tk.Frame(self.janela, bg=self.co0)
        self.frame_botoes.pack(fill="x", padx=10, pady=10)

    def criar_cabecalho(self, titulo: str):
        for w in self.frame_titulo.winfo_children():
            w.destroy()
        tk.Label(self.frame_titulo, text=titulo, font=("Arial", 14, "bold"), bg=self.co1, fg="white").pack(fill="x", padx=10, pady=10)

    def criar_filtros(self):
        tk.Label(self.frame_filtros, text="Mês:", bg=self.co0).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        sp_mes = ttk.Spinbox(self.frame_filtros, from_=1, to=12, width=5, textvariable=self.mes, command=self.atualizar_dias_letivos)
        sp_mes.grid(row=0, column=1, sticky="w")

        tk.Label(self.frame_filtros, text="Ano:", bg=self.co0).grid(row=0, column=2, padx=10, pady=5, sticky="w")
        sp_ano = ttk.Spinbox(self.frame_filtros, from_=2020, to=2100, width=7, textvariable=self.ano, command=self.atualizar_dias_letivos)
        sp_ano.grid(row=0, column=3, sticky="w")

        ttk.Button(self.frame_filtros, text="Carregar", command=lambda: [self.carregar_funcionarios(), self.atualizar_dias_letivos()]).grid(row=0, column=4, padx=10)
        self.lbl_dias = tk.Label(self.frame_filtros, text="Dias letivos: --", bg=self.co0, fg=self.co7)
        self.lbl_dias.grid(row=0, column=5, padx=10, sticky="w")
        
        # Adicionar legenda explicativa
        tk.Label(self.frame_filtros, text="💡 P (Presença) é calculado automaticamente: P = Total de Dias do Mês - (F + FJ)", 
                bg=self.co0, fg="#0066CC", font=("Arial", 9, "italic")).grid(row=1, column=0, columnspan=6, padx=5, pady=5, sticky="w")

    def criar_tabela(self):
        # Treeview com colunas: Nº, Matrícula, Nome, P, F, FJ, Observação
        colunas = ("num", "matricula", "nome", "p", "f", "fj", "obs")
        self.tabela = ttk.Treeview(self.frame_tabela, columns=colunas, show="headings", height=16)
        self.tabela.heading("num", text="Nº")
        self.tabela.heading("matricula", text="Matrícula")
        self.tabela.heading("nome", text="Nome")
        self.tabela.heading("p", text="P (Auto)")
        self.tabela.heading("f", text="F")
        self.tabela.heading("fj", text="FJ")
        self.tabela.heading("obs", text="Observação")

        self.tabela.column("num", width=50, anchor="center")
        self.tabela.column("matricula", width=110, anchor="center")
        self.tabela.column("nome", width=360, anchor="w")
        self.tabela.column("p", width=60, anchor="center")
        self.tabela.column("f", width=60, anchor="center")
        self.tabela.column("fj", width=60, anchor="center")
        self.tabela.column("obs", width=180, anchor="w")

        scroll_y = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scroll_y.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.inputs_por_id = {}

    def atualizar_dias_letivos(self):
        try:
            conn = conectar_bd()
            cur = cast(Any, conn).cursor()
            cast(Any, cur).execute(
                """
                SELECT dias_letivos FROM dias_letivos_mensais
                WHERE ano_letivo = %s AND mes = %s
                """,
                (int(self.ano.get()), int(self.mes.get())),
            )
            row = cast(Any, cur).fetchone()
            valor = row[0] if row else None
            texto = f"Dias letivos: {valor}" if valor is not None else "Dias letivos: --"
            if hasattr(self, 'lbl_dias') and self.lbl_dias.winfo_exists():
                self.lbl_dias.config(text=texto)
            cast(Any, cur).close()
            if conn:
                cast(Any, conn).close()
        except Exception:
            if hasattr(self, 'lbl_dias') and self.lbl_dias.winfo_exists():
                self.lbl_dias.config(text="Dias letivos: --")

    def criar_botoes(self):
        ttk.Button(self.frame_botoes, text="Salvar", command=self.salvar).pack(side="right", padx=5)
        ttk.Button(self.frame_botoes, text="Limpar", command=self.limpar_campos).pack(side="right", padx=5)

    # --- Dados ---
    def garantir_tabela(self, conn):
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
        try:
            conn = conectar_bd()
            self.garantir_tabela(conn)
            cur = cast(Any, conn).cursor(dictionary=True)

            cast(Any, cur).execute(
                """
                SELECT f.id, f.matricula, f.nome
                FROM Funcionarios f
                WHERE f.escola_id = %s
                ORDER BY f.nome
                """,
                (self.escola_id,),
            )
            funcionarios = cast(Any, cur).fetchall()

            # Carregar faltas existentes do mês/ano selecionados
            cast(Any, cur).execute(
                """
                SELECT funcionario_id, p, f, fj, observacao
                FROM funcionario_faltas_mensal
                WHERE ano = %s AND mes = %s
                """,
                (self.ano.get(), self.mes.get()),
            )
            regs = {r["funcionario_id"]: r for r in cast(Any, cur).fetchall()}

            # Reset tabela
            for item in self.tabela.get_children():
                self.tabela.delete(item)
            self.inputs_por_id.clear()

            # Inserir linhas e inputs
            for idx, f in enumerate(funcionarios, start=1):
                item_id = self.tabela.insert("", "end", values=(idx, f.get("matricula", ""), f["nome"], "", "", "", ""))
                bbox_p = self.tabela.bbox(item_id, "p")
                bbox_f = self.tabela.bbox(item_id, "f")
                bbox_fj = self.tabela.bbox(item_id, "fj")
                bbox_obs = self.tabela.bbox(item_id, "obs")

                # Criar entradas editáveis (P é somente leitura)
                entrada_p = tk.Entry(self.tabela, width=5, justify="center", state="readonly", 
                                    readonlybackground="#E0E0E0", fg="#666666")
                entrada_f = tk.Entry(self.tabela, width=5, justify="center")
                entrada_fj = tk.Entry(self.tabela, width=5, justify="center")
                entrada_obs = tk.Entry(self.tabela, width=25)

                # Posicionar se bbox válido
                def _place(entry, bbox):
                    if bbox:
                        x, y, w, h = bbox
                        entry.place(x=x + 3, y=y + 2, width=w - 6, height=h - 4)

                _place(entrada_p, bbox_p)
                _place(entrada_f, bbox_f)
                _place(entrada_fj, bbox_fj)
                _place(entrada_obs, bbox_obs)

                # Preencher se houver registro
                reg = regs.get(f["id"]) if regs else None
                if reg:
                    if reg.get("p"):
                        entrada_p.config(state="normal")
                        entrada_p.delete(0, tk.END)
                        entrada_p.insert(0, str(reg.get("p")))
                        entrada_p.config(state="readonly")
                    if reg.get("f"):
                        entrada_f.insert(0, str(reg.get("f")))
                    if reg.get("fj"):
                        entrada_fj.insert(0, str(reg.get("fj")))
                    if reg.get("observacao"):
                        entrada_obs.insert(0, str(reg.get("observacao")))

                # Guardar
                self.inputs_por_id[f["id"]] = {
                    "p": entrada_p,
                    "f": entrada_f,
                    "fj": entrada_fj,
                    "obs": entrada_obs,
                }
                
                # Bind para calcular P automaticamente ao digitar F ou FJ
                entrada_f.bind("<KeyRelease>", lambda e, fid=f["id"]: self._calcular_presenca(fid))
                entrada_fj.bind("<KeyRelease>", lambda e, fid=f["id"]: self._calcular_presenca(fid))

            cast(Any, cur).close()
            if conn:
                cast(Any, conn).close()

            # Ajustar on scroll/movimento/redimensionamento
            self.tabela.bind("<ButtonRelease-1>", self._ajustar_inputs)
            self.tabela.bind("<Motion>", self._ajustar_inputs)
            self.tabela.bind("<Configure>", self._ajustar_inputs)
            self.janela.bind("<Configure>", self._ajustar_inputs)
            self.frame_tabela.bind("<Configure>", self._ajustar_inputs)
            self.janela.after(200, self._ajustar_inputs)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar funcionários: {e}")

    def _ajustar_inputs(self, event=None):
        try:
            # Cancela ajuste anterior agendado para evitar múltiplas chamadas
            if self._ajuste_agendado:
                self.janela.after_cancel(self._ajuste_agendado)
                self._ajuste_agendado = None
            
            # Agenda ajuste para dar tempo da geometria atualizar
            self._ajuste_agendado = self.janela.after(10, self._realizar_ajuste)
        except Exception:
            pass
    
    def _realizar_ajuste(self):
        try:
            self._ajuste_agendado = None
            # Força atualização da geometria da tabela antes de pegar bbox
            self.tabela.update_idletasks()
            
            for item_id, (func_id, inputs) in zip(self.tabela.get_children(), self.inputs_por_id.items()):
                bbox_p = self.tabela.bbox(item_id, "p")
                bbox_f = self.tabela.bbox(item_id, "f")
                bbox_fj = self.tabela.bbox(item_id, "fj")
                bbox_obs = self.tabela.bbox(item_id, "obs")
                self._place_if_visible(inputs["p"], bbox_p)
                self._place_if_visible(inputs["f"], bbox_f)
                self._place_if_visible(inputs["fj"], bbox_fj)
                self._place_if_visible(inputs["obs"], bbox_obs)
        except Exception:
            pass

    def _place_if_visible(self, entry, bbox):
        try:
            if not entry.winfo_exists():
                return
            if bbox:
                x, y, w, h = bbox
                entry.place(x=x + 3, y=y + 2, width=w - 6, height=h - 4)
                entry.lift()
            else:
                entry.place_forget()
        except Exception:
            pass

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
            print(f"Erro ao calcular presença: {e}")

    def salvar(self):
        try:
            conn = conectar_bd()
            self.garantir_tabela(conn)
            cur = cast(Any, conn).cursor()
            ano = int(self.ano.get())
            mes = int(self.mes.get())

            # Total de dias do mês corrente (calendário)
            total_dias_mes = calendar.monthrange(ano, mes)[1]

            # Obter observações já salvas para preservar quando não for informado
            cur_exist = cast(Any, conn).cursor(dictionary=True)
            cast(Any, cur_exist).execute(
                """
                SELECT funcionario_id, observacao
                FROM funcionario_faltas_mensal
                WHERE ano = %s AND mes = %s
                """,
                (ano, mes),
            )
            obs_existente_map = {r["funcionario_id"]: r.get("observacao") for r in cast(Any, cur_exist).fetchall()}
            cast(Any, cur_exist).close()

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

            if conn:
                cast(Any, conn).commit()
            cast(Any, cur).close()
            if conn:
                cast(Any, conn).close()
            
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


