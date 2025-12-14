import os
import tempfile
from services import report_service as rs


def test_impl_gerar_relatorio_series_faltantes(monkeypatch):
    # preparar dados simples
    alunos_ativos = [
        {'aluno_id': 1, 'nome_aluno': 'Alice', 'serie_atual': 5},
        {'aluno_id': 2, 'nome_aluno': 'Bruno', 'serie_atual': 3},
    ]
    historico_lookup = {
        1: [
            {'serie_id': 3, 'situacao_final': 'Promovido(a)'},
            {'serie_id': 4, 'situacao_final': 'Promovido(a)'}
        ],
        2: [
            {'serie_id': 3, 'situacao_final': 'Promovido(a)'}
        ]
    }

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

    import src.services.utils.pdf as pdfmod
    monkeypatch.setattr(pdfmod, 'salvar_e_abrir_pdf', fake_salvar)

    result = rs._impl_gerar_relatorio_series_faltantes(alunos_ativos=alunos_ativos, historico_lookup=historico_lookup, out_dir=tempfile.gettempdir())
    assert result is True
    assert 'path' in saved
    assert os.path.isfile(saved['path'])
    try:
        os.remove(saved['path'])
    except Exception:
        pass
