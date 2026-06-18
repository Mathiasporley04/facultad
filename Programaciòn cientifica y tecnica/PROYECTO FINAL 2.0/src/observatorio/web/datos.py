"""Capa de acceso a datos para la web.

Reutiliza las fuentes del dominio (que ya cachean internamente via
`@cache_ttl`) y expone helpers que nunca lanzan: ante una fuente caida
devuelven un valor vacio + un mensaje, para que la UI no se rompa.
"""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from observatorio.core.excepciones import FuenteIndisponible
from observatorio.core.fuente import FuenteDatos
from observatorio.core.tipos import PuntoPrecio
from observatorio.fuentes.registro import fuentes_default
from observatorio.web.noticias import noticias_recientes
from observatorio.web.sp500 import SP500_TOP

# Universo de activos comparables (los que tienen historico real).
UNIVERSO: dict[str, tuple[str, str]] = {
    "BTC (Bitcoin)": ("cripto", "BTC"),
    "ETH (Ethereum)": ("cripto", "ETH"),
    "SOL (Solana)": ("cripto", "SOL"),
    "AAPL (Apple)": ("usa", "AAPL"),
    "MSFT (Microsoft)": ("usa", "MSFT"),
    "GOOGL (Alphabet)": ("usa", "GOOGL"),
    "TSLA (Tesla)": ("usa", "TSLA"),
    "NVDA (Nvidia)": ("usa", "NVDA"),
    "S&P 500 (^GSPC)": ("usa", "^GSPC"),
}

# Tarjetas del panorama: (clave_fuente, simbolo, etiqueta, icono).
TARJETAS_PANORAMA: list[tuple[str, str, str, str]] = [
    ("uy", "USD", "Dólar (Uruguay)", "dolar"),
    ("cripto", "BTC", "Bitcoin", "bitcoin"),
    ("usa", "^GSPC", "S&P 500", "tendencia"),
]

# Periodos disponibles -> dias.
PERIODOS_PANORAMA: dict[str, int] = {"7 dias": 7, "30 dias": 30, "90 dias": 90}
PERIODOS_COMPARAR: dict[str, int] = {
    "30 dias": 30,
    "90 dias": 90,
    "180 dias": 180,
    "1 año": 365,
}


@lru_cache(maxsize=1)
def fuentes() -> dict[str, FuenteDatos]:
    """Singletons de las fuentes (una sola instancia por proceso)."""
    return fuentes_default()


def cotizar_seguro(clave_fuente: str, simbolo: str) -> tuple[str, str]:
    """Devuelve (valor_formateado, error). Nunca lanza."""
    try:
        c = fuentes()[clave_fuente].precio_actual(simbolo)
        return f"{c.precio:,.2f} {c.moneda}", ""
    except FuenteIndisponible as e:
        return "—", str(e)


def obtener_serie(
    clave_fuente: str, simbolo: str, dias: int
) -> tuple[list[datetime], list[float]]:
    """Devuelve (fechas, precios) del historico. Lista vacia si la fuente falla."""
    # Cuantizamos la ventana a la hora en curso para que el cache TTL del
    # historico sea efectivo. Sin esto, cada request genera un `now()` distinto
    # (al microsegundo), la clave de cache nunca coincide y se golpea la API en
    # cada llamada; CoinGecko (market_chart, plan gratis) responde 429 enseguida.
    # Con la hora fija, hay como mucho una llamada por (simbolo, dias) por hora.
    hasta = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    desde = hasta - timedelta(days=dias)
    try:
        puntos: list[PuntoPrecio] = fuentes()[clave_fuente].historico(simbolo, desde, hasta)
    except FuenteIndisponible:
        return [], []
    return [p.fecha for p in puntos], [p.precio for p in puntos]


# --- Acceso concurrente: cada vista pide varias fuentes en paralelo ---
# Las llamadas son I/O-bound (HTTP), asi que un pool de hilos paraleliza bien;
# el tiempo total pasa de la suma de latencias a la de la fuente mas lenta.
_POOL = ThreadPoolExecutor(max_workers=8, thread_name_prefix="obs-fuentes")


def _tarjeta_dolar(etiqueta: str, icono: str) -> dict:
    """Tarjeta del dolar UY mostrando compra y venta por separado."""
    try:
        compra, venta = fuentes()["uy"].compra_venta("USD")
        return {
            "etiqueta": etiqueta,
            "icono": icono,
            "error": "",
            "compra": f"{compra:,.2f}",
            "venta": f"{venta:,.2f}",
        }
    except FuenteIndisponible as e:
        return {"etiqueta": etiqueta, "icono": icono, "error": str(e)}


def cotizaciones_panorama() -> list[dict]:
    """Cotiza en paralelo las cuatro tarjetas del panorama."""

    def una(tarjeta: tuple[str, str, str, str]) -> dict:
        clave, simbolo, etiqueta, icono = tarjeta
        if clave == "uy":
            return _tarjeta_dolar(etiqueta, icono)
        valor, error = cotizar_seguro(clave, simbolo)
        return {"etiqueta": etiqueta, "valor": valor, "error": error, "icono": icono}

    return list(_POOL.map(una, TARJETAS_PANORAMA))


