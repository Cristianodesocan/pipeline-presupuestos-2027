"""Registro de descargas (logs/manifest.jsonl) y localización del PDF vigente."""
import hashlib
import json
from pathlib import Path

from .rutas import LOGS, RAIZ

MANIFEST = LOGS / "manifest.jsonl"
EVENTOS_VALIDOS = {"nuevo", "sin_cambios", "republicado"}


def sha256_fichero(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_manifest() -> list[dict]:
    if not MANIFEST.exists():
        return []
    with open(MANIFEST, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def anotar(registro: dict) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")


def vigente(anio: int, fase: str, tomo: int = 3) -> dict | None:
    """Último registro válido de (anio, fase, tomo) cuyo fichero existe en disco."""
    for r in reversed(leer_manifest()):
        if (r["anio"], r["fase"], r["tomo"]) == (anio, fase, tomo) and r["evento"] in EVENTOS_VALIDOS:
            if (RAIZ / r["fichero"]).exists():
                return r
    return None


def documentos_vigentes() -> list[dict]:
    claves = sorted({(r["anio"], r["fase"], r["tomo"]) for r in leer_manifest()})
    return [d for d in (vigente(*k) for k in claves) if d]
