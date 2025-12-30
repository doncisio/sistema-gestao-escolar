from types import SimpleNamespace
import pytest
from src.utils.horarios_persistence import upsert_horarios


class DummyCursor:
    def __init__(self, should_fail_on_index=None):
        self.executed = []
        self.should_fail_on_index = should_fail_on_index
        self.closed = False

    def execute(self, sql, params=None):
        if self.should_fail_on_index is not None and len(self.executed) == self.should_fail_on_index:
            raise Exception("Simulated SQL error")
        self.executed.append((sql, params))

    def close(self):
        self.closed = True


class DummyConn:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.transaction_started = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def start_transaction(self):
        self.transaction_started = True

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


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
    
    # Verify transaction and cleanup
    assert conn.transaction_started
    assert conn.committed
    assert cursor.closed
    assert conn.closed


def test_upsert_horarios_validates_empty_list(monkeypatch):
    """Testa que lista vazia gera ValueError"""
    monkeypatch.setattr('src.utils.horarios_persistence.conectar_bd', lambda: None)
    
    with pytest.raises(ValueError, match="não pode ser vazia"):
        upsert_horarios([])


def test_upsert_horarios_validates_required_fields(monkeypatch):
    """Testa validação de campos obrigatórios"""
    cursor = DummyCursor()
    conn = DummyConn(cursor)
    monkeypatch.setattr('src.utils.horarios_persistence.conectar_bd', lambda: conn)
    
    # Faltando campo 'dia'
    dados_invalidos = [
        {'turma_id': 1, 'horario': '07:10-08:00', 'valor': 'MATEMÁTICA'}
    ]
    
    with pytest.raises(ValueError, match="campo obrigatório 'dia'"):
        upsert_horarios(dados_invalidos)


def test_upsert_horarios_validates_none_values(monkeypatch):
    """Testa que campos obrigatórios não podem ser None"""
    cursor = DummyCursor()
    conn = DummyConn(cursor)
    monkeypatch.setattr('src.utils.horarios_persistence.conectar_bd', lambda: conn)
    
    dados_invalidos = [
        {'turma_id': None, 'dia': 'Segunda', 'horario': '07:10-08:00', 'valor': 'MATEMÁTICA'}
    ]
    
    with pytest.raises(ValueError, match="campo obrigatório 'turma_id'"):
        upsert_horarios(dados_invalidos)


def test_upsert_horarios_validates_dict_type(monkeypatch):
    """Testa que itens devem ser dicionários"""
    cursor = DummyCursor()
    conn = DummyConn(cursor)
    monkeypatch.setattr('src.utils.horarios_persistence.conectar_bd', lambda: conn)
    
    dados_invalidos = ["string_invalida"]
    
    with pytest.raises(ValueError, match="não é um dicionário válido"):
        upsert_horarios(dados_invalidos)


def test_upsert_horarios_rollback_on_error(monkeypatch):
    """Testa que rollback é executado em caso de erro SQL"""
    # Cursor que vai falhar no segundo item
    cursor = DummyCursor(should_fail_on_index=1)
    conn = DummyConn(cursor)
    monkeypatch.setattr('src.utils.horarios_persistence.conectar_bd', lambda: conn)
    
    dados = [
        {'turma_id': 1, 'dia': 'Segunda', 'horario': '07:10-08:00', 'valor': 'MATEMÁTICA'},
        {'turma_id': 2, 'dia': 'Terça', 'horario': '08:00-08:50', 'valor': 'PORTUGUÊS'},
    ]
    
    with pytest.raises(Exception, match="Simulated SQL error"):
        upsert_horarios(dados)
    
    # Verificar que rollback foi chamado
    assert conn.rolled_back
    assert not conn.committed
    # Verificar que apenas 1 SQL foi executado antes do erro
    assert len(cursor.executed) == 1
    # Recursos devem ser limpos
    assert cursor.closed
    assert conn.closed


def test_upsert_horarios_connection_error(monkeypatch):
    """Testa tratamento de erro ao conectar ao banco"""
    monkeypatch.setattr('src.utils.horarios_persistence.conectar_bd', lambda: None)
    
    dados = [
        {'turma_id': 1, 'dia': 'Segunda', 'horario': '07:10-08:00', 'valor': 'MATEMÁTICA'}
    ]
    
    with pytest.raises(RuntimeError, match="Não foi possível conectar"):
        upsert_horarios(dados)
