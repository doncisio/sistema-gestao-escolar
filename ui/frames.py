"""
Módulo responsável pela criação e gerenciamento de frames da interface gráfica.

Este módulo contém funções para criar os principais frames da aplicação:
- Frame do logo/cabeçalho
- Frame de pesquisa
- Frames principais (dados, detalhes, tabela)
- Frame do rodapé

Extraído do main.py como parte da refatoração do Sprint 2.
"""

from tkinter import Frame, Label, Entry, Button, NSEW, EW, X, BOTH, W, LEFT, RIGHT, SOLID, RAISED, RIDGE
from tkinter import ttk
from PIL import Image, ImageTk
from config_logs import get_logger

logger = get_logger(__name__)


def criar_frames(janela, co0, co1):
    """
    Cria os frames principais da aplicação.
    
    Args:
        janela: Janela Tk principal
        co0: Cor de fundo primária
        co1: Cor de fundo secundária
        
    Returns:
        dict: Dicionário com referências aos frames criados
            - frame_logo: Frame do cabeçalho/logo
            - frame_dados: Frame para barra de pesquisa e dados
            - frame_detalhes: Frame para exibir detalhes de itens selecionados
            - frame_tabela: Frame para a tabela principal
    """
    # Criar os frames
    frame_logo = Frame(janela, height=70, bg=co0)
    frame_logo.grid(row=0, column=0, pady=0, padx=0, sticky=NSEW)
    frame_logo.grid_propagate(False)  # Impede que o frame mude de tamanho com base no conteúdo
    frame_logo.grid_columnconfigure(0, weight=1)  # Permite que o conteúdo do frame se expanda horizontalmente

    ttk.Separator(janela, orient='horizontal').grid(row=1, columnspan=1, sticky=EW)

    frame_dados = Frame(janela, height=65, bg=co1)
    frame_dados.grid(row=2, column=0, pady=0, padx=0, sticky=NSEW)

    ttk.Separator(janela, orient='horizontal').grid(row=3, columnspan=1, sticky=EW)

    frame_detalhes = Frame(janela, bg=co1)
    frame_detalhes.grid(row=4, column=0, pady=0, padx=10, sticky=NSEW)
    
    # Configurar frame_detalhes para expandir
    frame_detalhes.grid_columnconfigure(0, weight=1)
    frame_detalhes.grid_rowconfigure(0, weight=1)

    frame_tabela = Frame(janela, bg=co1)
    frame_tabela.grid(row=6, column=0, pady=0, padx=10, sticky=NSEW)
    
    # Configurar frame_tabela para expandir
    frame_tabela.grid_columnconfigure(0, weight=1)
    
    # Separador 4 (entre a tabela e o rodapé)
    ttk.Separator(janela, orient='horizontal').grid(row=7, column=0, sticky=EW)
    
    logger.debug("Frames principais criados com sucesso")
    
    return {
        'frame_logo': frame_logo,
        'frame_dados': frame_dados,
        'frame_detalhes': frame_detalhes,
        'frame_tabela': frame_tabela
    }


def criar_logo(frame_logo, nome_escola, co0, co1, co7):
    """
    Cria o cabeçalho/logo da aplicação.
    
    Args:
        frame_logo: Frame onde o logo será inserido
        nome_escola: Nome da escola para exibir
        co0: Cor de fundo
        co1: Cor do texto do nome da escola
        co7: Cor alternativa
        
    Returns:
        ImageTk.PhotoImage: Referência à imagem do logo (para manter na memória)
    """
    # Limpa o frame do logo antes de adicionar novos widgets
    for widget in frame_logo.winfo_children():
        widget.destroy()
        
    # Frame para o cabeçalho/logo
    logo_frame = Frame(frame_logo, bg=co0)
    logo_frame.pack(fill=BOTH, expand=True, padx=0, pady=0)
    
    # Configura para expandir
    logo_frame.grid_columnconfigure(0, weight=1)  # Logo (menor peso)
    logo_frame.grid_columnconfigure(1, weight=5)  # Título (maior peso)
    
    # Logo
    app_logo = None
    try:
        # Tenta carregar a imagem do logo
        app_img = Image.open('logopaco.png')
        app_img = app_img.resize((200, 50))
        app_logo = ImageTk.PhotoImage(app_img)
        
        # Ícone da escola
        app_logo_label = Label(logo_frame, image=app_logo, text=" ", bg=co0, fg=co7)
        setattr(app_logo_label, 'image', app_logo)  # Manter referência (silencia Pylance)
        app_logo_label.grid(row=0, column=0, sticky=W, padx=10)
        logger.debug("Logo principal carregado: logopaco.png")
    except FileNotFoundError:
        try:
            # Tenta carregar outro logo
            app_img = Image.open('icon/book.png')
            app_img = app_img.resize((45, 45))
            app_logo = ImageTk.PhotoImage(app_img)
            
            # Ícone da escola
            app_logo_label = Label(logo_frame, image=app_logo, text=" ", bg=co0, fg=co7)
            setattr(app_logo_label, 'image', app_logo)  # Manter referência (silencia Pylance)
            app_logo_label.grid(row=0, column=0, sticky=W, padx=10)
            logger.debug("Logo alternativo carregado: icon/book.png")
        except Exception as e:
            # Fallback quando a imagem não é encontrada
            logger.warning(f"Nenhuma imagem de logo encontrada, usando texto: {e}")
            app_logo_label = Label(logo_frame, text="LOGO", font=("Ivy 15 bold"), bg=co0, fg=co7)
            app_logo_label.grid(row=0, column=0, sticky=W, padx=10)

    # Título da escola
    escola_label = Label(logo_frame, text=str(nome_escola).upper(), font=("Ivy 15 bold"), bg=co0, fg=co1)
    escola_label.grid(row=0, column=1, sticky=W, padx=10)
    
    logger.debug(f"Logo criado para escola: {nome_escola}")
    return app_logo


