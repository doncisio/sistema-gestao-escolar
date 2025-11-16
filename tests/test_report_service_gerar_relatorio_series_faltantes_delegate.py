import sys
import importlib
from types import ModuleType


def test_gerar_relatorio_series_faltantes_delegates_to_mock():
    mod = ModuleType('gerar_relatorio_series_faltantes')
    mod.__spec__ = object()
    called = {'v': False}

    def fake():
        called['v'] = True
        return True

    mod.gerar_relatorio_series_faltantes = fake
    sys.modules['gerar_relatorio_series_faltantes'] = mod

    import services.report_service as rs
    importlib.reload(rs)

    res = rs.gerar_relatorio_series_faltantes()
    assert res is True
    assert called['v'] is True

    sys.modules.pop('gerar_relatorio_series_faltantes', None)
