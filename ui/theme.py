"""
Compatibilidade: constantes de tema usadas pela UI.

Este módulo fornece as constantes `CO_BG`, `CO_FG`, `CO_ACCENT`, `CO_WARN`
esperadas por diversos componentes (ex: `dashboard.py`). Ele mapeia para as
cores definidas em `ui.colors` de forma centralizada.
"""
from typing import Final

from .colors import BRANCO, AZUL_ESCURO, AMARELO, VERMELHO

# Fundo principal (azul escuro da identidade)
CO_BG: Final[str] = AZUL_ESCURO
# Cor de primeiro-plano / texto
CO_FG: Final[str] = BRANCO
# Cor de destaque / accent (botões etc.)
CO_ACCENT: Final[str] = AMARELO
# Cor de aviso / erro
CO_WARN: Final[str] = VERMELHO

__all__ = ["CO_BG", "CO_FG", "CO_ACCENT", "CO_WARN"]
"""Tema simples com cores/constantes usadas pela UI centralizada.

Colocar as cores aqui facilita a alteração de aparência e a revisão
durante refactors que movem widgets para `ui/`.
"""

CO_BG = '#003A70'   # cor principal de fundo (co1)
CO_FG = '#F5F5F5'   # cor de texto (co0)
CO_ACCENT = '#4A86E8'  # cor de destaque/acao (co4)
CO_WARN = '#F7B731'  # cor do botão/aviso (co6)
