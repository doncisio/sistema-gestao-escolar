"""
Arquivo para executar a geração da lista de alunos matriculados após o início do ano letivo.
Inclui alunos transferidos.
"""
from config_logs import get_logger
logger = get_logger(__name__)

if __name__ == "__main__":
    try:
        from Lista_atualizada import lista_matriculados_apos_inicio
        
        logger.info("=" * 60)
        logger.info("GERANDO LISTA DE ALUNOS MATRICULADOS APÓS O INÍCIO")
        logger.info("=" * 60)
        
        lista_matriculados_apos_inicio()
        
        logger.info("=" * 60)
        logger.info("PROCESSO CONCLUÍDO")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Erro ao gerar lista: {e}", exc_info=True)
        print(f"ERRO: {e}")
        input("Pressione ENTER para sair...")
