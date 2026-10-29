"""Puertas de calidad de la transformación (diseno_pipeline_presupuestos_2027.md §5.5). Si falla, no hay carga.

    python 2_transformacion/validar.py
    python 2_transformacion/validar.py --estricto     # los avisos también bloquean

Errores: T1 esquema · T2 unicidad · T3 cuadre entre dimensiones · T4 cuadre jerárquico · T10 retroproyección ·
         T11 ids en la serie oficial · T12 deflactor
Avisos:  T5 capítulos 2.16 vs 2.10 · T6 continuidad · T7 coherencia del ajustado · T8 techo de gasto ·
         T9 cobertura del crosswalk · T13 crosswalks pendientes de revisión
Salida: logs/validacion_transformacion.json; código 1 si hay errores.
"""
import argparse
import json
import sys

import pandas as pd

from _tcomun import DIMENSIONES_XWALK, LOGS, ahora, cfg, leer, log_evento

TOL = 1.0
CLAVE = ["anio", "anio_presupuesto", "fase", "tabla", "dimension", "codigo", "capitulo", "version_importe", "perimetro"]
CAPS_1_8 = [str(c) for c in (1, 2, 3, 4, 6, 7, 8)]


class Informe:
    def __init__(self):
        self.errores, self.avisos, self.ok, self.es_aviso = [], [], {}, set()

    def comprobar(self, regla, condicion, mensaje, aviso=False):
        self.ok.setdefault(regla, [0, 0])
        self.ok[regla][0 if condicion else 1] += 1
        if aviso:
            self.es_aviso.add(regla)
        if not condicion:
            (self.avisos if aviso else self.errores).append(f"{regla} {mensaje}")


