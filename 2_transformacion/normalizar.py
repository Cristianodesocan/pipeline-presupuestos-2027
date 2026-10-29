"""Staging tidy de la extracción → hechos base normalizados y dimensión temporal.

    python 2_transformacion/normalizar.py

Salidas (2_transformacion/staging/):
  fact_base.parquet               importes en € de las filas de detalle, con su dimensión analítica
  dim_anio.parquet                IPC, deflactor (base 2025), población, PIB y ventana de gobierno por año
  fondos_extraordinarios.parquet  servicios MRR / REACT-EU (decisión 5), también en .csv

- Serie oficial: por cada año, la Ley si existe; si no, el Proyecto (2027 hasta que se apruebe).
- Las correcciones de config/correcciones_manuales.csv se aplican aquí y quedan en el log.
- Claves compuestas: seccion_programa = «SS|PPPP»; ente_programa = «ENTE|PPPP» (código del ente según 3.1).
"""
import sys

import pandas as pd
import yaml

from _tcomun import CONFIG, DIMENSIONES, EXTERNOS, STG, cfg, guardar, log_evento, normalizar_nombre
from _comun.staging import leer_staging


def serie_oficial(df: pd.DataFrame) -> pd.Series:
    fases = df.groupby("anio_presupuesto").fase.agg(set)
    elegida = {a: ("ley" if "ley" in f else "proyecto") for a, f in fases.items()}
    return df.fase == df.anio_presupuesto.map(elegida)


def codigos_ente_por_nombre(stg: pd.DataFrame) -> dict:
    """{(doc_id, nombre del ente en 3.2): código del ente en 3.1}, por nombre y, si no, por importe."""
    out = {}
    e31 = stg[(stg.tabla == "entes") & (stg.nivel == "detalle") & (stg.columna == "inicial")]
    t32 = stg[(stg.tabla == "entes_prog_cap") & (stg.nivel == "total") & (stg.columna == "total")]
    for did, g in t32.groupby("doc_id"):
        ref = e31[e31.doc_id == did]
        por_nombre = dict(zip(ref.denominacion_raw, ref.codigo))
        por_importe = dict(zip(ref.valor, ref.codigo))
        for ente, valor in zip(g.ente, g.valor):
            out[(did, ente)] = por_nombre.get(ente) or por_importe.get(valor)
    return out


def aplicar_correcciones(df: pd.DataFrame) -> pd.DataFrame:
    corr = pd.read_csv(CONFIG / "correcciones_manuales.csv", dtype={"codigo": str})
    for _, c in corr.iterrows():
        m = ((df.anio_presupuesto == c.anio_presupuesto) & (df.fase == c.fase) & (df.tabla == c.tabla)
             & (df.codigo == c.codigo) & (df.columna == c.columna))
        if m.sum() != 1:
            raise ValueError(f"Corrección sin destino único ({m.sum()} filas): {c.to_dict()}")
        log_evento("correccion_manual", **c.to_dict(), valor_original=df.loc[m, "importe_corriente"].iloc[0])
        df.loc[m, "importe_corriente"] = c.valor_corregido
    return df


