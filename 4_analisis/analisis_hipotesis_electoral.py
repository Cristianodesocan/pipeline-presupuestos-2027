"""Hipótesis: «el gasto social se acentúa en los presupuestos que se diseñan para años electorales».

    python 4_analisis/analisis_hipotesis_electoral.py [--fuente local|supabase] [--anio-actual 2027]

Años electorales (config/analisis.yml): 2019, 2023 y 2027 (autonómicas de mayo; el presupuesto se diseña en otoño
del año anterior). Solo cuentan los que ya están en la serie: 2019 y 2023 con la serie 2015-2026; 2027 entra con su Proyecto.

Perímetros de gasto social (todos con perímetro estable entre años):
  A · Consejería de bienestar social: lo que hoy gestiona la sección 23, retroproyectado (fact_seccion_estructura).
      La sección orgánica 23 NO es comparable: en 2016-2019 incluía Empleo y Vivienda.
  B · Función 23 «Servicios Sociales y Promoción Social» (clasificación funcional, tabla 2.8).
  C · Subfunción 231 «Acción Social» (tabla 2.9) y su desglose por programas (dependencia, discapacidad…).
Indicadores por presupuesto t (euros constantes 2025; corrientes como robustez):
  g      variación real interanual del perímetro (%)
  g_tot  variación real del presupuesto total (caps. 1-8)
  dif    g − g_tot (pp): ¿crece el gasto social MÁS que el presupuesto? Es la medida de «acentuación», porque
         descuenta que el año electoral sea también un año de expansión general.
  dpeso  cambio del peso en el total (pp)
Contraste: media de los años electorales observados frente a los no electorales; permutación exacta (todas las
combinaciones de k años: p unilateral = proporción con media ≥ la observada); y cada año electoral frente a los otros tres años
de su legislatura. Robustez: sin fondos MRR/REACT-EU (perímetro A), variación homogénea (B, C) y precios corrientes.
Salidas en 4_analisis/salidas/hipotesis_electoral/: CSV tidy, informe Markdown y tablas APA.
"""
import sys
from itertools import combinations

import numpy as np
import pandas as pd

import _informes as inf
from _lectura import SALIDAS, ahora, argumentos, cfg, fase_por_anio, leer, log_evento, recortar

SALIDA = SALIDAS / "hipotesis_electoral"


# ----------------------------------------------------------------------------------------------- series
def serie_tabla(fact, tabla: str, codigos: list[str] | None = None, prefijo: str | None = None) -> pd.DataFrame:
    """Importe inicial y ajustado por año (serie oficial) de un conjunto de filas de una tabla comparativa."""
    f = fact[fact.serie_oficial & (fact.tabla == tabla) & (fact.capitulo == "TOTAL")]
    if codigos is not None:
        f = f[f.codigo.isin(codigos)]
    if prefijo is not None:
        f = f[f.codigo.str.startswith(prefijo)]
    out = []
    for precios, col in (("constantes", "importe_constante"), ("corrientes", "importe_corriente")):
        ini = f[f.version_importe == "inicial"].groupby("anio_presupuesto")[col].sum()
        aj = f[f.version_importe == "ajustado"].groupby("anio_presupuesto")[col].sum()
        out.append(pd.DataFrame({"anio": ini.index, "precios": precios, "importe": ini.values,
                                 "ajustado": aj.reindex(ini.index).values}))
    return pd.concat(out, ignore_index=True)


def serie_estructura(datos, seccion: str, restar_fondos: bool = False) -> pd.DataFrame:
    e = datos.seccion_estructura[datos.seccion_estructura.seccion_destino == seccion]
    g = e.groupby("anio")[["importe_corriente", "importe_constante"]].sum()
    if restar_fondos:   # aproximación: servicios MRR/REACT-EU de la sección con el mismo código
        fo = datos.fondos[datos.fondos.serie_oficial & (datos.fondos.codigo_padre == seccion)]
        fc = fo.groupby("anio_presupuesto").importe_corriente.sum().reindex(g.index).fillna(0)
        defl = datos.dim_anio.set_index("anio").deflactor.reindex(g.index)
        g["importe_corriente"] -= fc
        g["importe_constante"] -= fc * defl
    out = [pd.DataFrame({"anio": g.index, "precios": p, "importe": g[c].values, "ajustado": np.nan})
           for p, c in (("constantes", "importe_constante"), ("corrientes", "importe_corriente"))]
    return pd.concat(out, ignore_index=True)


