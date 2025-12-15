"""Compatibilidade de import para módulos que usam `import config`.

Este pacote reexporta as definições de `src.core.config` para manter compatibilidade
com código leg legacy que importa `config` no nível do projeto.
"""
from src.core.config import *  # noqa: F401,F403
from src.core.config.settings import settings, validate_settings  # noqa: F401

# Explicitar __all__ para evitar poluição quando usado via `from config import *`
__all__ = [name for name in dir() if not name.startswith("_")]
