"""Carga idempotente común a DuckDB y PostgreSQL, dentro de UNA transacción para toda la carga.

PostgreSQL (Supabase), por tabla:
  1. COPY a una tabla temporal,
  2. INSERT … ON CONFLICT (clave natural) DO UPDATE,
  3. DELETE de las filas cuya clave ya no está en el origen (el destino queda como espejo exacto).
DuckDB (local): reemplazo completo de cada tabla (ver _sincronizar_duckdb).
Ejecutarla dos veces deja el mismo contenido (salvo run_id y cargado_en).
"""
import re
import uuid

import pandas as pd

from modelo_bd import CARGA, ESQUEMA, TABLAS, ddl, preparar

VIEWS_SQL = (CARGA / "vistas_viz.sql").read_text(encoding="utf-8")
VISTAS = ["v_viz_treemap", "v_viz_series", "v_viz_meta"]


def sentencias(sql: str) -> list[str]:
    sin_comentarios = "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))
    return [s.strip() for s in sin_comentarios.split(";") if s.strip()]


def sql_vistas() -> str:
    return VIEWS_SQL.replace("{esquema}", ESQUEMA)


def sql_seguridad_supabase() -> str:
    """RLS en todas las tablas sin políticas para anon/authenticated: solo las vistas v_viz_* son legibles."""
    lineas = [f"ALTER TABLE {ESQUEMA}.{t} ENABLE ROW LEVEL SECURITY;" for t in [*TABLAS, "carga_registro"]]
    lineas += [f"REVOKE ALL ON ALL TABLES IN SCHEMA {ESQUEMA} FROM anon, authenticated;",
               f"GRANT USAGE ON SCHEMA {ESQUEMA} TO anon, authenticated;"]
    lineas += [f"GRANT SELECT ON {ESQUEMA}.{v} TO anon, authenticated;" for v in VISTAS]
    return "\n".join(lineas) + "\n"


def aplicar_esquema(conn, dialecto: str, seguridad: bool = False) -> None:
    for s in sentencias(ddl(dialecto)) + sentencias(sql_vistas()):
        conn.execute(s)
    if seguridad:
        for s in sentencias(sql_seguridad_supabase()):
            conn.execute(s)


def _volcar_temporal(conn, dialecto: str, nombre: str, df: pd.DataFrame, tmp: str) -> None:
    cols = list(df.columns)
    if dialecto == "duckdb":
        conn.execute(f"CREATE TEMP TABLE {tmp} AS SELECT * FROM {ESQUEMA}.{nombre} LIMIT 0")
        conn.register("_df_carga", df)
        conn.execute(f"INSERT INTO {tmp} ({', '.join(cols)}) SELECT {', '.join(cols)} FROM _df_carga")
        conn.unregister("_df_carga")
    else:
        conn.execute(f"CREATE TEMP TABLE {tmp} (LIKE {ESQUEMA}.{nombre}) ON COMMIT DROP")
        with conn.cursor().copy(f"COPY {tmp} ({', '.join(cols)}) FROM STDIN") as copy:
            for fila in df.astype(object).where(df.notna(), None).itertuples(index=False, name=None):
                copy.write_row(fila)


