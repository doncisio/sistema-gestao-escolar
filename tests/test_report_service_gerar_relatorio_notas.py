import sys
import types
import importlib.machinery

# Inject a mock NotaAta into sys.modules before importing the service
def test_delegates_to_notaatta():
    # Prepare mock and inject inside the test to avoid test collection/order issues
    mock = types.SimpleNamespace()

    def fake_gerar(*args, **kwargs):
        fake_gerar.called = True
        fake_gerar.args = (args, kwargs)
        return "ok"

    mock.gerar_relatorio_notas = fake_gerar
    mock.__spec__ = importlib.machinery.ModuleSpec('NotaAta', None)

    # Remove any existing real module and inject the mock
    if 'NotaAta' in sys.modules:
        del sys.modules['NotaAta']
    sys.modules['NotaAta'] = mock

    # Force re-import of the services module so it observes the injected mock
    if 'services.report_service' in sys.modules:
        del sys.modules['services.report_service']
    if 'services' in sys.modules:
        del sys.modules['services']

    from services import report_service

    # Call the service wrapper; it should use the injected mock
    res = report_service.gerar_relatorio_notas(1, nivel_ensino='Fundamental')
    assert res is True
    assert getattr(fake_gerar, 'called', False) is True
