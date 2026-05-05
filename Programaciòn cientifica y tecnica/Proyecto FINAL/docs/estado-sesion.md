# Estado del proyecto — sesion 2026-05-05

## Resumen
Implementacion completa de las 7 etapas definidas en `PROYECTO.md` seccion 11. La aplicacion corre en `http://localhost:8501` via Streamlit.

## Stack instalado en .venv (Python 3.14.3)
streamlit 1.57, plotly 6.7, pandas 3.0, numpy 2.4, pydantic 2.13, requests 2.33, yfinance 1.3, cryptography 48, aiohttp 3.13, python-dateutil 2.9, pytest 9.0.

## Comandos
```bash
.venv\Scripts\activate
streamlit run src/observatorio/ui/app.py        # UI en localhost:8501
.venv\Scripts\python.exe -m pytest tests -q     # 44 tests
.venv\Scripts\python.exe scripts\benchmark_async.py  # speedup ~9x
```

## Etapas completadas
| # | Hito | Evidencia |
|---|------|-----------|
| 1 | Setup + dominio | `src/observatorio/core/`, `pyproject.toml`, `.streamlit/config.toml` |
| 2 | Fuentes sync | `fuentes/{coingecko,yahoo_finance,data912,dolar_api_uy}.py` |
| 3 | Async + benchmark | `precio_actual_async`, `scripts/benchmark_async.py`, `docs/benchmark.md` (9.29x speedup medido) |
| 4 | Metricas funcionales | `metricas/` (6 fns puras) + 30 tests en `tests/test_metricas/` |
| 5 | Vista Comparar + glosario | `ui/vistas/comparar.py`, `ui/glosario.py` |
| 6 | Portfolio cifrado | `persistencia/{cifrado,almacen}.py`, `ui/vistas/portfolio.py` + 4 tests |
| 7 | Regex + docs | `normalizadores/` + 10 tests, `docs/etica.md`, `docs/glosario.md`, `docs/decisiones.md`, ADRs 001-003, `docs/portafolio/etapa-*`, `docs/peer-review/checklist.md` |

## Decisiones clave
- **Idioma del dominio:** espanol (PROYECTO.md seccion 10).
- **Yahoo Finance** se mantiene sync (yfinance es bloqueante) y se ejecuta en thread via `asyncio.to_thread` cuando se llama desde `precio_actual_async`.
- **CoinGecko free tier** devuelve 429 al disparar 3 cripto en paralelo. Manejado via `FuenteIndisponible` por simbolo.
- **data912** no expone historico publico: vista Comparar excluye activos arg.
- **Cifrado portfolio**: Fernet + PBKDF2-SHA256 200k iter, salt fijo (es app local mono-usuario).

## Pendientes no criticos (post-MVP)
- Tasa ARS real (MEP) en lugar de hardcoded en `Portfolio`.
- Validacion explicita Pydantic v2 sobre respuestas de APIs (hoy es implicita via `float()`).
- Modal de aceptacion del disclaimer al primer uso.
- Tests de integracion con APIs reales (skip en CI).
