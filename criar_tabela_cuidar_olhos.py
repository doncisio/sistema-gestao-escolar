"""
Script para criar a tabela de seleções do Programa Cuidar dos Olhos
"""
from pathlib import Path
from src.core.config_logs import get_logger
from src.core.conexao import conectar_bd

logger = get_logger(__name__)

def criar_tabela_cuidar_olhos():
    """Cria a tabela cuidar_olhos_selecoes no banco de dados."""
    try:
        # Conectar ao banco de dados
        conn = conectar_bd()
        if not conn:
            logger.error("Não foi possível conectar ao banco de dados")
            return False
        
        cursor = conn.cursor()
        
        # Ler o arquivo SQL
        sql_file = Path(__file__).parent / 'sql' / 'criar_tabela_cuidar_olhos_selecoes.sql'
        logger.info(f"Lendo arquivo SQL: {sql_file}")
        
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # Remover comentários
        linhas = []
        for linha in sql_script.split('\n'):
            linha = linha.strip()
            if linha and not linha.startswith('--'):
                linhas.append(linha)
        
        sql_completo = ' '.join(linhas)
        
        logger.info(f"Executando SQL: {sql_completo[:200]}...")
        cursor.execute(sql_completo)
        
        # Confirmar as alterações
        conn.commit()
        logger.info("✓ Tabela 'cuidar_olhos_selecoes' criada com sucesso!")
        
        # Verificar se realmente foi criada
        cursor.execute("SHOW TABLES LIKE 'cuidar_olhos_selecoes'")
        result = cursor.fetchone()
        
        if result:
            logger.info("✓ Tabela verificada - existe no banco!")
        else:
            logger.error("✗ Tabela não foi encontrada após criação!")
            cursor.close()
            conn.close()
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.exception(f"Erro ao criar tabela: {e}")
        return False

if __name__ == '__main__':
    print("=" * 70)
    print("CRIAÇÃO DE TABELA: cuidar_olhos_selecoes")
    print("=" * 70)
    print()
    
    sucesso = criar_tabela_cuidar_olhos()
    
    if sucesso:
        print("\n✓ Tabela criada com sucesso!")
        print("\nAgora as seleções do Programa Cuidar dos Olhos serão")
        print("salvas no banco de dados e poderão ser recuperadas no futuro.")
    else:
        print("\n✗ Erro ao criar tabela. Verifique os logs para detalhes.")
    
    print("\n" + "=" * 70)
