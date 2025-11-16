"""
Módulo utilitário para lidar com o carregamento seguro de imagens
e identificar problemas relacionados a imagens em toda a aplicação.
"""
import os
from tkinter import *
from PIL import Image, ImageTk
import weakref
from config_logs import get_logger

logger = get_logger(__name__)

# Dicionário global para armazenar referências a todas as imagens carregadas
# Isso evita que o coletor de lixo do Python as destrua prematuramente
_imagens_cache = {}

def limpar_cache_imagens():
    """Limpa o cache de imagens para liberar memória"""
    global _imagens_cache
    _imagens_cache.clear()

def carregar_imagem_segura(caminho, tamanho=None, usar_cache=True, chave=None):
    """
    Carrega uma imagem de forma segura, tratando possíveis erros.
    
    Args:
        caminho (str): O caminho para o arquivo de imagem
        tamanho (tuple): Uma tupla com largura e altura para redimensionar
        usar_cache (bool): Se deve armazenar a imagem no cache para evitar destruição pelo coletor de lixo
        chave (str): Chave personalizada para a imagem no cache. Se não fornecida, usa-se o caminho
        
    Returns:
        ImageTk.PhotoImage ou None: A imagem carregada ou None em caso de erro
    """
    # Gera uma chave única para a imagem no cache
    if chave is None:
        chave = f"{caminho}_{tamanho}"
    
    # Verifica se a imagem já está no cache
    if usar_cache and chave in _imagens_cache:
        return _imagens_cache[chave]
    
    try:
        if os.path.exists(caminho):
            img = Image.open(caminho)
            if tamanho:
                img = img.resize(tamanho)
            photo = ImageTk.PhotoImage(img)

            # Armazena no cache se solicitado
            if usar_cache:
                _imagens_cache[chave] = photo

            return photo
        else:
            logger.warning(f"Arquivo não encontrado: {caminho}")
            return None
    except Exception as e:
        logger.exception("Erro ao carregar imagem '%s': %s", caminho, str(e))
        return None

class GerenciadorImagens:
    """Classe para gerenciar imagens em uma aplicação Tkinter"""
    
    def __init__(self):
        # Dicionário para armazenar imagens por categoria
        self.imagens = {}
        # Dicionário para armazenar referências fracas aos widgets que usam as imagens
        self.referencias_widgets = {}
        # Imagem de backup padrão
        self._criar_imagem_backup()
    
    def _criar_imagem_backup(self):
        """Cria uma imagem de backup padrão para usar quando uma imagem não for encontrada"""
        try:
            img_vazia = Image.new('RGB', (45, 45), color=(3, 140, 252))  # Cor azul
            self.imagem_backup = ImageTk.PhotoImage(img_vazia)
        except Exception as e:
            logger.exception(f"Erro ao criar imagem de backup: {e}")
            self.imagem_backup = None
    
    def carregar_imagem(self, categoria, caminho, tamanho=None, chave=None):
        """
        Carrega uma imagem e armazena em uma categoria específica
        
        Args:
            categoria (str): Categoria para agrupar imagens (ex: 'icones', 'logos')
            caminho (str): Caminho para o arquivo de imagem
            tamanho (tuple): Tamanho para redimensionar a imagem
            chave (str): Identificador único para a imagem
            
        Returns:
            ImageTk.PhotoImage ou None: A imagem carregada ou None em caso de erro
        """
        # Inicializa a categoria se não existir
        if categoria not in self.imagens:
            self.imagens[categoria] = {}
            
        # Usa o nome do arquivo como chave se não for fornecida
        if chave is None:
            chave = os.path.basename(caminho)
        
        try:
            # Verifica se o arquivo existe
            if not os.path.exists(caminho):
                logger.warning(f"Arquivo não encontrado: {caminho}")
                return self.imagem_backup
            
            # Carrega e processa a imagem
            img = Image.open(caminho)
            if tamanho:
                img = img.resize(tamanho)
            photo = ImageTk.PhotoImage(img)
            
            # Armazena a imagem na categoria
            self.imagens[categoria][chave] = photo
            
            return photo
        except Exception as e:
            logger.exception(f"Erro ao carregar imagem '{caminho}': {str(e)}")
            return self.imagem_backup
    
    def obter_imagem(self, categoria, chave, widget=None):
        """
        Obtém uma imagem previamente carregada e opcionalmente registra o widget que a usa
        
        Args:
            categoria (str): Categoria da imagem
            chave (str): Identificador da imagem
            widget (Widget): Widget que está usando a imagem
            
        Returns:
            ImageTk.PhotoImage: A imagem solicitada ou a imagem de backup
        """
        try:
            # Verificar se a categoria e a chave existem
            if categoria not in self.imagens or chave not in self.imagens.get(categoria, {}):
                logger.warning(f"Imagem não encontrada: categoria='{categoria}', chave='{chave}'")
                # Tentar carregar a imagem novamente
                if categoria == 'interface_editar' and chave == 'header_logo':
                    # Caminho específico para o ícone de edição
                    self.carregar_imagem(categoria, 'icon/learning.png', tamanho=(45, 45), chave=chave)
                
                # Se ainda não existir após a tentativa de carregamento, retorna a imagem de backup
                if categoria not in self.imagens or chave not in self.imagens.get(categoria, {}):
                    return self.imagem_backup
            
            imagem = self.imagens[categoria][chave]
            
            # Registra o widget que está usando a imagem
            if widget:
                chave_ref = f"{categoria}_{chave}"
                if chave_ref not in self.referencias_widgets:
                    self.referencias_widgets[chave_ref] = []
                self.referencias_widgets[chave_ref].append(weakref.ref(widget))
                
                # Remove referências inválidas
                self.referencias_widgets[chave_ref] = [
                    ref for ref in self.referencias_widgets[chave_ref]
                    if ref() is not None
                ]
            
            return imagem
        except Exception as e:
            logger.exception(f"Erro ao obter imagem: categoria='{categoria}', chave='{chave}', erro={str(e)}")
            return self.imagem_backup
    
    def verificar_imagem_valida(self, categoria, chave):
        """
        Verifica se uma imagem ainda é válida
        
        Args:
            categoria (str): Categoria da imagem
            chave (str): Identificador da imagem
            
        Returns:
            bool: True se a imagem existe e é válida, False caso contrário
        """
        try:
            imagem = self.imagens[categoria][chave]
            # Tenta acessar a imagem para verificar se ainda é válida
            _ = imagem.width()
            return True
        except:
            return False
    
    def limpar_categoria(self, categoria):
        """Limpa todas as imagens de uma categoria"""
        if categoria in self.imagens:
            self.imagens[categoria].clear()
            
            # Remove referências de widgets para esta categoria
            chaves_para_remover = [
                chave for chave in self.referencias_widgets
                if chave.startswith(f"{categoria}_")
            ]
            for chave in chaves_para_remover:
                del self.referencias_widgets[chave]
    
    def limpar_todas(self):
        """Limpa todas as imagens de todas as categorias"""
        self.imagens.clear()
        self.referencias_widgets.clear()
        # Recria a imagem de backup
        self._criar_imagem_backup()

