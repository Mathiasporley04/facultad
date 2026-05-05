from __future__ import annotations

from ..core.activo import Activo
from ..core.tipos import TipoMercado


class Divisa(Activo):
    """Par cambiario. El 'precio' es el tipo de cambio respecto a USD."""

    @property
    def tipo(self) -> TipoMercado:
        return TipoMercado.DIVISA

    def precio_actual_usd(self, tasas: dict[str, float] | None = None) -> float:
        cotizacion = self.fuente.precio_actual(self.simbolo).precio
        # Si la moneda es USD, devolvemos 1.0; si no, devolvemos 1/cotizacion (USD por unidad local)
        if self.moneda_nativa == "USD":
            return 1.0
        return 1.0 / cotizacion if cotizacion > 0 else 0.0
