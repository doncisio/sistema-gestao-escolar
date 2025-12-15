"""Reexporta `settings` de `src.core.config.settings` para compatibilidade.

Permitirá que `from config.settings import settings` funcione como esperado
em scripts e workflows que assumem esse caminho.
"""
from src.core.config.settings import settings, validate_settings  # noqa: F401

__all__ = ["settings", "validate_settings"]
