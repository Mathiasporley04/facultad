from __future__ import annotations

from ..core.activo import Activo
from ..core.tipos import TipoMercado


class Cripto(Activo):
    """Criptomoneda. Su fuente ya devuelve precio en USD."""

    @property
    def tipo(self) -> TipoMercado:
        return TipoMercado.CRIPTO

    def precio_actual_usd(self, tasas: dict[str, float] | None = None) -> float:
        return self.fuente.precio_actual(self.simbolo).precio
