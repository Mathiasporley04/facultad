from __future__ import annotations

from ..core.activo import Activo
from ..core.tipos import TipoMercado


class AccionUSA(Activo):
    """Accion estadounidense. Cotiza en USD nativamente."""

    @property
    def tipo(self) -> TipoMercado:
        return TipoMercado.ACCION_USA

    def precio_actual_usd(self, tasas: dict[str, float] | None = None) -> float:
        return self.fuente.precio_actual(self.simbolo).precio
