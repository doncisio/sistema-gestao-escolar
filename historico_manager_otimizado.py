"""
Stub module to satisfy imports and basic tests in `teste_sistema_otimizado.py`.
Provides:
- `HistoricoManagerOtimizado` (minimal manager)
- `historico_manager` (singleton instance with a `validador` attribute)
- `CacheCompartilhado` (simple in-memory cache)

This stub is intentionally lightweight and only implements the small
subset of behavior expected by the test script. Replace with the
real implementation when available.
"""
from typing import Any, Optional


class Validador:
    """Minimal validator used by tests."""

    def validar_aluno_id(self, value: Any) -> int:
        # Accept int or numeric string
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        raise ValueError(f"aluno_id inválido: {value}")

    def validar_media(self, value: Any) -> float:
        # Accept float or numeric string like '8.5'
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(',', '.'))
            except Exception as e:
                raise ValueError(f"média inválida: {value}") from e
        raise ValueError(f"média inválida: {value}")

    def validar_conceito(self, value: Any) -> str:
        # Accept string concepts and normalize to upper-case
        if value is None:
            raise ValueError("conceito inválido: None")
        if not isinstance(value, str):
            raise ValueError(f"conceito inválido: {value}")
        return value.strip().upper()


class HistoricoManagerOtimizado:
    """Minimal manager providing a `validador` attribute."""

    def __init__(self) -> None:
        self.validador = Validador()


# Singleton instance used by tests
historico_manager = HistoricoManagerOtimizado()


class CacheCompartilhado:
    """Simple in-memory cache with set/get/invalidar methods."""

    def __init__(self) -> None:
        self._store: dict = {}

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    def invalidar(self, key: str) -> None:
        if key in self._store:
            del self._store[key]


__all__ = [
    "HistoricoManagerOtimizado",
    "historico_manager",
    "CacheCompartilhado",
    "Validador",
]
