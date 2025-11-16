import sys
import types
import importlib
import importlib.util


def test_gerar_lista_frequencia_delega_para_modulo_mock():
    # Injetar mock antes de importar o serviço
    mod = types.ModuleType('lista_frequencia')
    called = {'ok': False}

    def gerar():
        called['ok'] = True

    mod.lista_frequencia = gerar
    mod.__spec__ = importlib.util.spec_from_loader('lista_frequencia', loader=None)
    sys.modules['lista_frequencia'] = mod

    rs = importlib.import_module('services.report_service')

    assert rs.gerar_lista_frequencia() is True
    assert called['ok'] is True

    sys.modules.pop('lista_frequencia', None)
