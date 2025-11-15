import sys
import types
import os
import importlib

from services import report_service


def test_gerar_crachas_success(tmp_path, monkeypatch):
    # Mudar cwd para um diretório temporário
    monkeypatch.chdir(tmp_path)

    # Criar um módulo falso 'gerar_cracha' que cria a pasta de saída
    mod = types.ModuleType('gerar_cracha')

    def fake_gerar():
        out = os.path.join(os.getcwd(), 'Cracha_Anos_Iniciais')
        os.makedirs(out, exist_ok=True)

    mod.gerar_crachas_para_todos_os_alunos = fake_gerar

    # Inserir no sys.modules para que import funcione
    # When report_service does importlib.reload(), the module must have a __spec__.
    import importlib.util
    mod.__spec__ = importlib.util.spec_from_loader('gerar_cracha', loader=None)
    sys.modules['gerar_cracha'] = mod

    # Execute o serviço
    caminho = report_service.gerar_crachas_para_todos_os_alunos()

    assert os.path.isdir(caminho), "Pasta de crachá não foi criada"

    # Cleanup
    del sys.modules['gerar_cracha']


def test_gerar_crachas_importerror(tmp_path, monkeypatch):
    # Mudar cwd para tmp
    monkeypatch.chdir(tmp_path)

    # Garantir que não exista módulo
    if 'gerar_cracha' in sys.modules:
        del sys.modules['gerar_cracha']

    # Também garantir que scripts_nao_utilizados não contenha o módulo
    scripts_dir = os.path.join(os.getcwd(), 'scripts_nao_utilizados')
    if os.path.isdir(scripts_dir):
        # assegurar vazio (não criar módulos)
        pass

    try:
        try:
            report_service.gerar_crachas_para_todos_os_alunos()
            assert False, "Esperava ImportError quando gerar_cracha não está presente"
        except ImportError:
            # esperado
            pass
    finally:
        if 'gerar_cracha' in sys.modules:
            del sys.modules['gerar_cracha']


def test_relatorio_services_delegation(monkeypatch):
    # Mock NotaAta and relatorio_pendencias modules
    nota_mod = types.ModuleType('NotaAta')
    def fake_relatorio(*_, **__):
        return True
    nota_mod.gerar_relatorio_notas_com_assinatura = fake_relatorio
    sys.modules['NotaAta'] = nota_mod

    pend_mod = types.ModuleType('relatorio_pendencias')
    pend_mod.gerar_pdf_pendencias = fake_relatorio
    sys.modules['relatorio_pendencias'] = pend_mod

    # Call service functions
    ok1 = report_service.gerar_relatorio_avancado_com_assinatura('1º bimestre', 'iniciais', 2025, 'Ativo', False)
    ok2 = report_service.gerar_relatorio_pendencias('3º bimestre', 'iniciais', 2025, escola_id=60)

    assert ok1 is True
    assert ok2 is True

    # Cleanup
    del sys.modules['NotaAta']
    del sys.modules['relatorio_pendencias']


if __name__ == '__main__':
    # Run tests without pytest for environments without pytest installed
    import tempfile
    from types import SimpleNamespace

    tmp = tempfile.TemporaryDirectory()
    try:
        class M:
            pass

        # Emulate pytest fixtures calls
        monkeypatch = importlib.import_module('builtins')
    except Exception:
        pass

    print('Run this file with pytest for best results: pytest -q tests/test_report_service.py')
