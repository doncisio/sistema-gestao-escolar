"""
Script para gerar um arquivo contendo o código fonte de todos os
.py do projeto (exceto __pycache__ e o próprio arquivo de saída).

Uso:
    cd c:/gestao; python ./scripts/gerar_todos_codigos.py

Gera: c:/gestao/todos_codigos_sistema.txt
"""
import os
from pathlib import Path

ROOT = Path(os.getcwd())
OUTFILE = ROOT / 'todos_codigos_sistema.txt'

EXCLUDE_DIRS = {'__pycache__', '.git', 'venv', 'env', '.idea', '.vscode'}
EXCLUDE_FILES = {str(OUTFILE)}

def should_skip(path: Path) -> bool:
    try:
        for part in path.parts:
            if part in EXCLUDE_DIRS:
                return True
        if str(path) in EXCLUDE_FILES:
            return True
        return False
    except Exception:
        return True

def gather_py_files(root: Path):
    for p in root.rglob('*.py'):
        if should_skip(p):
            continue
        yield p

def main():
    files = list(gather_py_files(ROOT))
    files.sort()

    with OUTFILE.open('w', encoding='utf-8') as out:
        out.write('# Arquivo gerado: todos_codigos_sistema.txt\n')
        out.write(f'# Diretório base: {ROOT}\n')
        out.write(f'# Arquivos incluídos: {len(files)}\n\n')

        for f in files:
            out.write('\n' + '='*80 + '\n')
            out.write(f'# FILE: {f.relative_to(ROOT)}\n')
            out.write('='*80 + '\n')
            try:
                text = f.read_text(encoding='utf-8')
            except Exception:
                try:
                    text = f.read_text(encoding='latin-1')
                except Exception as e:
                    out.write(f'# ERRO AO LER: {e}\n')
                    continue
            out.write(text)
            out.write('\n')

    print(f'Gerado: {OUTFILE}')

if __name__ == '__main__':
    main()
