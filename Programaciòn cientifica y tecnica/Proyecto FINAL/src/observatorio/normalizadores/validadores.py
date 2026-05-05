"""Validacion de inputs del usuario via regex."""
from __future__ import annotations

import re

# Tickers: 1-6 alfanumericos, opcional prefijo ^ para indices, opcional .X (clase)
_REGEX_TICKER = re.compile(r"^\^?[A-Z0-9]{1,6}(\.[A-Z]{1,2})?$")


def es_ticker_valido(crudo: str) -> bool:
    if not crudo:
        return False
    return bool(_REGEX_TICKER.match(crudo.strip().upper()))
