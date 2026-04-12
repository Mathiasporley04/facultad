#!/usr/bin/env python3
"""Pipeline: Cruces ENG vs ESP — UEFA Champions League 2011-2025."""

import re, csv, os, sys
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── Configuración global ───────────────────────────────────────────────────────

ALIASES = {
    "manchester city": "Manchester City", "manchester city fc": "Manchester City",
    "chelsea": "Chelsea", "chelsea fc": "Chelsea",
    "arsenal": "Arsenal", "arsenal fc": "Arsenal",
    "liverpool": "Liverpool", "liverpool fc": "Liverpool",
    "tottenham": "Tottenham", "tottenham hotspur": "Tottenham", "tottenham hotspur fc": "Tottenham",
    "manchester united": "Manchester United", "manchester united fc": "Manchester United",
    "newcastle united": "Newcastle United", "newcastle united fc": "Newcastle United",
    "leicester city": "Leicester City", "leicester city fc": "Leicester City",
    "aston villa": "Aston Villa", "aston villa fc": "Aston Villa",
    "real madrid": "Real Madrid", "real madrid cf": "Real Madrid",
    "fc barcelona": "Barcelona", "barcelona": "Barcelona",
    "atletico madrid": "Atletico Madrid", "atletico de madrid": "Atletico Madrid",
    "atlético madrid": "Atletico Madrid", "atlético de madrid": "Atletico Madrid",
    "club atletico de madrid": "Atletico Madrid", "club atlético de madrid": "Atletico Madrid",
    "sevilla": "Sevilla", "sevilla fc": "Sevilla",
    "valencia": "Valencia", "valencia cf": "Valencia",
    "real sociedad": "Real Sociedad",
    "villarreal": "Villarreal", "villarreal cf": "Villarreal",
    "athletic club": "Athletic Club", "athletic bilbao": "Athletic Club",
    "girona": "Girona", "girona fc": "Girona",
}

FASES_POST_GRUPOS = {
    "round of 16", "last 16", "quarterfinals", "semifinals", "final",
    "playoffs, matchday 1", "playoffs, matchday 2",
    "finals, round of 16", "finals, quarterfinals", "finals, semifinals", "finals, final",
}

FASE_MAP = {
    "round of 16": "Octavos", "last 16": "Octavos", "finals, round of 16": "Octavos",
    "playoffs, matchday 1": "Playoffs", "playoffs, matchday 2": "Playoffs",
    "quarterfinals": "Cuartos", "finals, quarterfinals": "Cuartos",
    "semifinals": "Semis", "finals, semifinals": "Semis",
    "final": "Final", "finals, final": "Final",
}

# ── Helpers internos ───────────────────────────────────────────────────────────

def _parsear_marcador(area):
    """Extrae (score_raw, had_aet, had_pen, pen_score) del área de texto tras el equipo 2."""
    if m := re.search(r'(\d+-\d+)\s+pen\.\s+(\d+-\d+)', area):  # marcador con penales, ej. "1-1 pen. 4-3"
        return m.group(2), True, True, m.group(1)
    if m := re.search(r'(\d+-\d+)\s+a\.e\.t\.', area):  # marcador con prórroga (after extra time), ej. "2-1 a.e.t."
        return m.group(1), True, False, None
    if m := re.search(r'(\d+-\d+)', area):  # marcador normal, ej. "3-0"
        return m.group(1), False, False, None
    return None, False, False, None

def _parsear_linea_partido(linea, season, stage):
    """Convierte una línea cruda en un dict de partido; devuelve None si no es válida."""
    linea = re.sub(r'^\d{1,2}\.\d{2}\s+', '', linea)  # elimina minuto al inicio, ej. "3.45 " → ""
    partes = linea.split(' v ', 1)
    if len(partes) != 2:
        return None
    team1_raw, resto = partes[0].strip(), partes[1]
    codigos = list(re.finditer(r'\([A-Z]{2,3}\)', resto))  # busca todos los códigos de país en el lado del equipo 2, ej. "(ENG)"
    if not codigos or not re.search(r'\([A-Z]{2,3}\)\s*$', team1_raw):  # verifica que team1 también termine con código de país
        return None
    ultimo = codigos[-1]
    score_raw, had_aet, had_pen, pen_score = _parsear_marcador(resto[ultimo.end():].strip())
    return {"season": season, "stage": stage,
            "team1": team1_raw, "team2": resto[:ultimo.end()].strip(),
            "score_raw": score_raw, "had_aet": had_aet,
            "had_pen": had_pen, "pen_score": pen_score}

