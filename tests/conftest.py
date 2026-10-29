import sys
from pathlib import Path

import pdfplumber
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "1_extraccion"))

from _comun import manifest  # noqa: E402
from _comun.rutas import RAIZ, cargar_tablas  # noqa: E402


@pytest.fixture(scope="session")
def cfg():
    return cargar_tablas()[0]


@pytest.fixture(scope="session")
def abrir_pdf():
    """Abre el PDF vigente de (año, fase); omite el test si no se ha descargado."""
    abiertos = {}

    def _abrir(anio: int, fase: str = "ley"):
        if (anio, fase) not in abiertos:
            reg = manifest.vigente(anio, fase)
            if reg is None:
                pytest.skip(f"Tomo 3 {anio} {fase} no descargado: python 1_extraccion/descargar_tomos.py")
            abiertos[(anio, fase)] = pdfplumber.open(RAIZ / reg["fichero"])
        return abiertos[(anio, fase)]

    yield _abrir
    for pdf in abiertos.values():
        pdf.close()
