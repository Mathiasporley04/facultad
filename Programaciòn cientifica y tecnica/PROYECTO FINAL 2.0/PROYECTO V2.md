# Observatorio Financiero LATAM (V2)

> **Proyecto Final — Programación Científica y Técnica · Ciclo Lectivo 2026**
> Documento de especificación técnica y guía de desarrollo asistido con Claude Code.
>
> **Versión 2 (2026-05-19):** ajustes de coherencia interna y con los artefactos complementarios (`pipeline_observatorio V2.md`, `diagramas_uml V2.html`). Cambios principales:
> 1. `Activo.clasificar_volatilidad()` deja de listarse como método polimórfico — se materializa como función pura en `metricas/volatilidad.py` (ADR-004).
> 2. `Activo.obtener_historico()` queda explícitamente como **método concreto con delegación** en la fuente (no abstracto).
> 3. Subclases de `Activo` documentan sus atributos específicos (`market_cap/ranking` en `Cripto`, `sector` en `AccionUSA`, `par/tipo_cotizacion` en `Divisa`).
> 4. `Mercado` documenta `moneda_base`, `refrescar_precios_async()`, `correlaciones()` y `filtrar(predicado)`.
> 5. `Tenencia` incorpora `precio_compra` y métodos `valor_actual(tasas)` + `pnl(tasas)`. `Portfolio` agrega `distribucion()` y `exportar_xml()`.
> 6. ADR-005 reescrito: `AlmacenCifrado` es **clase OOP**, no funciones libres. Las primitivas criptográficas (`cifrar/descifrar/derivar_clave`) son métodos protegidos.
> 7. Orden de procesamiento clarificado en §6: **regex primero, Pydantic después** (la limpieza precede a la validación).
> 8. §7.1 actualizada para cubrir los tres formatos del PDF de cátedra: **JSON (APIs) + CSV + XML (export de portfolio)**.

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Contexto del Proyecto Académico](#2-contexto-del-proyecto-académico)
3. [El Producto: Observatorio Financiero LATAM](#3-el-producto-observatorio-financiero-latam)
4. [Dominio del Problema (para no-financieros)](#4-dominio-del-problema-para-no-financieros)
5. [Alcance del MVP](#5-alcance-del-mvp)
6. [Arquitectura Técnica](#6-arquitectura-técnica)
7. [Cumplimiento de Directrices Académicas (punto por punto)](#7-cumplimiento-de-directrices-académicas-punto-por-punto)
8. [Stack Técnico](#8-stack-técnico)
9. [Estructura del Repositorio](#9-estructura-del-repositorio)
10. [Convenciones de Código (reglas para Claude Code)](#10-convenciones-de-código-reglas-para-claude-code)
11. [Etapas de Desarrollo](#11-etapas-de-desarrollo)
12. [Consideraciones Éticas en Profundidad](#12-consideraciones-éticas-en-profundidad)
13. [Diseño de la Interfaz de Usuario](#13-diseño-de-la-interfaz-de-usuario)
14. [Decisiones Arquitectónicas Clave (ADRs)](#14-decisiones-arquitectónicas-clave-adrs)
15. [Glosario Técnico](#15-glosario-técnico)
16. [Riesgos y Mitigaciones](#16-riesgos-y-mitigaciones)
17. [Plan de Presentación](#17-plan-de-presentación)

---

## 1. Resumen Ejecutivo

Observatorio Financiero LATAM es una aplicación Python que permite visualizar, comparar y analizar simultáneamente tres mercados financieros relevantes para un usuario latinoamericano: el mercado de criptomonedas, la bolsa estadounidense, y las cotizaciones de divisas en Uruguay con foco en el BROU. El producto está diseñado para ser **informativo y educativo, no para asesoramiento financiero**, y prioriza la legibilidad del dato para personas sin formación financiera.

La aplicación opera en dos modos complementarios. El **modo Observatorio** expone una vista pública del estado de los mercados, con énfasis en visualizaciones comparativas que permiten entender la relación entre activos sin necesidad de cargar datos personales. El **modo Mi Portfolio** ofrece, sobre la misma base, la posibilidad de cargar tenencias propias para ver el valor agregado y la distribución del propio capital, con datos persistidos localmente y cifrados.

El proyecto cumple las cinco directrices del programa académico mediante la integración de tres APIs REST consumidas de forma asincrónica, el uso intensivo de programación orientada a objetos con jerarquías polimórficas claras, la aplicación de programación funcional para el cálculo de métricas financieras, el procesamiento de datos crudos con expresiones regulares para normalización, y un tratamiento sustantivo del marco ético y legal que rodea el manejo de información financiera y datos personales en Uruguay.

---

## 2. Contexto del Proyecto Académico

Este proyecto responde a la consigna de **Programación Científica y Técnica 2026**, cuyo enfoque declarado es la integración técnica y la capacidad analítica. Según el documento de cátedra, el verdadero valor del trabajo no reside únicamente en el código entregado sino en el razonamiento técnico, la toma de decisiones documentada y la capacidad de resolver problemas complejos del mundo real con herramientas científicas.

El proyecto debe demostrar dominio simultáneo de varias áreas: ingesta de datos en formatos estándar de la industria, arquitectura de software con paradigma orientado a objetos, consumo de APIs externas con técnicas de optimización asincrónica, programación funcional, y reflexión ética sobre el impacto del software desarrollado. El resultado se evalúa de forma continua a lo largo del proceso —no solo al final— y se complementa con un portafolio digital de aprendizaje y un ejercicio de peer review entre pares.

Este documento es el **artefacto central de coordinación** del proyecto: sirve como contrato con uno mismo respecto al alcance, como brief para el desarrollo asistido por Claude Code, y como insumo base para el portafolio digital que se entrega junto al código.

---

## 3. El Producto: Observatorio Financiero LATAM

### Propuesta de valor

El usuario latinoamericano —y en particular el uruguayo— vive cotidianamente expuesto a múltiples mercados que afectan su economía: la cotización del dólar BROU es referencia para ahorristas, las criptomonedas son una alternativa cada vez más consultada para preservar valor, y la bolsa estadounidense es el termómetro global de los mercados. Sin embargo, la mayoría de las herramientas existentes son o demasiado básicas (apps de "el dólar hoy") o demasiado profesionales (terminales tipo Bloomberg).

Observatorio Financiero LATAM se ubica deliberadamente en el medio: pretende dar una **visión panorámica** de los mercados relevantes para un latinoamericano, con un nivel de profundidad analítica suficiente para extraer insights útiles, pero con una capa de presentación pensada para personas que no son financistas. El énfasis está en la comprensión, no en la operación.

### Usuarios objetivo

El producto está pensado para tres perfiles. El primer perfil es la persona curiosa sobre finanzas que quiere entender cómo se mueven los mercados sin tener que aprender la jerga técnica de antemano. El segundo perfil es el ahorrista latinoamericano que ya tiene algunas posiciones (un poco de cripto, dólares en el banco, alguna acción) y quiere ver todo en un solo lugar con una métrica común. El tercer perfil es el estudiante de finanzas o economía que quiere una herramienta liviana para hacer análisis exploratorio sobre datos de mercado reales sin pagar suscripciones.

### No es

Es importante delimitar lo que el producto explícitamente **no es**, tanto por claridad de alcance como por consideraciones legales. No es una plataforma de trading: no permite comprar ni vender activos. No es un asesor financiero: no recomienda comprar, vender ni mantener ningún activo. No es una fuente oficial de cotizaciones: replica datos públicos pero no es responsable de su exactitud. No es una herramienta de uso institucional: está diseñado para uso personal y educativo.

---

## 4. Dominio del Problema (para no-financieros)

Esta sección documenta el conocimiento financiero mínimo necesario para entender el producto. El propósito es doble: por un lado sirve como referencia para el desarrollo, y por otro lado el contenido aquí descrito **debe estar embebido en la propia interfaz** mediante tooltips, glosario y lenguaje accesible. La presentación debe poder ser entendida por una persona sin formación financiera previa.

### Qué es un mercado financiero

Un mercado financiero es un lugar —hoy mayormente virtual— donde se compran y venden activos financieros. Cuando alguien dice "subió la bolsa", se refiere a que el promedio de precios de los activos que cotizan en ese mercado subió respecto al día anterior. Los mercados tradicionales tienen horarios de apertura y cierre, mientras que el mercado de criptomonedas opera las veinticuatro horas todos los días del año.

### Qué es un activo

Un activo financiero es cualquier cosa que tiene valor económico y se puede comprar o vender. Las cuatro categorías que cubre este proyecto son:

Una **acción** representa una porción muy pequeña de la propiedad de una empresa. Quien tiene una acción de Apple es, técnicamente, dueño de una fracción minúscula de la empresa Apple. Las acciones suben de precio cuando hay más gente queriendo comprarlas que venderlas, lo que suele pasar cuando la empresa tiene buenos resultados.

Una **criptomoneda** es una moneda digital que no está respaldada por ningún gobierno. Su valor depende exclusivamente de la oferta y demanda en el mercado. Bitcoin es la más conocida y funciona como una especie de "oro digital": tiene una cantidad máxima limitada y mucha gente la usa como reserva de valor.

Una **divisa** es la moneda de un país. Cuando hablamos de "el dólar", en realidad hablamos del tipo de cambio entre el peso uruguayo y el dólar estadounidense. Una cotización del dólar BROU de 40 UYU significa que para comprar un dólar hay que entregar cuarenta pesos uruguayos.

Un **índice bursátil** no es exactamente un activo, sino un promedio del comportamiento de un grupo de activos. El **S&P 500** mide el comportamiento promedio de las quinientas empresas más grandes que cotizan en bolsa en Estados Unidos. Los índices se usan como termómetros del estado general de un mercado.

### Los tres mercados que cubre el proyecto

**Mercado de criptomonedas**. Es global, descentralizado y opera 24/7. Los principales activos son Bitcoin (BTC), Ethereum (ETH) y un puñado de monedas estables ancladas al dólar como USDT y USDC. Es el mercado más volátil de los tres: caídas o subas del 10% en un día son frecuentes.

**Bolsa estadounidense**. Es el mercado bursátil más grande del mundo. Las dos bolsas principales son el NYSE (New York Stock Exchange) y el NASDAQ. Las empresas que cotizan ahí son las más grandes y conocidas globalmente: Apple, Microsoft, Google (Alphabet), Amazon, Tesla. El horario de operación es de lunes a viernes, aproximadamente de 10:30 a 17:00 hora de Uruguay.

**Mercado cambiario uruguayo (BROU)**. El BROU (Banco República) es el banco estatal uruguayo y su cotización del dólar es referencia para gran parte de la economía. La cotización tiene dos puntas: el precio al que el banco compra dólares (más bajo) y el precio al que los vende (más alto). La diferencia entre ambos se llama "spread" y es el margen del banco.

### Métricas financieras que vamos a calcular y mostrar

**Rendimiento porcentual**. Es el cambio relativo del precio en un período. Si una acción pasó de 100 a 110, su rendimiento es +10%. En la UI lo presentamos siempre como porcentaje, con color verde si es positivo y rojo si es negativo, evitando jerga.

**Volatilidad**. Mide qué tan inestable es el precio de un activo. Técnicamente se calcula como la desviación estándar de los rendimientos diarios, anualizada. En lenguaje simple: un activo de baja volatilidad tiene precios estables, uno de alta volatilidad sube y baja mucho. La presentamos en la UI como una etiqueta cualitativa ("Estable", "Moderada", "Alta", "Muy alta") complementada con el número técnico para usuarios avanzados.

**Correlación**. Mide si dos activos se mueven juntos. Va de -1 a +1. Una correlación cercana a +1 significa que cuando uno sube el otro también sube. Cercana a -1 significa que cuando uno sube el otro baja. Cercana a 0 significa que no hay relación. La presentamos visualmente con un heatmap de colores, no con números crudos.

**Drawdown máximo**. Es la peor caída desde un máximo histórico hasta el siguiente mínimo. Mide cuánto puede llegar a perder un inversor en el peor momento. La presentamos como "la peor caída registrada en el período" para evitar la palabra técnica.

### Por qué importa el contexto LATAM

A diferencia de un usuario en un país desarrollado, el latinoamericano vive con tres fuentes simultáneas de incertidumbre: la inflación local, el riesgo de devaluación, y la inestabilidad política y económica regional. Esto hace que el "rendimiento nominal" de cualquier inversión sea engañoso si no se contextualiza. Una acción que sube 80% en moneda local en un año donde la inflación fue del 100% en realidad perdió valor real. Por eso la herramienta debe permitir siempre **dos lecturas**: el rendimiento nominal en moneda local y el rendimiento ajustado o convertido a dólares como referencia más estable.

---

## 5. Alcance del MVP

### Lo que sí incluye el MVP

El MVP cubre las tres fuentes de datos definidas: criptomonedas vía CoinGecko, acciones estadounidenses vía Yahoo Finance, y cotizaciones de divisas uruguayas vía DolarApi.com (u otra API similar para cotizaciones del BROU). Cada fuente alimenta un conjunto acotado de activos para evitar que el alcance se vaya de tiempo: las diez criptomonedas principales por capitalización de mercado, los componentes del S&P 500 más una lista de tickers populares, y las cuatro divisas principales (USD, EUR, BRL, ARS).

La aplicación expone tres pantallas principales en su interfaz de Streamlit. La pantalla "Panorama" da una vista general del estado de los tres mercados. La pantalla "Comparar" permite seleccionar activos arbitrarios y compararlos en términos de rendimiento, volatilidad y correlaciones. La pantalla "Mi Portfolio" permite cargar tenencias propias y ver el valor agregado, la distribución y el desempeño del portfolio personal.

El sistema implementa todas las directrices técnicas exigidas por el programa: arquitectura orientada a objetos con clases abstractas y herencia, consumo de APIs REST con técnicas asincrónicas, procesamiento funcional para cálculo de métricas, normalización de datos con expresiones regulares, y persistencia local cifrada para los datos del modo portfolio.

### Lo que no incluye el MVP

No incluye sistema de cuentas de usuario ni autenticación: cada instalación es una sola "sesión" con su propio portfolio. No incluye operación real con dinero ni integración con brokers. No incluye notificaciones, alertas ni envío de emails. No incluye análisis predictivo ni machine learning: solo análisis descriptivo y exploratorio. No incluye datos de empresas más allá del precio (sin estados contables, sin ratios fundamentales, sin noticias). El alcance en USA se cubre con acciones directas. No incluye derivados, opciones ni futuros.

### Restricciones explícitas de tiempo y complejidad

El proyecto debe ser presentable en un tiempo acotado y debe ser entendible por una audiencia que incluye personas sin formación financiera. Esto impone dos restricciones de diseño que aplican transversalmente: cualquier feature que requiera más de tres días de desarrollo se evalúa contra el costo de oportunidad del resto, y cualquier feature que requiera explicación técnica para entenderse en una demo de cinco minutos queda fuera del MVP.

---

## 6. Arquitectura Técnica

### Visión general

La arquitectura sigue un patrón clásico de tres capas, adaptado al dominio del proyecto. La **capa de fuentes de datos** abstrae las tres APIs externas detrás de una interfaz uniforme. La **capa de dominio** modela los activos financieros, los mercados y las operaciones puras de cálculo de métricas. La **capa de presentación** consume el dominio y lo expone vía Streamlit con visualizaciones de Plotly.

El flujo principal de datos parte de las APIs externas (asincrónicas), pasa por una capa de normalización con regex y validación con Pydantic, alimenta los modelos de dominio que viven en memoria, y termina en la capa de presentación que consume tanto el estado actual como las funciones puras de métricas para generar las visualizaciones. Existe también un flujo secundario para el modo portfolio, donde los datos del usuario se persisten cifrados en disco y se hidratan al inicio de cada sesión.

### Jerarquía de clases (paradigma OOP)

La jerarquía de clases es el corazón del cumplimiento de la directriz académica de OOP avanzada. Hay dos jerarquías principales: la de fuentes de datos y la de activos.

La jerarquía de **fuentes de datos** se encabeza por una clase abstracta `FuenteDatos` que define el contrato común: métodos asincrónicos para obtener el precio actual de un símbolo, obtener su histórico de precios, y listar los activos disponibles en esa fuente. Las tres implementaciones concretas son `CoinGeckoAPI`, `YahooFinanceAPI` y `DolarApiUY`. Cada una resuelve internamente las particularidades de su API (paginación, rate limits, autenticación si aplica, formato de respuesta) pero expone hacia afuera la interfaz uniforme.

La jerarquía de **activos** se encabeza por una clase abstracta `Activo` que define las propiedades comunes (`simbolo`, `nombre`, `moneda_nativa`, `tipo: TipoMercado`) y mantiene una referencia a la `FuenteDatos` correspondiente por **composición** (atributo `fuente: FuenteDatos` recibido en el constructor). El método **polimórfico** central es `precio_actual_usd(tasas: dict[str, float] | None) -> float`, que cada subclase implementa a su manera. El método `obtener_historico(desde, hasta)` se implementa **una sola vez en la clase base** y delega en la fuente (`self.fuente.historico(self.simbolo, desde, hasta)`): las subclases no lo reimplementan. La clasificación cualitativa de volatilidad ("Estable", "Moderada", "Alta", "Muy alta") **no** es método de `Activo`; vive como función pura en `metricas/volatilidad.py` (ver ADR-004).

Las tres implementaciones concretas son `Cripto`, `AccionUSA` y `Divisa`, cada una con atributos específicos que justifican la herencia más allá del polimorfismo del método:

- `Cripto` agrega `market_cap: float` y `ranking: int`. Su `precio_actual_usd()` es pass-through: la fuente ya devuelve USD.
- `AccionUSA` agrega `sector: str`. Su `precio_actual_usd()` también es pass-through (yfinance devuelve USD).
- `Divisa` agrega `par: str` y `tipo_cotizacion: str` ("BROU", "BCU", etc). Su `precio_actual_usd()` invierte la cotización local cuando aplica (`1.0 / cotizacion`).

Una clase `Mercado` agrupa una colección de activos del mismo origen y expone operaciones de conjunto. Sus atributos son `nombre: str`, `tipo: TipoMercado`, `activos: list[Activo]` y `moneda_base: str`. Sus métodos públicos son:

- `refrescar_precios_async() -> None`: consulta el `RegistroFuentes` y dispara `asyncio.gather` para refrescar en paralelo los precios actuales de todos los activos del mercado.
- `correlaciones() -> np.ndarray`: calcula la matriz de correlaciones entre todos los activos del mercado.
- `filtrar(predicado: Callable[[Activo], bool]) -> list[Activo]`: devuelve los activos que cumplen un criterio arbitrario (usa `filter` nativo). Es uno de los lugares donde se materializa el uso genuino de programación funcional.

Una clase `Portfolio` representa la agregación de tenencias de un usuario. Sus atributos son `nombre: str`, `tenencias: list[Tenencia]` y `moneda_base: str`. Sus métodos públicos incluyen `agregar_tenencia(t)`, `valor_total(tasas) -> float` (implementado con `functools.reduce` sobre las tenencias), `distribucion() -> dict[str, float]` (porcentaje por activo), `exportar_csv() -> str` y `exportar_xml() -> str` (cubren los formatos CSV y XML exigidos por la directriz 7.1). La persistencia cifrada se delega en la clase `AlmacenCifrado` (ver ADR-005).

Una clase `Tenencia` modela una posición individual del portfolio: `activo: Activo` (**asociación**, no composición — el mismo activo puede aparecer en muchas tenencias y existe independientemente), `cantidad: float` y `precio_compra: float`. Métodos: `valor_actual(tasas) -> float` (cantidad × precio actual convertido) y `pnl(tasas) -> float` (valor actual − valor de compra), útil para mostrar ganancia/pérdida por posición sin sobre-prometer.

### Flujo asincrónico

La capa asincrónica está construida sobre `aiohttp` y `asyncio`. Cada `FuenteDatos` mantiene una sesión `aiohttp` reutilizable. La operación de "refrescar todos los activos del observatorio" se implementa como un `asyncio.gather` sobre las tres fuentes en paralelo, cada una resolviendo internamente sus propias llamadas también en paralelo cuando aplica. El speedup esperado respecto a una versión secuencial es de aproximadamente 3x para el escenario base, métrica que debe medirse y documentarse en el informe final.

Existe una capa de caché en memoria con TTL de sesenta segundos para precios actuales, configurable por fuente. Los datos históricos se cachean en disco como archivos parquet con TTL de un día, dado que su volumen es mucho mayor y su tasa de cambio es menor. Toda la lógica de caché está aislada en un decorador genérico que envuelve los métodos asincrónicos de las fuentes, lo que mantiene el código de las fuentes limpio.

### Capa funcional para métricas

Las métricas financieras están implementadas como **funciones puras** en el módulo `metricas`. Una función pura no muta su entrada, no depende de estado externo, y siempre devuelve el mismo resultado para los mismos argumentos. Esta restricción simplifica enormemente el testing y permite usar `map`, `filter` y `functools.reduce` con confianza sobre estas funciones.

El módulo expone funciones como `calcular_volatilidad(precios: list[float]) -> float`, `calcular_correlacion(serie_a: list[float], serie_b: list[float]) -> float`, `calcular_drawdown_maximo(precios: list[float]) -> float`, `calcular_rendimiento_porcentual(precio_inicial: float, precio_final: float) -> float`, `normalizar_a_base(precios: list[float], base: float = 100.0) -> list[float]`, y `convertir_moneda(monto: float, moneda_origen: str, moneda_destino: str, tasas: dict[str, float]) -> float`. Ninguna de estas funciones tiene side effects ni depende de la red.

La aplicación de programación funcional se complementa con el uso de `map`, `filter` y `functools.reduce` en los pipelines de procesamiento. Por ejemplo, calcular el valor total del portfolio se expresa como un `reduce` sobre la lista de tenencias, y filtrar activos por umbral de volatilidad se expresa como un `filter` con una función parcial. Es importante que el uso de funcional sea **genuino y útil**, no decorativo.

### Normalización con regex

Las expresiones regulares se usan en cuatro lugares concretos. El primero es la **normalización de tickers**: las distintas APIs devuelven el mismo activo con formatos distintos (BTC, BTC-USD, BTCUSDT) y un módulo `normalizadores` aplica reglas regex para llevar todo a una forma canónica. El segundo es la **normalización de fechas**: las APIs devuelven fechas en formatos heterogéneos (ISO 8601, timestamps Unix, formatos custom) y un parser robusto las convierte a `datetime` con timezone aware. El tercero es la **validación de inputs del usuario** en la UI: cuando el usuario escribe un ticker en el modo portfolio, regex valida que tenga forma de ticker válido antes de consultar las APIs. El cuarto es la **limpieza de campos textuales** que vienen sucios en las respuestas de algunas APIs (espacios extra, comillas inconsistentes, codificación rara).

### Orden de procesamiento: regex primero, Pydantic después

El pipeline de ingesta tiene un **orden estricto**: `API → asyncio.gather → caché → regex (normalizadores) → Pydantic (esquemas) → dominio`. La razón es práctica: regex normaliza el dato sucio (espacios, casing inconsistente, formatos heterogéneos de fecha) y Pydantic valida invariantes sobre el dato **ya limpio**. Si se invirtiera el orden, Pydantic rechazaría datos válidos por puro ruido sintáctico. Esta secuencia está reflejada en los flowcharts de `pipeline_observatorio V2.md`.

### Validación con Pydantic

Sobre la base de la limpieza con regex, una capa de validación con Pydantic asegura que los datos que entran al dominio cumplen las invariantes esperadas (precios estrictamente positivos, fechas dentro de rango razonable, símbolos no vacíos, monedas de 3 caracteres). Cualquier dato que falle la validación se rechaza con un error explícito antes de contaminar el resto del sistema. Los modelos viven en `fuentes/esquemas.py` como `CotizacionDTO`, `PuntoPrecioDTO` e `HistoricoDTO`.

---

## 7. Cumplimiento de Directrices Académicas (punto por punto)

Esta sección mapea de forma explícita cada directriz del documento de cátedra contra los componentes concretos del proyecto donde se cumple. Es un mapa de evidencias para la evaluación.

### 7.1 Recolección y Procesamiento de Datos

La directriz exige integración de datos en formatos estándar de la industria (CSV, JSON, XML), uso de regex para normalización, y garantía de calidad de los datos. **V2: el proyecto cubre los tres formatos** (cambio frente a V1, que solo cubría JSON + CSV).

**Formatos integrados.** El proyecto cubre los **tres formatos** exigidos por el documento de cátedra:

- **JSON** — formato principal de las tres APIs REST consumidas (CoinGecko, Yahoo Finance, DolarApi UY). El JSON cifrado también es el wire format de `AlmacenCifrado` para persistir el portfolio en disco.
- **CSV** — el modo Portfolio expone import/export de tenencias vía `Portfolio.exportar_csv()` e `importar_csv()`. El usuario que lleva su registro en una planilla puede importar sin re-tipear, y exportar el estado actual para llevarlo a Excel.
- **XML** — el modo Portfolio también ofrece import/export en XML vía `Portfolio.exportar_xml()` e `importar_xml()`, útil para integraciones con sistemas que consumen XML (contabilidad personal, planillas con macros, intercambio con asesores). La implementación usa `xml.etree.ElementTree` de la stdlib y produce un documento con `<portfolio>` raíz y un `<tenencia>` por posición (símbolo, cantidad, precio de compra).

Las tres rutas son **funcionales y no decorativas**: JSON viaja en el wire format de las 3 APIs, CSV/XML son rutas reales de import/export para el usuario final.

**Regex.** Su uso está documentado en la sección 6 (Normalización con regex). Los cuatro escenarios de uso son tickers, fechas, validación de input y limpieza de campos.

**Calidad de datos.** El sistema implementa cuatro mecanismos de calidad. Validación con Pydantic en la frontera entre las APIs externas y el dominio. Caché con TTL para evitar resultados inconsistentes en una misma sesión. Manejo de errores con fallbacks: si una fuente falla, se muestra el último dato cacheado con un timestamp visible. Tests unitarios sobre las funciones puras de métricas con casos límite (listas vacías, valores idénticos, valores extremos).

### 7.2 Organización y Diseño Modular

La directriz exige uso mandatorio de OOP, herencia y polimorfismo, y abstracción.

**OOP como paradigma estructural.** El núcleo del proyecto está construido alrededor de las dos jerarquías de clases descritas en la sección 6: fuentes de datos y activos. La capa funcional convive con la OOP pero no la reemplaza: las clases modelan entidades del dominio, las funciones puras modelan operaciones matemáticas sobre datos.

**Herencia.** Dos clases abstractas (`FuenteDatos`, `Activo`) actúan como contratos. Tres implementaciones concretas heredan de cada una. La herencia es genuina y no decorativa: las subclases comparten estructura común heredada y solo overridean lo específico de su mercado.

**Polimorfismo.** El polimorfismo se manifiesta en el método `precio_actual_usd()`. La capa `Mercado` itera sobre `list[Activo]` sin saber qué tipo concreto es cada elemento, y cada uno resuelve la conversión a USD según su lógica específica. Lo mismo ocurre con `obtener_historico()` y `clasificar_volatilidad()`.

**Abstracción.** Las clases abstractas son ABCs (`abc.ABC`) con métodos marcados como `@abstractmethod`, garantizando a nivel de Python que las subclases implementen el contrato. Las dependencias entre módulos se resuelven contra las abstracciones, no contra las implementaciones concretas, lo que permite agregar nuevos mercados o nuevas fuentes sin tocar el resto del sistema.

### 7.3 Rendimiento y APIs Externas

La directriz exige consumo de APIs REST, programación asincrónica y programación funcional.

**APIs REST.** El sistema consume tres APIs externas, todas REST, todas devolviendo JSON. La elección de fuentes está justificada en la sección 8 (Stack Técnico).

**Programación asincrónica.** La capa de fuentes está implementada con `aiohttp` y `asyncio`. La operación principal del observatorio (refrescar todos los activos) se ejecuta en paralelo con `asyncio.gather`. El proyecto incluye un benchmark explícito sync vs async como evidencia de la mejora de rendimiento, con números reportados en el informe final.

**Programación funcional.** Las métricas financieras son funciones puras. El procesamiento de datos en las pipelines internas usa `map`, `filter`, `functools.reduce` y comprehensions de manera consistente. El uso de funciones de orden superior (funciones que toman otras funciones como argumento) está presente en la capa de transformación de series temporales.

### 7.4 Ética y Responsabilidad Social

La directriz exige cumplimiento de legislación, ética profesional y responsabilidad. Esta directriz tiene tratamiento extenso en la sección 12.

**Legislación.** El proyecto opera dentro del marco legal uruguayo (Ley 18.331 de Protección de Datos Personales). Esta normativa se documenta explícitamente en `docs/etica.md` con análisis de qué partes del producto caen bajo qué regulación. El producto declara explícitamente que **no constituye asesoramiento financiero** y por tanto no cae bajo regulación del BCU/RNMV en Uruguay.

**Ética profesional.** El producto incorpora disclaimers visibles en todas las pantallas, comunicación honesta de incertidumbre (timestamps de cuándo se refrescaron los datos, marcadores cuando una fuente falla), evita lenguaje promocional o inductivo a la inversión, y muestra siempre métricas de riesgo junto a métricas de rendimiento.

**Responsabilidad.** Los datos del modo portfolio se cifran en reposo con Fernet. No hay telemetría: el sistema no envía información a ningún servidor externo más allá de las llamadas estrictamente necesarias a las tres APIs públicas. No hay cuentas de usuario ni almacenamiento centralizado. La privacidad se garantiza por diseño: la información que el usuario carga no sale de su máquina.

### 7.5 El Proceso como Producto

La directriz exige evaluación continua del razonamiento, portafolio digital de aprendizaje, y peer review.

**Razonamiento documentado.** Este documento (PROYECTO.md) es el primer artefacto. Las decisiones arquitectónicas se documentan como ADRs cortos en la sección 14, y las decisiones más profundas se documentan en archivos separados en `docs/adr/`.

**Portafolio digital.** El repositorio incluye una carpeta `docs/portafolio/` con la bitácora de aprendizaje: una entrada por cada hito del proyecto que registra qué se hizo, qué desafíos surgieron, cómo se resolvieron, y qué se aprendió. El portafolio es **narrativo, no técnico**: está pensado como insumo para la evaluación, no como documentación del código.

**Peer review.** El repositorio se estructura para facilitar la revisión por pares. El README incluye instrucciones de instalación reproducibles. Los commits siguen Conventional Commits para que el historial sea legible. Los PRs entre etapas tienen descripciones que explican el qué y el porqué de los cambios.

---

## 8. Stack Técnico

### Lenguaje y entorno

**Python 3.11+**. La versión mínima es 3.11 por dos motivos: mejor performance de asyncio, y soporte nativo de los grupos de tareas (`asyncio.TaskGroup`) que simplifican el código asincrónico. Se usa `pyproject.toml` para definir dependencias y configuración de herramientas.

### Dependencias principales

`aiohttp` para las llamadas asincrónicas a las APIs REST. Es el estándar de facto en Python async y tiene mejor performance que alternativas síncronas envueltas en threads.

`pandas` para manipulación de series temporales. Su uso es acotado: solo donde realmente aporta (manejo de fechas, resampling, series con índice temporal). No reemplaza al modelo de dominio.

`numpy` para los cálculos numéricos de las métricas. La volatilidad, correlación y drawdown se calculan vectorizadamente.

`pydantic` (v2) para validación de los datos que cruzan la frontera entre APIs externas y dominio interno. Cada respuesta de API se mapea a un modelo Pydantic antes de tocar el resto del sistema.

`streamlit` para la interfaz de usuario. La elección está justificada en el ADR-001.

`plotly` para las visualizaciones interactivas. Reemplaza a `matplotlib` en todo el proyecto. Las razones están en el ADR-002.

`cryptography` (paquete `cryptography`) para el cifrado del portfolio personal con Fernet (AES-128 en modo CBC con HMAC-SHA256).

`python-dateutil` para parsing robusto de fechas en formatos heterogéneos.

`yfinance` como cliente conveniente para Yahoo Finance, con fallback documentado a Twelve Data si la librería rompe.

### Dependencias de desarrollo

`pytest` y `pytest-asyncio` para la suite de tests. `ruff` para linting y formateo. `mypy` para type checking estático.

### Servicios externos

**CoinGecko API** (free tier, sin API key). Endpoint base: `https://api.coingecko.com/api/v3/`. Rate limit: 30 requests por minuto en free tier. Devuelve precios en múltiples monedas, históricos hasta varios años, market cap, volumen.

**Yahoo Finance** vía `yfinance`. Sin API key. Cubre acciones de USA, ETFs, e índices. Devuelve precios actuales y series históricas. Riesgo: la librería depende de scraping y puede romperse; se mantiene Twelve Data como fallback documentado.

**DolarApi (Uruguay)**. API que centraliza cotizaciones de divisas en Uruguay incluyendo BROU, BCU y otros. Endpoint base por confirmar al inicio de la Etapa 2; alternativa: scraping ligero de la página oficial del BROU si la API no es suficiente.

---

## 9. Estructura del Repositorio

```
observatorio-financiero/
├── pyproject.toml              # Dependencias, configuración de herramientas
├── README.md                   # Intro pública del proyecto, instalación, uso
├── PROYECTO.md                 # Este documento
├── .gitignore
├── .streamlit/
│   └── config.toml             # Tema custom, configuración de Streamlit
├── src/
│   └── observatorio/
│       ├── __init__.py
│       ├── core/                       # Modelos abstractos del dominio
│       │   ├── __init__.py
│       │   ├── activo.py               # ABC Activo
│       │   ├── fuente.py               # ABC FuenteDatos
│       │   ├── mercado.py              # Clase Mercado (composición)
│       │   ├── portfolio.py            # Clase Portfolio
│       │   └── tipos.py                # Tipos compartidos, enums, dataclasses
│       ├── activos/                    # Implementaciones concretas de Activo
│       │   ├── __init__.py
│       │   ├── cripto.py
│       │   ├── accion_usa.py
│       │   └── divisa.py
│       ├── fuentes/                    # Implementaciones concretas de FuenteDatos
│       │   ├── __init__.py
│       │   ├── coingecko.py
│       │   ├── yahoo_finance.py
│       │   ├── dolar_api_uy.py
│       │   ├── cache.py                # Decorador de caché reutilizable
│       │   └── registro.py             # Registro central de fuentes disponibles
│       ├── metricas/                   # Funciones puras
│       │   ├── __init__.py
│       │   ├── rendimiento.py
│       │   ├── volatilidad.py
│       │   ├── correlacion.py
│       │   ├── drawdown.py
│       │   ├── normalizacion.py
│       │   └── conversion.py
│       ├── normalizadores/             # Regex y limpieza de datos
│       │   ├── __init__.py
│       │   ├── tickers.py
│       │   ├── fechas.py
│       │   └── validadores.py
│       ├── persistencia/               # Cifrado y storage del portfolio
│       │   ├── __init__.py
│       │   ├── cifrado.py              # Wrapper sobre Fernet
│       │   └── almacen.py              # CRUD del portfolio cifrado
│       ├── ui/                         # Streamlit
│       │   ├── __init__.py
│       │   ├── app.py                  # Entrypoint de Streamlit
│       │   ├── vistas/
│       │   │   ├── __init__.py
│       │   │   ├── panorama.py
│       │   │   ├── comparar.py
│       │   │   └── portfolio.py
│       │   ├── componentes/
│       │   │   ├── __init__.py
│       │   │   ├── metric_card.py
│       │   │   ├── grafico_lineas.py
│       │   │   ├── heatmap.py
│       │   │   ├── treemap.py
│       │   │   └── disclaimer.py
│       │   └── glosario.py             # Tooltips y definiciones
│       └── utils/
│           ├── __init__.py
│           ├── logging_config.py
│           └── benchmark.py            # Sync vs async benchmark
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_metricas/                  # Tests de funciones puras
│   ├── test_normalizadores/            # Tests de regex
│   ├── test_fuentes/                   # Tests de fuentes (con mocks)
│   ├── test_activos/                   # Tests de jerarquía de activos
│   ├── test_persistencia/              # Tests de cifrado
│   └── test_integracion/               # Tests end-to-end con APIs reales (skip en CI)
├── data/
│   ├── cache/                          # Cache de precios (gitignored)
│   └── portfolio/                      # Datos cifrados del portfolio (gitignored)
├── docs/
│   ├── etica.md                        # Análisis ético y legal extendido
│   ├── glosario.md                     # Glosario financiero completo
│   ├── decisiones.md                   # Bitácora de decisiones técnicas
│   ├── adr/                            # Architecture Decision Records detallados
│   │   ├── 001-streamlit-vs-fastapi.md
│   │   ├── 002-plotly-vs-matplotlib.md
│   │   └── ...
│   ├── benchmark.md                    # Reporte del benchmark sync vs async
│   ├── portafolio/                     # Bitácora de aprendizaje (entrega académica)
│   │   ├── etapa-1.md
│   │   ├── etapa-2.md
│   │   └── ...
│   └── peer-review/                    # Estructura para el review de pares
│       └── checklist.md
└── scripts/
    ├── benchmark_async.py              # Script standalone del benchmark
    └── seed_demo.py                    # Carga datos de demo para presentación
```

---

## 10. Convenciones de Código (reglas para Claude Code)

Esta sección define las reglas que Claude Code debe respetar al generar o modificar código. Son reglas operativas, no sugerencias.

### Idioma

Los nombres de funciones, clases, variables y archivos del **dominio financiero** se escriben en **español**: `Activo`, `Mercado`, `calcular_volatilidad`, `obtener_precio`, `precio_actual_usd`. Los nombres de keywords técnicas de Python (`def`, `class`, `async`, `await`) son en inglés por obligación del lenguaje. Los comentarios y docstrings se escriben en **español**. Los mensajes de log y los strings visibles al usuario se escriben en **español rioplatense**, evitando localismos extremos.

### Type hints obligatorios

Toda función pública (no prefijada con guion bajo) tiene **type hints completos** en argumentos y retorno. Las funciones privadas también, salvo casos triviales. Los tipos compuestos usan sintaxis moderna de Python 3.11+ (`list[int]` en lugar de `List[int]`, `int | None` en lugar de `Optional[int]`).

### Async explícito

Toda función que hace I/O de red es `async`. No hay versiones síncronas paralelas: si algo necesita I/O, se usa `await`. El único lugar donde se llama código async desde código sync es la capa de Streamlit, que usa `asyncio.run()` en los puntos de entrada de las vistas.

### Docstrings

Todas las clases y funciones públicas tienen docstring estilo Google. Las funciones puras de métricas documentan en el docstring qué calculan, en qué unidades, qué supuestos hacen sobre los inputs (por ejemplo, "asume precios diarios consecutivos sin huecos"), y qué hacen con casos límite (lista vacía, único elemento, todos iguales).

### Tests

Toda función pura del módulo `metricas/` tiene tests unitarios que cubren al menos: caso típico, caso vacío, caso con un solo elemento, caso con valores extremos (todos iguales, ceros, negativos donde aplique). Los normalizadores con regex tienen tests con casos válidos, casos inválidos, y casos límite. Las fuentes de datos tienen tests con respuestas mockeadas de las APIs (no se testean contra APIs reales en CI).

### Manejo de errores

Las excepciones del dominio se definen en `core/excepciones.py` y heredan de una `ObservatorioError` base. Las fuentes de datos lanzan `FuenteIndisponible` cuando una API falla, y la capa de presentación maneja esa excepción mostrando el último dato cacheado con un indicador visual. **No se hace `except Exception`** salvo en el punto más externo de la app.

### Logging

Se usa `logging` estándar de Python configurado en `utils/logging_config.py`. Las fuentes loggean en nivel INFO los hits y misses de caché, en nivel WARNING las degradaciones (fallback a caché), y en nivel ERROR los fallos no recuperables. **No se usa `print()`** para nada que no sea scripts standalone.

### Constantes vs configuración

Las constantes del dominio (lista de criptomonedas trackeadas, tickers del S&P 500, divisas soportadas) viven en `core/configuracion.py` como constantes módulo. Los valores que pueden cambiar en runtime (TTL de caché, timeouts) se leen de variables de entorno con defaults sensatos, vía un módulo `utils/configuracion.py`.

### Reglas explícitas para Claude Code

Al agregar un nuevo activo, heredar de `Activo` en `activos/`, registrarlo en el `Mercado` correspondiente, y agregarlo a la lista de constantes en `core/configuracion.py`. No tocar otros archivos.

Al agregar una nueva fuente de datos, heredar de `FuenteDatos` en `fuentes/`, registrarla en `RegistroFuentes`, y proveer al menos los tres métodos abstractos. La nueva fuente debe ser autosuficiente (no depende de otras fuentes para funcionar).

Al agregar una nueva métrica, escribirla como **función pura** en `metricas/`, sin side effects, sin acceso a estado global, sin llamadas async. Agregar tests unitarios en `tests/test_metricas/`.

No introducir dependencias nuevas sin justificación documentada en `docs/decisiones.md`. Cada dependencia agrega superficie de mantenimiento.

No usar `matplotlib`. Todas las visualizaciones son con Plotly.

No mezclar lógica de presentación con lógica de dominio. La capa `ui/` consume el dominio y las métricas, no las modifica ni las extiende.

No introducir tracking, telemetría, ni envío de datos a servicios externos más allá de las tres APIs documentadas. Esto es un compromiso ético del proyecto, no una decisión técnica.

---

## 11. Etapas de Desarrollo

El desarrollo se organiza en siete etapas. Cada etapa cierra con un hito demostrable y una entrada en el portafolio digital.

**Etapa 1. Setup y dominio base.** Configuración del repositorio, `pyproject.toml`, estructura de carpetas. Implementación de las clases abstractas `FuenteDatos` y `Activo`, y de la clase `Mercado`. Tests vacíos pero funcionales. Hito: el proyecto importa, los tests corren (todos verdes con cero tests reales), `streamlit run` muestra una pantalla básica.

**Etapa 2. Fuentes de datos (síncrono).** Implementación de las tres fuentes con llamadas síncronas para validar que las APIs funcionan y entendemos sus particularidades. En esta etapa se descubren los problemas reales: rate limits, formatos heterogéneos, datos faltantes. Se documentan los hallazgos en `docs/decisiones.md`. Hito: un script standalone que pega a las tres APIs e imprime el precio actual de un activo de cada una.

**Etapa 3. Asincronía y caché.** Refactor de las fuentes a async con `aiohttp`. Implementación del decorador de caché. Implementación del benchmark sync vs async. Hito: la operación "refrescar todos los activos" tarda menos de la mitad que la versión sincrónica de la Etapa 2, con números reportados en `docs/benchmark.md`.

**Etapa 4. Métricas funcionales.** Implementación de todas las funciones puras del módulo `metricas/`. Tests unitarios exhaustivos. Hito: cobertura de tests del módulo `metricas/` superior al 90%.

**Etapa 5. UI básica (Panorama y Comparar).** Implementación de las dos primeras vistas de Streamlit. Componentes reutilizables (metric card, gráfico de líneas, heatmap). Tooltips y glosario. Hito: una persona que no es financista puede usar la aplicación y entender qué está mirando.

**Etapa 6. Modo Portfolio y persistencia cifrada.** Implementación de la vista "Mi Portfolio", del módulo de cifrado con Fernet, y de la importación/exportación CSV. Hito: un portfolio cargado se persiste cifrado, sobrevive un reinicio de la aplicación, y no es legible sin la clave.

**Etapa 7. Pulido, ética, peer review.** Documentación final: `etica.md` extendido, `glosario.md` completo, ADRs cierran sus pendientes, README pulido. Preparación de la presentación. Sesión de peer review con un compañero. Hito: la aplicación está lista para presentar y el repositorio está listo para entrega.

Cada etapa termina con una entrada en `docs/portafolio/` que registra qué se hizo, qué problemas aparecieron, cómo se resolvieron, y qué decisiones técnicas se tomaron en el camino.

---

## 12. Consideraciones Éticas en Profundidad

Esta sección documenta el análisis ético y legal del proyecto, en cumplimiento de la directriz académica de Ética y Responsabilidad Social. El análisis cubre tres dimensiones: el marco legal aplicable, la ética profesional en el dominio financiero, y los sesgos potenciales de la herramienta.

### 12.1 Marco legal aplicable

**Ley 18.331 de Protección de Datos Personales (Uruguay).** Esta ley regula el tratamiento de datos personales en el territorio uruguayo y establece principios de finalidad, legalidad, veracidad, previo consentimiento informado, seguridad y reserva. En el modo Observatorio puro, la aplicación no procesa datos personales: solo consume datos públicos de mercado. En el modo Portfolio, sí procesa datos personales en sentido amplio, dado que las tenencias económicas de una persona constituyen información sensible. La mitigación adoptada es triple. Primero, los datos no salen del dispositivo del usuario, lo que evita configuraciones de "tratamiento de datos por terceros". Segundo, los datos se almacenan cifrados con Fernet, lo que satisface el principio de seguridad. Tercero, no hay recopilación de datos identificatorios: la aplicación no pide nombre, email ni ningún dato personal adicional al ticker y la cantidad. Bajo este diseño, la aplicación queda fuera del alcance regulatorio sustancial de la Ley 18.331.

**Marco BCU/RNMV (Uruguay).** El Banco Central del Uruguay regula la actividad de asesoramiento de inversión a través del Registro Nacional del Mercado de Valores. La pregunta crítica es: ¿esta aplicación cae bajo esa regulación? La respuesta es no, por cuatro motivos. La aplicación es informativa, no recomendativa: muestra precios y métricas, pero nunca dice "comprá X" ni "vendé Y". La aplicación no gestiona dinero del usuario: no hay transacciones, no hay custodia, no hay órdenes. La aplicación no promete rendimientos: no hay simuladores que digan "si invertís X obtenés Y". La aplicación incorpora un disclaimer explícito de no asesoramiento, visible en cada pantalla. Esta combinación coloca al producto en el mismo régimen que un diario que publica cotizaciones: información pública sobre mercados, sin actividad regulada de intermediación o asesoramiento.

### 12.2 Ética profesional en el dominio financiero

El dominio financiero es éticamente sensible porque las decisiones que se toman con la información presentada pueden tener consecuencias económicas reales para los usuarios. Esto impone obligaciones específicas que el producto adopta deliberadamente.

**Disclaimer obligatorio.** Cada pantalla incluye un banner sutil pero visible con el texto "Datos informativos. No constituye asesoramiento financiero." con link a una explicación más extensa en una pantalla "Acerca de" que detalla los límites del producto. Al primer uso de la aplicación se muestra un modal que el usuario debe aceptar explícitamente.

**Comunicación honesta de incertidumbre.** Cada precio mostrado incluye el timestamp de cuándo fue obtenido. Cuando una fuente está caída y se muestra el último valor cacheado, se indica visualmente con un ícono y la edad del dato. Las métricas históricas indican explícitamente el período cubierto. Los gráficos de evolución incluyen un disclaimer "rendimiento pasado no garantiza rendimiento futuro" cuando aplica.

**Tono no inductivo.** El lenguaje de la interfaz evita verbos imperativos ("comprá", "invertí", "aprovechá") y adjetivos valorativos sobre los activos ("excelente oportunidad", "imperdible"). Los textos descriptivos son neutros: "el activo subió X%" en lugar de "el activo tuvo un fuerte rally". La diferencia parece sutil pero es ética.

**Riesgo siempre visible junto a rendimiento.** Cualquier vista que muestre rendimiento incluye también una métrica de riesgo (típicamente volatilidad clasificada cualitativamente). Esto contrarresta el sesgo natural del usuario a fijarse solo en lo que ganó o pudo haber ganado.

**Selección consciente de cotizaciones.** En Uruguay hay distintas cotizaciones del dólar (BROU comprador y vendedor, BCU) y la elección de cuál mostrar es una decisión económica, no neutra. La aplicación muestra todas las disponibles cuando aplica, con explicación de la diferencia, y deja al usuario elegir cuál usar como referencia para conversiones.

**Ajuste por inflación cuando aplica.** Mostrar el rendimiento nominal de un activo en moneda local sin contextualizar la inflación es engañoso. La aplicación, cuando muestra rendimientos en períodos largos, ofrece la opción de mostrarlos en moneda dura (USD) como referencia comparable, sumando un disclaimer educativo sobre por qué esto importa.

### 12.3 Sesgos potenciales de la herramienta

Toda herramienta de información tiene sesgos implícitos en sus decisiones de diseño. Documentarlos honestamente es parte del compromiso ético del proyecto.

**Sesgo de selección de mercados.** El proyecto cubre tres mercados elegidos por relevancia para el usuario latinoamericano. Esto invisibiliza otros mercados igualmente legítimos: bolsas europeas, mercados emergentes asiáticos, mercados de commodities, mercado inmobiliario. Un usuario que mira solo esta herramienta podría inferir incorrectamente que los tres mercados cubiertos son los únicos relevantes.

**Sesgo de selección de activos dentro de cada mercado.** Dentro de cripto, mostrar solo las top 10 por capitalización privilegia a los activos consolidados y oculta la parte especulativa del mercado. Dentro de USA, los componentes del S&P 500 son grandes empresas: las small caps quedan fuera. Estas decisiones son razonables para un MVP pero deben estar documentadas.

**Sesgo de moneda de referencia.** Convertir todo a USD para comparar es práctico pero ideológicamente cargado: implica que el dólar es la "moneda neutral" de referencia, lo que no es trivial en un contexto LATAM donde las economías han luchado históricamente con la dolarización. La herramienta ofrece la opción de cambiar la moneda base.

**Sesgo de rendimiento histórico.** Los rendimientos pasados se calculan sobre los activos que sobrevivieron. Esto es el clásico "sesgo de supervivencia": no vemos las criptomonedas que quebraron ni las acciones que dejaron de cotizar. Los rendimientos promedio mostrados son optimistas por construcción. Esta limitación se documenta en la pantalla "Acerca de".

---

## 13. Diseño de la Interfaz de Usuario

### Principios de diseño

La interfaz prioriza la legibilidad para usuarios sin formación financiera. Esto se traduce en cuatro principios operativos. Lenguaje simple en lugar de jerga: "la peor caída desde un máximo" en lugar de "máximo drawdown". Comparaciones concretas en lugar de números crudos: "1 Bitcoin equivale a 2.7 millones de pesos uruguayos". Visualizaciones que se entienden sin saber estadística: heatmaps de colores en lugar de matrices de correlación numéricas. Insights narrativos en lugar de tablas largas: "Bitcoin y el S&P 500 se movieron en direcciones opuestas esta semana" en lugar de tabla con la correlación.

### Vista 1: Panorama

Es la pantalla home y el modo de consulta rápida. La estructura es de arriba hacia abajo. En la franja superior, tres tarjetas con métricas (`st.metric`) que muestran de un vistazo: la cotización del dólar BROU, el precio de Bitcoin y el nivel del S&P 500, cada una con su variación porcentual respecto al día anterior y un sparkline mini. Debajo, un gráfico de líneas comparativo que muestra los tres mercados normalizados a base 100 al inicio del período (selector de período: 7 días, 30 días, 1 año), permitiendo ver de un vistazo cuál mercado tuvo mejor desempeño relativo. Debajo, una sección "Insights del día" con tres tarjetas narrativas escritas dinámicamente a partir de las métricas. Al pie, un disclaimer permanente.

### Vista 2: Comparar

Es la pantalla de análisis profundo. Permite seleccionar dos o más activos arbitrarios de cualquier mercado para compararlos en detalle. La estructura tiene un selector multi-select arriba con todos los activos disponibles. Debajo, un gráfico de líneas normalizadas con los activos seleccionados. A la derecha, una tabla compacta con métricas para cada activo seleccionado: rendimiento del período, volatilidad clasificada, drawdown máximo. Cada métrica tiene un tooltip con su explicación en lenguaje simple. Debajo del gráfico, un heatmap de correlaciones entre los activos seleccionados, con escala de colores intuitiva (rojo para correlación negativa, verde para positiva). Al pie, una explicación dinámica narrativa de los hallazgos principales.

### Vista 3: Mi Portfolio

Es la pantalla del modo opcional. Si no hay portfolio cargado, muestra un onboarding con opción de cargar manualmente o importar CSV. Si hay portfolio, la estructura es: en la franja superior, tres tarjetas con valor total (en USD, UYU y ARS para que cualquiera lo entienda), variación del día y variación del mes. Debajo, un treemap con la distribución del portfolio donde cada activo es un cuadrado proporcional a su peso, coloreado por mercado. A la derecha, una tabla editable de tenencias con opción de agregar, modificar y eliminar posiciones. Debajo, un gráfico de evolución del valor del portfolio en el tiempo. Al pie, opción de exportar a CSV y cerrar sesión (que cifra y guarda los cambios).

### Componentes reutilizables

El módulo `ui/componentes/` define componentes reutilizables que se usan en las tres vistas. La metric card extiende `st.metric` con un sparkline integrado. El gráfico de líneas es un wrapper sobre Plotly con tema custom y formateo de números en español. El heatmap aplica una paleta de colores accesible (compatible con daltonismo). El treemap usa Plotly con etiquetas legibles. El componente disclaimer aparece al pie de cada vista con el texto legal pertinente.

### Tema visual

El tema de Streamlit se configura en `.streamlit/config.toml`. La paleta es sobria: fondo claro (white smoke), texto oscuro (charcoal), acento principal en un azul sobrio (no el azul saturado típico fintech). Los colores semánticos son verde para positivo, rojo para negativo, amarillo para neutral o atención. La tipografía usa la fuente del sistema para máxima legibilidad. No hay animaciones llamativas: la herramienta busca transmitir confiabilidad, no entretener.

### Accesibilidad

La paleta de colores es accesible para daltonismo (probada con simuladores). Todos los gráficos tienen títulos descriptivos. Los datos numéricos siempre están disponibles también en formato tabular para usuarios que usan lectores de pantalla. La tipografía tiene tamaño mínimo de 14px en cuerpo y 16px en métricas principales.

---

## 14. Decisiones Arquitectónicas Clave (ADRs)

Esta sección resume las decisiones arquitectónicas más relevantes. Cada ADR completo vive en `docs/adr/`.

**ADR-001: Streamlit como framework de UI.** Se evaluaron Streamlit, FastAPI con frontend custom, y Dash. Se eligió Streamlit por tres razones: el costo de desarrollo es significativamente menor (semanas vs meses), el resultado visual es suficientemente profesional para una presentación académica, y el código permanece 100% en Python lo que mantiene la cohesión del proyecto. Las desventajas asumidas son: menor control sobre el layout, performance limitada en datasets grandes, y resultado menos diferenciado visualmente. Estas desventajas son aceptables para el alcance del proyecto.

**ADR-002: Plotly como librería de gráficos.** Se evaluaron matplotlib, seaborn, Plotly y Altair. Se eligió Plotly por dos razones: los gráficos son nativamente interactivos (hover, zoom, filtros) lo que mejora la demo, y la calidad visual default es superior a matplotlib sin esfuerzo adicional. La desventaja es el mayor peso de las dependencias, aceptable para una aplicación local.

**ADR-003: Pydantic en la frontera con APIs externas.** Se decidió validar con Pydantic todos los datos que cruzan la frontera entre las APIs externas y el dominio interno. La razón es que las APIs externas pueden cambiar formato sin previo aviso, y la validación temprana convierte errores silenciosos (datos corruptos en el dominio) en errores ruidosos (excepción explícita en el punto de entrada). **El orden es regex → Pydantic**: primero la limpieza sintáctica (espacios, encoding, formatos heterogéneos de fecha), después la validación semántica (precio > 0, moneda con 3 caracteres, símbolo no vacío). Los modelos viven en `fuentes/esquemas.py` como `CotizacionDTO`, `PuntoPrecioDTO` e `HistoricoDTO`.

**ADR-004: Separación estricta entre OOP y funcional.** Las clases modelan entidades del dominio (activos, mercados, fuentes). Las funciones puras modelan operaciones matemáticas (métricas). No hay métodos de instancia que sean cálculos puros: si una operación no depende del estado del objeto, va como función pura en `metricas/`. Esta separación facilita el testing y mantiene cada paradigma haciendo lo que mejor hace.

**ADR-005: Cifrado de portfolio con Fernet, encapsulado en clase `AlmacenCifrado`.** Se eligió Fernet (de la librería `cryptography`) sobre alternativas más complejas (AES-GCM directo, SQLCipher) por simplicidad. Fernet provee AES-128-CBC con HMAC-SHA256 para autenticación, formato versionado, y una API de bajo nivel difícil de usar mal. La clave deriva del password del usuario vía PBKDF2-SHA256 (200.000 iteraciones, salt fijo del proyecto).

**Decisión de diseño (V2):** las primitivas criptográficas (`cifrar(plano, clave)`, `descifrar(token, clave)`, `derivar_clave(password)`) se encapsulan en una **clase `AlmacenCifrado`** en `persistencia/almacen.py`, no se exponen como funciones libres de módulo. La clase tiene como atributos `ruta: Path`, `salt: bytes` e `iteraciones: int = 200_000`, y expone métodos públicos `guardar(portfolio, password)`, `cargar(password) -> Portfolio`, `existe() -> bool`. Las primitivas criptográficas son métodos protegidos (`_derivar_clave`, `_cifrar`, `_descifrar`). Esta decisión cumple la directriz 7.2 "OOP mandatorio" también en la capa de persistencia: el estado (ruta del archivo, salt, parámetros KDF) queda encapsulado en la clase en lugar de viajar como argumento de funciones libres.

El nivel de protección es suficiente para datos de portfolio personal en un dispositivo personal. El modelo de amenaza explícito está en `docs/etica.md`.

**ADR-006: Caché en memoria con TTL para precios actuales.** Los precios actuales tienen TTL de 60 segundos. Esto reduce drásticamente las llamadas a APIs durante una sesión de uso normal sin sacrificar frescura. El TTL es configurable por fuente vía variable de entorno.

**ADR-007: Idioma del dominio en español.** Las clases, funciones y variables del dominio financiero se nombran en español. Esto facilita la lectura del código por evaluadores hispanohablantes y reduce la fricción de traducción mental durante el desarrollo. La excepción son los términos técnicos universales sin traducción establecida (`ticker`, `cache`).

---

## 15. Glosario Técnico

Este glosario es referencia interna; el glosario de cara al usuario está en `docs/glosario.md` y se expone en la UI vía tooltips.

**Activo financiero.** Cualquier instrumento con valor económico que se puede comprar y vender. En este proyecto: criptomonedas, acciones y divisas.

**API REST.** Interfaz de programación que sigue el estilo arquitectónico REST, accedida sobre HTTP. Las tres fuentes del proyecto son APIs REST.

**BCU.** Banco Central del Uruguay. Regulador del sistema financiero uruguayo.

**BROU.** Banco República Oriental del Uruguay. Banco estatal uruguayo. Su cotización del dólar es referencia.

**Caché.** Almacenamiento temporal de datos para evitar recalcularlos o re-pedirlos. En este proyecto, en memoria con TTL.

**Correlación.** Medida estadística entre -1 y +1 de la relación entre dos series temporales.

**Drawdown.** Caída desde un máximo histórico hasta el siguiente mínimo, expresada en porcentaje.

**Fernet.** Especificación de cifrado simétrico autenticado de la librería `cryptography`. Usa AES-128-CBC + HMAC-SHA256.

**FuenteDatos.** Clase abstracta del proyecto que representa una fuente externa de datos de mercado.

**Función pura.** Función sin side effects que siempre devuelve el mismo resultado para los mismos argumentos.

**Polimorfismo.** Capacidad de tratar objetos de distinto tipo a través de una interfaz común.

**Rendimiento.** Cambio porcentual del precio en un período.

**RNMV.** Registro Nacional del Mercado de Valores. Registro uruguayo de actores del mercado de valores.

**S&P 500.** Índice estadounidense de las 500 empresas más grandes que cotizan en bolsa.

**Spread.** Diferencia entre precio de compra y precio de venta. En cotizaciones del BROU, el margen del banco.

**Ticker.** Símbolo identificatorio de un activo en su mercado. Por ejemplo: AAPL para Apple, BTC para Bitcoin.

**TTL.** Time To Live. Tiempo de vida útil de un dato cacheado antes de considerarse vencido.

**Volatilidad.** Medida estadística de la inestabilidad de los precios. Técnicamente, desviación estándar de los rendimientos.

---

## 16. Riesgos y Mitigaciones

**Riesgo: alguna de las tres APIs deja de funcionar durante el desarrollo.** Probabilidad media. Impacto medio. Mitigación: cada fuente tiene un fallback documentado (Twelve Data para Yahoo, scraping ligero del BROU si DolarApi cae). Si una fuente queda permanentemente fuera, la arquitectura permite reemplazarla sin afectar el resto del sistema.

**Riesgo: el alcance se va de tiempo.** Probabilidad alta. Impacto alto. Mitigación: cada etapa tiene un hito demostrable y la prioridad es entregar las primeras cinco etapas (que constituyen un MVP funcional) antes de pulir las dos últimas. La etapa 6 (modo portfolio) es deseable pero recortable si el tiempo aprieta.

**Riesgo: la presentación final no es entendible para audiencia no técnica.** Probabilidad media. Impacto alto. Mitigación: el glosario y los tooltips son parte del producto desde Etapa 5, no un add-on al final. Se hace al menos una sesión de prueba con una persona no técnica antes de la entrega.

**Riesgo: rate limits de las APIs cortan el desarrollo.** Probabilidad baja. Impacto bajo. Mitigación: el caché con TTL reduce las llamadas. En desarrollo se usa un mock de las APIs para no consumir cuota. CoinGecko free tier es la más restrictiva (30 req/min) pero suficiente para uso normal.

**Riesgo: cambios de schema en las APIs durante el desarrollo.** Probabilidad media. Impacto medio. Mitigación: la validación con Pydantic en la frontera detecta cambios de schema rápidamente y aísla el problema en la capa de fuentes sin contaminar el dominio.

**Riesgo: vulnerabilidades en el cifrado del portfolio.** Probabilidad baja. Impacto medio. Mitigación: se usa Fernet en lugar de cifrado custom. Las claves derivan de password con PBKDF2. La aplicación documenta explícitamente que el modelo de amenaza cubre solo "alguien con acceso al archivo, sin la contraseña" y no ataques sofisticados.

---

## 17. Plan de Presentación

La presentación final se estructura como una demo guiada de quince minutos con tres bloques. El primer bloque, de tres minutos, presenta el problema y el contexto: por qué un usuario LATAM necesita una vista panorámica de mercados, qué herramientas existen y por qué ninguna llena este nicho específico. El segundo bloque, de ocho minutos, es la demo de la aplicación: se recorre la vista Panorama, luego Comparar mostrando un análisis concreto interesante (por ejemplo, la correlación entre Bitcoin y el S&P 500 en 2024), luego Mi Portfolio cargando un portfolio de ejemplo y mostrando la persistencia cifrada. El tercer bloque, de cuatro minutos, presenta el detrás de escena: la arquitectura OOP, el benchmark sync vs async con números, la decisión de usar funciones puras para métricas, y el análisis ético con énfasis en por qué se decidió no caer bajo regulación BCU.

El soporte visual de la presentación combina la propia aplicación funcionando en vivo con una presentación corta de respaldo (cinco a siete slides) que cubren el contexto del problema, la arquitectura de alto nivel, el benchmark, y el cierre. Se prepara un dataset de demo con datos cacheados localmente para que la demo no dependa de la conectividad ni del estado de las APIs en el momento de presentar.

El portafolio digital se entrega como parte del repositorio en `docs/portafolio/`, con una entrada por etapa que captura el aprendizaje. El peer review se coordina con un compañero del curso usando el checklist en `docs/peer-review/checklist.md`, y los hallazgos se documentan como issues en el repositorio que se cierran antes de la entrega final.

---

## Apéndice A: Comandos útiles

```bash
# Setup inicial
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate      # Windows
pip install -e ".[dev]"

# Correr la aplicación
streamlit run src/observatorio/ui/app.py

# Tests
pytest                              # todos los tests
pytest tests/test_metricas/          # solo métricas
pytest --cov=src/observatorio       # con coverage

# Linting y type checking
ruff check src/ tests/
ruff format src/ tests/
mypy src/

# Benchmark
python scripts/benchmark_async.py
```

## Apéndice B: Variables de entorno

```bash
# Opcionales, todas tienen defaults sensatos
OBSERVATORIO_CACHE_TTL=60                   # segundos
OBSERVATORIO_TIMEOUT_API=10                  # segundos
OBSERVATORIO_LOG_LEVEL=INFO
OBSERVATORIO_DATA_DIR=./data                 # base para cache y portfolio
OBSERVATORIO_TWELVE_DATA_API_KEY=            # opcional, fallback de Yahoo
```

---

**Última actualización del documento:** V2 — 2026-05-19. Revisión de coherencia con `pipeline_observatorio V2.md` y `diagramas_uml V2.html`. Este documento se versiona junto al código y se actualiza cuando cambian decisiones arquitectónicas. Los cambios significativos generan una entrada en `docs/decisiones.md`.
