"""Tests de 4_analisis/analisis_hipotesis_electoral.py: contraste de permutación, legislatura e indicadores."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "4_analisis"))

from _lectura import BD_LOCAL  # noqa: E402
from analisis_hipotesis_electoral import dentro_de_legislatura, indicadores, permutacion  # noqa: E402


def test_permutacion_exacta():
    v = pd.Series([1.0, 2, 3, 4, 10], index=[2016, 2017, 2018, 2019, 2020])
    r = permutacion(v, [2019, 2020])
    assert r["combinaciones"] == 10 and r["p_minimo"] == pytest.approx(0.1)
    assert r["p_unilateral"] == pytest.approx(0.1)      # (4+10)/2 es la mayor media de las 10 parejas
    assert r["rangos"] == {2019: 2, 2020: 1}
    assert permutacion(v, [2016, 2017])["p_unilateral"] == pytest.approx(1.0)


def test_permutacion_ignora_anios_ausentes():
    v = pd.Series([1.0, 2, 3], index=[2016, 2017, 2018])
    assert permutacion(v, [2027]) == {"k": 0}


def test_dentro_de_legislatura():
    v = pd.Series([1.0, 2, 3, 9], index=[2016, 2017, 2018, 2019])
    d = dentro_de_legislatura(v, [2019, 2023]).iloc[0]
    assert (d.anio, d.electoral, d.media_previos, d.max_previos) == (2019, 9, 2, 3)


def test_indicadores_diferencial_y_peso():
    s = pd.DataFrame({"anio": [2018, 2019], "precios": "constantes", "importe": [100.0, 120], "ajustado": [np.nan, 110]})
    t = pd.DataFrame({"anio": [2018, 2019], "precios": "constantes", "importe": [1000.0, 1050]})
    d = indicadores(s, t).set_index("anio").loc[2019]
    assert d.g == pytest.approx(20) and d.g_tot == pytest.approx(5) and d.dif == pytest.approx(15)
    assert d.g_homog == pytest.approx(100 * (120 / 110 - 1))
    assert d.dpeso == pytest.approx(100 * 120 / 1050 - 10)


@pytest.mark.skipif(not BD_LOCAL.exists(), reason="sin base local: ejecuta 00_maestro.py")
def test_2019_es_el_mayor_diferencial_de_la_funcion_23():
    from _lectura import cfg, leer
    from analisis_hipotesis_electoral import serie_tabla
    datos = leer()
    d = indicadores(serie_tabla(datos.fact, "funciones", [cfg()["hipotesis_electoral"]["funcion_social"]]),
                    serie_tabla(datos.fact, "programas"))
    dif = d[d.precios == "constantes"].set_index("anio").dif.dropna()
    assert dif.idxmax() == 2019
    assert dif[2023] < dif[[2020, 2021, 2022]].mean()
