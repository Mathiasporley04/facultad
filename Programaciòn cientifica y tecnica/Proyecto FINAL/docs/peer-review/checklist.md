# Checklist de peer review

## Setup
- [ ] El README permite levantar el proyecto en menos de 5 minutos en una maquina limpia.
- [ ] `pytest` corre sin errores.
- [ ] `streamlit run src/observatorio/ui/app.py` abre la app sin warnings criticos.

## Cumplimiento academico
- [ ] OOP: jerarquias `Activo` y `FuenteDatos` con ABCs y polimorfismo real.
- [ ] Funcional: modulo `metricas/` con funciones puras + uso de `map`/`filter`/`reduce`.
- [ ] Async: `aiohttp` + `asyncio.gather`, benchmark documentado (`docs/benchmark.md`).
- [ ] Regex: normalizadores en `normalizadores/` con tests.
- [ ] Etica: `docs/etica.md` con marco legal UY/AR + sesgos del producto.

## UX
- [ ] Disclaimer visible en sidebar y al pie de cada vista.
- [ ] Tooltips para metricas tecnicas (volatilidad, correlacion, drawdown).
- [ ] Errores de fuentes manejados visualmente (warning) sin tumbar la app.

## Codigo
- [ ] No hay `print()` en codigo de aplicacion.
- [ ] Type hints en funciones publicas.
- [ ] Modulo `metricas/` con cobertura > 90%.

## Reporte
- Cosas que funcionaron especialmente bien:
- Friction points:
- Sugerencias de mejora:
