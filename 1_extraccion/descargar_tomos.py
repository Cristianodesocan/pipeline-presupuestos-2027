"""Descarga los tomos del catálogo (config/fuentes.yml) a 1_extraccion/raw/ y los anota en logs/manifest.jsonl.

    python 1_extraccion/descargar_tomos.py                 # todo el catálogo
    python 1_extraccion/descargar_tomos.py --anio 2027 --fase proyecto
    python 1_extraccion/descargar_tomos.py --forzar        # ignora ETag / Last-Modified

- Descarga condicional (If-None-Match / If-Modified-Since): un 304 no descarga nada.
- Cada versión se guarda inmutable como raw/<anio>/<fase>/tomo<n>_<sha8>.pdf. Si la web
  republica un fichero, se guarda la nueva versión (evento «republicado») y no se sobrescribe la anterior.
- Un fichero que no pasa la validación (§2.4: firma, tamaño, portada, índice) se rechaza y no se guarda.
Código de salida 1 si algún documento se rechaza o no se puede descargar.
"""
import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _comun import manifest  # noqa: E402
from _comun.red import TIMEOUT, pausar, sesion  # noqa: E402
from _comun.rutas import RAIZ, RAW, ahora, cargar_fuentes, cargar_tablas, log_evento, url_documento  # noqa: E402
from _comun.validacion_pdf import validar_pdf  # noqa: E402


def descargar(doc: dict, url: str, s, cfg_tablas: dict, forzar: bool) -> str:
    anio, fase, tomo = doc["anio"], doc["fase"], doc.get("tomo", 3)
    previo = manifest.vigente(anio, fase, tomo)
    cabeceras = {}
    if previo and not forzar:
        if previo.get("etag"):
            cabeceras["If-None-Match"] = previo["etag"]
        if previo.get("last_modified"):
            cabeceras["If-Modified-Since"] = previo["last_modified"]
    base = {"anio": anio, "fase": fase, "tomo": tomo, "url": url, "descargado_en": ahora()}

    pausar()
    try:
        r = s.get(url, headers=cabeceras, timeout=TIMEOUT, stream=True)
    except Exception as e:
        manifest.anotar({**base, "evento": "error_red", "motivo": f"{type(e).__name__}: {e}"})
        return "error"
    if r.status_code == 304:
        log_evento("descarga", **base, evento="sin_cambios_304")
        return "sin_cambios"
    tipo = r.headers.get("Content-Type", "")
    if r.status_code != 200 or "pdf" not in tipo.lower():
        manifest.anotar({**base, "evento": "rechazado", "http_status": r.status_code,
                         "motivo": f"HTTP {r.status_code}, Content-Type {tipo!r}"})
        return "rechazado"

    destino_dir = RAW / str(anio) / fase
    destino_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destino_dir, suffix=".part", delete=False) as tmp:
        for bloque in r.iter_content(1 << 16):
            tmp.write(bloque)
    tmp_path = Path(tmp.name)
    sha = manifest.sha256_fichero(tmp_path)
    registro = {**base, "http_status": 200, "etag": r.headers.get("ETag"),
                "last_modified": r.headers.get("Last-Modified"), "sha256": sha,
                "coincide_catalogo": (sha == doc.get("sha256")) if doc.get("sha256") else None}

    if previo and previo["sha256"] == sha:
        tmp_path.unlink()
        log_evento("descarga", **base, evento="sin_cambios_sha")
        return "sin_cambios"

    errores, detalle = validar_pdf(tmp_path, anio, fase, tomo, cfg_tablas)
    if errores:
        tmp_path.unlink()
        manifest.anotar({**registro, **detalle, "evento": "rechazado", "motivo": errores})
        return "rechazado"

    final = destino_dir / f"tomo{tomo}_{sha[:8]}.pdf"
    tmp_path.replace(final)
    evento = "republicado" if previo else "nuevo"
    manifest.anotar({**registro, **detalle, "evento": evento, "fichero": str(final.relative_to(RAIZ))})
    return evento


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--anio", type=int)
    ap.add_argument("--fase", choices=["proyecto", "ley"])
    ap.add_argument("--forzar", action="store_true")
    args = ap.parse_args()

    fuentes = cargar_fuentes()
    cfg_tablas, _ = cargar_tablas()
    docs = [d for d in fuentes["documentos"]
            if (args.anio is None or d["anio"] == args.anio) and (args.fase is None or d["fase"] == args.fase)]
    if not docs:
        print("Ningún documento del catálogo coincide con el filtro.")
        return 1
    s = sesion()
    resumen = {}
    for d in docs:
        res = descargar(d, url_documento(d, fuentes), s, cfg_tablas, args.forzar)
        resumen.setdefault(res, []).append(f"{d['anio']}_{d['fase']}")
        print(f"{d['anio']} {d['fase']:9s} {res}")
    for res, lista in resumen.items():
        print(f"  {res}: {len(lista)}")
    if "republicado" in resumen:
        print("AVISO: hay documentos republicados; revisa sha256 en config/fuentes.yml.")
    for d in docs:
        v = manifest.vigente(d["anio"], d["fase"], d.get("tomo", 3))
        if v and d.get("sha256") and v["sha256"] != d["sha256"]:
            print(f"AVISO: {d['anio']} {d['fase']}: la versión vigente ({v['sha256'][:8]}) no es la del catálogo ({d['sha256'][:8]}).")
    log_evento("descargar_tomos", resumen={k: len(v) for k, v in resumen.items()})
    return 1 if {"rechazado", "error"} & set(resumen) else 0


if __name__ == "__main__":
    sys.exit(main())
