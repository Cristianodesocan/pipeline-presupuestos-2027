"""Invariantes de los datos de la web (nivel 2 de auditoria/auditar_datos.py, sin PDF ni red).

Si una nueva carga rompe alguna (totales distintos entre dimensiones, pesos que no suman 100, constantes mal deflactadas,
capítulos que no cuadran…), el test falla antes de publicar. La auditoría completa frente al Tomo y la pantalla está en
auditoria/ (ver auditoria/informe_auditoria.md).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "auditoria"))

import auditar_datos as ad  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "5_visualizacion" / "data"


@pytest.mark.skipif(not (DATA / "viz_capitulos.csv").exists(), reason="sin CSV de la web")
def test_coherencia_y_calculos_de_la_web():
    ad.resultados.clear()
    t, s, c, a, m = ad.cargar()
    ad.nivel_coherencia(t, s, c, a, m)
    ad.nivel_calculos(t, s, c, a, None)
    errores = [f"{r['id']} {r['titulo']}: {r['ejemplos'][:2]}" for r in ad.resultados if r["estado"] == "ERROR"]
    assert not errores, "\n".join(errores)
    assert len(ad.resultados) >= 15
