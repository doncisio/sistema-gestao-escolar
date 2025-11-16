import traceback
import tkinter as tk

results = []

print('Iniciando smoke test GUI...')

# Test InterfaceCadastroAluno
try:
    from InterfaceCadastroAluno import InterfaceCadastroAluno
    try:
        root = tk.Tk()
        root.withdraw()
        app = InterfaceCadastroAluno(root)
        print('OK: InterfaceCadastroAluno instanciada')
        try:
            app.master.destroy()
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass
    except Exception as e:
        print('ERROR: InterfaceCadastroAluno ->', e)
        traceback.print_exc()
except Exception as e:
    print('IMPORT ERROR: InterfaceCadastroAluno ->', e)
    traceback.print_exc()

# Test InterfaceCadastroEdicaoFaltas
try:
    from InterfaceCadastroEdicaoFaltas import InterfaceCadastroEdicaoFaltas
    try:
        # chamar sem root para usar o fluxo padrão (pode tentar carregar dados)
        app2 = InterfaceCadastroEdicaoFaltas()
        print('OK: InterfaceCadastroEdicaoFaltas instanciada')
        try:
            if hasattr(app2, 'janela') and app2.janela:
                app2.janela.destroy()
        except Exception:
            pass
    except Exception as e:
        print('ERROR: InterfaceCadastroEdicaoFaltas ->', e)
        traceback.print_exc()
except Exception as e:
    print('IMPORT ERROR: InterfaceCadastroEdicaoFaltas ->', e)
    traceback.print_exc()

print('Smoke test finalizado.')
