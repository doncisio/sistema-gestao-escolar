from config_logs import get_logger
logger = get_logger(__name__)
from utils.db_config import get_db_config
import mysql.connector

def count_students():
    db_config = get_db_config()
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # Verificar turmas mencionadas pelo usuário
    turmas_usuario = [28, 29, 30, 33, 35]
    logger.info("Turmas específicas mencionadas pelo usuário:")
    logger.info("-------------------------------------------")
    total_alunos_mencionadas = 0
    
    for turma_id in turmas_usuario:
        cursor.execute('''
            SELECT t.id, s.nome as serie_nome, t.nome as turma_nome, t.turno,
                  (SELECT COUNT(*) FROM matriculas m WHERE m.turma_id = t.id AND m.status = 'Ativo') as total
            FROM Turmas t 
            JOIN Serie s ON t.serie_id = s.id
            WHERE t.id = %s
        ''', (turma_id,))
        turma = cursor.fetchone()
        if turma:
            total_alunos_mencionadas += turma['total']
            logger.info(f"Turma ID={turma['id']}, Série={turma['serie_nome']}, Nome={turma['turma_nome'] or '-'}, Turno={turma['turno']}, Total Alunos={turma['total']}")
    
    logger.info(f"\nTotal de alunos nas turmas mencionadas: {total_alunos_mencionadas}")

    # Buscar todas as turmas com alunos
    logger.info("\nTodas as turmas com alunos ativos:")
    logger.info("----------------------------------")
    
    cursor.execute('''
        SELECT t.id, s.nome as serie_nome, t.nome as turma_nome, t.turno,
              (SELECT COUNT(*) FROM matriculas m WHERE m.turma_id = t.id AND m.status = 'Ativo') as total
        FROM Turmas t 
        JOIN Serie s ON t.serie_id = s.id
        HAVING total > 0
        ORDER BY s.nome, t.nome
    ''')
    
    turmas = cursor.fetchall()
    
    total_geral = 0
    for turma in turmas:
        total_alunos = turma['total']
        total_geral += total_alunos
        logger.info(f"Turma ID={turma['id']}, Série={turma['serie_nome']}, Nome={turma['turma_nome'] or '-'}, Turno={turma['turno']}, Total Alunos={total_alunos}")
    
    logger.info(f"\nTotal de alunos em todas as turmas com matrícula ativa: {total_geral}")
    
    # Verificar total geral de alunos ativos
    cursor.execute("SELECT COUNT(*) as total FROM matriculas WHERE status = 'Ativo'")
    result = cursor.fetchone()
    logger.info(f"Total geral de alunos ativos de acordo com a tabela de matrículas: {result['total']}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    count_students() 