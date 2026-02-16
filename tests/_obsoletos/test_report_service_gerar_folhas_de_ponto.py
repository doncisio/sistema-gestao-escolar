import sys
import types
from importlib.machinery import ModuleSpec


def test_gerar_folhas_de_ponto_delega_para_modulo_injetado():
    # Preparar mock do módulo legado e injetar em sys.modules antes de importar o service
    called = {}

    def fake_gerar(*args, **kwargs):
        called['ok'] = True
        return True

    mod = types.ModuleType('preencher_folha_ponto')
    mod.__spec__ = ModuleSpec('preencher_folha_ponto', None)
    mod.gerar_folhas_de_ponto = fake_gerar

    sys.modules['preencher_folha_ponto'] = mod

    try:
        # Importar o serviço após injetar o mock
        import importlib
        rs = importlib.import_module('services.report_service')

        # Chamar a função delegadora
        resultado = rs.gerar_folhas_de_ponto()

        assert resultado is True
        assert called.get('ok', False) is True
    finally:
        # Limpar sys.modules para não poluir outros testes
        try:
            del sys.modules['preencher_folha_ponto']
        except KeyError:
            pass