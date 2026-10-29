"""Definición única de las tablas de la base de datos (DuckDB local y PostgreSQL/Supabase).

Cada tabla declara su origen, sus columnas con tipo y su clave natural. De aquí salen:
  - el DDL de ambos destinos (esquema.sql de Supabase se genera, no se escribe a mano),
  - la preparación de los DataFrames que se cargan (columnas, tipos, clave sin nulos ni duplicados).
"""
import sys
from pathlib import Path

import pandas as pd

CARGA = Path(__file__).resolve().parent
RAIZ = CARGA.parent
sys.path.insert(0, str(RAIZ / "1_extraccion"))

from _comun.rutas import LOGS, ahora, log_evento  # noqa: E402,F401

STG_T = RAIZ / "2_transformacion" / "staging"
SALIDAS_ANALISIS = RAIZ / "4_analisis" / "salidas"
ESQUEMA = "presupuestos_can"
TIPOS = {"txt": ("TEXT", "VARCHAR"), "int": ("BIGINT", "BIGINT"), "num": ("DOUBLE PRECISION", "DOUBLE"),
         "bool": ("BOOLEAN", "BOOLEAN"), "ts": ("TIMESTAMPTZ", "TIMESTAMPTZ")}

DIM_UNIDAD = {"dimension": "txt", "id_estable": "txt", "codigo": "txt", "denominacion_raw": "txt",
              "denominacion_std": "txt", "anio_desde": "int", "anio_hasta": "int", "anio_hasta_activo": "int",
              "padre_codigo": "txt", "familia_id": "txt", "comparabilidad": "txt", "concepto_ced": "txt",
              "n_codigos_id": "int"}

TABLAS = {
    "dim_anio": {
        "origen": "dim_anio", "clave": ["anio"],
        "columnas": {"anio": "int", "ipc_media": "num", "ipc_meses": "int", "ipc_estatus": "txt", "deflactor": "num",
                     "deflactor_base": "int", "poblacion": "int", "poblacion_estatus": "txt", "pib_nominal": "num",
                     "pib_estatus": "txt", "ventana": "txt", "presidencia": "txt", "coalicion": "txt",
                     "base_comparacion": "int", "ventana_actual": "bool", "fuente": "txt"}},
    **{f"dim_{d}": {"origen": f"dim_{d}", "clave": ["id_estable", "codigo"], "columnas": DIM_UNIDAD}
       for d in ("seccion", "funcion", "subfuncion", "programa", "ente")},
    "fact_presupuesto": {
        "origen": "fact_presupuesto",
        "clave": ["anio", "anio_presupuesto", "fase", "tabla", "dimension", "codigo", "capitulo", "version_importe", "perimetro"],
        "columnas": {"anio": "int", "anio_presupuesto": "int", "fase": "txt", "serie_oficial": "bool", "dimension": "txt",
                     "tabla": "txt", "codigo": "txt", "codigo_unidad": "txt", "codigo_padre": "txt",
                     "denominacion_raw": "txt", "capitulo": "txt", "version_importe": "txt", "perimetro": "txt",
                     "importe_corriente": "num", "importe_constante": "num", "deflactor": "num", "precios_base": "int",
                     "es_fondo_extraordinario": "bool", "id_estable": "txt", "familia_id": "txt", "id_padre": "txt",
                     "estatus_dato": "txt", "estatus_constante": "txt", "doc_id": "txt", "pagina": "int"}},
    "fact_seccion_estructura": {
        "origen": "fact_seccion_estructura", "clave": ["vista", "anio", "seccion_destino", "metodo"],
        "columnas": {"vista": "txt", "anio": "int", "seccion_destino": "txt", "denominacion_destino": "txt",
                     "metodo": "txt", "n_pares": "int", "importe_corriente": "num", "importe_constante": "num"}},
    "xwalk": {
        "origen": [f"xwalk_{d}" for d in ("seccion", "funcion", "subfuncion", "programa", "ente")],
        "clave": ["dimension", "anio_origen", "codigo_origen", "anio_destino", "codigo_destino", "tipo_enlace"],
        "columnas": {"dimension": "txt", "anio_origen": "int", "codigo_origen": "txt", "anio_destino": "int",
                     "codigo_destino": "txt", "tipo_enlace": "txt", "estado": "txt", "estado_final": "txt", "score": "num",
                     "s_importe": "num", "s_nombre": "num", "s_codigo": "num", "s_grupo": "num", "s_seccion": "num",
                     "denominacion_origen": "txt", "denominacion_destino": "txt", "inicial_origen": "num",
                     "ajustado_destino": "num", "inicial_destino": "num"}},
    "fondos_extraordinarios": {
        "origen": "fondos_extraordinarios", "clave": ["anio_presupuesto", "fase", "codigo"],
        "columnas": {"anio_presupuesto": "int", "fase": "txt", "serie_oficial": "bool", "codigo": "txt",
                     "codigo_padre": "txt", "denominacion_raw": "txt", "importe_corriente": "num", "pagina": "int"}},
    # Resultados de 4_analisis (§7.1). Se carga en la segunda pasada (--que analisis); hasta entonces, vacía.
    "ana_metricas": {
        "origen": [f"ana_{d}" for d in ("funciones", "secciones", "programas", "entes")], "analisis": True,
        "clave": ["dimension", "vista", "id_estable", "anio", "fase", "precios", "ventana", "metrica", "incluye_mrr"],
        "columnas": {"dimension": "txt", "vista": "txt", "id_estable": "txt", "etiqueta": "txt", "nivel": "int",
                     "padre_id": "txt", "padre_etiqueta": "txt", "ruta_jerarquia": "txt", "anio": "int", "fase": "txt",
                     "precios": "txt", "ventana": "txt", "metrica": "txt", "valor": "num", "unidad": "txt",
                     "comparabilidad": "txt", "estatus_dato": "txt", "concepto_ced": "txt", "incluye_mrr": "txt"}},
}
CONTROL = {"run_id": "txt", "cargado_en": "ts"}


