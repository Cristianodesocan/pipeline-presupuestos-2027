"""Fase, año y tomo leídos de la portada (página 1).

La portada es la única prueba documental de la fase:
    «• RESÚMENES / PROYECTO DE LEY DE PRESUPUESTOS: TOMO 3 / 2026»  -> proyecto
    «• RESÚMENES / LEY DE PRESUPUESTOS: TOMO 3 / 2026»              -> ley
"""
import re


def leer_portada(pdf) -> dict:
    texto = (pdf.pages[0].extract_text() or "").upper()
    if "PROYECTO DE LEY" in texto:
        fase = "proyecto"
    elif "LEY DE PRESUPUESTOS" in texto:
        fase = "ley"
    else:
        fase = None
    anio = re.search(r"\b(20\d{2})\b", texto)
    tomo = re.search(r"TOMO\s*(\d+)", texto)
    return {
        "fase": fase,
        "anio": int(anio.group(1)) if anio else None,
        "tomo": int(tomo.group(1)) if tomo else None,
        "texto": " / ".join(l.strip() for l in texto.split("\n") if l.strip())[:200],
    }
