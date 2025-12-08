import sys
import os

# Adicionar diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports essenciais
from config_logs import get_logger
from config import perfis_habilitados
from ui.app import Application

# Logger
logger = get_logger(__name__)

# TEST_MODE: Usar variável de ambiente para controlar modo de teste
# Forçar execução dos backups automáticos por padrão (pode ser sobrescrito
# pela variável de ambiente se quiser alterar manualmente)
TEST_MODE = False


def main():
    """
    Função principal da aplicação.
    
    Se perfis estiverem habilitados, exibe tela de login primeiro.
    Caso contrário, abre a aplicação diretamente (comportamento atual).
    """
    try:
        # Verificar se sistema de perfis está habilitado
        if perfis_habilitados():
            logger.info("🔐 Sistema de perfis habilitado - Exibindo tela de login")
            
            # Importar e exibir tela de login
            from ui.login import LoginWindow
            from auth import UsuarioLogado
            import tkinter as tk
            
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
            
            # Criar aplicação passando o usuário logado
            app = Application(usuario=usuario)
            logger.debug("Aplicação criada com sucesso")
        else:
            # Fluxo normal - sem login (comportamento atual)
            logger.debug("Sistema de perfis desabilitado - Abrindo direto")
            app = Application()
        
        # Inicializar todos os componentes (método único que orquestra tudo)
        logger.debug("Inicializando componentes...")
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
            janela.protocol("WM_DELETE_WINDOW", lambda: app.on_close_with_backup(test_mode=TEST_MODE))
        
        # Iniciar sistema de backup automático (sempre ativo por padrão)
        app.setup_backup(test_mode=False)
        
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
