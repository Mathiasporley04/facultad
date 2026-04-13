# Documentación del Pipeline de Limpieza de Datos

## Introducción: ¿Qué es un pipeline?

Imaginá una fábrica de jugos. Entra fruta sucia y con cáscara por un lado, pasa por varias máquinas (lavado, pelado, exprimido, filtrado, envasado), y sale jugo limpio y listo para tomar por el otro. Eso es exactamente un **pipeline**: una línea de producción donde cada etapa hace una tarea específica y le pasa el resultado a la siguiente.

En este caso:

- **Entra**: un archivo CSV con datos del censo, lleno de errores, formatos raros y texto roto
- **Pasa por**: 6 etapas que limpian, validan y organizan todo
- **Sale**: un CSV limpio listo para analizar + un reporte que explica qué se encontró y qué se arregló

---

## Las 6 etapas del pipeline

---

### Etapa 1 — Cargar (`cargar_datos`)

**¿Qué problema resuelve?**
Los archivos de texto no siempre hablan el mismo "idioma". Hay distintas formas de guardar caracteres como `á`, `ñ` o `ü` en una computadora, y si leés el archivo con el idioma equivocado, ves basura como `Ã©` en lugar de `é`. Esta etapa se encarga de abrir el archivo con el idioma correcto.

**¿Qué hace, paso a paso?**

1. Si tenés instalada la librería `chardet`, la usa para adivinar el idioma del archivo automáticamente
2. Si no, prueba los más comunes uno por uno: `utf-8`, `utf-8-sig`, `latin-1`, `cp1252`
3. Usa el primero que funcione sin errores
4. Muestra en pantalla con cuál funcionó, cuántas filas y columnas tiene, y las primeras 5 filas

**Ejemplo:**

```
Archivo: censo_ficticio.csv
→ Intentando con utf-8... OK
→ Encoding usado: utf-8
→ Shape: (16, 4)
→ Primeras 5 filas: [tabla con los datos]
```

---

### Etapa 2 — Inspeccionar (`inspeccionar_datos`)

**¿Qué problema resuelve?**
Antes de arreglar nada, hay que saber qué está roto. Esta etapa hace un diagnóstico completo: cuenta cuántos registros tienen problemas en cada columna, sin modificar nada todavía.

**¿Qué hace, paso a paso?**

1. Cuenta cuántas celdas están vacías en cada columna
2. Revisa la columna `nombre` buscando: títulos como "Dr." o "Ing.", nombres en MAYÚSCULAS, o texto con caracteres raros como `Ã` o `Â`
3. Revisa la columna `ci` buscando las que no tienen el formato correcto (`X.XXX.XXX-X`)
4. Revisa la columna `email` buscando las que no tienen arroba, no tienen dominio, o tienen espacios
5. Revisa la columna `direccion` buscando las que no tienen un número de 5 dígitos (código postal)
6. Imprime un reporte completo con todos los conteos

**Ejemplo:**

```
nombre — registros con problemas: 6
ci     — registros con formato incorrecto: 5
email  — registros con formato inválido: 3
dir.   — registros sin código postal: 4
```

---

### Etapa 3 — Limpiar (`limpiar_datos`)

**¿Qué problema resuelve?**
Elimina la suciedad más obvia: filas vacías, espacios de más, títulos innecesarios, mayúsculas donde no corresponden, y texto con caracteres rotos por problemas de codificación.

**¿Qué hace, paso a paso?**

1. Elimina filas que están completamente vacías
2. Quita espacios al principio y al final de todos los textos
3. Repara el texto roto en las columnas `nombre` y `direccion` (ej: `PÃ©rez` → `Pérez`)
4. Normaliza todos los nombres: quita el título, pone cada palabra con mayúscula inicial

**Ejemplo:**

```
"DR. JOSÉ PÉREZ"    →   "José Pérez"
"ing. maría núñez"  →   "María Núñez"
"dra. RamÃ³n GÃ³mez" →  "Ramón Gómez"
"Laura Suárez"      →   "Laura Suárez"  (ya estaba bien)
```

---

### Etapa 4 — Validar (`validar_datos`)

**¿Qué problema resuelve?**
Algunos datos no se pueden "arreglar", pero sí se puede saber si son correctos o no. Esta etapa marca los emails inválidos y normaliza las cédulas, sin eliminar nada todavía.

**¿Qué hace, paso a paso?**

