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
    
    Agora integra com services/estatistica_service.py para buscar dados de estatísticas.
    """
    def __init__(self, janela, db_service, frame_getter, cache_ref, escola_id: int = 60, ano_letivo: Optional[str] = None, co_bg=CO_BG, co_fg=CO_FG, co_accent=CO_ACCENT):
        self.janela = janela
        self.db_service = db_service
        self.frame_getter = frame_getter
        self.cache_ref = cache_ref
        # Garantir que `escola_id` seja um int (compatível com services.estatistica_service)
        try:
            self.escola_id: int = int(escola_id)  # ID da escola (padrão: 60)
        except Exception:
            # Fallback seguro caso o valor não seja conversível
            self.escola_id = 60
        self.ano_letivo = ano_letivo  # Ano letivo para filtrar (None = usa ano atual)
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
                # Usar estatistica_service para buscar dados
                from services.estatistica_service import obter_estatisticas_alunos
                
                dados = obter_estatisticas_alunos(escola_id=self.escola_id, ano_letivo=self.ano_letivo)

                if not dados or not dados.get('alunos_por_serie'):
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
                # Verificar se há turmas múltiplas em alguma série
                turmas_detalhadas = dados.get('alunos_por_serie_turma', [])
                
                # Agrupar turmas por série para verificar se há múltiplas
                series_com_multiplas_turmas = {}
                for item in turmas_detalhadas:
                    serie = item['serie']
                    if serie not in series_com_multiplas_turmas:
                        series_com_multiplas_turmas[serie] = []
                    series_com_multiplas_turmas[serie].append(item)
                
                # Preparar labels e quantidades
                labels = []
                quantidades = []
                
                for item in dados['alunos_por_serie']:
                    serie = item['serie']
                    qtd_total = item['quantidade']
                    
                    # Se a série tem múltiplas turmas, mostrar detalhadas
                    if serie in series_com_multiplas_turmas and len(series_com_multiplas_turmas[serie]) > 1:
                        for turma_item in series_com_multiplas_turmas[serie]:
                            turma = turma_item['turma']
                            qtd_turma = turma_item['quantidade']
                            label = f"{serie} {turma}" if turma.strip() else serie
                            labels.append(label)
                            quantidades.append(qtd_turma)
                    else:
                        # Série com turma única, mostrar apenas a série
                        labels.append(serie)
                        quantidades.append(qtd_total)

                # Construir figura do matplotlib (agora com 2 subplots: pizza + colunas mensais)
                from matplotlib.figure import Figure
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

                # Recuperar movimento mensal acumulado (pode falhar sem impactar o gráfico principal)
                movimento_resumo = None
                try:
                    from services.estatistica_service import obter_movimento_mensal_resumo
                    movimento_resumo = obter_movimento_mensal_resumo(escola_id=self.escola_id, ano_letivo=self.ano_letivo)
                except Exception as e_mov:
                    logger.warning(f"Falha ao obter movimento mensal resumo: {e_mov}")

                # Figura 1: Gráfico de Pizza (figura independente)
                fig_pie = Figure(figsize=(8, 5.5), dpi=100, facecolor=self.co1)
                ax = fig_pie.add_subplot(111)
                ax.set_facecolor(self.co1)
                cores = ['#1976d2', '#388e3c', '#d32f2f', '#f57c00', '#7b1fa2', '#0097a7', '#5d4037', '#455a64', '#c2185b', '#afb42b', '#00897b', '#e64a19']
                try:
                    resultado_pie = ax.pie(
                        quantidades,
                        labels= labels,  
                        autopct='%1.1f%%',
                        startangle=90,
                        colors=cores[:len(labels)],
                        textprops={'fontsize': 10, 'weight': 'bold'}
                    )
                    if len(resultado_pie) >= 3:
                        wedges, texts, autotexts = resultado_pie
                        for autotext in autotexts:
                            autotext.set_color('white')
                            autotext.set_fontsize(10)
                            autotext.set_fontweight('bold')
                        # guardar textos das fatias (labels ao redor/do lado do pie)
                        pie_texts = texts
                except Exception:
                    pass

                t1 = ax.set_title('Distribuição de Alunos por Série', fontsize=14, weight='bold', pad=10, color=self.co0, y=1.0)
                try:
                    t1.set_wrap(True)
                except Exception:
                    pass
                legendas = [f'{s}: {q}' for s, q in zip(labels, quantidades)]
                try:
                    # Legenda a esquerda antes do gráfico de pizza 
                    legend = ax.legend(legendas, loc='center left', bbox_to_anchor=(-0.5, 0.5), 
                                     ncol=1, fontsize=8, frameon=True, facecolor=self.co1, edgecolor=self.co0)
                    for text in legend.get_texts():
                        text.set_color(self.co0)
                except Exception:
                    pass
                # Reservar espaço para a legenda à esquerda e para o título no topo
                try:
                    fig_pie.subplots_adjust(top=0.82, bottom=0.12, left=0.36, right=0.98)
                except Exception:
                    pass

                # Guardar meta-informações para redimensionamento dinâmico de fontes
                try:
                    pie_autotexts = autotexts if 'autotexts' in locals() else []
                except Exception:
                    pie_autotexts = []
                try:
                    pie_texts = pie_texts if 'pie_texts' in locals() else []
                except Exception:
                    pie_texts = []
                try:
                    # incluir tamanhos-base em pixels para referência ao redimensionar
                    base_w, base_h = fig_pie.get_figwidth(), fig_pie.get_figheight()
                    setattr(fig_pie, '_dash_meta', {
                        'title': t1,
                        'legend': legend if 'legend' in locals() else None,
                        'autotexts': pie_autotexts,
                        'pie_texts': pie_texts,
                        'base_title': 14,
                        'base_legend': 8,
                        'base_autotext': 10,
                        'base_tick': 9,
                        'base_fig_inches': (base_w, base_h),
                        'base_fig_pixels_height': base_h * fig_pie.dpi
                    })
                except Exception:
                    pass

                # Figura 2: barras mensais empilhadas (figura independente)
                try:
                    fig_bars = Figure(figsize=(8, 5.5), dpi=100, facecolor=self.co1)
                    ax2 = fig_bars.add_subplot(111)
                    ax2.set_facecolor(self.co1)
                    if movimento_resumo and movimento_resumo.get('meses'):
                        meses_data = movimento_resumo['meses']
                        labels_meses = [m['mes'] for m in meses_data]
                        # Cada mês terá uma única coluna empilhada: ativos (base), transferidos (meio), evadidos (topo)
                        base_ativos = [m['ativos'] for m in meses_data]
                        seg_transferidos = [m['transferidos'] for m in meses_data]
                        seg_evadidos = [m['evadidos'] for m in meses_data]

                        import numpy as np
                        x = np.arange(len(labels_meses))

                        # Barras empilhadas (cores com melhor contraste no fundo azul)
                        b_ativos = ax2.bar(x, base_ativos, label='Ativos', color='#4CAF50', edgecolor='#FFFFFF', linewidth=0.6)
                        bottom_transferidos = base_ativos
                        b_transferidos = ax2.bar(
                            x, seg_transferidos, bottom=bottom_transferidos,
                            label='Transferidos', color='#FFC107', edgecolor='#FFFFFF', linewidth=0.6
                        )
                        # calcular bottom para evadidos (ativos + transferidos)
                        bottom_evadidos = [a + t for a, t in zip(base_ativos, seg_transferidos)]
                        b_evadidos = ax2.bar(
                            x, seg_evadidos, bottom=bottom_evadidos,
                            label='Evadidos', color='#E53935', edgecolor='#FFFFFF', linewidth=0.6
                        )

                        ax2.set_xticks(x)
                        nomes_meses = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
                        ax2.set_xticklabels([nomes_meses[m-1] for m in labels_meses], fontsize=9, color=self.co0)
                        ax2.tick_params(axis='y', colors=self.co0)
                        # Mostrar apenas as spines dos eixos (left e bottom).
                        for loc, spine in ax2.spines.items():
                            if loc in ('top', 'right'):
                                try:
                                    spine.set_visible(False)
                                except Exception:
                                    pass
                            else:
                                try:
                                    spine.set_visible(True)
                                    spine.set_color(self.co0)
                                except Exception:
                                    pass
                        ax2.set_ylabel('Quantidade', color=self.co0, fontsize=10)
                        t2 = ax2.set_title('Movimento Mensal', fontsize=14, weight='bold', color=self.co0, pad=10, y=1.0)
                        try:
                            t2.set_wrap(True)
                        except Exception:
                            pass
                        # Legenda a direita depois do gráfico de barras
                        legend2 = ax2.legend(loc='center left', bbox_to_anchor=(1.05, 0.5), ncol=1, fontsize=9, frameon=True)
                        legend2.get_frame().set_facecolor(self.co1)
                        legend2.get_frame().set_edgecolor(self.co0)
                        for text in legend2.get_texts():
                            text.set_color(self.co0)
                        # Reservar espaço para a legenda à direita e para o título no topo
                        try:
                            fig_bars.subplots_adjust(top=0.82, bottom=0.12, left=0.08, right=0.78)
                        except Exception:
                            pass

                        # Guardar meta para redimensionamento dinâmico
                        try:
                            base_w2, base_h2 = fig_bars.get_figwidth(), fig_bars.get_figheight()
                            setattr(fig_bars, '_dash_meta', {
                                'title': t2,
                                'legend': legend2 if 'legend2' in locals() else None,
                                'autotexts': [],
                                'base_title': 14,
                                'base_legend': 9,
                                'base_autotext': 8,
                                'base_tick': 9,
                                'base_fig_inches': (base_w2, base_h2),
                                'base_fig_pixels_height': base_h2 * fig_bars.dpi
                            })
                        except Exception:
                            pass

                        # Anotar totais no topo de cada coluna
                        try:
                            for i, (a, t, e) in enumerate(zip(base_ativos, seg_transferidos, seg_evadidos)):
                                total = a + t + e
                                if total > 0:
                                    ax2.text(i, total + 0.5, str(total), ha='center', va='bottom', fontsize=8, color=self.co0)
                        except Exception:
                            pass
                    else:
                        ax2.text(0.5, 0.5, 'Sem dados mensais', ha='center', va='center', color=self.co0, fontsize=12, transform=ax2.transAxes)
                        ax2.set_axis_off()
                except Exception as e_cols:
                    logger.warning(f"Falha ao gerar gráfico mensal (empilhado): {e_cols}")

                # Lista de figuras para renderização em grade no frame
                figures = []
                try:
                    figures.append(fig_pie)
                except Exception:
                    pass
                try:
                    if 'fig_bars' in locals():
                        figures.append(fig_bars)
                except Exception:
                    pass

                # Atualizar UI na thread principal
                def _on_main():
                    nonlocal figures
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
                            # Usar chaves corretas retornadas por estatistica_service
                            total_alunos = dados.get('total_alunos', 0)  # Inclui ativos + transferidos
                            alunos_ativos = dados.get('alunos_ativos', 0)
                            alunos_transferidos = dados.get('alunos_transferidos', 0)
                            
                            Label(totais_frame, text=f"Total (Ativos + Transferidos): {total_alunos}", 
                                  font=('Calibri', 12, 'bold'), bg=self.co1, fg=self.co0).pack(side='left', padx=20)
                            Label(totais_frame, text=f"Ativos: {alunos_ativos}", 
                                  font=('Calibri', 12, 'bold'), bg=self.co1, fg='#4CAF50').pack(side='left', padx=20)
                            Label(totais_frame, text=f"Transferidos: {alunos_transferidos}", 
                                  font=('Calibri', 12, 'bold'), bg=self.co1, fg='#FF9800').pack(side='left', padx=20)
                            
                            # Alunos por turno
                            turnos = dados.get('alunos_por_turno', [])
                            if turnos:
                                turno_str = " | ".join([f"{t['turno']}: {t['quantidade']}" for t in turnos])
                                Label(totais_frame, text=turno_str, font=('Calibri', 12, 'bold'), bg=self.co1, fg=self.co0).pack(side='left', padx=20)
                        except Exception:
                            logger.exception("Erro ao criar labels de totais no dashboard")

                        # Verificar novamente dashboard_frame antes de criar o grafico
                        if not getattr(dashboard_frame, 'winfo_exists', lambda: False)():
                            logger.debug("dashboard_frame foi destruído antes de criar o gráfico — abortando")
                            return

                        grafico_frame = Frame(dashboard_frame, bg=self.co1)
                        grafico_frame.pack(fill='both', expand=True)

                        # Distribuir as figuras em uma matriz dinâmica (linhas x colunas)
                        try:
                            import math
                            figs = figures if isinstance(figures, (list, tuple)) else [figures]
                            n = len(figs)
                            if n == 0:
                                Label(grafico_frame, text="Sem gráficos para exibir", bg=self.co1, fg=self.co0).pack(pady=10)
                            else:
                                cols = int(math.ceil(math.sqrt(n)))
                                rows = int(math.ceil(n / cols))

                                for r in range(rows):
                                    grafico_frame.grid_rowconfigure(r, weight=1, uniform='row')
                                for c in range(cols):
                                    grafico_frame.grid_columnconfigure(c, weight=1, uniform='col')

                                canvases = []
                                for idx, f in enumerate(figs):
                                    r = idx // cols
                                    c = idx % cols
                                    cell = Frame(grafico_frame, bg=self.co1)
                                    cell.grid(row=r, column=c, sticky='nsew', padx=8, pady=8)
                                    cv = FigureCanvasTkAgg(f, master=cell)
                                    cv.draw()
                                    cv.get_tk_widget().pack(fill='both', expand=True)
                                    canvases.append(cv)
                                    # Bind resize handler to adjust figure size and font sizes proportionally
                                    try:
                                        def _make_resizer(fig_obj, canvas_obj):
                                            def _on_resize(event):
                                                meta = getattr(fig_obj, '_dash_meta', None)
                                                try:
                                                    dpi = fig_obj.dpi or 100
                                                    # compute new figure size in inches and apply
                                                    new_w_in = max(1.0, event.width / dpi)
                                                    new_h_in = max(0.5, event.height / dpi)
                                                    try:
                                                        fig_obj.set_size_inches(new_w_in, new_h_in, forward=True)
                                                    except Exception:
                                                        pass

                                                    # scale fonts based on height ratio vs base pixels
                                                    if meta:
                                                        base_h_px = meta.get('base_fig_pixels_height') or (fig_obj.get_figheight() * dpi)
                                                        if base_h_px:
                                                            scale = event.height / base_h_px
                                                        else:
                                                            scale = 1.0

                                                        # Title
                                                        title = meta.get('title')
                                                        if title:
                                                            try:
                                                                title.set_fontsize(max(8, int(meta.get('base_title', 14) * scale)))
                                                            except Exception:
                                                                pass
                                                        # Legend
                                                        legend_obj = meta.get('legend')
                                                        if legend_obj:
                                                            for text in legend_obj.get_texts():
                                                                try:
                                                                    text.set_fontsize(max(6, int(meta.get('base_legend', 9) * scale)))
                                                                except Exception:
                                                                    pass
                                                        # Autotexts (pie percents)
                                                        for at in meta.get('autotexts', []):
                                                            try:
                                                                at.set_fontsize(max(6, int(meta.get('base_autotext', 10) * scale)))
                                                            except Exception:
                                                                pass
                                                        # Pie slice labels (texts returned by ax.pie)
                                                        for pt in meta.get('pie_texts', []):
                                                            try:
                                                                pt.set_fontsize(max(6, int(meta.get('base_legend', 8) * scale)))
                                                            except Exception:
                                                                pass
                                                        # Tick labels
                                                        ax_local = fig_obj.axes[0] if fig_obj.axes else None
                                                        if ax_local:
                                                            for lbl in ax_local.get_xticklabels() + ax_local.get_yticklabels():
                                                                try:
                                                                    lbl.set_fontsize(max(6, int(meta.get('base_tick', 9) * scale)))
                                                                except Exception:
                                                                    pass

                                                    try:
                                                        canvas_obj.draw_idle()
                                                    except Exception:
                                                        pass
                                                except Exception:
                                                    pass
                                            return _on_resize
                                        cv_widget = cv.get_tk_widget()
                                        cv_widget.bind('<Configure>', _make_resizer(f, cv))
                                    except Exception:
                                        pass
                                self.dashboard_canvas = canvases
                        except Exception as e:
                            try:
                                Label(grafico_frame, text=f"Erro ao renderizar gráficos: {e}", bg=self.co1, fg='red').pack(pady=10)
                            except Exception:
                                logger.exception("Erro ao renderizar gráficos e também falha ao exibir mensagem")

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
