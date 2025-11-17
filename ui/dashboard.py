from typing import Any, Optional
from threading import Thread
from tkinter import Toplevel, Frame, Label, Button, messagebox
from tkinter.ttk import Progressbar
from config_logs import get_logger

logger = get_logger(__name__)


class ProgressWindow:
    def __init__(self, parent, titulo: str, bg_color: str = '#003A70', fg_color: str = '#F5F5F5', btn_bg: str = '#F7B731', modal: bool = False):
        self.parent = parent
        self.titulo = titulo
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.btn_bg = btn_bg
        self.modal = modal
        self.win = None
        self.pb = None

    def show(self):
        try:
            self.win = Toplevel(self.parent)
            self.win.title(self.titulo)
            self.win.geometry("420x120")
            self.win.resizable(False, False)
            try:
                self.win.transient(self.parent)
            except Exception:
                logger.exception("ProgressWindow: falha ao tornar janela transitória")
            try:
                if self.modal:
                    self.win.grab_set()
            except Exception:
                logger.exception("ProgressWindow: falha ao aplicar grab_set()")

            frame = Frame(self.win, bg=self.bg_color, padx=12, pady=10)
            frame.pack(fill='both', expand=True)

            Label(frame, text=f"{self.titulo} — gerando, aguarde...", font=('Calibri', 11, 'bold'), bg=self.bg_color, fg=self.fg_color).pack(pady=(4, 8))
            self.pb = Progressbar(frame, mode='indeterminate', length=360)
            self.pb.pack(pady=4)
            try:
                self.pb.start(10)
            except Exception:
                pass

            def fechar():
                try:
                    if self.pb:
                        self.pb.stop()
                except Exception:
                    pass
                try:
                    if self.win and getattr(self.win, 'winfo_exists', lambda: False)():
                        self.win.destroy()
                except Exception:
                    pass

            Button(frame, text="Fechar", width=12, command=fechar, bg=self.btn_bg, fg=self.fg_color).pack(pady=(8, 0))
            self.win.update()
        except Exception:
            logger.exception("ProgressWindow.show falhou")

    def close(self):
        try:
            if self.win and getattr(self.win, 'winfo_exists', lambda: False)():
                try:
                    self.win.destroy()
                except Exception:
                    pass
        except Exception:
            logger.exception("ProgressWindow.close falhou")


def run_report_in_background(fn, descricao: str, janela, status_label=None, co1: str = '#003A70', co0: str = '#F5F5F5', co6: str = '#F7B731'):
    """Executa `fn()` em background mostrando uma janela de progresso ligada à `janela`.
    Usa `utils.executor.submit_background` se disponível, senão faz fallback para Thread.
    """
    progress = ProgressWindow(janela, descricao, bg_color=co1, fg_color=co0, btn_bg=co6)

    def _on_done(resultado):
        try:
            if status_label is not None:
                try:
                    status_label.config(text=f"{descricao} gerado com sucesso.")
                except Exception:
                    pass
        except Exception:
            pass

        try:
            try:
                janela.after(0, progress.close)
            except Exception:
                pass

            if isinstance(resultado, str) and resultado:
                try:
                    messagebox.showinfo(descricao, f"Arquivo gerado em:\n{resultado}")
                except Exception:
                    pass
            else:
                try:
                    messagebox.showinfo(descricao, f"{descricao} gerado com sucesso.")
                except Exception:
                    pass
        except Exception:
            pass

    def _on_error(exc):
        try:
            try:
                janela.after(0, progress.close)
            except Exception:
                pass
            try:
                messagebox.showerror(f"Erro - {descricao}", f"Falha ao gerar {descricao}: {exc}")
            except Exception:
                pass
            try:
                if status_label is not None:
                    status_label.config(text="")
            except Exception:
                pass
        except Exception:
            pass

    def _worker():
        return fn()

    # Mostrar a janela de progresso no thread principal
    try:
        progress.show()
    except Exception:
        logger.exception("Erro ao mostrar ProgressWindow para: %s", descricao)

    try:
        from utils.executor import submit_background
        submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=janela)
    except Exception:
        # Fallback: criar Thread e agendar callbacks via janela.after
        def _thread_worker():
            try:
                res = _worker()
                try:
                    janela.after(0, lambda: _on_done(res))
                except Exception:
                    pass
            except Exception as e:
                try:
                    janela.after(0, lambda: _on_error(e))
                except Exception:
                    pass

        Thread(target=_thread_worker, daemon=True).start()


