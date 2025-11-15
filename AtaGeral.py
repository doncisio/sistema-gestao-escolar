"""
Módulo de Gerenciamento de Atas

Este módulo unifica as funcionalidades de geração de atas gerais para diferentes níveis de ensino,
facilitando a manutenção e promovendo a reutilização de código.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from Ata_1a5ano import ata_geral as ata_1a5
from Ata_6a9ano import ata_geral_6a9ano as ata_6a9
from Ata_1a9ano import ata_geral_1a9ano as ata_1a9
import traceback

def gerar_ata_por_nivel(nivel="Séries Iniciais", ano_letivo=2025):
    """
    Função unificada para gerar atas por nível de ensino.
    
    Args:
        nivel (str): "Séries Iniciais" (1º ao 5º ano), "Séries Finais" (6º ao 9º ano) ou "Ensino Fundamental Completo" (1º ao 9º ano)
        ano_letivo (int): O ano letivo para o qual a ata será gerada
    
    Returns:
        bool: True se a operação foi bem sucedida, False caso contrário
    """
    try:
        # Aqui precisaríamos modificar as funções ata_1a5 e ata_6a9 para aceitar o ano_letivo como parâmetro
        # Como isso exigiria modificações nas funções originais, por enquanto apenas notificamos sobre o parâmetro
        if nivel == "Séries Iniciais":
            # Idealmente: ata_1a5(ano_letivo=ano_letivo)
            print(f"Gerando ata para Séries Iniciais, ano letivo: {ano_letivo}")
            ata_1a5()
        elif nivel == "Séries Finais":
            # Idealmente: ata_6a9(ano_letivo=ano_letivo)
            print(f"Gerando ata para Séries Finais, ano letivo: {ano_letivo}")
            ata_6a9()
        elif nivel == "Ensino Fundamental Completo":
            print(f"Gerando ata para Ensino Fundamental Completo, ano letivo: {ano_letivo}")
            ata_1a9()
        else:
            raise ValueError(f"Nível de ensino não reconhecido: {nivel}")
        return True
    except Exception as e:
        print(f"Erro ao gerar ata para {nivel}: {str(e)}")
        traceback.print_exc()
        return False

def abrir_interface_ata(janela_pai=None, status_label=None):
    """
    Abre uma interface para o usuário selecionar o nível de ensino para gerar a ata.
    
    Args:
        janela_pai: Janela pai (principal) que chamou esta interface
        status_label: Label para exibir mensagens de status na interface principal
    """
    # Exibir mensagem de status se disponível
    if status_label:
        status_label.config(text="Abrindo interface de Ata Geral...")
    
    # Criar janela modal
    janela = tk.Toplevel(janela_pai)
    janela.title("Gerar Ata Geral")
    janela.geometry("400x300")  # Aumentei altura para acomodar nova opção
    janela.resizable(False, False)
    janela.transient(janela_pai)  # Torna modal em relação à janela pai
    janela.grab_set()  # Impede interação com outras janelas
    
    # Centralizar na tela
    if janela_pai:
        janela.geometry("+%d+%d" % (
            janela_pai.winfo_rootx() + (janela_pai.winfo_width() / 2) - (400 / 2),
            janela_pai.winfo_rooty() + (janela_pai.winfo_height() / 2) - (300 / 2)))
    
    # Variável para armazenar a seleção
    nivel_var = tk.StringVar(value="Séries Iniciais")
    ano_var = tk.IntVar(value=2025)
    
    # Frame principal
    frame = tk.Frame(janela, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Título
    tk.Label(frame, text="Selecione o nível para gerar a Ata Geral", 
              font=("Arial", 12, "bold")).pack(pady=(0, 20))
    
    # Opções de nível
    tk.Label(frame, text="Nível de Ensino:").pack(anchor="w")
    tk.Radiobutton(frame, text="Séries Iniciais (1º ao 5º ano)", 
                   variable=nivel_var, value="Séries Iniciais").pack(anchor="w")
    tk.Radiobutton(frame, text="Séries Finais (6º ao 9º ano)", 
                   variable=nivel_var, value="Séries Finais").pack(anchor="w")
    tk.Radiobutton(frame, text="Ensino Fundamental Completo (1º ao 9º ano)", 
                   variable=nivel_var, value="Ensino Fundamental Completo").pack(anchor="w")
    
    # Ano letivo
    tk.Label(frame, text="Ano Letivo:").pack(anchor="w", pady=(10, 0))
    tk.Spinbox(frame, from_=2020, to=2050, textvariable=ano_var, width=6).pack(anchor="w")
    
    # Função para gerar ata com feedback de progresso
    def gerar():
        nivel = nivel_var.get()
        ano = ano_var.get()
        janela.destroy()
        
        # Atualizar status na janela principal
        if status_label:
            status_label.config(text=f"Gerando Ata Geral para {nivel} do ano {ano}...")
        
        # Criar janela de progresso
        prog_janela = tk.Toplevel(janela_pai)
        prog_janela.title("Gerando Ata Geral")
        prog_janela.geometry("350x100")
        prog_janela.resizable(False, False)
        prog_janela.transient(janela_pai)
        prog_janela.grab_set()
        
        # Centralizar na tela
        if janela_pai:
            prog_janela.geometry("+%d+%d" % (
                janela_pai.winfo_rootx() + (janela_pai.winfo_width() / 2) - (350 / 2),
                janela_pai.winfo_rooty() + (janela_pai.winfo_height() / 2) - (100 / 2)))
        
        # Adicionar mensagem e barra de progresso
        tk.Label(prog_janela, text=f"Gerando Ata Geral para {nivel} do ano {ano}", 
                font=("Arial", 10, "bold")).pack(pady=(15, 5))
        
        progresso = ttk.Progressbar(prog_janela, mode="indeterminate")
        progresso.pack(padx=30, fill="x")
        progresso.start(10)
        
        # Função para executar a geração em um processo separado
        def executar_geracao():
            sucesso = gerar_ata_por_nivel(nivel, ano)
            prog_janela.destroy()
            
            # Atualizar status na janela principal
            if status_label:
                if sucesso:
                    status_label.config(text=f"Ata Geral para {nivel} gerada com sucesso!")
                else:
                    status_label.config(text=f"Erro ao gerar Ata Geral para {nivel}")
            
            if not sucesso:
                messagebox.showerror("Erro", f"Ocorreu um erro ao gerar a ata para {nivel}.")
            else:
                messagebox.showinfo("Sucesso", f"Ata Geral para {nivel} do ano {ano} gerada com sucesso!")
        
        # Executar após um breve delay para atualizar a interface
        # Protege caso `janela_pai` seja None (evita acesso a atributo de None)
        if janela_pai is not None:
            janela_pai.after(100, executar_geracao)
        else:
            # Usa a própria janela de progresso quando não há janela pai
            prog_janela.after(100, executar_geracao)
    
    # Botões
    frame_botoes = tk.Frame(frame)
    frame_botoes.pack(fill="x", pady=(20, 0))
    
    tk.Button(frame_botoes, text="Gerar", command=gerar, 
             bg="#77B341", fg="white", width=10).pack(side="right", padx=5)
    tk.Button(frame_botoes, text="Cancelar", command=janela.destroy, 
             width=10).pack(side="right", padx=5)

if __name__ == "__main__":
    # Teste direto do módulo
    abrir_interface_ata() 