"""
Script para baixar o ChromeDriver correto para sua versão do Chrome
"""

import os
import sys
import subprocess
import zipfile
import shutil
import requests
from pathlib import Path
from config_logs import get_logger

logger = get_logger(__name__)


def obter_versao_chrome():
    """
    Obtém a versão do Google Chrome instalada
    """
    try:
        # Windows
        if sys.platform == 'win32':
            import winreg
            
            # Tentar diferentes locais do registro
            paths = [
                r"SOFTWARE\Google\Chrome\BLBeacon",
                r"SOFTWARE\Wow6432Node\Google\Chrome\BLBeacon",
            ]
            
            for path in paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                    version, _ = winreg.QueryValueEx(key, "version")
                    winreg.CloseKey(key)
                    return version
                except:
                    continue
            
            # Tentar via comando
            result = subprocess.run(
                ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                version = result.stdout.split()[-1]
                return version
                
        return None
        
    except Exception as e:
        logger.exception("⚠ Erro ao obter versão do Chrome: %s", e)
        return None


def obter_versao_chromedriver_compativel(versao_chrome):
    """
    Obtém a versão do ChromeDriver compatível
    """
    try:
        # Pegar apenas versão major (ex: 131 de 131.0.6778.109)
        versao_major = versao_chrome.split('.')[0]
        
        logger.info("→ Chrome versão: %s (major: %s)", versao_chrome, versao_major)
        
        # URL da API do Chrome for Testing
        url = f"https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        
        logger.info("→ Buscando versão compatível do ChromeDriver...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Procurar versão compatível
        for version_info in reversed(data['versions']):
            if version_info['version'].startswith(versao_major + '.'):
                # Verificar se tem chromedriver para Windows
                if 'downloads' in version_info and 'chromedriver' in version_info['downloads']:
                    for download in version_info['downloads']['chromedriver']:
                        if download['platform'] == 'win32' or download['platform'] == 'win64':
                            return version_info['version'], download['url']
        
        return None, None
        
    except Exception as e:
        logger.exception("⚠ Erro ao buscar versão compatível: %s", e)
        return None, None


def baixar_chromedriver(url, destino):
    """
    Baixa e extrai o ChromeDriver
    """
    try:
        logger.info("→ Baixando ChromeDriver de: %s", url)
        
        # Baixar arquivo
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Salvar ZIP temporário
        zip_path = destino + ".zip"
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        # manter a saída de progresso no terminal para UX
                        print(f"  → Progresso: {percent:.1f}%", end='\r')
        
        logger.info("✓ Download concluído: %s", zip_path)
        
        # Extrair ZIP
        logger.info("→ Extraindo arquivo...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Procurar chromedriver.exe no ZIP
            for file in zip_ref.namelist():
                if file.endswith('chromedriver.exe'):
                    # Extrair para pasta temporária
                    zip_ref.extract(file, os.path.dirname(destino))
                    
                    # Mover para destino final
                    extracted_path = os.path.join(os.path.dirname(destino), file)
                    shutil.move(extracted_path, destino)
                    
                    # Limpar pasta temporária
                    temp_dir = os.path.dirname(extracted_path)
                    if temp_dir != os.path.dirname(destino):
                        try:
                            shutil.rmtree(temp_dir)
                        except:
                            pass
                    
                    break
        
        # Remover ZIP
        os.remove(zip_path)
        
        logger.info("✓ ChromeDriver extraído para: %s", destino)
        return True
        
    except Exception as e:
        logger.exception("✗ Erro ao baixar ChromeDriver: %s", e)
        return False


def main():
    """
    Função principal
    """
    logger.info("╔═══════════════════════════════════════════════════════╗")
    logger.info("║                                                        ║")
    logger.info("║        BAIXAR CHROMEDRIVER AUTOMATICAMENTE            ║")
    logger.info("║                                                        ║")
    logger.info("╚═══════════════════════════════════════════════════════╝")
    logger.info("")
    
    # Verificar se requests está instalado
    try:
        import requests
    except ImportError:
        logger.warning("✗ Módulo 'requests' não encontrado!")
        logger.info("→ Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    
    # Obter versão do Chrome
    logger.info("→ Detectando versão do Google Chrome...")
    versao_chrome = obter_versao_chrome()
    
    if not versao_chrome:
        logger.error("✗ Não foi possível detectar a versão do Chrome")
        logger.info("→ Certifique-se de que o Google Chrome está instalado")
        
        # Perguntar versão manualmente (instrução visível ao usuário)
        print("\n📝 Digite a versão do seu Chrome (ex: 131.0.6778.109):")
        logger.info("   Abra o Chrome e vá em: chrome://settings/help")
        versao_chrome = input("→ Versão: ").strip()
        
        if not versao_chrome:
            logger.info("✗ Versão inválida")
            return
    
    # Obter versão compatível do ChromeDriver
    versao_driver, url_download = obter_versao_chromedriver_compativel(versao_chrome)
    
    if not versao_driver:
        logger.error("✗ Não foi possível encontrar ChromeDriver compatível")
        logger.info("\n📝 ALTERNATIVA:")
        logger.info("   Baixe manualmente em: https://googlechromelabs.github.io/chrome-for-testing/")
        return
    
    logger.info("✓ ChromeDriver compatível encontrado: %s", versao_driver)
    
    # Definir destino
    script_dir = os.path.dirname(os.path.abspath(__file__))
    destino = os.path.join(script_dir, "chromedriver.exe")
    
    # Verificar se já existe
    if os.path.exists(destino):
        logger.warning("\n⚠ ChromeDriver já existe em: %s", destino)
        resposta = input("→ Deseja substituir? (s/n): ").strip().lower()
        
        if resposta != 's':
            logger.info("→ Operação cancelada")
            return
        
        os.remove(destino)
    
    # Baixar
    logger.info()
    sucesso = baixar_chromedriver(url_download, destino)
    
    if sucesso:
        logger.info("")
        logger.info("╔═══════════════════════════════════════════════════════╗")
        logger.info("║                                                        ║")
        logger.info("║              ✅ CHROMEDRIVER INSTALADO!               ║")
        logger.info("║                                                        ║")
        logger.info("╚═══════════════════════════════════════════════════════╝")
        logger.info("")
        logger.info("📁 Local: %s", destino)
        logger.info("")
        logger.info("✅ Agora você pode usar o sistema de automação normalmente!")
        logger.info("")
    else:
        logger.info("")
        logger.info("╔═══════════════════════════════════════════════════════╗")
        logger.info("║                                                        ║")
        logger.info("║              ✗ FALHA NO DOWNLOAD                      ║")
        logger.info("║                                                        ║")
        logger.info("╚═══════════════════════════════════════════════════════╝")
        logger.info("")
        logger.info("📝 SOLUÇÃO MANUAL:")
        logger.info("   1. Acesse: %s", url_download)
        logger.info("   2. Extraia o arquivo ZIP")
        logger.info("   3. Copie chromedriver.exe para: %s", destino)
        logger.info("")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n→ Operação cancelada pelo usuário")
    except Exception as e:
        logger.exception("\n\n✗ Erro inesperado: %s", e)
    
    input("\nPressione ENTER para sair...")