"""
Pipeline completo de limpieza de datos para censo ficticio uruguayo.
Ejecutar con: python pipeline_censo.py
"""

import re
import os
import pandas as pd
from io import StringIO

# Intentar importar chardet (opcional)
try:
    import chardet
    CHARDET_DISPONIBLE = True
except ImportError:
    CHARDET_DISPONIBLE = False


# =============================================================================
# ETAPA 1 — CARGAR
# =============================================================================

def cargar_datos(ruta: str) -> pd.DataFrame:
    """Carga el CSV detectando el encoding correcto de forma robusta."""
    encodings_a_probar = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']

    # Intentar detección automática con chardet
    if CHARDET_DISPONIBLE:
        try:
            with open(ruta, 'rb') as f:
                resultado = chardet.detect(f.read())
            enc_detectado = resultado.get('encoding')
            if enc_detectado and enc_detectado.lower() not in [e.lower() for e in encodings_a_probar]:
                encodings_a_probar.insert(0, enc_detectado)
            elif enc_detectado:
                # Moverlo al frente si ya está en la lista
                encodings_a_probar = [enc_detectado] + [e for e in encodings_a_probar if e.lower() != enc_detectado.lower()]
            print(f"[chardet] Encoding detectado automáticamente: {enc_detectado}")
        except Exception as e:
            print(f"[chardet] No se pudo detectar automáticamente: {e}")

    df = None
    encoding_usado = None

    for enc in encodings_a_probar:
        try:
            df = pd.read_csv(ruta, encoding=enc, dtype=str)
            # Verificar que no haya errores de decodificación reales
            # (algunos encodings como latin-1 nunca fallan pero producen basura)
            encoding_usado = enc
            print(f"[Etapa 1] Archivo leído con encoding: {enc}")
            break
        except (UnicodeDecodeError, Exception) as e:
            print(f"[Etapa 1] Fallo con encoding '{enc}': {e}")
            continue

    if df is None:
        raise ValueError(f"No se pudo leer el archivo '{ruta}' con ningún encoding conocido.")

    print(f"[Etapa 1] Shape del DataFrame: {df.shape}")
    print("[Etapa 1] Primeras 5 filas:")
    print(df.head(5).to_string())
    print()
    return df


# =============================================================================
# ETAPA 2 — INSPECCIONAR
# =============================================================================

TITULOS_PATRON = re.compile(
    r'^\s*(Srta\.?|Sra\.?|Sr\.?|Dra\.?|Dr\.?|Prof\.?|Ing\.?|Lic\.?)\s+',
    re.IGNORECASE
)
ENCODING_CORRUPTO_PATRON = re.compile(r'[ÃÂ]')
CI_FORMATO_PATRON = re.compile(r'^\d\.\d{3}\.\d{3}-\d$')
CI_FORMATO_7_PATRON = re.compile(r'^\d{3}\.\d{3}-\d$')
EMAIL_PATRON = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$')
CP_PATRON = re.compile(r'(?<![0-9])(\d{5})(?![0-9])')


def _tiene_problema_nombre(nombre: str) -> bool:
    """Devuelve True si el nombre tiene título, mayúsculas o encoding corrupto."""
    if pd.isna(nombre):
        return False
    nombre = str(nombre)
    if TITULOS_PATRON.match(nombre):
        return True
    if nombre == nombre.upper() and any(c.isalpha() for c in nombre):
        return True
    if ENCODING_CORRUPTO_PATRON.search(nombre):
        return True
    return False


def _tiene_problema_ci(ci: str) -> bool:
    """Devuelve True si la CI no tiene el formato X.XXX.XXX-X ni XXX.XXX-X."""
    if pd.isna(ci):
        return True
    ci = str(ci).strip()
    return not (CI_FORMATO_PATRON.match(ci) or CI_FORMATO_7_PATRON.match(ci))


def _tiene_problema_email(email: str) -> bool:
    """Devuelve True si el email no es válido."""
    if pd.isna(email):
        return True
    return not EMAIL_PATRON.match(str(email).strip())


def _tiene_problema_direccion(direccion: str) -> bool:
    """Devuelve True si la dirección no contiene un CP de 5 dígitos."""
    if pd.isna(direccion):
        return True
    return not CP_PATRON.search(str(direccion))


