"""
Script para executar migração SQL usando a conexão do sistema
Autor: Sistema de Gestão Escolar
Data: 14/12/2025
"""

from src.core.config_logs import get_logger
logger = get_logger(__name__)

import sys
from src.core.conexao import conectar_bd

def executar_migracao():
    """Executa o script SQL de migração."""
    print("\n" + "="*80)
    print(" EXECUTANDO MIGRAÇÃO: Tabelas de Avaliações e Respostas")
    print("="*80 + "\n")
    
    # Ler arquivo SQL (versão simplificada sem procedures)
    sql_file = r"c:\gestao\db\migrations\adicionar_tabelas_avaliacoes_respostas_simples.sql"
    
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print(f"✅ Arquivo SQL lido: {sql_file}")
        print(f"   Tamanho: {len(sql_script)} caracteres\n")
        
    except Exception as e:
        print(f"❌ Erro ao ler arquivo SQL: {e}")
        return False
    
    # Conectar ao banco
    conn = conectar_bd()
    if not conn:
        print("❌ Falha ao conectar ao banco de dados")
        return False
    
    print("✅ Conectado ao banco de dados\n")
    
    # Executar script
    cursor = conn.cursor()
    
    try:
        # Ler o arquivo inteiro e executar com multi=True
        print(f"Executando script SQL completo...\n")
        
        # Executar múltiplos statements
        for result in cursor.execute(sql_script, multi=True):
            if result.with_rows:
                rows = result.fetchall()
                for row in rows:
                    print(f"  {row}")
        
        # Commit
        conn.commit()
        
        print(f"\n{'='*80}")
        print(f" MIGRAÇÃO CONCLUÍDA")
        print(f"{'='*80}")
        print(f"\n🎉 Migração executada com sucesso!")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro fatal durante migração: {e}")
        logger.error(f"Erro fatal: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()
        print("\n✅ Conexão com banco encerrada")

if __name__ == "__main__":
    sucesso = executar_migracao()
    sys.exit(0 if sucesso else 1)
