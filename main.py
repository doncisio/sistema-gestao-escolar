import sys
import os

# Adicionar diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports essenciais
from config_logs import get_logger
from ui.app import Application

# Logger
logger = get_logger(__name__)

# TEST_MODE: Usar variável de ambiente para controlar modo de teste
TEST_MODE = os.environ.get('GESTAO_TEST_MODE', 'false').lower() == 'true'


def main():
    """
    Função principal da aplicação.
    
    Cria a Application, inicializa todos os componentes e inicia o mainloop.
    """
    try:
        # Criar instância da aplicação
        logger.debug("Criando instância da Application...")
        app = Application()
        
        # Inicializar todos os componentes (método único que orquestra tudo)
        logger.debug("Inicializando componentes...")
        app.initialize()
        
        # Configurar fechamento da aplicação com backup
        if app.janela:
            app.janela.protocol("WM_DELETE_WINDOW", lambda: app.on_close_with_backup(test_mode=TEST_MODE))
        
        # Iniciar sistema de backup automático (se não estiver em modo teste)
        app.setup_backup(test_mode=TEST_MODE)
        
        # Iniciar mainloop
        logger.info("✅ Sistema pronto - Iniciando interface")
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Aplicação interrompida pelo usuário (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Erro fatal ao inicializar aplicação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
