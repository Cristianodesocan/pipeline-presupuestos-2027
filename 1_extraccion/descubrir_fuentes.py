"""Rastrea las páginas del portal de Presupuestos y PROPONE entradas para config/fuentes.yml.

    python 1_extraccion/descubrir_fuentes.py               # todos los portales del catálogo
    python 1_extraccion/descubrir_fuentes.py --anio 2027

No descarga PDF ni modifica el catálogo: escribe config/fuentes_propuestas.yml con lo que falta o cambia.
Cada enlace «Resúmenes» se asocia a la fase por el encabezado que lo precede
(«Proyecto de Ley de Presupuestos…» → proyecto; «Ley de Presupuestos…» → ley).
Si el enlace del portal está roto (2024 enlaza un .html que da 404) se prueba la variante .pdf.
Código de salida 2 si hay propuestas nuevas (útil para avisar desde el maestro o un workflow).
"""
import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import yaml
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _comun.red import TIMEOUT, pausar, sesion  # noqa: E402
from _comun.rutas import CONFIG, ahora, cargar_fuentes, log_evento, url_documento  # noqa: E402

RE_ENLACE_TOMO3 = re.compile(r"Res[uú]menes", re.I)
FASES = [(re.compile(r"^\s*Proyecto de Ley de Presupuestos", re.I), "proyecto"),
         (re.compile(r"^\s*Ley de Presupuestos", re.I), "ley")]


def fase_de(encabezado: str) -> str | None:
    for patron, fase in FASES:
        if patron.match(encabezado):
            return fase
    return None


def enlaces_tomo3(html: str, url_pagina: str) -> list[dict]:
    """[{fase, url, texto, seccion}] de una página de portal."""
    sopa = BeautifulSoup(html, "html.parser")
    out = []
    for a in sopa.find_all("a", href=True):
        texto = a.get_text(" ", strip=True)
        if not RE_ENLACE_TOMO3.search(texto):  # «Resumen Gráfico» no casa: es singular
            continue
        h = a.find_previous(["h2", "h3", "h4"])
        seccion = h.get_text(" ", strip=True) if h else ""
        fase = fase_de(seccion)
        if fase:
            out.append({"fase": fase, "url": urljoin(url_pagina, a["href"]), "texto": texto, "seccion": seccion})
    return out


def es_pdf_accesible(s, url: str) -> bool:
    pausar()
    try:
        r = s.head(url, timeout=TIMEOUT, allow_redirects=True)
    except Exception:
        return False
    return r.status_code == 200 and "pdf" in r.headers.get("Content-Type", "").lower()


def candidatas(url: str, base_url: str) -> list[str]:
    """La URL del enlace y sus reparaciones conocidas, por orden de preferencia.

    2024: el portal enlaza «../galeria/Presupuestos/2024/ley/TOMO-3-Resumenes.html», que resuelve
    fuera de /cmsgob1/export/sites/ y además es .html; el PDF real está en base_url + ….pdf
    """
    a_pdf = lambda u: re.sub(r"\.[A-Za-z]+$", ".pdf", u)  # noqa: E731
    out = [url, a_pdf(url)]
    if "/galeria/Presupuestos/" in url:
        relativa = url.split("/galeria/Presupuestos/", 1)[1]
        out += [base_url + relativa, base_url + a_pdf(relativa)]
    return list(dict.fromkeys(out))


def resolver(s, url: str, base_url: str) -> str | None:
    for candidata in candidatas(url, base_url):
        if candidata.lower().endswith(".pdf") and es_pdf_accesible(s, candidata):
            return candidata
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--anio", type=int)
    args = ap.parse_args()

    fuentes = cargar_fuentes()
    catalogo = {(d["anio"], d["fase"]): url_documento(d, fuentes) for d in fuentes["documentos"]}
    portales = {int(k): v for k, v in fuentes["portales"].items() if args.anio in (None, int(k))}
    s = sesion()
    propuestas, avisos = [], []
    for anio, url_pagina in sorted(portales.items()):
        pausar()
        r = s.get(url_pagina, timeout=TIMEOUT)
        if r.status_code != 200:
            avisos.append(f"{anio}: portal HTTP {r.status_code}")
            continue
        encontrados = enlaces_tomo3(r.text, url_pagina)
        print(f"{anio}: {len(encontrados)} enlace(s) «Resúmenes»")
        for e in encontrados:
            url = resolver(s, e["url"], fuentes["base_url"])
            if url is None:
                avisos.append(f"{anio} {e['fase']}: enlace no accesible {e['url']}")
                continue
            if url != e["url"]:
                avisos.append(f"{anio} {e['fase']}: enlace roto {e['url']} → se usa {url}")
            actual = catalogo.get((anio, e["fase"]))
            if actual == url:
                continue
            propuestas.append({
                "anio": anio, "fase": e["fase"], "tomo": 3,
                "ruta": url.replace(fuentes["base_url"], "") if url.startswith(fuentes["base_url"]) else None,
                "url": None if url.startswith(fuentes["base_url"]) else url,
                "sha256": None, "verificado": None,
                "nota": ("CAMBIO de URL; antes: " + actual) if actual else "NUEVO",
                "detectado_en": ahora(), "seccion_portal": e["seccion"],
            })

    for a in avisos:
        print("AVISO:", a)
    salida = CONFIG / "fuentes_propuestas.yml"
    if propuestas:
        with open(salida, "w", encoding="utf-8") as f:
            f.write("# Propuestas de descubrir_fuentes.py. Revisa y copia a fuentes.yml (documentos:)\n")
            yaml.safe_dump({"documentos": propuestas}, f, allow_unicode=True, sort_keys=False)
        print(f"{len(propuestas)} propuesta(s) en {salida.relative_to(CONFIG.parent)}")
    else:
        print("Sin novedades respecto al catálogo.")
    log_evento("descubrir_fuentes", propuestas=len(propuestas), avisos=avisos)
    return 2 if propuestas else 0


if __name__ == "__main__":
    sys.exit(main())