def series_en_paralelo(
    items: list[tuple[str, str, str]], dias: int
) -> tuple[dict[str, list[datetime]], dict[str, list[float]], list[str]]:
    """Trae varios historicos en paralelo.

    `items` es una lista de `(label, clave_fuente, simbolo)`. Devuelve
    `(series_fechas, series_precios, errores)` preservando el orden de entrada.
    """

    def una(item: tuple[str, str, str]):
        label, clave, simbolo = item
        fechas, precios = obtener_serie(clave, simbolo, dias)
        return label, fechas, precios

    series_fechas: dict[str, list[datetime]] = {}
    series_precios: dict[str, list[float]] = {}
    errores: list[str] = []
    for label, fechas, precios in _POOL.map(una, items):
        if precios:
            series_fechas[label] = fechas
            series_precios[label] = precios
        else:
            errores.append(label)
    return series_fechas, series_precios, errores


# --- Universo pickeable (cripto top + S&P 500 top ~100) ---


def _fmt_precio(p: float | None) -> str:
    if p is None:
        return "—"
    if p >= 1:
        return f"${p:,.2f}"
    return "$" + f"{p:,.6f}".rstrip("0").rstrip(".")


def universo_disponible() -> dict[str, dict]:
    """Activos elegibles con su precio actual, para el selector de Comparar.

    Devuelve {value: {grupo, clave, simbolo, corto, nombre, precio, precio_fmt}}
    donde `value` es estable (p.ej. 'cripto:BTC', 'usa:AAPL'). Resiliente: si una
    fuente falla, incluye lo que pueda (los precios faltantes quedan en None).
    """
    universo: dict[str, dict] = {}

    # Indice S&P 500 como referencia (no tiene precio por accion).
    universo["usa:^GSPC"] = {
        "grupo": "sp500", "clave": "usa", "simbolo": "^GSPC",
        "corto": "S&P 500", "nombre": "S&P 500 (índice)", "precio": None, "precio_fmt": "índice",
    }

    # Cripto: top por capitalizacion con precio (una sola llamada a CoinGecko).
    try:
        for c in fuentes()["cripto"].mercados(100):
            universo[f"cripto:{c['simbolo']}"] = {
                "grupo": "cripto", "clave": "cripto", "simbolo": c["simbolo"],
                "corto": c["simbolo"], "nombre": c["nombre"],
                "precio": c["precio"], "precio_fmt": _fmt_precio(c["precio"]),
            }
    except FuenteIndisponible:
        pass

    # S&P 500: top ~100 con precios en lote (yfinance).
    precios: dict[str, float] = {}
    try:
        precios = fuentes()["usa"].precios_bulk(tuple(t for t, _ in SP500_TOP))
    except FuenteIndisponible:
        pass
    for ticker, nombre in SP500_TOP:
        p = precios.get(ticker.upper())
        universo[f"usa:{ticker}"] = {
            "grupo": "sp500", "clave": "usa", "simbolo": ticker,
            "corto": ticker, "nombre": nombre, "precio": p, "precio_fmt": _fmt_precio(p),
        }
    return universo


# --- Precalentamiento del cache ---
# El arranque en frio es lento porque las APIs externas (sobre todo yfinance)
# tardan. Un hilo en segundo plano mantiene el cache caliente: al refrescar mas
# seguido que el TTL, el usuario casi nunca pega contra una llamada fria. El
# propio `@cache_ttl` evita golpear la API si el dato sigue vigente.

# Lo que ve el usuario al entrar: panorama (dias=30) y el comparar por defecto.
_PRECALENTAR_PANORAMA = [("BTC", "cripto", "BTC"), ("S&P 500", "usa", "^GSPC")]
_PRECALENTAR_COMPARAR = [("BTC (Bitcoin)", "cripto", "BTC"), ("S&P 500 (^GSPC)", "usa", "^GSPC")]


def _precalentar_una_vez() -> None:
    try:
        cotizaciones_panorama()
        series_en_paralelo(_PRECALENTAR_PANORAMA, 30)
        universo_disponible()  # mercados cripto + precios S&P en lote (cacheados)
        series_en_paralelo(_PRECALENTAR_COMPARAR, 90)
        noticias_recientes()  # mantener las noticias de la home calientes
    except Exception:
        # El precalentamiento nunca debe tumbar el servidor.
        pass


_precalentado = False


def iniciar_precalentamiento(intervalo: float = 45.0) -> None:
    """Lanza (una sola vez) el hilo que mantiene el cache caliente."""
    global _precalentado
    if _precalentado:
        return
    _precalentado = True

    def bucle() -> None:
        while True:
            _precalentar_una_vez()
            time.sleep(intervalo)

    threading.Thread(target=bucle, name="obs-precalentar", daemon=True).start()
