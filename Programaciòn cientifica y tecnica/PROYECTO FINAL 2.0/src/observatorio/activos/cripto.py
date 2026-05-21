from __future__ import annotations

from ..core.activo import Activo
from ..core.fuente import FuenteDatos
from ..core.tipos import TipoMercado


class Cripto(Activo):
    """Criptomoneda. Su fuente ya devuelve precio en USD.

    Atributos especificos:
        market_cap: capitalizacion de mercado en USD (opcional).
        ranking: posicion por capitalizacion (opcional).
    """

    def __init__(
        self,
        simbolo: str,
        nombre: str,
        fuente: FuenteDatos,
        market_cap: float | None = None,
        ranking: int | None = None,
    ) -> None:
        super().__init__(simbolo=simbolo, nombre=nombre, moneda_nativa="USD", fuente=fuente)
        self.market_cap = market_cap
        self.ranking = ranking

    @property
    def tipo(self) -> TipoMercado:
        return TipoMercado.CRIPTO

    def precio_actual_usd(self, tasas: dict[str, float] | None = None) -> float:
        return self.fuente.precio_actual(self.simbolo).precio
