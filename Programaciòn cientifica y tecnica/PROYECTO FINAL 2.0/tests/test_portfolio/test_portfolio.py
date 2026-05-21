"""Tests de Portfolio y Tenencia con campos y metodos V2."""
from datetime import datetime, timezone

from observatorio.activos.cripto import Cripto
from observatorio.core.fuente import FuenteDatos
from observatorio.core.portfolio import Portfolio, Tenencia
from observatorio.core.tipos import Cotizacion, PuntoPrecio


class FuenteFake(FuenteDatos):
    nombre = "fake"

    def __init__(self, precio: float) -> None:
        self._precio = precio

    def precio_actual(self, simbolo: str) -> Cotizacion:
        return Cotizacion(simbolo, self._precio, "USD", datetime.now(timezone.utc))

    def historico(self, simbolo, desde, hasta):
        return [PuntoPrecio(datetime.now(timezone.utc), self._precio)]

    def listar_disponibles(self) -> list[str]:
        return [simbolo for simbolo in ["FAKE"]]


def _cripto(simbolo: str, precio: float) -> Cripto:
    return Cripto(simbolo, simbolo, FuenteFake(precio=precio))


def test_tenencia_valor_actual():
    t = Tenencia(activo=_cripto("BTC", 50000.0), cantidad=0.5)
    assert t.valor_actual() == 25000.0


def test_tenencia_pnl_positivo():
    # Compre a 40k, vale 50k, tengo 0.5 -> PnL = (50000 - 40000) * 0.5 = 5000
    t = Tenencia(activo=_cripto("BTC", 50000.0), cantidad=0.5, precio_compra=40000.0)
    assert t.pnl() == 5000.0


def test_tenencia_pnl_negativo():
    # Compre a 60k, vale 50k, tengo 1 -> PnL = -10000
    t = Tenencia(activo=_cripto("BTC", 50000.0), cantidad=1.0, precio_compra=60000.0)
    assert t.pnl() == -10000.0


def test_tenencia_pnl_sin_precio_compra_es_cero():
    t = Tenencia(activo=_cripto("BTC", 50000.0), cantidad=1.0)
    assert t.pnl() == 0.0


def test_portfolio_valor_total_usa_reduce():
    p = Portfolio()
    p.agregar(_cripto("BTC", 50000.0), 0.5)  # 25000
    p.agregar(_cripto("ETH", 3000.0), 2.0)  # 6000
    assert p.valor_total() == 31000.0
    # Alias legacy debe coincidir
    assert p.valor_total_usd() == 31000.0


def test_portfolio_distribucion():
    p = Portfolio()
    p.agregar(_cripto("BTC", 50000.0), 0.5)  # 25000 -> ~80.65%
    p.agregar(_cripto("ETH", 3000.0), 2.0)  # 6000 -> ~19.35%
    dist = p.distribucion()
    assert set(dist.keys()) == {"BTC", "ETH"}
    assert abs(sum(dist.values()) - 100.0) < 1e-6
    assert dist["BTC"] > dist["ETH"]


def test_portfolio_distribucion_vacia():
    assert Portfolio().distribucion() == {}


def test_portfolio_filtrar():
    p = Portfolio()
    p.agregar(_cripto("BTC", 50000.0), 0.5)
    p.agregar(_cripto("ETH", 3000.0), 2.0)
    grandes = p.filtrar(lambda t: t.valor_actual() > 10000)
    assert len(grandes) == 1
    assert grandes[0].activo.simbolo == "BTC"


def test_portfolio_exportar_csv_y_xml():
    p = Portfolio()
    p.agregar(_cripto("BTC", 50000.0), 0.5, precio_compra=40000.0)
    csv = p.exportar_csv()
    assert "simbolo" in csv
    assert "BTC" in csv
    xml = p.exportar_xml()
    assert xml.startswith("<?xml")
    assert 'simbolo="BTC"' in xml