def indicadores(s: pd.DataFrame, total: pd.DataFrame) -> pd.DataFrame:
    """g, g_homog, g_tot, dif, peso y dpeso por año y precios."""
    d = s.merge(total[["anio", "precios", "importe"]].rename(columns={"importe": "total"}), on=["anio", "precios"])
    d = d.sort_values(["precios", "anio"])
    prev = d.groupby("precios")[["importe", "total", "anio"]].shift()
    consecutivo = prev.anio == d.anio - 1
    d["g"] = np.where(consecutivo, 100 * (d.importe / prev.importe - 1), np.nan)
    d["g_tot"] = np.where(consecutivo, 100 * (d.total / prev.total - 1), np.nan)
    d["g_homog"] = 100 * (d.importe / d.ajustado - 1)
    d["dif"] = d.g - d.g_tot
    d["peso"] = 100 * d.importe / d.total
    d["dpeso"] = np.where(consecutivo, d.peso - prev.importe / prev.total * 100, np.nan)
    return d


# ----------------------------------------------------------------------------------------------- contraste
def permutacion(valores: pd.Series, electorales: list[int]) -> dict:
    """Permutación exacta: ¿cuántas combinaciones de k años tienen una media ≥ la de los años electorales?"""
    v = valores.dropna()
    obs = [a for a in electorales if a in v.index]
    if not obs:
        return {"k": 0}
    media_e = v[obs].mean()
    combos = list(combinations(v.index, len(obs)))
    medias = np.array([v[list(c)].mean() for c in combos])
    resto = v.drop(obs)
    return {"k": len(obs), "n": len(v), "media_electoral": media_e, "media_resto": resto.mean(),
            "diferencia": media_e - resto.mean(), "combinaciones": len(combos),
            "p_unilateral": float((medias >= media_e - 1e-12).mean()),
            "p_minimo": 1 / len(combos), "rangos": {a: int(v.rank(ascending=False)[a]) for a in obs}}


def dentro_de_legislatura(valores: pd.Series, electorales: list[int]) -> pd.DataFrame:
    """Cada año electoral frente a la media de los tres presupuestos anteriores de la misma legislatura."""
    filas = []
    for a in electorales:
        previos = [x for x in (a - 3, a - 2, a - 1) if x in valores.index and pd.notna(valores[x])]
        if a in valores.index and pd.notna(valores[a]) and previos:
            filas.append({"anio": a, "electoral": valores[a], "media_previos": valores[previos].mean(),
                          "max_previos": valores[previos].max(), "previos": f"{previos[0]}-{previos[-1]}"})
    return pd.DataFrame(filas)


