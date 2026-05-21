"""Calculo de rendimientos."""
from __future__ import annotations


def calcular_rendimiento_porcentual(precio_inicial: float, precio_final: float) -> float:
    """Cambio relativo entre dos precios, en porcentaje (ej: 10.0 = +10%)."""
    if precio_inicial <= 0:
        return 0.0
    return (precio_final - precio_inicial) / precio_inicial * 100.0


def rendimientos_diarios(precios: list[float]) -> list[float]:
    """Serie de rendimientos diarios (no en %, en proporcion: 0.01 = +1%)."""
    if len(precios) < 2:
        return []
    return [
        (b - a) / a if a > 0 else 0.0
        for a, b in zip(precios[:-1], precios[1:])
    ]
