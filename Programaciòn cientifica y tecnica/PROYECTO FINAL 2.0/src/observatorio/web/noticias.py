"""Noticias financieras desde feeds RSS publicos (sin API key).

Mezcla varias fuentes en espanol (cripto + bolsa), las ordena por fecha y
expone las mas recientes. Sigue el patron "nunca lanza" del resto de la capa
web: si un feed se cae seguimos con los demas; si fallan todos devolvemos lo
ultimo cacheado (o lista vacia) y la UI simplemente oculta la seccion.
"""
from __future__ import annotations

import re
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import unescape

import requests
from dateutil import parser as fecha_parser  # ya es dependencia del proyecto

# (etiqueta_fuente, url). Feeds en espanol verificados (200 + items parseables).
_FEEDS: list[tuple[str, str]] = [
    ("CriptoNoticias", "https://www.criptonoticias.com/feed/"),
    ("Investing", "https://es.investing.com/rss/news_25.rss"),
    ("Expansión", "https://e00-expansion.uecdn.es/rss/mercados.xml"),
]

# Varios medios devuelven 403 sin un User-Agent de navegador.
_UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
_TIMEOUT = 8
_TTL = 900.0  # 15 min: las noticias no cambian tanto y no conviene martillar los feeds.

_MIN = datetime.min.replace(tzinfo=timezone.utc)  # para ordenar las sin fecha al final.

# Para extraer la imagen de cada noticia (namespaces RSS + busqueda de <img>).
_MEDIA_NS = "{http://search.yahoo.com/mrss/}"
_CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"
_IMG_RE = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)
_URL_RE = re.compile(r"^https?://[^\s'\"()<>]+$")


def _texto(item: ET.Element, tag: str) -> str:
    e = item.find(tag)
    return (e.text or "").strip() if e is not None else ""


def _limpiar(html_txt: str, limite: int = 160) -> str:
    """Quita tags HTML, colapsa espacios y recorta a `limite` caracteres."""
    txt = unescape(re.sub(r"<[^>]+>", "", html_txt))
    txt = re.sub(r"\s+", " ", txt).strip()
    return (txt[:limite].rstrip() + "…") if len(txt) > limite else txt


def _parse_fecha(pub: str) -> datetime | None:
    """Parsea fechas RFC822 ('Thu, 04 Jun...') o ISO ('2026-06-04 14:46:39')."""
    if not pub:
        return None
    try:
        dt = fecha_parser.parse(pub)
    except (ValueError, OverflowError):
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _fecha_relativa(dt: datetime | None) -> str:
    if dt is None:
        return ""
    seg = (datetime.now(timezone.utc) - dt).total_seconds()
    if seg < 60:
        return "hace un momento"
    if seg < 3600:
        return f"hace {int(seg // 60)} min"
    if seg < 86400:
        return f"hace {int(seg // 3600)} h"
    dias = int(seg // 86400)
    return "ayer" if dias == 1 else f"hace {dias} días"


# Imagenes a descartar: pixeles de tracking y placeholders genericos sin valor.
_IMG_BLOQUEADAS = (
    "imrworldwide", "doubleclick", "scorecardresearch", "/pixel", "1x1",
    "blank.gif", "spacer", "world_news_2_108x81",
)


def _imagen_segura(url: str) -> str:
    """Acepta solo URLs http(s) simples y reales (descarta tracking/placeholders)."""
    url = (url or "").strip()
    if url.startswith("//"):
        url = "https:" + url
    if not _URL_RE.match(url):
        return ""
    low = url.lower()
    return "" if any(b in low for b in _IMG_BLOQUEADAS) else url


def _extraer_imagen(item: ET.Element) -> str:
    """Imagen destacada del item: media:*, <enclosure> o el 1er <img> real del cuerpo."""
    for tag in (_MEDIA_NS + "content", _MEDIA_NS + "thumbnail"):
        for m in item.findall(tag):
            url = _imagen_segura(m.get("url", ""))
            if url:
                return url
    for enc in item.findall("enclosure"):
        tipo = enc.get("type", "")
        if not tipo or tipo.startswith("image"):
            url = _imagen_segura(enc.get("url", ""))
            if url:
                return url
    for tag in (_CONTENT_NS + "encoded", "description"):
        e = item.find(tag)
        if e is not None and e.text:
            for src in _IMG_RE.findall(e.text):
                url = _imagen_segura(src)
                if url:
                    return url
    return ""


def _traer_un_feed(fuente: str, url: str) -> list[dict]:
    r = requests.get(url, headers=_UA, timeout=_TIMEOUT)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    salida = []
    for item in root.findall(".//item"):
        titulo = _texto(item, "title")
        enlace = _texto(item, "link")
        if not titulo or not enlace:
            continue
        fecha = _parse_fecha(_texto(item, "pubDate"))
        salida.append(
            {
                "titulo": unescape(titulo),
                "enlace": enlace,
                "fuente": fuente,
                "fecha": fecha,
                "fecha_fmt": _fecha_relativa(fecha),
                "resumen": _limpiar(_texto(item, "description")),
                "imagen": _extraer_imagen(item),
            }
        )
    return salida


def _traer_todo() -> list[dict]:
    """Trae y mezcla todos los feeds, ordenados por fecha descendente."""
    noticias: list[dict] = []
    for fuente, url in _FEEDS:
        try:
            noticias.extend(_traer_un_feed(fuente, url))
        except Exception:
            continue  # un feed caido no rompe a los demas.
    noticias.sort(key=lambda n: n["fecha"] or _MIN, reverse=True)
    return noticias


# --- Cache simple con TTL + degradacion elegante (sirve lo viejo si falla) ---
_lock = threading.Lock()
_cache: dict = {"ts": 0.0, "datos": []}


def noticias_recientes(limite: int = 10) -> list[dict]:
    """Hasta `limite` noticias recientes (cacheadas 15 min). Nunca lanza."""
    ahora = time.time()
    with _lock:
        if _cache["datos"] and ahora - _cache["ts"] < _TTL:
            return _cache["datos"][:limite]

    try:
        datos = _traer_todo()
    except Exception:
        datos = []

    if datos:
        with _lock:
            _cache["datos"] = datos
            _cache["ts"] = ahora
        return datos[:limite]

    # Todos los feeds fallaron: servir lo ultimo bueno si lo hay.
    with _lock:
        return _cache["datos"][:limite]


def noticias_destacadas(limite: int = 3) -> list[dict]:
    """Las mas recientes con imagen real (para las tarjetas con foto).

    Si no alcanzan, completa con las mas recientes sin imagen para que las
    tarjetas nunca queden vacias.
    """
    todas = noticias_recientes(10_000)  # todo el cache, ya ordenado por fecha
    con = [n for n in todas if n["imagen"]]
    if len(con) >= limite:
        return con[:limite]
    sin = [n for n in todas if not n["imagen"]]
    return (con + sin)[:limite]
