"""Preparacion de datos para los graficos del front.

- Series temporales -> payload para TradingView Lightweight Charts (se dibujan
  en el navegador: crosshair, escala de precios, zoom/pan).
- Correlaciones -> matriz con colores (RdYlGn) para una tabla-heatmap en HTML.

No se usa Plotly: el front es liviano (sin bundle pesado).
"""
from __future__ import annotations

from datetime import datetime

from observatorio.metricas import matriz_correlacion

# Paleta categorica acorde a la estetica neutral de shadcn.
PALETA = ["#6366f1", "#10b981", "#f59e0b", "#a855f7", "#ef4444", "#0ea5e9"]


_SEG_DIA = 86400  # segundos por dia


def serie_payload(
    series_fechas: dict[str, list[datetime]],
    series_precios: dict[str, list[float]],
    base_100: bool = True,
) -> dict:
    """Payload para Lightweight Charts.

    Con `base_100=True` (default) cada serie se reescala a 100 en su primer dia,
    para comparar evolucion relativa. Con `base_100=False` se grafican los
    precios reales (valores numericos), util cuando interesa el precio absoluto.

    Todas las series se llevan a una grilla DIARIA comun (un punto por dia, el
    ultimo del dia) y se alinean sobre la union de fechas con *forward-fill*: si
    una serie no cotizo ese dia (p.ej. acciones el fin de semana) se arrastra su
    ultimo valor. Asi todas tienen punto en cada fecha y el crosshair muestra
    marker + valor en todas. `time` es el epoch (s) de la medianoche UTC del dia.
    """
    # 1) Downsample de cada serie a {dia_epoch: ultimo precio del dia}.
    diarios: dict[str, dict[int, float]] = {}
    for nombre, precios in series_precios.items():
        por_dia: dict[int, float] = {}
        for fecha, valor in zip(series_fechas[nombre], precios):
            dia = (int(fecha.timestamp()) // _SEG_DIA) * _SEG_DIA
            por_dia[dia] = float(valor)  # orden ascendente: el ultimo del dia gana
        diarios[nombre] = por_dia

    # 2) Union de dias (eje temporal compartido).
    todos_los_dias = sorted({d for por_dia in diarios.values() for d in por_dia})

    # 3) Normalizar a base 100 (primer dia de cada serie) o dejar el precio
    #    real (base_100=False), y forward-fill.
    series = []
    for i, (nombre, por_dia) in enumerate(diarios.items()):
        dias = sorted(por_dia)
        if not dias:
            continue
        base = por_dia[dias[0]]
        factor = (100.0 / base) if (base_100 and base) else 1.0
        data = []
        ultimo: float | None = None
        for dia in todos_los_dias:
            if dia in por_dia:
                ultimo = round(por_dia[dia] * factor, 4 if base_100 else 6)
            if ultimo is not None:
                data.append({"time": dia, "value": ultimo})
        series.append({"name": nombre, "color": PALETA[i % len(PALETA)], "data": data})
    return {"series": series}


# --- Heatmap de correlacion (RdYlGn) renderizado como tabla HTML ---

_STOPS = [(-1.0, (215, 48, 39)), (0.0, (255, 255, 191)), (1.0, (26, 152, 80))]


def _color_correlacion(v: float) -> str:
    """Mapea una correlacion [-1, 1] a un color hex de la escala RdYlGn."""
    v = max(-1.0, min(1.0, v))
    if v <= 0:
        (x0, c0), (x1, c1) = _STOPS[0], _STOPS[1]
    else:
        (x0, c0), (x1, c1) = _STOPS[1], _STOPS[2]
    t = 0.0 if x1 == x0 else (v - x0) / (x1 - x0)
    r, g, b = (round(c0[k] + (c1[k] - c0[k]) * t) for k in range(3))
    return f"#{r:02x}{g:02x}{b:02x}"


def heatmap_correlacion(series_precios: dict[str, list[float]]) -> dict:
    """Matriz de correlaciones con color por celda, lista para una tabla HTML."""
    m = matriz_correlacion(series_precios)
    labels = list(m.keys())
    cortos = [lab.split(" (")[0] for lab in labels]
    filas = []
    for i, a in enumerate(labels):
        celdas = [
            {"valor": f"{m[a][b]:.2f}", "color": _color_correlacion(m[a][b])}
            for b in labels
        ]
        filas.append({"label": cortos[i], "full": a, "celdas": celdas})
    return {"labels": cortos, "fulls": labels, "filas": filas}
