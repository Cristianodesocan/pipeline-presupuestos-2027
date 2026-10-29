"""Motor de parseo del Tomo 3 «Resúmenes» por coordenadas.

Capas (diseno_extraccion_tomo3.md §3):
  1. localizar   leer_indice() -> rango de páginas por sección; el título solo verifica la página
  2. geometría   palabras con x0/x1/top -> líneas visuales; anclas x de columna calibradas por TABLA
  3. filas       código / nivel (detalle, grupo, total) / denominación (con líneas partidas)
El paso a formato tidy y la validación viven en extraer_tomo3.py y validar_extraccion.py.
"""
import re
from dataclasses import dataclass, field

from .numeros_es import a_numero, es_numero

# Parámetros geométricos (puntos PDF), fijados con la serie 2015-2026
TOL_LINEA = 3.0          # misma línea visual si |Δtop| ≤ 3
BANDA_CABECERA = (-15, 8)  # palabras alrededor de «Cod.» que forman la cabecera
TOL_CLUSTER = 6.0        # agrupación de bordes derechos en anclas
TOL_ANCLA = 10.0         # distancia máxima token-ancla; si es mayor, el token vuelve al texto
X_MIN_NUMEROS = 250.0    # a la izquierda solo hay código y denominación
X_MAX_CODIGO = 80.0      # el código de fila empieza antes de esta x
DIST_HUERFANA = 14.0     # una línea sin cifras se une a la fila más cercana si está a ≤ 14
MARGEN_PIE = 40.0

RE_INDICE = re.compile(r"^(\d+(?:\.\d+)?)\.\s+(.+?)\s*\.{3,}\s*(?:p[áa]g\.\s*)?(\d+)$")
RE_CABECERA = re.compile(r"^C[oó]d")


# ----------------------------------------------------------------------------- 1. localizar
def leer_indice(pdf) -> dict[str, tuple[str, int, int]]:
    """{sección: (título, página_inicio, página_fin)} a partir de la página ÍNDICE.

    2015 escribe «pág. 16»; las entradas largas ocupan dos líneas y se unen.
    """
    for pg in pdf.pages[:5]:
        texto = pg.extract_text() or ""
        if "ÍNDICE" not in texto.upper():
            continue
        entradas, pendiente = [], ""
        for linea in texto.split("\n"):
            linea = f"{pendiente} {linea.strip()}".strip() if pendiente else linea.strip()
            m = RE_INDICE.match(linea)
            if m:
                entradas.append((m.group(1), m.group(2), int(m.group(3))))
                pendiente = ""
            elif re.match(r"^\d+(?:\.\d+)?\.\s", linea):
                pendiente = linea
        indice = {}
        for k, (sec, titulo, inicio) in enumerate(entradas):
            fin = entradas[k + 1][2] - 1 if k + 1 < len(entradas) else len(pdf.pages)
            indice[sec] = (titulo, inicio, fin)
        return indice
    raise ValueError("El documento no tiene página ÍNDICE")


def paginas_tabla(pdf, indice: dict, spec: dict) -> list[int]:
    """Páginas (1-based) del rango de la sección cuyo texto contiene el título."""
    _, inicio, fin = indice[spec["indice"]]
    return [n for n in range(inicio, fin + 1)
            if spec["titulo"] in (pdf.pages[n - 1].extract_text() or "").upper()]


# ----------------------------------------------------------------------------- 2. geometría
def lineas_visuales(palabras: list[dict]) -> list[tuple[float, list[dict]]]:
    out: list[list] = []
    for w in sorted(palabras, key=lambda w: (w["top"], w["x0"])):
        if out and abs(out[-1][0] - w["top"]) <= TOL_LINEA:
            out[-1][1].append(w)
        else:
            out.append([w["top"], [w]])
    return [(top, sorted(ws, key=lambda w: w["x0"])) for top, ws in out]


def inicio_datos(palabras: list[dict]) -> float | None:
    """Coordenada y donde empiezan los datos (bajo la banda de cabecera «Cod.»)."""
    cab = [w for w in palabras if RE_CABECERA.match(w["text"])]
    if not cab:
        return None
    y = cab[0]["top"]
    return max(w["bottom"] for w in palabras if BANDA_CABECERA[0] < w["top"] - y < BANDA_CABECERA[1]) + 1


def calibrar_anclas(pdf, paginas: list[int], n_columnas: int) -> list[float]:
    """Bordes derechos de las n columnas numéricas, con TODAS las páginas de la tabla.

    Calibrar por página falla cuando una página solo contiene la fila TOTAL
    (2.10 de 2016 y 2018: «TOTAL CAPITULOS DEL 1 AL 8» aporta dos cifras espurias).
    """
    bordes = []
    for n in paginas:
        palabras = pdf.pages[n - 1].extract_words()
        y0 = inicio_datos(palabras)
        if y0 is None:
            continue
        bordes += [w["x1"] for w in palabras
                   if w["top"] > y0 and w["x0"] > X_MIN_NUMEROS and es_numero(w["text"])]
    grupos: list[list[float]] = []
    for x in sorted(bordes):
        if grupos and x - grupos[-1][-1] <= TOL_CLUSTER:
            grupos[-1].append(x)
        else:
            grupos.append([x])
    if len(grupos) < n_columnas:
        raise ValueError(f"Solo {len(grupos)} columnas numéricas detectadas; se esperaban {n_columnas}")
    mayores = sorted(sorted(grupos, key=len, reverse=True)[:n_columnas], key=lambda g: g[0])
    return [max(g) for g in mayores]


