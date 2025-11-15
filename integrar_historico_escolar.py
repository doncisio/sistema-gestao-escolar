from interface_historico_escolar import InterfaceHistoricoEscolar
import tkinter as tk
from tkinter import ttk

def abrir_interface_historico(janela_pai=None):
    """
    Abre a interface de gerenciamento de histórico escolar.
    
    Parâmetros:
    janela_pai (Tk, opcional): Janela pai para abrir a interface como modal.
    """
    if janela_pai:
        # Criar uma janela de nível superior (Toplevel)
        janela = tk.Toplevel()
        janela.title("Gerenciamento de Histórico Escolar")
        janela.geometry("1200x700")
        
        # Esconder a janela pai em vez de usar grab_set
        janela_pai.withdraw()
        
        # Função para lidar com o fechamento da janela
        def on_close():
            janela_pai.deiconify()  # Mostrar janela principal novamente
            janela.destroy()
            
        # Associar a função ao evento de fechamento da janela
        janela.protocol("WM_DELETE_WINDOW", on_close)
        
        # Inicializar a interface dentro da janela Toplevel
        app = InterfaceHistoricoEscolar(janela)
        app.janela_pai = janela_pai  # Armazenar referência à janela pai
        
        # Centralizar a janela
        janela.update_idletasks()
        largura = janela.winfo_width()
        altura = janela.winfo_height()
        x = (janela.winfo_screenwidth() // 2) - (largura // 2)
        y = (janela.winfo_screenheight() // 2) - (altura // 2)
        janela.geometry(f"{largura}x{altura}+{x}+{y}")
        
        return app
    else:
        # Inicializar a interface como aplicação independente
        app = InterfaceHistoricoEscolar()
        app.janela.mainloop()
        return app

def abrir_historico_aluno(aluno_id, janela_pai=None):
    """
    Abre a interface de histórico escolar diretamente para um aluno específico.
    
    Parâmetros:
    aluno_id (int): ID do aluno para carregar o histórico.
    janela_pai (Tk, opcional): Janela pai para abrir a interface como modal.
    """
    # Criar a janela principal
    janela = tk.Toplevel() if janela_pai else tk.Tk()
    janela.title("Histórico Escolar do Aluno")
    janela.geometry("1200x700")
    
    # Se tiver janela pai, esconder ela
    if janela_pai:
        janela_pai.withdraw()
        
        # Função para lidar com o fechamento da janela
        def on_close():
            janela_pai.deiconify()  # Mostrar janela principal novamente
            janela.destroy()
            
        # Associar a função ao evento de fechamento da janela
        janela.protocol("WM_DELETE_WINDOW", on_close)
    
    # Inicializar a interface
    app = InterfaceHistoricoEscolar(janela)
    if janela_pai:
        app.janela_pai = janela_pai  # Armazenar referência à janela pai
    
    # Simular a seleção do aluno
    app.aluno_id = aluno_id
    
    # Conectar ao banco para obter o nome do aluno
    from conexao import conectar_bd
    conn = conectar_bd()
    if conn is None:
        print("✗ Falha ao conectar ao banco de dados")
        janela.destroy()
        return

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nome FROM alunos WHERE id = %s", (aluno_id,))
        resultado = cursor.fetchone()
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
    
    if resultado:
        nome_aluno = resultado[0]
        app.aluno_selecionado.set(f"{aluno_id} - {nome_aluno}")
        
        # Carregar o histórico do aluno
        app.carregar_historico()
        
        # Centralizar a janela
        janela.update_idletasks()
        largura = janela.winfo_width()
        altura = janela.winfo_height()
        x = (janela.winfo_screenwidth() // 2) - (largura // 2)
        y = (janela.winfo_screenheight() // 2) - (altura // 2)
        janela.geometry(f"{largura}x{altura}+{x}+{y}")
        
        janela.mainloop()
    else:
        janela.destroy()
        print(f"Aluno com ID {aluno_id} não encontrado.")

if __name__ == "__main__":
    # Teste da interface
    abrir_interface_historico() 