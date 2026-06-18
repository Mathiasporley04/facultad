"""Fuente DolarApi Uruguay para cotizaciones de divisas BROU/BCU."""
from __future__ import annotations

from datetime import datetime, timezone

import requests

from ..core.excepciones import FuenteIndisponible
from ..core.fuente import FuenteDatos
from ..core.tipos import Cotizacion, PuntoPrecio
from .cache import cache_ttl

_BASE = "https://uy.dolarapi.com/v1/cotizaciones"

_DEFAULTS = ["USD", "EUR", "BRL", "ARS"]


class DolarApiUY(FuenteDatos):
    nombre = "dolar_api_uy"

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    @cache_ttl(60)
    def precio_actual(self, simbolo: str) -> Cotizacion:
        try:
            r = requests.get(_BASE, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            raise FuenteIndisponible(f"DolarApiUY fallo: {e}") from e
        objetivo = simbolo.lower()
        for fila in data:
            moneda = str(fila.get("moneda", "")).lower()
            nombre = str(fila.get("nombre", "")).lower()
            if moneda == objetivo or objetivo in nombre:
                precio = float(fila.get("venta") or fila.get("compra") or 0.0)
                return Cotizacion(
                    simbolo.upper(), precio, "UYU", datetime.now(timezone.utc)
                )
        raise FuenteIndisponible(f"DolarApiUY no devolvio {simbolo}")

    @cache_ttl(60)
    def compra_venta(self, simbolo: str) -> tuple[float, float]:
        """Devuelve (compra, venta) de la divisa. Lanza FuenteIndisponible si falla."""
        try:
            r = requests.get(_BASE, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            raise FuenteIndisponible(f"DolarApiUY fallo: {e}") from e
        objetivo = simbolo.lower()
        for fila in data:
            moneda = str(fila.get("moneda", "")).lower()
            nombre = str(fila.get("nombre", "")).lower()
            if moneda == objetivo or objetivo in nombre:
                compra = float(fila.get("compra") or 0.0)
                venta = float(fila.get("venta") or 0.0)
                return compra, venta
        raise FuenteIndisponible(f"DolarApiUY no devolvio {simbolo}")

    def historico(self, simbolo: str, desde: datetime, hasta: datetime) -> list[PuntoPrecio]:
        return []

    def listar_disponibles(self) -> list[str]:
        return list(_DEFAULTS)

    async def precio_actual_async(self, simbolo: str) -> Cotizacion:
        import aiohttp

        try:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(
                    _BASE, timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as r:
                    r.raise_for_status()
                    data = await r.json()
        except Exception as e:
            raise FuenteIndisponible(f"DolarApiUY async fallo: {e}") from e
        objetivo = simbolo.lower()
        for fila in data:
            moneda = str(fila.get("moneda", "")).lower()
            nombre = str(fila.get("nombre", "")).lower()
            if moneda == objetivo or objetivo in nombre:
                precio = float(fila.get("venta") or fila.get("compra") or 0.0)
                return Cotizacion(
                    simbolo.upper(), precio, "UYU", datetime.now(timezone.utc)
                )
        raise FuenteIndisponible(f"DolarApiUY no devolvio {simbolo}")
