import sys
import types
import io
import importlib

import pytest

import os
import importlib.util

# importar o módulo `services/report_service.py` por caminho para evitar
# problemas de import quando `services` não for um pacote instalável.
spec = importlib.util.spec_from_file_location('report_service', os.path.join(os.getcwd(), 'services', 'report_service.py'))
report_service = importlib.util.module_from_spec(spec)
if spec and spec.loader:
    # garantir que o root do repositório esteja no sys.path para imports relativos
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    spec.loader.exec_module(report_service)


def test_gerar_lista_notas_delegates_to_mock():
    # preparar mock do módulo legado em sys.modules
    called = {}
    mod = types.ModuleType('Lista_notas')

    def lista_notas():
        called['ok'] = True

    mod.lista_notas = lista_notas
    sys.modules['Lista_notas'] = mod
    try:
        assert report_service.gerar_lista_notas() is True
        assert called.get('ok') is True
    finally:
        # cleanup
        del sys.modules['Lista_notas']


def test__impl_lista_notas_uses_pdf_helpers_and_returns_true():
    # Criar um módulo fake para services.utils.pdf com os helpers esperados
    called = {'salvar': False, 'built': False}

    pdf_mod = types.ModuleType('services.utils.pdf')

    def create_pdf_buffer():
        buf = io.BytesIO()

        class DummyDoc:
            def build(self, elements):
                # marca que build foi chamado
                called['built'] = True

        return DummyDoc(), buf

    def salvar_e_abrir_pdf(buf):
        called['salvar'] = True
        # buf deve oferecer getvalue
        assert hasattr(buf, 'getvalue')

    pdf_mod.create_pdf_buffer = create_pdf_buffer
    pdf_mod.salvar_e_abrir_pdf = salvar_e_abrir_pdf

    # preservar possíveis módulos existentes
    old_services = sys.modules.get('services')
    old_utils = sys.modules.get('services.utils')

    if 'services' not in sys.modules:
        sys.modules['services'] = types.ModuleType('services')
    if 'services.utils' not in sys.modules:
        sys.modules['services.utils'] = types.ModuleType('services.utils')

    sys.modules['services.utils.pdf'] = pdf_mod

    dados = [{'NOME DO ALUNO': 'Alice'}, {'NOME DO ALUNO': 'Bob'}]
    try:
        # chamar a implementação migrada diretamente
        assert report_service._impl_lista_notas(dados_aluno=dados) is True
        assert called['built'] is True
        assert called['salvar'] is True
    finally:
        # cleanup: remover o módulo fake e restaurar o estado anterior
        if 'services.utils.pdf' in sys.modules:
            del sys.modules['services.utils.pdf']
        if old_utils is None and 'services.utils' in sys.modules:
            del sys.modules['services.utils']
        if old_services is None and 'services' in sys.modules:
            del sys.modules['services']
