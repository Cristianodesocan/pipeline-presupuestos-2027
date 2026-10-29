"""Carga en el entorno local: DuckDB (3_carga/local/presupuestos.duckdb) + espejo CSV (3_carga/local/csv/).

    python 3_carga/local/cargar_local.py                 # todo lo disponible
    python 3_carga/local/cargar_local.py --que base      # solo datos de la transformación
    python 3_carga/local/cargar_local.py --que analisis  # solo ana_metricas (tras 4_analisis)

Mismo esquema, clave y vistas que Supabase (modelo_bd.py, vistas_viz.sql). Es el destino por defecto
de los scripts de análisis: rápido, sin red y sin consumir cuota de Supabase.
"""
import argparse
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _sincronizar import VISTAS, aplicar_esquema, cargar  # noqa: E402
from modelo_bd import ESQUEMA, TABLAS, log_evento  # noqa: E402

LOCAL = Path(__file__).resolve().parent
BD = LOCAL / "presupuestos.duckdb"
CSV = LOCAL / "csv"


def exportar_csv(conn) -> int:
    CSV.mkdir(parents=True, exist_ok=True)
    n = 0
    for obj in [*TABLAS, "carga_registro", *VISTAS]:
        conn.execute(f"COPY (SELECT * FROM {ESQUEMA}.{obj}) TO '{CSV / (obj + '.csv')}' (HEADER, DELIMITER ',')")
        n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--que", choices=["base", "analisis", "todo"], default="todo")
    ap.add_argument("--bd", type=Path, default=BD, help="ruta de la base DuckDB (por defecto, la del proyecto)")
    args = ap.parse_args()
    conn = duckdb.connect(str(args.bd))
    try:
        conn.execute("BEGIN TRANSACTION")
        aplicar_esquema(conn, "duckdb")
        res = cargar(conn, "duckdb", "local", args.que)
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    for t, r in res["tablas"].items():
        print(f"  {t:24s} {r}")
    if args.bd == BD:
        print(f"CSV exportados: {exportar_csv(conn)} en {CSV.relative_to(LOCAL.parents[1])}/")
    conn.close()
    log_evento("cargar_local", run_id=res["run_id"], tablas=res["tablas"])
    print(f"run_id {res['run_id']} → {args.bd.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
