"""Lector INDEPENDIENTE de las tablas resumen del Tomo 3 (no usa el código del pipeline, 1_extraccion/_comun).

Sirve para auditar los datos de la web contra el documento oficial: si el extractor del pipeline tuviera un error,
este lector, escrito de otra manera, no lo repetiría.

Método: cada página se identifica por su título («RESUMEN DE GASTOS POR SECCIONES»…). Las palabras se agrupan en
líneas por su posición vertical; las cifras están alineadas a la derecha, así que su borde derecho (x1) identifica la
columna. Las columnas se obtienen agrupando los x1 de todas las cifras de la tabla (en todas sus páginas). Una fila
con código se reconoce por el patrón de código de la tabla; las filas «TOTAL» se guardan aparte.
"""
import re
from collections import defaultdict
from pathlib import Path

import pdfplumber

IMPORTE = re.compile(r"^\d{1,3}(?:\.\d{3})*$")
PORCENTAJE = re.compile(r"^\d{1,3}(?:\.\d{3})*,\d{1,2}-?$|^\*$")
TITULOS = {
    "secciones": ("RESUMEN DE GASTOS POR SECCIONES", r"^\d{2}$", 5),
    "funciones": ("RESUMEN DE GASTOS POR FUNCIONES", r"^\d{2}$", 5),
    "subfunciones": ("RESUMEN DE GASTOS POR SUBFUNCIONES", r"^\d{3}$", 5),
    "programas": ("RESUMEN DE GASTOS POR PROGRAMAS", r"^\d{3}[A-Z]$", 5),
    "secciones_cap": ("RESUMEN DE GASTOS POR SECCIONES Y CAPÍTULOS", r"^\d{2}$", 9),
    "funciones_cap": ("RESUMEN DE GASTOS POR FUNCIONES Y CAPÍTULOS", r"^\d{2}$", 9),
    "entes": ("RESUMEN DE GASTOS COMPARATIVO POR ENTES", r"^[A-Z][A-Z0-9]{1,5}$", 5),
}
CAPS = [1, 2, 3, 4, 6, 7, 8, 9]


def numero(t: str):
    """«4.542.898.685» → 4542898685 ; «38,15» → 38.15 ; «0,71-» → -0.71 ; «*» → None."""
    if t == "*":
        return None
    neg = t.endswith("-")
    t = t.rstrip("-")
    v = float(t.replace(".", "").replace(",", ".")) if "," in t else int(t.replace(".", ""))
    return -v if neg else v


def _lineas(pagina, tolerancia: float = 3.0):
    """Agrupa las palabras en líneas por proximidad vertical (centro de la palabra), no por franjas fijas:
    las filas en negrita o con el nombre partido en dos líneas tienen la cifra algo desplazada."""
    palabras = sorted(pagina.extract_words(keep_blank_chars=False, use_text_flow=False, x_tolerance=1.5),
                      key=lambda w: (w["top"] + w["bottom"]) / 2)
    lineas, centros = [], []
    for w in palabras:
        c = (w["top"] + w["bottom"]) / 2
        if centros and c - centros[-1] <= tolerancia:
            lineas[-1].append(w)
            centros[-1] = sum((x["top"] + x["bottom"]) / 2 for x in lineas[-1]) / len(lineas[-1])
        else:
            lineas.append([w])
            centros.append(c)
    return [sorted(ws, key=lambda w: w["x0"]) for ws in lineas]


def _titulo(pagina) -> str:
    for linea in (pagina.extract_text() or "").split("\n")[:6]:
        if linea.startswith("RESUMEN DE "):
            return linea.strip()
    return ""


def paginas_por_titulo(pdf) -> dict[str, list]:
    out = defaultdict(list)
    for p in pdf.pages:
        out[_titulo(p)].append(p)
    return out


def _columnas(x1s: list[float], n: int, tolerancia: float = 6) -> list[float]:
    """Agrupa los bordes derechos de las cifras y devuelve los n grupos más poblados, de izquierda a derecha."""
    grupos = []
    for x in sorted(x1s):
        if grupos and x - grupos[-1][-1] <= tolerancia:
            grupos[-1].append(x)
        else:
            grupos.append([x])
    mejores = sorted(grupos, key=len, reverse=True)[:n]
    return sorted(sum(g) / len(g) for g in mejores)


def leer_tabla(pdf, clave: str) -> dict:
    """{'filas': {codigo: [valores por columna]}, 'total': [valores], 'columnas': n}."""
    titulo, patron, n = TITULOS[clave]
    patron = re.compile(patron)
    paginas = paginas_por_titulo(pdf).get(titulo, [])
    if not paginas:
        return {"filas": {}, "total": None, "columnas": n}
    filas_num = []
    for p in paginas:
        for ws in _lineas(p):
            cifras = [w for w in ws if IMPORTE.match(w["text"]) or PORCENTAJE.match(w["text"])]
            # las cifras son la cola de la línea: lo que hay antes es código y nombre
            cola = []
            for w in reversed(ws[1:]):        # el primer elemento es siempre código o etiqueta («08» parece una cifra)
                if w in cifras:
                    cola.append(w)
                else:
                    break
            cola.reverse()
            if not cola:
                continue
            cabeza = [w["text"] for w in ws[: len(ws) - len(cola)]]
            filas_num.append((cabeza, cola))
    x1s = [w["x1"] for _, cola in filas_num for w in cola]
    cols = _columnas(x1s, n)
    filas, total = {}, None
    for cabeza, cola in filas_num:
        valores = [None] * len(cols)
        for w in cola:
            j = min(range(len(cols)), key=lambda k: abs(cols[k] - w["x1"]))
            if abs(cols[j] - w["x1"]) <= 8:
                valores[j] = numero(w["text"])
        if cabeza and cabeza[0].upper() == "TOTAL":
            total = valores
        elif cabeza and patron.match(cabeza[0]):
            filas[cabeza[0]] = valores
    return {"filas": filas, "total": total, "columnas": len(cols)}


def leer_documento(ruta: Path) -> dict:
    with pdfplumber.open(str(ruta)) as pdf:
        return {k: leer_tabla(pdf, k) for k in TITULOS}
