"""
Script simples para criar usuário admin de teste.
Uso: python scripts/criar_admin_teste.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from conexao import conectar_bd
from auth.password_utils import gerar_hash_senha


def main():
    print("Criando usuário admin de teste...")
    
    conn = conectar_bd()
    if not conn:
        print("Erro: não foi possível conectar ao banco")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    # Verificar se já existe
    cursor.execute("SELECT id FROM usuarios WHERE username = 'admin'")
    if cursor.fetchone():
        print("Usuário 'admin' já existe!")
        cursor.close()
        conn.close()
        return
    
    # Criar hash da senha
    senha_hash = gerar_hash_senha('Admin@123')
    
    # Inserir usuário (funcionário ID 1)
    cursor.execute('''
        INSERT INTO usuarios (funcionario_id, username, senha_hash, perfil, primeiro_acesso)
        VALUES (%s, %s, %s, %s, FALSE)
    ''', (1, 'admin', senha_hash, 'administrador'))
    
    conn.commit()
    
    print()
    print("=" * 50)
    print("✅ Usuário admin criado com sucesso!")
    print("=" * 50)
    print()
    print("   Username: admin")
    print("   Senha:    Admin@123")
    print("   Perfil:   Administrador")
    print()
    
    cursor.close()
    conn.close()


if __name__ == '__main__':
    main()