def criar_pesquisa(frame_dados, pesquisar_callback, co0, co1, co4):
    """
    Cria a barra de pesquisa.
    
    Args:
        frame_dados: Frame onde a barra de pesquisa será inserida
        pesquisar_callback: Função callback para executar a pesquisa
        co0: Cor de fundo do campo de entrada
        co1: Cor de fundo do frame
        co4: Cor de fundo do botão
        
    Returns:
        Entry: Widget de entrada de texto para pesquisa
    """
    # Frame para a barra de pesquisa
    pesquisa_frame = Frame(frame_dados, bg=co1)
    pesquisa_frame.pack(fill=X, expand=True, padx=10, pady=5)
    
    # Configura pesquisa_frame para expandir horizontalmente
    pesquisa_frame.grid_columnconfigure(0, weight=3)  # Entrada de pesquisa
    pesquisa_frame.grid_columnconfigure(1, weight=1)  # Botão de pesquisa
    
    # Entrada para pesquisa
    e_nome_pesquisa = Entry(pesquisa_frame, width=45, justify='left', relief=SOLID, bg=co0)
    e_nome_pesquisa.grid(row=0, column=0, padx=5, pady=5, sticky=EW)
    
    # Vincula o evento de pressionar Enter à função de pesquisa
    e_nome_pesquisa.bind("<Return>", pesquisar_callback)

    # Botão para pesquisar
    botao_pesquisar = Button(pesquisa_frame, command=pesquisar_callback, text="Pesquisar", 
                            font=('Ivy 10 bold'), relief=RAISED, overrelief=RIDGE, bg=co4, fg=co0)
    botao_pesquisar.grid(row=0, column=1, padx=5, pady=5, sticky=EW)
    
    logger.debug("Barra de pesquisa criada")
    return e_nome_pesquisa


def criar_rodape(janela, co0, co1, co2):
    """
    Cria o rodapé na parte inferior da janela.
    
    Args:
        janela: Janela Tk principal
        co0: Cor do texto
        co1: Cor de fundo
        co2: Cor do status de backup
        
    Returns:
        tuple: (label_rodape, status_label) - Labels do rodapé e status
    """
    # Cria um frame para o rodapé
    frame_rodape = Frame(janela, bg=co1)
    frame_rodape.grid(row=8, column=0, pady=5, sticky=EW)
    
    # Cria o novo rodapé
    label_rodape = Label(frame_rodape, text="Criado por Tarcisio Sousa de Almeida, Técnico em Administração Escolar", 
                         font=('Ivy 10'), bg=co1, fg=co0)
    label_rodape.pack(side=LEFT, padx=10)
    
    # Indicador de backup automático
    backup_status = Label(frame_rodape, text="🔄 Backup automático: ATIVO (14:05 e 17:00 + ao fechar)", 
                         font=('Ivy 9 italic'), bg=co1, fg=co2)
    backup_status.pack(side=LEFT, padx=20)
    
    # Adiciona status_label para mensagens
    status_label = Label(frame_rodape, text="", font=('Ivy 10'), bg=co1, fg=co0)
    status_label.pack(side=RIGHT, padx=10)
    
    logger.debug("Rodapé criado")
    return label_rodape, status_label


def destruir_frames(frame_detalhes, frame_tabela, frame_dados, frame_logo, criar_rodape_callback):
    """
    Destrói o conteúdo de todos os frames principais.
    
    Args:
        frame_detalhes: Frame de detalhes
        frame_tabela: Frame da tabela
        frame_dados: Frame de dados
        frame_logo: Frame do logo
        criar_rodape_callback: Callback para recriar o rodapé
    """
    for widget in frame_detalhes.winfo_children():
        widget.destroy()
    for widget in frame_tabela.winfo_children():
        widget.destroy()
    for widget in frame_dados.winfo_children():
        widget.destroy()
    for widget in frame_logo.winfo_children():
        widget.destroy()
        
    # Recria o rodapé para garantir que ele seja sempre exibido
    if criar_rodape_callback:
        criar_rodape_callback()
    
    logger.debug("Frames destruídos e rodapé recriado")
