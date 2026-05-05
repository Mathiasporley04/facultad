"""Drawdown maximo: peor caida desde un maximo historico."""
from __future__ import annotations


def calcular_drawdown_maximo(precios: list[float]) -> float:
    """Devuelve el drawdown maximo como proporcion negativa (ej: -0.35 = -35%)."""
    if not precios:
        return 0.0
    pico = precios[0]
    peor = 0.0
    for p in precios:
        if p > pico:
            pico = p
        if pico > 0:
            dd = (p - pico) / pico
            if dd < peor:
                peor = dd
    return peor
