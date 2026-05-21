from __future__ import annotations

from ..core.activo import Activo
from ..core.fuente import FuenteDatos
from ..core.tipos import TipoMercado


class Divisa(Activo):
    """Par cambiario. El 'precio' es el tipo de cambio respecto a USD.

    Atributos especificos:
        par: par cambiario ("USD/UYU", "USD/ARS", "EUR/USD"...).
        tipo_cotizacion: BROU, BCU, MEP, oficial, blue, etc.
    """

    def __init__(
        self,
        simbolo: str,
        nombre: str,
        fuente: FuenteDatos,
        moneda_nativa: str = "UYU",
        par: str | None = None,
        tipo_cotizacion: str = "BROU",
    ) -> None:
        super().__init__(simbolo=simbolo, nombre=nombre, moneda_nativa=moneda_nativa, fuente=fuente)
        self.par = par or f"USD/{moneda_nativa}"
        self.tipo_cotizacion = tipo_cotizacion

    @property
    def tipo(self) -> TipoMercado:
        return TipoMercado.DIVISA

    def precio_actual_usd(self, tasas: dict[str, float] | None = None) -> float:
        cotizacion = self.fuente.precio_actual(self.simbolo).precio
        if self.moneda_nativa == "USD":
            return 1.0
        return 1.0 / cotizacion if cotizacion > 0 else 0.0
