"""Vista competencial de secciones: cada año expresado en la estructura de consejerías del último año.

    python 2_transformacion/retroproyectar_secciones.py

Responde a «¿cuánto se destinaba en 2015 a lo que hoy gestiona la Consejería X?» (§5.3.2).
Base: tabla 2.16 (sección × programa), caps. 1-8, presupuesto inicial de la serie oficial.
Cada par (sección, programa) del año y se asigna a la sección del año objetivo T que gestiona su
FAMILIA de programas:
  familia_unica      la familia está en una sola sección en T
  seccion_heredera   está en varias (p. ej. 912A en todas) y la sección de origen tiene heredera en T entre ellas
  proporcional       está en varias y no hay heredera: se reparte según el peso de cada sección en T
  sin_equivalente    la familia ya no existe en T → «sin_equivalente_<T>»
Salida: staging/fact_seccion_estructura.parquet. La suma por año cuadra con el total de 2.1.
"""
import sys

import pandas as pd

from _tcomun import guardar, leer, log_evento

CAPS_1_8 = [str(c) for c in (1, 2, 3, 4, 6, 7, 8)]


def main() -> int:
    f = leer("fact_presupuesto")
    dim_secc = leer("dim_seccion")
    da = leer("dim_anio").set_index("anio")
    of = f[f.serie_oficial & (f.version_importe == "inicial")]
    spc = of[(of.dimension == "seccion_programa") & of.capitulo.isin(CAPS_1_8)]
    spc = spc.groupby(["anio_presupuesto", "codigo_padre", "codigo_unidad", "familia_id"], as_index=False).importe_corriente.sum()
    T = int(spc.anio_presupuesto.max())

    # distribución de cada familia entre las secciones del año objetivo
    obj = spc[spc.anio_presupuesto == T].groupby(["familia_id", "codigo_padre"]).importe_corriente.sum()
    reparto = {}
    for fam, g in obj.groupby(level=0):
        g = g.droplevel(0)
        total = g.sum()
        reparto[fam] = (g / total).to_dict() if total > 0 else {s: 1 / len(g) for s in g.index}

    # sección heredera en T de cada (año, sección): mismo id_estable
    id_por_nodo = {}
    for r in dim_secc.itertuples():
        for a in range(r.anio_desde, r.anio_hasta + 1):
            id_por_nodo[(a, r.codigo)] = r.id_estable
    codigo_en_T = {r.id_estable: r.codigo for r in dim_secc.itertuples() if r.anio_desde <= T <= r.anio_hasta}

    filas = []
    for r in spc.itertuples():
        destinos = reparto.get(r.familia_id, {})
        heredera = codigo_en_T.get(id_por_nodo.get((r.anio_presupuesto, r.codigo_padre)))
        if not destinos:
            asign, metodo = {f"sin_equivalente_{T}": 1.0}, "sin_equivalente"
        elif len(destinos) == 1:
            asign, metodo = destinos, "familia_unica"
        elif heredera in destinos:
            asign, metodo = {heredera: 1.0}, "seccion_heredera"
        else:
            asign, metodo = destinos, "proporcional"
        for destino, peso in asign.items():
            filas.append({"anio": r.anio_presupuesto, "seccion_destino": destino, "seccion_origen": r.codigo_padre,
                          "programa": r.codigo_unidad, "familia_id": r.familia_id, "metodo": metodo,
                          "peso_reparto": peso, "importe_corriente": r.importe_corriente * peso})
    det = pd.DataFrame(filas)
    nombres = of[(of.dimension == "seccion") & (of.tabla == "secciones") & (of.anio_presupuesto == T)]
    nombres = nombres.drop_duplicates("codigo").set_index("codigo").denominacion_raw
    out = det.groupby(["anio", "seccion_destino", "metodo"], as_index=False).agg(
        importe_corriente=("importe_corriente", "sum"), n_pares=("programa", "size"))
    out["denominacion_destino"] = out.seccion_destino.map(nombres).fillna("Sin equivalente en la estructura " + str(T))
    out["vista"] = f"estructura_{T}"
    out["importe_constante"] = out.importe_corriente * out.anio.map(da.deflactor)
    guardar(out, "fact_seccion_estructura")
    guardar(det, "fact_seccion_estructura_detalle")

    resumen = det.groupby("metodo").importe_corriente.sum() / det.importe_corriente.sum()
    print(f"Estructura objetivo {T}: {out.seccion_destino.nunique()} destinos · reparto por método "
          + ", ".join(f"{k} {v:.1%}" for k, v in resumen.items()))
    sin = out[out.metodo == "sin_equivalente"].groupby("anio").importe_corriente.sum() / out.groupby("anio").importe_corriente.sum()
    print("Peso sin equivalente por año:", {int(a): f"{v:.1%}" for a, v in sin.items()})
    log_evento("retroproyectar_secciones", objetivo=T, metodos=resumen.round(4).to_dict())
    return 0


if __name__ == "__main__":
    sys.exit(main())
