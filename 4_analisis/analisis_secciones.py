"""Peso y evolución de las secciones (consejerías) en dos vistas y con/sin fondos MRR / REACT-EU.

    python 4_analisis/analisis_secciones.py [--fuente local|supabase] [--anio-actual 2027]

Independiente: lee fact_presupuesto, fact_seccion_estructura, fondos_extraordinarios, dim_seccion y dim_anio.
Vistas (§5.3.2):
  organica          la sección tal como se publicó (id_estable del crosswalk de secciones)
  estructura_<T>    cada año expresado en las consejerías del último año (retroproyección por familias)
incluye_mrr = no: variante orgánica sin los servicios MRR / REACT-EU (decisión 5; solo aislables por sección).
Salidas en 4_analisis/salidas/secciones/.
"""
import sys

import pandas as pd

import _informes as inf
import _metricas as m
from _lectura import ahora, argumentos, cfg, ensamblar, escribir_salidas, leer, panel, recortar

CONSEJERIAS, NO_DEPT = "Consejerías", "Secciones no departamentales"


def meta_organica(datos, no_dept: dict) -> pd.DataFrame:
    d = datos.dims["seccion"].sort_values("anio_hasta").drop_duplicates("id_estable", keep="last")
    grupo = d.codigo.map(lambda c: NO_DEPT if c in no_dept else CONSEJERIAS)
    return pd.DataFrame({"id": d.id_estable, "etiqueta": d.denominacion_std + " (" + d.codigo + ")", "nivel": 1,
                         "padre_id": grupo, "padre_etiqueta": grupo, "ruta_jerarquia": grupo,
                         "comparabilidad": d.comparabilidad, "concepto_ced": None})


def panel_estructura(datos) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    e = datos.seccion_estructura
    vista = e.vista.iloc[0]
    g = e.groupby(["seccion_destino", "anio"], as_index=False)[["importe_corriente", "importe_constante"]].sum()
    partes = [g.rename(columns={"seccion_destino": "id", col: "importe"})[["id", "anio", "importe"]].assign(precios=pr)
              for pr, col in (("corrientes", "importe_corriente"), ("constantes", "importe_constante"))]
    etiquetas = e.drop_duplicates("seccion_destino").set_index("seccion_destino").denominacion_destino
    return pd.concat(partes, ignore_index=True), etiquetas, vista


def panel_sin_mrr(datos, p_org: pd.DataFrame) -> pd.DataFrame:
    """Orgánica menos los servicios MRR / REACT-EU de cada sección (sin ajustado: solo métricas de nivel)."""
    f = datos.fondos[datos.fondos.serie_oficial]
    secc = datos.fact[datos.fact.serie_oficial & (datos.fact.tabla == "secciones") & (datos.fact.version_importe == "inicial")]
    id_de = dict(zip(zip(secc.anio_presupuesto, secc.codigo), secc.id_estable))
    f = f.assign(id=[id_de.get((a, c)) for a, c in zip(f.anio_presupuesto, f.codigo_padre)])
    fc = f.groupby(["id", "anio_presupuesto"]).importe_corriente.sum()
    defl = datos.dim_anio.set_index("anio").deflactor
    q = p_org.drop(columns=["ajustado"]).copy()
    resta = [fc.get((i, a), 0.0) * (1 if pr == "corrientes" else defl[a]) for i, a, pr in zip(q.id, q.anio, q.precios)]
    q["importe"] = q.importe - resta
    return q


