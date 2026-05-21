"""Fuente Yahoo Finance via yfinance para acciones e indices USA."""
from __future__ import annotations

from datetime import datetime, timezone

from ..core.excepciones import FuenteIndisponible
from ..core.fuente import FuenteDatos
from ..core.tipos import Cotizacion, PuntoPrecio
from .cache import cache_ttl


class YahooFinanceAPI(FuenteDatos):
    nombre = "yahoo_finance"

    _DEFAULTS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "^GSPC"]

    @cache_ttl(60)
    def precio_actual(self, simbolo: str) -> Cotizacion:
        try:
            import yfinance as yf

            ticker = yf.Ticker(simbolo)
            hist = ticker.history(period="2d", interval="1d")
            if hist.empty:
                raise FuenteIndisponible(f"Yahoo sin datos para {simbolo}")
            precio = float(hist["Close"].iloc[-1])
        except FuenteIndisponible:
            raise
        except Exception as e:
            raise FuenteIndisponible(f"Yahoo fallo: {e}") from e
        return Cotizacion(simbolo.upper(), precio, "USD", datetime.now(timezone.utc))

    @cache_ttl(3600)
    def historico(self, simbolo: str, desde: datetime, hasta: datetime) -> list[PuntoPrecio]:
        try:
            import yfinance as yf

            ticker = yf.Ticker(simbolo)
            df = ticker.history(start=desde.date(), end=hasta.date(), interval="1d")
            if df.empty:
                return []
            puntos = [
                PuntoPrecio(idx.to_pydatetime().replace(tzinfo=timezone.utc), float(row["Close"]))
                for idx, row in df.iterrows()
            ]
            return puntos
        except Exception as e:
            raise FuenteIndisponible(f"Yahoo historico fallo: {e}") from e

    def listar_disponibles(self) -> list[str]:
        return list(self._DEFAULTS)
