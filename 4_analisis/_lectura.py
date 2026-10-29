"""Lectura de la carga (DuckDB local o Supabase) y paneles por dimensión. Sin cálculo de métricas."""
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

ANALISIS = Path(__file__).resolve().parent
RAIZ = ANALISIS.parent
SALIDAS = ANALISIS / "salidas"
sys.path.insert(0, str(RAIZ / "3_carga"))
sys.path.insert(0, str(RAIZ / "1_extraccion"))

from _comun.rutas import CONFIG, ahora, log_evento  # noqa: E402,F401
from modelo_bd import ESQUEMA, TABLAS  # noqa: E402

BD_LOCAL = RAIZ / "3_carga" / "local" / "presupuestos.duckdb"
COLUMNAS_ANA = list(TABLAS["ana_metricas"]["columnas"])


@dataclass
class Datos:
    fact: pd.DataFrame
    dims: dict
    dim_anio: pd.DataFrame
    seccion_estructura: pd.DataFrame
    fondos: pd.DataFrame
    xwalk: pd.DataFrame


def cfg() -> dict:
    return yaml.safe_load((CONFIG / "analisis.yml").read_text(encoding="utf-8"))


def leer(fuente: str = "local", confirmar: bool = False) -> Datos:
    tablas = ["fact_presupuesto", "dim_anio", "fact_seccion_estructura", "fondos_extraordinarios", "xwalk",
              *[f"dim_{d}" for d in ("seccion", "funcion", "subfuncion", "programa", "ente")]]
    if fuente == "local":
        import duckdb
        if not BD_LOCAL.exists():
            raise SystemExit("No existe la base local: ejecuta 3_carga/local/cargar_local.py")
        with duckdb.connect(str(BD_LOCAL), read_only=True) as c:
            t = {n: c.execute(f"SELECT * FROM {ESQUEMA}.{n}").df() for n in tablas}
    else:
        from dotenv import load_dotenv
        import psycopg
        from _sincronizar import es_remoto
        load_dotenv(RAIZ / ".env")
        url = os.environ["SUPABASE_DB_URL"]
        if es_remoto(url) and not confirmar:
            raise SystemExit("Fuente remota: repite con --confirmar-produccion para leer de Supabase.")
        t = {}
        with psycopg.connect(url) as c, c.cursor() as cur:
            for n in tablas:
                cur.execute(f"SELECT * FROM {ESQUEMA}.{n}")
                t[n] = pd.DataFrame(cur.fetchall(), columns=[d.name for d in cur.description])
    dims = {d: t[f"dim_{d}"] for d in ("seccion", "funcion", "subfuncion", "programa", "ente")}
    return Datos(t["fact_presupuesto"], dims, t["dim_anio"], t["fact_seccion_estructura"],
                 t["fondos_extraordinarios"], t["xwalk"])


def fase_por_anio(fact: pd.DataFrame) -> dict:
    of = fact[fact.serie_oficial]
    return of.groupby("anio_presupuesto").fase.first().to_dict()


def panel(fact: pd.DataFrame, tabla: str, por: str = "id_estable") -> pd.DataFrame:
    """Panel largo (id, anio, precios, importe, ajustado) de la serie oficial de una tabla comparativa.

    importe = presupuesto inicial del año; ajustado = el año anterior reexpresado en el tomo de ese año.
    `por` agrupa (id_estable, familia_id, codigo…); los importes se suman dentro de cada grupo.
    """
    t = fact[fact.serie_oficial & (fact.tabla == tabla) & (fact.capitulo == "TOTAL")]
    partes = []
    for precios, col in (("corrientes", "importe_corriente"), ("constantes", "importe_constante")):
        ini = t[t.version_importe == "inicial"].groupby([por, "anio_presupuesto"])[col].sum().rename("importe")
        aj = t[t.version_importe == "ajustado"].groupby([por, "anio_presupuesto"])[col].sum().rename("ajustado")
        d = pd.concat([ini, aj], axis=1).reset_index().rename(columns={por: "id", "anio_presupuesto": "anio"})
        d = d[d.importe.notna()]
        d["precios"] = precios
        partes.append(d)
    out = pd.concat(partes, ignore_index=True)
    out["anio"] = out.anio.astype(int)
    return out


def ensamblar(metr: pd.DataFrame, meta: pd.DataFrame, dimension: str, vista: str, datos: Datos,
              incluye_mrr: str = "si") -> pd.DataFrame:
    """Une métricas con la descripción de cada unidad y deja el esquema de ana_metricas (§7.1).

    meta: id, etiqueta, nivel, padre_id, padre_etiqueta, ruta_jerarquia, comparabilidad, concepto_ced
    """
    fases = fase_por_anio(datos.fact)
    est_ipc = datos.dim_anio.set_index("anio").ipc_estatus.to_dict()
    d = metr.merge(meta, on="id", how="left")
    d.loc[d.id == "__total__", ["etiqueta", "nivel"]] = ["Total", 0]
    d["dimension"], d["vista"], d["incluye_mrr"] = dimension, vista, incluye_mrr
    d["fase"] = d.anio.map(fases)
    d["estatus_dato"] = "verificado"
    d.loc[(d.precios == "constantes") & (d.anio.map(est_ipc) == "estimacion"), "estatus_dato"] = "estimacion"
    d = d.rename(columns={"id": "id_estable"})
    return d.reindex(columns=COLUMNAS_ANA)


def argumentos(descripcion: str):
    import argparse
    ap = argparse.ArgumentParser(description=descripcion)
    ap.add_argument("--fuente", choices=["local", "supabase"], default="local")
    ap.add_argument("--confirmar-produccion", action="store_true")
    ap.add_argument("--anio-actual", type=int, help="último año a analizar (por defecto, el último con datos)")
    return ap.parse_args()


def recortar(datos: Datos, anio_actual: int | None) -> Datos:
    if anio_actual:
        datos.fact = datos.fact[datos.fact.anio_presupuesto <= anio_actual]
        datos.seccion_estructura = datos.seccion_estructura[datos.seccion_estructura.anio <= anio_actual]
    return datos


def agrupar(p: pd.DataFrame, mapa: dict) -> pd.DataFrame:
    """Suma un panel en grupos (id → grupo)."""
    q = p.assign(id=p.id.map(mapa))
    return q.groupby(["id", "anio", "precios"], as_index=False)[["importe", "ajustado"]].sum(min_count=1)


def escribir_salidas(dim: str, tidy: pd.DataFrame, md: str, tablas: list[tuple]) -> None:
    from _informes import escribir_xlsx
    carpeta = SALIDAS / dim
    carpeta.mkdir(parents=True, exist_ok=True)
    tidy.to_csv(carpeta / f"ana_{dim}.csv", index=False)
    tidy.to_parquet(SALIDAS / f"ana_{dim}.parquet", index=False)   # lo carga 3_carga (--que analisis)
    (carpeta / f"insights_{dim}.md").write_text(md, encoding="utf-8")
    escribir_xlsx(carpeta / f"tablas_{dim}.xlsx", tablas)
    log_evento(f"analisis_{dim}", filas=len(tidy))
    print(f"{dim}: {len(tidy):,} filas tidy · {tidy.id_estable.nunique()} unidades · "
          f"salidas/{dim}/ (ana_{dim}.csv, insights_{dim}.md, tablas_{dim}.xlsx)")