# ----------------------------------------------------------------------------------------------- programa
def main() -> int:
    a = argumentos(__doc__.split("\n")[0])
    datos = recortar(leer(a.fuente, a.confirmar_produccion), a.anio_actual)
    h = cfg()["hipotesis_electoral"]
    E = h["anios_electorales"]
    f = datos.fact
    total = serie_tabla(f, "programas")
    perimetros = {
        "A · Consejería de bienestar social (estructura actual)": serie_estructura(datos, h["seccion_bienestar"]),
        "A' · Consejería de bienestar social, sin fondos MRR/REACT-EU": serie_estructura(datos, h["seccion_bienestar"], True),
        "B · Función 23: servicios sociales y promoción social": serie_tabla(f, "funciones", [h["funcion_social"]]),
        "C · Subfunción 231: acción social": serie_tabla(f, "subfunciones", [h["subfuncion_nucleo"]]),
    }
    for bloque, cods in h["bloques_231"].items():
        perimetros[f"C · {bloque}"] = serie_tabla(f, "programas", cods)

    ind = pd.concat([indicadores(s, total).assign(perimetro=p) for p, s in perimetros.items()], ignore_index=True)
    ind["electoral"] = ind.anio.isin(E)
    ventana = datos.dim_anio.set_index("anio").ventana
    inicio = datos.dim_anio.dropna(subset=["ventana"]).groupby("ventana").anio.min()
    ind["legislatura"] = ind.anio.map(ventana)
    ind["posicion_ciclo"] = [a - inicio.get(v, a) + 1 if pd.notna(v) else None for a, v in zip(ind.anio, ind.legislatura)]
    ultimo = int(ind.anio.max())
    est_ipc = datos.dim_anio.set_index("anio").ipc_estatus

    # --- contraste por perímetro (constantes, medida principal = dif)
    resumen, legis = [], []
    for p in perimetros:
        for precios in ("constantes", "corrientes"):
            d = ind[(ind.perimetro == p) & (ind.precios == precios)].set_index("anio")
            for medida in ("dif", "dpeso", "g"):
                r = permutacion(d[medida], E)
                if r.get("k"):
                    resumen.append({"perimetro": p, "precios": precios, "medida": medida, **{k: v for k, v in r.items() if k != "rangos"},
                                    **{f"rango_{x}": r["rangos"].get(x) for x in E}})
            if precios == "constantes":
                legis.append(dentro_de_legislatura(d["dif"], E).assign(perimetro=p))
    res = pd.DataFrame(resumen)
    leg = pd.concat(legis, ignore_index=True)

    # --- Proyecto frente a Ley en 2023 (¿lo acentúan las enmiendas?)
    pl = []
    for fase in ("proyecto", "ley"):
        x = f[(f.anio_presupuesto == 2023) & (f.fase == fase) & (f.version_importe == "inicial") & (f.capitulo == "TOTAL")]
        if len(x):
            pl.append({"fase": fase, "funcion_23": x[(x.tabla == "funciones") & (x.codigo == "23")].importe_corriente.sum(),
                       "total": x[x.tabla == "programas"].importe_corriente.sum()})
    t_pl = pd.DataFrame(pl)

    # --- salidas tidy
    largo = ind.melt(id_vars=["perimetro", "anio", "precios", "electoral", "legislatura", "posicion_ciclo"],
                     value_vars=["importe", "g", "g_homog", "g_tot", "dif", "peso", "dpeso"], var_name="metrica", value_name="valor")
    largo["estatus_dato"] = np.where((largo.precios == "constantes") & (largo.anio.map(est_ipc) == "estimacion"), "estimacion", "verificado")
    SALIDA.mkdir(parents=True, exist_ok=True)
    largo.dropna(subset=["valor"]).to_csv(SALIDA / "hipotesis_electoral.csv", index=False)
    res.to_csv(SALIDA / "contraste_permutacion.csv", index=False)

    md = informe(ind, res, leg, t_pl, E, ultimo, perimetros, fase_por_anio(f))
    (SALIDA / "informe_hipotesis_electoral.md").write_text(md, encoding="utf-8")
    inf.escribir_xlsx(SALIDA / "tablas_hipotesis_electoral.xlsx", tablas_apa(ind, res, leg, perimetros))
    log_evento("analisis_hipotesis_electoral", filas=len(largo), contrastes=len(res))
    print(f"hipótesis electoral: {len(largo):,} filas tidy · {len(res)} contrastes · salidas/hipotesis_electoral/")
    principal = res[(res.precios == "constantes") & (res.medida == "dif")][["perimetro", "media_electoral", "media_resto", "p_unilateral"]]
    print(principal.round(3).to_string(index=False))
    return 0


# ----------------------------------------------------------------------------------------------- informe
def _tabla_anual(ind, p, E):
    d = ind[(ind.perimetro == p) & (ind.precios == "constantes")].sort_values("anio")
    return pd.DataFrame({"Año": [f"**{a}** ⚑" if a in E else str(a) for a in d.anio],
                         "Legislatura": d.legislatura.fillna("—"), "Importe (M€ const.)": d.importe.map(inf.meur),
                         "Var. real (%)": d.g.map(inf.num), "Var. real total (%)": d.g_tot.map(inf.num),
                         "Diferencial (pp)": d.dif.map(lambda v: inf.num(v, 1)), "Δ peso (pp)": d.dpeso.map(lambda v: inf.num(v, 2))})


