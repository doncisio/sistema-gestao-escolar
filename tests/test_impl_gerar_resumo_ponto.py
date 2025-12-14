import os
import io
import tempfile
from reportlab.pdfgen import canvas
from services import report_service as rs


def make_blank_pdf(path):
    c = canvas.Canvas(path)
    c.drawString(100, 750, "Base PDF")
    c.showPage()
    c.save()


def test_impl_gerar_resumo_ponto_with_mocked_bases(tmp_path, monkeypatch):
    # criar 3 PDFs base mínimos
    base2 = tmp_path / "base2.pdf"
    base3 = tmp_path / "base3.pdf"
    base4 = tmp_path / "base4.pdf"
    make_blank_pdf(str(base2))
    make_blank_pdf(str(base3))
    make_blank_pdf(str(base4))

    # dados de exemplo: 5 profissionais apenas para testar fluxo
    profissionais = [
        {"matricula": "100", "nome": "Ana Silva", "situacao_funcional": "Ativo", "funcao": "Prof", "carga_horaria": "20", "turno": "Matutino", "p": 20, "f": 0, "fj": 0, "observacao": ""},
        {"matricula": "101", "nome": "Bruno Souza", "situacao_funcional": "Ativo", "funcao": "Prof", "carga_horaria": "20", "turno": "Vespertino", "p": 20, "f": 1, "fj": 0, "observacao": ""},
    ]
    escola = {"nome": "ESCOLA MUNICIPAL TESTE", "endereco": "Rua X", "inep": "123", "cnpj": "111"}

    # capturar o caminho salvo pelo helper
    saved = {}

    def fake_salvar(buffer_io, filename=None):
        # escrever em arquivo temporário para verificar saída
        fd, path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        with open(path, 'wb') as f:
            # buffer_io may be BytesIO
            try:
                buffer_io.seek(0)
            except Exception:
                pass
            f.write(buffer_io.read() if hasattr(buffer_io, 'read') else buffer_io.getvalue())
        saved['path'] = path
        return path

    # monkeypatch helper
    import src.services.utils.pdf as pdfmod
    monkeypatch.setattr(pdfmod, 'salvar_e_abrir_pdf', fake_salvar)

    # executar a implementação migrada com bases injetadas e dados em memória
    result = rs._impl_gerar_resumo_ponto(1, 2025, profissionais=profissionais, escola=escola,
                                         base2_path=str(base2), base3_path=str(base3), base4_path=str(base4))

    assert result is True
    assert 'path' in saved
    assert os.path.isfile(saved['path'])
    # cleanup
    try:
        os.remove(saved['path'])
    except Exception:
        pass
