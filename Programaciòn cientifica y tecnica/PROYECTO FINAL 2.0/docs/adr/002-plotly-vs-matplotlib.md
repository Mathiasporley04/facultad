# ADR-002: Plotly como libreria de graficos

**Estado:** aceptado.

## Contexto
La aplicacion muestra series temporales, treemaps de portfolio y heatmaps de correlacion. Tiene que verse bien en una demo en vivo.

## Opciones evaluadas
1. **matplotlib** + **seaborn**: estandar cientifico, estatico.
2. **Plotly**: interactivo nativamente, bien integrado a Streamlit via `st.plotly_chart`.
3. **Altair**: declarativo, compatible con Streamlit.

## Decision
**Plotly.**

## Razones
- Interactividad nativa (hover, zoom, pan, leyenda toggleable). Mejora la demo significativamente.
- Calidad visual default superior a matplotlib sin esfuerzo adicional.
- API expressiva (`plotly.express`) para casos comunes (treemap, heatmap) y `graph_objects` para control fino.

## Consecuencias
- Mayor peso de dependencias (~30 MB). Aceptable: la app es local.
- No hay backend nativo de export a SVG vectorial sin dependencias extra (no critico para el alcance).
