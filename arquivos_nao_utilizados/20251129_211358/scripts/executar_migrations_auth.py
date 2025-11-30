"""
Script para executar as migrations do sistema de autenticação.

Executa os scripts SQL na pasta migrations/ em ordem.

Uso:
    python scripts/executar_migrations_auth.py
"""

import sys
import os
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from conexao import conectar_bd
from config_logs import get_logger

logger = get_logger(__name__)

MIGRATIONS_DIR = Path(__file__).parent.parent / 'migrations'

# Ordem de execução das migrations
MIGRATIONS = [
    '001_criar_tabela_usuarios.sql',
    '002_criar_tabela_permissoes.sql',
    '003_inserir_permissoes_base.sql',
]


def executar_sql_file(cursor, arquivo: Path) -> bool:
    """Executa um arquivo SQL."""
    print(f"\n📄 Executando: {arquivo.name}")
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Dividir em statements individuais (por ;)
        # Ignorar comentários de linha única
        statements = []
        current_statement = []
        
        for line in sql_content.split('\n'):
            stripped = line.strip()
            
            # Ignorar linhas vazias e comentários
            if not stripped or stripped.startswith('--'):
                continue
            
            current_statement.append(line)
            
            # Se termina com ; é fim do statement
            if stripped.endswith(';'):
                full_statement = '\n'.join(current_statement).strip()
                if full_statement:
                    statements.append(full_statement)
                current_statement = []
        
        # Executar cada statement
        for i, statement in enumerate(statements, 1):
            try:
                # Ignorar SET FOREIGN_KEY_CHECKS e TRUNCATE comentados
                if statement.strip().startswith('SET FOREIGN_KEY_CHECKS') or \
                   statement.strip().startswith('TRUNCATE'):
                    continue
                
                cursor.execute(statement)
                # Consumir resultados se houver (para evitar "Unread result found")
                try:
                    cursor.fetchall()
                except:
                    pass
                    
            except Exception as e:
                # Ignorar erros de "já existe" para permitir reexecução
                erro_str = str(e).lower()
                if 'already exists' in erro_str or 'duplicate' in erro_str:
                    print(f"   ⚠️  Objeto já existe (ignorado)")
                else:
                    print(f"   ❌ Erro no statement {i}: {e}")
                    # Mostrar trecho do statement
                    trecho = statement[:100] + "..." if len(statement) > 100 else statement
                    print(f"      Statement: {trecho}")
        
        print(f"   ✅ {arquivo.name} executado com sucesso")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao executar {arquivo.name}: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("🔧 Executor de Migrations - Sistema de Autenticação")
    print("=" * 60)
    
    # Verificar conexão
    print("\n🔌 Conectando ao banco de dados...")
    conn = conectar_bd()
    
    if not conn:
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        print("   Verifique as configurações no arquivo .env")
        sys.exit(1)
    
    print("✅ Conexão estabelecida")
    
    cursor = conn.cursor()
    
    # Verificar se pasta de migrations existe
    if not MIGRATIONS_DIR.exists():
        print(f"❌ Erro: Pasta de migrations não encontrada: {MIGRATIONS_DIR}")
        cursor.close()
        conn.close()
        sys.exit(1)
    
    # Executar migrations
    print(f"\n📁 Pasta de migrations: {MIGRATIONS_DIR}")
    print(f"📋 Total de migrations: {len(MIGRATIONS)}")
    
    sucesso = 0
    falhas = 0
    
    for migration in MIGRATIONS:
        arquivo = MIGRATIONS_DIR / migration
        
        if not arquivo.exists():
            print(f"\n⚠️  Arquivo não encontrado: {migration}")
            falhas += 1
            continue
        
        if executar_sql_file(cursor, arquivo):
            sucesso += 1
        else:
            falhas += 1
    
    # Commit das alterações
    conn.commit()
    
    # Verificar tabelas criadas
    print("\n" + "-" * 60)
    print("📊 Verificando tabelas criadas...")
    
    tabelas_esperadas = ['usuarios', 'permissoes', 'perfil_permissoes', 
                         'usuario_permissoes', 'logs_acesso', 'sessoes_usuario']
    
    cursor.execute("SHOW TABLES")
    tabelas_existentes = [row[0] for row in cursor.fetchall()]
    
    for tabela in tabelas_esperadas:
        if tabela in tabelas_existentes:
            print(f"   ✅ {tabela}")
        else:
            print(f"   ❌ {tabela} (não encontrada)")
    
    # Contar permissões
    try:
        cursor.execute("SELECT COUNT(*) FROM permissoes")
        result = cursor.fetchone()
        if result:
            # result is typically a sequence like (count,)
            total_permissoes = result[0]
        else:
            total_permissoes = 0
        print(f"\n📋 Total de permissões cadastradas: {total_permissoes}")
        
        cursor.execute("""
            SELECT perfil, COUNT(*) 
            FROM perfil_permissoes 
            GROUP BY perfil
        """)
        print("\n📋 Permissões por perfil:")
        for row in cursor.fetchall():
            # row can be a sequence; format accordingly
            nome_perfil = row[0] if isinstance(row, (list, tuple)) else row.get('perfil')
            quantidade = row[1] if isinstance(row, (list, tuple)) else row.get('COUNT(*)')
            print(f"   • {nome_perfil}: {quantidade} permissões")
    except Exception as e:
        print(f"⚠️  Não foi possível contar permissões: {e}")
    
    cursor.close()
    conn.close()
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DA EXECUÇÃO")
    print("=" * 60)
    print(f"   ✅ Sucesso: {sucesso}")
    print(f"   ❌ Falhas:  {falhas}")
    
    if falhas == 0:
        print("\n🎉 Todas as migrations foram executadas com sucesso!")
        print("\n💡 Próximo passo:")
        print("   Execute: python scripts/criar_usuario_admin.py")
    else:
        print("\n⚠️  Algumas migrations falharam. Verifique os erros acima.")
    
    print()


if __name__ == '__main__':
    main()
