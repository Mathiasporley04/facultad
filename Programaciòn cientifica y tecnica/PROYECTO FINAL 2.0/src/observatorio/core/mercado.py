"""Clase Mercado: agrega activos del mismo origen.

V2: incorpora `moneda_base`, `refrescar_precios_async`, `correlaciones` y
`filtrar(predicado)` para materializar el uso genuino de `filter`.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Callable

import numpy as np

from ..core.excepciones import FuenteIndisponible
from .activo import Activo
from .tipos import Cotizacion, TipoMercado


class Mercado:
    """Coleccion de activos del mismo tipo de mercado."""

    def __init__(
        self,
        nombre: str,
        tipo: TipoMercado,
        activos: list[Activo] | None = None,
        moneda_base: str = "USD",
    ) -> None:
        self.nombre = nombre
        self.tipo = tipo
        self.activos: list[Activo] = activos or []
        self.moneda_base = moneda_base

    # ---------- mutadores ----------

    def agregar(self, activo: Activo) -> None:
        self.activos.append(activo)

    # ---------- consultas ----------

    def simbolos(self) -> list[str]:
        return [a.simbolo for a in self.activos]

    def filtrar(self, predicado: Callable[[Activo], bool]) -> list[Activo]:
        """Devuelve los activos que cumplen un criterio arbitrario.

        Ejemplo:
            cripto_top10 = mercado.filtrar(lambda a: getattr(a, "ranking", None) and a.ranking <= 10)
        """
        return list(filter(predicado, self.activos))

    # ---------- operaciones de conjunto ----------

    async def refrescar_precios_async(self) -> dict[str, Cotizacion | Exception]:
        """Refresca los precios actuales de todos los activos en paralelo.

        Devuelve un dict `{simbolo: Cotizacion | Exception}`. Las excepciones por
        simbolo NO tumban al resto: cada llamada se aisla via `return_exceptions=True`.
        """
        tareas = [a.fuente.precio_actual_async(a.simbolo) for a in self.activos]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)
        return {a.simbolo: r for a, r in zip(self.activos, resultados)}

    def correlaciones(
        self,
        desde: datetime,
        hasta: datetime,
    ) -> tuple[list[str], np.ndarray]:
        """Matriz de correlaciones entre todos los activos del mercado.

        Devuelve `(simbolos, matriz)`. La matriz es NxN con `corr[i, j]` en [-1, 1].
        Los activos para los que la fuente no responde se omiten.
        """
        from ..metricas.correlacion import calcular_correlacion

        series: dict[str, list[float]] = {}
        for a in self.activos:
            try:
                historico = a.obtener_historico(desde, hasta)
                series[a.simbolo] = [p.precio for p in historico]
            except (FuenteIndisponible, NotImplementedError):
                continue

        simbolos = list(series.keys())
        n = len(simbolos)
        matriz = np.eye(n)
        for i in range(n):
            for j in range(i + 1, n):
                serie_a = series[simbolos[i]]
                serie_b = series[simbolos[j]]
                # alinear al minimo comun de puntos
                m = min(len(serie_a), len(serie_b))
                if m < 2:
                    continue
                corr = calcular_correlacion(serie_a[-m:], serie_b[-m:])
                matriz[i, j] = corr
                matriz[j, i] = corr
        return simbolos, matriz

    def __len__(self) -> int:
        return len(self.activos)

    def __repr__(self) -> str:
        return f"<Mercado {self.nombre} ({self.tipo.value}) n={len(self.activos)}>"
