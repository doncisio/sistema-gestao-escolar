"""
Script para criar o primeiro usuário administrador.

Uso:
    python scripts/criar_usuario_admin.py
"""

import sys
import getpass
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from conexao import conectar_bd
from config_logs import get_logger
from auth.password_utils import gerar_hash_senha, validar_forca_senha

logger = get_logger(__name__)


def listar_funcionarios_disponiveis(cursor) -> list:
    """Lista funcionários que ainda não têm usuário."""
    cursor.execute("""
        SELECT f.id, f.nome, f.cargo
        FROM funcionarios f
        LEFT JOIN usuarios u ON u.funcionario_id = f.id
        WHERE u.id IS NULL
        ORDER BY f.nome
    """)
    return cursor.fetchall()


def verificar_usuario_existe(cursor, username: str) -> bool:
    """Verifica se username já existe."""
    cursor.execute(
        "SELECT id FROM usuarios WHERE username = %s",
        (username.lower(),)
    )
    return cursor.fetchone() is not None


def criar_usuario(cursor, funcionario_id: int, username: str, 
                  senha_hash: str, perfil: str) -> int:
    """Cria usuário no banco."""
    cursor.execute("""
        INSERT INTO usuarios (funcionario_id, username, senha_hash, perfil, primeiro_acesso)
        VALUES (%s, %s, %s, %s, FALSE)
    """, (funcionario_id, username.lower(), senha_hash, perfil))
    return cursor.lastrowid


def main():
    print("\n" + "=" * 60)
    print("👤 Criador de Usuário Administrador")
    print("=" * 60)
    
    # Conectar ao banco
    print("\n🔌 Conectando ao banco de dados...")
    conn = conectar_bd()
    
    if not conn:
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        sys.exit(1)
    
    print("✅ Conexão estabelecida")
    
    cursor = conn.cursor(dictionary=True)
    
    # Verificar se tabela usuarios existe
    try:
        cursor.execute("SELECT COUNT(*) as total FROM usuarios")
        result = cursor.fetchone()
        total_usuarios = result['total']
        print(f"\n📊 Usuários existentes: {total_usuarios}")
        
        if total_usuarios > 0:
            print("\n⚠️  Já existem usuários cadastrados.")
            resp = input("Deseja criar mais um administrador? (s/N): ").strip().lower()
            if resp != 's':
                print("Operação cancelada.")
                cursor.close()
                conn.close()
                return
    except Exception as e:
        print(f"❌ Erro: Tabela 'usuarios' não encontrada.")
        print("   Execute primeiro: python scripts/executar_migrations_auth.py")
        cursor.close()
        conn.close()
        sys.exit(1)
    
    # Listar funcionários disponíveis
    print("\n📋 Funcionários disponíveis (sem usuário vinculado):")
    print("-" * 60)
    
    funcionarios = listar_funcionarios_disponiveis(cursor)
    
    if not funcionarios:
        print("❌ Nenhum funcionário disponível.")
        print("   Todos os funcionários já possuem usuário vinculado.")
        cursor.close()
        conn.close()
        return
    
    for i, func in enumerate(funcionarios, 1):
        cargo = func['cargo'] or 'Sem cargo'
        print(f"  {i:3}. {func['nome'][:40]:<40} ({cargo})")
    
    print("-" * 60)
    print(f"Total: {len(funcionarios)} funcionários disponíveis")
    
    # Selecionar funcionário
    while True:
        try:
            escolha = input("\nDigite o número do funcionário (ou 0 para cancelar): ").strip()
            if escolha == '0':
                print("Operação cancelada.")
                cursor.close()
                conn.close()
                return
            
            indice = int(escolha) - 1
            if 0 <= indice < len(funcionarios):
                funcionario = funcionarios[indice]
                break
            else:
                print("❌ Número inválido. Tente novamente.")
        except ValueError:
            print("❌ Digite apenas o número.")
    
    print(f"\n✅ Funcionário selecionado: {funcionario['nome']}")
    
    # Definir username
    # Sugerir username baseado no nome
    nome_partes = funcionario['nome'].lower().split()
    username_sugerido = nome_partes[0] if nome_partes else 'admin'
    
    while True:
        username = input(f"\nDigite o nome de usuário [{username_sugerido}]: ").strip()
        if not username:
            username = username_sugerido
        
        username = username.lower()
        
        if len(username) < 3:
            print("❌ Username deve ter pelo menos 3 caracteres.")
            continue
        
        if verificar_usuario_existe(cursor, username):
            print(f"❌ Username '{username}' já está em uso.")
            continue
        
        break
    
    # Definir senha
    print("\n🔐 Definir senha:")
    print("   Requisitos: mínimo 8 caracteres, incluir maiúsculas, minúsculas e números")
    
    while True:
        senha = getpass.getpass("   Senha: ")
        
        valida, msg = validar_forca_senha(senha)
        if not valida:
            print(f"   ❌ {msg}")
            continue
        
        senha_confirm = getpass.getpass("   Confirme a senha: ")
        
        if senha != senha_confirm:
            print("   ❌ As senhas não conferem.")
            continue
        
        break
    
    # Confirmar dados
    print("\n" + "-" * 60)
    print("📋 RESUMO:")
    print(f"   Funcionário: {funcionario['nome']}")
    print(f"   Username:    {username}")
    print(f"   Perfil:      Administrador")
    print("-" * 60)
    
    confirmar = input("\nConfirma criação do usuário? (s/N): ").strip().lower()
    
    if confirmar != 's':
        print("Operação cancelada.")
        cursor.close()
        conn.close()
        return
    
    # Criar usuário
    try:
        senha_hash = gerar_hash_senha(senha)
        user_id = criar_usuario(
            cursor, 
            funcionario['id'], 
            username, 
            senha_hash, 
            'administrador'
        )
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("🎉 USUÁRIO CRIADO COM SUCESSO!")
        print("=" * 60)
        print(f"\n   ID:          {user_id}")
        print(f"   Username:    {username}")
        print(f"   Perfil:      Administrador")
        print(f"   Funcionário: {funcionario['nome']}")
        print("\n💡 Para ativar o sistema de perfis:")
        print("   python testar_perfis.py on")
        print()
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro ao criar usuário: {e}")
        logger.exception("Erro ao criar usuário admin")
    
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
