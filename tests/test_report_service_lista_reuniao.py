import sys
import types
import importlib
import importlib.util


def test_gerar_lista_reuniao_delega_para_modulo_mock():
    # Criar mock do módulo e injetar em sys.modules antes de importar o serviço
    mod = types.ModuleType('gerar_lista_reuniao')
    called = {'ok': False}

    def gerar():
        called['ok'] = True

    mod.gerar_lista_reuniao = gerar
    # Definir __spec__ para evitar problemas com importlib.reload
    mod.__spec__ = importlib.util.spec_from_loader('gerar_lista_reuniao', loader=None)
    sys.modules['gerar_lista_reuniao'] = mod

    # Importar o serviço após injetar o mock
    rs = importlib.import_module('services.report_service')

    # Chamar a função do serviço - deve delegar para o mock
    assert rs.gerar_lista_reuniao() is True
    assert called['ok'] is True

    # Limpar o mock do sys.modules
    sys.modules.pop('gerar_lista_reuniao', None)
