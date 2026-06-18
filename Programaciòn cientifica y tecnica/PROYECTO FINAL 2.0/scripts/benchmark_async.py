"""Benchmark sync vs async sobre las tres fuentes de datos."""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from observatorio.core.excepciones import FuenteIndisponible
from observatorio.fuentes.registro import fuentes_default

PETICIONES = [
    ("cripto", "BTC"),
    ("cripto", "ETH"),
    ("cripto", "SOL"),
    ("usa", "AAPL"),
    ("usa", "MSFT"),
    ("uy", "USD"),
    ("uy", "EUR"),
]


def correr_sync(fuentes):
    resultados = {}
    for clave, simbolo in PETICIONES:
        try:
            resultados[(clave, simbolo)] = fuentes[clave].precio_actual(simbolo).precio
        except FuenteIndisponible as e:
            resultados[(clave, simbolo)] = f"ERR: {e}"
    return resultados


async def correr_async(fuentes):
    async def una(clave, simbolo):
        try:
            c = await fuentes[clave].precio_actual_async(simbolo)
            return (clave, simbolo), c.precio
        except FuenteIndisponible as e:
            return (clave, simbolo), f"ERR: {e}"

    pares = await asyncio.gather(*[una(k, s) for k, s in PETICIONES])
    return dict(pares)


def main() -> None:
    # Construyo fuentes nuevas para cada modo asi el cache no contamina
    fuentes_s = fuentes_default()
    t0 = time.perf_counter()
    res_s = correr_sync(fuentes_s)
    t_sync = time.perf_counter() - t0

    fuentes_a = fuentes_default()
    t0 = time.perf_counter()
    res_a = asyncio.run(correr_async(fuentes_a))
    t_async = time.perf_counter() - t0

    print(f"SYNC : {t_sync:.2f}s  ({len(PETICIONES)} peticiones)")
    print(f"ASYNC: {t_async:.2f}s  ({len(PETICIONES)} peticiones)")
    if t_async > 0:
        print(f"Speedup: {t_sync / t_async:.2f}x")

    print("\nResultados (async):")
    for k, v in res_a.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
