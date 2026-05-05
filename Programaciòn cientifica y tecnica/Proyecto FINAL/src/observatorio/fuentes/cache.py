"""Cache en memoria con TTL para fuentes de datos."""
from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable

_TTL_DEFAULT = 60.0


def cache_ttl(ttl_segundos: float = _TTL_DEFAULT) -> Callable:
    """Decorador: cachea retornos de un metodo por (args, kwargs)."""

    def decorador(fn: Callable) -> Callable:
        store: dict[tuple, tuple[float, Any]] = {}

        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = (args[1:], tuple(sorted(kwargs.items())))
            ahora = time.time()
            if key in store:
                ts, valor = store[key]
                if ahora - ts < ttl_segundos:
                    return valor
            valor = fn(*args, **kwargs)
            store[key] = (ahora, valor)
            return valor

        return wrapper

    return decorador
