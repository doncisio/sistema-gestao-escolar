import os
import sys
import time
import subprocess
import platform
from config_logs import get_logger

logger = get_logger(__name__)

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

def executar_comando(comando, descricao):
    """Executa um comando e exibe feedback"""
    logger.info(cor_texto(f"\n=== {descricao} ===", "azul"))
    logger.info(cor_texto(f"Executando: {comando}", "amarelo"))
    
    # Em Windows, usamos shell=True para comandos como 'cls'
    shell_param = True if platform.system() == "Windows" else False
    
    try:
        resultado = subprocess.run(comando, shell=shell_param, check=True)
        return resultado.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(cor_texto(f"Erro ao executar comando: {e}", "vermelho"))
        return False
    except Exception as e:
        logger.exception(cor_texto(f"Erro inesperado: {e}", "vermelho"))
        return False

def limpar_tela():
    """Limpa a tela do console"""
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def mostrar_menu():
    """Exibe o menu principal"""
    limpar_tela()
    logger.info("=" * 60)
    logger.info(cor_texto("SISTEMA DE CRIAÇÃO DE EXECUTÁVEL", "azul"))
    logger.info("=" * 60)
    logger.info("\nEscolha uma opção:")
    logger.info("1. Verificar imagens referenciadas")
    logger.info("2. Corrigir caminhos de imagens")
    logger.info("3. Compilar executável")
    logger.info("4. Processo completo (verificar, corrigir e compilar)")
    logger.info("5. Sair")
    
    escolha = input("\nSua escolha (1-5): ").strip()
    return escolha

def main():
    # Configurar cores no Windows
    if sys.platform.startswith('win'):
        os.system('color')
    
    while True:
        escolha = mostrar_menu()
        
        if escolha == '1':
            # Verificar imagens
            executar_comando("python verificar_imagens.py", "Verificando imagens")
            input("\nPressione Enter para voltar ao menu...")
            
        elif escolha == '2':
            # Corrigir caminhos
            executar_comando("python corrigir_caminhos.py", "Corrigindo caminhos de imagens")
            input("\nPressione Enter para voltar ao menu...")
            
        elif escolha == '3':
            # Compilar executável
            executar_comando("python setup.py", "Compilando executável")
            
            if os.path.exists("dist/Sistema_Escolar.exe"):
                tamanho = os.path.getsize("dist/Sistema_Escolar.exe") / (1024 * 1024)
                logger.info(cor_texto(f"\nExecutável criado com sucesso! Tamanho: {tamanho:.2f} MB", "verde"))
            else:
                logger.error(cor_texto("\nErro: Executável não foi criado.", "vermelho"))
            
            input("\nPressione Enter para voltar ao menu...")
            
        elif escolha == '4':
            # Processo completo
            logger.info(cor_texto("\n=== INICIANDO PROCESSO COMPLETO ===", "azul"))
            
            # Verificar imagens
            logger.info(cor_texto("\nPasso 1/3: Verificação de imagens", "azul"))
            if not executar_comando("python verificar_imagens.py", "Verificando imagens"):
                logger.warning(cor_texto("\nDetectados problemas com imagens!", "amarelo"))
                
                # Perguntar se deseja corrigir
                if input("\nDeseja tentar corrigir os problemas? (s/n): ").lower() == 's':
                    executar_comando("python corrigir_caminhos.py", "Corrigindo caminhos de imagens")
                else:
                    logger.info("Processo interrompido pelo usuário.")
                    input("\nPressione Enter para voltar ao menu...")
                    continue
            
            # Verificar novamente após correções
            logger.info(cor_texto("\nPasso 2/3: Verificando novamente após correções", "azul"))
            verificacao_ok = executar_comando("python verificar_imagens.py", "Verificando imagens")
            
            if not verificacao_ok:
                continuar = input("\nAinda há problemas com imagens. Deseja continuar mesmo assim? (s/n): ").lower()
                if continuar != 's':
                    logger.info("Processo interrompido pelo usuário.")
                    input("\nPressione Enter para voltar ao menu...")
                    continue
            
            # Compilar executável
            logger.info(cor_texto("\nPasso 3/3: Compilação do executável", "azul"))
            executar_comando("python setup.py", "Compilando executável")
            
            if os.path.exists("dist/Sistema_Escolar.exe"):
                tamanho = os.path.getsize("dist/Sistema_Escolar.exe") / (1024 * 1024)
                logger.info(cor_texto(f"\nExecutável criado com sucesso! Tamanho: {tamanho:.2f} MB", "verde"))
            else:
                logger.error(cor_texto("\nErro: Executável não foi criado.", "vermelho"))
            
            input("\nPressione Enter para voltar ao menu...")
            
        elif escolha == '5':
            # Sair
            logger.info(cor_texto("\nSaindo do sistema...", "amarelo"))
            break
            
        else:
            logger.warning(cor_texto("\nOpção inválida! Tente novamente.", "vermelho"))
            time.sleep(1.5)

if __name__ == "__main__":
    main() 