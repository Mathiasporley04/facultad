"""Registro central de fuentes disponibles."""
from __future__ import annotations

from ..core.fuente import FuenteDatos
from .coingecko import CoinGeckoAPI
from .dolar_api_uy import DolarApiUY
from .yahoo_finance import YahooFinanceAPI


def fuentes_default() -> dict[str, FuenteDatos]:
    return {
        "cripto": CoinGeckoAPI(),
        "usa": YahooFinanceAPI(),
        "uy": DolarApiUY(),
    }
