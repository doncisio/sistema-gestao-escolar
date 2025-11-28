"""
Script de teste para a interface de gestao de usuarios.
Testa a criacao da janela e carregamento de dados.
"""

import sys
sys.path.insert(0, '.')

print("=" * 60)
print("  TESTE DA INTERFACE DE GESTAO DE USUARIOS")
print("=" * 60)

import tkinter as tk
from tkinter import ttk

# Importar módulo
try:
    from ui.gestao_usuarios import GestaoUsuariosWindow
    print("✓ Módulo gestao_usuarios importado com sucesso")
except ImportError as e:
    print(f"✗ Erro ao importar módulo: {e}")
    exit(1)

# Criar janela de teste
root = tk.Tk()
root.withdraw()

try:
    print("\n--- Criando janela de gestão de usuários ---")
    window = GestaoUsuariosWindow(root)
    print("✓ Janela criada")
    
    # Verificar se funcionários foram carregados
    func_count = len(window.funcionarios_dict) if hasattr(window, 'funcionarios_dict') else 0
    print(f"✓ Funcionários carregados: {func_count}")
    
    # Verificar se usuários foram carregados
    user_count = len(window.usuarios_cache) if hasattr(window, 'usuarios_cache') else 0
    print(f"✓ Usuários carregados: {user_count}")
    
    # Listar usuários encontrados
    if user_count > 0:
        print("\n--- Usuários cadastrados ---")
        for u in window.usuarios_cache[:5]:  # Mostrar até 5
            print(f"  - {u['username']} ({u['perfil']}) - {u['nome']}")
    
    print("\n✓ TESTE CONCLUÍDO COM SUCESSO!")
    
except Exception as e:
    print(f"\n✗ Erro no teste: {e}")
    import traceback
    traceback.print_exc()

finally:
    root.destroy()
