"""Correlacion de Pearson entre series."""
from __future__ import annotations

import math


def calcular_correlacion(serie_a: list[float], serie_b: list[float]) -> float:
    n = min(len(serie_a), len(serie_b))
    if n < 2:
        return 0.0
    a = serie_a[-n:]
    b = serie_b[-n:]
    ma = sum(a) / n
    mb = sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    var_a = sum((x - ma) ** 2 for x in a)
    var_b = sum((y - mb) ** 2 for y in b)
    den = math.sqrt(var_a * var_b)
    if den == 0:
        return 0.0
    return cov / den


def matriz_correlacion(series: dict[str, list[float]]) -> dict[str, dict[str, float]]:
    nombres = list(series.keys())
    return {
        a: {b: calcular_correlacion(series[a], series[b]) for b in nombres}
        for a in nombres
    }
