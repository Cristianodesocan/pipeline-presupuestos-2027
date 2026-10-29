"""Tests de 3_carga: esquema, sincronización idempotente, vistas y seguridad.

Los de PostgreSQL solo se ejecutan si PG_TEST_URL apunta a un PostgreSQL DE PRUEBA en localhost
(nunca a producción), con los roles anon y authenticated creados.
"""
import os
import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "3_carga"))

from _sincronizar import aplicar_esquema, cargar, es_remoto, sincronizar  # noqa: E402
from modelo_bd import ESQUEMA, STG_T, TABLAS, ddl  # noqa: E402

AHORA = pd.Timestamp("2026-10-28", tz="UTC")


@pytest.fixture
def bd(tmp_path):
    c = duckdb.connect(str(tmp_path / "t.duckdb"))
    aplicar_esquema(c, "duckdb")
    yield c
    c.close()


def contenido(c, tabla, orden):
    return c.execute(f"SELECT * EXCLUDE (run_id, cargado_en) FROM {ESQUEMA}.{tabla} ORDER BY {orden}").df()


def anios(filas):
    df = pd.DataFrame(filas, columns=["anio", "ipc_media"]).reindex(columns=list(TABLAS["dim_anio"]["columnas"]))
    df["anio"] = df.anio.astype("Int64")
    return df


def test_ddl_tiene_clave_en_todas_las_tablas():
    for dialecto in ("duckdb", "postgres"):
        sql = ddl(dialecto)
        assert sql.count("PRIMARY KEY") == len(TABLAS) + 1   # + carga_registro


@pytest.mark.parametrize("url, remoto", [
    ("postgresql://postgres@localhost:55432/postgres", False),
    ("postgresql://u:p@127.0.0.1/db", False),
    ("postgresql://postgres.ref:clave@aws-0-eu-west-1.pooler.supabase.com:5432/postgres", True),
    ("postgresql://postgres:x@db.ref.supabase.co:5432/postgres?sslmode=require", True),
])
def test_es_remoto(url, remoto):
    assert es_remoto(url) is remoto


def test_sincronizacion_idempotente_y_espejo(bd):
    r1 = sincronizar(bd, "duckdb", "dim_anio", anios([(2024, 98.0), (2025, 100.0), (2026, 102.8)]), "r1", AHORA)
    assert r1 == {"filas": 3, "nuevas": 3, "borradas": 0}
    r2 = sincronizar(bd, "duckdb", "dim_anio", anios([(2024, 98.0), (2025, 100.0), (2026, 102.8)]), "r2", AHORA)
    assert r2 == {"filas": 3, "nuevas": 0, "borradas": 0}
    # cambia un valor y desaparece 2024: se actualiza y se borra
    r3 = sincronizar(bd, "duckdb", "dim_anio", anios([(2025, 100.0), (2026, 103.1)]), "r3", AHORA)
    assert r3 == {"filas": 2, "nuevas": 0, "borradas": 1}
    df = contenido(bd, "dim_anio", "anio")
    assert df.anio.tolist() == [2025, 2026] and df.ipc_media.tolist() == [100.0, 103.1]


def test_vistas_pivotan_ana_metricas(bd):
    filas = []
    base = {"dimension": "programa", "vista": "individual", "id_estable": "P312A_2015", "etiqueta": "Asistencia Sanitaria",
            "nivel": 3, "padre_id": "SF312_2015", "padre_etiqueta": "Sanidad", "ruta_jerarquia": "Sanidad|Sanidad",
            "fase": "ley", "precios": "corrientes", "unidad": "", "comparabilidad": "continua",
            "estatus_dato": "verificado", "concepto_ced": "sanidad", "incluye_mrr": "si"}
    for metrica, valor in (("importe", 4.5e9), ("peso_total_pct", 38.1), ("peso_padre_pct", 99.0), ("var_pct", 5.4),
                           ("var_abs", 2.3e8), ("indice_2015", 184.8)):
        filas.append({**base, "anio": 2026, "ventana": "anual", "metrica": metrica, "valor": valor})
    for metrica, valor in (("delta_peso_pp_ventana", 1.2), ("var_pct_ventana", 27.0)):
        filas.append({**base, "anio": 2026, "ventana": "clavijo_ii", "metrica": metrica, "valor": valor})
    df = pd.DataFrame(filas).reindex(columns=list(TABLAS["ana_metricas"]["columnas"]))
    sincronizar(bd, "duckdb", "ana_metricas", df, "r1", AHORA)
    t = bd.execute(f"SELECT * FROM {ESQUEMA}.v_viz_treemap").df()
    assert len(t) == 1
    r = t.iloc[0]
    assert (r.nivel_1, r.nivel_2, r.nivel_3) == ("Sanidad", "Sanidad", None)
    assert (r.importe, r.peso_total_pct, r.var_pct_interanual) == (4.5e9, 38.1, 5.4)
    assert (r.delta_peso_pp_clavijo_ii, r.var_pct_clavijo_ii) == (1.2, 27.0)
    s = bd.execute(f"SELECT * FROM {ESQUEMA}.v_viz_series").df()
    assert s.iloc[0].indice_2015 == 184.8


@pytest.mark.skipif(not (STG_T / "fact_presupuesto.parquet").exists(), reason="sin staging de transformación")
def test_carga_completa_cuadra(bd):
    res = cargar(bd, "duckdb", "test", "base")
    assert res["tablas"]["fact_presupuesto"]["nuevas"] > 40_000
    total = bd.execute(f"SELECT SUM(importe_corriente) FROM {ESQUEMA}.fact_presupuesto WHERE serie_oficial "
                       f"AND tabla = 'programas' AND version_importe = 'inicial' AND anio = 2026").fetchone()[0]
    assert total == 11_909_123_064
    assert cargar(bd, "duckdb", "test", "base")["tablas"]["fact_presupuesto"] == \
        {"filas": res["tablas"]["fact_presupuesto"]["filas"], "nuevas": 0, "borradas": 0}


PG = os.environ.get("PG_TEST_URL")


@pytest.mark.skipif(not PG or es_remoto(PG or "x@remoto"), reason="PG_TEST_URL no definida o no es localhost")
def test_postgres_rls_solo_vistas():
    import psycopg
    with psycopg.connect(PG) as c:
        aplicar_esquema(c, "postgres", seguridad=True)
        c.execute("SET ROLE anon")
        c.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.v_viz_meta").fetchone()
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            c.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.fact_presupuesto")
        c.rollback()