def run_report_module_returning_buffer(module_fn, descricao: str, janela, status_label=None, co1: str = '#003A70', co0: str = '#F5F5F5', co6: str = '#F7B731'):
    def _worker():
        res = module_fn()
        if not res:
            return None
        try:
            from gerarPDF import salvar_e_abrir_pdf
            return salvar_e_abrir_pdf(res)
        except Exception:
            raise

    run_report_in_background(_worker, descricao, janela=janela, status_label=status_label, co1=co1, co0=co0, co6=co6)


from ui.theme import CO_BG, CO_FG, CO_ACCENT, CO_WARN


class DashboardManager:
    """Manager responsável por criar e atualizar o dashboard dentro de um frame.

    Recebe um `DbService` (com método `connection()`), uma função `obter_estatisticas_alunos`
    e um `frame_getter` que retorna o `frame_tabela` onde o dashboard deve ser renderizado.
    """
    def __init__(self, janela, db_service, obter_estatisticas_alunos, frame_getter, cache_ref, co_bg=CO_BG, co_fg=CO_FG, co_accent=CO_ACCENT):
        self.janela = janela
        self.db_service = db_service
        self.obter_estatisticas_alunos = obter_estatisticas_alunos
        self.frame_getter = frame_getter
        self.cache_ref = cache_ref
        self.co1 = co_bg
        self.co0 = co_fg
        self.co4 = co_accent
        self.dashboard_canvas = None
        # Token to track the currently active background worker for the dashboard.
        # Each time a new dashboard is created we bump this token; workers compare
        # their captured token and silently abort if it's stale. This prevents
        # workers from logging warnings when older workers try to update a
        # destroyed UI after the user navigated away.
        self._worker_token = 0
        # Keep a reference to the last created dashboard frame so we can
        # verify the worker is updating the intended widget instance.
        self._last_dashboard_frame = None

    def criar_dashboard(self):
        """Cria o dashboard dentro do `frame_tabela` atual (obtido via `frame_getter`)."""
        try:
            frame_tabela = self.frame_getter()
        except Exception:
            frame_tabela = None

        if frame_tabela is None:
            return

        # Limpar dashboard anterior se existir
        if self.dashboard_canvas is not None:
            try:
                self.dashboard_canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self.dashboard_canvas = None

        # Criar frame para o dashboard com UI de carregamento e manter a UI responsiva
        dashboard_frame = Frame(frame_tabela, bg=self.co1)
        dashboard_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Frame para informações gerais (topo)
        info_frame = Frame(dashboard_frame, bg=self.co1)
        info_frame.pack(fill='x', pady=(0, 10))

        title_label = Label(info_frame, text="Dashboard - Carregando...", font=('Calibri', 16, 'bold'), bg=self.co1, fg=self.co0)
        title_label.pack(pady=(0, 10))

        loading_frame = Frame(dashboard_frame, bg=self.co1)
        loading_frame.pack(fill='both', expand=True)
        loading_label = Label(loading_frame, text="Carregando dados, aguarde...", font=('Calibri', 12), bg=self.co1, fg=self.co0)
        loading_label.pack(pady=20)
        progress = Progressbar(loading_frame, mode='indeterminate')
        progress.pack(pady=10, padx=20)
        try:
            progress.start(10)
        except Exception:
            pass

        # Trabalho pesado em background
        # Bump worker token and capture a snapshot token for this worker.
        self._worker_token = (self._worker_token or 0) + 1
        local_worker_token = self._worker_token

        def _worker(local_worker_token=local_worker_token):
            try:
                dados = self.obter_estatisticas_alunos()

                if not dados or not dados.get('por_serie'):
                    def _on_empty():
                        try:
                            progress.stop()
                        except Exception:
                            pass
                        try:
                            loading_frame.destroy()
                        except Exception:
                            pass
                        Label(dashboard_frame, text="Nenhum dado disponível para exibir no dashboard", font=('Calibri', 14), bg=self.co1, fg=self.co0).pack(pady=50)
                    self.janela.after(0, _on_empty)
                    return

                # Determinar ano letivo em background
                try:
                    with self.db_service.connection() as conn_temp:
                        if conn_temp:
                            cursor_temp = conn_temp.cursor()
                            try:
                                cursor_temp.execute("SELECT ano_letivo FROM anosletivos WHERE YEAR(CURDATE()) = ano_letivo")
                                resultado_ano = cursor_temp.fetchone()
                                if not resultado_ano:
                                    cursor_temp.execute("SELECT ano_letivo FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                                    resultado_ano = cursor_temp.fetchone()
                                if resultado_ano:
                                    if isinstance(resultado_ano, (list, tuple)):
                                        ano_val = resultado_ano[0]
                                    elif isinstance(resultado_ano, dict):
                                        ano_val = resultado_ano.get('ano_letivo') or next(iter(resultado_ano.values()), None)
                                    else:
                                        ano_val = resultado_ano
                                    ano_letivo_exibir = ano_val if ano_val is not None else "Corrente"
                                else:
                                    ano_letivo_exibir = "Corrente"
                            finally:
                                try:
                                    cursor_temp.close()
                                except Exception:
                                    pass
                        else:
                            ano_letivo_exibir = "Corrente"
                except Exception:
                    ano_letivo_exibir = "Corrente"

                # Preparar dados para o gráfico
                series = [item['serie'] for item in dados['por_serie']]
                quantidades = [item['quantidade'] for item in dados['por_serie']]

                # Construir figura do matplotlib
                from matplotlib.figure import Figure
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

                fig = Figure(figsize=(11, 6.5), dpi=100, facecolor=self.co1)
                ax = fig.add_subplot(111)
                ax.set_facecolor(self.co1)
                cores = ['#1976d2', '#388e3c', '#d32f2f', '#f57c00', '#7b1fa2', '#0097a7', '#5d4037', '#455a64', '#c2185b', '#afb42b']
                resultado_pie = ax.pie(
                    quantidades,
                    labels=series,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=cores[:len(series)],
                    textprops={'fontsize': 10, 'weight': 'bold', 'color': self.co0}
                )

                try:
                    if len(resultado_pie) >= 3:
                        wedges, texts, autotexts = resultado_pie
                        for autotext in autotexts:
                            autotext.set_color('white')
                            autotext.set_fontsize(10)
                            autotext.set_fontweight('bold')
                    else:
                        wedges, texts = resultado_pie
                except Exception:
                    pass

                ax.set_title('Distribuição de Alunos por Série', fontsize=14, weight='bold', pad=25, color=self.co0)
                legendas = [f'{s}: {q} alunos' for s, q in zip(series, quantidades)]
                try:
                    legend = ax.legend(legendas, loc='center left', bbox_to_anchor=(1.15, 0.5), fontsize=9, frameon=True, facecolor=self.co1, edgecolor=self.co0)
                    for text in legend.get_texts():
                        text.set_color(self.co0)
                except Exception:
                    pass

                fig.tight_layout(rect=(0, 0, 0.85, 0.95))

                # Atualizar UI na thread principal
                def _on_main():
                    nonlocal fig
                    # Antes de manipular o UI, verificar se os frames principais ainda existem.
                    try:
                        # Parar o progresso e remover o carregador, ignorando erros
                        try:
                            progress.stop()
                        except Exception:
                            pass
                        try:
                            loading_frame.destroy()
                        except Exception:
                            pass

                        # Se o dashboard_frame foi destruído enquanto o worker rodava,
                        # abortamos a atualização já que não há mais onde desenhar.
                        # If this worker is stale (a newer dashboard was requested),
                        # silently abort without logging warnings.
                        if local_worker_token != self._worker_token:
                            logger.debug("dashboard worker obsoleto (token mismatch) — abortando atualização silenciosamente")
                            return

                        if not (dashboard_frame and getattr(dashboard_frame, 'winfo_exists', lambda: False)()):
                            logger.debug("dashboard_frame não existe mais — abortando atualização do dashboard")
                            return

                        if not (info_frame and getattr(info_frame, 'winfo_exists', lambda: False)()):
                            logger.debug("info_frame não existe mais — abortando atualização do dashboard")
                            return

                        # Protege a atualização do título caso o widget já tenha sido destruído
                        try:
                            if title_label is not None and getattr(title_label, 'winfo_exists', lambda: False)():
                                title_label.config(text=f"Dashboard - Alunos Matriculados no Ano Letivo de {ano_letivo_exibir}")
                            else:
                                logger.warning("title_label não existe mais ao atualizar dashboard")
                        except Exception:
                            logger.exception("Falha ao atualizar title_label do dashboard")

                        totais_frame = Frame(info_frame, bg=self.co1)
                        totais_frame.pack()
                        try:
                            Label(totais_frame, text=f"Total Matriculados: {dados['total_matriculados']}", font=('Calibri', 12, 'bold'), bg=self.co1, fg=self.co0).pack(side='left', padx=20)
                            Label(totais_frame, text=f"Ativos: {dados['total_ativos']}", font=('Calibri', 12, 'bold'), bg=self.co1, fg=self.co0).pack(side='left', padx=20)
                            Label(totais_frame, text=f"Transferidos: {dados['total_transferidos']}", font=('Calibri', 12, 'bold'), bg=self.co1, fg=self.co0).pack(side='left', padx=20)
                        except Exception:
                            logger.exception("Erro ao criar labels de totais no dashboard")

                        # Verificar novamente dashboard_frame antes de criar o grafico
                        if not getattr(dashboard_frame, 'winfo_exists', lambda: False)():
                            logger.debug("dashboard_frame foi destruído antes de criar o gráfico — abortando")
                            return

                        grafico_frame = Frame(dashboard_frame, bg=self.co1)
                        grafico_frame.pack(fill='both', expand=True)

                        try:
                            canvas = FigureCanvasTkAgg(fig, master=grafico_frame)
                            canvas.draw()
                            canvas.get_tk_widget().pack(fill='both', expand=True)
                            self.dashboard_canvas = canvas
                        except Exception as e:
                            try:
                                Label(grafico_frame, text=f"Erro ao renderizar gráfico: {e}", bg=self.co1, fg='red').pack(pady=10)
                            except Exception:
                                logger.exception("Erro ao renderizar gráfico e também falha ao exibir mensagem")

                        # Link the last created dashboard frame so future workers can
                        # verify they still target the correct instance.
                        try:
                            self._last_dashboard_frame = dashboard_frame
                        except Exception:
                            pass

                        btn_atualizar = Button(dashboard_frame, text="🔄 Atualizar Dashboard", font=('Calibri', 11, 'bold'), bg=self.co4, fg=self.co1, relief='raised', command=lambda: self.atualizar_dashboard())
                        btn_atualizar.pack(pady=10)
                    except Exception as e:
                        logger.exception("Erro durante atualização do _on_main do dashboard: %s", e)

                self.janela.after(0, _on_main)
            except Exception as e:
                def _on_error():
                    try:
                        progress.stop()
                    except Exception:
                        pass
                    try:
                        loading_frame.destroy()
                    except Exception:
                        pass
                    messagebox.showerror("Dashboard", f"Falha ao gerar dashboard: {e}")
                self.janela.after(0, _on_error)

        try:
            from utils.executor import submit_background
            submit_background(_worker, janela=self.janela)
        except Exception:
            try:
                from utils.executor import submit_background
                submit_background(_worker, janela=self.janela)
            except Exception:
                from threading import Thread
                Thread(target=_worker, daemon=True).start()

    def atualizar_dashboard(self):
        try:
            self.cache_ref['timestamp'] = None
            self.cache_ref['dados'] = None
        except Exception:
            pass
        try:
            self.criar_dashboard()
        except Exception:
            pass

"""Stub for dashboard UI component.

Move the `criar_dashboard` / dashboard-related functions from `main.py` here
incrementally. Keep thin wrappers that call service-layer functions.
"""
from typing import Any


def criar_dashboard(root: Any, executor=None):
    """Placeholder: original `criar_dashboard` should be migrated here.
    For now, this function is a stub to be implemented incrementally.
    """
    # TODO: move implementation from main.py
    raise NotImplementedError("criar_dashboard not migrated yet")
