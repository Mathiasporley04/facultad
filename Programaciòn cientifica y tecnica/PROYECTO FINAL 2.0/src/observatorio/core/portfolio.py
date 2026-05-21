"""Portfolio personal y tenencias individuales.

V2: `Tenencia` incorpora `precio_compra` y metodos `valor_actual` + `pnl`.
`Portfolio` agrega `moneda_base`, `distribucion`, `exportar_csv`, `exportar_xml`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import reduce
from typing import Callable, Iterable

from .activo import Activo


@dataclass
class Tenencia:
    """Posicion individual del portfolio.

    Relacion con `Activo`: asociacion (no composicion). El mismo activo puede
    aparecer en muchas tenencias y existe aunque no haya ninguna.
    """

    activo: Activo
    cantidad: float
    precio_compra: float = 0.0

    def valor_actual(self, tasas: dict[str, float] | None = None) -> float:
        """Valor actual de la posicion en USD."""
        return self.activo.precio_actual_usd(tasas) * self.cantidad

    def pnl(self, tasas: dict[str, float] | None = None) -> float:
        """Ganancia/perdida (PnL) en USD respecto al precio de compra.

        Si `precio_compra` es 0 (no informado), devuelve 0.0 para no inducir
        a errores de interpretacion.
        """
        if self.precio_compra <= 0:
            return 0.0
        valor = self.valor_actual(tasas)
        costo = self.precio_compra * self.cantidad
        return valor - costo


@dataclass
class Portfolio:
    """Coleccion de tenencias con valuacion agregada."""

    nombre: str = "Mi Portfolio"
    tenencias: list[Tenencia] = field(default_factory=list)
    moneda_base: str = "USD"

    # ---------- mutadores ----------

    def agregar_tenencia(self, tenencia: Tenencia) -> None:
        self.tenencias.append(tenencia)

    def agregar(self, activo: Activo, cantidad: float, precio_compra: float = 0.0) -> None:
        """Helper. Construye `Tenencia` y la agrega."""
        self.agregar_tenencia(Tenencia(activo=activo, cantidad=cantidad, precio_compra=precio_compra))

    # ---------- consultas ----------

    def valor_total(self, tasas: dict[str, float] | None = None) -> float:
        """Suma del valor actual de cada tenencia en USD. Usa `functools.reduce`."""
        return reduce(
            lambda acc, t: acc + t.valor_actual(tasas),
            self.tenencias,
            0.0,
        )

    # Alias por compatibilidad con la API anterior.
    def valor_total_usd(self, tasas: dict[str, float] | None = None) -> float:
        return self.valor_total(tasas)

    def distribucion(self, tasas: dict[str, float] | None = None) -> dict[str, float]:
        """Porcentaje del valor total por simbolo. Devuelve dict {simbolo: 0..100}."""
        total = self.valor_total(tasas)
        if total <= 0:
            return {}
        salida: dict[str, float] = {}
        for t in self.tenencias:
            sim = t.activo.simbolo
            salida[sim] = salida.get(sim, 0.0) + (t.valor_actual(tasas) / total) * 100.0
        return salida

    def filtrar(self, predicado: Callable[[Tenencia], bool]) -> list[Tenencia]:
        """Devuelve las tenencias que cumplen un criterio (uso de `filter`)."""
        return list(filter(predicado, self.tenencias))

    # ---------- serializacion ----------

    def a_dicts(self) -> list[dict]:
        """Serializa a la representacion de la UI (lista de dicts)."""
        return [
            {
                "simbolo": t.activo.simbolo,
                "tipo": t.activo.tipo.value,
                "cantidad": t.cantidad,
                "precio_compra": t.precio_compra,
            }
            for t in self.tenencias
        ]

    def exportar_csv(self) -> str:
        """Importa el serializador para evitar dependencia circular."""
        from ..persistencia.almacen import tenencias_a_csv

        return tenencias_a_csv(self.a_dicts())

    def exportar_xml(self) -> str:
        from ..persistencia.almacen import tenencias_a_xml

        return tenencias_a_xml(self.a_dicts())

    # ---------- construccion desde dicts ----------

    @classmethod
    def desde_dicts(
        cls,
        tenencias: Iterable[dict],
        resolver_activo: Callable[[str, str], Activo | None],
        nombre: str = "Mi Portfolio",
        moneda_base: str = "USD",
    ) -> "Portfolio":
        """Reconstruye un `Portfolio` desde la lista de dicts de la UI.

        `resolver_activo(simbolo, tipo) -> Activo` mapea cada entrada a un objeto
        `Activo` concreto. Entradas que no resuelven se ignoran.
        """
        p = cls(nombre=nombre, moneda_base=moneda_base)
        for d in tenencias:
            activo = resolver_activo(d["simbolo"], d["tipo"])
            if activo is None:
                continue
            p.agregar(
                activo=activo,
                cantidad=float(d.get("cantidad", 0)),
                precio_compra=float(d.get("precio_compra", 0.0)),
            )
        return p
