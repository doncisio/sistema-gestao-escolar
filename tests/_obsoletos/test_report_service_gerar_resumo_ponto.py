import sys
import types
import importlib.machinery

# Inject mock before importing service
mock = types.SimpleNamespace()

def fake_gerar(mes, ano, *args, **kwargs):
    fake_gerar.called = True
    fake_gerar.args = (mes, ano)
    return True

mock.gerar_resumo_ponto = fake_gerar
mock.__spec__ = importlib.machinery.ModuleSpec('gerar_resumo_ponto', None)
sys.modules['gerar_resumo_ponto'] = mock

from services import report_service


def test_delegates_to_gerar_resumo_ponto():
    res = report_service.gerar_resumo_ponto(1, 2025)
    assert res is True
    assert getattr(fake_gerar, 'called', False) is True