1. Revisa cada email con una regla precisa: debe tener exactamente un `@`, algo antes y después, un punto en el dominio, y sin espacios
2. Agrega una columna nueva `email_valido` con `True` o `False`
3. Intenta convertir cada CI al formato correcto (`X.XXX.XXX-X`)
4. Agrega una columna nueva `ci_normalizada` con el resultado (o vacío si no se pudo)

**Ejemplo:**

```
"juan@gmail.com"    →  email_valido = True
"juangmail.com"     →  email_valido = False  (sin @)
"juan@.com"         →  email_valido = False  (sin dominio)
"juan @gmail.com"   →  email_valido = False  (con espacio)
```

---

### Etapa 5 — Transformar (`transformar_datos`)

**¿Qué problema resuelve?**
Extrae información útil que estaba "escondida" dentro de otros campos y reorganiza el DataFrame con los datos ya limpios.

**¿Qué hace, paso a paso?**

1. Busca el código postal (número de exactamente 5 dígitos) dentro de cada dirección
2. Agrega una columna nueva `codigo_postal` con ese valor (o vacío si no había)
3. Reemplaza la columna `ci` con la versión normalizada
4. Elimina la columna auxiliar `ci_normalizada` que ya no se necesita

**Ejemplo:**

```
"Av. 18 de Julio 1234, 11200, Montevideo"  →  codigo_postal = "11200"
"Calle Falsa 123, Salto"                   →  codigo_postal = None
"Calle José Enrique Rodó 456, 50000"       →  codigo_postal = "50000"
```

---

### Etapa 6 — Exportar (`exportar_datos`)

**¿Qué problema resuelve?**
Guarda los resultados en archivos permanentes para que puedan ser usados después. También genera un resumen escrito de todo lo que se encontró y corrigió.

**¿Qué hace, paso a paso?**

1. Guarda el DataFrame limpio en `censo_limpio.csv` con una codificación especial (`utf-8-sig`) que hace que Excel muestre las tildes correctamente
2. Genera un archivo `reporte_calidad.txt` con:
   - Cuántos problemas había antes de limpiar
   - Cuántos quedan después de limpiar
   - Cuántos encodings se repararon, cuántos CP se encontraron, etc.
3. Muestra en pantalla las rutas exactas de los archivos generados

---

## Las funciones del pipeline, explicadas

---

### `reparar_encoding(texto)`

**Para qué existe:** Para arreglar texto que fue guardado en un formato y leído en otro, produciendo caracteres extraños.

**Qué recibe:** Una cadena de texto que puede tener caracteres raros como `Ã©` o `Â`

**Qué devuelve:** El mismo texto pero con los caracteres corregidos, o el texto original si no se pudo reparar

**Por qué:** Cuando un archivo guardado en UTF-8 es abierto como si fuera Latin-1, los acentos se "rompen" de una forma predecible. Esta función deshace ese proceso.

**Ejemplos:**

```
"PÃ©rez"           →  "Pérez"
"GÃ³mez"           →  "Gómez"
"RamÃ³n"           →  "Ramón"
"Laura Suárez"     →  "Laura Suárez"  (no estaba roto, no cambia nada)
```

---

### `normalizar_nombre(nombre)`

**Para qué existe:** Para que todos los nombres queden en el mismo formato limpio y consistente.

**Qué recibe:** Un nombre como puede venir en el CSV: con títulos, en mayúsculas, con texto roto

**Qué devuelve:** El nombre con solo la primera letra de cada palabra en mayúscula, sin títulos, sin caracteres rotos

**Por qué:** Si los nombres no tienen un formato consistente, es imposible buscar, ordenar o comparar personas correctamente.

**Ejemplos:**

```
"DR. JOSÉ PÉREZ"      →  "José Pérez"
"ing. maría núñez"    →  "María Núñez"
"dra. RamÃ³n GÃ³mez"  →  "Ramón Gómez"
"Prof. CARLOS"        →  "Carlos"
```

---

### `normalizar_ci(ci)`

**Para qué existe:** Para que todas las cédulas de identidad tengan el mismo formato, sin importar cómo estaban escritas.

**Qué recibe:** Una CI en cualquier formato: `12345678`, `1.234567-8`, `1.234.567-8`, `AB12345`

**Qué devuelve:** La CI en formato `X.XXX.XXX-X` (8 dígitos) o `XXX.XXX-X` (7 dígitos), o `None` si no es válida

