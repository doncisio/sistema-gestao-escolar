"""
Arquivo para executar a geração da lista de alunos matriculados após o início do ano letivo (TRANSFERÊNCIAS RECEBIDAS).
"""
from config_logs import get_logger
logger = get_logger(__name__)

if __name__ == "__main__":
    try:
        from movimentomensal import gerar_lista_alunos_matriculados_depois
        
        logger.info("=" * 60)
        logger.info("GERANDO LISTA DE TRANSFERÊNCIAS RECEBIDAS")
        logger.info("=" * 60)
        
        gerar_lista_alunos_matriculados_depois()
        
        logger.info("=" * 60)
        logger.info("PROCESSO CONCLUÍDO")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Erro ao gerar lista: {e}", exc_info=True)
        print(f"ERRO: {e}")
        input("Pressione ENTER para sair...")
