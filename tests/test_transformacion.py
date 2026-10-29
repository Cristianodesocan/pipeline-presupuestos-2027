"""Tests de 2_transformacion: motor de emparejamiento (datos sintéticos) e integración con el staging real."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "2_transformacion"))

from _emparejar import emparejar_par  # noqa: E402
from _tcomun import STG, cfg, normalizar_nombre  # noqa: E402
from construir_modelo import asignar_ids, concepto_ced  # noqa: E402

P = cfg()["crosswalk"]
PESOS = P["pesos"]["programa"]


def u(anio, filas):
    """filas: (codigo, nombre, inicial, ajustado)"""
    df = pd.DataFrame(filas, columns=["codigo", "denominacion_raw", "inicial", "ajustado"])
    df["anio_presupuesto"] = anio
    df["nombre_norm"] = df.denominacion_raw.map(normalizar_nombre)
    df["grupo"] = df.codigo.str[:3]
    df["secciones"] = [frozenset({"14"})] * len(df)
    return df


def enlaces(prev, act):
    r = emparejar_par(prev, act, "programa", PESOS, P)
    return {(o, d): t for o, d, t in zip(r.codigo_origen, r.codigo_destino, r.tipo_enlace)}, r


def test_normalizar_nombre():
    assert normalizar_nombre("Dirección Admva y Servicios Grales.") == "direccion administrativa y servicios generales"
    assert normalizar_nombre("CONSEJ. PRESIDENCIA, ADMONES. PÚBL.") == "consejeria presidencia administraciones publicas"


def test_identico_aunque_cambie_importe():
    e, r = enlaces(u(2020, [("312A", "Asistencia Sanitaria", 100, 0)]),
                   u(2021, [("312A", "Asistencia Sanitaria", 130, 80)]))
    assert e[("312A", "312A")] == "identico"
    assert r.estado.iloc[0] == "auto"


def test_recodificado_por_importe_y_nombre():
    e, r = enlaces(u(2020, [("231X", "Atención a personas mayores", 50_000_000, 0)]),
                   u(2021, [("231D", "Atención a personas mayores", 55_000_000, 50_000_000)]))
    assert e[("231X", "231D")] == "recodificado"
    assert r[r.tipo_enlace == "recodificado"].estado.iloc[0] == "auto"


def test_nuevo_y_nuevo_sin_origen_y_extinguido():
    e, _ = enlaces(u(2020, [("111A", "Programa que muere", 10, 0)]),
                   u(2021, [("222A", "Programa realmente nuevo", 5, 0),
                            ("333A", "Fondo reexpresado sin origen claro", 7, 9_999)]))
    assert e[(None, "222A")] == "nuevo"
    assert e[(None, "333A")] == "nuevo_sin_origen"
    assert e[("111A", None)] == "extinguido"


def test_fusion_de_varios_programas():
    """Caso real 2022: los programas 911x del Parlamento se funden en 912L."""
    prev = u(2021, [("911A", "Actuación Legislativa", 22_539_357, 0), ("911B", "Diputado del Común", 3_227_343, 0),
                    ("911F", "Acción Consultiva", 3_022_047, 0)])
    act = u(2022, [("912L", "Parlamento y Entes de relevancia Estatutaria", 30_000_000, 28_788_747)])
    e, _ = enlaces(prev, act)
    assert {o for (o, d), t in e.items() if t == "fusion" and d == "912L"} == {"911A", "911B", "911F"}


def test_division_conserva_el_mismo_codigo():
    prev = u(2023, [("241A", "Fomento del empleo", 100_000_000, 0)])
    act = u(2024, [("241A", "Fomento del empleo", 61_000_000, 60_000_000),
                   ("241K", "Fomento del empleo: refuerzo empresarial", 41_000_000, 40_000_000)])
    e, _ = enlaces(prev, act)
    assert e[("241A", "241A")] == "identico"
    assert e[("241A", "241K")] == "division"


def test_ids_siguen_recodificaciones_y_familias_unen_divisiones():
    unid = pd.DataFrame({"anio_presupuesto": [2020, 2021, 2021], "codigo": ["231X", "231D", "231E"]})
    ef = pd.DataFrame({
        "anio_origen": [2020, 2020], "codigo_origen": ["231X", "231X"],
        "anio_destino": [2021, 2021], "codigo_destino": ["231D", "231E"],
        "tipo_enlace": ["recodificado", "division"], "estado_final": ["auto", "auto"], "score": [0.9, 0.7]})
    ids, fams, pend = asignar_ids(unid, ef, "programa")
    assert ids[(2021, "231D")] == ids[(2020, "231X")] == "P231X_2020"
    assert ids[(2021, "231E")] == "P231E_2021"
    assert fams[(2021, "231E")] == fams[(2020, "231X")]
    assert not pend


def test_concepto_ced_prioridad():
    conceptos = {"sanidad": {"codigos": ["312A", "311*"], "keywords": ["salud"]},
                 "igualdad": {"codigos": ["232B"], "keywords": ["igualdad"]}}
    assert concepto_ced("312A", "asistencia sanitaria", conceptos) == "sanidad"
    assert concepto_ced("311C", "formacion", conceptos) == "sanidad"
    assert concepto_ced("999Z", "politicas de igualdad", conceptos) == "igualdad"
    assert concepto_ced("999Z", "carreteras", conceptos) is None


# --------------------------------------------------------------------------- integración (staging real)
@pytest.fixture(scope="module")
def stg():
    if not (STG / "fact_presupuesto.parquet").exists():
        pytest.skip("Sin staging de transformación: ejecuta los scripts de 2_transformacion")
    return {n: pd.read_parquet(STG / f"{n}.parquet") for n in
            ("fact_presupuesto", "dim_anio", "xwalk_programa", "fact_seccion_estructura", "dim_programa")}


def test_fdcan_explica_el_perimetro_2017(stg):
    """El +159,2 M€ del ajustado de 2017 (aviso E8) es el Fondo de Desarrollo de Canarias (943A)."""
    x = stg["xwalk_programa"]
    f = x[(x.codigo_destino == "943A") & (x.anio_destino == 2017)]
    assert f.tipo_enlace.iloc[0] == "nuevo_sin_origen"
    assert f.ajustado_destino.iloc[0] == 159_232_310


def test_fusion_parlamento_2022(stg):
    x = stg["xwalk_programa"]
    f = x[(x.codigo_destino == "912L") & (x.tipo_enlace == "fusion")]
    assert set(f.codigo_origen) >= {"911A", "911B", "911F", "911O", "911P"}


def test_deflactor_base_2025(stg):
    da = stg["dim_anio"].set_index("anio")
    assert abs(da.deflactor[2025] - 1) < 1e-4
    assert da.deflactor[2015] > da.deflactor[2024] > 1


def test_retroproyeccion_cuadra_con_21(stg):
    f = stg["fact_presupuesto"]
    t21 = f[f.serie_oficial & (f.tabla == "secciones") & (f.version_importe == "inicial")].groupby("anio").importe_corriente.sum()
    retro = stg["fact_seccion_estructura"].groupby("anio").importe_corriente.sum()
    assert (retro - t21).abs().max() < 1


def test_312A_continua(stg):
    d = stg["dim_programa"]
    assert d[d.codigo == "312A"].comparabilidad.iloc[0] == "continua"
