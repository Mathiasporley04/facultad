# Estado del proyecto — sesion 2026-05-19 (V2, migrado)

## Resumen
Implementacion de los ajustes V2 acordados a partir del analisis de coherencia entre `PROYECTO V2.md`, `pipeline_observatorio V2.md` y `diagramas_uml V2.html`. **El proyecto se consolido en una sola carpeta**: `PROYECTO FINAL 2.0/`. La carpeta vieja `Proyecto FINAL/` fue eliminada. El historial de git se mantiene intacto porque el `.git/` vive un nivel arriba (`facultad/`); los archivos del observatorio aparecen como renames en el proximo commit.

**Ubicacion canonica:** `C:\Users\mathi\Desktop\facultad\Programaciòn cientifica y tecnica\PROYECTO FINAL 2.0\`.
La aplicacion corre en `http://localhost:8501` (puerto explicito).

## Stack instalado en .venv (Python 3.14.3)
streamlit 1.57, plotly 6.7, pandas 3.0, numpy 2.4, pydantic 2.13, requests 2.33, yfinance 1.3, cryptography 48, aiohttp 3.13, python-dateutil 2.9, pytest 9.0.

## Comandos
```bash
.venv\Scripts\activate
# UI en localhost:8501 (puerto explicito para evitar colisiones con otras apps Streamlit)
.venv\Scripts\python.exe -m streamlit run src/observatorio/ui/app.py --server.port 8501
# 76 tests (44 originales + 32 nuevos V2)
.venv\Scripts\python.exe -m pytest tests -q
# Benchmark sync vs async (speedup ~9x)
.venv\Scripts\python.exe scripts\benchmark_async.py
```

## Estado por etapa (post V2)

| # | Hito | Evidencia |
|---|------|-----------|
| 1 | Setup + dominio | `src/observatorio/core/`, `pyproject.toml`, `.streamlit/config.toml` |
| 2 | Fuentes sync | `fuentes/{coingecko,yahoo_finance,dolar_api_uy}.py` |
| 3 | Async + benchmark | `precio_actual_async`, `scripts/benchmark_async.py`, `docs/benchmark.md` (9.29x medido) |
| 4 | Metricas funcionales | `metricas/` (6 fns puras) + 30 tests en `tests/test_metricas/` |
| 5 | Vista Comparar + glosario | `ui/vistas/comparar.py`, `ui/glosario.py` |
| 6 | Portfolio cifrado | `persistencia/{cifrado,almacen}.py` (clase `AlmacenCifrado`), `ui/vistas/portfolio.py` |
| 7 | Regex + docs | `normalizadores/`, `docs/etica.md`, `docs/glosario.md`, ADRs 001-003, portafolio, peer-review |

## Cambios V2 aplicados al codigo

1. **`AlmacenCifrado` como clase OOP** (`persistencia/almacen.py`). Atributos `ruta`, `salt`, `iteraciones`. Metodos publicos `guardar/cargar/existe`. Primitivas protegidas `_derivar_clave`, `_cifrar`, `_descifrar`. Funciones legacy (`guardar_portfolio`, etc.) quedan como wrappers thin para compatibilidad con tests viejos.
2. **Modelos Pydantic** en `fuentes/esquemas.py`: `CotizacionDTO`, `PuntoPrecioDTO`, helpers `validar_cotizacion`, `validar_historico`. Los DTOs canonican (`simbolo`/`moneda` upper) y validan invariantes (precio > 0, moneda len=3). Disponibles para integrarse en las 3 fuentes; hoy no estan invocados desde el codigo de produccion.
3. **Export XML del portfolio** (`tenencias_a_xml`, `xml_a_tenencias`). Cubre la directriz 7.1 con los 3 formatos del PDF: JSON (APIs) + CSV + XML. La vista portfolio agrega boton "Exportar XML" e importador que detecta `.xml` o `.csv` por extension.
4. **`Tenencia` ampliada**: `precio_compra: float = 0.0`. Metodos `valor_actual(tasas)` y `pnl(tasas)`. La vista portfolio muestra una columna editable "Precio de compra (USD)" y una tabla "PnL por posicion".
5. **`Portfolio` ampliado**: `moneda_base`, `distribucion()` (porcentaje por simbolo), `filtrar(predicado)` (uso de `filter`), `exportar_csv()`, `exportar_xml()`, `desde_dicts(...)`. `valor_total_usd` queda como alias de `valor_total` por compatibilidad.
6. **`Mercado` ampliado**: `moneda_base`, `refrescar_precios_async()` (usa `asyncio.gather` con `return_exceptions`), `correlaciones(desde, hasta)` (matriz NxN), `filtrar(predicado)`.
7. **Subclases de `Activo` con atributos especificos**: `Cripto(market_cap, ranking)`, `AccionUSA(sector)`, `Divisa(par, tipo_cotizacion)`. La herencia ya no se ve "decorativa".

