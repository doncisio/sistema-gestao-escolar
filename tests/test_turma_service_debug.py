"""Debug do turma_service."""
import sys
sys.path.insert(0, 'c:\\gestao')

# Limpar cache
import importlib
mods_to_delete = [m for m in sys.modules if 'turma_service' in m]
for m in mods_to_delete:
    del sys.modules[m]

# Monkeypatch para debug
original_get_connection = None

def debug_get_connection():
    from db.connection import get_connection as orig
    global original_get_connection
    original_get_connection = orig
    print("DEBUG: get_connection() chamado")
    ctx = orig()
    print(f"DEBUG: contexto retornado: {type(ctx)}")
    return ctx

# Substituir temporariamente
import db.connection
db.connection.get_connection = debug_get_connection

from src.services.turma_service import listar_turmas

print("Chamando listar_turmas(aplicar_filtro_perfil=False)...")
try:
    resultado = listar_turmas(aplicar_filtro_perfil=False)
    print(f"Tipo: {type(resultado)}")
    print(f"Resultado: {resultado}")
except Exception as e:
    print(f"ERRO: {e}")
    import traceback
    traceback.print_exc()
