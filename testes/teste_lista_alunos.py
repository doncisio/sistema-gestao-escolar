"""
Script para testar a visualização da lista de alunos
"""
import tkinter as tk
from tkinter import messagebox
from views.aluno_view import ListaAlunosView
from utils.config import Config

def testar_lista_alunos():
    """Testa a visualização da lista de alunos"""
    # Configurar janela
    root = tk.Tk()
    root.title("Teste - Lista de Alunos")
    root.geometry("1000x600")
    
    # Criar frame para conteúdo
    content_frame = tk.Frame(root, bg=Config.COR_FUNDO)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Tentar criar a lista de alunos
    try:
        print("Iniciando teste da ListaAlunosView...")
        lista_alunos = ListaAlunosView(content_frame)
        print("ListaAlunosView criada com sucesso!")
    except Exception as e:
        print(f"Erro ao criar ListaAlunosView: {str(e)}")
        messagebox.showerror("Erro", f"Erro ao criar ListaAlunosView: {str(e)}")
    
    # Botão para fechar
    btn_fechar = tk.Button(root, text="Fechar", command=root.destroy)
    btn_fechar.pack(pady=10)
    
    # Iniciar loop principal
    root.mainloop()

if __name__ == "__main__":
    testar_lista_alunos() 