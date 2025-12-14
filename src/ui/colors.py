"""
Definições de cores do sistema de gestão escolar.

Este módulo centraliza todas as cores usadas na interface,
permitindo fácil manutenção e consistência visual.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class AppColors:
    """Esquema de cores da aplicação."""
    
    # Cores principais
    co0: str = "#F5F5F5"  # Branco suave para o fundo
    co1: str = "#003A70"  # Azul escuro (identidade visual)
    co2: str = "#77B341"  # Verde
    co3: str = "#E2418E"  # Rosa/Magenta
    co4: str = "#4A86E8"  # Azul claro (melhor contraste)
    co5: str = "#F26A25"  # Laranja
    co6: str = "#F7B731"  # Amarelo
    co7: str = "#333333"  # Cinza escuro
    co8: str = "#BF3036"  # Vermelho
    co9: str = "#6FA8DC"  # Azul claro (harmonia)
    
    def to_dict(self) -> Dict[str, str]:
        """Retorna as cores como dicionário para compatibilidade com código legado."""
        return {
            'co0': self.co0,
            'co1': self.co1,
            'co2': self.co2,
            'co3': self.co3,
            'co4': self.co4,
            'co5': self.co5,
            'co6': self.co6,
            'co7': self.co7,
            'co8': self.co8,
            'co9': self.co9,
        }


# Instância global para uso direto
COLORS = AppColors()


def get_color(name: str) -> str:
    """
    Obtém uma cor pelo nome.
    
    Args:
        name: Nome da cor (ex: 'co0', 'co1', etc.)
    
    Returns:
        Código hexadecimal da cor
    
    Raises:
        AttributeError: Se a cor não existir
    """
    color = getattr(COLORS, name)
    return str(color)


def get_colors_dict() -> Dict[str, str]:
    """
    Retorna todas as cores como dicionário.
    
    Útil para passar para componentes que esperam dict de cores.
    """
    return COLORS.to_dict()


# Atalhos para cores mais usadas (compatibilidade com código legado)
BRANCO = COLORS.co0
AZUL_ESCURO = COLORS.co1
VERDE = COLORS.co2
ROSA = COLORS.co3
AZUL_CLARO = COLORS.co4
LARANJA = COLORS.co5
AMARELO = COLORS.co6
CINZA_ESCURO = COLORS.co7
VERMELHO = COLORS.co8
AZUL_CLARO_ALT = COLORS.co9