**Por qué:** Sin un formato único es imposible comparar CIs o detectar duplicados.

**Ejemplos:**

```
"12345678"     →  "1.234.567-8"
"4567890"      →  "456.789-0"
"1.234567-8"   →  "1.234.567-8"
"AB12345"      →  None  (tiene letras, no es válida)
"123456"       →  None  (menos de 7 dígitos)
```

---

### `validar_email(email)`

**Para qué existe:** Para saber si un email tiene el formato mínimo necesario para ser real.

**Qué recibe:** Una cadena de texto que puede o no ser un email

**Qué devuelve:** `True` si parece un email válido, `False` si no

**Por qué:** Los emails inválidos no sirven para contactar a nadie, y conviene saber cuáles son antes de usarlos.

**Ejemplos:**

```
"juan@gmail.com"    →  True
"juangmail.com"     →  False  (falta la @)
"juan@.com"         →  False  (falta el dominio entre @ y el punto)
"juan @gmail.com"   →  False  (tiene espacio)
"a@b.uy"            →  True   (mínimo válido)
```

---

### `extraer_codigo_postal(direccion)`

**Para qué existe:** Para sacar el código postal de la dirección y tenerlo en su propia columna.

**Qué recibe:** Una dirección que puede o no tener un CP de 5 dígitos

**Qué devuelve:** El CP como texto (ej: `"11200"`) o `None` si no había ninguno

**Por qué:** El código postal permite saber la zona geográfica, pero mezclado con la dirección es difícil de usar. Solo se considera CP un número de exactamente 5 dígitos (no más, no menos).

**Ejemplos:**

```
"Av. 18 de Julio 1234, 11200, Montevideo"  →  "11200"
"Calle JR 456, 50000"                      →  "50000"
"Calle Falsa 123, Salto"                   →  None
"Rivera 567, 4000, Melo"                   →  None  (4000 tiene solo 4 dígitos)
```

---

## Errores comunes y cómo los maneja el script

**¿Qué pasa si el archivo no existe?**
El script intenta abrirlo y, si no lo encuentra, muestra un mensaje de error claro y se detiene. No genera archivos de salida vacíos.

**¿Qué pasa si el encoding es muy raro?**
Prueba `utf-8`, `utf-8-sig`, `latin-1` y `cp1252` en orden. Si ninguno funciona, lanza un error explicando que no pudo leer el archivo. Si `chardet` está instalado, primero intenta detectarlo automáticamente.

**¿Qué pasa si una CI tiene letras?**
La función `normalizar_ci` detecta que no son solo dígitos y devuelve `None`. La celda queda vacía en el CSV final. El reporte cuenta cuántas quedaron así.

**¿Qué pasa si todos los emails son inválidos?**
El script no se rompe. Agrega la columna `email_valido` con todos los valores en `False` y lo reporta. No elimina ninguna fila por ese motivo.

**¿Qué pasa si el encoding corrupto no se puede reparar?**
La función `reparar_encoding` intenta la corrección dentro de un bloque `try/except`. Si falla, devuelve el texto original sin modificarlo. No tira un error.

---

## Glosario

| Término | Definición |
|---|---|
| **Pipeline** | Línea de procesamiento donde los datos pasan por varias etapas en orden, como una cinta de producción |
| **Encoding** | La forma en que una computadora guarda texto como números. Distintos encodings representan los mismos caracteres de manera diferente |
| **UTF-8** | El encoding más usado hoy en día. Puede representar todos los caracteres del mundo, incluyendo emojis |
| **Latin-1** | Encoding antiguo usado en Europa occidental. Solo soporta 256 caracteres, incluyendo tildes del español |
| **Regex** | "Expresión regular". Una forma de describir un patrón de texto para buscar o validar (ej: "un número de exactamente 5 dígitos") |
| **DataFrame** | Una tabla de datos en Python (como una hoja de cálculo) que maneja la librería `pandas` |
| **CSV** | Archivo de texto donde los datos están separados por comas. Puede abrirse con Excel o cualquier editor de texto |
| **Código postal** | Número de 5 dígitos que identifica una zona geográfica para el correo. En Uruguay van de 11000 a 99999 aproximadamente |
| **Normalizar** | Convertir datos que están en distintos formatos al mismo formato único y estándar |
| **Validar** | Verificar que un dato cumple con ciertas reglas mínimas (ej: que un email tenga @) sin necesariamente corregirlo |
