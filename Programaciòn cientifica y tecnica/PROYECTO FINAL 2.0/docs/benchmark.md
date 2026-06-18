# Benchmark sync vs async

Script: `scripts/benchmark_async.py`. Compara consultar 7 cotizaciones de las tres fuentes (CoinGecko, Yahoo Finance, DolarApi UY) en modo secuencial vs paralelo (`asyncio.gather`).

## Resultado de referencia (corrida local)

| Modo  | Tiempo (s) | Peticiones |
|-------|-----------:|-----------:|
| SYNC  | 10.43      | 7          |
| ASYNC |  1.12      | 7          |

**Speedup: 9.29x**

Las llamadas son I/O-bound contra tres servicios distintos. La version async lanza las peticiones concurrentemente con `asyncio.gather`, lo que permite que las tres APIs sean consultadas en paralelo. La version sincronica espera secuencialmente cada una.

> Nota: en algunas corridas CoinGecko devuelve 429 (rate limit) por hacer las 3 cripto simultaneas. El sistema maneja la falla con `FuenteIndisponible` sin tumbar al resto, lo que demuestra el aislamiento de errores entre fuentes.

## Reproducir

```bash
.venv\Scripts\python.exe scripts\benchmark_async.py
```