def ddl_tabla(nombre: str, dialecto: str) -> str:
    i = 0 if dialecto == "postgres" else 1
    t = TABLAS[nombre]
    cols = [f'  {c} {TIPOS[tp][i]}{" NOT NULL" if c in t["clave"] else ""}'
            for c, tp in {**t["columnas"], **CONTROL}.items()]
    cols.append(f"  PRIMARY KEY ({', '.join(t['clave'])})")
    return f"CREATE TABLE IF NOT EXISTS {ESQUEMA}.{nombre} (\n" + ",\n".join(cols) + "\n);"


def ddl(dialecto: str) -> str:
    partes = [f"CREATE SCHEMA IF NOT EXISTS {ESQUEMA};"]
    partes += [ddl_tabla(n, dialecto) for n in TABLAS]
    partes.append(f"""CREATE TABLE IF NOT EXISTS {ESQUEMA}.carga_registro (
  run_id {TIPOS['txt'][0 if dialecto == 'postgres' else 1]} NOT NULL,
  tabla {TIPOS['txt'][0 if dialecto == 'postgres' else 1]} NOT NULL,
  destino {TIPOS['txt'][0 if dialecto == 'postgres' else 1]},
  filas BIGINT, nuevas BIGINT, borradas BIGINT,
  cargado_en TIMESTAMPTZ,
  PRIMARY KEY (run_id, tabla)
);""")
    return "\n\n".join(partes) + "\n"


def _leer_origen(origen) -> pd.DataFrame | None:
    nombres = origen if isinstance(origen, list) else [origen]
    partes = []
    for n in nombres:
        for ruta in (STG_T / f"{n}.parquet", SALIDAS_ANALISIS / f"{n}.parquet"):
            if ruta.exists():
                partes.append(pd.read_parquet(ruta).dropna(axis=1, how="all"))  # preparar() repone las columnas
                break
    return pd.concat(partes, ignore_index=True) if partes else None


def preparar(nombre: str) -> pd.DataFrame | None:
    """DataFrame listo para cargar: solo las columnas declaradas, tipos coherentes y clave válida."""
    t = TABLAS[nombre]
    df = _leer_origen(t["origen"])
    if df is None:
        return None
    df = df.reindex(columns=list(t["columnas"]))
    for c, tp in t["columnas"].items():
        if tp == "int":
            df[c] = pd.to_numeric(df[c], errors="coerce").round().astype("Int64")
        elif tp == "num":
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
        elif tp == "bool":
            df[c] = df[c].astype("boolean")
        else:
            df[c] = df[c].astype("string")
    # claves: los nulos de texto se guardan como '' (una PK no admite NULL); los numéricos como 0
    for c in t["clave"]:
        if t["columnas"][c] == "txt":
            df[c] = df[c].fillna("")
        elif df[c].isna().any():
            df[c] = df[c].fillna(0)
    dup = df.duplicated(t["clave"]).sum()
    if dup:
        raise ValueError(f"{nombre}: {dup} filas con la clave {t['clave']} duplicada")
    return df.reset_index(drop=True)
