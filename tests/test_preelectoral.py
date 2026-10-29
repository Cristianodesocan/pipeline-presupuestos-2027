"""Tests de 4_analisis/analisis_preelectoral.py: medidas, anomalía de legislatura, Benjamini-Hochberg e integración."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "4_analisis"))

from _lectura import BD_LOCAL  # noqa: E402
from analisis_preelectoral import benjamini_hochberg, medidas, resumen_nivel  # noqa: E402


def test_benjamini_hochberg():
    q = benjamini_hochberg(pd.Series([0.01, 0.04, 0.03, 0.20], index=list("abcd")))
    assert q["a"] == pytest.approx(0.04) and q["b"] == pytest.approx(0.0533, abs=1e-3)
    assert q["c"] == pytest.approx(0.0533, abs=1e-3) and q["d"] == pytest.approx(0.20)


def test_medidas_y_exceso():
    total = pd.Series({2018: 1000.0, 2019: 1100.0})
    p = pd.DataFrame({"id": ["x", "x"], "anio": [2018, 2019], "importe": [100.0, 130.0]})
    m = medidas(p, total, [2019]).iloc[0]
    assert m.g == pytest.approx(30) and m.g_tot == pytest.approx(10) and m.dif == pytest.approx(20)
    assert m.exceso == pytest.approx(130 - 100 * 1.1)


def test_patron_y_anomalia_frente_a_la_legislatura():
    anios = list(range(2015, 2024))
    total = pd.Series({a: 1000.0 for a in anios})
    # «sube» crece 10 % los años electorales y 0 % el resto; «baja», al revés
    imp_sube, imp_baja, v1, v2 = [], [], 100.0, 100.0
    for a in anios:
        if a > 2015:
            v1 *= 1.10 if a in (2019, 2023) else 1.0
            v2 *= 0.95 if a in (2019, 2023) else 1.0
        imp_sube.append(v1)
        imp_baja.append(v2)
    p = pd.DataFrame({"id": ["sube"] * len(anios) + ["baja"] * len(anios), "anio": anios * 2, "importe": imp_sube + imp_baja})
    r = resumen_nivel(medidas(p, total, [2019, 2023]), {}, [2019, 2023], None).set_index("id")
    assert r.loc["sube", "patron"] == "se acentúa" and r.loc["sube", "anomalia_2019"] == pytest.approx(10)
    assert r.loc["baja", "patron"] == "se contrae"
    assert r.loc["sube", "p"] == pytest.approx(1 / 28)       # 8 años con variación: C(8,2) = 28 parejas


@pytest.mark.skipif(not BD_LOCAL.exists(), reason="sin base local: ejecuta 00_maestro.py")
def test_transferencias_locales_se_acentuan_en_2019_y_2023():
    from _lectura import leer
    from analisis_preelectoral import unidades
    datos = leer()
    niveles = unidades(datos)
    p, et = niveles["consejeria"]
    tot = datos.fact[datos.fact.serie_oficial & (datos.fact.tabla == "programas") & (datos.fact.version_importe == "inicial")]
    total = tot.groupby("anio").importe_constante.sum()
    r = resumen_nivel(medidas(p, total, [2019, 2023]), et, [2019, 2023], None).set_index("id")
    assert r.loc["20", "patron"] == "se acentúa"
    assert "sin_equivalente_2026" not in r.index
