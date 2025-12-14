from typing import Any, List


def converter_para_int_seguro(valor: Any) -> int:
    """
    Converte qualquer valor para int de forma segura.
    Lida com None, strings, floats, Decimal, etc.
    Retorna 0 em caso de falha.
    """
    try:
        if valor is None:
            return 0
        if isinstance(valor, int):
            return valor
        if isinstance(valor, float):
            return int(valor)
        if isinstance(valor, str):
            v = valor.strip()
            if v == "":
                return 0
            try:
                return int(v)
            except Exception:
                try:
                    return int(float(v))
                except Exception:
                    return 0
        return int(valor)
    except Exception:
        return 0


def _safe_get(row: Any, index: int, default: Any = None) -> Any:
    """
    Retorna de forma segura o valor na posição `index` de `row`.
    - Se `row` for None retorna `default`.
    - Se for tuple/list retorna o elemento ou `default` se fora do alcance.
    - Se for dict tenta por chave numérica ou nomeada; se não existir, retorna `default`.
    """
    if row is None:
        return default
    try:
        if isinstance(row, dict):
            if index in row:
                return row[index]
            key = str(index)
            return row.get(key, default)
        if isinstance(row, (list, tuple)):
            try:
                return row[index]
            except Exception:
                return default
        if index == 0:
            return row
    except Exception:
        return default
    return default


def _safe_slice(row: Any, start: int, end: int) -> List[Any]:
    """
    Retorna uma fatia segura de `row` como lista entre `start` (inclusive) e `end` (exclusive).
    Se `row` for tuple/list retorna a slice; se None retorna lista de Nones do tamanho solicitado.
    """
    length = max(0, end - start)
    if row is None:
        return [None] * length
    try:
        if isinstance(row, (list, tuple)):
            s = list(row[start:end])
            if len(s) < length:
                s.extend([None] * (length - len(s)))
            return s
        if isinstance(row, dict):
            out = []
            for i in range(start, end):
                out.append(_safe_get(row, i, None))
            return out
        if length == 1:
            return [row]
    except Exception:
        pass
    return [None] * length
