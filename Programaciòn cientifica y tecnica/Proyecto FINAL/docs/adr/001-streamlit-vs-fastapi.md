# ADR-001: Streamlit como framework de UI

**Estado:** aceptado.

## Contexto
La aplicacion necesita una UI con varias vistas, graficos interactivos, formularios y persistencia local. El equipo es una sola persona con tiempo acotado.

## Opciones evaluadas
1. **Streamlit**: framework Python centrado en data apps.
2. **FastAPI + frontend custom (React/Vue)**: backend Python + frontend JS.
3. **Dash (Plotly)**: similar a Streamlit con enfoque mas rigido en callbacks.

## Decision
**Streamlit.**

## Razones
- Costo de desarrollo significativamente menor (semanas vs meses).
- Resultado visual suficientemente profesional para presentacion academica.
- 100% Python: cohesion del proyecto, no hay context switch a JS/TS.
- Soporta `st.cache_data` y `st.cache_resource` que cubren caching de UI sin trabajo extra.

## Consecuencias
- Menor control sobre el layout fino (aceptable).
- Performance limitada en datasets muy grandes (no es un problema con N≤50 activos).
- Resultado visual menos diferenciado que un frontend custom (aceptable para el alcance).
