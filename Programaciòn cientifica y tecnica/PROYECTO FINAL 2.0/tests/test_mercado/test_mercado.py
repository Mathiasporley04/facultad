"""Tests de Mercado: filtrar, correlaciones, refrescar async."""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from observatorio.activos.cripto import Cripto
from observatorio.core.fuente import FuenteDatos
from observatorio.core.mercado import Mercado
from observatorio.core.tipos import Cotizacion, PuntoPrecio, TipoMercado


class FuenteSerieFake(FuenteDatos):
    """Fuente fake con serie historica determinista por simbolo."""

    nombre = "fake-serie"

    def __init__(self, series: dict[str, list[float]]) -> None:
        self._series = series

    def precio_actual(self, simbolo: str) -> Cotizacion:
        precios = self._series.get(simbolo, [100.0])
        return Cotizacion(simbolo, precios[-1], "USD", datetime.now(timezone.utc))

    def historico(self, simbolo, desde, hasta):
        precios = self._series.get(simbolo, [])
        base = datetime.now(timezone.utc) - timedelta(days=len(precios))
        return [PuntoPrecio(base + timedelta(days=i), p) for i, p in enumerate(precios)]

    def listar_disponibles(self) -> list[str]:
        return list(self._series.keys())


def test_mercado_filtrar():
    f = FuenteSerieFake({"BTC": [50000.0], "DOGE": [0.1], "ETH": [3000.0]})
    m = Mercado("cripto", TipoMercado.CRIPTO)
    m.agregar(Cripto("BTC", "Bitcoin", f, ranking=1))
    m.agregar(Cripto("DOGE", "Doge", f, ranking=10))
    m.agregar(Cripto("ETH", "Ethereum", f, ranking=2))

    top2 = m.filtrar(lambda a: a.ranking <= 2)
    assert {a.simbolo for a in top2} == {"BTC", "ETH"}


def test_mercado_correlaciones_perfecta():
    # Dos series identicas -> corr = 1
    serie = [100.0, 102.0, 105.0, 103.0, 110.0, 115.0]
    f = FuenteSerieFake({"A": serie, "B": serie})
    m = Mercado("test", TipoMercado.CRIPTO)
    m.agregar(Cripto("A", "A", f))
    m.agregar(Cripto("B", "B", f))

    desde = datetime.now(timezone.utc) - timedelta(days=10)
    hasta = datetime.now(timezone.utc)
    simbolos, matriz = m.correlaciones(desde, hasta)

    assert set(simbolos) == {"A", "B"}
    # Diagonal = 1
    assert matriz[0, 0] == 1.0
    assert matriz[1, 1] == 1.0
    # Series identicas -> correlacion = 1
    assert matriz[0, 1] == pytest.approx(1.0, abs=1e-6)
    assert matriz[1, 0] == pytest.approx(1.0, abs=1e-6)


def test_mercado_refrescar_precios_async():
    """asyncio.gather sobre los activos del mercado."""
    f = FuenteSerieFake({"BTC": [50000.0], "ETH": [3000.0]})
    m = Mercado("cripto", TipoMercado.CRIPTO)
    m.agregar(Cripto("BTC", "Bitcoin", f))
    m.agregar(Cripto("ETH", "Ethereum", f))

    resultados = asyncio.run(m.refrescar_precios_async())
    assert set(resultados.keys()) == {"BTC", "ETH"}
    assert resultados["BTC"].precio == 50000.0
    assert resultados["ETH"].precio == 3000.0


def test_mercado_repr_y_len():
    m = Mercado("cripto", TipoMercado.CRIPTO)
    assert len(m) == 0
    assert "Mercado" in repr(m)
