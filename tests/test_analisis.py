"""Tests de 4_analisis: métricas puras con datos sintéticos e integridad de las salidas reales."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "4_analisis"))

import _metricas as m  # noqa: E402
from _lectura import COLUMNAS_ANA, SALIDAS  # noqa: E402


def panel(filas, precios="corrientes"):
    """filas: (id, anio, importe[, ajustado[, padre]])"""
    df = pd.DataFrame([f + (None,) * (5 - len(f)) for f in filas], columns=["id", "anio", "importe", "ajustado", "padre"])
    df["precios"] = precios
    return df


def val(t, metrica, id_, anio=None, ventana="anual"):
    x = t[(t.metrica == metrica) & (t.id == id_) & (t.ventana == ventana)]
    if anio is not None:
        x = x[x.anio == anio]
    return x.valor.iloc[0] if len(x) else None


P = panel([("a", 2015, 60, None, "X"), ("b", 2015, 40, None, "X"),
           ("a", 2019, 90, 80, "X"), ("b", 2019, 30, 35, "X")])


def test_pesos_suman_100_y_rank():
    t = m.importe_y_peso(P)
    assert val(t, "peso_total_pct", "a", 2015) == 60 and val(t, "peso_total_pct", "a", 2019) == 75
    assert val(t, "peso_padre_pct", "b", 2019) == 25
    assert val(t, "rank_peso", "a", 2019) == 1


def test_variaciones_no_cruzan_huecos_e_indice():
    p = panel([("a", 2015, 100), ("a", 2016, 110), ("a", 2018, 121)])
    t = m.variaciones(p)
    assert val(t, "var_pct", "a", 2016) == pytest.approx(10)
    assert val(t, "var_pct", "a", 2018) is None          # 2017 falta: no se compara 2018 con 2016
    assert val(t, "indice_2015", "a", 2018) == pytest.approx(121)


def test_homogeneas_y_reestructuracion():
    p = panel([("a", 2015, 100), ("a", 2016, 130, 120), ("n", 2016, 50, 40)])
    t = m.variaciones_homogeneas(p)
    assert val(t, "var_abs_homog", "a", 2016) == 10          # decisión: 130 − 120
    assert val(t, "efecto_reestr", "a", 2016) == 20          # perímetro: 120 − 100
    assert val(t, "efecto_reestr", "n", 2016) is None        # sin año anterior: no se imputa


def test_ventana_tcac_delta_elasticidad():
    t = m.metricas_ventana(P, [{"id": "v", "base": 2015, "fin": 2019}])
    assert val(t, "tcac_ventana", "a", ventana="v") == pytest.approx(100 * (1.5 ** 0.25 - 1))
    assert val(t, "delta_peso_pp_ventana", "a", ventana="v") == pytest.approx(15)
    assert val(t, "delta_peso_pp_ventana", "b", ventana="v") == pytest.approx(-15)
    tc_tot = val(t, "tcac_ventana", m.TOTAL, ventana="v")
    assert val(t, "elasticidad_ventana", "a", ventana="v") == pytest.approx(100 * (1.5 ** 0.25 - 1) / tc_tot)


def test_ruptura_tendencia_signo():
    v = pd.DataFrame({"id": ["a", "a"], "anio": [2019, 2023], "precios": "corrientes", "ventana": ["ant", "act"],
                      "metrica": "tcac_ventana", "valor": [2.0, 5.0], "unidad": "pct"})
    r = m.ruptura_tendencia(v, "act", ["ant"])
    assert r.valor.iloc[0] == 3.0 and r.metrica.iloc[0] == "ruptura_tendencia_vs_ant"


def test_hhi_partes_iguales():
    p = panel([(k, 2020, 25) for k in "abcd"])
    assert m.hhi(p).valor.iloc[0] == pytest.approx(2500)


def test_ventanas_desde_acotan_al_ultimo_anio():
    da = pd.DataFrame({"anio": range(2015, 2028),
                       "ventana": ["base"] + ["v1"] * 4 + ["v2"] * 4 + ["v3"] * 4,
                       "base_comparacion": [np.nan] + [2015] * 4 + [2019] * 4 + [2023] * 4})
    vs = {v["id"]: v for v in m.ventanas_desde(da, list(range(2015, 2027)))}
    assert vs["v3"]["fin"] == 2026 and not vs["v3"]["completa"]
    assert vs["2015_2026"]["base"] == 2015 and "base" not in vs


# --------------------------------------------------------------------------- salidas reales
SCRIPTS = ("funciones", "secciones", "programas", "entes")


@pytest.fixture(scope="module")
def salidas():
    faltan = [d for d in SCRIPTS if not (SALIDAS / f"ana_{d}.parquet").exists()]
    if faltan:
        pytest.skip(f"Faltan salidas de análisis: {faltan}")
    return {d: pd.read_parquet(SALIDAS / f"ana_{d}.parquet") for d in SCRIPTS}


def test_esquema_tidy_comun(salidas):
    for d, t in salidas.items():
        assert list(t.columns) == COLUMNAS_ANA, d
        clave = ["dimension", "vista", "id_estable", "anio", "fase", "precios", "ventana", "metrica", "incluye_mrr"]
        assert not t.duplicated(clave).any(), d
        assert set(t.estatus_dato) <= {"verificado", "estimacion"}


def test_pesos_por_dimension_suman_100(salidas):
    t = pd.concat(salidas.values())
    p = t[(t.metrica == "peso_total_pct") & (t.ventana == "anual") & (t.id_estable != "__total__")]
    sumas = p.groupby(["dimension", "vista", "incluye_mrr", "anio", "precios"]).valor.sum()
    assert np.allclose(sumas, 100)


def test_total_funciones_cuadra_con_pdf(salidas):
    f = salidas["funciones"]
    tot = f[(f.dimension == "funcion") & (f.metrica == "importe") & (f.anio == 2026) & (f.precios == "corrientes")
            & (f.id_estable != "__total__")].valor.sum()
    assert tot == 11_909_123_064


def test_vistas_de_secciones_tienen_el_mismo_total(salidas):
    s = salidas["secciones"]
    imp = s[(s.metrica == "importe") & (s.precios == "corrientes") & (s.incluye_mrr == "si") & (s.id_estable != "__total__")]
    g = imp.groupby(["vista", "anio"]).valor.sum().unstack(0)
    assert np.allclose(g.iloc[:, 0], g.iloc[:, 1])


def test_variante_sin_mrr_resta_los_fondos(salidas):
    s = salidas["secciones"]
    imp = s[(s.metrica == "importe") & (s.precios == "corrientes") & (s.vista == "organica") & (s.anio == 2026)
            & (s.id_estable != "__total__")]
    dif = imp[imp.incluye_mrr == "si"].valor.sum() - imp[imp.incluye_mrr == "no"].valor.sum()
    assert dif == pytest.approx(447_381_405, abs=1)   # servicios MRR / REACT-EU de la Ley 2026 (tabla 2.2)
