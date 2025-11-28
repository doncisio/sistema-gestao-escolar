"""Teste minimalista."""

import sys
sys.path.insert(0, r'c:\gestao')

from db.connection import get_connection

print("1. Teste direto com get_connection:")
with get_connection() as conn:
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT t.id, t.nome FROM turmas t LIMIT 3")
    result = cursor.fetchall()
    print(f"   Resultado direto: {result}")

print("\n2. Teste função listar_turmas:")
from services.turma_service import listar_turmas as lt
result2 = lt(aplicar_filtro_perfil=False)
print(f"   Resultado função: {result2}")

print("\n3. Reimportando e testando:")
import importlib
import services.turma_service as ts
importlib.reload(ts)
result3 = ts.listar_turmas(aplicar_filtro_perfil=False)
print(f"   Resultado após reload: {result3}")
