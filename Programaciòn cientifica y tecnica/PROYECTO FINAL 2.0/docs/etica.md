# Analisis etico y legal — Observatorio Financiero LATAM

Este documento extiende la seccion 12 de `PROYECTO.md`. Cubre tres ejes: marco legal aplicable, etica profesional en el dominio financiero, y sesgos potenciales del producto.

## 1. Marco legal aplicable

### 1.1 Proteccion de datos personales

**Uruguay — Ley 18.331.** Regula el tratamiento de datos personales y establece principios de finalidad, legalidad, veracidad, consentimiento previo informado, seguridad y reserva.

**Como aplica al producto.**

| Modo | Datos personales tratados | Mitigacion |
|------|---------------------------|------------|
| Observatorio | Ninguno (solo datos publicos de mercado) | N/A |
| Mi Portfolio | Tenencias economicas (informacion sensible en sentido amplio) | (1) los datos no salen del dispositivo del usuario; (2) cifrado en reposo con Fernet (AES-128 + HMAC-SHA256) y derivacion de clave por PBKDF2 con 200k iteraciones; (3) no se solicita ningun dato identificatorio (nombre, email, documento) |

Bajo este diseno, el producto queda fuera del alcance regulatorio sustancial de la ley: no hay tratamiento por terceros, no hay base de datos centralizada, no hay datos identificatorios.

### 1.2 Asesoramiento financiero — BCU/RNMV (UY)

El producto **no constituye asesoramiento de inversion** ni cae bajo regulacion del Banco Central del Uruguay / Registro Nacional del Mercado de Valores, por las siguientes razones:

1. **Es informativo, no recomendativo.** Muestra precios y metricas. No emite recomendaciones de comprar, vender ni mantener.
2. **No gestiona dinero del usuario.** No hay transacciones, no hay custodia, no hay ordenes ni integracion con brokers.
3. **No promete rendimientos.** No incluye simuladores con proyecciones futuras.
4. **Disclaimer permanente.** Cada vista incluye el aviso "Datos informativos. No constituye asesoramiento financiero."

Esta combinacion lo coloca en el mismo regimen que un diario que publica cotizaciones.

## 2. Etica profesional

### 2.1 Disclaimer obligatorio

Visible en sidebar y al pie de cada vista. La pantalla "Acerca de" (en construccion) detalla los limites del producto y el modelo de amenaza del cifrado.

### 2.2 Comunicacion honesta de incertidumbre

- Cada cotizacion incluye implicitamente un timestamp (cache TTL = 60s).
- Si una fuente falla, se muestra ":warning: no disponible" en lugar de un cero o un dato viejo silencioso.
- Los graficos historicos muestran "rendimientos pasados no garantizan rendimientos futuros".

### 2.3 Tono no inductivo

El lenguaje evita verbos imperativos ("compra", "invierte") y adjetivos valorativos ("oportunidad", "imperdible"). Los textos descriptivos son neutros: "el activo subio X%".

### 2.4 Riesgo siempre junto a rendimiento

La vista Comparar muestra siempre la columna "Volatilidad / clasificacion" y "Peor caida %" al lado del rendimiento. Esto contrarresta el sesgo del usuario a fijarse solo en lo que gano.

## 3. Sesgos potenciales

### 3.1 Sesgo de seleccion de mercados

El producto cubre tres mercados elegidos por relevancia para el usuario LATAM. Esto invisibiliza otros mercados igualmente legitimos (Europa, Asia, commodities, real estate). Documentado.

### 3.2 Sesgo de seleccion de activos

Dentro de cripto se priorizan las top por capitalizacion; dentro de USA, el S&P 500. Las small caps y los activos especulativos quedan fuera. Decision razonable para un MVP, documentada.

### 3.3 Sesgo de moneda de referencia

Convertir todo a USD para comparar es practico pero no neutral en un contexto LATAM. La aplicacion permite visualizar valores tambien en UYU.

### 3.4 Sesgo de supervivencia

Los rendimientos pasados se calculan sobre los activos que sobrevivieron. Los activos que quebraron o dejaron de cotizar no aparecen. Los promedios mostrados son optimistas por construccion. Documentado en este archivo.

## 4. Modelo de amenaza del cifrado del Portfolio

**Cubre:** alguien con acceso al archivo `data/portfolio/portfolio.enc` que no tenga la contrasena. Sin la contrasena, el contenido es indescifrable en tiempos practicos por la combinacion AES-128-CBC + HMAC-SHA256 + PBKDF2-SHA256 (200k iteraciones, salt fijo del proyecto).

**No cubre:**
- Atacantes con keylogger u otro acceso al input del usuario.
- Atacantes con acceso a la memoria del proceso mientras el portfolio esta abierto.
- Ataques de fuerza bruta sobre contrasenas debiles (responsabilidad del usuario elegir una contrasena fuerte).
- Manipulacion de la propia aplicacion (supply-chain, dependencias maliciosas).

Esta delimitacion explicita es parte del compromiso etico de no sobre-prometer seguridad.
