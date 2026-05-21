"""Normalizacion de tickers a forma canonica usando regex."""
from __future__ import annotations

import re

# Sufijos comunes que distintas APIs anaden
_SUFIJOS_CRIPTO = re.compile(r"[-/]?(USD|USDT|USDC)$", re.IGNORECASE)
# Caracteres no validos
_LIMPIAR = re.compile(r"[^A-Z0-9\^.]")


def normalizar_ticker(crudo: str) -> str:
    """Convierte BTC-USD, btcusdt, " btc " a 'BTC'. Preserva ^GSPC y prefijos."""
    if not crudo:
        return ""
    t = crudo.strip().upper()
    # Quitar sufijos cripto solo si el resto sigue siendo alfanumerico no vacio
    sin_sufijo = _SUFIJOS_CRIPTO.sub("", t)
    if sin_sufijo and sin_sufijo != t:
        t = sin_sufijo
    return _LIMPIAR.sub("", t)