def construir_fact_base(stg: pd.DataFrame) -> pd.DataFrame:
    eur = stg[(stg.unidad == "eur") & (stg.nivel == "detalle")].copy()
    eur["dimension"] = eur.tabla.map(DIMENSIONES)
    eur["codigo_unidad"] = eur.codigo
    # códigos compuestos de las tablas cruzadas
    spc = eur.tabla == "secc_prog_cap"
    eur.loc[spc, "codigo"] = eur.loc[spc, "codigo_padre"] + "|" + eur.loc[spc, "codigo_unidad"]
    epc = eur.tabla == "entes_prog_cap"
    mapa = codigos_ente_por_nombre(stg)
    ente_cod = [mapa.get((d, e)) for d, e in zip(eur.loc[epc, "doc_id"], eur.loc[epc, "ente"])]
    eur.loc[epc, "codigo_padre"] = ente_cod
    eur.loc[epc, "codigo"] = [f"{c}|{p}" for c, p in zip(ente_cod, eur.loc[epc, "codigo_unidad"])]
    # padre jerárquico de las dimensiones simples
    eur.loc[eur.dimension == "programa", "codigo_padre"] = eur.codigo.str[:3]
    eur.loc[eur.dimension == "subfuncion", "codigo_padre"] = eur.codigo.str[:2]
    eur.loc[eur.dimension == "servicio", "codigo_padre"] = eur.codigo.str[:2]
    eur.loc[eur.dimension == "funcion", "codigo_padre"] = eur.codigo.str[:1]

    patron = cfg()["fondos_extraordinarios"]["patron"]
    eur["es_fondo_extraordinario"] = (eur.dimension == "servicio") & eur.denominacion_raw.str.upper().str.contains(patron, regex=True)
    eur["nombre_norm"] = eur.denominacion_raw.map(normalizar_nombre)
    eur["serie_oficial"] = serie_oficial(eur)
    eur = eur.rename(columns={"valor": "importe_corriente", "anio_importe": "anio"})
    eur = aplicar_correcciones(eur)
    columnas = ["anio", "anio_presupuesto", "fase", "serie_oficial", "dimension", "tabla", "codigo", "codigo_unidad",
                "codigo_padre", "denominacion_raw", "nombre_norm", "capitulo", "version_importe", "perimetro",
                "importe_corriente", "es_fondo_extraordinario", "columna", "doc_id", "pagina", "orden"]
    return eur[columnas].reset_index(drop=True)


def construir_dim_anio() -> pd.DataFrame:
    ext = pd.read_csv(EXTERNOS / "externos_canarias.csv")
    base = cfg()["deflactor"]["base"]
    ipc_base = ext.loc[ext.anio == base, "ipc_media"].iloc[0]
    ext["deflactor"] = ipc_base / ext.ipc_media          # importe_constante = corriente × deflactor
    ext["deflactor_base"] = base
    leg = yaml.safe_load((CONFIG / "legislaturas.yml").read_text(encoding="utf-8"))["ventanas"]
    for v in leg:
        desde, hasta = v["presupuestos"]
        m = ext.anio.between(desde, hasta)
        ext.loc[m, "ventana"] = v["id"]
        ext.loc[m, "presidencia"] = v["presidencia"]
        ext.loc[m, "coalicion"] = v["coalicion"]
        ext.loc[m, "base_comparacion"] = v["base_comparacion"]
        ext.loc[m, "ventana_actual"] = bool(v.get("actual", False))
    return ext


def main() -> int:
    stg = leer_staging()
    if stg.empty:
        print("Staging de extracción vacío: ejecuta 1_extraccion/extraer_tomo3.py")
        return 1
    fact = construir_fact_base(stg)
    sin_ente = fact[(fact.dimension == "ente_programa") & fact.codigo_padre.isna()]
    if len(sin_ente):
        print(f"ERROR: {sin_ente.doc_id.nunique()} documentos con entes de 3.2 sin código en 3.1")
        return 1
    guardar(fact, "fact_base")
    dim_anio = construir_dim_anio()
    guardar(dim_anio, "dim_anio")

    fondos = fact[fact.es_fondo_extraordinario & (fact.version_importe == "inicial")]
    fondos = fondos[["anio_presupuesto", "fase", "serie_oficial", "codigo", "codigo_padre", "denominacion_raw", "importe_corriente", "pagina"]]
    guardar(fondos, "fondos_extraordinarios")
    fondos.to_csv(STG / "fondos_extraordinarios.csv", index=False)

    of = fact[fact.serie_oficial]
    print(f"fact_base: {len(fact):,} filas · {fact.doc_id.nunique()} documentos · serie oficial "
          f"{sorted(of.anio_presupuesto.unique())[0]}-{sorted(of.anio_presupuesto.unique())[-1]} "
          f"({', '.join(f'{a}:{f}' for a, f in of.groupby('anio_presupuesto').fase.first().items() if f != 'ley') or 'todo Ley'})")
    print(fact.groupby("dimension").size().to_string())
    print("Fondos extraordinarios (serie oficial, M€):",
          fondos[fondos.serie_oficial].groupby("anio_presupuesto").importe_corriente.sum().div(1e6).round(1).to_dict())
    log_evento("normalizar", filas=len(fact), fondos=len(fondos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
