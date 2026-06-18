"""Definiciones para tooltips y ayudas en la UI web."""

GLOSARIO: dict[str, str] = {
    "rendimiento": (
        "Cambio porcentual del precio en el periodo. Verde = subio, rojo = bajo."
    ),
    "volatilidad": (
        "Que tan inestables son los precios. Estable = poco movimiento; Muy alta = oscila mucho."
    ),
    "drawdown": (
        "La peor caida desde un maximo del periodo. Mide cuanto se pudo perder en el peor momento."
    ),
    "correlacion": (
        "Si dos activos se mueven juntos. +1 = igual; -1 = opuesto; 0 = sin relacion."
    ),
    "base_100": (
        "Para comparar mercados de distinto precio se reescala todo a 100 al inicio. "
        "Asi una linea que sube a 120 = +20% en el periodo."
    ),
    "spread": "Diferencia entre precio de compra y venta. Es el margen del banco.",
}
