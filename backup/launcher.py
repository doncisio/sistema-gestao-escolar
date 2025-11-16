import sys
import os
import importlib.util
from config_logs import get_logger

logger = get_logger(__name__)

def importar_modulo(nome_arquivo):
    """Importa um módulo pelo nome do arquivo."""
    try:
        spec = importlib.util.spec_from_file_location(nome_arquivo, nome_arquivo)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo
    except Exception as e:
        logger.exception("Erro ao importar %s: %s", nome_arquivo, e)
        return None

# Função principal
def main():
    logger.info("Iniciando o Sistema de Gerenciamento Escolar...")
    
    # Verificar e configurar o MySQL
    verificar_mysql = importar_modulo("verificar_mysql.py")
    
    if verificar_mysql and verificar_mysql.main():
        logger.info("MySQL configurado com sucesso. Iniciando o sistema...")
        
        # Importar e executar o aplicativo principal
        app_principal = importar_modulo("main.py")
        
        if app_principal:
            # O main.py já executa o aplicativo
            pass
        else:
            logger.error("Erro ao iniciar o aplicativo principal.")
            return False
    else:
        logger.error("Configuração do MySQL falhou. O aplicativo não pode ser iniciado.")
        return False
    
    return True

if __name__ == "__main__":
    main() 