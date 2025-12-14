"""
FASE 6 - TESTES E AJUSTES DO SISTEMA DE PERFIS

Este script executa testes automatizados de todos os cenarios
previstos na Fase 6 do plano de implementacao.
"""

import sys
sys.path.insert(0, '.')

from typing import Tuple, Optional


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_test(name: str, passed: bool, details: str = ""):
    status = "PASSOU" if passed else "FALHOU"
    icon = "✓" if passed else "✗"
    print(f"  {icon} {name}: {status}")
    if details:
        print(f"      {details}")


def print_section(title: str):
    print(f"\n--- {title} ---")


# =============================================================================
# ETAPA 6.1: VERIFICAR USUARIOS DE TESTE
# =============================================================================
def verificar_usuarios_teste() -> dict:
    """Verifica se os usuarios de teste existem."""
    print_header("ETAPA 6.1: VERIFICAR USUARIOS DE TESTE")
    
    from db.connection import get_cursor
    
    usuarios = {}
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT u.id, u.username, u.perfil, u.ativo, f.nome
            FROM usuarios u
            LEFT JOIN funcionarios f ON u.funcionario_id = f.id
        """)
        for row in cursor.fetchall():
            usuarios[row['username']] = row
    
    # Verificar usuarios esperados
    esperados = {
        'admin': 'administrador',
        'coord_teste': 'coordenador', 
        'prof_teste': 'professor'
    }
    
    for username, perfil_esperado in esperados.items():
        if username in usuarios:
            user = usuarios[username]
            correto = user['perfil'] == perfil_esperado and user['ativo']
            print_test(
                f"Usuario '{username}' ({perfil_esperado})",
                correto,
                f"Nome: {user['nome']}, Ativo: {user['ativo']}"
            )
        else:
            print_test(f"Usuario '{username}'", False, "NAO ENCONTRADO")
    
    return usuarios


# =============================================================================
# ETAPA 6.2.1: TESTAR LOGIN VALIDO/INVALIDO
# =============================================================================
def testar_login():
    """Testa login com credenciais validas e invalidas."""
    print_header("ETAPA 6.2.1: TESTAR LOGIN")
    
    from auth.auth_service import AuthService
    
    # Teste 1: Login valido (admin)
    print_section("Login com credenciais validas")
    usuario, msg = AuthService.login("admin", "Admin@123")
    print_test("Login admin", usuario is not None, msg)
    
    # Teste 2: Login com senha errada
    print_section("Login com senha incorreta")
    usuario, msg = AuthService.login("admin", "senha_errada")
    print_test("Rejeitar senha incorreta", usuario is None, msg)
    
    # Teste 3: Login com usuario inexistente
    print_section("Login com usuario inexistente")
    usuario, msg = AuthService.login("usuario_fake", "qualquer")
    print_test("Rejeitar usuario inexistente", usuario is None, msg)
    
    # Teste 4: Login coordenador
    print_section("Login coordenador")
    usuario, msg = AuthService.login("coord_teste", "Coord@123")
    print_test("Login coord_teste", usuario is not None, msg)
    
    # Teste 5: Login professor
    print_section("Login professor")
    usuario, msg = AuthService.login("prof_teste", "Prof@123")
    print_test("Login prof_teste", usuario is not None, msg)


# =============================================================================
# ETAPA 6.2.2: TESTAR PERMISSOES POR PERFIL
# =============================================================================
def testar_permissoes():
    """Testa se cada perfil tem as permissoes corretas."""
    print_header("ETAPA 6.2.2: TESTAR PERMISSOES POR PERFIL")
    
    from auth.auth_service import AuthService
    from auth.usuario_logado import UsuarioLogado
    from auth.decorators import ControleAcesso
    
    perfis_testes = [
        ('admin', 'Admin@123', 'administrador'),
        ('coord_teste', 'Coord@123', 'coordenador'),
        ('prof_teste', 'Prof@123', 'professor')
    ]
    
    # Permissoes a testar por perfil
    permissoes_esperadas = {
        'administrador': {
            'alunos.criar': True,
            'alunos.editar': True,
            'alunos.excluir': True,
            'funcionarios.criar': True,
            'sistema.backup': True,
            'sistema.usuarios': True,
        },
        'coordenador': {
            'alunos.criar': False,
            'alunos.editar': False,
            'relatorios.visualizar': True,
            'notas.visualizar': True,
            'sistema.backup': False,
        },
        'professor': {
            'alunos.criar': False,
            'alunos.editar': False,
            'notas.lancar_proprias': True,  # Pode lançar nas próprias turmas
            'notas.visualizar_proprias': True,  # Pode visualizar suas turmas
            'notas.lancar': False,  # NAO pode lançar em qualquer turma
            'notas.visualizar': False,  # NAO pode ver notas de todas turmas
            'sistema.backup': False,
            'sistema.usuarios': False,
        }
    }
    
    for username, senha, perfil in perfis_testes:
        print_section(f"Perfil: {perfil.upper()}")
        
        # Fazer login
        usuario, msg = AuthService.login(username, senha)
        if not usuario:
            print_test(f"Login {username}", False, msg)
            continue
        
        # Definir usuario logado
        UsuarioLogado.set_usuario(usuario)
        
        # Verificar permissoes
        acesso = ControleAcesso()
        
        for permissao, esperado in permissoes_esperadas.get(perfil, {}).items():
            tem = acesso.pode(permissao)
            correto = tem == esperado
            print_test(
                f"{permissao}",
                correto,
                f"Esperado: {esperado}, Obtido: {tem}"
            )
        
        # Limpar
        UsuarioLogado.limpar()


# =============================================================================
# ETAPA 6.2.3: TESTAR FILTRO DE TURMAS (PROFESSOR)
# =============================================================================
def testar_filtro_turmas_professor():
    """Testa se professor ve apenas suas turmas."""
    print_header("ETAPA 6.2.3: TESTAR FILTRO TURMAS (PROFESSOR)")
    
    from auth.auth_service import AuthService
    from auth.usuario_logado import UsuarioLogado
    from src.services.turma_service import listar_turmas
    from src.services.perfil_filter_service import PerfilFilterService
    
    # Login como admin primeiro
    print_section("Admin ve todas as turmas")
    usuario, _ = AuthService.login("admin", "Admin@123")
    UsuarioLogado.set_usuario(usuario)
    
    turmas_admin = listar_turmas(aplicar_filtro_perfil=True)
    total_turmas = len(turmas_admin) if turmas_admin else 0
    print_test("Admin lista turmas", turmas_admin is not None, f"Total: {total_turmas}")
    
    # Login como professor
    print_section("Professor ve apenas suas turmas")
    usuario, _ = AuthService.login("prof_teste", "Prof@123")
    UsuarioLogado.set_usuario(usuario)
    
    turmas_prof = listar_turmas(aplicar_filtro_perfil=True)
    turmas_prof_count = len(turmas_prof) if turmas_prof else 0
    
    # Professor deve ver MENOS turmas que admin
    filtro_funciona = turmas_prof_count < total_turmas
    print_test(
        "Filtro de turmas aplicado",
        filtro_funciona,
        f"Professor ve {turmas_prof_count} de {total_turmas} turmas"
    )
    
    # Verificar IDs permitidos
    turmas_ids = PerfilFilterService.get_turmas_usuario()
    print_test(
        "Turmas permitidas identificadas",
        turmas_ids is not None and len(turmas_ids) > 0,
        f"IDs: {turmas_ids}"
    )
    
    UsuarioLogado.limpar()


# =============================================================================
# ETAPA 6.2.4: TESTAR COORDENADOR (VISUALIZA MAS NAO EDITA)
# =============================================================================
def testar_coordenador_somente_leitura():
    """Testa se coordenador pode visualizar mas nao editar."""
    print_header("ETAPA 6.2.4: TESTAR COORDENADOR (SOMENTE LEITURA)")
    
    from auth.auth_service import AuthService
    from auth.usuario_logado import UsuarioLogado
    from auth.decorators import ControleAcesso
    from src.services.turma_service import listar_turmas
    
    # Login como coordenador
    usuario, _ = AuthService.login("coord_teste", "Coord@123")
    UsuarioLogado.set_usuario(usuario)
    
    acesso = ControleAcesso()
    
    print_section("Permissoes de visualizacao")
    # Pode visualizar
    print_test("relatorios.visualizar", acesso.pode('relatorios.visualizar'))
    print_test("notas.visualizar", acesso.pode('notas.visualizar'))
    print_test("alunos.visualizar", acesso.pode('alunos.visualizar'))
    
    print_section("Permissoes de edicao (devem ser NEGADAS)")
    # Nao pode editar
    print_test("alunos.criar NEGADO", not acesso.pode('alunos.criar'))
    print_test("alunos.editar NEGADO", not acesso.pode('alunos.editar'))
    print_test("alunos.excluir NEGADO", not acesso.pode('alunos.excluir'))
    print_test("funcionarios.criar NEGADO", not acesso.pode('funcionarios.criar'))
    
    print_section("Visualizacao de turmas")
    # Deve ver TODAS as turmas (nao tem filtro)
    turmas = listar_turmas(aplicar_filtro_perfil=True)
    total = len(turmas) if turmas else 0
    print_test("Ve todas as turmas", total > 0, f"Total: {total}")
    
    UsuarioLogado.limpar()


# =============================================================================
# ETAPA 6.2.5: TESTAR ADMIN (ACESSO TOTAL)
# =============================================================================
def testar_admin_acesso_total():
    """Testa se admin tem acesso total."""
    print_header("ETAPA 6.2.5: TESTAR ADMIN (ACESSO TOTAL)")
    
    from auth.auth_service import AuthService
    from auth.usuario_logado import UsuarioLogado
    from auth.decorators import ControleAcesso
    
    # Login como admin
    usuario, _ = AuthService.login("admin", "Admin@123")
    UsuarioLogado.set_usuario(usuario)
    
    acesso = ControleAcesso()
    
    # Testar todas as permissoes criticas
    permissoes_criticas = [
        'alunos.criar', 'alunos.editar', 'alunos.excluir',
        'funcionarios.criar', 'funcionarios.editar',
        'notas.lancar', 'notas.visualizar',
        'relatorios.visualizar',
        'sistema.backup', 'sistema.usuarios',
        'matriculas.criar', 'matriculas.transferir'
    ]
    
    todas_ok = True
    for perm in permissoes_criticas:
        tem = acesso.pode(perm)
        print_test(perm, tem)
        if not tem:
            todas_ok = False
    
    print_section("Resultado")
    print_test("ADMIN TEM ACESSO TOTAL", todas_ok)
    
    UsuarioLogado.limpar()


# =============================================================================
# ETAPA 6.2.6: TESTAR LOGOUT E TROCA DE USUARIO
# =============================================================================
def testar_logout_troca():
    """Testa logout e troca de usuario."""
    print_header("ETAPA 6.2.6: TESTAR LOGOUT E TROCA DE USUARIO")
    
    from auth.auth_service import AuthService
    from auth.usuario_logado import UsuarioLogado
    
    # Login inicial
    print_section("Login inicial como admin")
    usuario1, _ = AuthService.login("admin", "Admin@123")
    UsuarioLogado.set_usuario(usuario1)
    
    perfil1 = UsuarioLogado.get_perfil()
    print_test("Login admin OK", perfil1 == 'administrador', f"Perfil: {perfil1}")
    
    # Logout
    print_section("Logout")
    UsuarioLogado.limpar()
    perfil_apos_logout = UsuarioLogado.get_perfil()
    print_test("Usuario limpo apos logout", perfil_apos_logout is None)
    
    # Troca para outro usuario
    print_section("Troca para professor")
    usuario2, _ = AuthService.login("prof_teste", "Prof@123")
    UsuarioLogado.set_usuario(usuario2)
    
    perfil2 = UsuarioLogado.get_perfil()
    print_test("Troca de usuario OK", perfil2 == 'professor', f"Perfil: {perfil2}")
    
    UsuarioLogado.limpar()


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("\n" + "=" * 70)
    print("  FASE 6 - TESTES E AJUSTES DO SISTEMA DE PERFIS")
    print("  Sistema de Gestao Escolar")
    print("=" * 70)
    
    resultados = {
        'passou': 0,
        'falhou': 0
    }
    
    try:
        # Verificar usuarios
        verificar_usuarios_teste()
        
        # Testar login
        testar_login()
        
        # Testar permissoes
        testar_permissoes()
        
        # Testar filtro professor
        testar_filtro_turmas_professor()
        
        # Testar coordenador
        testar_coordenador_somente_leitura()
        
        # Testar admin
        testar_admin_acesso_total()
        
        # Testar logout/troca
        testar_logout_troca()
        
        print_header("RESUMO FINAL")
        print("\n  Todos os testes da Fase 6 foram executados!")
        print("  Verifique os resultados acima para detalhes.")
        
    except Exception as e:
        print(f"\n\n!!! ERRO DURANTE TESTES: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
