"""Propone los crosswalks entre años de secciones, funciones, subfunciones, programas y entes.

    python 2_transformacion/crosswalks.py                    # todas las dimensiones
    python 2_transformacion/crosswalks.py --dimension programa

Para cada dimensión escribe en 2_transformacion/crosswalks/:
  xwalk_<dim>_propuesto.csv   todos los enlaces propuestos y sucesos (nuevo, extinguido, reutilizado…)
  revision_<dim>.md           casos dudosos ordenados por importe, para la revisión humana
  xwalk_<dim>_validado.csv    decisiones humanas (se crea vacío; se versiona en git)
y en staging/xwalk_<dim>.parquet los enlaces efectivos: «auto» no rechazados + «aceptar» validados.

Revisión humana: copia una fila del propuesto al validado con decision=aceptar|rechazar (y, si quieres,
otro tipo_enlace). Un enlace en revisión sin decisión deja sus series como comparabilidad=pendiente.
Las secciones van primero: su crosswalk alimenta la señal s_seccion de los programas.
"""
import argparse
import sys

import pandas as pd

from _emparejar import CONTINUIDAD, emparejar, unidades
from _tcomun import DIMENSIONES_XWALK, XWALKS, ahora, cfg, guardar, leer, log_evento

CLAVE = ["anio_origen", "codigo_origen", "anio_destino", "codigo_destino"]
COLS_VALIDADO = CLAVE + ["decision", "tipo_enlace", "validado_por", "validado_en", "nota"]


def leer_validado(dim: str) -> pd.DataFrame:
    ruta = XWALKS / f"xwalk_{dim}_validado.csv"
    if not ruta.exists():
        pd.DataFrame(columns=COLS_VALIDADO).to_csv(ruta, index=False)
    v = pd.read_csv(ruta, dtype={"codigo_origen": str, "codigo_destino": str})
    malas = v[~v.decision.isin(["aceptar", "rechazar"])]
    if len(malas):
        raise ValueError(f"{ruta.name}: decision debe ser aceptar|rechazar ({len(malas)} filas)")
    return v


def efectivos(prop: pd.DataFrame, validado: pd.DataFrame) -> pd.DataFrame:
    """Enlaces que usa el modelo y su estado final (auto, validado, pendiente o suceso sin enlace)."""
    e = prop.copy()
    e["estado_final"] = e.estado.map({"auto": "auto", "revision": "pendiente", "sin_enlace": "sin_enlace"})
    if len(validado):
        v = validado.set_index(CLAVE)
        clave = list(zip(*(e[c] for c in CLAVE)))
        dec = [v.decision.get(k) if k in v.index else None for k in clave]
        e["decision"] = dec
        e.loc[e.decision == "aceptar", "estado_final"] = "validado"
        e.loc[e.decision == "rechazar", "estado_final"] = "rechazado"
        tipo_v = [v.tipo_enlace.get(k) if k in v.index else None for k in clave]
        e["tipo_enlace"] = [t if isinstance(t, str) and t else o for t, o in zip(tipo_v, e.tipo_enlace)]
        # enlaces añadidos a mano que el algoritmo no propuso
        nuevos = validado[(validado.decision == "aceptar") &
                          ~validado.set_index(CLAVE).index.isin(e.set_index(CLAVE).index)]
        if len(nuevos):
            extra = nuevos[CLAVE + ["tipo_enlace"]].assign(dimension=e.dimension.iloc[0], estado="manual",
                                                          estado_final="validado")
            e = pd.concat([e, extra], ignore_index=True)
    return e


def enlaces_seccion_por_anio(ef: pd.DataFrame) -> dict:
    """{año destino: {código sección t-1: {códigos herederos en t}}} con enlaces aceptados."""
    ok = ef[ef.estado_final.isin(["auto", "validado"]) & ef.codigo_destino.notna() & ef.codigo_origen.notna()]
    out = {}
    for (anio, origen), g in ok.groupby(["anio_destino", "codigo_origen"]):
        out.setdefault(int(anio), {})[origen] = set(g.codigo_destino)
    return out


