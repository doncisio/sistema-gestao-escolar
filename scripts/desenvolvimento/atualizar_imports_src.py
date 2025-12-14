"""
Script para atualizar imports de diretórios raiz para src/
Atualiza imports de models, services, ui, utils, config, utilitarios
"""

import os
import re
from pathlib import Path

# Mapeamentos de imports antigos para novos
MAPEAMENTOS = {
    'from src.models.': 'from src.models.',
    'import src.models.': 'import src.models.',
    'from src.services.': 'from src.services.',
    'import src.services.': 'import src.services.',
    'from src.ui.': 'from src.ui.',
    'import src.ui.': 'import src.ui.',
    'from src.utils.': 'from src.utils.',
    'import src.utils.': 'import src.utils.',
    'from src.core.config.settings': 'from src.core.config.settings',
    'from src.core.config.': 'from src.core.config.',
    'import src.core.config.': 'import src.core.config.',
    'from src.utils.utilitarios.': 'from src.utils.utilitarios.',
    'import src.utils.utilitarios.': 'import src.utils.utilitarios.',
}

def atualizar_imports_arquivo(caminho_arquivo):
    """Atualiza imports em um arquivo Python"""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        conteudo_original = conteudo
        substituicoes = 0
        
        # Aplicar cada mapeamento
        for antigo, novo in MAPEAMENTOS.items():
            if antigo in conteudo:
                # Usar regex para garantir que estamos substituindo imports completos
                # e não partes de strings ou comentários
                padrao = re.escape(antigo)
                conteudo_temp = re.sub(padrao, novo, conteudo)
                if conteudo_temp != conteudo:
                    substituicoes += len(re.findall(padrao, conteudo))
                    conteudo = conteudo_temp
        
        if conteudo != conteudo_original:
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            return substituicoes
        
        return 0
    except Exception as e:
        print(f"❌ Erro ao processar {caminho_arquivo}: {e}")
        return 0

def main():
    raiz = Path(r'c:\gestao')
    total_arquivos = 0
    total_substituicoes = 0
    arquivos_modificados = []
    
    print("=" * 80)
    print("FASE 3: Atualização de Imports para src/")
    print("=" * 80)
    print()
    
    # Processar todos os arquivos Python
    for arquivo_py in raiz.rglob('*.py'):
        # Pular diretórios que não devem ser processados
        partes_caminho = arquivo_py.parts
        if any(skip in partes_caminho for skip in [
            'venv', 'env', '.venv', 
            'arquivos_nao_utilizados', 'scripts_nao_utilizados',
            'node_modules', '.git'
        ]):
            continue
        
        total_arquivos += 1
        subs = atualizar_imports_arquivo(arquivo_py)
        
        if subs > 0:
            total_substituicoes += subs
            arquivo_relativo = arquivo_py.relative_to(raiz)
            arquivos_modificados.append((str(arquivo_relativo), subs))
            print(f"✅ {arquivo_relativo}: {subs} imports atualizados")
    
    print()
    print("=" * 80)
    print("RESUMO DA ATUALIZAÇÃO")
    print("=" * 80)
    print(f"Arquivos processados: {total_arquivos}")
    print(f"Arquivos modificados: {len(arquivos_modificados)}")
    print(f"Total de imports atualizados: {total_substituicoes}")
    print()
    
    if arquivos_modificados:
        print("Arquivos com mais alterações:")
        for arquivo, subs in sorted(arquivos_modificados, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  • {arquivo}: {subs} substituições")
    
    print()
    print("=" * 80)
    print("✅ Atualização de imports concluída!")
    print("=" * 80)
    
    return total_substituicoes

if __name__ == "__main__":
    main()
