import sys
import os
import importlib
import tempfile
from types import ModuleType
from typing import Any, cast


def ensure_repo_in_path():
    repo_root = os.path.abspath(os.getcwd())
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


def test_gerar_lista_reuniao_delegates_to_mock():
    """Se um módulo `gerar_lista_reuniao` for injetado em sys.modules, o wrapper deve delegar."""
    ensure_repo_in_path()
    mod = ModuleType('gerar_lista_reuniao')
    called = {'ok': False}

    def fake():
        called['ok'] = True
        return True

    mod.gerar_lista_reuniao = fake
    prev = sys.modules.get('gerar_lista_reuniao')
    try:
        # evitar avisos de analisador em atribuições dinâmicas
        sys.modules['gerar_lista_reuniao'] = cast(Any, mod)

        # importar o serviço e chamar o wrapper
        import services.report_service as rs
        # Garantir que o mock será usado no momento da chamada
        assert rs.gerar_lista_reuniao() is True
        assert called['ok'] is True
    finally:
        # restaurar estado anterior
        if prev is None:
            del sys.modules['gerar_lista_reuniao']
        else:
            sys.modules['gerar_lista_reuniao'] = prev


def test__impl_gerar_lista_reuniao_uses_pdf_helper_and_returns_true(tmp_path):
    """Chama `_impl_gerar_lista_reuniao` com dados injetados e um helper de PDF mockado."""
    ensure_repo_in_path()

    # mock do helper de PDF em services.utils.pdf
    pdf_mod = ModuleType('services.utils.pdf')
    called = {'saved': False}

    def fake_salvar_e_abrir_pdf(buf):
        # receber um BytesIO ou objeto semelhante
        called['saved'] = True

    pdf_mod.salvar_e_abrir_pdf = fake_salvar_e_abrir_pdf
    prev = sys.modules.get('services.utils.pdf')
    try:
        sys.modules['services.utils.pdf'] = cast(Any, pdf_mod)

        # importar o serviço
        import services.report_service as rs

        dados = [
            {'NOME_SERIE': '1', 'NOME_TURMA': 'A', 'TURNO': 'M', 'NOME DO ALUNO': 'Aluno Teste', 'NOME_PROFESSOR': 'Prof X', 'SITUAÇÃO': 'Ativo'}
        ]

        # chamar a implementação diretamente com dados injetados
        result = rs._impl_gerar_lista_reuniao(dados_aluno=dados, ano_letivo=2025, out_dir=str(tmp_path))
        assert result is True
        assert called['saved'] is True
    finally:
        # restaurar/saneamento
        if prev is None:
            del sys.modules['services.utils.pdf']
        else:
            sys.modules['services.utils.pdf'] = prev
