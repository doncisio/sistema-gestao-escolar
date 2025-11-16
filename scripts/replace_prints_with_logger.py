"""
Conservador: substitui ocorrências simples de `print(...)` por `logger` em arquivos .py.
Modo dry-run exibe as mudanças propostas; use --apply para aplicar.
Exclusões por regex de caminho, e limite de arquivos processados.

Uso:
  python scripts\replace_prints_with_logger.py --dry-run --exclude "scripts_nao_utilizados|testes" --limit 20
  python scripts\replace_prints_with_logger.py --apply --exclude "tests|scripts_nao_utilizados" --limit 5

Observações:
- Mantém `print(..., end='\r')` (progresso de terminal) e `print()` usados para prompts antes de `input()`.
- Não tenta reestruturar prints complexos (file=, flush=) ou prints multilinha complexos.
- Insere `from config_logs import get_logger` e `logger = get_logger(__name__)` quando necessário.
"""
from __future__ import annotations
import re
import argparse
from pathlib import Path
from typing import List, Pattern, Optional
import shutil
import subprocess
import sys
import os

PRINT_RE = re.compile(r"(?P<indent>\s*)print\s*\(")
PROGRESS_RE = re.compile(r"end\s*=\s*['\"]\\r['\"]")
ERROR_KEYWORDS = re.compile(r"\b(Erro|Erro ao|✗|⚠|Falha|Exception|Traceback)\b", re.IGNORECASE)

TEMPLATE_IMPORT = "from config_logs import get_logger\nlogger = get_logger(__name__)\n"


def should_skip_file(path: Path, exclude_re: Optional[Pattern[str]]) -> bool:
    s = str(path)
    if exclude_re and exclude_re.search(s):
        return True
    # skip hidden dirs and venvs
    parts = path.parts
    for p in parts:
        if p.startswith('.') or p in ("venv", "env", ".venv", "__pycache__"):
            return True
    return False


def analyze_and_transform(text: str) -> tuple[str, List[str]]:
    """Return new_text, list of changed lines (for dry-run)."""
    lines = text.splitlines()
    changed = []
    new_lines = []
    has_logger = 'get_logger' in text or 'getLogger(' in text
    inserted_logger = False

    for i, line in enumerate(lines):
        m = PRINT_RE.search(line)
        if not m:
            new_lines.append(line)
            continue

        # skip prints used for progress
        if PROGRESS_RE.search(line):
            new_lines.append(line)
            continue

        # skip commented prints
        stripped = line.strip()
        if stripped.startswith('#'):
            new_lines.append(line)
            continue

        # skip prints very likely to be UI prompts (heuristic: contains 'Digite' or 'Pressione' or 'Opção')
        if re.search(r"Digite|Pressione|Opção|Escolha", line, re.IGNORECASE):
            new_lines.append(line)
            continue

        # choose level
        if ERROR_KEYWORDS.search(line):
            level = 'error'
        else:
            level = 'info'

        # replace only the first occurrence of print( in the line
        new_line = line.replace('print(', f'logger.{level}(', 1)
        new_lines.append(new_line)
        changed.append(f"{i+1}: {line.strip()} -> {new_line.strip()}")

    new_text = '\n'.join(new_lines)

    # if changes and no logger import, prepend import
    if changed and not has_logger:
        new_text = TEMPLATE_IMPORT + new_text
        inserted_logger = True
        changed.insert(0, 'inserted logger import')

    return new_text, changed


def process_file(path: Path, dry_run: bool) -> List[str]:
    text = path.read_text(encoding='utf-8')
    new_text, changes = analyze_and_transform(text)
    if not changes:
        return []
    if dry_run:
        return changes
    # backup
    bak = path.with_suffix(path.suffix + '.bak')
    shutil.copy2(path, bak)
    path.write_text(new_text, encoding='utf-8')
    return changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Mostrar mudanças propostas')
    parser.add_argument('--apply', action='store_true', help='Aplicar mudanças')
    parser.add_argument('--exclude', default='', help='Regex para caminhos a excluir')
    parser.add_argument('--limit', type=int, default=0, help='Limite de arquivos a processar (0 = sem limite)')
    parser.add_argument('--paths', nargs='*', help='Arquivos ou pastas específicos para incluir')
    parser.add_argument('--no-cleanup', action='store_true', help='Não rodar pytest/apagar .bak automaticamente após --apply')
    args = parser.parse_args()

    exclude_re = re.compile(args.exclude) if args.exclude else None

    root = Path('.').resolve()
    candidate_files: List[Path] = []

    if args.paths:
        for p in args.paths:
            pth = Path(p)
            if pth.is_file() and pth.suffix == '.py':
                candidate_files.append(pth)
            elif pth.is_dir():
                candidate_files.extend([f for f in pth.rglob('*.py')])
    else:
        candidate_files = [f for f in root.rglob('*.py')]

    # sort for determinism
    candidate_files = sorted([f for f in candidate_files if not should_skip_file(f, exclude_re)])

    if args.limit:
        candidate_files = candidate_files[:args.limit]

    total_changed = 0
    for f in candidate_files:
        changes = process_file(f, dry_run=not args.apply)
        if changes:
            total_changed += 1
            print(f"== {f} ==")
            for c in changes:
                print('   ', c)

    print(f"Processed {len(candidate_files)} files, changed {total_changed} files.")

    # If we applied changes, optionally run pytest and cleanup .bak files
    if args.apply and not getattr(args, 'no_cleanup', False):
        def run_pytest(root: Path) -> bool:
            print('Running pytest -q in:', root)
            proc = subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=str(root))
            return proc.returncode == 0

        def find_bak_files(root: Path) -> List[Path]:
            bak_files: List[Path] = []
            for dirpath, dirnames, filenames in os.walk(str(root)):
                for fn in filenames:
                    if fn.endswith('.bak'):
                        bak_files.append(Path(dirpath) / fn)
            return bak_files

        root = Path('.').resolve()
        ok = run_pytest(root)
        if not ok:
            print('\nPytest failed — not deleting any .bak files.')
            sys.exit(1)

        bak_files = find_bak_files(root)
        if not bak_files:
            print('\nNo .bak files found to delete under', root)
        else:
            print('\nDeleting .bak files:')
            deleted = 0
            for p in bak_files:
                try:
                    p.unlink()
                    print('  Deleted', p)
                    deleted += 1
                except Exception as e:
                    print('  Failed to delete', p, '-', e)
            print('\nDeleted', deleted, 'of', len(bak_files), 'files.')


if __name__ == '__main__':
    main()
