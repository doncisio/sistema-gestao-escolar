import os
import sys
from typing import List


def _find_repo_root(start_dir: str) -> str:
    cur = os.path.abspath(start_dir)
    for _ in range(8):
        if os.path.exists(os.path.join(cur, 'main.py')) or os.path.exists(os.path.join(cur, '.git')):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.abspath(os.getcwd())


def find_template(name: str) -> str:
    """Procura um arquivo de template pelo nome em locais prováveis.

    Ordem de busca (aproximada):
      - `<repo_root>/Modelos/<name>`
      - `<repo_root>/<name>`
      - `cwd/Modelos/<name>`
      - `cwd/<name>`
      - caminhos relativos à localização do pacote `services`

    Retorna o caminho absoluto do primeiro candidato encontrado ou levanta
    `FileNotFoundError` se nenhum for encontrado.
    """
    cwd = os.path.abspath(os.getcwd())
    pkg_dir = os.path.dirname(__file__)
    repo_root = _find_repo_root(pkg_dir)

    candidates: List[str] = [
        os.path.join(repo_root, 'Modelos', name),
        os.path.join(repo_root, name),
        os.path.join(cwd, 'Modelos', name),
        os.path.join(cwd, name),
        os.path.join(pkg_dir, '..', '..', 'Modelos', name),
        os.path.join(pkg_dir, '..', '..', name),
    ]

    for c in candidates:
        try:
            c_abs = os.path.abspath(c)
        except Exception:
            continue
        if os.path.isfile(c_abs):
            return c_abs

    raise FileNotFoundError(f"Arquivo base não encontrado. Procurado: {', '.join(candidates)}")
