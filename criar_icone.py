"""
Script para converter PNG em ícone .ico para o executável.
"""
from PIL import Image
import sys

def criar_icone(caminho_png: str, caminho_ico: str):
    """Converte PNG para ICO com múltiplos tamanhos."""
    try:
        # Abrir imagem PNG
        img = Image.open(caminho_png)
        
        # Converter para RGBA se necessário
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Criar ícone com múltiplos tamanhos (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        # Salvar como .ico
        img.save(caminho_ico, format='ICO', sizes=icon_sizes)
        print(f"✅ Ícone criado com sucesso: {caminho_ico}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar ícone: {e}")
        return False

if __name__ == "__main__":
    caminho_png = r"C:\gestao\imagens\executo.png"
    caminho_ico = r"C:\gestao\icon.ico"
    
    print(f"Convertendo {caminho_png} para {caminho_ico}...")
    sucesso = criar_icone(caminho_png, caminho_ico)
    
    sys.exit(0 if sucesso else 1)
