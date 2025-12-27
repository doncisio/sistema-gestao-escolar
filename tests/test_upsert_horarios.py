from types import SimpleNamespace
import pytest
from src.utils.horarios_persistence import upsert_horarios


class DummyCursor:
    def __init__(self):
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def close(self):
        pass


class DummyConn:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        pass


def test_upsert_horarios_executes_on_duplicate(monkeypatch):
    cursor = DummyCursor()
    conn = DummyConn(cursor)

    # mock conectar_bd to return our dummy connection
    monkeypatch.setattr('src.utils.horarios_persistence.conectar_bd', lambda: conn)

    dados = [
        {'turma_id': 1, 'dia': 'Segunda', 'horario': '07:10-08:00', 'valor': 'MATEMÁTICA (João)', 'disciplina_id': 2, 'professor_id': 10},
        {'turma_id': 1, 'dia': 'Terça', 'horario': '08:00-08:50', 'valor': 'LÍNGUA PORTUGUESA', 'disciplina_id': 1, 'professor_id': None},
    ]

    count = upsert_horarios(dados)
    assert count == 2

    # Ensure we executed SQL for each row
    assert len(cursor.executed) == 2

    sql0, params0 = cursor.executed[0]
    assert 'ON DUPLICATE KEY UPDATE' in sql0.upper()
    assert params0[0] == 1
    assert params0[4] == 2  # disciplina_id
    assert params0[5] == 10  # professor_id

    sql1, params1 = cursor.executed[1]
    assert params1[4] == 1
    assert params1[5] is None
