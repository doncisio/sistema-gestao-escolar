import sys
import types
import importlib
import importlib.util


def test_gerar_lista_notas_delega_para_modulo_mock():
    # Injetar mock antes de importar o serviço
    mod = types.ModuleType('Lista_notas')
    called = {'ok': False}

    def gerar():
        called['ok'] = True

    mod.lista_notas = gerar
    mod.__spec__ = importlib.util.spec_from_loader('Lista_notas', loader=None)
    sys.modules['Lista_notas'] = mod

    rs = importlib.import_module('services.report_service')

    assert rs.gerar_lista_notas() is True
    assert called['ok'] is True

    sys.modules.pop('Lista_notas', None)
