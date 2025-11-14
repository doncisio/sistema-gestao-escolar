from utilitarios.conversoes import to_safe_int


def test_to_safe_int():
    assert to_safe_int(None) is None
    assert to_safe_int(5) == 5
    assert to_safe_int(5.9) == 5
    assert to_safe_int('12') == 12
    assert to_safe_int('12.9') == 12
    assert to_safe_int('  7  ') == 7
    assert to_safe_int('abc') is None


if __name__ == '__main__':
    test_to_safe_int()
    print('test_conversoes: OK')
