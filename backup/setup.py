import os
import sys
import re
import glob
import shutil
import subprocess
from PyInstaller.__main__ import run
from config_logs import get_logger
from typing import Any

logger = get_logger(__name__)

# Diretório do projeto
diretorio_base = os.path.abspath(os.path.dirname(__file__))

# Diretórios personalizados para saída (ajustável)
diretorio_dist = os.path.join("D:", "dist")
diretorio_build = os.path.join("D:", "build")

os.makedirs(diretorio_dist, exist_ok=True)
os.makedirs(diretorio_build, exist_ok=True)

# Lista para armazenar todos os recursos (origem, destino)
recursos = []

logger.info("%s", "=" * 60)
logger.info("PREPARANDO A COMPILAÇÃO DO SISTEMA DE GERENCIAMENTO ESCOLAR")
logger.info("%s", "=" * 60)
logger.info("Diretório de saída (dist): %s", diretorio_dist)
logger.info("Diretório de trabalho (build): %s", diretorio_build)


def criar_recursos_padrao():
    """Cria diretórios e arquivos básicos necessários para a compilação."""
    try:
        # Diretórios básicos
        for d in ('icon', 'imagens'):
            if not os.path.exists(d):
                os.makedirs(d, exist_ok=True)
                logger.info("✓ Diretório '%s' criado", d)

        # Ícones básicos
        icones_basicos = [
            'icon/learning.png',
            'icon/book.png',
            'icon/left.png',
            'icon/plus.png',
            'icon/video-conference.png',
            'icon/history.png',
            'icon/settings.png'
        ]

        try:
            from PIL import Image, ImageDraw
        except Exception:
            logger.warning("Pillow não disponível; pulando criação de imagens de ícone")
            Image = None

        cores = {
            'learning': (65, 105, 225),
            'book': (46, 139, 87),
            'left': (255, 165, 0),
            'plus': (50, 205, 50),
            'video-conference': (218, 112, 214),
            'history': (30, 144, 255),
            'settings': (128, 128, 128)
        }

        if Image:
            bg_color: Any = (255, 255, 255)
            for icone in icones_basicos:
                if not os.path.exists(icone):
                    nome_base = os.path.splitext(os.path.basename(icone))[0]
                    tamanho = (50, 50)
                    img = Image.new('RGB', tamanho, bg_color)
                    cor = cores.get(nome_base, (100, 100, 100))
                    draw = ImageDraw.Draw(img)
                    draw.ellipse([(5, 5), (45, 45)], fill=cor)
                    img.save(icone)
                    logger.info("✓ Ícone '%s' criado", icone)

        # Logotipo simples
        if not os.path.exists('logopaco.png'):
            try:
                if Image:
                    img = Image.new('RGB', (200, 50), bg_color)
                    draw = ImageDraw.Draw(img)
                    draw.rectangle([(0, 0), (200, 50)], outline=(0, 0, 0))
                    img.save('logopaco.png')
                else:
                    # Cria arquivo vazio como fallback
                    open('logopaco.png', 'wb').close()
                logger.info("✓ Arquivo 'logopaco.png' criado")
            except Exception as e:
                logger.exception("Erro ao criar 'logopaco.png': %s", e)

        return True
    except Exception as e:
        logger.exception("Erro ao criar recursos padrão: %s", e)
        return False


