"""Crosswalks efectivos → identificadores estables, familias, dimensiones y tabla de hechos.

    python 2_transformacion/construir_modelo.py

Salidas (2_transformacion/staging/):
  dim_<dim>.parquet          una fila por (id_estable, código): vigencia, familia, comparabilidad, concepto_ced
  fact_presupuesto.parquet   hechos con id_estable, familia y € constantes (base 2025)

id_estable: cadena de enlaces de continuidad (identico, renombrado, recodificado) 1:1 entre años.
Si una unidad tiene varios sucesores, la cadena sigue por el del mismo código (o el de mayor score);
los demás abren un id nuevo dentro de la misma familia.
familia_id: componente conexa del grafo de TODOS los enlaces aceptados (incluidas divisiones y fusiones).
comparabilidad (§5.3.1, paso 5):
  continua    el id cubre todos los años de la serie oficial
  pendiente   el id tiene un enlace en revisión sin decidir
  familia     solo es comparable agregando su familia, que sí cubre toda la serie
  subfuncion  nace con importe reexpresado (> 0) sin origen identificado: comparar a nivel agregado
  parcial     nace después del primer año o muere antes del último (programa nuevo / extinguido)
"""
import sys

import networkx as nx
import pandas as pd
import yaml

from _emparejar import CONTINUIDAD, unidades
from _tcomun import DIMENSIONES_XWALK, PREFIJO_ID, cfg, guardar, leer, log_evento

ACEPTADOS = {"auto", "validado"}


def asignar_ids(u: pd.DataFrame, ef: pd.DataFrame, dim: str) -> tuple[dict, dict, set]:
    """{(año, código): id_estable}, {(año, código): familia_id}, nodos con enlaces pendientes."""
    ok = ef[ef.estado_final.isin(ACEPTADOS) & ef.codigo_origen.notna() & ef.codigo_destino.notna()].copy()
    ok["origen"] = list(zip(ok.anio_origen.astype(int), ok.codigo_origen))
    ok["destino"] = list(zip(ok.anio_destino.astype(int), ok.codigo_destino))
    ok["score"] = ok.score.fillna(1.0)
    cont = ok[ok.tipo_enlace.isin(CONTINUIDAD)]

    def preferido(g: pd.DataFrame, lado: str, codigo: str):
        mismo = g[g[f"codigo_{lado}"] == codigo]
        return (mismo if len(mismo) else g).sort_values("score", ascending=False).iloc[0]

    sucesor = {o: preferido(g, "destino", o[1])["destino"] for o, g in cont.groupby("origen")}
    predecesor = {d: preferido(g, "origen", d[1])["origen"] for d, g in cont.groupby("destino")}

    ids = {}
    for a, c in sorted(zip(u.anio_presupuesto, u.codigo)):
        nodo = (int(a), c)
        pred = predecesor.get(nodo)
        if pred is not None and sucesor.get(pred) == nodo and pred in ids:
            ids[nodo] = ids[pred]
        else:
            ids[nodo] = f"{PREFIJO_ID[dim]}{c}_{a}"

    g = nx.Graph()
    g.add_nodes_from(ids)
    g.add_edges_from(zip(ok.origen, ok.destino))
    familias = {}
    for comp in nx.connected_components(g):
        fam = "FAM-" + min(ids[n] for n in comp if n in ids)
        familias.update({n: fam for n in comp})

    pend = ef[ef.estado_final == "pendiente"]
    pendientes = {(int(a), c) for a, c in zip(pend.anio_origen, pend.codigo_origen) if pd.notna(a)} | \
                 {(int(a), c) for a, c in zip(pend.anio_destino, pend.codigo_destino) if pd.notna(a)}
    return ids, familias, pendientes


def concepto_ced(codigo: str, nombre_norm: str, conceptos: dict) -> str | None:
    """Misma prioridad que Canarias en Datos: código exacto, prefijo con *, palabra clave."""
    for nivel in ("exacto", "prefijo", "keyword"):
        for concepto, regla in conceptos.items():
            cods = [str(x) for x in regla.get("codigos", [])]
            if nivel == "exacto" and codigo in cods:
                return concepto
            if nivel == "prefijo" and any(x.endswith("*") and codigo.startswith(x[:-1]) for x in cods):
                return concepto
            if nivel == "keyword" and any(f" {k} " in f" {nombre_norm} " for k in
                                          (" ".join(str(w).lower().split()) for w in regla.get("keywords", []))):
                return concepto
    return None


