"""Helpers de conversão seguros centralizados.

Fornece `to_safe_int` e `to_safe_float` usados por vários módulos.
"""
from decimal import Decimal

def to_safe_int(value):
    """Tenta converter `value` para int retornando None em caso de falha.

    Aceita int, float, Decimal, str com números, e objetos que implementam __int__.
    Retorna None quando a conversão não é possível.
    """
    try:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, Decimal):
            return int(value)
        if isinstance(value, str):
            s = value.strip()
            if s.isdigit():
                return int(s)
            try:
                f = float(s)
                return int(f)
            except Exception:
                return None
        if hasattr(value, '__int__'):
            try:
                return int(value)
            except Exception:
                return None
    except Exception:
        return None
    return None


def to_safe_float(value):
    """Tenta converter `value` para float retornando None em caso de falha.

    Aceita float, int, Decimal, str com números, e objetos que implementam __float__.
    """
    try:
        if value is None:
            return None
        if isinstance(value, float):
            return value
        if isinstance(value, int):
            return float(value)
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, str):
            s = value.strip()
            try:
                return float(s)
            except Exception:
                return None
        if hasattr(value, '__float__'):
            try:
                return float(value)
            except Exception:
                return None
    except Exception:
        return None
    return None


__all__ = ["to_safe_int", "to_safe_float"]
