"""
Script de validação para garantir que não há código de inicialização
em lugares errados nas interfaces.

Verifica especificamente se métodos como criar_frames(), criar_header(), 
criar_botoes(), criar_conteudo_principal() estão apenas no __init__
e não aparecem após returns em outros métodos.
"""

import os
import re
from pathlib import Path

def validar_arquivo(arquivo_path):
    """
    Valida um arquivo de interface Python.
    
    Retorna:
        list: Lista de problemas encontrados (vazia se OK)
    """
    problemas = []
    
    with open(arquivo_path, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    
    # Padrões a procurar
    metodos_inicializacao = [
        r'self\.criar_frames\(\)',
        r'self\.criar_header\(\)',
        r'self\.criar_botoes\(\)',
        r'self\.criar_conteudo_principal\(\)',
        r'self\.master\.grid_rowconfigure\(',
        r'self\.master\.grid_columnconfigure\(',
    ]
    
    # Estado do parser
    dentro_de_init = False
    dentro_de_outro_metodo = False
    nome_metodo_atual = None
    linha_return_recente = None
    identacao_metodo = 0
    
    for i, linha in enumerate(linhas, start=1):
        linha_stripped = linha.lstrip()
        
        # Detectar início de método __init__
        if re.match(r'def __init__\(', linha_stripped):
            dentro_de_init = True
            dentro_de_outro_metodo = False
            nome_metodo_atual = '__init__'
            identacao_metodo = len(linha) - len(linha_stripped)
            linha_return_recente = None
            continue
        
        # Detectar início de outro método
        if re.match(r'def \w+\(', linha_stripped) and not dentro_de_init:
            match = re.match(r'def (\w+)\(', linha_stripped)
            if match:
                dentro_de_outro_metodo = True
                nome_metodo_atual = match.group(1)
                identacao_metodo = len(linha) - len(linha_stripped)
                linha_return_recente = None
                continue
        
        # Detectar início de nova classe ou método no mesmo nível (sai do método atual)
        if linha_stripped.startswith('def ') or linha_stripped.startswith('class '):
            identacao_atual = len(linha) - len(linha_stripped)
            if identacao_atual <= identacao_metodo:
                dentro_de_init = False
                dentro_de_outro_metodo = False
                nome_metodo_atual = None
                linha_return_recente = None
        
        # Detectar return statements
        if dentro_de_outro_metodo and re.search(r'^\s+return\s+', linha):
            linha_return_recente = i
        
        # Verificar chamadas de métodos de inicialização
        if dentro_de_outro_metodo and linha_return_recente:
            for padrao in metodos_inicializacao:
                if re.search(padrao, linha):
                    # Código de inicialização encontrado após return em método não-__init__
                    problemas.append({
                        'linha': i,
                        'metodo': nome_metodo_atual,
                        'linha_return': linha_return_recente,
                        'codigo': linha.strip(),
                        'tipo': 'codigo_inicializacao_apos_return'
                    })
    
    return problemas


def validar_diretorio_interfaces():
    """
    Valida todos os arquivos .py no diretório src/interfaces.
    """
    interfaces_dir = Path('c:/gestao/src/interfaces')
    
    if not interfaces_dir.exists():
        print(f"Diretório não encontrado: {interfaces_dir}")
        return
    
    arquivos_python = list(interfaces_dir.glob('*.py'))
    
    print(f"Validando {len(arquivos_python)} arquivos de interface...\n")
    
    total_problemas = 0
    arquivos_com_problemas = []
    
    for arquivo in sorted(arquivos_python):
        problemas = validar_arquivo(arquivo)
        
        if problemas:
            total_problemas += len(problemas)
            arquivos_com_problemas.append(arquivo.name)
            print(f"\n[ERRO] {arquivo.name}:")
            print("=" * 80)
            
            for problema in problemas:
                print(f"  Linha {problema['linha']}: {problema['codigo']}")
                print(f"    → Encontrado no método '{problema['metodo']}'")
                print(f"    → Código de inicialização após return (linha {problema['linha_return']})")
                print()
    
    # Resumo
    print("\n" + "=" * 80)
    print("RESUMO DA VALIDACAO")
    print("=" * 80)
    
    if total_problemas == 0:
        print("[OK] Nenhum problema encontrado!")
        print(f"   {len(arquivos_python)} arquivos validados com sucesso.")
    else:
        print(f"[ERRO] {total_problemas} problema(s) encontrado(s) em {len(arquivos_com_problemas)} arquivo(s):")
        for arquivo in arquivos_com_problemas:
            print(f"   - {arquivo}")
    
    print("\n")


if __name__ == '__main__':
    validar_diretorio_interfaces()
