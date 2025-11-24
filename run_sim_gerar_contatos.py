import sys
import os
# garantir que o repositório atual esteja no path
sys.path.insert(0, os.path.abspath(os.getcwd()))

from utilitarios import gerenciador_documentos

# stub para evitar autenticação/BD durante a simulação
def fake_salvar(caminho_arquivo, tipo_documento, aluno_id=None, funcionario_id=None, finalidade=None, descricao=None, pasta_drive=None):
    print("[STUB] salvar_documento_sistema called with:", caminho_arquivo, tipo_documento, funcionario_id, finalidade, descricao)
    return True, "Simulado", "http://fake/link"

gerenciador_documentos.salvar_documento_sistema = fake_salvar

import Lista_contatos_responsaveis as m

print("Chamando gerar_pdf_contatos(2025)...")
res = m.gerar_pdf_contatos(2025)
print("Resultado da função:", res)
