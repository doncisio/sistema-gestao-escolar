import os
import shutil
from PIL import Image, ImageDraw

def cor_texto(texto, cor):
    """Aplica cor ao texto para console"""
    cores = {
        'verde': '\033[92m',
        'amarelo': '\033[93m',
        'vermelho': '\033[91m',
        'azul': '\033[94m',
        'reset': '\033[0m'
    }
    return f"{cores.get(cor, '')}{texto}{cores['reset']}"

def criar_pasta_se_nao_existir(pasta):
    """Cria uma pasta se ela não existir"""
    if not os.path.exists(pasta):
        try:
            os.makedirs(pasta, exist_ok=True)
            print(cor_texto(f"✓ Pasta '{pasta}' criada com sucesso", "verde"))
            return True
        except Exception as e:
            print(cor_texto(f"✗ Erro ao criar pasta '{pasta}': {e}", "vermelho"))
            return False
    else:
        print(f"✓ Pasta '{pasta}' já existe")
        return True

def criar_imagem_icone(caminho, nome, cor=(100, 100, 100)):
    """Cria uma imagem básica para um ícone"""
    try:
        diretorio = os.path.dirname(caminho)
        
        # Criar o diretório se não existir
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        
        # Criar uma imagem básica
        tamanho = (50, 50)
        img = Image.new('RGB', tamanho, (255, 255, 255))  # Fundo branco
        
        # Desenhar um círculo colorido
        draw = ImageDraw.Draw(img)
        draw.ellipse([(5, 5), (45, 45)], fill=cor)
        
        # Salvar a imagem
        img.save(caminho)
        print(cor_texto(f"✓ Imagem '{caminho}' criada com sucesso", "verde"))
        return True
    except Exception as e:
        print(cor_texto(f"✗ Erro ao criar imagem '{caminho}': {e}", "vermelho"))
        return False

def main():
    print("=" * 60)
    print(cor_texto("CORREÇÃO DE PROBLEMAS COM IMAGENS", "azul"))
    print("=" * 60)
    print("\nEste script irá criar ou corrigir as imagens que foram reportadas como faltantes.")
    
    # Verificar e criar a pasta 'icon'
    print("\n1. Verificando e criando pastas necessárias...")
    criar_pasta_se_nao_existir('icon')
    
    # Criar as imagens faltantes
    print("\n2. Criando imagens faltantes...")
    
    # Cores para diferentes tipos de ícones
    cores = {
        'learning': (65, 105, 225),    # Azul real
        'settings': (128, 128, 128),   # Cinza
        'history': (30, 144, 255),     # Azul dodger
    }
    
    # Lista de imagens para criar
    imagens_para_criar = [
        ('icon/learning.png', 'learning', cores['learning']),
        ('icon/settings.png', 'settings', cores['settings']),
        ('icon/history.png', 'history', cores['history']),
        ('arquivo.png', 'arquivo', (200, 200, 200))  # Arquivo genérico
    ]
    
    for caminho, nome, cor in imagens_para_criar:
        criar_imagem_icone(caminho, nome, cor)
    
    print("\n3. Verificando se tudo foi criado corretamente...")
    
    # Verificar se as imagens foram criadas
    sucesso = True
    for caminho, _, _ in imagens_para_criar:
        if os.path.exists(caminho):
            print(f"✓ Arquivo '{caminho}' existe")
        else:
            print(cor_texto(f"✗ Arquivo '{caminho}' ainda não existe!", "vermelho"))
            sucesso = False
    
    # Resumo final
    print("\n" + "=" * 60)
    if sucesso:
        print(cor_texto("✓ CORREÇÃO CONCLUÍDA COM SUCESSO!", "verde"))
        print("=" * 60)
        print("\nTodas as imagens problemáticas foram criadas com sucesso.")
        print("Agora você pode executar 'python verificar_imagens.py' novamente")
        print("para confirmar que os problemas foram resolvidos.")
    else:
        print(cor_texto("✗ CORREÇÃO CONCLUÍDA COM AVISOS!", "amarelo"))
        print("=" * 60)
        print("\nAlgumas imagens ainda não puderam ser criadas.")
        print("Tente criar manualmente as imagens faltantes.")
    
    input("\nPressione Enter para sair...")

if __name__ == "__main__":
    # Configurar cores no Windows se disponível
    if os.name == 'nt':
        os.system('color')
    
    main() 