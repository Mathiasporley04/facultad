# Decisiones de diseño — Pipeline ENG vs ESP Champions League

## Descripción del problema

Dado un conjunto de archivos `.txt` con resultados de la UEFA Champions League
(temporadas 2011/12 a 2024/25), identificar todos los cruces (eliminatorias)
entre clubes ingleses y españoles desde octavos en adelante, y determinar
quién ganó cada uno.

## Dominio y unidad de análisis

El dominio de esta estadística está formado por todos los cruces de fase
eliminatoria de la UEFA Champions League entre clubes de España e Inglaterra
desde la temporada 2011/12 hasta la 2024/25. La unidad que se analiza es el
cruce, no los partidos individuales.

Dentro de este dominio se incluyen los enfrentamientos de octavos, cuartos,
semifinales y finales, y en la temporada 2024/25 también los play-offs del
nuevo formato, ya que forman parte de la fase eliminatoria. Quedan fuera los
partidos de fase de liga o grupos, los cruces contra equipos de otros países
y los enfrentamientos entre clubes del mismo país.

El resultado que se registra en cada caso es qué país avanzó en el cruce,
por lo que la estadística mide cuántas veces avanzaron los clubes españoles
y cuántas veces avanzaron los clubes ingleses en enfrentamientos directos
entre ambos.

---

## Estructura del pipeline

El script se divide en **6 funciones**, una por paso, con responsabilidad única.
El `main` las encadena explícitamente para que el flujo sea legible.

```
cargar_archivos → inspeccionar → limpiar → validar → transformar → exportar
```

Cada función recibe exactamente la salida de la anterior. No hay estado global
mutable ni efectos secundarios entre pasos.

---

## Paso 01 — CARGAR

**Decisión: buscar `cl.txt` recursivamente, no aceptar `el.txt` ni `conf.txt`.**

Los archivos están organizados en subcarpetas por temporada
(`champions-league/2011-12/cl.txt`). Se usa `os.walk()` para recorrerlas sin
necesitar conocer los nombres exactos de carpeta. Solo se procesan archivos
llamados `cl.txt` para no mezclar Champions con Europa League o Conference League.

**Decisión: extraer temporada del encabezado `= UEFA Champions League YYYY/YY`.**

Esta línea aparece una sola vez por archivo y es la única fuente confiable del
año. Se extrae con regex `\d{4}/\d{2}` y se guarda tal cual (ej. `"2011/12"`).

**Decisión: detectar fase con el carácter `»` como marcador.**

Todas las secciones del archivo abren con `»`. Al encontrar una, se actualiza
`stage_actual`. Los partidos que siguen heredan esa fase hasta el próximo `»`.

**Decisión: separar equipo 1 y equipo 2 usando ` v ` como delimitador.**

El formato es consistente en todos los archivos. El separador siempre tiene
espacios a ambos lados, lo que evita falsos positivos con letras "v" en nombres.

**Decisión: delimitar el final del nombre del equipo 2 buscando el último `(COD)`.**

El código de país siempre cierra el nombre del equipo. Al encontrar el último
patrón `([A-Z]{2,3})` en la línea restante, todo lo que sigue es el marcador.

---

## Paso 02 — INSPECCIONAR

**Decisión: mostrar fases y países únicos antes de cualquier transformación.**

Esto permite detectar fases con nombres inesperados (ej. `Gruppe G` en alemán)
o códigos de país inusuales antes de que el filtro los descarte silenciosamente.

---

## Paso 03 — LIMPIAR

**Decisión: parsear el marcador en tres casos con regex.**

Los archivos tienen tres formatos de marcador:
- `X-Y (A-B)` — resultado normal
- `X-Y a.e.t. (...)` — prórroga sin penales
- `X-Y pen. A-B a.e.t. (...)` — penales; `X-Y` es la tanda, `A-B` el partido

En el caso con penales, el marcador para el agregado es el del partido (`A-B`),
no el de la tanda. El de la tanda se guarda separado en `pen_t1` / `pen_t2`.

**Decisión: normalizar nombres con un diccionario de aliases.**

