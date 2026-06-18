"""Fuente CoinGecko para criptomonedas."""
from __future__ import annotations

from datetime import datetime, timezone

import requests

from ..core.excepciones import FuenteIndisponible
from ..core.fuente import FuenteDatos
from ..core.tipos import Cotizacion, PuntoPrecio
from .cache import cache_ttl

_BASE = "https://api.coingecko.com/api/v3"

# Mapeo de simbolos canonicos a ids de CoinGecko
_MAPA = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "BNB": "binancecoin",
    "SOL": "solana",
    "USDC": "usd-coin",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "ADA": "cardano",
    "TRX": "tron",
}


class CoinGeckoAPI(FuenteDatos):
    nombre = "coingecko"

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout
        self._ids: dict[str, str] = {}  # simbolo -> id CoinGecko (poblado por mercados())

    @cache_ttl(60)
    def precio_actual(self, simbolo: str) -> Cotizacion:
        cg_id = _MAPA.get(simbolo.upper())
        if not cg_id:
            raise FuenteIndisponible(f"Simbolo no mapeado en CoinGecko: {simbolo}")
        url = f"{_BASE}/simple/price"
        try:
            r = requests.get(
                url,
                params={"ids": cg_id, "vs_currencies": "usd"},
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
            precio = float(data[cg_id]["usd"])
        except Exception as e:
            raise FuenteIndisponible(f"CoinGecko fallo: {e}") from e
        return Cotizacion(simbolo.upper(), precio, "USD", datetime.now(timezone.utc))

    @cache_ttl(3600)
    def historico(self, simbolo: str, desde: datetime, hasta: datetime) -> list[PuntoPrecio]:
        cg_id = _MAPA.get(simbolo.upper()) or self._ids.get(simbolo.upper())
        if not cg_id:
            raise FuenteIndisponible(f"Simbolo no mapeado en CoinGecko: {simbolo}")
        dias = max(1, (hasta - desde).days)
        url = f"{_BASE}/coins/{cg_id}/market_chart"
        try:
            r = requests.get(
                url,
                params={"vs_currency": "usd", "days": dias},
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
            puntos = [
                PuntoPrecio(datetime.fromtimestamp(ts / 1000, tz=timezone.utc), float(p))
                for ts, p in data.get("prices", [])
            ]
            return puntos
        except Exception as e:
            raise FuenteIndisponible(f"CoinGecko historico fallo: {e}") from e

    @cache_ttl(300)
    def mercados(self, top: int = 100) -> list[dict]:
        """Top monedas por capitalizacion, con precio actual (una sola llamada).

        Devuelve [{simbolo, nombre, id, precio}] y cachea el mapeo simbolo->id
        para que `historico` funcione con cualquiera de estas monedas.
        """
        url = f"{_BASE}/coins/markets"
        try:
            r = requests.get(
                url,
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": min(top, 250),
                    "page": 1,
                },
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            raise FuenteIndisponible(f"CoinGecko markets fallo: {e}") from e
        salida = []
        for c in data:
            sym = str(c.get("symbol", "")).upper()
            cg_id = c.get("id")
            precio = c.get("current_price")
            if not sym or not cg_id or precio is None:
                continue
            self._ids[sym] = cg_id
            salida.append(
                {"simbolo": sym, "nombre": c.get("name", sym), "id": cg_id, "precio": float(precio)}
            )
        return salida

    def listar_disponibles(self) -> list[str]:
        return list(_MAPA.keys())

    async def precio_actual_async(self, simbolo: str) -> Cotizacion:
        import aiohttp

        cg_id = _MAPA.get(simbolo.upper())
        if not cg_id:
            raise FuenteIndisponible(f"Simbolo no mapeado en CoinGecko: {simbolo}")
        url = f"{_BASE}/simple/price"
        try:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(
                    url,
                    params={"ids": cg_id, "vs_currencies": "usd"},
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as r:
                    r.raise_for_status()
                    data = await r.json()
            precio = float(data[cg_id]["usd"])
        except Exception as e:
            raise FuenteIndisponible(f"CoinGecko async fallo: {e}") from e
        return Cotizacion(simbolo.upper(), precio, "USD", datetime.now(timezone.utc))
