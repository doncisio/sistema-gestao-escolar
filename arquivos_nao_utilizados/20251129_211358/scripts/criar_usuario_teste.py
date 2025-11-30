#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para criar usuários de teste com diferentes perfis.

Uso:
    python scripts/criar_usuario_teste.py <perfil> <senha>
    
    perfil: administrador, coordenador ou professor
    senha: senha do usuário (mínimo 8 caracteres)
    
Exemplos:
    python scripts/criar_usuario_teste.py coordenador Coord@123
    python scripts/criar_usuario_teste.py professor Prof@123
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.auth_service import AuthService
from auth.models import Perfil


def criar_usuario_teste(perfil: str, senha: str):
    """
    Cria um usuário de teste com o perfil especificado.
    
    Args:
        perfil: 'administrador', 'coordenador' ou 'professor'
        senha: Senha do usuário
    """
    # Validar perfil
    perfil_lower = perfil.lower()
    if perfil_lower not in ['administrador', 'coordenador', 'professor']:
        print(f"❌ Perfil inválido: {perfil}")
        print("   Perfis válidos: administrador, coordenador, professor")
        return False
    
    # Gerar username baseado no perfil
    prefixos = {
        'administrador': 'admin_teste',
        'coordenador': 'coord_teste',
        'professor': 'prof_teste'
    }
    username = prefixos[perfil_lower]
    
    # Tentar criar usuário
    print(f"\n📝 Criando usuário de teste...")
    print(f"   Username: {username}")
    print(f"   Perfil: {perfil_lower}")
    print(f"   Senha: {senha}")
    
    try:
        # Verificar se já existe
        from db.connection import get_cursor
        with get_cursor() as cursor:
            cursor.execute("SELECT id FROM usuarios WHERE username = %s", (username,))
            existing = cursor.fetchone()
            if existing:
                # obter id do usuário existente
                user_id = existing['id'] if isinstance(existing, dict) else existing[0]
                print(f"\n⚠️  Usuário '{username}' já existe! (ID: {user_id})")

                # Perguntar se deseja resetar
                resposta = input("   Deseja resetar a senha? (s/n): ")
                if resposta.lower() == 's':
                    # executar reset de senha -- admin_id=0 (script)
                    sucesso, msg, _ = AuthService.resetar_senha(int(user_id), 0)
                    if sucesso:
                        print(f"✅ Senha resetada com sucesso!")
                        return True
                    else:
                        print(f"❌ Falha ao resetar senha: {msg}")
                        return False
                return False
        
        # Buscar um funcionário para vincular (apenas para testes)
        funcionario_id = None
        with get_cursor() as cursor:
            # Buscar funcionário com cargo relacionado ao perfil
            if perfil_lower == 'coordenador':
                cursor.execute("""
                    SELECT id, nome FROM funcionarios 
                    WHERE cargo LIKE '%Coordenador%' OR cargo LIKE '%Especialista%'
                    LIMIT 1
                """)
            elif perfil_lower == 'professor':
                cursor.execute("""
                    SELECT id, nome FROM funcionarios 
                    WHERE cargo LIKE '%Professor%'
                    LIMIT 1
                """)
            else:
                cursor.execute("SELECT id, nome FROM funcionarios LIMIT 1")
            
            func = cursor.fetchone()
            if func:
                funcionario_id = func['id'] if isinstance(func, dict) else func[0]
                nome_func = func['nome'] if isinstance(func, dict) else func[1]
                print(f"   Vinculando a: {nome_func} (ID: {funcionario_id})")
        
        if not funcionario_id:
            print(f"\n❌ Nenhum funcionário encontrado para vincular")
            print("   Crie um funcionário primeiro ou use um ID existente")
            return False
        
        # Criar novo usuário
        sucesso, mensagem, senha_gerada = AuthService.criar_usuario(
            funcionario_id=funcionario_id,
            username=username,
            perfil=perfil_lower,
            senha=senha
        )
        
        if sucesso:
            print(f"\n✅ {mensagem}")
            
            print(f"\n💡 Para testar:")
            print(f"   1. python testar_perfis.py on")
            print(f"   2. python main.py")
            print(f"   3. Login: {username} / {senha}")
            
            return True
        else:
            print(f"\n❌ {mensagem}")
            return False
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def listar_usuarios():
    """Lista todos os usuários do sistema."""
    print("\n📋 Usuários cadastrados:")
    print("-" * 50)
    
    try:
        usuarios = AuthService.listar_usuarios()
        
        for u in usuarios:
            status = "🟢" if u.get('ativo', True) else "🔴"
            print(f"   {status} {u['username']} ({u['perfil']}) - ID: {u['id']}")
        
        print("-" * 50)
        print(f"   Total: {len(usuarios)} usuários")
        
    except Exception as e:
        print(f"❌ Erro ao listar usuários: {e}")


def main():
    """Função principal."""
    print("=" * 60)
    print(" CRIAR USUÁRIO DE TESTE - Sistema de Perfis")
    print("=" * 60)
    
    if len(sys.argv) == 1:
        # Sem argumentos: mostrar ajuda e listar usuários
        print("\nUso: python scripts/criar_usuario_teste.py <perfil> <senha>")
        print("\nPerfis disponíveis:")
        print("  - administrador: Acesso total ao sistema")
        print("  - coordenador: Acesso pedagógico (visualização)")
        print("  - professor: Acesso às próprias turmas")
        print("\nExemplos:")
        print("  python scripts/criar_usuario_teste.py coordenador Coord@123")
        print("  python scripts/criar_usuario_teste.py professor Prof@123")
        
        listar_usuarios()
        return
    
    if len(sys.argv) < 3:
        print("❌ Argumentos insuficientes!")
        print("   Uso: python scripts/criar_usuario_teste.py <perfil> <senha>")
        return
    
    perfil = sys.argv[1]
    senha = sys.argv[2]
    
    criar_usuario_teste(perfil, senha)


if __name__ == "__main__":
    main()
