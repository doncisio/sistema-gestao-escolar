import sys
import importlib
from types import ModuleType


def test_gerar_lista_reuniao_delegates_to_mock():
    mod = ModuleType('gerar_lista_reuniao')
    mod.__spec__ = object()
    called = {'v': False}

    def fake():
        called['v'] = True
        return True

    mod.gerar_lista_reuniao = fake
    sys.modules['gerar_lista_reuniao'] = mod

    import src.services.report_service as rs
    importlib.reload(rs)

    res = rs.gerar_lista_reuniao()
    assert res is True
    assert called['v'] is True

    sys.modules.pop('gerar_lista_reuniao', None)
