"""
Módulo de diálogos estendidos.
Contém diálogos complexos para folhas de ponto e resumos.
Extraído do main.py (Sprint 15 Fase 2).
"""

from tkinter import (Toplevel, Frame, Label, Button, IntVar, StringVar, Entry, 
                     filedialog, messagebox, BOTH, X, W, RIGHT)
from tkinter import ttk
from datetime import datetime
import os
from config_logs import get_logger

logger = get_logger(__name__)


def abrir_dialogo_folhas_ponto(janela_pai, status_label=None):
    """
    Abre diálogo para configurar e gerar folhas de ponto.
    
    Args:
        janela_pai: Janela principal do Tkinter
        status_label: Label para mostrar status da operação (opcional)
    """
    from utils.dates import nome_mes_pt
    from preencher_folha_ponto import gerar_folhas_de_ponto
    from ui.colors import COLORS
    
    # Importar _run_report_in_background do main.py onde está definida
    import sys
    if 'main' in sys.modules:
        _run_report_in_background = sys.modules['main']._run_report_in_background
    else:
        # Fallback: executar diretamente sem background
        def _run_report_in_background(fn, desc):
            try:
                fn()
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Erro", f"Erro ao {desc}: {e}")
    
    dialog = Toplevel(janela_pai)
    dialog.title("Gerar Folhas de Ponto")
    dialog.geometry("380x200")
    dialog.resizable(False, False)
    dialog.transient(janela_pai)
    dialog.grab_set()

    mes_var = IntVar(value=datetime.today().month)
    ano_var = IntVar(value=datetime.today().year)
    pasta_var = StringVar(value=os.getcwd())

    frame = Frame(dialog, padx=15, pady=15)
    frame.pack(fill=BOTH, expand=True)

    Label(frame, text="Mês:").grid(row=0, column=0, sticky=W, pady=5)
    ttk.Spinbox(frame, from_=1, to=12, width=5, textvariable=mes_var).grid(row=0, column=1, sticky=W)

    Label(frame, text="Ano:").grid(row=1, column=0, sticky=W, pady=5)
    ttk.Spinbox(frame, from_=2020, to=2100, width=7, textvariable=ano_var).grid(row=1, column=1, sticky=W)

    Label(frame, text="Pasta de saída:").grid(row=2, column=0, sticky=W, pady=5)
    entrada_pasta = Entry(frame, textvariable=pasta_var, width=28)
    entrada_pasta.grid(row=2, column=1, sticky=W)

    def escolher_pasta():
        pasta = filedialog.askdirectory()
        if pasta:
            pasta_var.set(pasta)

    Button(frame, text="Escolher…", command=escolher_pasta).grid(row=2, column=2, padx=5)

    def gerar():
        dialog.destroy()
        try:
            try:
                from services.utils.templates import find_template
                base_pdf = find_template("folha de ponto.pdf")
            except Exception:
                base_pdf = os.path.join(os.getcwd(), "Modelos", "folha de ponto.pdf")
                if not os.path.isfile(base_pdf):
                    base_pdf = os.path.join(os.getcwd(), "folha de ponto.pdf")
            if not os.path.isfile(base_pdf):
                messagebox.showerror("Erro", f"Arquivo base não encontrado: {base_pdf}")
                return
            mes = mes_var.get()
            ano = ano_var.get()
            nome_mes = nome_mes_pt(mes)
            saida = os.path.join(pasta_var.get(), f"Folhas_de_Ponto_{nome_mes}_{ano}.pdf")
            if status_label is not None:
                status_label.config(text=f"Gerando folhas de ponto de {nome_mes}/{ano}…")

            def _worker():
                # Executa a geração em background e retorna o caminho de saída
                gerar_folhas_de_ponto(base_pdf, saida, mes_referencia=mes, ano_referencia=ano)
                return saida

            try:
                _run_report_in_background(_worker, f"Folhas de Ponto {nome_mes}/{ano}")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao agendar geração das folhas de ponto: {e}")
        except Exception as e:
            if status_label is not None:
                status_label.config(text="")
            messagebox.showerror("Erro", str(e))

    botoes = Frame(dialog, padx=15, pady=10)
    botoes.pack(fill=X)
    Button(botoes, text="Cancelar", command=dialog.destroy).pack(side=RIGHT, padx=5)
    Button(botoes, text="Gerar", command=gerar, bg=COLORS.co5, fg=COLORS.co0).pack(side=RIGHT)


def abrir_dialogo_resumo_ponto(janela_pai, status_label=None):
    """
    Abre diálogo para configurar e gerar resumo de ponto.
    
    Args:
        janela_pai: Janela principal do Tkinter
        status_label: Label para mostrar status da operação (opcional)
    """
    from utils.dates import nome_mes_pt
    from gerar_resumo_ponto import gerar_resumo_ponto
    from ui.colors import COLORS
    
    # Importar _run_report_in_background do main.py onde está definida
    import sys
    if 'main' in sys.modules:
        _run_report_in_background = sys.modules['main']._run_report_in_background
    else:
        # Fallback: executar diretamente sem background
        def _run_report_in_background(fn, desc):
            try:
                fn()
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Erro", f"Erro ao {desc}: {e}")
    
    dialog = Toplevel(janela_pai)
    dialog.title("Gerar Resumo de Ponto")
    dialog.geometry("320x160")
    dialog.resizable(False, False)
    dialog.transient(janela_pai)
    dialog.grab_set()

    mes_var = IntVar(value=datetime.today().month)
    ano_var = IntVar(value=datetime.today().year)

    frame = Frame(dialog, padx=15, pady=15)
    frame.pack(fill=BOTH, expand=True)

    Label(frame, text="Mês:").grid(row=0, column=0, sticky=W, pady=5)
    ttk.Spinbox(frame, from_=1, to=12, width=5, textvariable=mes_var).grid(row=0, column=1, sticky=W)

    Label(frame, text="Ano:").grid(row=1, column=0, sticky=W, pady=5)
    ttk.Spinbox(frame, from_=2020, to=2100, width=7, textvariable=ano_var).grid(row=1, column=1, sticky=W)

    def gerar():
        dialog.destroy()
        try:
            mes = mes_var.get()
            ano = ano_var.get()
            nome_mes = nome_mes_pt(mes)
            if status_label is not None:
                status_label.config(text=f"Gerando resumo de ponto de {nome_mes}/{ano}…")

            def _worker():
                gerar_resumo_ponto(mes, ano)
                return None

            try:
                _run_report_in_background(_worker, f"Resumo de Ponto {nome_mes}/{ano}")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao agendar resumo de ponto: {e}")
        except Exception as e:
            if status_label is not None:
                status_label.config(text="")
            messagebox.showerror("Erro", str(e))

    botoes = Frame(dialog, padx=15, pady=10)
    botoes.pack(fill=X)
    Button(botoes, text="Cancelar", command=dialog.destroy).pack(side=RIGHT, padx=5)
    Button(botoes, text="Gerar", command=gerar, bg=COLORS.co5, fg=COLORS.co0).pack(side=RIGHT)