# ----------------------------------------------------------------------------- 3. filas
@dataclass
class Fila:
    pagina: int
    top: float
    nivel: str                      # detalle | grupo | total
    codigo: str | None
    denominacion: str
    valores: dict                   # columna -> número (None = celda vacía)
    asteriscos: set = field(default_factory=set)
    padre: str | None = None        # sección (2.16) o tipo de ente (3.1)
    ente: str | None = None         # 3.2
    orden: int = 0


def _ente_de_cabecera(palabras: list[dict]) -> str | None:
    """En 3.2 el ente es la línea entre el título y «(IMPORTE EN EUROS)»."""
    titulo = [w for w in palabras if w["text"] == "RESUMEN"]
    importe = [w for w in palabras if w["text"] == "(IMPORTE"]
    if not titulo or not importe:
        return None
    ws = [w for w in palabras if titulo[0]["bottom"] + 1 < w["top"] < importe[0]["top"] - 1]
    return " ".join(w["text"] for w in sorted(ws, key=lambda w: (round(w["top"]), w["x0"]))) or None


def _limpiar_denominacion(texto: str) -> str:
    texto = re.sub(r"(\w)- +(\w)", r"\1\2", texto)   # guion de corte: «ALI- MENTARIA»
    return re.sub(r"\s+", " ", texto).strip()


def parsear_tabla(pdf, indice: dict, spec: dict) -> tuple[list[Fila], dict]:
    """Filas de una tabla y contadores de degradación."""
    paginas = paginas_tabla(pdf, indice, spec)
    cont = {"paginas": len(paginas), "lineas": 0, "filas": 0, "huerfanas_unidas": 0,
            "huerfanas_descartadas": 0, "tokens_fuera_ancla": 0, "filas_incompletas": 0}
    if not paginas:
        return [], cont
    columnas = spec["columnas"]
    anclas = calibrar_anclas(pdf, paginas, len(columnas))
    cont["anclas"] = [round(a, 1) for a in anclas]
    re_codigo = re.compile(spec["codigo"])
    re_grupo = re.compile(spec["codigo_grupo"]) if spec.get("codigo_grupo") else None
    re_total = re.compile(spec.get("total", r"^TOTAL"), re.I)
    x_num_min = min(anclas) - 60  # la columna más estrecha no supera ~60 pt

    filas: list[Fila] = []
    ente = padre = None
    for n in paginas:
        pg = pdf.pages[n - 1]
        palabras = pg.extract_words()
        y0 = inicio_datos(palabras)
        if y0 is None:
            continue
        if spec.get("ente_en_cabecera"):
            ente = _ente_de_cabecera(palabras) or ente
        datos = [w for w in palabras if y0 < w["top"] < pg.height - MARGEN_PIE]
        filas_pagina, huerfanas = [], []
        for top, ws in lineas_visuales(datos):
            cont["lineas"] += 1
            cifras, texto = [], []
            for w in ws:
                if w["text"] == "%":                    # «100 %»: el símbolo se descarta
                    continue
                if w["x1"] >= x_num_min and es_numero(w["text"]):
                    j = min(range(len(anclas)), key=lambda k: abs(anclas[k] - w["x1"]))
                    if abs(anclas[j] - w["x1"]) <= TOL_ANCLA:
                        cifras.append((columnas[j], w["text"]))
                        continue
                    if w["x0"] > X_MIN_NUMEROS:
                        cont["tokens_fuera_ancla"] += 1
                texto.append(w)
            if not cifras:
                huerfanas.append((top, " ".join(w["text"] for w in texto)))
                continue
            valores, asteriscos = {}, set()
            for col, tok in cifras:
                valores[col], ast = a_numero(tok)
                if ast:
                    asteriscos.add(col)
            palabras_txt = [w["text"] for w in texto]
            primera_x = texto[0]["x0"] if texto else 999
            codigo, nivel = None, "grupo"
            if palabras_txt and primera_x < X_MAX_CODIGO and re_codigo.match(palabras_txt[0]):
                codigo, palabras_txt, nivel = palabras_txt[0], palabras_txt[1:], "detalle"
            elif palabras_txt and re_grupo and primera_x < X_MAX_CODIGO and re_grupo.match(palabras_txt[0]):
                codigo, palabras_txt = palabras_txt[0], palabras_txt[1:]
            elif re_total.match(" ".join(palabras_txt)):
                nivel = "total"
            fila = Fila(n, top, nivel, codigo, " ".join(palabras_txt), valores, asteriscos, ente=ente)
            if len(valores) < len(columnas):
                cont["filas_incompletas"] += 1
            filas_pagina.append(fila)
        # denominaciones partidas: la línea sin cifras se une a la fila más cercana en vertical
        for top, txt in huerfanas:
            if not filas_pagina or re.fullmatch(r"\d+", txt):   # número de página
                cont["huerfanas_descartadas"] += bool(filas_pagina)
                continue
            fila = min(filas_pagina, key=lambda f: abs(f.top - top))
            if abs(fila.top - top) <= DIST_HUERFANA:
                fila.denominacion = f"{txt} {fila.denominacion}" if top < fila.top else f"{fila.denominacion} {txt}"
                cont["huerfanas_unidas"] += 1
            else:
                cont["huerfanas_descartadas"] += 1
        filas += filas_pagina

    # jerarquía implícita y orden
    for k, f in enumerate(filas):
        f.denominacion = _limpiar_denominacion(f.denominacion)
        f.orden = k
        if f.nivel == "grupo":
            padre = f.codigo or f.denominacion
        elif f.nivel == "detalle":
            f.padre = padre
    cont["filas"] = len(filas)
    return filas, cont
