"""Conversion entre monedas usando tasas vs USD."""
from __future__ import annotations


def convertir_moneda(
    monto: float,
    moneda_origen: str,
    moneda_destino: str,
    tasas: dict[str, float],
) -> float:
    """Convierte usando un dict {MONEDA: unidades_por_USD}. USD = 1.0."""
    tasas = {**tasas, "USD": 1.0}
    if moneda_origen not in tasas or moneda_destino not in tasas:
        raise ValueError(f"Tasa faltante: {moneda_origen} o {moneda_destino}")
    monto_usd = monto / tasas[moneda_origen]
    return monto_usd * tasas[moneda_destino]
