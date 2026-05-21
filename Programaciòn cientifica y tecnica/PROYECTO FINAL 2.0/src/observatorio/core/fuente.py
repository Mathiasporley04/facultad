"""ABC de fuentes de datos externas."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from .tipos import Cotizacion, PuntoPrecio


class FuenteDatos(ABC):
    """Contrato uniforme para una fuente externa de datos de mercado."""

    nombre: str = "fuente"

    @abstractmethod
    def precio_actual(self, simbolo: str) -> Cotizacion:
        """Devuelve la cotizacion actual del simbolo."""

    @abstractmethod
    def historico(
        self, simbolo: str, desde: datetime, hasta: datetime
    ) -> list[PuntoPrecio]:
        """Devuelve la serie de precios entre las fechas dadas."""

    @abstractmethod
    def listar_disponibles(self) -> list[str]:
        """Lista los simbolos que esta fuente puede consultar."""

    async def precio_actual_async(self, simbolo: str) -> Cotizacion:
        """Version async por defecto: corre el sync en un thread.

        Las subclases que pueden hacer I/O async nativo deberian overridear.
        """
        import asyncio

        return await asyncio.to_thread(self.precio_actual, simbolo)
