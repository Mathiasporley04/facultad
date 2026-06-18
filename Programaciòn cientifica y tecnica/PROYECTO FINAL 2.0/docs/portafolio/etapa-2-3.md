# Etapas 2 y 3 — Fuentes de datos (sync) y migracion a async

## Que se hizo
- Tres fuentes funcionando contra APIs reales: CoinGecko, Yahoo Finance (yfinance), DolarApi UY.
- Decorador `cache_ttl(ttl)` reutilizable para evitar pegarle a las APIs en cada `st.rerun()`.
- Implementacion async de `precio_actual_async` en CoinGecko y DolarApiUY. Yahoo se mantiene sync y se ejecuta en thread via `asyncio.to_thread`.
- Script `scripts/benchmark_async.py` y reporte `docs/benchmark.md`.

## Resultados
- **Sync**: 10.43s (7 peticiones).
- **Async**: 1.12s. **Speedup ≈ 9.3x**.

## Desafios
- CoinGecko free tier devuelve 429 al disparar 3 cripto en paralelo. Se acepta como degradacion temporal: la arquitectura aisla el error por simbolo.