# Instância global do gerenciador de imagens
gerenciador_imagens = GerenciadorImagens()

def verificar_imagens_necessarias():
    """
    Verifica se todas as imagens necessárias para o funcionamento do sistema estão presentes.
    
    Returns:
        dict: Um dicionário com o caminho da imagem como chave e um booleano indicando se ela existe como valor
    """
    # Lista de imagens usadas em todo o sistema
    imagens_sistema = [
        'icon/learning.png',
        'icon/video-conference.png',
        'icon/diskette.png',
        'icon/plus.png',
        'icon/trash.png',
        'icon/update.png',
        'icon/left.png',
        'icon/casa.png',
        'icon/notebook.png',
        'icon/book.png',
        'icon/settings.png',
        'icon/history.png',
        'logopaco.png'
    ]
    
    resultado = {}
    for imagem in imagens_sistema:
        resultado[imagem] = os.path.exists(imagem)
    
    return resultado

def exibir_status_imagens():
    """
    Exibe o status das imagens do sistema e sugere correções.
    """
    status = verificar_imagens_necessarias()
    
    logger.info("\n===== STATUS DAS IMAGENS DO SISTEMA =====")
    todas_ok = True
    
    for caminho, existe in status.items():
        if existe:
            logger.info(f"✓ {caminho}")
        else:
            todas_ok = False
            logger.warning(f"✗ {caminho} (NÃO ENCONTRADA)")
    
    if todas_ok:
        logger.info("\nTodas as imagens necessárias foram encontradas!")
    else:
        logger.warning("\nALGUMAS IMAGENS ESTÃO FALTANDO!")
        logger.warning("Isso pode causar erros como 'pyimage doesn't exist'.")
        logger.info("\nSoluções possíveis:")
        logger.info("1. Certifique-se de que a pasta 'icon' existe na raiz do projeto")
        logger.info("2. Baixe as imagens faltantes")
        logger.info("3. Modifique o código para usar imagens alternativas")
    
    return todas_ok

if __name__ == "__main__":
    # Se executado diretamente, verifica as imagens
    exibir_status_imagens() 