def _sincronizar_duckdb(conn, nombre: str, df: pd.DataFrame) -> dict:
    """DuckDB: reemplazo completo dentro de la transacción; altas y bajas se cuentan en pandas.

    DuckDB 2.0.0 devolvió resultados erróneos en el anti-join (NOT EXISTS / EXCEPT) contra una tabla con clave
    primaria dentro de una transacción de escritura: la carga de ana_metricas quedaba vacía sin error. El
    reemplazo completo es igual de idempotente y deja el destino como espejo exacto del origen.
    """
    clave = TABLAS[nombre]["clave"]
    previas = conn.execute(f"SELECT {', '.join(clave)} FROM {ESQUEMA}.{nombre}").df()
    k_new = set(map(tuple, df[clave].astype(str).itertuples(index=False, name=None)))
    k_old = set(map(tuple, previas.astype(str).itertuples(index=False, name=None)))
    conn.execute(f"DELETE FROM {ESQUEMA}.{nombre}")
    conn.register("_df_carga", df)
    cols = ", ".join(df.columns)
    conn.execute(f"INSERT INTO {ESQUEMA}.{nombre} ({cols}) SELECT {cols} FROM _df_carga")
    conn.unregister("_df_carga")
    escritas = conn.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{nombre}").fetchone()[0]
    if escritas != len(df):
        raise RuntimeError(f"{nombre}: se escribieron {escritas} filas de {len(df)}")
    return {"filas": len(df), "nuevas": len(k_new - k_old), "borradas": len(k_old - k_new)}


def sincronizar(conn, dialecto: str, nombre: str, df: pd.DataFrame, run_id: str, ahora) -> dict:
    t = TABLAS[nombre]
    df = df.assign(run_id=run_id, cargado_en=ahora)
    if dialecto == "duckdb":
        return _sincronizar_duckdb(conn, nombre, df)
    tmp = f"tmp_{nombre}"
    _volcar_temporal(conn, dialecto, nombre, df, tmp)
    clave = t["clave"]
    igual = " AND ".join(f"d.{c} = s.{c}" for c in clave)
    cols = list(df.columns)
    resto = [c for c in cols if c not in clave]
    nuevas = conn.execute(f"SELECT COUNT(*) FROM {tmp} s WHERE NOT EXISTS "
                          f"(SELECT 1 FROM {ESQUEMA}.{nombre} d WHERE {igual})").fetchone()[0]
    conn.execute(f"INSERT INTO {ESQUEMA}.{nombre} ({', '.join(cols)}) SELECT {', '.join(cols)} FROM {tmp} "
                 f"ON CONFLICT ({', '.join(clave)}) DO UPDATE SET "
                 + ", ".join(f"{c} = EXCLUDED.{c}" for c in resto))
    borradas = conn.execute(f"SELECT COUNT(*) FROM {ESQUEMA}.{nombre} d WHERE NOT EXISTS "
                            f"(SELECT 1 FROM {tmp} s WHERE {igual})").fetchone()[0]
    conn.execute(f"DELETE FROM {ESQUEMA}.{nombre} d WHERE NOT EXISTS (SELECT 1 FROM {tmp} s WHERE {igual})")
    return {"filas": len(df), "nuevas": int(nuevas), "borradas": int(borradas)}


def cargar(conn, dialecto: str, destino: str, que: str) -> dict:
    """Carga en una transacción las tablas disponibles. que ∈ {base, analisis, todo}."""
    run_id = uuid.uuid4().hex[:12]
    ahora = pd.Timestamp.now(tz="UTC")
    resumen = {}
    for nombre, t in TABLAS.items():
        es_analisis = bool(t.get("analisis"))
        if (que == "base" and es_analisis) or (que == "analisis" and not es_analisis):
            continue
        df = preparar(nombre)
        if df is None:
            resumen[nombre] = "sin origen (se omite)"
            continue
        r = sincronizar(conn, dialecto, nombre, df, run_id, ahora)
        conn.execute(f"INSERT INTO {ESQUEMA}.carga_registro (run_id, tabla, destino, filas, nuevas, borradas, cargado_en) "
                     f"VALUES ('{run_id}', '{nombre}', '{destino}', {r['filas']}, {r['nuevas']}, {r['borradas']}, "
                     f"CAST('{ahora.isoformat()}' AS TIMESTAMPTZ))")
        resumen[nombre] = r
    return {"run_id": run_id, "tablas": resumen}


def es_remoto(url: str) -> bool:
    host = re.sub(r"^.*@", "", url.split("?")[0]).split("/")[0].split(":")[0]
    return host not in {"localhost", "127.0.0.1", "::1", ""}