def construir_dimension(u: pd.DataFrame, ids: dict, familias: dict, pendientes: set, ef: pd.DataFrame,
                        dim: str, conceptos: dict) -> pd.DataFrame:
    anios = sorted(u.anio_presupuesto.unique())
    u = u.copy()
    u["nodo"] = list(zip(u.anio_presupuesto.astype(int), u.codigo))
    u["id_estable"] = u.nodo.map(ids)
    u["familia_id"] = u.nodo.map(familias)
    sin_origen = ef[ef.tipo_enlace == "nuevo_sin_origen"]
    nodos_sin_origen = set(zip(sin_origen.anio_destino.astype(int), sin_origen.codigo_destino))

    comp = {}
    for idn, g in u.groupby("id_estable"):
        fam_nodos = u[u.familia_id == g.familia_id.iloc[0]]
        if g.anio_presupuesto.min() == anios[0] and g.anio_presupuesto.max() == anios[-1]:
            comp[idn] = "continua"
        elif set(g.nodo) & pendientes:
            comp[idn] = "pendiente"
        elif (fam_nodos.id_estable.nunique() > 1 and fam_nodos.anio_presupuesto.min() == anios[0]
              and fam_nodos.anio_presupuesto.max() == anios[-1]):
            comp[idn] = "familia"
        elif g.sort_values("anio_presupuesto").nodo.iloc[0] in nodos_sin_origen:
            comp[idn] = "subfuncion" if dim == "programa" else "sin_enlace"
        else:
            comp[idn] = "parcial"

    ultima = u.sort_values("anio_presupuesto").groupby("id_estable").denominacion_raw.last()
    filas = []
    for (idn, cod), g in u.groupby(["id_estable", "codigo"]):
        g = g.sort_values("anio_presupuesto")
        activos = g[g.inicial > 0]
        filas.append({
            "dimension": dim, "id_estable": idn, "codigo": cod,
            "denominacion_raw": g.denominacion_raw.iloc[-1], "denominacion_std": ultima[idn],
            "anio_desde": int(g.anio_presupuesto.min()), "anio_hasta": int(g.anio_presupuesto.max()),
            "anio_hasta_activo": int(activos.anio_presupuesto.max()) if len(activos) else None,
            "padre_codigo": g.grupo.iloc[-1] if "grupo" in g and g.grupo.notna().all() else None,
            "familia_id": g.familia_id.iloc[-1], "comparabilidad": comp[idn],
            "concepto_ced": concepto_ced(cod, g.nombre_norm.iloc[-1], conceptos) if dim in ("programa", "subfuncion") else None,
            "n_codigos_id": u[u.id_estable == idn].codigo.nunique(),
        })
    return pd.DataFrame(filas)


def main() -> int:
    fact = leer("fact_base")
    dim_anio = leer("dim_anio")
    conceptos = yaml.safe_load(open(cfg()["ced"]["correspondencias"], encoding="utf-8"))["conceptos"]
    nodo_id, nodo_fam, dims = {}, {}, {}
    for dim in DIMENSIONES_XWALK:
        u = unidades(fact, dim)
        ef = leer(f"xwalk_{dim}")
        ids, familias, pendientes = asignar_ids(u, ef, dim)
        d = construir_dimension(u, ids, familias, pendientes, ef, dim, conceptos)
        guardar(d, f"dim_{dim}")
        dims[dim] = d
        nodo_id[dim], nodo_fam[dim] = ids, familias
        por_comp = d.drop_duplicates("id_estable").comparabilidad.value_counts().to_dict()
        print(f"{dim:11s} ids={d.id_estable.nunique():4d} familias={d.familia_id.nunique():4d} · {por_comp}")
        log_evento("construir_modelo", dimension=dim, ids=int(d.id_estable.nunique()), comparabilidad=por_comp)

    # --- tabla de hechos
    f = fact.copy()
    clave = list(zip(f.anio_presupuesto.astype(int), f.codigo_unidad))
    f["id_estable"] = None
    f["familia_id"] = None
    f["id_padre"] = None
    for dim in DIMENSIONES_XWALK:
        m = (f.dimension == dim).to_numpy()
        f.loc[m, "id_estable"] = [nodo_id[dim].get(k) for k, mm in zip(clave, m) if mm]
        f.loc[m, "familia_id"] = [nodo_fam[dim].get(k) for k, mm in zip(clave, m) if mm]
    # tablas cruzadas: id del programa y de la sección / ente padre
    m = (f.dimension == "seccion_programa").to_numpy()
    f.loc[m, "id_estable"] = [nodo_id["programa"].get(k) for k, mm in zip(clave, m) if mm]
    f.loc[m, "familia_id"] = [nodo_fam["programa"].get(k) for k, mm in zip(clave, m) if mm]
    clave_padre = list(zip(f.anio_presupuesto.astype(int), f.codigo_padre))
    for dim_hija, dim_padre in (("seccion_programa", "seccion"), ("servicio", "seccion"), ("ente_programa", "ente")):
        m = (f.dimension == dim_hija).to_numpy()
        f.loc[m, "id_padre"] = [nodo_id[dim_padre].get(k) for k, mm in zip(clave_padre, m) if mm]
    # deflactación: el importe se refiere a `anio` (t-1 en los ajustados)
    da = dim_anio.set_index("anio")
    f["deflactor"] = f.anio.map(da.deflactor)
    f["importe_constante"] = f.importe_corriente * f.deflactor
    f["precios_base"] = int(cfg()["deflactor"]["base"])
    f["estatus_dato"] = "verificado"
    f["estatus_constante"] = f.anio.map(da.ipc_estatus)
    guardar(f, "fact_presupuesto")
    print(f"fact_presupuesto: {len(f):,} filas; sin id en dimensiones con crosswalk (serie oficial): "
          f"{int((f.serie_oficial & f.dimension.isin(DIMENSIONES_XWALK) & f.id_estable.isna()).sum())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
