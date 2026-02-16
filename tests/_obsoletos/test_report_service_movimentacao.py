import sys
import types
import importlib


def test_gerar_relatorio_movimentacao_delega_para_modulo(monkeypatch):
    called = {}

    mod = types.ModuleType('movimentomensal')

    def fake_relatorio(numero_mes):
        called['numero_mes'] = numero_mes
        return True

    mod.relatorio_movimentacao_mensal = fake_relatorio

    # Garantir spec para reload
    import importlib.util
    mod.__spec__ = importlib.util.spec_from_loader('movimentomensal', loader=None)
    # Injeta mock ANTES de importar o serviço para evitar side-effects
    sys.modules['movimentomensal'] = mod

    try:
        from services import report_service

        ok = report_service.gerar_relatorio_movimentacao_mensal(7)
        assert ok is True
        assert called.get('numero_mes') == 7
    finally:
        del sys.modules['movimentomensal']
