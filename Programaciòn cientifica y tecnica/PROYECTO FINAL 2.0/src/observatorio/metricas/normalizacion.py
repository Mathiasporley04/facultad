"""Normalizacion de series a base comun."""
from __future__ import annotations


def normalizar_a_base(precios: list[float], base: float = 100.0) -> list[float]:
    """Reescala la serie para que el primer valor sea `base`."""
    if not precios or precios[0] == 0:
        return list(precios)
    factor = base / precios[0]
    return list(map(lambda p: p * factor, precios))
