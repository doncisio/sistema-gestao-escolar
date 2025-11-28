"""Verifica as permissoes cadastradas."""
import sys
sys.path.insert(0, '.')

from db.connection import get_cursor

with get_cursor() as cursor:
    print("\n=== PERMISSOES POR PERFIL ===")
    cursor.execute("""
        SELECT pp.perfil, p.codigo 
        FROM perfil_permissoes pp 
        JOIN permissoes p ON p.id = pp.permissao_id 
        ORDER BY pp.perfil, p.codigo
    """)
    rows = cursor.fetchall()
    
    if rows:
        for r in rows:
            print(f"  {r['perfil']:15} - {r['codigo']}")
    else:
        print("  NENHUMA PERMISSAO CADASTRADA!")
    
    print("\n=== PERMISSOES DISPONIVEIS ===")
    cursor.execute("SELECT id, codigo, descricao FROM permissoes ORDER BY codigo")
    perms = cursor.fetchall()
    
    if perms:
        for p in perms:
            print(f"  [{p['id']:3}] {p['codigo']:30} - {p['descricao']}")
    else:
        print("  NENHUMA PERMISSAO CADASTRADA NA TABELA permissoes!")