def totales(of: pd.DataFrame, tabla: str) -> pd.Series:
    t = of[(of.tabla == tabla) & (of.capitulo == "TOTAL")]
    return t.groupby(["anio_presupuesto", "fase", "version_importe"]).importe_corriente.sum()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--estricto", action="store_true")
    args = ap.parse_args()
    c = cfg()["validacion"]
    f = leer("fact_presupuesto")
    inf = Informe()

    # T1 · esquema
    for col in ["anio", "anio_presupuesto", "fase", "dimension", "codigo", "capitulo", "importe_corriente", "deflactor"]:
        inf.comprobar("T1", f[col].notna().all(), f"nulos en {col}: {int(f[col].isna().sum())}")
    inf.comprobar("T1", f.codigo.map(type).eq(str).all(), "codigo no es texto en alguna fila")
    # T2 · unicidad
    dup = f.duplicated(CLAVE).sum()
    inf.comprobar("T2", dup == 0, f"{dup} filas duplicadas en la clave natural")

    # T3 · cuadre entre dimensiones (caps. 1-8): secciones = funciones = subfunciones = programas
    tots = {t: totales(f, t) for t in ("secciones", "funciones", "subfunciones", "programas")}
    for k in tots["programas"].index:
        vals = {t: s.get(k) for t, s in tots.items()}
        inf.comprobar("T3", max(vals.values()) - min(vals.values()) <= TOL, f"{k}: {vals}")

    # T4 · cuadre jerárquico: Σ programas por prefijo de 3 = subfunción; Σ subfunciones por prefijo de 2 = función
    for hija, madre, n in (("programas", "subfunciones", 3), ("subfunciones", "funciones", 2)):
        h = f[(f.tabla == hija) & (f.capitulo == "TOTAL")]
        m = f[(f.tabla == madre) & (f.capitulo == "TOTAL")]
        sh = h.assign(pref=h.codigo.str[:n]).groupby(["doc_id", "version_importe", "pref"]).importe_corriente.sum()
        sm = m.groupby(["doc_id", "version_importe", "codigo"]).importe_corriente.sum()
        dif = (sh - sm.reindex(sh.index).fillna(0)).abs()
        inf.comprobar("T4", (dif <= TOL).all(), f"{hija}→{madre}: {int((dif > TOL).sum())} descuadres, p. ej. {dif[dif > TOL].head(3).to_dict()}")

    of = f[f.serie_oficial]
    # T5 · Σ caps. 1-8 de 2.16 por programa = total del programa en 2.10 (aviso)
    spc = of[(of.dimension == "seccion_programa") & of.capitulo.isin(CAPS_1_8)]
    spc = spc.groupby(["anio_presupuesto", "codigo_unidad"]).importe_corriente.sum()
    prog = of[(of.tabla == "programas") & (of.version_importe == "inicial")].set_index(["anio_presupuesto", "codigo"]).importe_corriente
    dif = (spc - prog.reindex(spc.index)).abs()
    inf.comprobar("T5", (dif <= TOL).all(), f"{int((dif > TOL).sum())} programas no cuadran 2.16 vs 2.10: {dif[dif > TOL].head(5).to_dict()}", aviso=True)

    # T6 · continuidad por id_estable (programas): |var| > 40 % con peso ≥ 0,5 %
    p = of[(of.tabla == "programas") & (of.version_importe == "inicial")]
    serie = p.groupby(["id_estable", "anio"]).importe_corriente.sum().unstack()
    total = p.groupby("anio").importe_corriente.sum()
    var = serie.pct_change(axis=1, fill_method=None)
    peso = serie / total
    saltos = ((var.abs() > c["continuidad_var"]) & (peso >= c["continuidad_peso"])).stack()
    saltos = saltos[saltos]
    for (idn, anio), _ in saltos.items():
        inf.comprobar("T6", False, f"{idn} {anio}: var {var.loc[idn, anio]:+.0%}, peso {peso.loc[idn, anio]:.1%}", aviso=True)
    inf.comprobar("T6", True, "")

    # T7 · coherencia del ajustado: Σ ajustado del tomo t vs Σ inicial del tomo t-1 (>1 %)
    tp = totales(of, "programas")
    ini = {a: v for (a, _, ver), v in tp.items() if ver == "inicial"}
    aj = {a: v for (a, _, ver), v in tp.items() if ver == "ajustado"}
    for a in sorted(aj):
        if a - 1 in ini:
            d = aj[a] / ini[a - 1] - 1
            inf.comprobar("T7", abs(d) <= 0.01, f"{a}: ajustado {d:+.2%} frente al inicial de {a - 1} (reestructuración amplia)", aviso=True)

    # T8 · techo de gasto no financiero (caps. 1-7) del año en curso
    for anio, techo in (c.get("techo_gasto_no_financiero") or {}).items():
        g = of[(of.anio_presupuesto == int(anio)) & (of.tabla == "secciones_cap") & of.capitulo.isin([str(x) for x in range(1, 8)])]
        inf.comprobar("T8", g.importe_corriente.sum() <= techo, f"{anio}: gasto no financiero {g.importe_corriente.sum():,.0f} > techo {techo:,.0f}", aviso=True)

    # T9 · cobertura del crosswalk de programas: % del importe del último año en series continua/familia
    dp = leer("dim_programa").drop_duplicates("id_estable").set_index("id_estable").comparabilidad
    ult = p[p.anio_presupuesto == p.anio_presupuesto.max()]
    cobertura = ult[ult.id_estable.map(dp).isin(["continua", "familia"])].importe_corriente.sum() / ult.importe_corriente.sum()
    inf.comprobar("T9", cobertura >= c["cobertura_minima"], f"cobertura {cobertura:.1%} < {c['cobertura_minima']:.0%}", aviso=True)

    # T10 · retroproyección de secciones = total de 2.1
    retro = leer("fact_seccion_estructura").groupby("anio").importe_corriente.sum()
    t21 = of[(of.tabla == "secciones") & (of.version_importe == "inicial")].groupby("anio").importe_corriente.sum()
    d = (retro - t21.reindex(retro.index)).abs()
    inf.comprobar("T10", (d <= TOL).all(), f"retroproyección ≠ 2.1: {d[d > TOL].to_dict()}")

    # T11 · toda fila oficial de una dimensión con crosswalk tiene id_estable y familia
    sin = of[of.dimension.isin(DIMENSIONES_XWALK) & (of.id_estable.isna() | of.familia_id.isna())]
    inf.comprobar("T11", sin.empty, f"{len(sin)} filas oficiales sin id_estable/familia")

    # T12 · deflactor = 1 en el año base y € constantes coherentes
    base = cfg()["deflactor"]["base"]
    dbase = f[f.anio == base].deflactor.unique()
    inf.comprobar("T12", len(dbase) == 1 and abs(dbase[0] - 1) < 1e-4, f"deflactor del año base {base} = {dbase}")

    # T13 · crosswalks con enlaces pendientes de revisión
    for dim in DIMENSIONES_XWALK:
        n = (leer(f"xwalk_{dim}").estado_final == "pendiente").sum()
        inf.comprobar("T13", n == 0, f"{dim}: {n} enlaces pendientes (2_transformacion/crosswalks/revision_{dim}.md)", aviso=True)

    res = {"ts": ahora(), "cobertura_programas": round(float(cobertura), 4), "reglas": inf.ok,
           "errores": inf.errores, "avisos": inf.avisos}
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / "validacion_transformacion.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    log_evento("validar_transformacion", errores=len(inf.errores), avisos=len(inf.avisos))
    for regla, (bien, mal) in sorted(inf.ok.items(), key=lambda x: int(x[0][1:])):
        marca = "✅" if mal == 0 else "⚠️ " if regla in inf.es_aviso else "❌"
        print(f"  {regla:4s} {marca} {bien} correctas, {mal} fallidas")
    print(f"Cobertura del crosswalk de programas (último año, continua+familia): {cobertura:.1%}")
    for a in inf.avisos:
        print("AVISO", a)
    for e in inf.errores[:30]:
        print("ERROR", e)
    return 1 if inf.errores or (args.estricto and inf.avisos) else 0


if __name__ == "__main__":
    sys.exit(main())
