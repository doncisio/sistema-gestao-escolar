import importlib
import sys
import types
from types import ModuleType


def make_mock_module(func_name='lista_frequencia'):
    m = ModuleType('gerar_tabela_frequencia')
    def lista_frequencia():
        lista_frequencia.called = True
        return True
    setattr(m, func_name, lista_frequencia)
    # Provide a ModuleSpec for tests that expect it
    m.__spec__ = types.SimpleNamespace(name='gerar_tabela_frequencia')
    return m


def test_delegates_to_injected_mock(tmp_path, monkeypatch):
    # Inject mock module into sys.modules before importing the service
    mock_mod = make_mock_module()
    sys.modules['gerar_tabela_frequencia'] = mock_mod

    # (Re)import the service module to ensure it uses the injected mock
    rs = importlib.import_module('services.report_service')
    importlib.reload(rs)

    # Call the wrapper
    result = rs.gerar_tabela_frequencia()

    assert result is True
    assert getattr(mock_mod, 'lista_frequencia', None) is not None
    assert getattr(mock_mod.lista_frequencia, 'called', False) is True
