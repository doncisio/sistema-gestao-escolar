"""
Script para construir o executável do Sistema de Gestão Escolar.
Usa PyInstaller para empacotar a aplicação em um executável Windows.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_dirs():
    """Remove diretórios de builds anteriores."""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"Removendo {dir_name}/...")
            shutil.rmtree(dir_path)
    
    # Remover arquivos .spec antigos
    for spec_file in Path('.').glob('*.spec'):
        print(f"Removendo {spec_file}...")
        spec_file.unlink()

def create_version_file():
    """Cria arquivo de informações de versão para o executável."""
    version_info = """# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Sistema de Gestão Escolar'),
        StringStruct(u'FileDescription', u'Sistema de Gestão Escolar'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'GestaoEscolar'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2025'),
        StringStruct(u'OriginalFilename', u'GestaoEscolar.exe'),
        StringStruct(u'ProductName', u'Sistema de Gestão Escolar'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    print("Arquivo de versão criado: version_info.txt")

def collect_data_files():
    """Identifica arquivos de dados que devem ser incluídos."""
    data_files = []
    
    # Arquivos e diretórios essenciais
    essentials = [
        ('.env.example', '.'),
        ('credentials.json', '.'),
        ('feature_flags.json', '.'),
        ('habilidades_bncc_parsed.csv', '.'),
    ]
    
    for src, dest in essentials:
        if os.path.exists(src):
            data_files.append((src, dest))
    
    # Diretórios completos
    dirs_to_include = ['config', 'ui', 'templates', 'static']
    for dir_name in dirs_to_include:
        if os.path.exists(dir_name):
            data_files.append((f'{dir_name}', dir_name))
    
    return data_files

def construir_wizard():
    """Função auxiliar para construir apenas o wizard (sem limpar)."""
    return build_setup_wizard()

def build_setup_wizard():
    """Constrói o executável do assistente de configuração."""
    print("\n" + "="*70)
    print("CONSTRUINDO ASSISTENTE DE CONFIGURAÇÃO")
    print("="*70 + "\n")
    
    cmd = [
        'pyinstaller',
        '--name=setup_wizard',
        '--onefile',
        '--windowed',
        '--clean',
        '--noconfirm',
        '--hidden-import=mysql.connector',
        '--hidden-import=tkinter',
        'setup_wizard.py'
    ]
    
    # Adicionar ícone se existir
    if os.path.exists('icon.ico'):
        cmd.insert(5, '--icon=icon.ico')
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Assistente de configuração criado!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erro ao criar assistente de configuração")
        return False

def build_executable(skip_clean=False):
    """Constrói o executável usando PyInstaller."""
    print("\n" + "="*70)
    print("CONSTRUINDO EXECUTÁVEL DO SISTEMA DE GESTÃO ESCOLAR")
    print("="*70 + "\n")
    
    # Limpar builds anteriores (apenas se não estiver construindo ambos)
    if not skip_clean:
        clean_build_dirs()
    
    # Criar arquivo de versão
    create_version_file()
    
    # Coletar arquivos de dados
    data_files = collect_data_files()
    
    # Montar comando PyInstaller
    cmd = [
        'pyinstaller',
        '--name=GestaoEscolar',
        '--onefile',  # Criar um único arquivo executável
        '--windowed',  # Não mostrar console (aplicação GUI)
        '--version-file=version_info.txt',
        '--clean',
        '--noconfirm',
    ]
    
    # Adicionar ícone se existir
    if os.path.exists('icon.ico'):
        cmd.insert(5, '--icon=icon.ico')
    
    # Adicionar hidden imports necessários
    hidden_imports = [
        'mysql.connector',
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'google.auth',
        'google.oauth2',
        'selenium',
        'reportlab',
        'pandas',
        'openpyxl',
    ]
    
    for imp in hidden_imports:
        cmd.append(f'--hidden-import={imp}')
    
    # Adicionar arquivos de dados
    for src, dest in data_files:
        if os.path.isfile(src):
            cmd.append(f'--add-data={src};{dest}')
        elif os.path.isdir(src):
            cmd.append(f'--add-data={src};{dest}')
    
    # Arquivo principal
    cmd.append('main.py')
    
    # Remover strings vazias
    cmd = [c for c in cmd if c]
    
    print("Comando PyInstaller:")
    print(' '.join(cmd))
    print("\n" + "="*70 + "\n")
    
    # Executar PyInstaller
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*70)
        print("✅ EXECUTÁVEL CRIADO COM SUCESSO!")
        print("="*70)
        print(f"\nArquivo criado em: dist\\GestaoEscolar.exe")
        print("\nPróximos passos:")
        print("1. Teste o executável: .\\dist\\GestaoEscolar.exe")
        print("2. Crie o instalador: Execute o script Inno Setup (GestaoEscolar.iss)")
        print("="*70 + "\n")
        return True
    except subprocess.CalledProcessError as e:
        print("\n" + "="*70)
        print("❌ ERRO AO CRIAR EXECUTÁVEL")
        print("="*70)
        print(f"Erro: {e}")
        return False
    except FileNotFoundError:
        print("\n" + "="*70)
        print("❌ PYINSTALLER NÃO ENCONTRADO")
        print("="*70)
        print("Instale o PyInstaller primeiro:")
        print("  pip install pyinstaller")
        print("="*70 + "\n")
        return False

if __name__ == '__main__':
    # Construir ambos executáveis
    print("\n" + "="*70)
    print("INICIANDO BUILD COMPLETO")
    print("="*70 + "\n")
    
    # Limpar uma vez no início
    clean_build_dirs()
    
    success_wizard = build_setup_wizard()
    success_main = build_executable(skip_clean=True)  # Não limpar novamente
    
    if success_wizard and success_main:
        print("\n" + "="*70)
        print("✅ TODOS OS EXECUTÁVEIS CRIADOS COM SUCESSO!")
        print("="*70)
        print("\nArquivos criados:")
        print("  • dist\\GestaoEscolar.exe - Aplicação principal")
        print("  • dist\\setup_wizard.exe - Assistente de configuração")
        print("\nPróximo passo: Compilar instalador com Inno Setup")
        print("="*70 + "\n")
    
    sys.exit(0 if (success_wizard and success_main) else 1)