# ══════════════════════════════════════════════
#  PASO 01 — CARGAR
# ══════════════════════════════════════════════

def cargar_archivos(directorio: str) -> list:
    """
    Lee todos los cl.txt del árbol de directorios y devuelve registros crudos.
    No limpia ni transforma. Solo lee y estructura.
    Recibe: ruta al directorio raíz. Devuelve: lista de dicts por partido.
    """
    registros, n = [], 0
    for raiz, _, archivos in os.walk(directorio):
        for nombre in archivos:
            if nombre != "cl.txt":
                continue
            try:
                lineas = open(os.path.join(raiz, nombre), encoding="utf-8").readlines()
            except Exception as e:
                print(f"  [AVISO 01] {os.path.join(raiz, nombre)}: {e}"); continue
            n += 1
            season = stage = None
            for linea in lineas:
                s = linea.strip()
                if s.startswith("= UEFA"):
                    if m := re.search(r'(\d{4}/\d{2})', s): season = m.group(1)  # extrae temporada, ej. "2023/24"
                elif s.startswith("»"):
                    stage = s[1:].strip()
                elif " v " in s and season and stage:
                    if r := _parsear_linea_partido(s, season, stage):
                        registros.append(r)
    print(f"[01 CARGAR] {n} archivos cargados → {len(registros)} líneas de partido leídas")
    return registros

# ══════════════════════════════════════════════
#  PASO 02 — INSPECCIONAR
# ══════════════════════════════════════════════

def inspeccionar(registros: list) -> None:
    """
    Imprime un resumen del dataset crudo. No modifica nada.
    Recibe: lista de dicts de cargar_archivos().
    """
    print("\n[02 INSPECCIONAR]")
    print(f"  Partidos cargados : {len(registros)}")
    t = sorted({r["season"] for r in registros})
    print(f"  Temporadas únicas : {len(t)} → {t}")
    print(f"  Fases únicas      : {sorted({r['stage'] for r in registros})}")
    paises = set()
    for r in registros:
        for campo in ("team1", "team2"):
            if m := re.search(r'\(([A-Z]{2,3})\)\s*$', r[campo]):  # captura código de país al final del nombre, ej. "Chelsea (ENG)" → "ENG"
                paises.add(m.group(1))
    print(f"  Países únicos     : {sorted(paises)}")
    print("\n  Primeros 5 registros crudos:")
    for r in registros[:5]: print(f"    {r}")
    sin = sum(1 for r in registros if r["score_raw"] is None)
    print(f"\n  [AVISO 02] {sin} sin marcador (se descartarán en LIMPIAR)" if sin
          else "\n  Todos los registros tienen marcador válido.")

# ══════════════════════════════════════════════
#  PASO 03 — LIMPIAR
# ══════════════════════════════════════════════

def limpiar(registros: list) -> list:
    """
    Parsea y normaliza cada registro: extrae país, separa goles, aplica aliases.
    Descarta filas sin marcador válido, sin código de país, o con N.N.
    Recibe: lista cruda. Devuelve: lista limpia con campos adicionales.
    """
    limpios, desc_m, desc_p = [], 0, 0
    for r in registros:
        if not (r["score_raw"] and re.match(r'^\d+-\d+$', r["score_raw"])):  # descarta si el marcador no es exactamente "N-N"
            desc_m += 1; continue
        m1 = re.search(r'\(([A-Z]{2,3})\)\s*$', r["team1"])  # extrae código de país de team1, ej. "(ESP)"
        m2 = re.search(r'\(([A-Z]{2,3})\)\s*$', r["team2"])  # extrae código de país de team2
        n1 = r["team1"][:m1.start()].strip() if m1 else ""
        n2 = r["team2"][:m2.start()].strip() if m2 else ""
        if not m1 or not m2 or n1.upper() == "N.N." or n2.upper() == "N.N.":
            desc_p += 1; continue
        g1, g2 = map(int, r["score_raw"].split("-"))
        pen_t1 = pen_t2 = None
        if r["had_pen"] and r["pen_score"]:
            pen_t1, pen_t2 = map(int, r["pen_score"].split("-"))
        limpios.append({
            "season": r["season"], "stage": r["stage"],
            "team1": ALIASES.get(n1.lower(), n1.title()), "team1_pais": m1.group(1),
            "team2": ALIASES.get(n2.lower(), n2.title()), "team2_pais": m2.group(1),
            "goles_t1": g1, "goles_t2": g2,
            "had_aet": r["had_aet"], "had_pen": r["had_pen"],
            "pen_t1": pen_t1, "pen_t2": pen_t2,
        })
    print(f"\n[03 LIMPIAR]  Sin marcador: {desc_m} | Sin país/N.N.: {desc_p} | Limpios: {len(limpios)}")
    return limpios

