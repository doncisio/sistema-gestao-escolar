import sys
import os
from types import ModuleType
from typing import Any, cast


def ensure_repo_in_path():
    repo_root = os.path.abspath(os.getcwd())
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


def test_delegates_to_mock():
    ensure_repo_in_path()
    mod = ModuleType('NotaAta')
    called = {'ok': False}

    def fake(bimestre, nivel_ensino, ano_letivo, status_matricula, preencher_nulos):
        called['ok'] = True
        return True

    mod.gerar_relatorio_notas_com_assinatura = fake
    prev = sys.modules.get('NotaAta')
    try:
        sys.modules['NotaAta'] = cast(Any, mod)
        import services.report_service as rs
        assert rs.gerar_relatorio_avancado_com_assinatura('1', 'Fundamental', 2025, None, False) is True
        assert called['ok'] is True
    finally:
        if prev is None:
            del sys.modules['NotaAta']
        else:
            sys.modules['NotaAta'] = prev


def test__impl_uses_pdf_helper(tmp_path):
    ensure_repo_in_path()
    # mock do helper de PDF
    pdf_mod = ModuleType('services.utils.pdf')
    called = {'saved': False}

    def fake_create():
        class B:
            def getvalue(self):
                return b''

            def seek(self, pos):
                pass

        class D:
            def __init__(self):
                pass

            def build(self, elements):
                pass

        return D(), B()

    def fake_salvar(buf):
        called['saved'] = True

    pdf_mod.create_pdf_buffer = fake_create
    pdf_mod.salvar_e_abrir_pdf = fake_salvar
    prev = sys.modules.get('services.utils.pdf')
    try:
        sys.modules['services.utils.pdf'] = cast(Any, pdf_mod)
        import services.report_service as rs

        dados = {'alunos': []}
        result = rs._impl_gerar_relatorio_notas_com_assinatura(dados=dados, bimestre='1', nivel_ensino='Fundamental', ano_letivo=2025)
        assert result is True
        assert called['saved'] is True
    finally:
        if prev is None:
            del sys.modules['services.utils.pdf']
        else:
            sys.modules['services.utils.pdf'] = prev
