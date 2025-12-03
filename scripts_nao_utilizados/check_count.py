import os
import sys
from config_logs import get_logger
logger = get_logger(__name__)

# Garantir que a raiz do projeto esteja em sys.path para que imports locais
# (como `utils.db_config`) resolvam corretamente tanto em tempo de execução
# quanto para ferramentas de análise estática quando o script é executado
# a partir da pasta `scripts_nao_utilizados`.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import protegido: o comentário `# type: ignore` suprime o aviso do
# Pylance quando ele não consegue resolver o import estático.
try:
    from utils.db_config import get_db_config  # type: ignore
except Exception:
    # Fallback simples caso o módulo não exista no ambiente de execução
    def get_db_config():
        return {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'user': os.environ.get('DB_USER', 'root'),
            'password': os.environ.get('DB_PASSWORD', ''),
            'database': os.environ.get('DB_NAME', 'gestao'),
            'port': int(os.environ.get('DB_PORT', 3306)),
        }

import mysql.connector
from typing import Any, Dict, Optional

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
            JOIN series s ON t.serie_id = s.id
            WHERE t.id = %s
        ''', (turma_id,))
        turma = cursor.fetchone()
        # cursor.fetchone() com `dictionary=True` deve retornar um dict, mas
        # verificamos o tipo explicitamente para suprimir avisos do Pylance
        # e evitar erros caso a API retorne outro formato.
        if turma and isinstance(turma, dict):
            total = int(turma.get('total') or 0)
            total_alunos_mencionadas += total
            logger.info(f"Turma ID={turma.get('id')}, Série={turma.get('serie_nome')}, Nome={turma.get('turma_nome') or '-'}, Turno={turma.get('turno')}, Total Alunos={total}")
    
    logger.info(f"\nTotal de alunos nas turmas mencionadas: {total_alunos_mencionadas}")

    # Buscar todas as turmas com alunos
    logger.info("\nTodas as turmas com alunos ativos:")
    logger.info("----------------------------------")
    
    cursor.execute('''
        SELECT t.id, s.nome as serie_nome, t.nome as turma_nome, t.turno,
              (SELECT COUNT(*) FROM matriculas m WHERE m.turma_id = t.id AND m.status = 'Ativo') as total
        FROM Turmas t 
        JOIN series s ON t.serie_id = s.id
        HAVING total > 0
        ORDER BY s.nome, t.nome
    ''')
    
    turmas = cursor.fetchall()
    
    total_geral = 0
    for turma in turmas:
        if not isinstance(turma, dict):
            continue
        total_alunos = int(turma.get('total') or 0)
        total_geral += total_alunos
        logger.info(f"Turma ID={turma.get('id')}, Série={turma.get('serie_nome')}, Nome={turma.get('turma_nome') or '-'}, Turno={turma.get('turno')}, Total Alunos={total_alunos}")
    
    logger.info(f"\nTotal de alunos em todas as turmas com matrícula ativa: {total_geral}")
    
    # Verificar total geral de alunos ativos
    cursor.execute("SELECT COUNT(*) as total FROM matriculas WHERE status = 'Ativo'")
    result = cursor.fetchone()
    total_ativos = int(result.get('total') or 0) if isinstance(result, dict) else 0
    logger.info(f"Total geral de alunos ativos de acordo com a tabela de matrículas: {total_ativos}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    count_students() 
