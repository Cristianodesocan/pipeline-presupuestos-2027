"""Lectura del staging tidy (1_extraccion/staging/stg_tomo3/<doc_id>.parquet).

Los stg_secciones, stg_programas… del diseño general son vistas: leer_staging(tabla="programas").
"""
import json

import pandas as pd

from . import manifest
from .rutas import STAGING, doc_id

INDICE = STAGING / "_indice.json"


def leer_indice_staging() -> dict:
    return json.loads(INDICE.read_text(encoding="utf-8")) if INDICE.exists() else {}


def guardar_indice_staging(indice: dict) -> None:
    STAGING.mkdir(parents=True, exist_ok=True)
    INDICE.write_text(json.dumps(indice, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


def ids_vigentes() -> list[str]:
    return [doc_id(d["anio"], d["fase"], d["tomo"], d["sha256"]) for d in manifest.documentos_vigentes()]


def leer_staging(tabla: str | None = None, fase: str | None = None, solo_vigentes: bool = True) -> pd.DataFrame:
    ids = ids_vigentes() if solo_vigentes else [p.stem for p in STAGING.glob("*.parquet")]
    partes = [pd.read_parquet(STAGING / f"{i}.parquet") for i in ids if (STAGING / f"{i}.parquet").exists()]
    if not partes:
        return pd.DataFrame()
    df = pd.concat(partes, ignore_index=True)
    if tabla:
        df = df[df["tabla"] == tabla]
    if fase:
        df = df[df["fase"] == fase]
    return df.reset_index(drop=True)
