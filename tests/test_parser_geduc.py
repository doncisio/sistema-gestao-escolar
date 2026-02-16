import pytest
from pathlib import Path
from src.importadores.geduc_horarios import parse_horario_por_turma


def test_parse_horario_por_turma_local():
    # caminho esperado do HTML exportado do GEDUC (ajuste se necessário)
    sample = Path(r'c:/gestao/historico geduc/horario por turma.html')
    if not sample.exists():
        pytest.skip(f"Arquivo de exemplo não encontrado: {sample}")

    parsed = parse_horario_por_turma(sample)
    assert isinstance(parsed, dict)
    assert 'rows' in parsed
    assert isinstance(parsed['rows'], list)
    assert len(parsed['rows']) > 0