def informe(ind, res, leg, t_pl, E, ultimo, perimetros, fases) -> str:
    obs = [a for a in E if a <= ultimo]
    pend = [a for a in E if a > ultimo]
    main_p = "B · Función 23: servicios sociales y promoción social"
    principal = res[(res.precios == "constantes") & (res.medida == "dif")].set_index("perimetro")
    n_anios = int(principal.n.max())   # presupuestos con variación calculable
    serie = "Ley" if fases.get(ultimo) == "ley" else f"Ley; {ultimo}: Proyecto"

    def veredicto(r):
        if r.diferencia > 0 and r.p_unilateral <= 0.10:
            return "a favor"
        if r.diferencia > 0:
            return "débil (positivo, no distinguible del azar)"
        return "en contra"

    def rango(v):
        return "—" if v is None or v != v else str(int(v))

    filas = []
    for p, r in principal.iterrows():
        filas.append({"Perímetro": p, "Dif. media años electorales (pp)": inf.num(r.media_electoral),
                      "Dif. media resto (pp)": inf.num(r.media_resto), "Diferencia (pp)": inf.num(r.diferencia),
                      f"Rango {' / '.join(map(str, obs))} (de {n_anios})": " / ".join(rango(r.get(f"rango_{x}")) for x in obs),
                      "p permutación": inf.num(r.p_unilateral, 2), "Lectura": veredicto(r)})
    t_res = pd.DataFrame(filas)
    t_leg = leg.assign(**{"Año": leg.anio.astype(str), "Dif. año electoral (pp)": leg.electoral.map(inf.num),
                          "Media de los 3 anteriores (pp)": leg.media_previos.map(inf.num),
                          "Máximo de los 3 anteriores (pp)": leg.max_previos.map(inf.num)})[
        ["perimetro", "Año", "Dif. año electoral (pp)", "Media de los 3 anteriores (pp)", "Máximo de los 3 anteriores (pp)"]
    ].rename(columns={"perimetro": "Perímetro"})

    # robustez: misma lectura con otras medidas / precios
    rob = res[(res.perimetro.isin(list(perimetros)[:4]))].copy()
    rob["Lectura"] = [veredicto(r) for r in rob.itertuples()]
    t_rob = rob.assign(**{"Medida": rob.medida.map({"dif": "diferencial", "dpeso": "Δ peso", "g": "variación"}),
                          "Electorales": rob.media_electoral.map(inf.num), "Resto": rob.media_resto.map(inf.num),
                          "p": rob.p_unilateral.map(lambda v: inf.num(v, 2))})[
        ["perimetro", "precios", "Medida", "Electorales", "Resto", "p", "Lectura"]].rename(columns={"perimetro": "Perímetro", "precios": "Precios"})

    b = principal.loc[main_p] if main_p in principal.index else None
    a_ = principal.iloc[0]
    n_favor = sum(veredicto(r) == "a favor" for _, r in principal.iterrows())
    resumen = (f"Con {len(obs)} presupuestos electorales observables ({', '.join(map(str, obs))}), "
               f"{n_favor} de {len(principal)} perímetros muestran una acentuación del gasto social distinguible del resto de años "
               f"(p ≤ 0,10 en la permutación exacta).")
    # umbral para 2027: diferencial que lo situaría por encima de todos los años no electorales de la legislatura actual
    umbrales = []
    for p in list(perimetros)[:4]:
        d = ind[(ind.perimetro == p) & (ind.precios == "constantes")].set_index("anio")
        actual = [x for x in (2024, 2025, 2026) if x in d.index]
        no_e = d[~d.index.isin(E)].dif.dropna()
        umbrales.append({"Perímetro": p, "Dif. 2024-2026 (pp)": " · ".join(inf.num(d.dif.get(x)) for x in actual),
                         "Máximo no electoral 2016-2026 (pp)": inf.num(no_e.max()),
                         "Media + 1 DE no electoral (pp)": inf.num(no_e.mean() + no_e.std())})
    t_umbral = pd.DataFrame(umbrales)

    partes = [
        "# Hipótesis: ¿se acentúa el gasto social en los presupuestos de años electorales?", "",
        f"Generado {ahora()} por `analisis_hipotesis_electoral.py`. Serie oficial 2015-{ultimo} ({serie}), euros constantes de 2025.", "",
        "## Resumen", "", f"**Estatus:** verificado (descripción) · la atribución a la intención electoral es *hipótesis*.", "",
        resumen,
        "",
        f"- Perímetro A (consejería de bienestar social, estructura actual): diferencial medio en años electorales "
        f"{inf.num(a_.media_electoral)} pp frente a {inf.num(a_.media_resto)} pp en el resto (p = {inf.num(a_.p_unilateral, 2)}).",
    ]
    if b is not None:
        partes.append(f"- Perímetro B (función 23): {inf.num(b.media_electoral)} pp frente a {inf.num(b.media_resto)} pp "
                      f"(p = {inf.num(b.p_unilateral, 2)}).")
    # lectura año a año: ¿el año electoral supera a todos los presupuestos previos de su legislatura?
    partes += ["", "**Lectura por año electoral** (diferencial real frente a los tres presupuestos previos de la misma legislatura):", ""]
    for anio in obs:
        fil = leg[(leg.anio == anio) & leg.perimetro.isin(list(perimetros)[:4])]
        supera = (fil.electoral > fil.max_previos).sum()
        sobre_media = (fil.electoral > fil.media_previos).sum()
        txt = ("**acentuación clara**: supera el máximo de su legislatura" if supera == len(fil) else
               "**acentuación parcial**: por encima de la media de su legislatura" if sobre_media == len(fil) else
               "**sin acentuación**: por debajo de la media de su legislatura" if sobre_media == 0 else "**resultado mixto**")
        puesto = principal.loc[main_p, f"rango_{anio}"] if main_p in principal.index and f"rango_{anio}" in principal.columns else None
        cuenta = supera if supera == len(fil) else sobre_media if sobre_media == len(fil) else \
            len(fil) - sobre_media if sobre_media == 0 else sobre_media
        partes.append(f"- **{anio}**: {txt} en {cuenta} de {len(fil)} perímetros amplios"
                      + (f" (función 23: puesto {int(puesto)} de {n_anios} en diferencial)" if puesto == puesto and puesto is not None else "") + ".")
    if pend:
        partes.append(f"- **{', '.join(map(str, pend))}**: pendiente de publicación; el contraste se repetirá automáticamente al cargarlo.")
    partes += [
        "",
        "**Comparaciones múltiples.** El desglose por programas hace 5 contrastes adicionales: con un umbral de 0,10, "
        "cabe esperar alrededor de uno «significativo» por azar. Un bloque aislado a favor no basta para sostener la hipótesis.",
        "",
        f"**Advertencia de potencia.** Con {len(obs)} casos electorales frente a {n_anios - len(obs)} no electorales, la permutación exacta solo puede "
        f"bajar hasta p = {inf.num(res.p_minimo.min(), 3)} y el contraste detecta únicamente efectos muy grandes. Un resultado "
        f"no significativo **no prueba** que el efecto no exista; un resultado significativo con {len(obs)} casos tampoco lo prueba.",
        "",
        "## 1. Definiciones",
        "",
        "- **Año electoral:** año de elecciones autonómicas (mayo). Su presupuesto lo diseña el gobierno saliente en otoño del año anterior: 2019 (Clavijo I), 2023 (Torres) y 2027 (Clavijo II).",
        "- **Gasto social:** tres perímetros estables. A = lo que hoy gestiona la Consejería de Bienestar Social (sección 23) retroproyectado a todos los años; "
        "B = función 23 de la clasificación funcional; C = subfunción 231 *Acción social* y sus programas.",
        "- **Acentuación:** que el gasto social crezca **más que el presupuesto total** ese año (diferencial, en pp) o gane peso. "
        "Se usa el diferencial y no la variación bruta porque los presupuestos electorales también suelen ser expansivos.",
        "",
        "## 2. Contraste principal (diferencial real, euros constantes)",
        "",
        inf.tabla_md(t_res),
        f"Rango: posición del año entre los {n_anios} presupuestos con variación calculable (1 = mayor diferencial). "
        f"p: proporción de combinaciones de {len(obs)} años cuya media es ≥ la de {'+'.join(map(str, obs))}.",
        "",
        "## 3. Cada año electoral frente a su propia legislatura",
        "",
        inf.tabla_md(t_leg),
        "",
        "## 4. Robustez (otras medidas y precios corrientes)",
        "",
        inf.tabla_md(t_rob),
        "",
        "## 5. Series anuales",
        "",
    ]
    for p in perimetros:
        partes += [f"### {p}", "", inf.tabla_md(_tabla_anual(ind, p, E)), ""]
    if len(t_pl) == 2:
        pr, le = t_pl.set_index("fase").loc["proyecto"], t_pl.set_index("fase").loc["ley"]
        partes += ["## 6. ¿Lo acentúa el Parlamento? Proyecto frente a Ley 2023", "",
                   f"Función 23: Proyecto {inf.meur(pr.funcion_23)} → Ley {inf.meur(le.funcion_23)} "
                   f"({inf.meur(le.funcion_23 - pr.funcion_23)}); total: {inf.meur(pr.total)} → {inf.meur(le.total)}. "
                   "Las enmiendas no cambian el total; cualquier diferencia es redistribución.", ""]
    partes += [
        "## 7. Qué mirar en el Proyecto 2027", "",
        "Valores de referencia para juzgar si 2027 rompe el patrón de los años no electorales (diferencial real, pp):", "",
        inf.tabla_md(t_umbral),
        "Si el diferencial de 2027 supera el máximo no electoral, habría un indicio descriptivo de acentuación; si queda dentro "
        "del rango 2024-2026, el presupuesto preelectoral seguiría la tendencia de la legislatura.", "",
        "## 8. Factores de confusión", "",
        "- **Dependencia:** el programa 231M crece por el calendario de la Ley de Dependencia y la financiación estatal (nivel mínimo y acordado), no solo por decisión autonómica.",
        "- **2023:** inflación de 2022-2023 (las cifras reales la descuentan) y fondos MRR/REACT-EU (perímetro A′ los resta, solo a nivel de sección).",
        "- **2019:** expansión general del presupuesto (+7,3 % nominal) y reorganización de 2020 (la vista estructura evita el salto orgánico).",
        "- **Presupuesto inicial, no ejecutado:** el anuncio electoral puede estar en el presupuesto inicial y no en la liquidación; contrastar con la ejecución sería el siguiente paso.",
        "- Ciclo político ≠ causalidad: coinciden en el tiempo la posición en la legislatura, la coyuntura económica y las transferencias del Estado.",
        "",
    ]
    return "\n".join(partes)