# ══════════════════════════════════════════════
#  PASO 04 — VALIDAR
# ══════════════════════════════════════════════

def validar(registros: list) -> list:
    """
    Aplica los filtros de negocio en cascada:
      temporada 2012-2025 → fase post-grupos → cruces ENG vs ESP.
    Recibe: lista limpia. Devuelve: registros que superan los tres filtros.
    """
    print("\n[04 VALIDAR]")
    t = [r for r in registros if 2012 <= int(r["season"].split("/")[0]) + 1 <= 2025]
    print(f"  Tras filtro de temporada (2012–2025) : {len(t):>4} / {len(registros)} partidos")
    f = [r for r in t if r["stage"].lower() in FASES_POST_GRUPOS]
    print(f"  Tras filtro de fase post-grupos      : {len(f):>4} partidos")
    result = [r for r in f if {r["team1_pais"], r["team2_pais"]} == {"ENG", "ESP"}]
    print(f"  Partidos ENG vs ESP                  : {len(result):>4}")
    if not result:
        print("  [ERROR 04] No se encontraron partidos ENG vs ESP.")
    return result

# ══════════════════════════════════════════════
#  PASO 05 — TRANSFORMAR
# ══════════════════════════════════════════════

def transformar(registros: list) -> tuple:
    """
    Agrupa partidos en cruces y calcula quién ganó cada uno.
    Clave de agrupación: (temporada, fase_normalizada, frozenset({ing, esp})).
    Recibe: registros filtrados. Devuelve: ([cruces], {estadísticas}).
    """
    print("\n[05 TRANSFORMAR]")
    grupos = defaultdict(list)
    for r in registros:
        ing = r["team1"] if r["team1_pais"] == "ENG" else r["team2"]
        esp = r["team2"] if r["team1_pais"] == "ENG" else r["team1"]
        grupos[(r["season"], FASE_MAP.get(r["stage"].lower(), r["stage"]), frozenset([ing, esp]))].append(r)

    cruces = []
    for (season, fase, _), partidos in sorted(grupos.items()):
        p0 = partidos[0]
        club_ing = p0["team1"] if p0["team1_pais"] == "ENG" else p0["team2"]
        club_esp = p0["team2"] if p0["team1_pais"] == "ENG" else p0["team1"]

        gi = ge = 0
        pen_p = None
        for p in partidos:
            if p["team1_pais"] == "ENG":
                gi += p["goles_t1"]; ge += p["goles_t2"]
            else:
                gi += p["goles_t2"]; ge += p["goles_t1"]
            if p["had_pen"]: pen_p = p

        if gi > ge:
            res = "Victoria inglesa"
        elif ge > gi:
            res = "Victoria española"
        elif pen_p:
            pi = pen_p["pen_t1"] if pen_p["team1_pais"] == "ENG" else pen_p["pen_t2"]
            pe = pen_p["pen_t2"] if pen_p["team1_pais"] == "ENG" else pen_p["pen_t1"]
            res = "Victoria inglesa (pen.)" if pi > pe else "Victoria española (pen.)"
        else:
            res = "Empate / a resolver"

        cruces.append({"temporada": season, "fase": fase,
                       "club_ingles": club_ing, "club_espanol": club_esp,
                       "goles_ingles": gi, "goles_espanol": ge,
                       "penales": pen_p is not None, "resultado": res,
                       "partidos": len(partidos)})

    total = len(cruces)
    vi  = sum(1 for c in cruces if "Victoria inglesa"  in c["resultado"])
    ve  = sum(1 for c in cruces if "Victoria española" in c["resultado"])
    vip = sum(1 for c in cruces if c["resultado"] == "Victoria inglesa (pen.)")
    vep = sum(1 for c in cruces if c["resultado"] == "Victoria española (pen.)")
    tp  = vip + vep
    pi_pct = vi / total * 100 if total else 0.
    pe_pct = ve / total * 100 if total else 0.

    est = {"total_cruces": total, "victorias_inglesas": vi, "victorias_espanolas": ve,
           "pct_ing": pi_pct, "pct_esp": pe_pct,
           "vic_ing_pen": vip, "vic_esp_pen": vep, "total_pen": tp}

    sep = "═" * 51
    print(f"  ╔{sep}╗\n  ║   CRUCES ING vs ESP — Champions League 2012–2025   ║")
    print(f"  ╠{sep}╣\n  ║  Total de cruces              :  {total:>3}               ║")
    print(f"  ╠{sep}╣")
    print(f"  ║  Victorias inglesas           :  {vi:>3}  ( {pi_pct:>5.1f}% )  ║")
    print(f"  ║  Victorias españolas          :  {ve:>3}  ( {pe_pct:>5.1f}% )  ║")
    if tp:
        print(f"  ╠{sep}╣\n  ║  EXTRA — Cruces decididos a penales:              ║")
        print(f"  ║    → Victoria inglesa en penales  :   {vip:>2}           ║")
        print(f"  ║    → Victoria española en penales :   {vep:>2}           ║")
    print(f"  ╚{sep}╝\n")
    print(f"  {'Temporada':<10} {'Fase':<10} {'Enfrentamiento':<46} Resultado")
    print(f"  {'-'*95}")
    for c in sorted(cruces, key=lambda x: x["temporada"]):
        print(f"  {c['temporada']:<10} {c['fase']:<10} "
              f"{c['club_ingles'] + ' vs ' + c['club_espanol']:<46} {c['resultado']}")

    return cruces, est

