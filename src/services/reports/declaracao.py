"""Geração de declarações."""

import sys
from typing import Optional, Any, cast, Tuple

from src.core.config_logs import get_logger
from src.services.reports._utils import _ensure_legacy_module

logger = get_logger(__name__)


def gerar_declaracao(aluno_id: int, tipo: str = 'comparecimento', data=None) -> Tuple[bool, Optional[str]]:
    """Wrapper compatível para geração de declarações."""
    _mod = sys.modules.get('gerar_declaracao') or sys.modules.get('Gerar_Declaracao_Aluno')
    if _mod is not None:
        if hasattr(_mod, 'gerar_declaracao'):
            resultado = cast(Any, _mod).gerar_declaracao(aluno_id=aluno_id, tipo=tipo, data=data)
            if isinstance(resultado, tuple):
                return (bool(resultado[0]), resultado[1] if len(resultado) > 1 and isinstance(resultado[1], str) else None)
            if isinstance(resultado, str):
                return True, resultado
            return bool(resultado), None

    try:
        _leg = _ensure_legacy_module('Gerar_Declaracao_Aluno', candidate_filename='Gerar_Declaracao_Aluno.py')
        if hasattr(_leg, 'gerar_declaracao'):
            resultado = cast(Any, _leg).gerar_declaracao(aluno_id=aluno_id, tipo=tipo, data=data)
            if isinstance(resultado, tuple):
                return (bool(resultado[0]), resultado[1] if len(resultado) > 1 and isinstance(resultado[1], str) else None)
            if isinstance(resultado, str):
                return True, resultado
            return bool(resultado), None
    except Exception:
        pass

    return True, None
