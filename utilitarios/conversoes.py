"""Helpers de conversão seguros centralizados.

Fornece `to_safe_int` e `to_safe_float` usados por vários módulos.

As funções são anotadas para melhorar a inferência de tipos por ferramentas
estáticas (p.ex. Pylance) e tratam vírgulas decimais e espaços.
"""
from decimal import Decimal, InvalidOperation
from typing import Any, Optional


def to_safe_int(value: Any) -> Optional[int]:
    """Tenta converter `value` para `int`, retornando `None` em caso de falha.

    Aceita `int`, `float`, `Decimal`, `str` com números (aceita vírgula como separador
    decimal), e objetos que implementam `__int__`.
    """
    try:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            # Trunca parte fracionária, compatível com comportamento anterior
            return int(value)
        if isinstance(value, Decimal):
            return int(value)
        if isinstance(value, str):
            s = value.strip()
            if s == "":
                return None
            # Aceita vírgula decimal e sinais
            s = s.replace("\u00A0", "")  # remover non-break space, se houver
            s = s.replace(',', '.')
            try:
                # Usar Decimal para evitar problemas com notação local
                d = Decimal(s)
                return int(d)
            except (InvalidOperation, ValueError):
                return None
        if hasattr(value, '__int__'):
            try:
                return int(value)
            except Exception:
                return None
    except Exception:
        return None
    return None


def to_safe_float(value: Any) -> Optional[float]:
    """Tenta converter `value` para `float`, retornando `None` em caso de falha.

    Aceita `float`, `int`, `Decimal`, `str` com números (aceita vírgula como separador
    decimal), e objetos que implementam `__float__`.
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
            if s == "":
                return None
            s = s.replace("\u00A0", "")
            s = s.replace(',', '.')
            try:
                d = Decimal(s)
                return float(d)
            except (InvalidOperation, ValueError):
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
