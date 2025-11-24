import sys
import os
sys.path.insert(0, os.path.abspath(os.getcwd()))

# stub do helper de PDF (forçar que não retorne path)
import gerarPDF

def fake_helper_return_none(buffer, *args, **kwargs):
    print('[STUB helper] salvar_e_abrir_pdf called — returning None to force gerenciador')
    return None

gerarPDF.salvar_e_abrir_pdf = fake_helper_return_none

# stub do gerenciador_documentos para observar a chamada
from utilitarios import gerenciador_documentos

def fake_salvar(caminho_arquivo, tipo_documento, aluno_id=None, funcionario_id=None, finalidade=None, descricao=None, pasta_drive=None):
    print('[STUB gerenciador] salvar_documento_sistema called with:', caminho_arquivo, tipo_documento, funcionario_id, finalidade, descricao)
    return True, 'Simulado', 'http://fake/link'

# substituir função no módulo
gerenciador_documentos.salvar_documento_sistema = fake_salvar

import Lista_contatos_responsaveis as m

print('Chamando gerar_pdf_contatos(2025) com helper forçado a retornar None...')
res = m.gerar_pdf_contatos(2025)
print('Resultado da função:', res)
