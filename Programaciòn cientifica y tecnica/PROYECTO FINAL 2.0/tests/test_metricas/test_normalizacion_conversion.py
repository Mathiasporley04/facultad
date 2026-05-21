import pytest

from observatorio.metricas.conversion import convertir_moneda
from observatorio.metricas.normalizacion import normalizar_a_base


def test_normalizar_lista_vacia():
    assert normalizar_a_base([]) == []


def test_normalizar_primer_valor_es_base():
    r = normalizar_a_base([50.0, 100.0, 75.0], base=100.0)
    assert r[0] == 100.0
    assert r[1] == 200.0
    assert r[2] == 150.0


def test_normalizar_cero_inicial_devuelve_misma_lista():
    assert normalizar_a_base([0.0, 1.0, 2.0]) == [0.0, 1.0, 2.0]


def test_convertir_usd_a_uyu():
    tasas = {"UYU": 40.0, "ARS": 1000.0}
    assert convertir_moneda(1.0, "USD", "UYU", tasas) == 40.0


def test_convertir_uyu_a_ars():
    tasas = {"UYU": 40.0, "ARS": 1000.0}
    # 40 UYU = 1 USD = 1000 ARS
    assert convertir_moneda(40.0, "UYU", "ARS", tasas) == 1000.0


def test_convertir_moneda_faltante():
    with pytest.raises(ValueError):
        convertir_moneda(1.0, "USD", "JPY", {"UYU": 40.0})
