from __future__ import annotations

from ..core.activo import Activo
from ..core.excepciones import DatoInvalido
from ..core.fuente import FuenteDatos
from ..core.tipos import TipoMercado


class AccionArg(Activo):
    """Accion argentina. Cotiza en ARS, requiere tasa USD/ARS para convertir.

    Atributos especificos:
        panel: panel del Merval ("lider", "general", "cedears"...).
    """

    def __init__(
        self,
        simbolo: str,
        nombre: str,
        fuente: FuenteDatos,
        panel: str | None = None,
    ) -> None:
        super().__init__(simbolo=simbolo, nombre=nombre, moneda_nativa="ARS", fuente=fuente)
        self.panel = panel

    @property
    def tipo(self) -> TipoMercado:
        return TipoMercado.ACCION_ARG

    def precio_actual_usd(self, tasas: dict[str, float] | None = None) -> float:
        precio_ars = self.fuente.precio_actual(self.simbolo).precio
        if not tasas or "ARS" not in tasas or tasas["ARS"] <= 0:
            raise DatoInvalido("Falta tasa ARS->USD para convertir AccionArg")
        return precio_ars / tasas["ARS"]
