"""
Script para baixar as imagens necessárias para gerar certificados offline
Execute este script uma vez para configurar o ambiente
"""

import os
import requests
from config_logs import get_logger

logger = get_logger(__name__)

# URLs das imagens necessárias
IMAGENS = {
    "fcertificado3.png": "https://geduc-data.s3.us-east-1.amazonaws.com/logo/fcertificado3.png",
    "logo_prefeitura.png": "https://geduc-data.s3.us-east-1.amazonaws.com/logo/2107506.png",
    "brasao_maranhao.png": "https://geduc-data.s3.us-east-1.amazonaws.com/logo/brasao%20maranhao.png"
}

def baixar_imagens():
    """Baixa todas as imagens necessárias para o diretório 'imagens'"""
    # Criar diretório se não existir
    pasta_imagens = "imagens"
    os.makedirs(pasta_imagens, exist_ok=True)
    
    print("Baixando imagens para certificados...")
    print("=" * 50)
    
    for nome_arquivo, url in IMAGENS.items():
        caminho_destino = os.path.join(pasta_imagens, nome_arquivo)
        
        # Verificar se já existe
        if os.path.exists(caminho_destino):
            print(f"✓ {nome_arquivo} já existe")
            continue
        
        try:
            print(f"Baixando {nome_arquivo}...", end=" ")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                with open(caminho_destino, 'wb') as f:
                    f.write(response.content)
                print("✓ OK")
                logger.info(f"Imagem baixada: {nome_arquivo}")
            else:
                print(f"✗ ERRO (Status: {response.status_code})")
                logger.error(f"Erro ao baixar {nome_arquivo}: Status {response.status_code}")
                
        except Exception as e:
            print(f"✗ ERRO: {e}")
            logger.error(f"Erro ao baixar {nome_arquivo}: {e}")
    
    print("=" * 50)
    print("Download concluído!")
    
    # Verificar quais imagens foram baixadas com sucesso
    imagens_ok = []
    imagens_faltando = []
    
    for nome_arquivo in IMAGENS.keys():
        caminho = os.path.join(pasta_imagens, nome_arquivo)
        if os.path.exists(caminho):
            imagens_ok.append(nome_arquivo)
        else:
            imagens_faltando.append(nome_arquivo)
    
    print(f"\nImagens disponíveis: {len(imagens_ok)}/{len(IMAGENS)}")
    
    if imagens_faltando:
        print("\nImagens faltando:")
        for img in imagens_faltando:
            print(f"  - {img}")
        return False
    
    return True


if __name__ == "__main__":
    sucesso = baixar_imagens()
    
    if sucesso:
        print("\n✓ Todas as imagens foram baixadas com sucesso!")
        print("Agora você pode gerar certificados offline.")
    else:
        print("\n✗ Algumas imagens não foram baixadas.")
        print("Verifique sua conexão com a internet e tente novamente.")
