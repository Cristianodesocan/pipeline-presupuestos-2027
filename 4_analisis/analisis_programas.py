"""Peso y evolución de los programas presupuestarios, con su comparabilidad entre años.

    python 4_analisis/analisis_programas.py [--fuente local|supabase] [--anio-actual 2027]

Independiente: lee fact_presupuesto, dim_programa, dim_subfuncion, dim_funcion, xwalk y dim_anio.
Vistas:
  individual    cada id_estable (un programa a través de renombres y recodificaciones)
  familia       familias de programas (divisiones y fusiones agregadas): base de las métricas de ventana
  concepto_ced  agregado por los 13 conceptos de política social de Canarias en Datos
Salidas en 4_analisis/salidas/programas/.
"""
import sys

import pandas as pd

import _informes as inf
import _metricas as m
from _lectura import ahora, argumentos, cfg, ensamblar, escribir_salidas, leer, panel, recortar


def metas(datos):
    dp = datos.dims["programa"].sort_values("anio_hasta").drop_duplicates("id_estable", keep="last")
    sub = datos.dims["subfuncion"].sort_values("anio_hasta").drop_duplicates("codigo", keep="last").set_index("codigo")
    fun = datos.dims["funcion"].sort_values("anio_hasta").drop_duplicates("codigo", keep="last").set_index("codigo")
    sf = dp.codigo.str[:3]
    ind = pd.DataFrame({"id": dp.id_estable, "etiqueta": dp.denominacion_std + " (" + dp.codigo + ")", "nivel": 4,
                        "padre_id": sf.map(sub.id_estable), "padre_etiqueta": sf.map(sub.denominacion_std),
                        "ruta_jerarquia": dp.codigo.str[:2].map(fun.denominacion_std) + "|" + sf.map(sub.denominacion_std),
                        "comparabilidad": dp.comparabilidad, "concepto_ced": dp.concepto_ced})
    n_ids = dp.groupby("familia_id").id_estable.nunique()
    raiz = ind.set_index("id")
    fam_ids = dp.familia_id.unique()
    base = {f: f.removeprefix("FAM-") for f in fam_ids}
    fam = pd.DataFrame({"id": fam_ids,
                        "etiqueta": [raiz.etiqueta.get(base[f], f) + (" · familia" if n_ids[f] > 1 else "") for f in fam_ids],
                        "nivel": 4, "padre_id": [raiz.padre_id.get(base[f]) for f in fam_ids],
                        "padre_etiqueta": [raiz.padre_etiqueta.get(base[f]) for f in fam_ids],
                        "ruta_jerarquia": [raiz.ruta_jerarquia.get(base[f]) for f in fam_ids],
                        "comparabilidad": ["familia" if n_ids[f] > 1 else raiz.comparabilidad.get(base[f]) for f in fam_ids],
                        "concepto_ced": [raiz.concepto_ced.get(base[f]) for f in fam_ids]})
    return ind, fam, dp


