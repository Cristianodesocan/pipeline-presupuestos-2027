"""Peso y evolución de la clasificación funcional: área → función → subfunción (CAC 2015-…).

    python 4_analisis/analisis_funciones.py [--fuente local|supabase] [--anio-actual 2027]

Independiente: lee fact_presupuesto, dim_funcion, dim_subfuncion y dim_anio de la carga.
Salidas en 4_analisis/salidas/funciones/: ana_funciones.csv (tidy §7.1), insights_funciones.md, tablas_funciones.xlsx.
Perímetro: tablas 2.8 y 2.9 (caps. 1-8); la composición por capítulos usa 2.14 (caps. 1-9).
"""
import sys

import pandas as pd

import _informes as inf
import _metricas as m
from _lectura import agrupar, ahora, argumentos, cfg, ensamblar, escribir_salidas, leer, panel, recortar

CAPITULOS = {"1": "Personal", "2": "Bienes y servicios", "3": "Gastos financieros", "4": "Transferencias corrientes",
             "6": "Inversiones reales", "7": "Transferencias de capital", "8": "Activos financieros", "9": "Pasivos financieros"}
AREAS_SOCIALES = {"2", "3"}   # protección y promoción social · bienes públicos preferentes (sanidad, educación, cultura)


def metas(datos, c):
    areas = {k: v for k, v in c["areas_gasto"].items()}
    df = datos.dims["funcion"].drop_duplicates("id_estable")
    fun = pd.DataFrame({"id": df.id_estable, "etiqueta": df.denominacion_std, "nivel": 2,
                        "padre_id": "A" + df.codigo.str[0], "padre_etiqueta": df.codigo.str[0].map(areas),
                        "ruta_jerarquia": df.codigo.str[0].map(areas), "comparabilidad": df.comparabilidad,
                        "concepto_ced": None})
    id_fun = dict(zip(df.codigo, df.id_estable))
    et_fun = dict(zip(df.codigo, df.denominacion_std))
    ds = datos.dims["subfuncion"].drop_duplicates("id_estable")
    sub = pd.DataFrame({"id": ds.id_estable, "etiqueta": ds.denominacion_std, "nivel": 3,
                        "padre_id": ds.codigo.str[:2].map(id_fun), "padre_etiqueta": ds.codigo.str[:2].map(et_fun),
                        "ruta_jerarquia": ds.codigo.str[0].map(areas) + "|" + ds.codigo.str[:2].map(et_fun),
                        "comparabilidad": ds.comparabilidad, "concepto_ced": ds.concepto_ced})
    are = pd.DataFrame({"id": ["A" + k for k in areas], "etiqueta": list(areas.values()), "nivel": 1, "padre_id": None,
                        "padre_etiqueta": None, "ruta_jerarquia": "", "comparabilidad": "continua", "concepto_ced": None})
    return fun, sub, are, id_fun


def composicion_capitulos(fact, v: dict, id_area: dict) -> pd.DataFrame:
    """Insight 9: qué capítulos explican el cambio de cada área de gasto en la ventana (€ constantes, gasto no
    financiero: caps. 1-7 de la tabla 2.14; la amortización de deuda del cap. 9 distorsionaría las contribuciones)."""
    t = fact[fact.serie_oficial & (fact.tabla == "subfunciones_cap") & fact.capitulo.isin(list("1234567"))
             & fact.anio_presupuesto.isin([v["base"], v["fin"]])]
    t = t.assign(area=t.codigo.str[0])
    g = t.groupby(["area", "capitulo", "anio_presupuesto"]).importe_constante.sum().unstack().fillna(0)
    g["cambio"] = g[v["fin"]] - g[v["base"]]
    out = g.reset_index()
    out["Área"] = out.area.map(id_area)
    out["Capítulo"] = out.capitulo.map(lambda x: f"{x}. {CAPITULOS.get(x, x)}")
    tot = out.groupby("area").cambio.transform("sum")
    out["Contribución (%)"] = 100 * out.cambio / tot.where(tot != 0)
    return out[out.cambio.abs() >= 50_000]


