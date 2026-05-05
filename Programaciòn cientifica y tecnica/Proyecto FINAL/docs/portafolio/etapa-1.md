# Etapa 1 — Setup y dominio base

## Que se hizo
- Estructura de carpetas siguiendo PROYECTO.md seccion 9.
- `pyproject.toml` con dependencias y target Python 3.11+.
- ABCs `FuenteDatos` y `Activo`. Clases `Mercado`, `Portfolio`, `Tenencia`. Excepciones del dominio.
- Tema custom de Streamlit en `.streamlit/config.toml`.

## Desafios
- Python 3.14 instalado en la maquina de desarrollo: algunas wheels tardan en estar disponibles. Se opta por aceptar 3.14 (todas las dependencias instalaron limpiamente, incluyendo numpy/pandas con wheels nativas).

## Decisiones
- `Activo` recibe la `FuenteDatos` por composicion en el constructor: facilita testing y mantiene OOP/funcional separados.
- `precio_actual_usd` polimorfico: cada subclase resuelve la conversion (cripto y USA = pasthrough, ARG requiere tasa, divisa es 1/cotizacion).
