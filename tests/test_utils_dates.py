from datetime import datetime, date
from src.utils.dates import formatar_data, formatar_data_extenso, nome_mes_pt, periodo_mes_referencia


def test_formatar_data_from_datetime():
    d = datetime(2025, 10, 3)
    assert formatar_data(d) == "03/10/2025"


def test_formatar_data_from_string():
    assert formatar_data("2025-10-03") == "03/10/2025"


def test_formatar_data_extenso():
    d = date(2025, 10, 3)
    assert formatar_data_extenso(d) == "3 de outubro de 2025"


def test_nome_mes_pt():
    assert nome_mes_pt(1) == "Janeiro"
    assert nome_mes_pt(1, capitalize=False) == "janeiro"


def test_periodo_mes_referencia():
    s = periodo_mes_referencia(2, 2025)
    assert "1 a" in s and "de Fevereiro de 2025" in s