# ══════════════════════════════════════════════
#  PASO 06 — EXPORTAR
# ══════════════════════════════════════════════

def exportar(cruces: list, estadisticas: dict, carpeta_salida: str) -> None:
    """
    Guarda los resultados en disco. No calcula nada nuevo.
    Genera cruces_ing_esp.csv y resumen_ing_esp.txt en carpeta_salida.
    Recibe: lista de cruces y dict de estadísticas de transformar().
    """
    print("\n[06 EXPORTAR]")
    os.makedirs(carpeta_salida, exist_ok=True)

    ruta_csv = os.path.join(carpeta_salida, "cruces_ing_esp.csv")
    cols = ["temporada", "fase", "club_ingles", "club_espanol",
            "goles_ingles", "goles_espanol", "penales", "resultado", "partidos"]
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for c in sorted(cruces, key=lambda c: c["temporada"]): w.writerow(c)
    print(f"  ✓ {ruta_csv}  — {len(cruces)} filas")

    ruta_txt = os.path.join(carpeta_salida, "resumen_ing_esp.txt")
    e = estadisticas
    with open(ruta_txt, "w", encoding="utf-8") as f:
        f.write("CRUCES INGLATERRA vs ESPAÑA — UEFA Champions League 2012–2025\n" + "="*64 + "\n\n")
        f.write(f"Total de cruces            : {e['total_cruces']}\n"
                f"Victorias inglesas         : {e['victorias_inglesas']}  ({e['pct_ing']:.1f}%)\n"
                f"Victorias españolas        : {e['victorias_espanolas']}  ({e['pct_esp']:.1f}%)\n")
        if e["total_pen"]:
            f.write(f"\nCruces decididos a penales :\n"
                    f"  Victoria inglesa  : {e['vic_ing_pen']}\n"
                    f"  Victoria española : {e['vic_esp_pen']}\n")
        f.write("\n\nLISTADO DETALLADO DE CRUCES\n" + "-"*64 + "\n")
        f.write(f"{'Temporada':<10} {'Fase':<10} {'Club inglés':<22} "
                f"{'Club español':<22} {'Goles':<7} Resultado\n" + "-"*64 + "\n")
        for c in sorted(cruces, key=lambda c: c["temporada"]):
            pen = " *" if c["penales"] else ""
            f.write(f"{c['temporada']:<10} {c['fase']:<10} {c['club_ingles']:<22} "
                    f"{c['club_espanol']:<22} {c['goles_ingles']}-{c['goles_espanol']:<6} "
                    f"{c['resultado']}{pen}\n")
        f.write("\n(* = cruce decidido a penales)\n")
    print(f"  ✓ {ruta_txt}  — guardado")

# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "champions-league")
    out_dir = os.path.join(base_dir, "output")
    
    registros_crudos    = cargar_archivos(data_dir)
    inspeccionar(registros_crudos)
    registros_limpios   = limpiar(registros_crudos)
    registros_filtrados = validar(registros_limpios)
    cruces, estadisticas = transformar(registros_filtrados)
    exportar(cruces, estadisticas, out_dir)
