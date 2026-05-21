# Bitacora de decisiones tecnicas

## Stack
- **Streamlit** para UI: 100% Python, costo de desarrollo bajo, suficiente para presentacion academica.
- **Plotly** para visualizaciones: interactividad nativa (hover, zoom), mejor look default que matplotlib.
- **Pydantic v2** para validacion de datos en frontera con APIs externas (planeado, pendiente de aplicarse a respuestas concretas).
- **aiohttp** + **asyncio.gather** para paralelismo de fuentes. Yahoo se ejecuta en thread porque `yfinance` es sincrono.
- **cryptography (Fernet)** para portfolio: AES-128-CBC + HMAC-SHA256 en formato versionado.

## Hallazgos descubiertos durante el desarrollo
- **CoinGecko free tier** devuelve 429 cuando se hacen 3+ requests cripto en paralelo. Manejado con `FuenteIndisponible` por simbolo, sin tumbar las otras fuentes. Mitigacion futura: serializar las cripto o reducir la frecuencia.
- **data912.com** expone snapshot pero no historico publico. La vista Comparar excluye activos arg por ahora; vista Panorama solo muestra ultimo precio.
- **DolarApi UY**: endpoint `https://uy.dolarapi.com/v1/cotizaciones`. La cotizacion BROU se extrae filtrando por nombre.

## Convenciones reforzadas
- Idioma del dominio en espanol.
- Cero `print()` en codigo de aplicacion.
- Cada metrica es funcion pura, sin acceso a estado, sin red.
- No `except Exception` salvo en bordes externos.
