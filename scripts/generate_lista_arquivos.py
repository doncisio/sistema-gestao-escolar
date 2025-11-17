"""
Gera `lista_arquivos_codigo.txt` com caminhos relativos de todos os arquivos .py
Ignora pastas comuns de build/IDE.
"""
import os
from pathlib import Path

ROOT = Path(os.getcwd())
OUT = ROOT / 'lista_arquivos_codigo.txt'
EXCLUDE_DIRS = {'__pycache__', '.git', 'venv', 'env', '.idea', '.vscode', 'backup', 'scripts_nao_utilizados'}

with OUT.open('w', encoding='utf-8') as out:
    out.write('# Lista de arquivos .py no projeto\n')
    out.write('# Gerado automaticamente\n')
    out.write(f'# Diretório base: {ROOT}\n\n')

    for root, dirs, files in os.walk(ROOT):
        # Normalizar dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        rel_root = Path(root).relative_to(ROOT)
        for name in sorted(files):
            if not name.endswith('.py'):
                continue
            path = (rel_root / name) if str(rel_root) != '.' else Path(name)
            out.write(str(path).replace('\\', '/') + '\n')

print(f'Gerado: {OUT}')