from __future__ import annotations

from ..core.activo import Activo
from ..core.fuente import FuenteDatos
from ..core.tipos import TipoMercado


class AccionUSA(Activo):
    """Accion estadounidense. Cotiza en USD nativamente.

    Atributos especificos:
        sector: sector economico (Technology, Healthcare, Financials...).
    """

    def __init__(
        self,
        simbolo: str,
        nombre: str,
        fuente: FuenteDatos,
        sector: str | None = None,
    ) -> None:
        super().__init__(simbolo=simbolo, nombre=nombre, moneda_nativa="USD", fuente=fuente)
        self.sector = sector

    @property
    def tipo(self) -> TipoMercado:
        return TipoMercado.ACCION_USA

    def precio_actual_usd(self, tasas: dict[str, float] | None = None) -> float:
        return self.fuente.precio_actual(self.simbolo).precio
