import unicodedata
import re

import pytest

from types import SimpleNamespace


class FakeRoot:
    def configure(self, **kwargs):
        return None

    def focus_force(self):
        return None

    def transient(self, *a, **k):
        return None

    def grab_set(self):
        return None

    def protocol(self, *a, **k):
        return None

    def winfo_rootx(self):
        return 0

    def winfo_rooty(self):
        return 0

    def winfo_width(self):
        return 800

    def winfo_height(self):
        return 600


class FakeCell:
    def __init__(self, value):
        self._v = value

    def get(self):
        return self._v


def test_salvar_horarios_flow(monkeypatch):
    # Antes de importar o módulo, substituir tkinter/ttk por stubs para evitar abrir UI
    import sys
    import types

    class FakeWidget:
        def __init__(self, *a, **k):
            pass
        def pack(self, *a, **k):
            return None
        def pack_forget(self, *a, **k):
            return None
        def grid(self, *a, **k):
            return None
        def grid_rowconfigure(self, *a, **k):
            return None
        def grid_columnconfigure(self, *a, **k):
            return None
        def destroy(self, *a, **k):
            return None
        def bind(self, *a, **k):
            return None
        def insert(self, *a, **k):
            return None
        def delete(self, *a, **k):
            return None
        def config(self, *a, **k):
            return None
        def configure(self, *a, **k):
            return None
        def winfo_children(self, *a, **k):
            return []
        def create_window(self, *a, **k):
            return None
        def bbox(self, *a, **k):
            return (0, 0, 0, 0)
        def yview(self, *a, **k):
            return None
        def xview(self, *a, **k):
            return None
        def set(self, *a, **k):
            return None

    class FakeEntry(FakeWidget):
        def get(self):
            return ''

    class FakeCombobox(FakeWidget):
        def __init__(self, *a, **k):
            self._v = ''
        def get(self):
            return self._v
        def set(self, v):
            self._v = v

    fake_tk = types.ModuleType('tkinter')
    fake_tk.Frame = FakeWidget
    fake_tk.Label = FakeWidget
    fake_tk.Entry = FakeEntry
    fake_tk.Canvas = FakeWidget
    fake_tk.Toplevel = FakeWidget
    fake_tk.Button = FakeWidget
    fake_tk.Scrollbar = FakeWidget
    fake_tk.StringVar = lambda *a, **k: types.SimpleNamespace(get=lambda: '', set=lambda v: None)
    fake_tk.END = 'end'
    # Constantes comumente usadas
    fake_tk.LEFT = 'left'
    fake_tk.RIGHT = 'right'
    fake_tk.TOP = 'top'
    fake_tk.BOTTOM = 'bottom'
    fake_tk.BOTH = 'both'
    fake_tk.X = 'x'
    fake_tk.Y = 'y'
    fake_tk.N = 'n'
    fake_tk.S = 's'
    fake_tk.E = 'e'
    fake_tk.W = 'w'

    fake_ttk = types.ModuleType('tkinter.ttk')
    fake_ttk.Combobox = FakeCombobox
    fake_ttk.Scrollbar = FakeWidget
    fake_ttk.Button = FakeWidget

    # messagebox/filedialog simples como módulos
    fake_msg = types.ModuleType('tkinter.messagebox')
    fake_msg.showwarning = lambda *a, **k: None
    fake_msg.showinfo = lambda *a, **k: None
    fake_msg.showerror = lambda *a, **k: None
    fake_msg.askyesno = lambda *a, **k: False

    fake_fd = types.ModuleType('tkinter.filedialog')
    fake_fd.asksaveasfilename = lambda *a, **k: ''

    # Injeta nos módulos para quando src.interfaces.horarios_escolares fizer import tkinter/ttk
    monkeypatch.setitem(sys.modules, 'tkinter', fake_tk)
    monkeypatch.setitem(sys.modules, 'tkinter.ttk', fake_ttk)
    monkeypatch.setitem(sys.modules, 'tkinter.messagebox', fake_msg)
    monkeypatch.setitem(sys.modules, 'tkinter.filedialog', fake_fd)

    # Agora importar o módulo sob teste
    import importlib
    mod = importlib.import_module('src.interfaces.horarios_escolares')
    importlib.reload(mod)
    from src.interfaces.horarios_escolares import InterfaceHorariosEscolares

    # Prevent GUI messageboxes from popping (redundante, mas seguro)
    monkeypatch.setattr(mod.messagebox, 'showwarning', lambda *a, **k: None)
    monkeypatch.setattr(mod.messagebox, 'showinfo', lambda *a, **k: None)
    monkeypatch.setattr(mod.messagebox, 'showerror', lambda *a, **k: None)

    # Make conectar_bd() return None so carregar_dados_iniciais uses fallbacks
    monkeypatch.setattr(mod, 'conectar_bd', lambda: None)

    # Instantiate with a dummy root to avoid creating real Toplevel windows
    dummy_root = FakeRoot()
    ih = InterfaceHorariosEscolares(root=dummy_root)

    # Prepare controlled test state
    ih.turma_atual = 'Turma Teste'
    ih.turma_id = 123
    ih.turno_atual = 'Matutino'
    ih.horarios_matutino = ['08:00-08:50']
    ih.dias_semana = ['Segunda']

    # Provide disciplines and professors to be matched
    ih.disciplinas = [{'id': 10, 'nome': 'MATEMÁTICA'}]
    ih.professores = [{'id': 20, 'nome': 'João Silva'}]

    # Populate a single cell with a discipline+professor text
    ih.celulas_horario = {
        (1, 1): FakeCell('MATEMÁTICA (João)')
    }

    # Capture calls to upsert_horarios
    captured = []

    def fake_upsert(rows):
        captured.extend(rows)
        return len(rows)

    monkeypatch.setattr('src.utils.horarios_persistence.upsert_horarios', fake_upsert)

    # Call salvar_horarios (function under test)
    ih.salvar_horarios()

    # Assertions: one row persisted with matched disciplina_id and professor_id
    assert len(captured) == 1
    row = captured[0]
    assert row['turma_id'] == 123
    assert row['dia'] == 'Segunda'
    assert row['horario'] == '08:00-08:50'
    assert row['valor'] == 'MATEMÁTICA (João)'
    assert row['disciplina_id'] == 10
    assert row['professor_id'] == 20