def tablas_apa(ind, res, leg, perimetros):
    out = []
    for p in list(perimetros)[:4]:
        d = ind[(ind.perimetro == p) & (ind.precios == "constantes")].sort_values("anio")
        out.append((f"{p}: variación real y diferencial frente al total",
                    pd.DataFrame({"Año": d.anio, "Electoral": np.where(d.electoral, "sí", ""), "Importe (M€)": (d.importe / 1e6).round(1),
                                  "Var. real (%)": d.g.round(2), "Var. real total (%)": d.g_tot.round(2),
                                  "Diferencial (pp)": d.dif.round(2), "Δ peso (pp)": d.dpeso.round(3)}),
                    "Euros constantes de 2025. Fuente: Tomo 3 (tablas 2.8, 2.9 y 2.16). Elaboración propia, ODESOCAN."))
    r = res[res.precios == "constantes"][["perimetro", "medida", "media_electoral", "media_resto", "diferencia", "p_unilateral"]].round(3)
    obs = sorted(ind.loc[ind.electoral, "anio"].unique())
    out.append((f"Contraste de permutación exacta: años electorales ({', '.join(map(str, obs))}) frente al resto", r,
                f"p unilateral = proporción de las {int(res.combinaciones.max())} combinaciones de {len(obs)} años "
                "con media ≥ la observada."))
    return out


if __name__ == "__main__":
    sys.exit(main())
