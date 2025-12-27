from pathlib import Path
from src.interfaces.horarios_escolares import InterfaceHorariosEscolares
import tkinter as tk
from tkinter import filedialog, messagebox
# Patch filedialog and messagebox
file_path = r'c:/gestao/historico geduc/horario por turma.html'
filedialog.askopenfilename = lambda **kwargs: file_path
messagebox.showinfo = lambda *args, **kwargs: print('INFO:', args)
messagebox.showwarning = lambda *args, **kwargs: print('WARN:', args)
messagebox.showerror = lambda *args, **kwargs: print('ERROR:', args)
# Create a hidden root
root = tk.Tk()
root.withdraw()
iface = InterfaceHorariosEscolares(root=root, janela_principal=root)
iface.importar_geduc()
# Inspect some cells
for r in range(1,7):
    row_vals = []
    for c in range(1,6):
        cel = iface.celulas_horario.get((r,c))
        row_vals.append(cel.get() if cel else None)
    print('row', r, row_vals)
root.destroy()
