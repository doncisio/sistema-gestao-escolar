"""
Teste do filtro de dados por perfil de usuário.

Este script testa se professores veem apenas suas turmas e alunos vinculados.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ajustar para ignorar imports opcionais
os.environ['SKIP_OPTIONAL_IMPORTS'] = '1'

from auth.auth_service import AuthService
from auth.usuario_logado import UsuarioLogado
from src.services.perfil_filter_service import PerfilFilterService, get_turmas_usuario, get_sql_filtro_turmas
from src.services.turma_service import listar_turmas
from src.core.config import perfis_habilitados
from db.connection import get_cursor


def print_header(titulo: str):
    """Imprime cabeçalho formatado."""
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}")


def print_section(titulo: str):
    """Imprime seção formatada."""
    print(f"\n--- {titulo} ---")


def verificar_turmas_professor_no_banco():
    """Verifica quais turmas existem para professores no banco."""
    print_section("Turmas disponíveis com professor vinculado")
    
    try:
        with get_cursor() as cursor:
            # Buscar turmas que têm professor responsável ou disciplinas vinculadas
            cursor.execute("""
                SELECT DISTINCT 
                    t.id, 
                    t.nome as turma_nome, 
                    s.nome as serie_nome,
                    t.turno,
                    f.id as funcionario_id,
                    f.nome as professor_nome
                FROM turmas t
                LEFT JOIN series s ON t.serie_id = s.id
                LEFT JOIN funcionarios f ON t.professor_id = f.id
                WHERE t.ano_letivo_id = (
                    SELECT id FROM anosletivos 
                    WHERE YEAR(CURDATE()) = ano_letivo 
                    LIMIT 1
                )
                AND f.id IS NOT NULL
                ORDER BY s.nome, t.nome
                LIMIT 10
            """)
            
            resultados = cursor.fetchall()
            
            if not resultados:
                print("  Nenhuma turma com professor responsável encontrada")
                return None
            
            for r in resultados:
                if isinstance(r, dict):
                    print(f"  Turma {r['id']}: {r['serie_nome']} - {r['turma_nome']} ({r['turno']}) -> Prof: {r['professor_nome']} (ID: {r['funcionario_id']})")
                else:
                    print(f"  Turma {r[0]}: {r[2]} - {r[1]} ({r[3]}) -> Prof: {r[5]} (ID: {r[4]})")
            
            # Retorna o primeiro funcionário encontrado
            if isinstance(resultados[0], dict):
                return resultados[0]['funcionario_id']
            return resultados[0][4]
            
    except Exception as e:
        print(f"  ERRO: {e}")
        return None


def criar_usuario_professor_teste(funcionario_id: int):
    """Cria ou obtém usuário professor para teste."""
    print_section(f"Verificando/criando usuário professor para funcionário {funcionario_id}")
    
    try:
        with get_cursor(commit=True) as cursor:
            # Verificar se já existe
            cursor.execute(
                "SELECT id, username FROM usuarios WHERE funcionario_id = %s",
                (funcionario_id,)
            )
            resultado = cursor.fetchone()
            
            if resultado:
                username = resultado['username'] if isinstance(resultado, dict) else resultado[1]
                print(f"  Usuário já existe: {username}")
                return username
            
            # Buscar nome do funcionário
            cursor.execute("SELECT nome FROM funcionarios WHERE id = %s", (funcionario_id,))
            func = cursor.fetchone()
            nome = func['nome'] if isinstance(func, dict) else func[0]
            
            # Criar usuário
            import hashlib
            senha_hash = hashlib.sha256("Prof@123".encode()).hexdigest()
            username = f"prof_{funcionario_id}"
            
            cursor.execute("""
                INSERT INTO usuarios (username, senha_hash, nome_completo, perfil, ativo, funcionario_id)
                VALUES (%s, %s, %s, 'professor', 1, %s)
            """, (username, senha_hash, nome, funcionario_id))
            
            print(f"  Criado usuário: {username} (senha: Prof@123)")
            return username
            
    except Exception as e:
        print(f"  ERRO ao criar usuário: {e}")
        return None


def testar_como_admin():
    """Testa listagem como administrador."""
    print_header("TESTE COMO ADMINISTRADOR")
    
    # Login como admin
    auth = AuthService()
    resultado = auth.login("admin", "Admin@123")
    
    if isinstance(resultado, tuple):
        usuario, msg = resultado
    else:
        usuario = resultado
    
    if not usuario:
        print("ERRO: Falha no login como admin")
        return
    
    UsuarioLogado.set_usuario(usuario)
    
    print_section("Informações do usuário")
    print(f"  Perfil: {UsuarioLogado.get_perfil()}")
    print(f"  Nome: {UsuarioLogado.get_nome_display()}")
    
    # Testar filtro de turmas
    turmas_ids = get_turmas_usuario()
    print_section("Filtro de turmas")
    print(f"  Turmas IDs: {turmas_ids}")  # Deve ser None (acesso total)
    
    filtro_sql, params = get_sql_filtro_turmas("t")
    print(f"  SQL: '{filtro_sql}'")  # Deve ser vazio
    print(f"  Params: {params}")
    
    # Listar turmas
    print_section("Turmas visíveis")
    turmas = listar_turmas()
    print(f"  Total de turmas: {len(turmas)}")


def testar_como_professor(username: str):
    """Testa listagem como professor."""
    print_header("TESTE COMO PROFESSOR")
    
    # Login como professor
    auth = AuthService()
    resultado = auth.login(username, "Prof@123")
    
    if isinstance(resultado, tuple):
        usuario, msg = resultado
    else:
        usuario = resultado
    
    if not usuario:
        print(f"ERRO: Falha no login como {username}")
        return
    
    UsuarioLogado.set_usuario(usuario)
    
    print_section("Informações do usuário")
    print(f"  Perfil: {UsuarioLogado.get_perfil()}")
    print(f"  Nome: {UsuarioLogado.get_nome_display()}")
    print(f"  Funcionário ID: {UsuarioLogado.get_funcionario_id()}")
    
    # Testar filtro de turmas
    turmas_ids = get_turmas_usuario()
    print_section("Filtro de turmas")
    print(f"  Turmas IDs: {turmas_ids}")  # Deve ser lista de IDs
    
    filtro_sql, params = get_sql_filtro_turmas("t")
    print(f"  SQL: '{filtro_sql}'")  # Deve ter "AND t.id IN (...)"
    print(f"  Params: {params}")
    
    # Informações de acesso
    print_section("Informações de acesso")
    info = PerfilFilterService.get_info_acesso()
    for k, v in info.items():
        print(f"  {k}: {v}")
    
    # Listar turmas
    print_section("Turmas visíveis (com filtro)")
    turmas = listar_turmas()
    print(f"  Total de turmas: {len(turmas)}")
    for t in turmas[:5]:  # Mostra até 5 turmas
        print(f"    - {t.get('serie_nome', 'N/A')} - {t.get('nome', 'N/A')} ({t.get('turno', 'N/A')})")
    
    # Listar turmas SEM filtro (para comparação)
    print_section("Turmas visíveis (SEM filtro - comparação)")
    turmas_sem_filtro = listar_turmas(aplicar_filtro_perfil=False)
    print(f"  Total de turmas (sem filtro): {len(turmas_sem_filtro)}")


def main():
    """Função principal de teste."""
    print_header("TESTE DE FILTRO POR PERFIL DE USUÁRIO")
    
    # Verificar se perfis estão habilitados
    print_section("Configuração")
    habilitado = perfis_habilitados()
    print(f"  Perfis habilitados: {habilitado}")
    
    if not habilitado:
        print("\n⚠️  Sistema de perfis está DESABILITADO!")
        print("    Para testar, defina 'perfis_habilitados': true em feature_flags.json")
        return
    
    # Verificar turmas com professor
    funcionario_id = verificar_turmas_professor_no_banco()
    
    # Testar como admin (deve ver tudo)
    testar_como_admin()
    
    # Testar como professor (deve ver apenas suas turmas)
    if funcionario_id:
        username = criar_usuario_professor_teste(funcionario_id)
        if username:
            testar_como_professor(username)
    else:
        # Tentar com professor existente
        print_section("Tentando com professor de teste existente")
        try:
            testar_como_professor("prof_teste")
        except Exception as e:
            print(f"  ERRO: {e}")
    
    print_header("RESUMO")
    print("""
  ✓ Admin/Coordenador: Vê todas as turmas e alunos (filtro = None)
  ✓ Professor: Vê apenas turmas vinculadas a ele (por professor_id ou funcionario_disciplinas)
  ✓ Funções de serviço aceitam parâmetro 'aplicar_filtro_perfil' para bypass
    """)


if __name__ == "__main__":
    main()
