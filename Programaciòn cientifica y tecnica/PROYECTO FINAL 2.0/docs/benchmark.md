# Benchmark sync vs async

Script: `scripts/benchmark_async.py`. Compara consultar 8 cotizaciones de las cuatro fuentes (CoinGecko, Yahoo Finance, data912, DolarApi UY) en modo secuencial vs paralelo (`asyncio.gather`).

## Resultado de referencia (corrida local)

| Modo  | Tiempo (s) | Peticiones |
|-------|-----------:|-----------:|
| SYNC  | 10.43      | 8          |
| ASYNC |  1.12      | 8          |

**Speedup: 9.29x**

Las llamadas son I/O-bound contra cuatro servicios distintos. La version async lanza las peticiones concurrentemente con `asyncio.gather`, lo que permite que las cuatro APIs sean consultadas en paralelo. La version sincronica espera secuencialmente cada una.

> Nota: en algunas corridas CoinGecko devuelve 429 (rate limit) por hacer las 3 cripto simultaneas. El sistema maneja la falla con `FuenteIndisponible` sin tumbar al resto, lo que demuestra el aislamiento de errores entre fuentes.

## Reproducir

```bash
.venv\Scripts\python.exe scripts\benchmark_async.py
```
