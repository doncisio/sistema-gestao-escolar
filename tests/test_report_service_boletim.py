import sys
import types
import importlib

from services import report_service


def test_gerar_boletim_delega_para_modulo_boletim(monkeypatch):
    # Mudar cwd não é necessário para esse teste

    called = {}

    mod = types.ModuleType('boletim')

    def fake_boletim(aluno_id, ano_letivo_id):
        called['aluno_id'] = aluno_id
        called['ano_letivo_id'] = ano_letivo_id

    mod.boletim = fake_boletim

    # Garantir que importlib.reload não falhe: fornecer __spec__
    import importlib.util
    mod.__spec__ = importlib.util.spec_from_loader('boletim', loader=None)
    sys.modules['boletim'] = mod

    try:
        ok = report_service.gerar_boletim(123, 2025)
        assert ok is True
        assert called.get('aluno_id') == 123
        assert called.get('ano_letivo_id') == 2025
    finally:
        del sys.modules['boletim']
