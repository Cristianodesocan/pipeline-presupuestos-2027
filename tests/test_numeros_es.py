import pytest

from _comun.numeros_es import a_numero, es_numero


@pytest.mark.parametrize("token, esperado", [
    ("4.536.754.790", (4536754790, False)),
    ("38,09", (38.09, False)),
    ("0,71-", (-0.71, False)),
    ("100,00-", (-100.0, False)),
    ("0", (0, False)),
    ("-", (None, False)),
    ("110,02*", (110.02, True)),
    ("100", (100, False)),
    ("1.000.000", (1000000, False)),
])
def test_a_numero(token, esperado):
    assert a_numero(token) == esperado


def test_cero_no_es_vacio():
    valor, _ = a_numero("0")
    assert valor == 0 and valor is not None


@pytest.mark.parametrize("token", ["312A", "%", "TOTAL", "1.23.4", "2/1", "12,5%"])
def test_no_son_cifras(token):
    assert not es_numero(token)


def test_error_si_no_es_cifra():
    with pytest.raises(ValueError):
        a_numero("312A")
