import json
import unicodedata
import re
from pathlib import Path
import pytest


def _norm(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^0-9A-Za-z\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip().upper()


@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("Matemática (Prof. João)", "MATEMATICA PROF JOAO"),
        (" Língua Portuguesa ", "LINGUA PORTUGUESA"),
        ("Ciências/História", "CIENCIAS HISTORIA"),
        ("José-Álvaro", "JOSE ALVARO"),
        ("", ""),
        (None, "")
    ],
)
def test_norm_examples(input_text, expected):
    assert _norm(input_text) == expected


def test_mapeamentos_json_io(tmp_path):
    data = {
        "disciplinas": {"MATEMATICA": 2, "LINGUA PORTUGUESA": 1},
        "professores": {"JOAO SILVA": 10}
    }

    ddir = tmp_path / "historico_geduc_imports"
    ddir.mkdir()
    fpath = ddir / "mapeamentos_horarios.json"

    # write
    fpath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    # read back
    txt = fpath.read_text(encoding='utf-8')
    loaded = json.loads(txt)

    assert loaded == data

    # Ensure normalized keys can be matched using _norm
    key = _norm('Matemática')
    assert key in loaded['disciplinas']
    assert loaded['disciplinas'][key] == 2
