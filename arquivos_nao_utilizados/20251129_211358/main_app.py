"""
Exemplo de uso da arquitetura OOP refatorada (Sprint 5 - COMPLETO)

Este arquivo demonstra como usar a classe Application com todos os componentes:
- Application: Gerenciador principal da aplicação
- ActionHandler: Gerenciador de ações (botões, eventos)
- MenuManager: Gerenciador de menus (contextual, dropdowns)
- TableManager: Gerenciador da tabela (Treeview)

Refatorado do main.py monolítico para arquitetura modular baseada em classes.
Sprint 5: Integração completa com menus e botões de ação.
"""

from ui.app import Application
from config_logs import get_logger

logger = get_logger(__name__)


def main():
    """Ponto de entrada da aplicação."""
    try:
        logger.info("=== Iniciando aplicação com arquitetura Sprint 5 ===")
        
        # Criar instância da aplicação
        app = Application()
        
        # Configurar frames básicos
        logger.info("Configurando frames...")
        app.setup_frames()
        
        # Configurar logo/header
        logger.info("Configurando logo...")
        app.setup_logo()
        
        # Configurar handlers antes de criar componentes que os usam
        logger.info("Configurando ActionHandler e MenuManager...")
        app.setup_action_handler()
        app.setup_menu_manager()
        
        # Configurar barra de pesquisa (delegando para ActionHandler)
        def pesquisar():
            """Callback de pesquisa - delega para ActionHandler."""
            # Aqui você pode capturar o termo do campo de entrada
            # Por simplicidade, usando exemplo fixo
            termo = "exemplo"
            app.action_handler.pesquisar(termo)
            app.update_status(f"Pesquisando por: {termo}")
        
        logger.info("Configurando barra de pesquisa...")
        app.setup_search(pesquisar)
        
        # Configurar botões de ação principais
        # Estes botões chamam automaticamente os métodos do ActionHandler:
        # - cadastrar_novo_aluno()
        # - cadastrar_novo_funcionario()
        # - abrir_historico_escolar()
        # - abrir_interface_administrativa()
        logger.info("Configurando botões de ação...")
        app.setup_action_buttons(app.frames['frame_dados'])
        
        # Configurar tabela com callback de seleção
        def on_select(event):
            """Callback quando item é selecionado na tabela."""
            if app.table_manager:
                selected = app.table_manager.get_selected_item()
                if selected:
                    app.selected_item = selected
                    logger.debug(f"Item selecionado: {selected[0]}")
                    app.update_status(f"Selecionado: ID {selected[0]}")
        
        logger.info("Configurando tabela...")
        app.setup_table(on_select_callback=on_select)
        
        # Configurar menu contextual (clique direito na tabela)
        # Menu inclui: Editar, Excluir, Ver Detalhes
        logger.info("Configurando menu contextual...")
        app.setup_context_menu()
        
        # Configurar rodapé
        logger.info("Configurando rodapé...")
        app.setup_footer()
        
        # Dados de exemplo para a tabela
        dados_exemplo = [
            (1, 'João Silva', '10/05/2010', 'Ativo', '5º Ano'),
            (2, 'Maria Santos', '15/03/2011', 'Ativo', '4º Ano'),
            (3, 'Pedro Costa', '20/08/2009', 'Transferido', '6º Ano'),
            (4, 'Ana Oliveira', '25/11/2010', 'Ativo', '5º Ano'),
            (5, 'Carlos Souza', '05/02/2011', 'Ativo', '4º Ano')
        ]
        
        colunas_exemplo = ['ID', 'Nome', 'Data Nasc.', 'Status', 'Série']
        
        # Atualizar tabela com dados de exemplo
        if app.table_manager:
            app.table_manager.criar_tabela(
                colunas=colunas_exemplo,
                on_select_callback=on_select
            )
            app.table_manager.atualizar_dados(dados_exemplo)
            app.table_manager.show()
            logger.info(f"Tabela configurada com {len(dados_exemplo)} registros de exemplo")
        
        # Atualizar status inicial
        app.update_status("Sistema iniciado - Arquitetura OOP Sprint 5")
        
        # Log de componentes criados
        logger.info("=== Componentes configurados com sucesso ===")
        logger.info(f"- ActionHandler: {app.action_handler is not None}")
        logger.info(f"- MenuManager: {app.menu_manager is not None}")
        logger.info(f"- TableManager: {app.table_manager is not None}")
        logger.info(f"- Frames: {list(app.frames.keys())}")
        
        # Iniciar loop principal
        logger.info("Iniciando mainloop da aplicação...")
        app.run()
        
        logger.info("=== Aplicação encerrada com sucesso ===")
        
    except Exception as e:
        logger.exception(f"Erro fatal na aplicação: {e}")
        raise


if __name__ == '__main__':
    main()
