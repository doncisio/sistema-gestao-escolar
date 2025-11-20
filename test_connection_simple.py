"""
Teste simples de conexão
"""
import logging
logging.basicConfig(level=logging.DEBUG)

from conexao import inicializar_pool
from db.connection import get_connection, get_cursor

print("1. Inicializando pool...")
inicializar_pool()

print("2. Testando get_connection()...")
try:
    with get_connection() as conn:
        print(f"   Conexão obtida: {conn}")
        cursor = conn.cursor()
        print(f"   Cursor criado: {cursor}")
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        print(f"   Resultado: {result}")
        cursor.close()
    print("   ✓ get_connection() funcionou")
except Exception as e:
    print(f"   ✗ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Testando get_cursor()...")
try:
    with get_cursor() as cursor:
        print(f"   Cursor obtido: {cursor}")
        cursor.execute("SELECT 2 as test")
        result = cursor.fetchone()
        print(f"   Resultado: {result}")
    print("   ✓ get_cursor() funcionou")
except Exception as e:
    print(f"   ✗ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\nFIM DO TESTE")
