"""Volatilidad anualizada (desv. estandar de retornos diarios * sqrt(252))."""
from __future__ import annotations

import math

from .rendimiento import rendimientos_diarios


def calcular_volatilidad(precios: list[float], periodos_anuales: int = 252) -> float:
    rets = rendimientos_diarios(precios)
    if len(rets) < 2:
        return 0.0
    media = sum(rets) / len(rets)
    var = sum((r - media) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(periodos_anuales)


def clasificar_volatilidad(vol_anualizada: float) -> str:
    if vol_anualizada < 0.15:
        return "Estable"
    if vol_anualizada < 0.30:
        return "Moderada"
    if vol_anualizada < 0.60:
        return "Alta"
    return "Muy alta"