## Decisiones clave (sin cambios V2)
- Idioma del dominio: espanol (PROYECTO.md seccion 10).
- Yahoo se mantiene sync (yfinance bloqueante) y corre en thread via `asyncio.to_thread` cuando se llama async.
- CoinGecko free tier devuelve 429 con 3 cripto en paralelo: aislado via `FuenteIndisponible` por simbolo.
- Cifrado: Fernet + PBKDF2-SHA256 200k iter, salt fijo (app local mono-usuario).

## Tests
**76 pasando, 0 fallos** (44 originales + 32 nuevos V2). Distribucion:
- `tests/test_metricas/`: 30 tests (rendimiento, volatilidad, correlacion, drawdown, normalizacion, conversion).
- `tests/test_normalizadores/`: 10 tests (tickers, fechas, validadores).
- `tests/test_persistencia/`: 10 tests (cifrado helpers, `AlmacenCifrado` clase, CSV roundtrip, XML roundtrip, errores).
- `tests/test_fuentes/`: 6 tests (Pydantic DTOs y validators).
- `tests/test_activos/`: 7 tests (polimorfismo `precio_actual_usd`, atributos especificos, delegacion de `obtener_historico`).
- `tests/test_portfolio/`: 9 tests (`Tenencia.pnl`, `Portfolio.distribucion`, `valor_total` con `reduce`, `filtrar`, exports CSV/XML).
- `tests/test_mercado/`: 4 tests (`filtrar`, `correlaciones` con series identicas → corr=1, `refrescar_precios_async`).

## Pendientes no criticos (post V2)
- **Integrar Pydantic en las 3 fuentes**: hoy `CotizacionDTO`/`PuntoPrecioDTO` existen pero las fuentes construyen `Cotizacion` directamente. Cambiar para que pasen por `validar_cotizacion` cierra el ADR-003 V2 a nivel de codigo.
- **Tasa ARS real (MEP)**: sigue hardcoded en la UI (`tasa_ars = 1000.0`).
- **Modal de aceptacion del disclaimer al primer uso**.
- **Vista "Acerca de"** (mencionada en `docs/etica.md` como "en construccion").
- **Renombrar ADR `003-fernet-portfolio.md`** a `005-...` y crear los ADRs 003 (Pydantic), 004 (OOP/funcional), 006 (cache TTL), 007 (idioma).
- **Reflejar V2 en `docs/portafolio/`** (idealmente abrir `etapa-8-v2.md` con la bitacora de los cambios).
- **Tests de integracion** contra APIs reales (skip en CI).

## Layout actual
```
PROYECTO FINAL 2.0/
├── PROYECTO V2.md                              # espec del proyecto
├── pipeline_observatorio V2.md
├── diagramas_uml V2.html
├── Proyecto-Final-Programacion-Cientifica-y-Tecnica.pdf
├── README.md
├── pyproject.toml
├── .gitignore
├── .streamlit/                                 # tema custom
├── .venv/                                      # python 3.14 + deps (no commitear)
├── src/observatorio/                           # codigo V2
│   ├── core/        (Activo, FuenteDatos, Mercado, Portfolio, Tenencia, tipos)
│   ├── activos/     (Cripto, AccionUSA, Divisa con atributos especificos)
│   ├── fuentes/     (3 APIs + cache + registro + esquemas Pydantic)
│   ├── metricas/    (6 funciones puras)
│   ├── normalizadores/ (regex: tickers, fechas, validadores)
│   ├── persistencia/ (clase AlmacenCifrado + CSV/XML)
│   └── ui/          (Streamlit: panorama, comparar, portfolio)
├── tests/          (76 tests)
├── scripts/        (benchmark_async.py)
└── docs/           (etica, glosario, decisiones, adr/, portafolio/, peer-review/)
```

## Procesos en ejecucion (sesion actual)
- Streamlit V2: PID variable, puerto **8501 explicito** (`--server.port 8501`). Background task ID al momento del cierre: `bvqr5kw3p`.
- Antes de relanzar, matar cualquier python.exe residual con `Stop-Process -Id <PID> -Force` o `Get-Process python | Stop-Process -Force` si no hay otras apps Python sensibles abiertas.

## Como retomar la sesion
1. `cd "C:\Users\mathi\Desktop\facultad\Programaciòn cientifica y tecnica\PROYECTO FINAL 2.0"`.
2. Activar venv: `.\.venv\Scripts\activate`.
3. Levantar app: `.\.venv\Scripts\python.exe -m streamlit run src\observatorio\ui\app.py --server.port 8501`.
4. Si `Address in use`: matar python existente o usar `--server.port 8502`.
5. Para correr tests: `.\.venv\Scripts\python.exe -m pytest tests -q` (debe dar 76 passed).
