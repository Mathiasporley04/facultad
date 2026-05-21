"""Tests de los modelos Pydantic en la frontera con APIs externas."""
from datetime import datetime, timezone

import pytest

from observatorio.fuentes.esquemas import (
    CotizacionDTO,
    PuntoPrecioDTO,
    validar_cotizacion,
    validar_historico,
)


def test_cotizacion_dto_acepta_dato_valido():
    dto = CotizacionDTO(
        simbolo="btc ",  # sucio: minusculas + espacio
        precio=50000.0,
        moneda="usd",
        timestamp=datetime.now(timezone.utc),
    )
    # Los validators canonican
    assert dto.simbolo == "BTC"
    assert dto.moneda == "USD"


def test_cotizacion_dto_rechaza_precio_no_positivo():
    with pytest.raises(Exception):
        CotizacionDTO(
            simbolo="BTC",
            precio=0,
            moneda="USD",
            timestamp=datetime.now(timezone.utc),
        )


def test_cotizacion_dto_rechaza_moneda_invalida():
    with pytest.raises(Exception):
        CotizacionDTO(
            simbolo="BTC",
            precio=100.0,
            moneda="DOLAR",  # longitud != 3
            timestamp=datetime.now(timezone.utc),
        )


def test_validar_cotizacion_devuelve_dataclass_dominio():
    dato = {
        "simbolo": "eth",
        "precio": 3000.0,
        "moneda": "usd",
        "timestamp": datetime.now(timezone.utc),
    }
    cot = validar_cotizacion(dato)
    assert cot.simbolo == "ETH"
    assert cot.precio == 3000.0
    assert cot.moneda == "USD"


def test_validar_historico_serie_minima():
    ahora = datetime.now(timezone.utc)
    puntos = [
        {"fecha": ahora, "precio": 100.0},
        {"fecha": ahora, "precio": 105.5},
    ]
    serie = validar_historico(puntos)
    assert len(serie) == 2
    assert serie[0].precio == 100.0
    assert serie[1].precio == 105.5


def test_punto_precio_dto_rechaza_precio_negativo():
    with pytest.raises(Exception):
        PuntoPrecioDTO(fecha=datetime.now(timezone.utc), precio=-1.0)
