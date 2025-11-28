"""Teste com logging habilitado."""

import sys
sys.path.insert(0, r'c:\gestao')

import logging
logging.basicConfig(level=logging.DEBUG)

# Testar a função diretamente com mais detalhes
from db.connection import get_connection
from config_logs import get_logger

logger = get_logger(__name__)

def test_listar_turmas():
    """Cópia da função para debug."""
    try:
        logger.debug("Iniciando listar_turmas")
        
        with get_connection() as conn:
            logger.debug(f"Conexão obtida: {conn}")
            cursor = conn.cursor(dictionary=True)
            logger.debug("Cursor criado")
            
            query = """
                SELECT 
                    t.id,
                    t.nome,
                    t.turno
                FROM turmas t
                WHERE 1=1
                LIMIT 5
            """
            
            logger.debug(f"Executando query: {query[:100]}...")
            cursor.execute(query)
            logger.debug("Query executada")
            
            turmas = cursor.fetchall()
            logger.debug(f"Resultado: {len(turmas)} turmas")
            
            return turmas
            
    except Exception as e:
        logger.exception(f"Erro: {e}")
        raise

print("Executando teste manual:")
resultado = test_listar_turmas()
print(f"Resultado manual: {resultado}")

print("\nAgora testando função original:")
from services.turma_service import listar_turmas
resultado2 = listar_turmas(aplicar_filtro_perfil=False)
print(f"Resultado original: {resultado2}")
