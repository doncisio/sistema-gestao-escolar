from src.utils.safe import converter_para_int_seguro, _safe_get, _safe_slice


def test_converter_para_int_seguro():
    assert converter_para_int_seguro(None) == 0
    assert converter_para_int_seguro(" 123 ") == 123
    assert converter_para_int_seguro("12.0") == 12


def test_safe_get_and_slice():
    row = (1, 2, 3)
    assert _safe_get(row, 1) == 2
    assert _safe_get(None, 0) is None
    d = {"0": "zero", 1: "one"}
    assert _safe_get(d, 1) == "one"
    assert _safe_slice(row, 0, 2) == [1, 2]
    assert _safe_slice(None, 0, 3) == [None, None, None]
