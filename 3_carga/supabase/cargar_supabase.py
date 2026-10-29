"""Carga en Supabase (PostgreSQL), esquema presupuestos_can.

    python 3_carga/supabase/cargar_supabase.py --escribir-esquema        # solo regenera esquema.sql (sin conexión)
    python 3_carga/supabase/cargar_supabase.py --solo-esquema            # aplica DDL + vistas + RLS
    python 3_carga/supabase/cargar_supabase.py                           # carga lo disponible
    python 3_carga/supabase/cargar_supabase.py --confirmar-produccion    # obligatorio si el destino no es localhost

Conexión: SUPABASE_DB_URL en .env (mismo nombre de variable que Canarias en Datos). Las credenciales
nunca van en el código ni en el repositorio. Por seguridad, contra un host remoto la carga se niega
sin --confirmar-produccion: así un ensayo contra un PostgreSQL local nunca toca producción.

Seguridad (diseño §6.1): RLS activado en todas las tablas y sin políticas para anon/authenticated;
solo las vistas v_viz_* tienen GRANT SELECT. Para exponer el esquema por la API REST hay que añadir
presupuestos_can a «Exposed schemas» en el panel de Supabase.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _sincronizar import aplicar_esquema, cargar, es_remoto, sql_seguridad_supabase, sql_vistas  # noqa: E402
from modelo_bd import RAIZ, ddl, log_evento  # noqa: E402

ESQUEMA_SQL = Path(__file__).resolve().parent / "esquema.sql"


def escribir_esquema() -> Path:
    cabecera = ("-- GENERADO por 3_carga/supabase/cargar_supabase.py --escribir-esquema a partir de modelo_bd.py\n"
                "-- y vistas_viz.sql. No editar a mano: cambia el modelo y regenera.\n\n")
    ESQUEMA_SQL.write_text(cabecera + ddl("postgres") + "\n" + sql_vistas() + "\n-- Seguridad (Supabase)\n"
                           + sql_seguridad_supabase(), encoding="utf-8")
    return ESQUEMA_SQL


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--que", choices=["base", "analisis", "todo"], default="todo")
    ap.add_argument("--escribir-esquema", action="store_true")
    ap.add_argument("--solo-esquema", action="store_true")
    ap.add_argument("--confirmar-produccion", action="store_true")
    ap.add_argument("--sin-seguridad", action="store_true", help="no aplica RLS/GRANT (PostgreSQL sin roles de Supabase)")
    args = ap.parse_args()

    ruta = escribir_esquema()
    print(f"Esquema escrito en {ruta.relative_to(RAIZ)}")
    if args.escribir_esquema:
        return 0

    from dotenv import load_dotenv
    import psycopg

    load_dotenv(RAIZ / ".env")
    url = os.environ.get("SUPABASE_DB_URL")
    if not url:
        print("Falta SUPABASE_DB_URL (copia .env.example a .env y rellénalo).")
        return 1
    if es_remoto(url) and not args.confirmar_produccion:
        print("El destino es remoto (producción). Repite con --confirmar-produccion si de verdad quieres cargar.")
        return 1
    destino = "supabase" if es_remoto(url) else "postgres_local"
    with psycopg.connect(url) as conn:          # una transacción: o se carga todo o nada
        aplicar_esquema(conn, "postgres", seguridad=not args.sin_seguridad)
        if args.solo_esquema:
            print("Esquema aplicado.")
            return 0
        res = cargar(conn, "postgres", destino, args.que)
    for t, r in res["tablas"].items():
        print(f"  {t:24s} {r}")
    log_evento("cargar_supabase", destino=destino, run_id=res["run_id"], tablas=res["tablas"])
    print(f"run_id {res['run_id']} → {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
