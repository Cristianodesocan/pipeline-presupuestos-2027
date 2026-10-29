"""Utilidades compartidas por los scripts de 2_transformacion."""
import re
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd
import yaml

TRANS = Path(__file__).resolve().parent
sys.path.insert(0, str(TRANS.parent / "1_extraccion"))

from _comun.rutas import CONFIG, LOGS, RAIZ, ahora, log_evento  # noqa: E402,F401

STG = TRANS / "staging"
XWALKS = TRANS / "crosswalks"
EXTERNOS = TRANS / "externos"

# dimensión analítica ← tabla del Tomo 3
DIMENSIONES = {
    "secciones": "seccion",
    "servicios": "servicio",
    "funciones": "funcion",
    "subfunciones": "subfuncion",
    "programas": "programa",
    "entes": "ente",
    "secciones_cap": "seccion",
    "subfunciones_cap": "subfuncion",
    "secc_prog_cap": "seccion_programa",
    "entes_prog_cap": "ente_programa",
}
DIMENSIONES_XWALK = ["seccion", "funcion", "subfuncion", "programa", "ente"]  # orden de ejecución
PREFIJO_ID = {"seccion": "S", "funcion": "F", "subfuncion": "SF", "programa": "P", "ente": "E"}


@lru_cache
def cfg() -> dict:
    return yaml.safe_load((CONFIG / "transformacion.yml").read_text(encoding="utf-8"))


@lru_cache
def _abreviaturas() -> dict:
    return yaml.safe_load((CONFIG / "abreviaturas.yml").read_text(encoding="utf-8")) or {}


def normalizar_nombre(texto: str | None) -> str:
    """Forma comparable de una denominación: minúsculas, sin diacríticos ni puntuación y
    con las abreviaturas de config/abreviaturas.yml expandidas. Solo para emparejar."""
    if not texto:
        return ""
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9ñ]+", " ", t)
    abrev = _abreviaturas()
    return " ".join(abrev.get(p, p) for p in t.split())


def leer(nombre: str) -> pd.DataFrame:
    ruta = STG / f"{nombre}.parquet"
    if not ruta.exists():
        raise FileNotFoundError(f"Falta {ruta.relative_to(RAIZ)}: ejecuta antes el paso que lo genera")
    return pd.read_parquet(ruta)


def guardar(df: pd.DataFrame, nombre: str) -> Path:
    STG.mkdir(parents=True, exist_ok=True)
    ruta = STG / f"{nombre}.parquet"
    df.to_parquet(ruta, index=False)
    return ruta


def anios_oficiales(fact: pd.DataFrame) -> list[int]:
    return sorted(fact.loc[fact.serie_oficial, "anio_presupuesto"].unique().tolist())