def main() -> int:
    a = argumentos(__doc__.split("\n")[0])
    datos = recortar(leer(a.fuente, a.confirmar_produccion), a.anio_actual)
    c = cfg()
    fun, sub, are, id_fun = metas(datos, c)
    pf = datos.fact[datos.fact.tabla == "funciones"].drop_duplicates("id_estable").set_index("id_estable").codigo
    base_fun = panel(datos.fact, "funciones")
    p_fun = base_fun.assign(padre=base_fun.id.map(lambda i: "A" + pf[i][0]))
    p_sub = panel(datos.fact, "subfunciones")
    p_sub = p_sub.assign(padre=p_sub.id.map(dict(zip(sub.id, sub.padre_id))))
    p_are = agrupar(base_fun, {i: "A" + cod[0] for i, cod in pf.items()})

    tidy = pd.concat([
        ensamblar(m.calcular_todo(p_are, datos.dim_anio, c), are, "area", "individual", datos),
        ensamblar(m.calcular_todo(p_fun, datos.dim_anio, c), fun, "funcion", "individual", datos),
        ensamblar(m.calcular_todo(p_sub, datos.dim_anio, c), sub, "subfuncion", "individual", datos),
    ], ignore_index=True)

    anios = sorted(p_fun.anio.unique())
    ventanas = m.ventanas_desde(datos.dim_anio, anios)
    va = next(v for v in ventanas if v["id"] == c["ventana_actual"])
    tf = tidy[tidy.dimension == "funcion"]
    ta = tidy[tidy.dimension == "area"]

    # gasto social (áreas 2 y 3) frente al resto: peso por año
    peso_area = ta[(ta.metrica == "peso_total_pct") & (ta.precios == "corrientes")]
    social = peso_area[peso_area.id_estable.str[1].isin(AREAS_SOCIALES)].groupby("anio").valor.sum()
    t_social = pd.DataFrame({"Año": social.index, "Peso áreas sociales (%)": social.map(inf.num).values})
    comp = composicion_capitulos(datos.fact, va, c["areas_gasto"])
    t_comp = comp[["Área", "Capítulo", "cambio", "Contribución (%)"]].rename(columns={"cambio": "Cambio (M€ const.)"})
    t_comp["Cambio (M€ const.)"] = t_comp["Cambio (M€ const.)"].map(inf.meur)
    t_comp["Contribución (%)"] = t_comp["Contribución (%)"].map(inf.num)

    insights = [
        inf.prioridades(tf, va, c["top_n"]),
        inf.ruptura(tf, c["ventana_actual"], c["ventana_anterior"], c["top_n"]),
        inf.real_vs_nominal(tf, ventanas),
        inf.elasticas(tf, va, c["top_n"]),
        inf.concentracion(tf, anios),
        ("Gasto social (áreas 2 y 3) frente al resto", "verificado",
         "Peso conjunto de *Actuaciones de protección y promoción social* y *Producción de bienes públicos de carácter "
         "preferente* (sanidad, educación, cultura) sobre el total, caps. 1-8.\n\n" + inf.tabla_md(t_social)),
        (f"Composición económica del cambio {va['base']}→{va['fin']} por área (capítulos)", "estimacion",
         "Contribución de cada capítulo al cambio del gasto no financiero (caps. 1-7, tabla 2.14), en € constantes.\n\n" + inf.tabla_md(t_comp)),
        inf.saltos(tidy[tidy.dimension == "subfuncion"], 2024),
        inf.preelectoral(tf, c["top_n"]),
    ]
    md = inf.documento("Insights · Clasificación funcional",
                       f"Generado {ahora()} por `analisis_funciones.py`. Serie oficial "
                       f"{anios[0]}-{anios[-1]}; perímetro caps. 1-8 (tablas 2.8 y 2.9).", insights)
    pesos_fin = tf[(tf.metrica == "peso_total_pct") & (tf.anio == anios[-1]) & (tf.precios == "corrientes")]
    imp_fin = tf[(tf.metrica == "importe") & (tf.anio == anios[-1]) & (tf.precios == "corrientes")].set_index("id_estable").valor
    t1 = pesos_fin.assign(importe=pesos_fin.id_estable.map(imp_fin)).sort_values("valor", ascending=False)
    t1 = pd.DataFrame({"Función": t1.etiqueta, "Área": t1.padre_etiqueta, f"Importe {anios[-1]} (M€)": (t1.importe / 1e6).round(1),
                       "Peso (%)": t1.valor.round(2)})
    tablas = [(f"Peso de las funciones en {anios[-1]} (euros corrientes)", t1,
               "Presupuesto inicial, caps. 1-8. Fuente: Tomo 3, tabla 2.8. Elaboración propia."),
              (f"Composición por capítulos del cambio {va['base']}→{va['fin']}", t_comp,
               "Euros constantes de 2025; gasto no financiero (caps. 1-7). Fuente: Tomo 3, tabla 2.14. Elaboración propia.")]
    escribir_salidas("funciones", tidy, md, tablas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
