import os
import sys
import re
import glob
import shutil
from PyInstaller.__main__ import run
import subprocess

# Diretório do projeto
diretorio_base = os.path.abspath(os.path.dirname(__file__))

# Diretórios personalizados para saída
diretorio_dist = os.path.join("D:\\", "dist")
diretorio_build = os.path.join("D:\\", "build")

# Criar os diretórios de saída se não existirem
os.makedirs(diretorio_dist, exist_ok=True)
os.makedirs(diretorio_build, exist_ok=True)

# Lista para armazenar todos os recursos
recursos = []

print("=" * 60)
print("PREPARANDO A COMPILAÇÃO DO SISTEMA DE GERENCIAMENTO ESCOLAR")
print("=" * 60)
print(f"Diretório de saída (dist): {diretorio_dist}")
print(f"Diretório de trabalho (build): {diretorio_build}")

# Função para criar diretórios e imagens padrão que podem estar faltando
def criar_recursos_padrao():
    """Cria diretórios e arquivos básicos necessários para a compilação"""
    try:
        # Verificar e criar diretório 'icon'
        if not os.path.exists('icon'):
            os.makedirs('icon', exist_ok=True)
            print(f"✓ Diretório 'icon' criado")
        
        # Verificar e criar diretório 'imagens'
        if not os.path.exists('imagens'):
            os.makedirs('imagens', exist_ok=True)
            print(f"✓ Diretório 'imagens' criado")
        
        # Lista de ícones básicos a verificar/criar
        icones_basicos = [
            'icon/learning.png',
            'icon/book.png',
            'icon/left.png',
            'icon/plus.png',
            'icon/video-conference.png',
            'icon/history.png',
            'icon/settings.png'
        ]
        
        # Se o ícone não existir, criar uma imagem básica
        from PIL import Image, ImageDraw
        
        # Cores para diferentes tipos de ícones
        cores = {
            'learning': (65, 105, 225),    # Azul real
            'book': (46, 139, 87),         # Verde mar
            'left': (255, 165, 0),         # Laranja
            'plus': (50, 205, 50),         # Verde lima
            'video-conference': (218, 112, 214),  # Orquídea
            'history': (30, 144, 255),     # Azul dodger
            'settings': (128, 128, 128)    # Cinza
        }
        
        for icone in icones_basicos:
            if not os.path.exists(icone):
                # Extrair o nome do ícone
                nome_base = os.path.splitext(os.path.basename(icone))[0]
                
                # Criar uma imagem básica
                tamanho = (50, 50)
                img = Image.new('RGB', tamanho, (255, 255, 255))  # Fundo branco
                
                # Escolher a cor com base no nome do ícone
                cor = cores.get(nome_base, (100, 100, 100))  # Cinza como cor padrão
                
                # Desenhar um círculo colorido
                draw = ImageDraw.Draw(img)
                draw.ellipse([(5, 5), (45, 45)], fill=cor)
                
                # Salvar a imagem
                img.save(icone)
                print(f"✓ Ícone '{icone}' criado")
        
        # Verificar se o arquivo logopaco.png existe
        if not os.path.exists('logopaco.png'):
            # Criar uma imagem simples como logotipo
            tamanho = (200, 50)
            img = Image.new('RGB', tamanho, (255, 255, 255))  # Fundo branco
            draw = ImageDraw.Draw(img)
            draw.rectangle([(0, 0), (200, 50)], outline=(0, 0, 0))
            # Não podemos adicionar texto facilmente sem fonte, então deixamos um retângulo
            img.save('logopaco.png')
            print(f"✓ Arquivo 'logopaco.png' criado")
        
        return True
    except Exception as e:
        print(f"Erro ao criar recursos padrão: {e}")
        return False