def main() -> int:
    a = argumentos(__doc__.split("\n")[0])
    datos = recortar(leer(a.fuente, a.confirmar_produccion), a.anio_actual)
    c = cfg()
    ind, fam, dp = metas(datos)
    p_ind = panel(datos.fact, "programas", por="id_estable")
    p_ind = p_ind.assign(padre=p_ind.id.map(dict(zip(ind.id, ind.padre_id))))
    p_fam = panel(datos.fact, "programas", por="familia_id")
    concepto = dict(zip(dp.id_estable, dp.concepto_ced.fillna("sin_concepto")))
    p_ced = p_ind.assign(id=p_ind.id.map(concepto)).groupby(["id", "anio", "precios"], as_index=False)[["importe", "ajustado"]].sum(min_count=1)
    meta_ced = pd.DataFrame({"id": sorted(p_ced.id.unique())}).assign(
        etiqueta=lambda d: d.id.str.replace("_", " ").str.capitalize(), nivel=1, padre_id=None, padre_etiqueta=None,
        ruta_jerarquia="", comparabilidad="agregado", concepto_ced=lambda d: d.id)

    t_ind = ensamblar(m.calcular_todo(p_ind, datos.dim_anio, c), ind, "programa", "individual", datos)
    t_fam = ensamblar(m.calcular_todo(p_fam, datos.dim_anio, c), fam, "programa", "familia", datos)
    t_ced = ensamblar(m.calcular_todo(p_ced, datos.dim_anio, c), meta_ced, "programa", "concepto_ced", datos)
    tidy = pd.concat([t_ind, t_fam, t_ced], ignore_index=True)

    anios = sorted(p_ind.anio.unique())
    ultimo = anios[-1]
    ventanas = m.ventanas_desde(datos.dim_anio, anios)
    va = next(v for v in ventanas if v["id"] == c["ventana_actual"])
    n = c["top_n"]

    # ranking de peso (top 20)
    pw = t_ind[(t_ind.metrica == "peso_total_pct") & (t_ind.anio == ultimo) & (t_ind.precios == "corrientes") & (t_ind.id_estable != "__total__")]
    imp = t_ind[(t_ind.metrica == "importe") & (t_ind.anio == ultimo) & (t_ind.precios == "corrientes")].set_index("id_estable").valor
    top = pw.sort_values("valor", ascending=False).head(20)
    t_top = pd.DataFrame({"#": range(1, len(top) + 1), "Programa": top.etiqueta, f"Importe {ultimo} (M€)": top.id_estable.map(imp).map(inf.meur),
                          "Peso (%)": top.valor.map(lambda x: inf.num(x, 2)), "Comparabilidad": top.comparabilidad})

    # altas y bajas en la legislatura actual
    ini_v = va["base"] + 1
    imp_por = t_ind[(t_ind.metrica == "importe") & (t_ind.precios == "corrientes")].pivot_table(index="id_estable", columns="anio", values="valor")
    altas = dp[(dp.anio_desde >= ini_v) & (dp.anio_desde == dp.groupby("id_estable").anio_desde.transform("min"))]
    t_altas = pd.DataFrame({"Programa": altas.denominacion_std + " (" + altas.codigo + ")", "Alta": altas.anio_desde,
                            f"Importe {ultimo} (M€)": [inf.meur(imp_por.get(ultimo, pd.Series()).get(i, float("nan"))) for i in altas.id_estable],
                            "Comparabilidad": altas.comparabilidad}).sort_values("Alta")
    bajas = dp[dp.anio_hasta_activo.notna() & (dp.anio_hasta_activo >= va["base"]) & (dp.anio_hasta_activo < ultimo)]
    t_bajas = pd.DataFrame({"Programa": bajas.denominacion_std + " (" + bajas.codigo + ")",
                            "Último año con importe": bajas.anio_hasta_activo.astype(int),
                            "Importe ese año (M€)": [inf.meur(imp_por.loc[i, int(y)]) if i in imp_por.index else "—"
                                                     for i, y in zip(bajas.id_estable, bajas.anio_hasta_activo)]})

    # gasto social (conceptos CED)
    pc = t_ced[(t_ced.metrica == "peso_total_pct") & (t_ced.precios == "corrientes") & (t_ced.id_estable != "__total__")]
    t_social = pc.pivot_table(index="etiqueta", columns="anio", values="valor")
    cols = [x for x in (anios[0], 2019, va["base"], ultimo) if x in t_social.columns]
    t_social = t_social[cols].round(2).reset_index().rename(columns={"etiqueta": "Concepto CED"})
    tc = t_ced[(t_ced.metrica == "tcac_ventana") & (t_ced.precios == "constantes") & (t_ced.id_estable != "__total__")]
    t_tcac = tc.pivot_table(index="etiqueta", columns="ventana", values="valor").round(1)
    t_tcac = t_tcac[[v["id"] for v in ventanas if v["id"] in t_tcac.columns]].reset_index().rename(columns={"etiqueta": "Concepto CED"})

    # reestructuración de programas al inicio de la legislatura
    re = t_ind[(t_ind.metrica == "efecto_reestr") & (t_ind.anio == ini_v) & (t_ind.precios == "corrientes") & (t_ind.valor.abs() >= 1e6)]
    t_re = pd.DataFrame({"Programa": re.etiqueta, "Efecto reestructuración (M€)": re.valor.map(inf.meur)}).iloc[re.valor.argsort()]

    # calidad: cobertura del crosswalk
    ult = t_ind[(t_ind.metrica == "importe") & (t_ind.anio == ultimo) & (t_ind.precios == "corrientes") & (t_ind.id_estable != "__total__")]
    cob = ult.groupby("comparabilidad").valor.sum() / ult.valor.sum() * 100
    t_cob = pd.DataFrame({"Comparabilidad": cob.index, f"% del importe {ultimo}": cob.map(inf.num).values})
    pend = datos.xwalk[(datos.xwalk.dimension == "programa") & (datos.xwalk.estado_final == "pendiente")]
    multi = fam[fam.comparabilidad == "familia"]

    insights = [
        (f"Los 20 programas de mayor peso en {ultimo}", "verificado", inf.tabla_md(t_top)),
        inf.prioridades(t_fam, va, n),
        inf.ruptura(t_fam, c["ventana_actual"], c["ventana_anterior"], n),
        (f"Programas creados en la legislatura actual ({ini_v}-{ultimo})", "verificado",
         "Prioridades políticas nuevas y candidatas a titular. Revisa la columna de comparabilidad: `subfuncion` indica "
         "que su contenido ya existía con otro código.\n\n" + inf.tabla_md(t_altas)),
        (f"Programas que dejan de tener importe desde {va['base']}", "verificado", inf.tabla_md(t_bajas)),
        ("Gasto social según los conceptos de Canarias en Datos: peso (%)", "verificado", inf.tabla_md(t_social)),
        ("Gasto social: TCAC real por ventana (%)", "estimacion", inf.tabla_md(t_tcac)),
        (f"Reestructuración de programas en {ini_v}", "verificado",
         "efecto_reestr ≥ 1 M€ en valor absoluto (ajustado del año anterior en el tomo nuevo − inicial del año anterior).\n\n"
         + inf.tabla_md(t_re)),
        inf.elasticas(t_fam, va, n),
        inf.saltos(t_ind, ini_v),
        inf.preelectoral(t_fam, n),
        ("Calidad: comparabilidad de las series", "verificado",
         inf.tabla_md(t_cob) + f"\n{len(multi)} familias agregan varios programas (divisiones o fusiones); "
         f"{len(pend)} enlaces del crosswalk siguen pendientes de revisión humana "
         "(`2_transformacion/crosswalks/revision_programa.md`). Las métricas de ventana se presentan por familia.\n"),
    ]
    md = inf.documento("Insights · Programas presupuestarios",
                       f"Generado {ahora()} por `analisis_programas.py`. Serie oficial {anios[0]}-{ultimo}; tabla 2.10 "
                       "(caps. 1-8).", insights)
    tablas = [(f"Los 20 programas de mayor peso en {ultimo}", t_top, "Presupuesto inicial, caps. 1-8. Fuente: Tomo 3, tabla 2.10. Elaboración propia."),
              (f"Programas creados en {ini_v}-{ultimo}", t_altas, "Alta = primer año con el programa en la serie oficial."),
              ("Peso del gasto social por concepto (%)", t_social, "Conceptos de Canarias en Datos (correspondencias.yml)."),
              ("Comparabilidad de las series de programas", t_cob, "Crosswalk de programas (§5.3.1 del diseño).")]
    escribir_salidas("programas", tidy, md, tablas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
