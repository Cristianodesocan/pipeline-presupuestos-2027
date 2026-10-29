"""Extrae las tablas de config/tablas_tomo3.yml de cada Tomo 3 descargado a staging tidy.

    python 1_extraccion/extraer_tomo3.py                       # todos los documentos vigentes
    python 1_extraccion/extraer_tomo3.py --anio 2027 --fase proyecto
    python 1_extraccion/extraer_tomo3.py --forzar              # ignora la caché

Salida: 1_extraccion/staging/stg_tomo3/<doc_id>.parquet, una observación por celda
(diseno_extraccion_tomo3.md §4). Caché: no se vuelve a parsear un doc_id cuyo
(sha256, versión del extractor, hash de tablas_tomo3.yml) ya está en staging.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _comun import manifest  # noqa: E402
from _comun.portada import leer_portada  # noqa: E402
from _comun.rutas import RAIZ, STAGING, VERSION_EXTRACTOR, ahora, cargar_tablas, doc_id, log_evento  # noqa: E402
from _comun.staging import guardar_indice_staging, leer_indice_staging  # noqa: E402
from _comun.tomo3 import leer_indice, parsear_tabla  # noqa: E402

COLUMNAS = ["doc_id", "anio_presupuesto", "fase", "tomo", "tabla", "indice", "pagina", "orden", "nivel",
            "codigo", "codigo_padre", "ente", "denominacion_raw", "columna", "anio_importe",
            "version_importe", "capitulo", "valor", "unidad", "perimetro", "marca_asterisco",
            "sha256", "version_extractor", "extraido_en"]


def semantica(columna: str, anio: int) -> dict:
    """Desdoble bianual y capítulo de cada columna de origen."""
    if columna in ("ajustado_prev", "pct_ajustado_prev"):
        return {"anio_importe": anio - 1, "version_importe": "ajustado", "capitulo": "TOTAL"}
    if columna in ("inicial", "pct_inicial"):
        return {"anio_importe": anio, "version_importe": "inicial", "capitulo": "TOTAL"}
    if columna == "var_pct":
        return {"anio_importe": anio, "version_importe": None, "capitulo": "TOTAL"}
    if columna.startswith("cap_"):
        return {"anio_importe": anio, "version_importe": "inicial", "capitulo": columna[4:]}
    if columna == "total":
        return {"anio_importe": anio, "version_importe": "inicial", "capitulo": "TOTAL"}
    raise ValueError(f"Columna desconocida: {columna}")


def extraer_documento(reg: dict, cfg: dict) -> tuple[pd.DataFrame, dict]:
    anio, fase, tomo, sha = reg["anio"], reg["fase"], reg["tomo"], reg["sha256"]
    did = doc_id(anio, fase, tomo, sha)
    filas_tidy, contadores = [], {}
    momento = ahora()
    with pdfplumber.open(RAIZ / reg["fichero"]) as pdf:
        portada = leer_portada(pdf)
        if (portada["fase"], portada["anio"]) != (fase, anio):
            raise ValueError(f"{did}: la portada dice {portada['fase']} {portada['anio']}")
        indice = leer_indice(pdf)
        for id_tabla, spec in cfg["tablas"].items():
            filas, cont = parsear_tabla(pdf, indice, spec)
            contadores[id_tabla] = cont
            for f in filas:
                for col in spec["columnas"]:
                    filas_tidy.append({
                        "doc_id": did, "anio_presupuesto": anio, "fase": fase, "tomo": tomo,
                        "tabla": id_tabla, "indice": spec["indice"], "pagina": f.pagina, "orden": f.orden,
                        "nivel": f.nivel, "codigo": f.codigo, "codigo_padre": f.padre, "ente": f.ente,
                        "denominacion_raw": f.denominacion, "columna": col, **semantica(col, anio),
                        "valor": f.valores.get(col), "unidad": "pct" if col.startswith(("pct_", "var_")) else "eur",
                        "perimetro": spec["perimetro"], "marca_asterisco": col in f.asteriscos,
                        "sha256": sha, "version_extractor": VERSION_EXTRACTOR, "extraido_en": momento,
                    })
    df = pd.DataFrame(filas_tidy, columns=COLUMNAS)
    df["valor"] = df["valor"].astype("float64")
    for c in ("anio_presupuesto", "tomo", "pagina", "orden", "anio_importe"):
        df[c] = df[c].astype("int64")
    return df, contadores


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--anio", type=int)
    ap.add_argument("--fase", choices=["proyecto", "ley"])
    ap.add_argument("--forzar", action="store_true")
    args = ap.parse_args()

    cfg, hash_spec = cargar_tablas()
    docs = [d for d in manifest.documentos_vigentes()
            if (args.anio is None or d["anio"] == args.anio) and (args.fase is None or d["fase"] == args.fase)]
    if not docs:
        print("No hay documentos descargados que coincidan; ejecuta antes descargar_tomos.py.")
        return 1
    indice_stg = leer_indice_staging()
    STAGING.mkdir(parents=True, exist_ok=True)
    fallos = 0
    for reg in docs:
        did = doc_id(reg["anio"], reg["fase"], reg["tomo"], reg["sha256"])
        firma = {"sha256": reg["sha256"], "version_extractor": VERSION_EXTRACTOR, "hash_tablas": hash_spec}
        previo = indice_stg.get(did, {})
        if not args.forzar and (STAGING / f"{did}.parquet").exists() and \
                all(previo.get(k) == v for k, v in firma.items()):
            print(f"{did}: en caché")
            continue
        try:
            df, contadores = extraer_documento(reg, cfg)
        except Exception as e:
            fallos += 1
            print(f"{did}: ERROR {type(e).__name__}: {e}")
            log_evento("extraer_tomo3", doc_id=did, error=f"{type(e).__name__}: {e}")
            continue
        df.to_parquet(STAGING / f"{did}.parquet", index=False)
        indice_stg[did] = {**firma, "anio": reg["anio"], "fase": reg["fase"], "extraido_en": ahora(),
                           "n_celdas": len(df), "contadores": contadores}
        guardar_indice_staging(indice_stg)
        detalle = {t: c["filas"] for t, c in contadores.items()}
        print(f"{did}: {len(df)} celdas · filas por tabla {detalle}")
        log_evento("extraer_tomo3", doc_id=did, n_celdas=len(df), contadores=contadores)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
