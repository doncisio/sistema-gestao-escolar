import os
import tempfile
from services import report_service as rs
import pandas as pd


def make_sample_dados():
    # criar duas turmas com alguns alunos
    dados = [
        {'NOME_SERIE': '1º', 'NOME_TURMA': 'A', 'TURNO': 'Matutino', 'NOME_PROFESSOR': 'Prof A', 'SITUAÇÃO': 'Ativo', 'NOME DO ALUNO': 'Aluno1'},
        {'NOME_SERIE': '1º', 'NOME_TURMA': 'A', 'TURNO': 'Matutino', 'NOME_PROFESSOR': 'Prof A', 'SITUAÇÃO': 'Ativo', 'NOME DO ALUNO': 'Aluno2'},
        {'NOME_SERIE': '2º', 'NOME_TURMA': 'B', 'TURNO': 'Vespertino', 'NOME_PROFESSOR': 'Prof B', 'SITUAÇÃO': 'Inativo', 'NOME DO ALUNO': 'AlunoX'},
    ]
    return dados


def test_impl_gerar_lista_reuniao_creates_pdf(monkeypatch, tmp_path):
    dados = make_sample_dados()
    saved = {}

    def fake_salvar(buffer_io, filename=None):
        fd, path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        try:
            buffer_io.seek(0)
        except Exception:
            pass
        data = buffer_io.read() if hasattr(buffer_io, 'read') else buffer_io.getvalue()
        with open(path, 'wb') as f:
            f.write(data)
        saved['path'] = path
        return path

    import services.utils.pdf as pdfmod
    monkeypatch.setattr(pdfmod, 'salvar_e_abrir_pdf', fake_salvar)

    result = rs._impl_gerar_lista_reuniao(dados_aluno=dados, out_dir=str(tmp_path))
    assert result is True
    assert 'path' in saved
    assert os.path.isfile(saved['path'])
    try:
        os.remove(saved['path'])
    except Exception:
        pass