def main() -> int:
    a = argumentos(__doc__.split("\n")[0])
    datos = recortar(leer(a.fuente, a.confirmar_produccion), a.anio_actual)
    c = cfg()
    no_dept = c["secciones_no_departamentales"]
    meta_o = meta_organica(datos, no_dept)
    grupo_de = dict(zip(meta_o.id, meta_o.padre_id))
    p_org = panel(datos.fact, "secciones")
    p_org = p_org.assign(padre=p_org.id.map(grupo_de))
    p_est, et_est, vista_est = panel_estructura(datos)
    p_est = p_est.assign(padre=p_est.id.map(lambda s: NO_DEPT if s in no_dept else CONSEJERIAS))
    grupo_est = p_est.drop_duplicates("id").set_index("id").padre
    meta_e = pd.DataFrame({"id": et_est.index, "etiqueta": et_est.values + " (" + et_est.index + ")", "nivel": 1,
                           "padre_id": grupo_est.reindex(et_est.index).values, "padre_etiqueta": grupo_est.reindex(et_est.index).values,
                           "ruta_jerarquia": grupo_est.reindex(et_est.index).values, "comparabilidad": "retroproyectada",
                           "concepto_ced": None})
    p_sin = panel_sin_mrr(datos, p_org)

    t_org = ensamblar(m.calcular_todo(p_org, datos.dim_anio, c), meta_o, "seccion", "organica", datos)
    t_est = ensamblar(m.calcular_todo(p_est, datos.dim_anio, c), meta_e, "seccion", vista_est, datos)
    t_sin = ensamblar(m.calcular_todo(p_sin, datos.dim_anio, c), meta_o, "seccion", "organica", datos, incluye_mrr="no")
    tidy = pd.concat([t_org, t_est, t_sin], ignore_index=True)

    anios = sorted(p_org.anio.unique())
    ventanas = m.ventanas_desde(datos.dim_anio, anios)
    va = next(v for v in ventanas if v["id"] == c["ventana_actual"])
    ultimo = anios[-1]

    # Por CÓDIGO (no por id_estable): los enlaces de secciones pendientes de revisión cortan los id en 2024.
    of_s = datos.fact[datos.fact.serie_oficial & (datos.fact.tabla == "secciones")]
    ini = of_s[of_s.version_importe == "inicial"].set_index(["anio_presupuesto", "codigo"]).importe_corriente
    aj = of_s[of_s.version_importe == "ajustado"].set_index(["anio_presupuesto", "codigo"]).importe_corriente
    nombre = of_s.drop_duplicates(["anio_presupuesto", "codigo"]).set_index(["anio_presupuesto", "codigo"]).denominacion_raw

    # reorganización del gobierno actual: ajustado 2023 en el tomo 2024 − inicial 2023 de la sección con el mismo código
    anio_reorg = va["base"] + 1
    filas = []
    for (a, cod), v in aj.items():
        if a == anio_reorg:
            filas.append({"cod": cod, "v": v - ini.get((a - 1, cod), 0.0)})
    re24 = pd.DataFrame(filas).sort_values("v")
    re24 = re24[re24.v.abs() >= 1e6]
    t_re = pd.DataFrame({"Sección": [f"{nombre[(anio_reorg, c)]} ({c})" for c in re24.cod],
                         f"Inicial {anio_reorg - 1}, mismo código (M€)": [inf.meur(ini.get((anio_reorg - 1, c), 0.0)) for c in re24.cod],
                         f"Ajustado {anio_reorg - 1} en el tomo {anio_reorg} (M€)": [inf.meur(aj[(anio_reorg, c)]) for c in re24.cod],
                         "Efecto reestructuración (M€)": re24.v.map(inf.meur).values})

    # distancia entre vistas en el año base: estructura actual retroproyectada frente a la sección del mismo código
    imp_e = t_est[(t_est.metrica == "importe") & (t_est.precios == "corrientes") & (t_est.anio == va["base"])].set_index("id_estable").valor
    cods = sorted(c for (a, c) in ini.index if a == ultimo)
    t_dist = pd.DataFrame([{"Consejería actual": f"{et_est.get(c, c)} ({c})",
                            f"Mismo código en {va['base']} (M€)": inf.meur(ini.get((va["base"], c), float("nan"))),
                            f"Nombre en {va['base']}": nombre.get((va["base"], c), "— (no existía)"),
                            f"Estructura {ultimo} retroproyectada (M€)": inf.meur(imp_e.get(c, float("nan"))),
                            "Diferencia (M€)": inf.meur(imp_e.get(c, float("nan")) - ini.get((va["base"], c), 0.0))}
                           for c in cods])

    # no departamentales y fondos MRR
    pn = t_org[(t_org.metrica == "peso_total_pct") & (t_org.precios == "corrientes") & (t_org.padre_id == NO_DEPT)]
    t_nd = pn.pivot_table(index="etiqueta", columns="anio", values="valor").round(1)
    t_nd = t_nd[[x for x in (anios[0], 2019, 2023, ultimo) if x in t_nd.columns]].reset_index()
    fon = datos.fondos[datos.fondos.serie_oficial].groupby("anio_presupuesto").importe_corriente.sum()
    tot = p_org[p_org.precios == "corrientes"].groupby("anio").importe.sum()
    t_mrr = pd.DataFrame({"Año": fon.index, "MRR / REACT-EU (M€)": fon.map(inf.meur).values,
                          "% del total": (100 * fon / tot.reindex(fon.index)).map(inf.num).values})
    tot_sin = t_sin[(t_sin.id_estable == "__total__") & (t_sin.metrica == "var_pct_ventana") & (t_sin.precios == "constantes")]
    tot_con = t_org[(t_org.id_estable == "__total__") & (t_org.metrica == "var_pct_ventana") & (t_org.precios == "constantes")]
    t_var = pd.DataFrame({"Ventana": tot_con.ventana, "Con MRR (%)": tot_con.valor.map(inf.num).values,
                          "Sin MRR (%)": tot_sin.set_index("ventana").valor.reindex(tot_con.ventana).map(inf.num).values})

    insights = [
        inf.prioridades(t_est, va, c["top_n"]),
        (f"Vista competencial frente a orgánica ({va['base']})", "verificado",
         f"Cuánto tenía en {va['base']} lo que hoy gestiona cada consejería (estructura {ultimo} retroproyectada) frente a la "
         "sección que entonces tenía el mismo código. La diferencia es el **efecto reestructuración** acumulado: un "
         "mismo código puede ser otra consejería.\n\n" + inf.tabla_md(t_dist)),
        (f"Reorganización de {anio_reorg}: competencias que entran y salen por sección", "verificado",
         f"Ajustado {anio_reorg - 1} en el tomo {anio_reorg} − inicial {anio_reorg - 1} de la sección con el mismo código "
         "(≥ 1 M€ en valor absoluto). Positivo: la sección recibe competencias; negativo: las cede.\n\n" + inf.tabla_md(t_re)),
        inf.ruptura(t_est, c["ventana_actual"], c["ventana_anterior"], c["top_n"]),
        inf.real_vs_nominal(t_est, ventanas),
        ("Secciones no departamentales (dinámica contable)", "verificado",
         "Peso (%) de Deuda Pública, Diversas Consejerías, Transferencias a Corporaciones Locales y Parlamento.\n\n" + inf.tabla_md(t_nd)),
        ("Fondos MRR / REACT-EU (servicios 70-71 de la tabla 2.2)", "verificado",
         "La Ley 2021 no los etiqueta; desde 2022 se aíslan por sección.\n\n" + inf.tabla_md(t_mrr) +
         "\nCrecimiento real del total con y sin estos fondos:\n\n" + inf.tabla_md(t_var)),
        inf.concentracion(t_est, anios),
        inf.saltos(t_org, 2024),
        inf.preelectoral(t_est, c["top_n"]),
    ]
    md = inf.documento("Insights · Secciones presupuestarias",
                       f"Generado {ahora()} por `analisis_secciones.py`. Serie oficial {anios[0]}-{ultimo}; tabla 2.1 "
                       f"(caps. 1-8). Vista competencial: `{vista_est}`.", insights)
    pe = t_est[(t_est.metrica == "importe") & (t_est.anio == ultimo) & (t_est.precios == "corrientes") & (t_est.id_estable != "__total__")]
    pw = t_est[(t_est.metrica == "peso_total_pct") & (t_est.anio == ultimo) & (t_est.precios == "corrientes")].set_index("id_estable").valor
    t1 = pd.DataFrame({"Sección": pe.etiqueta, "Grupo": pe.padre_etiqueta, f"Importe {ultimo} (M€)": (pe.valor / 1e6).round(1),
                       "Peso (%)": pe.id_estable.map(pw).round(2)}).sort_values("Peso (%)", ascending=False)
    tablas = [(f"Peso de las secciones en {ultimo}", t1, "Presupuesto inicial, caps. 1-8. Fuente: Tomo 3, tabla 2.1. Elaboración propia."),
              (f"Vista competencial frente a orgánica en {va['base']}", t_dist,
               f"Estructura de consejerías de {ultimo} retroproyectada con la tabla 2.16. Elaboración propia."),
              ("Fondos MRR / REACT-EU por año", t_mrr, "Servicios etiquetados en la tabla 2.2. Elaboración propia.")]
    escribir_salidas("secciones", tidy, md, tablas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
