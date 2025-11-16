import importlib.util
import os
import sys
import types
import io
from typing import Any, cast


def _load_report_service():
    repo_root = os.getcwd()
    # garantir que imports do projeto (ex: config_logs) sejam resolvidos
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    path = os.path.join(repo_root, 'services', 'report_service.py')
    spec = importlib.util.spec_from_file_location('services.report_service', path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Não foi possível criar spec para {path}")
    mod = importlib.util.module_from_spec(spec)
    # mypy/pylance: spec is not None and spec.loader is not None here
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def test_gerar_folhas_de_ponto_delegates_to_mock():
    fake = types.ModuleType('preencher_folha_ponto')

    called = {'ok': False}

    def fake_gerar(*args, **kwargs):
        called['ok'] = True
        return True

    cast(Any, fake).gerar_folhas_de_ponto = fake_gerar

    sys.modules['preencher_folha_ponto'] = fake
    try:
        rs = _load_report_service()
        assert rs.gerar_folhas_de_ponto() is True
        assert called['ok'] is True
    finally:
        sys.modules.pop('preencher_folha_ponto', None)


def test__impl_gerar_folhas_de_ponto_uses_pdf_helpers_and_returns_true():
    # preparar um helper de PDF falso
    pdf_mod = types.ModuleType('services.utils.pdf')

    class DummyDoc:
        def __init__(self):
            self.built = False

        def build(self, elements):
            self.built = True

    created = {'saved': False}

    def create_pdf_buffer():
        return (DummyDoc(), io.BytesIO())

    def salvar_e_abrir_pdf(buf):
        # buf pode ser BytesIO ou objeto com getvalue
        created['saved'] = True

    cast(Any, pdf_mod).create_pdf_buffer = create_pdf_buffer
    cast(Any, pdf_mod).salvar_e_abrir_pdf = salvar_e_abrir_pdf

    # injetar o helper antes de carregar o serviço
    sys.modules['services.utils.pdf'] = pdf_mod
    try:
        rs = _load_report_service()
        profissionais = [{'nome': 'Fulano', 'funcao': 'Professor'}]
        result = rs._impl_gerar_folhas_de_ponto(profissionais=profissionais, mes=1, ano=2025)
        assert result is True
        assert created['saved'] is True
    finally:
        sys.modules.pop('services.utils.pdf', None)
