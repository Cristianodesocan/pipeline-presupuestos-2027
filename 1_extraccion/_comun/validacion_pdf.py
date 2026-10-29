"""Comprobaciones de un PDF descargado antes de aceptarlo (diseno_extraccion_tomo3.md §2.4)."""
from pathlib import Path

import pdfplumber

from .portada import leer_portada
from .tomo3 import leer_indice

TAMANO_MINIMO = 300_000


def validar_pdf(ruta: Path, anio: int, fase: str, tomo: int, cfg_tablas: dict) -> tuple[list[str], dict]:
    """Devuelve (errores, detalle). Sin errores = documento aceptable."""
    errores, detalle = [], {}
    with open(ruta, "rb") as f:
        if not f.read(5).startswith(b"%PDF-"):
            return ["firma: no empieza por %PDF-"], detalle
    detalle["bytes"] = ruta.stat().st_size
    if detalle["bytes"] < TAMANO_MINIMO:
        errores.append(f"tamaño: {detalle['bytes']} bytes < {TAMANO_MINIMO}")
    try:
        with pdfplumber.open(ruta) as pdf:
            detalle["n_paginas"] = len(pdf.pages)
            portada = leer_portada(pdf)
            detalle.update(portada_fase=portada["fase"], portada_anio=portada["anio"],
                           portada_tomo=portada["tomo"], portada_texto=portada["texto"])
            indice = leer_indice(pdf)
            detalle["n_entradas_indice"] = len(indice)
    except Exception as e:  # PDF corrupto o sin índice
        return errores + [f"lectura: {type(e).__name__}: {e}"], detalle
    if portada["fase"] != fase:
        errores.append(f"portada: fase {portada['fase']!r} ≠ catálogo {fase!r}")
    if portada["anio"] != anio:
        errores.append(f"portada: año {portada['anio']} ≠ catálogo {anio}")
    if portada["tomo"] != tomo:
        errores.append(f"portada: tomo {portada['tomo']} ≠ catálogo {tomo}")
    esperadas = cfg_tablas["entradas_indice_esperadas"]
    if len(indice) != esperadas:
        errores.append(f"índice: {len(indice)} entradas ≠ {esperadas} (¿cambio de maqueta?)")
    faltan = [s for s in cfg_tablas["secciones_obligatorias"] if s not in indice]
    if faltan:
        errores.append(f"índice: faltan las secciones {faltan}")
    return errores, detalle
