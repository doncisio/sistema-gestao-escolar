"""
Script para aplicar a migration da tabela notas_finais

Este script:
1. Verifica se a tabela já existe
2. Cria a tabela notas_finais se não existir
3. Exibe confirmação

Uso:
    python aplicar_migration_notas_finais.py
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.conexao import conectar_bd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verificar_tabela_existe(cursor, nome_tabela):
    """Verifica se uma tabela existe no banco de dados"""
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables 
        WHERE table_schema = DATABASE()
        AND table_name = %s
    """, (nome_tabela,))
    
    resultado = cursor.fetchone()
    return resultado[0] > 0

def aplicar_migration():
    """Aplica a migration da tabela notas_finais"""
    try:
        logger.info("="*60)
        logger.info("APLICAÇÃO DE MIGRATION: notas_finais")
        logger.info("="*60)
        
        # Conectar ao banco
        logger.info("\n→ Conectando ao banco de dados...")
        conn = conectar_bd()
        if not conn:
            logger.error("✗ Erro ao conectar ao banco de dados")
            return False
        
        cursor = conn.cursor()
        logger.info("✓ Conectado ao banco de dados")
        
        # Verificar se a tabela já existe
        logger.info("\n→ Verificando se a tabela 'notas_finais' já existe...")
        if verificar_tabela_existe(cursor, 'notas_finais'):
            logger.warning("⚠️ A tabela 'notas_finais' já existe!")
            resposta = input("\nDeseja recriar a tabela? (isso irá apagar todos os dados) [s/N]: ")
            
            if resposta.lower() != 's':
                logger.info("✓ Migration cancelada pelo usuário")
                cursor.close()
                conn.close()
                return True
            
            logger.info("\n→ Removendo tabela existente...")
            cursor.execute("DROP TABLE IF EXISTS notas_finais")
            logger.info("✓ Tabela removida")
        else:
            logger.info("✓ Tabela não existe, prosseguindo com criação")
        
        # Ler o arquivo SQL de migration
        logger.info("\n→ Lendo arquivo de migration...")
        migration_path = os.path.join(os.path.dirname(__file__), '..', 'migrations', 'criar_tabela_notas_finais.sql')
        
        if not os.path.exists(migration_path):
            logger.error(f"✗ Arquivo de migration não encontrado: {migration_path}")
            cursor.close()
            conn.close()
            return False
        
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        logger.info("✓ Arquivo de migration carregado")
        
        # Separar comandos SQL (dividir por ponto e vírgula)
        logger.info("\n→ Executando migration...")
        comandos = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
        
        for i, comando in enumerate(comandos, 1):
            if comando:
                logger.info(f"  Executando comando {i}/{len(comandos)}...")
                cursor.execute(comando)
        
        # Commit
        conn.commit()
        logger.info("✓ Migration aplicada com sucesso!")
        
        # Verificar criação
        logger.info("\n→ Verificando criação da tabela...")
        if verificar_tabela_existe(cursor, 'notas_finais'):
            logger.info("✓ Tabela 'notas_finais' criada com sucesso!")
            
            # Mostrar estrutura
            cursor.execute("DESCRIBE notas_finais")
            colunas = cursor.fetchall()
            
            logger.info("\n📋 Estrutura da tabela 'notas_finais':")
            logger.info("-" * 80)
            for coluna in colunas:
                logger.info(f"  {coluna[0]:30} {coluna[1]:20} {coluna[2]:10} {coluna[3]:10}")
            logger.info("-" * 80)
        else:
            logger.error("✗ Erro: tabela não foi criada!")
            cursor.close()
            conn.close()
            return False
        
        # Fechar conexão
        cursor.close()
        conn.close()
        
        logger.info("\n" + "="*60)
        logger.info("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
        logger.info("="*60)
        logger.info("\nA tabela 'notas_finais' está pronta para uso.")
        logger.info("Você pode agora usar a opção 'Recuperação Anual' no menu GEDUC.")
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Erro ao aplicar migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("APLICAÇÃO DE MIGRATION: Tabela notas_finais")
    print("="*60)
    print("\nEste script irá criar a tabela 'notas_finais' no banco de dados.")
    print("Esta tabela é necessária para o funcionamento da Recuperação Anual.\n")
    
    resposta = input("Deseja continuar? [S/n]: ")
    
    if resposta.lower() in ['', 's', 'sim', 'yes', 'y']:
        sucesso = aplicar_migration()
        
        if sucesso:
            print("\n✅ Migration aplicada com sucesso!")
            sys.exit(0)
        else:
            print("\n✗ Falha ao aplicar migration")
            sys.exit(1)
    else:
        print("\n✓ Operação cancelada pelo usuário")
        sys.exit(0)
