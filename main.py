import sys
import os

# Adicionar diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports essenciais
from tkinter import messagebox
from config_logs import get_logger
from ui.app import Application
import Seguranca

# Logger
logger = get_logger(__name__)

# TEST_MODE: Usar variável de ambiente para controlar modo de teste
TEST_MODE = os.environ.get('GESTAO_TEST_MODE', 'false').lower() == 'true'

if TEST_MODE:
    logger.warning("⚠️ SISTEMA EM MODO DE TESTE - Backups automáticos desabilitados")


def main():
    """
    Função principal da aplicação.
    
    Cria e inicializa a Application, configura todos os componentes
    e inicia o mainloop.
    """
    try:
        # Criar instância da aplicação
        logger.debug("Criando instância da Application...")
        app = Application()
        
        # Adicionar referência ao app na janela para acesso pelos callbacks
        if app.janela:
            setattr(app.janela, '_app_instance', app)  # type: ignore
        
        # Configurar frames principais
        logger.debug("Configurando frames...")
        app.setup_frames()
        
        # Configurar logo
        logger.debug("Configurando logo...")
        app.setup_logo()
        
        # Configurar callbacks de ações
        logger.debug("Configurando action callbacks...")
        app.setup_action_callbacks(atualizar_tabela_callback=None)  # TODO: implementar callback
        
        # Configurar botões e menus usando ButtonFactory
        logger.debug("Configurando botões e menus...")
        app.setup_action_buttons_and_menus()
        
        # Configurar barra de pesquisa
        logger.debug("Configurando pesquisa...")
        
        def pesquisar_callback(event=None):
            """Callback de pesquisa integrado"""
            from ui.search import pesquisar_alunos_funcionarios
            from ui.frames import criar_pesquisa
            
            # Obter referência ao Entry de pesquisa
            e_nome_pesquisa = app.e_nome_pesquisa
            if e_nome_pesquisa:
                texto = e_nome_pesquisa.get()
                
                # Executar pesquisa
                pesquisar_alunos_funcionarios(
                    texto_pesquisa=texto,
                    get_treeview_func=lambda: app.table_manager.treeview if app.table_manager else None,
                    get_tabela_frame_func=lambda: app.table_manager.tabela_frame if app.table_manager else None,
                    frame_tabela=app.frames.get('frame_tabela'),
                    criar_tabela_func=lambda: app.setup_table(on_select_callback=on_select_callback),
                    criar_dashboard_func=lambda: app.dashboard_manager.criar_dashboard() if app.dashboard_manager else None
                )
        
        app.setup_search(callback_pesquisa=pesquisar_callback)
        
        # Configurar tabela principal
        logger.debug("Configurando tabela...")
        
        def on_select_callback(event):
            """Callback de seleção na tabela"""
            try:
                from ui.detalhes import exibir_detalhes_item
                
                if not app.table_manager or not app.table_manager.treeview:
                    return
                
                treeview = app.table_manager.treeview
                selected = treeview.selection()
                
                if not selected:
                    return
                
                item = selected[0]
                values = treeview.item(item, 'values')
                
                if not values or len(values) < 3:
                    return
                
                # Estrutura Sprint 15: (id, nome, tipo, cargo, data_nascimento)
                # values[0] = ID
                # values[1] = Nome
                # values[2] = Tipo
                # values[3] = Cargo (funcionário) ou NULL (aluno)
                # values[4] = Data de nascimento
                
                item_id = values[0]
                tipo = values[2]
                
                # Atualizar selected_item na aplicação
                app.selected_item = {'tipo': tipo, 'id': item_id, 'values': values}
                
                logger.debug(f"Item selecionado: {tipo} ID={item_id}")
                
                # Atualizar logo/título
                if 'frame_logo' in app.frames:
                    frame_logo = app.frames['frame_logo']
                    for widget in frame_logo.winfo_children():
                        widget.destroy()
                    
                    # Criar frame para o título
                    from tkinter import Frame, Label, LEFT, BOTH, TRUE, X
                    from PIL import Image, ImageTk
                    
                    titulo_frame = Frame(frame_logo, bg=app.colors['co0'])
                    titulo_frame.pack(fill=BOTH, expand=TRUE)
                    
                    try:
                        # Tentar carregar ícone
                        app_lp = Image.open('icon/learning.png')
                        app_lp = app_lp.resize((30, 30))
                        app_lp = ImageTk.PhotoImage(app_lp)
                        app_logo = Label(titulo_frame, image=app_lp, text=f"Detalhes: {values[1]}", 
                                        compound=LEFT, anchor='w', font=('Ivy 15 bold'), 
                                        bg=app.colors['co0'], fg=app.colors['co1'], padx=10, pady=5)
                        # Manter referência à imagem
                        setattr(app_logo, '_image_ref', app_lp)
                        app_logo.pack(fill=X, expand=TRUE)
                    except:
                        # Fallback sem ícone
                        app_logo = Label(titulo_frame, text=f"Detalhes: {values[1]}", 
                                        anchor='w', font=('Ivy 15 bold'), 
                                        bg=app.colors['co0'], fg=app.colors['co1'], padx=10, pady=5)
                        app_logo.pack(fill=X, expand=TRUE)
                
                # Exibir detalhes no frame_detalhes
                if 'frame_detalhes' in app.frames:
                    exibir_detalhes_item(
                        frame_detalhes=app.frames['frame_detalhes'],
                        tipo=tipo,
                        item_id=item_id,
                        values=values,
                        colors=app.colors
                    )
                
            except Exception as e:
                logger.exception(f"Erro ao processar seleção: {e}")
        
        app.setup_table(
            on_select_callback=on_select_callback,
            on_keyboard_callback=None
        )
        
        # Configurar rodapé
        logger.debug("Configurando rodapé...")
        app.setup_footer()
        
        # Configurar e exibir dashboard automaticamente (otimizado)
        logger.debug("Configurando dashboard...")
        app.setup_dashboard(criar_agora=True)
        
        # Configurar menu contextual
        logger.debug("Configurando menu contextual...")
        
        def editar_callback():
            """Callback de edição via menu contextual"""
            try:
                if not app.selected_item:
                    messagebox.showwarning("Aviso", "Nenhum item selecionado")
                    return
                
                tipo = app.selected_item.get('tipo')
                item_id = app.selected_item.get('id')
                
                if tipo == 'Aluno':
                    from InterfaceEdicaoAluno import InterfaceEdicaoAluno
                    
                    # Destruir frames de detalhes/tabela
                    if 'frame_detalhes' in app.frames:
                        for widget in app.frames['frame_detalhes'].winfo_children():
                            widget.destroy()
                    
                    # Abrir interface de edição
                    InterfaceEdicaoAluno(app.janela, item_id)
                    logger.info(f"Aluno {item_id} editado")
                        
                elif tipo == 'Funcionário':
                    from InterfaceEdicaoFuncionario import InterfaceEdicaoFuncionario
                    
                    # Destruir frames de detalhes
                    if 'frame_detalhes' in app.frames:
                        for widget in app.frames['frame_detalhes'].winfo_children():
                            widget.destroy()
                    
                    # Abrir interface de edição
                    InterfaceEdicaoFuncionario(app.janela, item_id)
                    logger.info(f"Funcionário {item_id} editado")
                        
            except Exception as e:
                logger.exception(f"Erro ao editar item: {e}")
                messagebox.showerror("Erro", f"Erro ao editar: {e}")
        
        app.setup_context_menu(editar_callback=editar_callback)
        
        # Configurar fechamento da aplicação com backup
        def on_close_with_backup():
            """Handler de fechamento que inclui backup automático"""
            try:
                # Parar o sistema de backup automático e executar backup final
                if not TEST_MODE:
                    logger.info("Executando backup final antes de fechar...")
                    Seguranca.parar_backup_automatico(executar_backup_final=True)
            except Exception as e:
                logger.error(f"Erro ao executar backup final: {e}")
            finally:
                # Chamar o handler padrão de fechamento
                app.on_close()
        
        # Substituir o handler de fechamento padrão (apenas se janela existe)
        if app.janela:
            app.janela.protocol("WM_DELETE_WINDOW", on_close_with_backup)
        
        # Iniciar sistema de backup automático (se não estiver em modo teste)
        if not TEST_MODE:
            try:
                logger.debug("Iniciando sistema de backup automático...")
                Seguranca.iniciar_backup_automatico()
                logger.debug("Sistema de backup iniciado (14:05 e 17:00)")
            except Exception as e:
                logger.error(f"Erro ao iniciar backup automático: {e}")
        
        # Mensagem de sucesso (resumida)
        logger.info("Sistema inicializado com sucesso")
        
        # Iniciar mainloop
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
