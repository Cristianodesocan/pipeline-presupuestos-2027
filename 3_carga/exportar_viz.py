"""Exporta las vistas v_viz_* a 5_visualizacion/data/viz_*.csv (los CSV que lee la web D3).

    python 3_carga/exportar_viz.py                    # desde DuckDB local (por defecto)
    python 3_carga/exportar_viz.py --fuente supabase  # desde Supabase (versión final publicada)

Ambas fuentes usan las mismas vistas (vistas_viz.sql), así que el CSV es idéntico salvo diferencias de carga.
Orden estable de filas para que los cambios se puedan revisar con git diff.
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _sincronizar import VISTAS, es_remoto  # noqa: E402
from modelo_bd import ESQUEMA, RAIZ, log_evento  # noqa: E402

DATA = RAIZ / "5_visualizacion" / "data"
BD_LOCAL = RAIZ / "3_carga" / "local" / "presupuestos.duckdb"
ORDEN = {"v_viz_treemap": ["dimension", "vista", "precios", "anio", "id_estable"],
         "v_viz_series": ["dimension", "vista", "precios", "id_estable", "anio"],
         "v_viz_meta": ["tipo", "id"]}


def leer_vistas(fuente: str, confirmar: bool) -> dict[str, pd.DataFrame]:
    if fuente == "local":
        import duckdb
        with duckdb.connect(str(BD_LOCAL), read_only=True) as c:
            return {v: c.execute(f"SELECT * FROM {ESQUEMA}.{v}").df() for v in VISTAS}
    from dotenv import load_dotenv
    import psycopg
    load_dotenv(RAIZ / ".env")
    url = os.environ["SUPABASE_DB_URL"]
    if es_remoto(url) and not confirmar:
        raise SystemExit("Fuente remota: repite con --confirmar-produccion para leer de Supabase.")
    out = {}
    with psycopg.connect(url) as c, c.cursor() as cur:
        for v in VISTAS:
            cur.execute(f"SELECT * FROM {ESQUEMA}.{v}")
            out[v] = pd.DataFrame(cur.fetchall(), columns=[d.name for d in cur.description])
    return out


def normalizar_tipos(df: pd.DataFrame) -> pd.DataFrame:
    """Mismo CSV desde DuckDB y PostgreSQL: años enteros aunque haya nulos; decimales como float."""
    for c in df.columns:
        if c in ("anio", "inicio", "fin"):
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
        elif df[c].dtype == object and df[c].map(lambda x: x is None or hasattr(x, "as_integer_ratio")).all() \
                and df[c].notna().any() and not df[c].map(lambda x: isinstance(x, bool)).any():
            df[c] = pd.to_numeric(df[c], errors="coerce")   # Decimal de PostgreSQL → float
    return df


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fuente", choices=["local", "supabase"], default="local")
    ap.add_argument("--confirmar-produccion", action="store_true")
    args = ap.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    resumen = {}
    for vista, df in leer_vistas(args.fuente, args.confirmar_produccion).items():
        df = normalizar_tipos(df)
        df = df.sort_values(ORDEN[vista], kind="stable") if len(df) else df
        destino = DATA / f"{vista.replace('v_', '', 1)}.csv"
        df.to_csv(destino, index=False)
        resumen[destino.name] = len(df)
        print(f"  {destino.relative_to(RAIZ)}: {len(df)} filas")
    if not resumen.get("viz_treemap.csv"):
        print("AVISO: viz_treemap y viz_series están vacías hasta que se cargue ana_metricas (fase 4).")
    log_evento("exportar_viz", fuente=args.fuente, filas=resumen)
    return 0


if __name__ == "__main__":
    sys.exit(main())
