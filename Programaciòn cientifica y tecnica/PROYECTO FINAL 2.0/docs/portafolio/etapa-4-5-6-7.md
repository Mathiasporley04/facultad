# Etapas 4 a 7 — Metricas, UI, Portfolio cifrado, pulido

## Etapa 4 — Metricas funcionales
- Modulo `metricas/` con seis funciones puras: rendimiento, volatilidad (con clasificacion cualitativa), correlacion, drawdown maximo, normalizacion a base 100, conversion entre monedas.
- 30 tests unitarios cubriendo casos tipicos, vacios, un solo elemento, valores extremos, monedas faltantes.
- Uso genuino de `map`/`filter`/`reduce`: `normalizar_a_base` con `map`, `Portfolio.valor_total_usd` con `reduce`.

## Etapa 5 — Vista Comparar
- Multi-select de hasta 9 activos (cripto + acciones USA + indice).
- Grafico Plotly de evolucion normalizada base 100.
- Tabla de metricas por activo con tooltip explicativo.
- Heatmap de correlaciones con escala RdYlGn de -1 a +1.
- Glosario embebido en `ui/glosario.py` y referenciado desde la UI.

## Etapa 6 — Portfolio cifrado
- `persistencia/cifrado.py`: Fernet (AES-128-CBC + HMAC-SHA256) con clave derivada via PBKDF2-SHA256 (200k iter).
- `persistencia/almacen.py`: roundtrip JSON cifrado + import/export CSV.
- Vista Streamlit con login por password, editor de tenencias, treemap de distribucion, valuacion en USD/UYU.
- 4 tests de roundtrip, password incorrecto, CSV.

## Etapa 7 — Normalizadores y docs
- `normalizadores/` con regex para tickers (`BTC-USD` -> `BTC`), fechas (ISO/Unix/Unix-ms) y validacion de input del usuario.
- 10 tests adicionales de normalizadores.
- `docs/etica.md`, `docs/glosario.md`, `docs/decisiones.md`, ADRs 001-003.

## Total tests
44 tests, 0 fallos.