def inspeccionar_datos(df: pd.DataFrame) -> dict:
    """Inspecciona el DataFrame y reporta problemas por columna. Retorna el reporte."""
    print("=" * 60)
    print("[Etapa 2] INSPECCIÓN DE DATOS")
    print("=" * 60)

    # Nulos
    nulos = df.isnull().sum()
    print("\nValores nulos por columna:")
    print(nulos.to_string())

    # Problemas por columna
    reporte = {}

    if 'nombre' in df.columns:
        problemas_nombre = df['nombre'].apply(_tiene_problema_nombre).sum()
        reporte['nombre_problemas'] = int(problemas_nombre)
        print(f"\nnombre — registros con problemas: {problemas_nombre}")

    if 'ci' in df.columns:
        problemas_ci = df['ci'].apply(_tiene_problema_ci).sum()
        reporte['ci_problemas'] = int(problemas_ci)
        print(f"ci     — registros con formato incorrecto: {problemas_ci}")

    if 'email' in df.columns:
        problemas_email = df['email'].apply(_tiene_problema_email).sum()
        reporte['email_problemas'] = int(problemas_email)
        print(f"email  — registros con formato inválido: {problemas_email}")

    if 'direccion' in df.columns:
        problemas_dir = df['direccion'].apply(_tiene_problema_direccion).sum()
        reporte['direccion_sin_cp'] = int(problemas_dir)
        print(f"dir.   — registros sin código postal: {problemas_dir}")

    print()
    return reporte


# =============================================================================
# ETAPA 3 — LIMPIAR
# =============================================================================

def reparar_encoding(texto: str) -> str:
    """
    Detecta y repara texto con doble-encoding UTF-8 interpretado como Latin-1.
    Ejemplo: 'PÃ©rez' -> 'Pérez'
    """
    if not isinstance(texto, str):
        return texto
    if ENCODING_CORRUPTO_PATRON.search(texto):
        try:
            return texto.encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return texto
    return texto


TITULOS_LIMPIEZA = re.compile(
    r'^(Srta\.?|Sra\.?|Sr\.?|Dra\.?|Dr\.?|Prof\.?|Ing\.?|Lic\.?)\s+',
    re.IGNORECASE
)


def normalizar_nombre(nombre: str) -> str:
    """
    Limpia un nombre: repara encoding, quita títulos y aplica Title Case.
    Python 3 maneja correctamente caracteres acentuados con .title() de forma nativa.
    """
    if pd.isna(nombre):
        return nombre
    nombre = str(nombre).strip()
    nombre = reparar_encoding(nombre)
    # Quitar títulos repetidamente (por si hay más de uno)
    while True:
        nuevo = TITULOS_LIMPIEZA.sub('', nombre).strip()
        if nuevo == nombre:
            break
        nombre = nuevo
    # .title() en Python 3 es Unicode-aware: maneja á, é, ñ, ü correctamente
    return nombre.title()


def normalizar_ci(ci) -> 'str | None':
    """
    Normaliza una CI uruguaya al formato X.XXX.XXX-X (8 dígitos) o XXX.XXX-X (7 dígitos).
    Retorna None si la CI no es normalizable.
    """
    if pd.isna(ci):
        return None
    ci = str(ci).strip()
    # Quitar separadores
    solo_digitos = re.sub(r'[\.\-\s]', '', ci)
    # Validar que solo queden dígitos
    if not solo_digitos.isdigit():
        return None
    n = len(solo_digitos)
    if n == 8:
        return f"{solo_digitos[0]}.{solo_digitos[1:4]}.{solo_digitos[4:7]}-{solo_digitos[7]}"
    elif n == 7:
        return f"{solo_digitos[0:3]}.{solo_digitos[3:6]}-{solo_digitos[6]}"
    else:
        return None


def limpiar_datos(df: pd.DataFrame) -> tuple:
    """
    Limpia el DataFrame: elimina filas vacías, repara encoding y normaliza columnas.
    Retorna (df_limpio, conteo_encoding_reparados).
    """
    print("[Etapa 3] Limpiando datos...")

    # Eliminar filas completamente vacías
    df = df.dropna(how='all').copy()

    # Aplicar strip a todas las columnas string
    for col in df.select_dtypes(include='str').columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # Contar y reparar encoding corrupto en nombre y direccion
    encoding_reparados = 0

    def reparar_y_contar(texto):
        nonlocal encoding_reparados
        if isinstance(texto, str) and ENCODING_CORRUPTO_PATRON.search(texto):
            reparado = reparar_encoding(texto)
            if reparado != texto:
                encoding_reparados += 1
            return reparado
        return texto

    if 'nombre' in df.columns:
        df['nombre'] = df['nombre'].apply(reparar_y_contar)
    if 'direccion' in df.columns:
        df['direccion'] = df['direccion'].apply(reparar_y_contar)

    # Normalizar nombre
    if 'nombre' in df.columns:
        df['nombre'] = df['nombre'].apply(normalizar_nombre)

    print(f"[Etapa 3] Registros con encoding reparado: {encoding_reparados}")
    print("[Etapa 3] Limpieza completada.\n")
    return df, encoding_reparados


# =============================================================================
# ETAPA 4 — VALIDAR
# =============================================================================

_EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$')