def encontrar_referencias_arquivos(diretorio_base):
    """Analisa arquivos .py na raiz para encontrar referências a recursos."""
    referencias = set()
    logger.info("Procurando referências a arquivos no código...")

    padroes = [
        r"Image\.open\([\'\"](.+?)[\'\"]\)",
        r"ImageTk\.PhotoImage\(.*?file=[\'\"](.+?)[\'\"]\)",
        r"open\([\'\"](.+?)[\'\"]\)",
        r"--icon=([^\s\'\"]+)",
        r"os\.path\.join\([^\)]*?[\'\"](.+?)[\'\"]\)"
    ]

    arquivos_py = glob.glob(os.path.join(diretorio_base, "*.py"))
    for arquivo_py in arquivos_py:
        try:
            with open(arquivo_py, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            for padrao in padroes:
                matches = re.findall(padrao, conteudo)
                for match in matches:
                    match = match.strip("'\"")
                    if (not match.endswith('.py') and not os.path.isabs(match) and
                            not match.startswith('%') and '(' not in match and ')' not in match):
                        referencias.add(match)
        except Exception:
            logger.exception("Erro ao analisar %s", arquivo_py)

    return referencias


def existem_arquivos_com_extensao(extensao):
    padrao = f"*.{extensao}"
    arquivos = glob.glob(padrao)
    return len(arquivos) > 0


def verificar_launcher():
    """Garante que exista um `launcher.py` simples que importe e execute `main.py`."""
    caminho = os.path.join(diretorio_base, 'launcher.py')
    if os.path.exists(caminho):
        logger.info("Arquivo 'launcher.py' já existe")
        return True

    logger.info("Arquivo 'launcher.py' não encontrado. Criando...")
    codigo_launcher = '''import importlib.util
import sys
import os

def importar_modulo_por_arquivo(caminho):
    try:
        spec = importlib.util.spec_from_file_location('main', caminho)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo
    except Exception as e:
        logger.error(f"Erro ao importar {caminho}: {e}")
        return None

if __name__ == '__main__':
    base = os.path.dirname(__file__)
    main_py = os.path.join(base, 'main.py')
    importar_modulo_por_arquivo(main_py)
'''

    try:
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(codigo_launcher)
        logger.info("✓ Arquivo 'launcher.py' criado com sucesso")
        return True
    except Exception as e:
        logger.exception("Erro ao criar launcher.py: %s", e)
        return False


def main():
    logger.info("\nVerificando e criando recursos básicos...")
    criar_recursos_padrao()
    verificar_launcher()

    logger.info("Adicionando imagens conhecidas à lista de recursos...")
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

    for imagem in imagens_conhecidas:
        caminho_completo = os.path.join(diretorio_base, imagem)
        if os.path.exists(caminho_completo):
            recursos.append((imagem, os.path.dirname(imagem) or '.'))
            logger.info("✓ Imagem conhecida: %s", imagem)
        else:
            logger.warning("⚠ Imagem %s não encontrada. Será ignorada.", imagem)

    # Adicionar pastas de recursos completas
    pastas_recursos = ['icon', 'imagens']
    for pasta in pastas_recursos:
        pasta_completa = os.path.join(diretorio_base, pasta)
        if os.path.exists(pasta_completa) and os.path.isdir(pasta_completa):
            logger.info("Processando pasta: %s", pasta)
            for root, dirs, files in os.walk(pasta_completa):
                for arquivo in files:
                    caminho_relativo = os.path.relpath(os.path.join(root, arquivo), diretorio_base)
                    recursos.append((caminho_relativo, os.path.dirname(caminho_relativo) or '.'))
                    logger.info("  - Adicionado: %s", caminho_relativo)

    # Encontrar referências no código
    referencias_arquivos = encontrar_referencias_arquivos(diretorio_base)
    for ref in referencias_arquivos:
        try:
            caminho_completo = os.path.join(diretorio_base, ref)
            if os.path.exists(caminho_completo) and os.path.isfile(caminho_completo):
                pasta_destino = os.path.dirname(ref) or '.'
                recursos.append((ref, pasta_destino))
                logger.info("✓ Adicionado recurso encontrado no código: %s", ref)
        except Exception:
            logger.exception("Erro ao processar referência %s", ref)

    # Adicionar todos os módulos Python da raiz
    for arquivo in os.listdir(diretorio_base):
        if arquivo.endswith('.py'):
            recursos.append((arquivo, '.'))
            logger.info("✓ Módulo Python: %s", arquivo)

    # Remover duplicatas
    recursos_unicos = []
    [recursos_unicos.append(item) for item in recursos if item not in recursos_unicos]

    # Configurações do PyInstaller
    opcoes = [
        'launcher.py',
        '--name=Sistema_Escolar',
        '--onefile',
        '--windowed',
        '--clean',
        '--icon=icon/learning.png',
        '--hidden-import=mysql.connector',
        f'--distpath={diretorio_dist}',
        f'--workpath={diretorio_build}',
        '--specpath=D:'
    ]

    # Adicionar arquivos de dados (imagens)
    for ext in ('png', 'jpg', 'jpeg'):
        encontrados = glob.glob(os.path.join(diretorio_base, f'*.{ext}'))
        if encontrados:
            opcoes.append(f'--add-data=*.{ext};.')
            logger.info("✓ Adicionando arquivos .%s da pasta raiz", ext)
        else:
            logger.warning("⚠ Não foram encontrados arquivos .%s na pasta raiz", ext)

    # Adicionar recursos identificados
    for arquivo_origem, pasta_destino in recursos_unicos:
        separador = ';' if sys.platform.startswith('win') else ':'
        opcoes.append(f'--add-data={arquivo_origem}{separador}{pasta_destino}')

    logger.info("%s", "=" * 60)
    logger.info("Iniciando compilação com PyInstaller...")
    logger.info("Total de recursos incluídos: %d", len(recursos_unicos))

    try:
        # Instalar dependência extra para MySQL, se necessário
        subprocess.run([sys.executable, "-m", "pip", "install", "mysql-connector-python"], check=False)
        run(opcoes)
        logger.info("Compilação concluída! Verifique a pasta: %s", diretorio_dist)
    except Exception as e:
        logger.exception("Erro durante a compilação: %s", e)


if __name__ == '__main__':
    main()