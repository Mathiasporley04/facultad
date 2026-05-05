"""Portfolio personal."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import reduce

from .activo import Activo


@dataclass
class Tenencia:
    activo: Activo
    cantidad: float


@dataclass
class Portfolio:
    nombre: str = "Mi Portfolio"
    tenencias: list[Tenencia] = field(default_factory=list)

    def agregar(self, activo: Activo, cantidad: float) -> None:
        self.tenencias.append(Tenencia(activo, cantidad))

    def valor_total_usd(self, tasas: dict[str, float] | None = None) -> float:
        precios = [(t.activo.precio_actual_usd(tasas), t.cantidad) for t in self.tenencias]
        return reduce(lambda acc, par: acc + par[0] * par[1], precios, 0.0)
