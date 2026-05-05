"""Fuente data912.com para acciones argentinas (Merval)."""
from __future__ import annotations

from datetime import datetime, timezone

import requests

from ..core.excepciones import FuenteIndisponible
from ..core.fuente import FuenteDatos
from ..core.tipos import Cotizacion, PuntoPrecio
from .cache import cache_ttl

_BASE = "https://data912.com"

_DEFAULTS = ["GGAL", "YPFD", "PAMP", "BMA", "TXAR", "ALUA", "TGSU2", "COME"]


class Data912API(FuenteDatos):
    nombre = "data912"

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    @cache_ttl(60)
    def precio_actual(self, simbolo: str) -> Cotizacion:
        url = f"{_BASE}/live/arg_stocks"
        try:
            r = requests.get(url, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            raise FuenteIndisponible(f"data912 fallo: {e}") from e
        for fila in data:
            if str(fila.get("symbol", "")).upper() == simbolo.upper():
                precio = float(fila.get("c") or fila.get("close") or 0.0)
                return Cotizacion(
                    simbolo.upper(), precio, "ARS", datetime.now(timezone.utc)
                )
        raise FuenteIndisponible(f"data912 no devolvio {simbolo}")

    def historico(self, simbolo: str, desde: datetime, hasta: datetime) -> list[PuntoPrecio]:
        # Data912 expone principalmente snapshots; historico no esta disponible publico.
        # Devolvemos lista vacia y dejamos que la UI muestre el dato actual.
        return []

    def listar_disponibles(self) -> list[str]:
        return list(_DEFAULTS)

    async def precio_actual_async(self, simbolo: str) -> Cotizacion:
        import aiohttp

        url = f"{_BASE}/live/arg_stocks"
        try:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(
                    url, timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as r:
                    r.raise_for_status()
                    data = await r.json()
        except Exception as e:
            raise FuenteIndisponible(f"data912 async fallo: {e}") from e
        for fila in data:
            if str(fila.get("symbol", "")).upper() == simbolo.upper():
                precio = float(fila.get("c") or fila.get("close") or 0.0)
                return Cotizacion(
                    simbolo.upper(), precio, "ARS", datetime.now(timezone.utc)
                )
        raise FuenteIndisponible(f"data912 no devolvio {simbolo}")