# Função para analisar o código Python e encontrar referências a arquivos
def encontrar_referencias_arquivos(diretorio_base):
    referencias = set()
    
    print("\nProcurando referências a arquivos no código...")
    
    # Padrões para encontrar referências a arquivos em código Python
    padroes = [
        r'Image\.open\([\'"](.+?)[\'"]\)',  # Padrão para PIL: Image.open('arquivo.png')
        r'ImageTk\.PhotoImage\(.*?file=[\'"](.+?)[\'"]\)',  # PhotoImage com file=
        r'app_img = Image\.open\([\'"](.+?)[\'"]\)',  # Específico para main.py
        r'open\([\'"](.+?)[\'"]\)',  # open('arquivo.txt')
        r'--icon=([^\s\'\"]+)',  # Referências a ícones
        r'os\.path\.join\([^\)]*?[\'"](.+?)[\'"]\)'  # os.path.join com caminhos
    ]
    
    # Encontrar todos os arquivos Python
    arquivos_py = glob.glob(os.path.join(diretorio_base, "*.py"))
    
    for arquivo_py in arquivos_py:
        try:
            with open(arquivo_py, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
                # Aplicar todos os padrões
                for padrao in padroes:
                    matches = re.findall(padrao, conteudo)
                    for match in matches:
                        # Limpar o match
                        match = match.strip("'\"")
                        
                        # Ignorar módulos Python e caminhos absolutos
                        if (not match.endswith('.py') and 
                            not os.path.isabs(match) and 
                            not match.startswith('%') and
                            not '(' in match and not ')' in match):
                            referencias.add(match)
        except Exception as e:
            print(f"Erro ao analisar {arquivo_py}: {e}")
    
    return referencias

# Função para verificar se existem arquivos com determinada extensão
def existem_arquivos_com_extensao(extensao):
    """Verifica se existem arquivos com a extensão especificada na pasta raiz"""
    padrao = f"*.{extensao}"
    arquivos = glob.glob(padrao)
    return len(arquivos) > 0

# Garante que o arquivo launcher.py existe
def verificar_launcher():
    if not os.path.exists('launcher.py'):
        print("Arquivo launcher.py não encontrado. Criando...")
        
        codigo_launcher = """import sys
import os
import importlib.util

def importar_modulo(nome_arquivo):
    try:
        spec = importlib.util.spec_from_file_location(nome_arquivo, nome_arquivo)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo
    except Exception as e:
        print(f"Erro ao importar {nome_arquivo}: {e}")
        return None

def main():
    print("Iniciando o Sistema de Gerenciamento Escolar...")
    
    # Verificar e configurar o MySQL
    verificar_mysql = importar_modulo("verificar_mysql.py")
    
    if verificar_mysql and verificar_mysql.main():
        print("MySQL configurado com sucesso. Iniciando o sistema...")
        
        # Importar e executar o aplicativo principal
        app_principal = importar_modulo("main.py")
        
        if app_principal:
            # O main.py já executa o aplicativo
            pass
        else:
            print("Erro ao iniciar o aplicativo principal.")
            return False
    else:
        print("Configuração do MySQL falhou. O aplicativo não pode ser iniciado.")
        return False
    
    return True

if __name__ == "__main__":
    main()
"""
        
        try:
            with open('launcher.py', 'w') as f:
                f.write(codigo_launcher)
            print("✓ Arquivo launcher.py criado com sucesso")
            return True
        except Exception as e:
            print(f"Erro ao criar launcher.py: {e}")
            return False
    
    return True

# Criar recursos básicos que podem estar faltando
print("\nVerificando e criando recursos básicos...")
criar_recursos_padrao()

# Verificar e criar launcher.py se necessário
verificar_launcher()

# Lista explícita de imagens que sabemos que são utilizadas
print("\nAdicionando imagens conhecidas à lista de recursos...")
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

# Adicionar as imagens conhecidas à lista de recursos
for imagem in imagens_conhecidas:
    caminho_completo = os.path.join(diretorio_base, imagem)
    if os.path.exists(caminho_completo):
        pasta_destino = os.path.dirname(imagem) if os.path.dirname(imagem) else '.'
        recursos.append((imagem, pasta_destino))
        print(f"✓ Imagem conhecida: {imagem}")
    else:
        print(f"⚠ Imagem {imagem} não encontrada. Será ignorada.")

# Adicionar pastas completas de recursos
print("\nAdicionando pastas completas de recursos...")
pastas_recursos = ['icon', 'imagens']
for pasta in pastas_recursos:
    pasta_completa = os.path.join(diretorio_base, pasta)
    if os.path.exists(pasta_completa) and os.path.isdir(pasta_completa):
        print(f"Processando pasta: {pasta}")
        for root, dirs, files in os.walk(pasta_completa):
            for arquivo in files:
                caminho_relativo = os.path.relpath(os.path.join(root, arquivo), diretorio_base)
                pasta_destino = os.path.dirname(caminho_relativo)
                recursos.append((caminho_relativo, pasta_destino))
                print(f"  - Adicionado: {caminho_relativo}")

# Encontrar referências a arquivos no código-fonte
print("\nProcurando referências a arquivos no código...")
referencias_arquivos = encontrar_referencias_arquivos(diretorio_base)
for ref in referencias_arquivos:
    try:
        # Verificar se a referência é um caminho válido
        caminho_completo = os.path.join(diretorio_base, ref)
        if os.path.exists(caminho_completo) and os.path.isfile(caminho_completo):
            pasta_destino = os.path.dirname(ref) if os.path.dirname(ref) else '.'
            item = (ref, pasta_destino)
            if item not in recursos:
                recursos.append(item)
                print(f"✓ Adicionado recurso encontrado no código: {ref}")
    except Exception as e:
        print(f"Erro ao processar referência {ref}: {e}")

# Adicionar todos os módulos Python na raiz (para garantir que estão inclusos)
print("\nAdicionando todos os módulos Python na raiz...")
for arquivo in os.listdir(diretorio_base):
    if arquivo.endswith('.py') and os.path.isfile(os.path.join(diretorio_base, arquivo)):
        recursos.append((arquivo, '.'))
        print(f"✓ Módulo Python: {arquivo}")

# Remover duplicatas da lista de recursos
recursos_unicos = []
[recursos_unicos.append(item) for item in recursos if item not in recursos_unicos]

# Configurações do PyInstaller
print("\nConfigurando opções do PyInstaller...")
opcoes = [
    'launcher.py',                  # Script principal atualizado (launcher em vez de main)
    '--name=Sistema_Escolar',       # Nome do executável
    '--onefile',                    # Cria um único arquivo executável
    '--windowed',                   # Não mostra console ao executar
    '--clean',                      # Limpa arquivos temporários antes de compilar
    '--icon=icon/learning.png',     # Ícone do executável
    '--hidden-import=mysql.connector', # Importação necessária para o verificador MySQL
    
    # Definir diretórios personalizados
    f'--distpath={diretorio_dist}',     # Pasta para o executável final
    f'--workpath={diretorio_build}',    # Pasta para arquivos temporários de compilação
    '--specpath=D:\\',                  # Pasta para arquivo .spec
]

# Verificar extensões antes de adicionar aos arquivos de dados
extensoes = ['png', 'jpg', 'jpeg']
for ext in extensoes:
    if existem_arquivos_com_extensao(ext):
        opcoes.append(f'--add-data=*.{ext};.')
        print(f"✓ Adicionando arquivos .{ext} da pasta raiz")
    else:
        print(f"⚠ Não foram encontrados arquivos .{ext} na pasta raiz")

# Adicionar todos os recursos identificados
print("\nAdicionando recursos às opções do PyInstaller...")
for arquivo_origem, pasta_destino in recursos_unicos:
    separador = ';' if sys.platform.startswith('win') else ':'
    opcoes.append(f'--add-data={arquivo_origem}{separador}{pasta_destino}')

# Executar o PyInstaller
print("\n" + "=" * 60)
print(f"Iniciando compilação com PyInstaller...")
print(f"Total de recursos incluídos: {len(recursos_unicos)}")
print("=" * 60)

try:
    # Adicionar extra dependências para mysql
    subprocess.run([sys.executable, "-m", "pip", "install", "mysql-connector-python"], check=True)
    print("Dependência mysql-connector-python instalada com sucesso!")

    run(opcoes)
    
    print("\n" + "=" * 60)
    print(f"Compilação concluída! Verifique a pasta '{diretorio_dist}' para encontrar o executável.")
    print("=" * 60)
    
    # Verificar se o executável foi criado
    executavel_path = os.path.join(diretorio_dist, 'Sistema_Escolar.exe')
    if os.path.exists(executavel_path):
        tamanho = os.path.getsize(executavel_path) / (1024 * 1024)
        print(f"\nTamanho do executável: {tamanho:.2f} MB")
        print(f"\nCaminho do executável: {executavel_path}")
        print("\nCompilação bem-sucedida!")
    else:
        print("\nAVISO: O executável não foi encontrado na pasta de destino.")
        print("Verifique se houve erros durante a compilação.")
except Exception as e:
    print("\n" + "=" * 60)
    print(f"ERRO DURANTE A COMPILAÇÃO: {str(e)}")
    print("=" * 60)
    
    print("\nDicas para resolver o problema:")
    print("1. Verifique se o drive D: existe e está acessível")
    print("2. Verifique se você tem permissões de escrita no drive D:")
    print("3. Tente executar 'pip install --upgrade pyinstaller mysql-connector-python'")
    print("4. Remova a opção '--onefile' para depurar problemas") 