def informe_revision(dim: str, ef: pd.DataFrame) -> str:
    fmt = lambda v: "" if pd.isna(v) else f"{v / 1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")  # noqa: E731
    lineas = [f"# Revisión del crosswalk · {dim}", "", f"Generado {ahora()} por `crosswalks.py`.", "",
              "## Resumen", "", "| Estado | Tipo | Enlaces |", "|---|---|---|"]
    for (est, tipo), n in ef.groupby(["estado_final", "tipo_enlace"]).size().items():
        lineas.append(f"| {est} | {tipo} | {n} |")
    pend = ef[ef.estado_final == "pendiente"].sort_values("ajustado_destino", ascending=False)
    lineas += ["", f"## Enlaces pendientes de revisión ({len(pend)})", "",
               "Para decidir, copia la fila de `xwalk_" + dim + "_propuesto.csv` a `xwalk_" + dim + "_validado.csv` "
               "con `decision=aceptar` o `rechazar`.", "",
               "| Año | Origen | → Destino | Tipo | Score | s_imp | s_nom | Inicial t-1 (M€) | Ajustado t (M€) |",
               "|---|---|---|---|---|---|---|---|---|"]
    for r in pend.itertuples():
        lineas.append(f"| {int(r.anio_destino)} | `{r.codigo_origen}` {r.denominacion_origen} | `{r.codigo_destino}` "
                      f"{r.denominacion_destino} | {r.tipo_enlace} | {r.score} | {r.s_importe} | {r.s_nombre} | "
                      f"{fmt(r.inicial_origen)} | {fmt(r.ajustado_destino)} |")
    sin = ef[(ef.tipo_enlace.isin(["nuevo_sin_origen", "reutilizado"]))].sort_values("ajustado_destino", ascending=False)
    lineas += ["", f"## Unidades con importe reexpresado pero sin origen identificado ({len(sin)})", "",
               "Su ajustado de t-1 es > 0, así que su contenido existía antes con otro código: buscar su origen.", "",
               "| Año | Código | Denominación | Tipo | Ajustado t-1 (M€) | Inicial t (M€) |", "|---|---|---|---|---|---|"]
    for r in sin.itertuples():
        lineas.append(f"| {int(r.anio_destino)} | `{r.codigo_destino}` | {r.denominacion_destino} | {r.tipo_enlace} | "
                      f"{fmt(r.ajustado_destino)} | {fmt(r.inicial_destino)} |")
    return "\n".join(lineas) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dimension", choices=DIMENSIONES_XWALK)
    args = ap.parse_args()
    fact = leer("fact_base")
    c = cfg()["crosswalk"]
    XWALKS.mkdir(parents=True, exist_ok=True)
    enl_secc = None
    dims = DIMENSIONES_XWALK if args.dimension is None else \
        (["seccion", args.dimension] if args.dimension == "programa" else [args.dimension])
    for dim in dims:
        u = unidades(fact, dim)
        prop = emparejar(u, dim, c["pesos"][dim], c, enl_secc if dim == "programa" else None)
        prop.to_csv(XWALKS / f"xwalk_{dim}_propuesto.csv", index=False)
        ef = efectivos(prop, leer_validado(dim))
        guardar(ef, f"xwalk_{dim}")
        (XWALKS / f"revision_{dim}.md").write_text(informe_revision(dim, ef), encoding="utf-8")
        if dim == "seccion":
            enl_secc = enlaces_seccion_por_anio(ef)
        resumen = ef.groupby("estado_final").size().to_dict()
        tipos = ef[ef.estado_final.isin(["auto", "validado", "pendiente"])].tipo_enlace.value_counts().to_dict()
        print(f"{dim:11s} unidades={len(u):5d} · {resumen} · {tipos}")
        log_evento("crosswalk", dimension=dim, estados=resumen, tipos=tipos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