def validar_email(email) -> bool:
    """
    Valida un email: debe tener un @, dominio con punto, extensión ≥2 chars y sin espacios.
    """
    if pd.isna(email):
        return False
    email = str(email).strip()
    if ' ' in email:
        return False
    return bool(_EMAIL_REGEX.match(email))


def validar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas 'email_valido' y 'ci_normalizada' al DataFrame."""
    print("[Etapa 4] Validando datos...")

    if 'email' in df.columns:
        df['email_valido'] = df['email'].apply(validar_email)
        invalidos = (~df['email_valido']).sum()
        print(f"[Etapa 4] Emails inválidos: {invalidos}")

    if 'ci' in df.columns:
        df['ci_normalizada'] = df['ci'].apply(normalizar_ci)
        ci_nulas = df['ci_normalizada'].isna().sum()
        print(f"[Etapa 4] CIs no normalizables (quedarán nulas): {ci_nulas}")

    print("[Etapa 4] Validación completada.\n")
    return df


# =============================================================================
# ETAPA 5 — TRANSFORMAR
# =============================================================================

# CP: exactamente 5 dígitos, no precedidos ni seguidos de otro dígito
_CP_REGEX = re.compile(r'(?<![0-9])(\d{5})(?![0-9])')


def extraer_codigo_postal(direccion) -> 'str | None':
    """
    Extrae el código postal de 5 dígitos de una dirección uruguaya.
    Retorna el CP como string o None si no existe.
    """
    if pd.isna(direccion):
        return None
    coincidencias = _CP_REGEX.findall(str(direccion))
    if coincidencias:
        return coincidencias[0]
    return None


def transformar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega 'codigo_postal', reemplaza nombre y ci, elimina columna auxiliar."""
    print("[Etapa 5] Transformando datos...")

    if 'direccion' in df.columns:
        df['codigo_postal'] = df['direccion'].apply(extraer_codigo_postal)
        encontrados = df['codigo_postal'].notna().sum()
        print(f"[Etapa 5] Códigos postales encontrados: {encontrados}")

    # Reemplazar ci con la versión normalizada
    if 'ci_normalizada' in df.columns:
        df['ci'] = df['ci_normalizada']
        df = df.drop(columns=['ci_normalizada'])

    print("[Etapa 5] Transformación completada.\n")
    return df


# =============================================================================
# ETAPA 6 — EXPORTAR
# =============================================================================

def exportar_datos(df: pd.DataFrame, reporte_inicial: dict, encoding_reparados: int,
                   ruta_csv: str = 'censo_limpio.csv',
                   ruta_reporte: str = 'reporte_calidad.txt') -> None:
    """Guarda el CSV limpio y el reporte de calidad."""
    print("[Etapa 6] Exportando resultados...")

    # Guardar CSV limpio con UTF-8 BOM para compatibilidad con Excel
    df.to_csv(ruta_csv, index=False, encoding='utf-8-sig')
    print(f"[Etapa 6] CSV limpio guardado en: {os.path.abspath(ruta_csv)}")

    # Calcular estadísticas post-limpieza
    emails_invalidos_post = int((~df['email_valido']).sum()) if 'email_valido' in df.columns else 'N/A'
    ci_nulas_post = int(df['ci'].isna().sum()) if 'ci' in df.columns else 'N/A'
    cp_encontrados_post = int(df['codigo_postal'].notna().sum()) if 'codigo_postal' in df.columns else 'N/A'

    # Generar reporte de texto
    lineas = [
        "=" * 60,
        "REPORTE DE CALIDAD — PIPELINE CENSO URUGUAYO",
        "=" * 60,
        "",
        "--- PROBLEMAS DETECTADOS EN INSPECCIÓN INICIAL ---",
        f"  Nombres con problemas:       {reporte_inicial.get('nombre_problemas', 'N/A')}",
        f"  CIs con formato incorrecto:  {reporte_inicial.get('ci_problemas', 'N/A')}",
        f"  Emails inválidos:            {reporte_inicial.get('email_problemas', 'N/A')}",
        f"  Direcciones sin CP:          {reporte_inicial.get('direccion_sin_cp', 'N/A')}",
        "",
        "--- RESULTADOS POST-LIMPIEZA ---",
        f"  Registros con encoding reparado: {encoding_reparados}",
        f"  Emails inválidos restantes:      {emails_invalidos_post}",
        f"  CIs nulas (no normalizables):    {ci_nulas_post}",
        f"  Códigos postales encontrados:    {cp_encontrados_post}",
        f"  Total de registros finales:      {len(df)}",
        "",
        "=" * 60,
    ]

    with open(ruta_reporte, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lineas))

    print(f"[Etapa 6] Reporte guardado en: {os.path.abspath(ruta_reporte)}")
    print()


# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================

def ejecutar_pipeline(ruta_csv: str) -> pd.DataFrame:
    """
    Ejecuta el pipeline completo de limpieza de datos sobre el CSV indicado.
    Retorna el DataFrame limpio.
    """
    print("\n" + "=" * 60)
    print("  PIPELINE DE LIMPIEZA DE DATOS — CENSO URUGUAYO")
    print("=" * 60 + "\n")

    # Etapa 1: Cargar
    df = cargar_datos(ruta_csv)

    # Etapa 2: Inspeccionar
    reporte_inicial = inspeccionar_datos(df)

    # Etapa 3: Limpiar
    df, encoding_reparados = limpiar_datos(df)

    # Etapa 4: Validar
    df = validar_datos(df)

    # Etapa 5: Transformar
    df = transformar_datos(df)

    # Etapa 6: Exportar
    exportar_datos(df, reporte_inicial, encoding_reparados)

    print("[Pipeline] Completado exitosamente.")
    return df


# =============================================================================
# GENERADOR DEL CSV DE MUESTRA
# =============================================================================

def generar_csv_muestra(ruta: str = 'censo_ficticio.csv') -> None:
    """Genera un CSV de muestra con 15+ registros que cubren todos los casos problemáticos."""
    # Nota: los casos de encoding corrupto se escriben como latin-1 bytes interpretados
    # como si fueran texto UTF-8 mal leído. Para simular esto en el CSV guardado como
    # UTF-8, escribimos directamente las secuencias corruptas como cadenas Python.
    registros = [
        # nombre,                           ci,             email,                  direccion
        # Casos de nombre
        ("DR. JOSÉ PÉREZ",                  "1.234.567-8",  "jose@gmail.com",       "Av. 18 de Julio 1234, 11200, Montevideo"),
        ("ing. maría núñez",                "2345678",      "maria@hotmail.com",    "Calle Falsa 123, Salto"),
        ("dra. RamÃ³n GÃ³mez",             "3.456.789-0",  "ramon@yahoo.com",      "Calle JosÃ© Enrique RodÃ³ 456, 50000"),
        ("Laura Suárez",                    "4567890",      "laura@uy.edu",         "Bvar. Artigas 890, 11300, Montevideo"),
        ("Prof. CARLOS RODRÍGUEZ",          "5.678.901-2",  "carlos@gmail.com",     "Rambla 25 de Agosto 300, 11000"),
        # Casos de CI
        ("Ana Fernández",                   "12345678",     "ana@outlook.com",      "Rivera 567, 40000, Melo"),
        ("Pedro Alonso",                    "1.234567-8",   "pedro@gmail.com",      "Colonia 890, 11100, Montevideo"),
        ("Lucía Giménez",                   "AB12345",      "lucia@gmail.com",      "San José 234, 60000, Trinidad"),
        ("Tomás Berón",                     "1.234.567-8",  "tomas@correo.uy",      "Av. Italia 1500, 11600, Montevideo"),
        ("Valentina Pose",                  "123456",       "vale@gmail.com",       "Rincón 45, Paysandú"),
        # Casos de email
        ("Roberto Sosa",                    "9.876.543-2",  "juangmail.com",        "Sarandí 123, 11000, Montevideo"),
        ("Florencia Pérez",                 "8.765.432-1",  "juan@.com",            "Treinta y Tres 456, 30000"),
        ("Ignacio Martínez",               "7.654.321-0",  "juan @gmail.com",      "Av. Gral. Rivera 789, 11600"),
        # Casos de dirección
        ("Sofía Benítez",                   "6.543.210-9",  "sofia@gmail.com",      "Av. 18 de Julio 1234, 11200, Montevideo"),
        ("Lic. DIEGO CASTRO",               "5432109",      "diego@gmail.com",      "Calle Falsa 123, Salto"),
        # Extra con encoding corrupto en dirección
        ("Sra. NatÃ¡lia Vega",              "4.321.098-7",  "natalia@gmail.com",    "Calle JosÃ© Enrique RodÃ³ 456, 50000"),
    ]

    columnas = "nombre,ci,email,direccion\n"
    filas = []
    for r in registros:
        # Escapar comas dentro de campos con comillas
        campos = []
        for campo in r:
            if ',' in campo:
                campos.append(f'"{campo}"')
            else:
                campos.append(campo)
        filas.append(','.join(campos))

    contenido = columnas + '\n'.join(filas) + '\n'

    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(contenido)

    print(f"CSV de muestra generado: {os.path.abspath(ruta)}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Generar CSV de muestra si no existe
    if not os.path.exists("censo_ficticio.csv"):
        print("Generando CSV de muestra...")
        generar_csv_muestra("censo_ficticio.csv")

    ejecutar_pipeline("censo_ficticio.csv")
