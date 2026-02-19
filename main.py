import sys
import os

# Adicionar diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports essenciais
from src.core.config_logs import get_logger, setup_logging
from src.core.config import perfis_habilitados

# Importar settings centralizado
try:
    from src.core.config.settings import settings, validate_settings
    HAS_SETTINGS = True
except ImportError:
    settings = None
    HAS_SETTINGS = False

# Configurar logging ANTES de criar o logger
setup_logging()

# Logger
logger = get_logger(__name__)

# TEST_MODE: Deprecated - usar GESTAO_TEST_MODE no .env
# Mantido por compatibilidade
TEST_MODE = False


def log_startup_info():
    """Registra informações do ambiente e versão no início da aplicação."""
    if settings:
        logger.info("="*70)
        logger.info(f"Sistema de Gestão Escolar v{settings.version}")
        logger.info("="*70)
        logger.info(f"Ambiente: {'TESTE' if settings.app.test_mode else 'PRODUÇÃO'}")
        logger.info(f"Banco: {settings.database.host}/{settings.database.name}")
        logger.info(f"Escola ID: {settings.app.escola_id}")
        logger.info(f"Backup automático: {'HABILITADO' if settings.backup.enabled else 'DESABILITADO'}")
        logger.info(f"Log Level: {settings.log.level}")
        logger.info(f"Log Format: {settings.log.format}")
        logger.info("="*70)
    else:
        logger.warning("Settings não disponível - usando configuração padrão")


def main():
    """
    Função principal da aplicação.
    
    Se perfis estiverem habilitados, exibe tela de login primeiro.
    Caso contrário, abre a aplicação diretamente (comportamento atual).
    """
    try:
        # Validar configurações (falha rápido se houver erro crítico)
        if HAS_SETTINGS:
            try:
                validate_settings()
                logger.debug("✓ Configurações validadas com sucesso")
            except ValueError as e:
                logger.error(f"Erro de configuração: {e}")
                logger.error("Verifique seu arquivo .env e corrija os erros antes de continuar")
                sys.exit(1)
        
        # Log de inicialização com informações do ambiente
        log_startup_info()
        
        # Importar Application após validar settings (lazy import)
        logger.debug("Importando módulos da aplicação...")
        from src.ui.app import Application
        logger.debug("✓ Módulos importados")
        # Verificar se sistema de perfis está habilitado
        if perfis_habilitados():
            logger.info("🔐 Sistema de perfis habilitado - Exibindo tela de login")
            
            # Importar e exibir tela de login (lazy imports)
            import tkinter as tk
            from src.ui.login import LoginWindow
            from auth import UsuarioLogado
            
            # Criar uma janela Tk temporária para o login
            root_temp = tk.Tk()
            root_temp.withdraw()  # Esconder a janela root temporária
            
            login_window = LoginWindow(root=root_temp)
            usuario = login_window.mostrar()
            
            if not usuario:
                # Usuário cancelou ou fechou a janela
                logger.info("Login cancelado pelo usuário")
                root_temp.destroy()
                sys.exit(0)
            
            logger.info(f"✅ Usuário autenticado: {usuario.username} ({usuario.perfil_display})")
            
            # Destruir a janela temporária APÓS obter o usuário
            try:
                root_temp.quit()
                root_temp.destroy()
            except:
                pass
            
            logger.debug("Janela de login destruída, criando aplicação principal...")
            
            # Feedback visual de carregamento
            logger.info("Inicializando interface principal...")
            
            # Criar aplicação passando o usuário logado
            app = Application(usuario=usuario)
            logger.debug("Aplicação criada com sucesso")
        else:
            # Fluxo normal - sem login (comportamento atual)
            logger.info("Sistema de perfis desabilitado - Carregando sistema...")
            app = Application()
        
        # Inicializar todos os componentes (método único que orquestra tudo)
        logger.info("Configurando interface...")
        app.initialize()
        
        # Garantir que a janela principal fique visível e em foco
        janela = getattr(app, 'janela', None)
        if janela:
            janela.deiconify()  # Garante que esteja visível
            janela.lift()  # Traz para frente
            janela.focus_force()  # Força o foco
            janela.attributes('-topmost', True)  # Temporariamente no topo
            janela.after(100, lambda: janela.attributes('-topmost', False))  # Remove após 100ms
        
        # Configurar fechamento da aplicação com backup
        if janela:
            # Usar configuração de test_mode do settings se disponível
            test_mode = settings.app.test_mode if settings else TEST_MODE
            janela.protocol("WM_DELETE_WINDOW", lambda: app.on_close_with_backup(test_mode=test_mode))
        
        # Iniciar sistema de backup automático (respeitando configuração)
        test_mode = settings.app.test_mode if settings else TEST_MODE
        app.setup_backup(test_mode=test_mode)
        
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
