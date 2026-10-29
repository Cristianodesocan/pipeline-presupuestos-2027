"""Rutas del proyecto, carga de configuración y registro de eventos."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / "config"
EXTRACCION = RAIZ / "1_extraccion"
RAW = EXTRACCION / "raw"
STAGING = EXTRACCION / "staging" / "stg_tomo3"
LOGS = RAIZ / "logs"

VERSION_EXTRACTOR = "1.0.0"


def ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def cargar_fuentes() -> dict:
    with open(CONFIG / "fuentes.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def url_documento(doc: dict, fuentes: dict) -> str:
    return doc.get("url") or fuentes["base_url"] + doc["ruta"]


def cargar_tablas() -> tuple[dict, str]:
    """Devuelve (especificaciones resueltas con su plantilla, hash del YAML)."""
    texto = (CONFIG / "tablas_tomo3.yml").read_bytes()
    cfg = yaml.safe_load(texto)
    specs = {}
    for id_tabla, t in cfg["tablas"].items():
        spec = dict(cfg["plantillas"][t["plantilla"]]) if "plantilla" in t else {}
        spec.update(t)
        spec["id"] = id_tabla
        specs[id_tabla] = spec
    cfg["tablas"] = specs
    return cfg, hashlib.sha256(texto).hexdigest()[:12]


def doc_id(anio: int, fase: str, tomo: int, sha256: str) -> str:
    return f"{anio}_{fase}_t{tomo}_{sha256[:8]}"


def log_evento(paso: str, **datos) -> None:
    """Una línea JSON por evento en logs/pipeline.jsonl."""
    LOGS.mkdir(parents=True, exist_ok=True)
    with open(LOGS / "pipeline.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ahora(), "paso": paso, **datos}, ensure_ascii=False, default=str) + "\n")
