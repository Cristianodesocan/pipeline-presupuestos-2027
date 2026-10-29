"""Peso y evolución de los entes con presupuesto limitativo (Tomo 3, tabla 3.1 «comparativo por entes»).

    python 4_analisis/analisis_entes.py [--fuente local|supabase] [--anio-actual 2027]

Independiente: lee fact_presupuesto, dim_ente y dim_anio.
⚠ NO es aditivo con secciones, funciones ni programas: los organismos autónomos se financian sobre todo con
transferencias de la Administración general (p. ej. el Servicio Canario de la Salud con el programa 312A),
así que sumarlos duplicaría el gasto. El peso se calcula sobre el total de la propia tabla 3.1 (perímetro «entes»).
Las altas y bajas de entes son cambios de perímetro, no crecimiento.
Salidas en 4_analisis/salidas/entes/.
"""
import sys

import pandas as pd

import _informes as inf
import _metricas as m
from _lectura import agrupar, ahora, argumentos, cfg, ensamblar, escribir_salidas, leer, panel, recortar

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "2_transformacion"))
from _tcomun import normalizar_nombre  # noqa: E402


def tipo_normalizado(texto: str, tipos: dict) -> str:
    clave = " ".join(w for w in normalizar_nombre(texto).split() if not w.isdigit())
    return tipos.get(clave, texto)


def main() -> int:
    a = argumentos(__doc__.split("\n")[0])
    datos = recortar(leer(a.fuente, a.confirmar_produccion), a.anio_actual)
    c = cfg()
    f = datos.fact[datos.fact.serie_oficial & (datos.fact.tabla == "entes") & (datos.fact.version_importe == "inicial")]
    ult_tipo = f.sort_values("anio_presupuesto").groupby("id_estable").codigo_padre.last()
    tipo = ult_tipo.map(lambda t: tipo_normalizado(t, c["tipos_ente"]))
    de = datos.dims["ente"].sort_values("anio_hasta").drop_duplicates("id_estable", keep="last")
    meta = pd.DataFrame({"id": de.id_estable, "etiqueta": de.denominacion_std + " (" + de.codigo + ")", "nivel": 2,
                         "padre_id": de.id_estable.map(tipo), "padre_etiqueta": de.id_estable.map(tipo),
                         "ruta_jerarquia": de.id_estable.map(tipo), "comparabilidad": de.comparabilidad, "concepto_ced": None})
    p = panel(datos.fact, "entes")
    p = p.assign(padre=p.id.map(tipo))
    p_tipo = agrupar(p, tipo.to_dict())
    meta_t = pd.DataFrame({"id": sorted(tipo.unique())}).assign(etiqueta=lambda d: d.id, nivel=1, padre_id=None,
                                                                padre_etiqueta=None, ruta_jerarquia="",
                                                                comparabilidad="agregado", concepto_ced=None)
    t_ente = ensamblar(m.calcular_todo(p, datos.dim_anio, c), meta, "ente", "individual", datos)
    t_tipo = ensamblar(m.calcular_todo(p_tipo, datos.dim_anio, c), meta_t, "tipo_ente", "individual", datos)
    tidy = pd.concat([t_ente, t_tipo], ignore_index=True)

    anios = sorted(p.anio.unique())
    ultimo = anios[-1]
    ventanas = m.ventanas_desde(datos.dim_anio, anios)
    va = next(v for v in ventanas if v["id"] == c["ventana_actual"])

    imp = t_ente[(t_ente.metrica == "importe") & (t_ente.precios == "corrientes") & (t_ente.id_estable != "__total__")]
    pw = t_ente[(t_ente.metrica == "peso_total_pct") & (t_ente.precios == "corrientes")].set_index(["id_estable", "anio"]).valor
    fin = imp[imp.anio == ultimo].sort_values("valor", ascending=False)
    t_peso = pd.DataFrame({"Ente": fin.etiqueta, "Tipo": fin.padre_etiqueta, f"Importe {ultimo} (M€)": fin.valor.map(inf.meur),
                           "Peso (%)": [pw.get((i, ultimo)) for i in fin.id_estable]})
    vt = t_tipo[(t_tipo.metrica == "peso_total_pct") & (t_tipo.precios == "corrientes") & (t_tipo.id_estable != "__total__")]
    t_tipos = vt.pivot_table(index="etiqueta", columns="anio", values="valor")
    t_tipos = t_tipos[[x for x in (anios[0], 2019, va["base"], ultimo) if x in t_tipos.columns]].reset_index().rename(columns={"etiqueta": "Tipo de ente"})
    perim = de[de.comparabilidad != "continua"]
    t_perim = pd.DataFrame({"Ente": perim.denominacion_std + " (" + perim.codigo + ")", "Desde": perim.anio_desde,
                            "Hasta": perim.anio_hasta, "Comparabilidad": perim.comparabilidad}).sort_values("Desde")
    # consolidación: SCS frente a la transferencia de la CAC (programa 312A)
    scs = imp[imp.etiqueta.str.contains(r"\(SCS\)", regex=True)].set_index("anio").valor
    p312 = datos.fact[datos.fact.serie_oficial & (datos.fact.tabla == "programas") & (datos.fact.codigo == "312A")
                      & (datos.fact.version_importe == "inicial")].set_index("anio").importe_corriente
    t_cons = pd.DataFrame({"Año": [x for x in (anios[0], va["base"], ultimo)],
                           "SCS en 3.1 (M€)": [inf.meur(scs.get(x, float("nan"))) for x in (anios[0], va["base"], ultimo)],
                           "Programa 312A de la CAC (M€)": [inf.meur(p312.get(x, float("nan"))) for x in (anios[0], va["base"], ultimo)]})

    insights = [
        (f"Peso de cada ente en {ultimo}", "verificado", "Sobre el total de la tabla 3.1 (no aditivo con la CAC).\n\n" + inf.tabla_md(t_peso)),
        ("Peso por tipo de ente (%)", "verificado", inf.tabla_md(t_tipos)),
        inf.prioridades(t_ente, va, c["top_n"]),
        inf.ruptura(t_ente, c["ventana_actual"], c["ventana_anterior"], c["top_n"]),
        inf.real_vs_nominal(t_ente, ventanas),
        ("Altas, bajas y cambios de nombre de entes (cambio de perímetro, no crecimiento)", "verificado", inf.tabla_md(t_perim)),
        ("Consolidación: por qué los entes no se suman a la CAC", "verificado",
         "El Servicio Canario de la Salud se financia casi por completo con la transferencia del programa 312A "
         "*Asistencia Sanitaria* de la Administración general: sumar ambos duplicaría el gasto sanitario.\n\n" + inf.tabla_md(t_cons)),
        inf.saltos(t_ente, va["base"] + 1),
        inf.preelectoral(t_ente, c["top_n"]),
    ]
    md = inf.documento("Insights · Entes con presupuesto limitativo",
                       f"Generado {ahora()} por `analisis_entes.py`. Serie oficial {anios[0]}-{ultimo}; tabla 3.1 "
                       "(perímetro «entes»; no aditivo con las demás dimensiones).", insights)
    tablas = [(f"Peso de los entes en {ultimo}", t_peso, "Presupuesto inicial. Fuente: Tomo 3, tabla 3.1. No aditivo con la CAC."),
              ("Peso por tipo de ente (%)", t_tipos, "Fuente: Tomo 3, tabla 3.1. Elaboración propia."),
              ("Altas, bajas y cambios de entes", t_perim, "Cambios de perímetro según el crosswalk de entes.")]
    escribir_salidas("entes", tidy, md, tablas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
