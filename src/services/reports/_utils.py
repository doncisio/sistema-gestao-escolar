"""Utilitários compartilhados entre os submódulos de relatório."""

import os
import importlib
import importlib.util
from typing import Optional

from src.core.config_logs import get_logger

logger = get_logger(__name__)


def _find_image_in_repo(filename: str) -> Optional[str]:
    """Tenta localizar uma imagem no repositório retornando caminho absoluto.

    Procura em alguns locais prováveis (diretório do módulo, diretório pai e
    raíz do repositório/workdir). Retorna ``None`` se não encontrar.
    """
    import os as _os

    # Tentativa 1: localizar raiz do repositório subindo a partir do diretório do módulo
    mod_dir = _os.path.dirname(__file__)
    repo_root = None
    cur = mod_dir
    for _ in range(6):
        if not cur:
            break
        if _os.path.exists(_os.path.join(cur, 'main.py')) or _os.path.exists(_os.path.join(cur, '.git')):
            repo_root = cur
            break
        parent = _os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    if repo_root is None:
        repo_root = _os.path.abspath(_os.getcwd())

    candidates = [
        _os.path.join(mod_dir, filename),
        _os.path.join(mod_dir, '..', filename),
        _os.path.join(repo_root, filename),
        _os.path.join(repo_root, 'imagens', filename),
        _os.path.join(mod_dir, '..', 'imagens', filename),
    ]

    base, ext = _os.path.splitext(filename)
    other_exts = ['.png', '.jpg', '.jpeg']
    for e in other_exts:
        candidates.append(_os.path.join(repo_root, base + e))
        candidates.append(_os.path.join(mod_dir, base + e))
        candidates.append(_os.path.join(repo_root, 'imagens', base + e))

    for c in candidates:
        try:
            c_abs = _os.path.abspath(c)
        except Exception:
            continue
        if _os.path.exists(c_abs):
            return c_abs

    try:
        repo_root_abs = _os.path.abspath(repo_root)
        for dirpath, dirnames, files in _os.walk(repo_root_abs):
            rel = _os.path.relpath(dirpath, repo_root_abs)
            depth = 0 if rel == '.' else rel.count(_os.path.sep) + 1
            if depth > 3:
                dirnames.clear()
                continue
            if filename in files:
                return _os.path.join(dirpath, filename)
            for e in other_exts:
                alt = base + e
                if alt in files:
                    return _os.path.join(dirpath, alt)
    except Exception:
        pass

    logger.warning("Imagem '%s' não encontrada nos locais procurados; exemplos: %s", filename, ','.join(candidates))
    return None


def _ensure_legacy_module(target, required=None, candidate_filename: Optional[str] = None):
    """Garantir acesso ao módulo legado.

    - ``target`` pode ser o nome do módulo (str) ou um módulo já importado.
    - ``required`` (opcional) é uma lista de atributos esperados no módulo.
    - ``candidate_filename`` indica o arquivo-fonte caso seja necessário
      carregar direto do disco.

    Retorna o módulo real. Levanta exceções se não conseguir carregar.
    """
    import os as _os

    if isinstance(target, str):
        name = target
        candidate = candidate_filename or f"{name}.py"
        try:
            mod = importlib.import_module(name)
            if required and not all(hasattr(mod, r) for r in required):
                repo_root = _os.path.abspath(_os.getcwd())
                candidate_path = _os.path.join(repo_root, candidate)
                if not _os.path.isfile(candidate_path):
                    return mod
                spec = importlib.util.spec_from_file_location(f"{name}_real", candidate_path)
                if spec is None or spec.loader is None:
                    return mod
                real = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(real)  # type: ignore
                return real
            return mod
        except Exception:
            repo_root = _os.path.abspath(_os.getcwd())
            candidate_path = _os.path.join(repo_root, candidate)
            if not _os.path.isfile(candidate_path):
                raise
            spec = importlib.util.spec_from_file_location(f"{name}_real", candidate_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Não foi possível carregar spec para {candidate_path}")
            real = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(real)  # type: ignore
            return real

    # target é um módulo
    mod = target
    if not required:
        return mod
    if all(hasattr(mod, r) for r in required):
        return mod

    name = getattr(mod, '__name__', None) or 'legacy'
    candidate = candidate_filename or f"{name}.py"
    repo_root = _os.path.abspath(_os.getcwd())
    candidate_path = _os.path.join(repo_root, candidate)
    if not _os.path.isfile(candidate_path):
        return mod
    spec = importlib.util.spec_from_file_location(f"{name}_real", candidate_path)
    if spec is None or spec.loader is None:
        return mod
    real = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(real)  # type: ignore
    return real