El mismo club aparece con nombres distintos según el año (ej. `FC Barcelona`
vs `Barcelona`, `Real Madrid CF` vs `Real Madrid`). La normalización se aplica
convirtiendo el nombre a minúsculas antes de buscar en el diccionario, para
que la comparación sea case-insensitive. Si el nombre no está en el diccionario,
se aplica `.title()` como fallback.

**Decisión: descartar filas con N.N. o sin marcador válido.**

`N.N.` indica que el rival aún no estaba definido al momento de generar el
archivo. Estas filas no aportan información y se descartan explícitamente.

---

## Paso 04 — VALIDAR

**Decisión: filtrar por año de fin de temporada, no por año de inicio.**

`"2011/12"` representa la temporada que *termina* en 2012. El año de fin se
calcula como `int(season.split("/")[0]) + 1`. El rango válido es 2012–2025.

**Decisión: usar lista blanca (`FASES_POST_GRUPOS`) en lugar de lista negra.**

Es más seguro incluir explícitamente las fases que interesan que excluir las
de grupos. Si aparece una fase nueva con nombre inesperado, queda fuera por
defecto en lugar de incluirse por accidente.

**Decisión: identificar cruces ENG vs ESP con un `set` de dos países.**

`{r["team1_pais"], r["team2_pais"]} == {"ENG", "ESP"}` es True sin importar
qué equipo jugó de local. Evita tener que comprobar los dos órdenes posibles.

---

## Paso 05 — TRANSFORMAR

**Decisión: agrupar con `frozenset` como parte de la clave.**

La clave de agrupación es `(temporada, fase_normalizada, frozenset({ing, esp}))`.
El `frozenset` garantiza que el mismo cruce se agrupa independientemente del
orden en que aparecen los equipos en el archivo (el local varía entre piernas).

**Decisión: normalizar el nombre de la fase para el agrupamiento (`FASE_MAP`).**

`"Playoffs, Matchday 1"` y `"Playoffs, Matchday 2"` son las dos piernas del
mismo cruce; deben colapsar a `"Playoffs"`. El mapa también unifica el formato
viejo (`"Round of 16"`) con el nuevo (`"Finals, Round of 16"`).

**Decisión: acumular goles del partido, no de la tanda de penales.**

El ganador del cruce se determina por goles de campo (90' + prórroga).
Los penales solo se consultan cuando el agregado está igualado.

**Decisión: determinar el ganador de penales desde la perspectiva del partido.**

`pen_t1` y `pen_t2` están en perspectiva del `team1` y `team2` de ESE partido.
Antes de comparar, se reasignan a `pen_ing` / `pen_esp` según `team1_pais`.

---

## Paso 06 — EXPORTAR

**Decisión: generar dos archivos con propósitos distintos.**

- `cruces_ing_esp.csv`: estructura tabular pensada para análisis posterior
  (pandas, Excel, etc.). Incluye todos los campos numéricos.
- `resumen_ing_esp.txt`: legible por humanos, con estadísticas y listado
  alineado en columnas. Los cruces con penales se marcan con `*`.

**Decisión: crear la carpeta `output/` automáticamente si no existe.**

`os.makedirs(carpeta_salida, exist_ok=True)` evita un error si la carpeta
no existe, sin necesidad de verificarla previamente.

---

## Herramientas utilizadas

| Herramienta | Motivo |
|---|---|
| `re` | Parseo de marcadores y códigos de país con patrones simples |
| `csv.DictWriter` | Exportación estructurada sin depender de pandas |
| `os.walk` | Recorrido recursivo de carpetas sin conocer la estructura exacta |
| `collections.defaultdict` | Agrupación de partidos por cruce sin inicializar listas manualmente |
| `frozenset` | Clave de agrupación sin orden garantizado |

No se usa pandas para mantener la dependencia en cero (solo stdlib).

---

## Resultados obtenidos

| | Cruces | % |
|---|---|---|
| **Total** | 31 | — |
| Victorias inglesas | 10 | 32.3% |
| Victorias españolas | 21 | 67.7% |
| Decididos a penales | 1 | Man City vs Real Madrid, Cuartos 2023/24 |
