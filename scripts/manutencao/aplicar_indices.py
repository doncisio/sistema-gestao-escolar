"""
Script para aplicar índices de otimização na interface de histórico escolar
"""

from src.core.conexao import conectar_bd
from src.core.config_logs import get_logger

logger = get_logger(__name__)

def aplicar_indices():
    """Aplica índices de otimização no banco de dados"""
    conn = conectar_bd()
    if not conn:
        logger.error("Não foi possível conectar ao banco de dados")
        return False
    
    cursor = conn.cursor()
    
    indices = [
        ("idx_aluno_historico", 
         "CREATE INDEX idx_aluno_historico ON historico_escolar(aluno_id, ano_letivo_id, serie_id, escola_id)"),
        
        ("idx_disciplinas_escola_nivel",
         "CREATE INDEX idx_disciplinas_escola_nivel ON disciplinas(escola_id, nivel_id)"),
        
        ("idx_alunos_nome",
         "CREATE INDEX idx_alunos_nome ON alunos(nome)"),
        
        ("idx_observacoes_historico",
         "CREATE INDEX idx_observacoes_historico ON observacoes_historico(serie_id, ano_letivo_id, escola_id)"),
        
        ("idx_carga_horaria_total",
         "CREATE INDEX idx_carga_horaria_total ON carga_horaria_total(serie_id, ano_letivo_id, escola_id)")
    ]
    
    sucesso = 0
    erros = 0
    ja_existem = 0
    
    for nome_indice, sql_indice in indices:
        try:
            # Verificar se o índice já existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.statistics 
                WHERE table_schema = DATABASE() 
                AND index_name = %s
            """, (nome_indice,))
            
            existe = cursor.fetchone()[0] > 0
            
            if existe:
                logger.info(f"Índice {nome_indice} já existe, pulando...")
                ja_existem += 1
                continue
            
            # Criar o índice
            cursor.execute(sql_indice)
            conn.commit()
            logger.info(f"Índice {nome_indice} criado com sucesso!")
            sucesso += 1
            
        except Exception as e:
            logger.error(f"Erro ao criar índice {nome_indice}: {str(e)}")
            erros += 1
            conn.rollback()
    
    cursor.close()
    conn.close()
    
    # Relatório
    print("\n" + "="*60)
    print("RELATÓRIO DE CRIAÇÃO DE ÍNDICES")
    print("="*60)
    print(f"Índices criados com sucesso: {sucesso}")
    print(f"Índices que já existiam: {ja_existem}")
    print(f"Erros: {erros}")
    print("="*60 + "\n")
    
    return erros == 0

if __name__ == "__main__":
    print("Aplicando índices de otimização...")
    if aplicar_indices():
        print("✓ Índices aplicados com sucesso!")
    else:
        print("✗ Houve erros ao aplicar alguns índices. Verifique o log.")
