"""
Módulo de diálogos de relatórios.
Contém interfaces para configuração de relatórios avançados.
Extraído do main.py (Sprint 15 Fase 2).
"""

from tkinter import (Toplevel, Frame, Label, StringVar, IntVar, BooleanVar,
                     Radiobutton, Checkbutton, messagebox, BOTH, X, W, RIGHT)
from tkinter import ttk
from src.ui.colors import COLORS


def abrir_relatorio_avancado(janela_pai, status_label, gerar_func):
    """
    Abre interface para configuração de relatório avançado de notas.
    
    Args:
        janela_pai: Janela principal do Tkinter
        status_label: Label para mostrar status da operação (opcional)
        gerar_func: Função que gera o relatório (gerar_relatorio_notas)
    """
    # Criar janela para configuração de relatório avançado
    janela_relatorio = Toplevel(janela_pai)
    janela_relatorio.title("Relatório de Notas - Opções Avançadas")
    janela_relatorio.geometry("550x480")
    janela_relatorio.resizable(False, False)
    janela_relatorio.transient(janela_pai)  # Torna a janela dependente da principal
    janela_relatorio.grab_set()  # Torna a janela modal
    janela_relatorio.configure(bg=COLORS.co0)

    # Configurar estilos ttk para tema moderno e consistente
    try:
        style = ttk.Style()
        # tentar um tema mais moderno quando disponível
        for th in ("clam", "alt", "default"):
            try:
                style.theme_use(th)
                break
            except Exception:
                pass
    except Exception:
        style = ttk.Style()

    style.configure("Primary.TButton", background=COLORS.co5, foreground=COLORS.co0, font=("Segoe UI", 10, "bold"))
    style.map("Primary.TButton", background=[('active', COLORS.co4)])
    style.configure("Secondary.TButton", background="#EEEEEE", foreground="#333333", font=("Segoe UI", 10))
    style.configure("TLabel", background=COLORS.co0, foreground=COLORS.co7, font=("Segoe UI", 10))
    
    # Variáveis para armazenar as opções
    bimestre_var = StringVar(value="1º bimestre")
    nivel_var = StringVar(value="iniciais")
    ano_letivo_var = IntVar(value=2025)
    status_var = StringVar(value="Ativo")
    incluir_transferidos = BooleanVar(value=False)
    preencher_zeros = BooleanVar(value=False)
    
    # Frame principal
    frame_principal = Frame(janela_relatorio, padx=20, pady=20)
    frame_principal.pack(fill=BOTH, expand=True)
    
    # Título
    Label(frame_principal, text="Configurar Relatório de Notas", 
          font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky=W)
    
    # Bimestre
    Label(frame_principal, text="Bimestre:", anchor=W).grid(row=1, column=0, sticky=W, pady=5)
    bimestres = ["1º bimestre", "2º bimestre", "3º bimestre", "4º bimestre"]
    combo_bimestre = ttk.Combobox(frame_principal, textvariable=bimestre_var, values=bimestres, 
                                   state="readonly", width=20)
    combo_bimestre.grid(row=1, column=1, sticky=W, pady=5)
    
    # Nível de ensino
    Label(frame_principal, text="Nível de ensino:", anchor=W).grid(row=2, column=0, sticky=W, pady=5)
    frame_nivel = Frame(frame_principal)
    frame_nivel.grid(row=2, column=1, sticky=W, pady=5)
    Radiobutton(frame_nivel, text="Séries iniciais (1º ao 5º)", variable=nivel_var, 
                value="iniciais").pack(anchor=W)
    Radiobutton(frame_nivel, text="Séries finais (6º ao 9º)", variable=nivel_var, 
                value="finais").pack(anchor=W)
    
    # Ano letivo
    Label(frame_principal, text="Ano letivo:", anchor=W).grid(row=3, column=0, sticky=W, pady=5)
    anos = ["2023", "2024", "2025", "2026", "2027"]
    combo_ano = ttk.Combobox(frame_principal, textvariable=ano_letivo_var, values=anos, 
                             state="readonly", width=20)
    combo_ano.grid(row=3, column=1, sticky=W, pady=5)
    
    # Status de matrícula
    Label(frame_principal, text="Status de matrícula:", anchor=W).grid(row=4, column=0, sticky=W, pady=5)
    frame_status = Frame(frame_principal)
    frame_status.grid(row=4, column=1, sticky=W, pady=5)
    Radiobutton(frame_status, text="Apenas ativos", variable=status_var, value="Ativo").pack(anchor=W)
    Checkbutton(frame_status, text="Incluir transferidos", variable=incluir_transferidos).pack(anchor=W)
    
    # Opções de exibição
    Label(frame_principal, text="Opções de exibição:", anchor=W).grid(row=5, column=0, sticky=W, pady=5)
    frame_opcoes = Frame(frame_principal)
    frame_opcoes.grid(row=5, column=1, sticky=W, pady=5)
    Checkbutton(frame_opcoes, text="Preencher notas em branco com zeros", 
                variable=preencher_zeros).pack(anchor=W)
    
    # Frame para botões
    frame_botoes = Frame(janela_relatorio, padx=20, pady=15, bg=COLORS.co0)
    frame_botoes.pack(fill=X)
    
    # Função para gerar o relatório
    def gerar_relatorio():
        bimestre = bimestre_var.get()
        nivel = nivel_var.get()
        ano = ano_letivo_var.get()
        preencher_com_zeros = preencher_zeros.get()
        
        # Configurar status de matrícula
        status: list[str]
        if incluir_transferidos.get():
            status = ["Ativo", "Transferido"]
        else:
            status = [status_var.get()]
        
        # Fechar a janela
        janela_relatorio.destroy()
        
        # Exibir feedback ao usuário
        if status_label is not None:
            status_label.config(text=f"Gerando relatório de notas para {bimestre} ({nivel})...")
        janela_pai.update()
        
        # Gerar o relatório
        try:
            resultado = gerar_func(
                bimestre=bimestre,
                nivel_ensino=nivel,
                ano_letivo=ano,
                status_matricula=status,
                preencher_nulos=preencher_com_zeros
            )
            
            if resultado:
                if status_label is not None:
                    status_label.config(text=f"Relatório gerado com sucesso!")
            else:
                if status_label is not None:
                    status_label.config(text=f"Nenhum dado encontrado para o relatório.")
                messagebox.showwarning("Sem dados", 
                                      f"Não foram encontrados dados para o {bimestre} no nível {nivel}.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório: {str(e)}")
            if status_label is not None:
                status_label.config(text="")
    
    # Botões (usando ttk para consistência)
    ttk.Button(frame_botoes, text="Cancelar", command=janela_relatorio.destroy, style="Secondary.TButton").pack(side=RIGHT, padx=5)
    ttk.Button(frame_botoes, text="Gerar", command=gerar_relatorio, style="Primary.TButton").pack(side=RIGHT, padx=5)
