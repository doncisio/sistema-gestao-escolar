"""
Script para executar a migração da tabela livros_faltantes

Este script cria a tabela necessária para o controle de livros faltantes
por turma e disciplina.

Uso:
    python executar_migracao_livros_faltantes.py
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.conexao import conectar_bd
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def executar_migracao():
    """Executa a migração da tabela livros_faltantes."""
    try:
        logger.info("Conectando ao banco de dados...")
        conn = conectar_bd()
        cursor = conn.cursor()
        
        # Ler o arquivo SQL de migração
        migration_file = os.path.join(
            os.path.dirname(__file__),
            'db',
            'migrations',
            'criar_tabela_livros_faltantes.sql'
        )
        
        logger.info(f"Lendo arquivo de migração: {migration_file}")
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Dividir em comandos individuais (separados por ponto e vírgula)
        commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
        
        logger.info(f"Executando {len(commands)} comandos SQL...")
        
        for i, command in enumerate(commands, 1):
            if command.strip():
                try:
                    logger.debug(f"Executando comando {i}/{len(commands)}")
                    cursor.execute(command)
                    conn.commit()
                except Exception as e:
                    # Se for erro de tabela já existente, apenas avisa
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        logger.warning(f"Tabela já existe (ignorado): {e}")
                    else:
                        raise
        
        logger.info("✓ Migração executada com sucesso!")
        logger.info("A tabela 'livros_faltantes' foi criada/atualizada.")
        
        # Verificar se a tabela foi criada
        cursor.execute("SHOW TABLES LIKE 'livros_faltantes'")
        if cursor.fetchone():
            logger.info("✓ Tabela 'livros_faltantes' confirmada no banco de dados.")
            
            # Mostrar estrutura da tabela
            cursor.execute("DESCRIBE livros_faltantes")
            colunas = cursor.fetchall()
            logger.info("Estrutura da tabela:")
            for coluna in colunas:
                logger.info(f"  - {coluna[0]}: {coluna[1]}")
        else:
            logger.error("✗ Tabela 'livros_faltantes' NÃO foi encontrada!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao executar migração: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("MIGRAÇÃO: Criação da tabela livros_faltantes")
    print("=" * 70)
    print()
    
    sucesso = executar_migracao()
    
    print()
    print("=" * 70)
    if sucesso:
        print("STATUS: SUCESSO ✓")
        print()
        print("Próximos passos:")
        print("1. Execute o sistema: python main.py")
        print("2. Acesse: Listas > Gerenciar Livros Faltantes")
        print("3. Cadastre os dados de livros faltantes por turma")
        print("4. Gere o PDF: Listas > Gerar PDF Livros Faltantes")
    else:
        print("STATUS: ERRO ✗")
        print("Verifique os erros acima e tente novamente.")
    print("=" * 70)
    
    sys.exit(0 if sucesso else 1)
