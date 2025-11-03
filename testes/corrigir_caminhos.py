import os
import re
import glob
import sys
import shutil
from pathlib import Path

def cor_texto(texto, cor):
    """Aplica cor ao texto para console Windows"""
    cores = {
        'verde': '\033[92m',
        'amarelo': '\033[93m',
        'vermelho': '\033[91m',
        'azul': '\033[94m',
        'reset': '\033[0m'
    }
    return f"{cores.get(cor, '')}{texto}{cores['reset']}"

def encontrar_referencias_imagens():
    """Encontra todas as referências a imagens no código Python"""
    referencias = set()
    
    print(cor_texto("\n[1/3] Analisando código fonte para encontrar referências a imagens...", "azul"))
    print("-" * 50)
    
    # Padrões para encontrar referências a imagens
    padroes = [
        r'Image\.open\([\'"](.+?)[\'"]\)',  # PIL: Image.open('arquivo.png')
        r'ImageTk\.PhotoImage\(.*?file=[\'"](.+?)[\'"]\)',  # PhotoImage com file=
        r'--icon=([^\s]+)'  # Referências a ícones
    ]
    
    # Obter todos os arquivos Python
    arquivos_py = glob.glob("*.py")
    
    for arquivo_py in arquivos_py:
        try:
            with open(arquivo_py, 'r', encoding='utf-8') as f:
                print(f"Analisando {arquivo_py}...")
                conteudo = f.read()
                
                # Aplicar todos os padrões
                for padrao in padroes:
                    matches = re.findall(padrao, conteudo)
                    for match in matches:
                        # Filtrar apenas caminhos relativos que parecem ser imagens
                        if (not os.path.isabs(match) and 
                            not match.startswith('%') and
                            ('.' in match or '/' in match or '\\' in match)):
                            referencias.add(match)
        except Exception as e:
            print(cor_texto(f"Erro ao analisar {arquivo_py}: {e}", "vermelho"))
    
    # Adicionar imagens conhecidas que podem não ser detectadas pela análise de código
    imagens_conhecidas = [
        'logopaco.png',
        'icon/learning.png',
        'icon/book.png',
        'icon/left.png',
        'icon/plus.png',
        'icon/video-conference.png',
        'icon/history.png',
        'icon/settings.png'
    ]
    
    referencias.update(imagens_conhecidas)
    
    return referencias

def encontrar_imagens_disponiveis():
    """Encontra todas as imagens disponíveis no projeto"""
    imagens = []
    
    print(cor_texto("\n[2/3] Procurando imagens disponíveis no projeto...", "azul"))
    print("-" * 50)
    
    # Extensões de imagem comuns
    extensoes = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico']
    
    # Procurar em todos os diretórios
    for root, dirs, files in os.walk('.'):
        for arquivo in files:
            if os.path.splitext(arquivo)[1].lower() in extensoes:
                caminho = os.path.join(root, arquivo)
                caminho = os.path.normpath(caminho)
                # Converter para caminho relativo se for absoluto
                if os.path.isabs(caminho):
                    caminho = os.path.relpath(caminho, '.')
                imagens.append(caminho)
    
    print(f"Encontradas {len(imagens)} imagens no projeto")
    return imagens

def verificar_e_corrigir_caminhos(referencias, imagens_disponiveis):
    """Verifica caminhos de imagens e sugere/corrige problemas"""
    print(cor_texto("\n[3/3] Verificando e corrigindo caminhos de imagens...", "azul"))
    print("-" * 50)
    
    # Normalizar caminhos para comparação
    referencias_norm = [os.path.normpath(ref) for ref in referencias]
    imagens_norm = [os.path.normpath(img) for img in imagens_disponiveis]
    
    # Dicionário para mapear nomes de arquivos para caminhos completos
    map_nome_caminho = {}
    for img in imagens_disponiveis:
        nome_arquivo = os.path.basename(img)
        if nome_arquivo not in map_nome_caminho:
            map_nome_caminho[nome_arquivo] = []
        map_nome_caminho[nome_arquivo].append(img)
    
    # Verificar cada referência
    for i, ref in enumerate(referencias_norm):
        ref_original = referencias[i]
        
        # Verificar se o arquivo existe diretamente
        if ref in imagens_norm or os.path.exists(ref):
            print(f"✓ {ref} - OK")
            continue
        
        # Verificar pelo nome do arquivo
        nome_arquivo = os.path.basename(ref)
        if nome_arquivo in map_nome_caminho:
            caminhos_possíveis = map_nome_caminho[nome_arquivo]
            
            print(cor_texto(f"! {ref} - Não encontrado, mas arquivo com mesmo nome existe em:", "amarelo"))
            
            for j, caminho in enumerate(caminhos_possíveis):
                print(f"  {j+1}. {caminho}")
            
            # Perguntar qual caminho usar ou copiar
            print(f"\nOpções para {ref}:")
            print("  1. Copiar imagem para o caminho esperado")
            print("  2. Ignorar este arquivo")
            
            escolha = input("Escolha (1-2): ").strip()
            
            if escolha == '1':
                # Garantir que o diretório de destino exista
                dir_destino = os.path.dirname(ref)
                if dir_destino and not os.path.exists(dir_destino):
                    os.makedirs(dir_destino, exist_ok=True)
                    print(f"✓ Diretório criado: {dir_destino}")
                
                if len(caminhos_possíveis) == 1:
                    # Se só há uma opção, usar ela
                    origem = caminhos_possíveis[0]
                    shutil.copy2(origem, ref)
                    print(cor_texto(f"✓ Copiado {origem} -> {ref}", "verde"))
                else:
                    # Se há múltiplas opções, perguntar qual usar
                    print("\nQual arquivo copiar?")
                    for j, caminho in enumerate(caminhos_possíveis):
                        print(f"  {j+1}. {caminho}")
                    
                    sub_escolha = input(f"Escolha (1-{len(caminhos_possíveis)}): ").strip()
                    try:
                        idx = int(sub_escolha) - 1
                        if 0 <= idx < len(caminhos_possíveis):
                            origem = caminhos_possíveis[idx]
                            shutil.copy2(origem, ref)
                            print(cor_texto(f"✓ Copiado {origem} -> {ref}", "verde"))
                        else:
                            print(cor_texto("Escolha inválida, ignorando.", "vermelho"))
                    except ValueError:
                        print(cor_texto("Entrada inválida, ignorando.", "vermelho"))
            else:
                print("Ignorando este arquivo.")
        else:
            print(cor_texto(f"✗ {ref} - Não encontrado em nenhum lugar do projeto", "vermelho"))

def main():
    # Configurar cores no Windows
    if sys.platform.startswith('win'):
        os.system('color')
    
    print("=" * 50)
    print(cor_texto("CORRETOR DE CAMINHOS DE IMAGENS", "azul"))
    print("=" * 50)
    
    # Encontrar referências a imagens no código
    referencias = encontrar_referencias_imagens()
    
    # Encontrar todas as imagens disponíveis no projeto
    imagens_disponiveis = encontrar_imagens_disponiveis()
    
    # Verificar e corrigir caminhos
    verificar_e_corrigir_caminhos(referencias, imagens_disponiveis)
    
    print("\n" + "=" * 50)
    print(cor_texto("✓ PROCESSO DE CORREÇÃO CONCLUÍDO!", "verde"))
    print("=" * 50)
    print("Agora você pode executar a verificação de imagens novamente\npara confirmar se todos os problemas foram resolvidos.")

if __name__ == "__main__":
    main() 