"""Servidor web (FastAPI) del Observatorio Financiero LATAM.

Sirve HTML server-rendered. Los graficos de lineas se dibujan con TradingView
Lightweight Charts y la correlacion con una tabla-heatmap (sin librerias
pesadas). Las fuentes se consultan en paralelo. Ver ADR-004.

Ejecutar:
    python -m observatorio.web
    # o, con autoreload en desarrollo:
    uvicorn observatorio.web.app:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from observatorio.metricas import (
    calcular_drawdown_maximo,
    calcular_rendimiento_porcentual,
    calcular_volatilidad,
    clasificar_volatilidad,
)
from observatorio.web.datos import (
    PERIODOS_COMPARAR,
    PERIODOS_PANORAMA,
    cotizaciones_panorama,
    iniciar_precalentamiento,
    series_en_paralelo,
    universo_disponible,
)
from observatorio.web.glosario import GLOSARIO
from observatorio.web.graficos import heatmap_correlacion, serie_payload
from observatorio.web.noticias import noticias_destacadas, noticias_recientes

_AQUI = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(_AQUI / "templates"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Mantener el cache caliente desde el arranque (evita el lag inicial de 2-3s).
    iniciar_precalentamiento()
    yield


app = FastAPI(title="Observatorio Financiero LATAM", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(_AQUI / "static")), name="static")

# Series fijas que dibuja el panorama (comparativa rapida cripto vs bolsa USA).
_SERIES_PANORAMA: dict[str, tuple[str, str]] = {
    "BTC": ("cripto", "BTC"),
    "S&P 500": ("usa", "^GSPC"),
}

_DISCLAIMER = (
    "Producto informativo y educativo. No constituye asesoramiento financiero. "
    "Rendimientos pasados no garantizan rendimientos futuros."
)


@app.get("/", response_class=HTMLResponse)
def panorama(request: Request, dias: int = 30):
    """Snapshot de los tres mercados + comparativa normalizada."""
    if dias not in PERIODOS_PANORAMA.values():
        dias = 30

    tarjetas = cotizaciones_panorama()
    items = [(nombre, clave, simbolo) for nombre, (clave, simbolo) in _SERIES_PANORAMA.items()]
    series_fechas, series_precios, errores = series_en_paralelo(items, dias)
    chart = serie_payload(series_fechas, series_precios) if series_precios else None
    noticias = noticias_recientes(10)
    destacadas = noticias_destacadas(3)

    return templates.TemplateResponse(
        request,
        "panorama.html",
        {
            "vista": "panorama",
            "tarjetas": tarjetas,
            "periodos": PERIODOS_PANORAMA,
            "dias": dias,
            "chart": chart,
            "errores": errores,
            "noticias": noticias,
            "destacadas": destacadas,
            "disclaimer": _DISCLAIMER,
        },
    )


# Activos por defecto en cada bloque de Comparar (para que arranque con datos).
_DEF_CRIPTO = ["cripto:BTC", "cripto:ETH", "cripto:SOL"]
_DEF_SP = ["usa:AAPL", "usa:MSFT", "usa:NVDA"]
_DEF_MIXTO = ["usa:^GSPC", "cripto:BTC"]
_MAX_BLOQUE = 5  # tope de activos por bloque (mas que esto el grafico se vuelve ilegible).


def _bloque_comparacion(
    universo: dict, valores: list[str], dias: int, correlacion: bool,
    base_100: bool = True, auto: bool = False,
) -> dict:
    """Arma un bloque: grafico + tabla de metricas (+ correlacion opcional).

    Con `auto=True` el grafico usa precio real si hay un solo activo y base 100
    si hay dos o mas (asi una comparativa con escalas dispares no queda ilegible).
    """
    items = [(universo[v]["corto"], universo[v]["clave"], universo[v]["simbolo"]) for v in valores]
    series_fechas, series_precios, errores = series_en_paralelo(items, dias)
    if auto:
        base_100 = len(series_precios) >= 2

    filas = []
    for label, precios in series_precios.items():
        vol = calcular_volatilidad(precios)
        filas.append(
            {
                "activo": label,
                "rendimiento": round(calcular_rendimiento_porcentual(precios[0], precios[-1]), 2),
                "volatilidad": round(vol, 3),
                "clasificacion": clasificar_volatilidad(vol),
                "peor_caida": round(calcular_drawdown_maximo(precios) * 100, 2),
            }
        )

    return {
        "chart": serie_payload(series_fechas, series_precios, base_100=base_100) if series_precios else None,
        "filas": filas,
        "errores": errores,
        "heatmap": heatmap_correlacion(series_precios) if correlacion and len(series_precios) >= 2 else None,
        "seleccion": set(valores),
    }


def _seleccion_valida(pedidos, universo, grupos, por_defecto, limite):
    """Filtra `pedidos` a valores existentes del/los grupo(s); si no queda nada, usa el default."""
    validos = [v for v in (pedidos or []) if v in universo and universo[v]["grupo"] in grupos]
    if not validos:
        validos = [v for v in por_defecto if v in universo]
    return validos[:limite]


@app.get("/comparar", response_class=HTMLResponse)
def comparar(
    request: Request,
    cripto_sel: list[str] | None = Query(default=None),
    sp_sel: list[str] | None = Query(default=None),
    activos: list[str] | None = Query(default=None),
    dias: int = 90,
):
    """Tres comparaciones base 100: cripto vs cripto, S&P vs S&P, y una mixta con correlacion."""
    if dias not in PERIODOS_COMPARAR.values():
        dias = 90

    universo = universo_disponible()

    # Opciones de cada selector, por precio descendente.
    cripto_opts = sorted(
        [(v, it) for v, it in universo.items() if it["grupo"] == "cripto"],
        key=lambda kv: kv[1]["precio"] or 0.0,
        reverse=True,
    )
    sp_opts = sorted(
        [(v, it) for v, it in universo.items()
         if it["grupo"] == "sp500" and it["simbolo"] != "^GSPC"],
        key=lambda kv: kv[1]["precio"] if kv[1]["precio"] is not None else -1.0,
        reverse=True,
    )
    # La mixta admite cripto, empresas y tambien el indice S&P 500 como activo.
    indice_opt = [(v, it) for v, it in universo.items() if v == "usa:^GSPC"]
    # Cripto primero y luego todo lo de S&P (indice + empresas), contiguos, para
    # que el selector del bloque mixto los muestre agrupados por categoria.
    mixto_opts = cripto_opts + indice_opt + sp_opts

    sel_crip = _seleccion_valida(cripto_sel, universo, {"cripto"}, _DEF_CRIPTO, _MAX_BLOQUE)
    sel_sp = _seleccion_valida(sp_sel, universo, {"sp500"}, _DEF_SP, _MAX_BLOQUE)
    sel_mix = _seleccion_valida(activos, universo, {"cripto", "sp500"}, _DEF_MIXTO, _MAX_BLOQUE)

    return templates.TemplateResponse(
        request,
        "comparar.html",
        {
            "vista": "comparar",
            "periodos": PERIODOS_COMPARAR,
            "dias": dias,
            "max_bloque": _MAX_BLOQUE,
            "cripto_opts": cripto_opts,
            "sp_opts": sp_opts,
            "mixto_opts": mixto_opts,
            "b_crip": _bloque_comparacion(universo, sel_crip, dias, correlacion=False, auto=True),
            "b_sp": _bloque_comparacion(universo, sel_sp, dias, correlacion=False, auto=True),
            "b_mix": _bloque_comparacion(universo, sel_mix, dias, correlacion=True, base_100=True),
            "glosario": GLOSARIO,
            "disclaimer": _DISCLAIMER,
        },
    )


@app.get("/salud")
def salud():
    """Healthcheck simple."""
    return JSONResponse({"estado": "ok"})


def main() -> None:
    """Punto de entrada para `python -m observatorio.web`."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
