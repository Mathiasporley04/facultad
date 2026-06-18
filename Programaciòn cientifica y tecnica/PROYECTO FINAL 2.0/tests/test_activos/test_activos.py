"""Tests de la jerarquia de activos con polimorfismo real."""
from datetime import datetime, timezone

import pytest

from observatorio.activos.accion_usa import AccionUSA
from observatorio.activos.cripto import Cripto
from observatorio.activos.divisa import Divisa
from observatorio.core.fuente import FuenteDatos
from observatorio.core.tipos import Cotizacion, PuntoPrecio, TipoMercado


class FuenteFake(FuenteDatos):
    """Fuente en memoria para tests sin tocar la red."""

    nombre = "fake"

    def __init__(self, precio: float = 100.0) -> None:
        self._precio = precio

    def precio_actual(self, simbolo: str) -> Cotizacion:
        return Cotizacion(simbolo, self._precio, "USD", datetime.now(timezone.utc))

    def historico(self, simbolo, desde, hasta):
        return [PuntoPrecio(datetime.now(timezone.utc), self._precio)]

    def listar_disponibles(self) -> list[str]:
        return ["FAKE"]


# ---------- Cripto ----------


def test_cripto_atributos_y_polimorfismo():
    c = Cripto("BTC", "Bitcoin", FuenteFake(precio=50000.0), market_cap=1e12, ranking=1)
    assert c.tipo == TipoMercado.CRIPTO
    assert c.market_cap == 1e12
    assert c.ranking == 1
    assert c.precio_actual_usd() == 50000.0  # pass-through USD


# ---------- AccionUSA ----------


def test_accion_usa_sector():
    a = AccionUSA("AAPL", "Apple", FuenteFake(precio=200.0), sector="Technology")
    assert a.sector == "Technology"
    assert a.tipo == TipoMercado.ACCION_USA
    assert a.precio_actual_usd() == 200.0


# ---------- Divisa ----------


def test_divisa_invierte_cotizacion():
    d = Divisa("USD", "Dolar BROU", FuenteFake(precio=40.0), moneda_nativa="UYU", tipo_cotizacion="BROU")
    assert d.tipo == TipoMercado.DIVISA
    assert d.tipo_cotizacion == "BROU"
    # cotizacion local = 40 UYU por 1 USD -> 1/40 USD por unidad local
    assert d.precio_actual_usd() == pytest.approx(1 / 40.0)


def test_divisa_usd_pass_through():
    d = Divisa("USD", "USD itself", FuenteFake(precio=1.0), moneda_nativa="USD")
    assert d.precio_actual_usd() == 1.0


# ---------- obtener_historico es concreto (delegacion) ----------


def test_obtener_historico_delega_en_fuente():
    c = Cripto("BTC", "Bitcoin", FuenteFake(precio=50000.0))
    h = c.obtener_historico(datetime.now(timezone.utc), datetime.now(timezone.utc))
    assert len(h) == 1
    assert h[0].precio == 50000.0
