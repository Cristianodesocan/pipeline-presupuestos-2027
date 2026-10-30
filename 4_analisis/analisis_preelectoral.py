"""Exploración: ¿qué suele pasar en los presupuestos preelectorales? (años electorales de config/analisis.yml).

    python 4_analisis/analisis_preelectoral.py [--fuente local|supabase] [--anio-actual 2027]

Complementa a analisis_hipotesis_electoral.py: en vez de contrastar una partida (el gasto social), recorre TODAS
las partidas en cinco niveles y busca regularidades que se repitan en los presupuestos electorales observables
(2019 y 2023 con la serie 2015-2026; 2027 entra con su Proyecto):
  total · capítulos (naturaleza económica, tabla 2.11) · funciones (2.8) · consejerías en la estructura actual
  (retroproyección) · subfunciones (2.9) y programas (2.10, series continuas) con peso ≥ 0,5 %.
Medidas (euros constantes 2025):
  dif       variación real de la partida − variación real del total (pp): crece más o menos que el presupuesto
  anomalia  dif del año electoral − media del dif de los tres presupuestos previos de su legislatura (pp):
            ¿el año electoral rompe la tendencia de su propia legislatura?
  exceso    euros por encima (o por debajo) de lo que habría tenido la partida creciendo como el total
  p, q      permutación exacta de dif (años electorales frente al resto) y q de Benjamini-Hochberg por nivel
Una partida «se acentúa en los presupuestos electorales» si su anomalía es positiva en TODOS los años electorales
observados; se «contrae» si es negativa en todos. Salidas en 4_analisis/salidas/preelectoral/.
"""
import sys

import numpy as np
import pandas as pd

import _informes as inf
from _lectura import SALIDAS, ahora, argumentos, cfg, fase_por_anio, leer, log_evento, panel, recortar
from analisis_hipotesis_electoral import permutacion

SALIDA = SALIDAS / "preelectoral"
CAPITULOS = {"1": "Personal", "2": "Bienes corrientes y servicios", "3": "Gastos financieros",
             "4": "Transferencias corrientes", "6": "Inversiones reales", "7": "Transferencias de capital",
             "8": "Activos financieros"}
AGREGADOS_CAP = {"Gasto corriente (caps. 1-4)": list("1234"), "Gasto de capital (caps. 6-7)": list("67")}
PESO_MIN = 0.5


# ----------------------------------------------------------------------------------------------- unidades
def constantes(p: pd.DataFrame) -> pd.DataFrame:
    return p[p.precios == "constantes"][["id", "anio", "importe"]]


def unidades(datos) -> dict[str, tuple[pd.DataFrame, dict]]:
    """{nivel: (panel id/anio/importe en constantes, {id: etiqueta})}."""
    f = datos.fact
    of = f[f.serie_oficial & (f.version_importe == "inicial")]
    et = lambda tabla, por="codigo": of[of.tabla == tabla].sort_values("anio").groupby(por).denominacion_raw.last()  # noqa: E731
    niveles = {}

    cap = of[(of.tabla == "secciones_cap") & of.capitulo.isin(CAPITULOS)]
    pc = cap.groupby(["capitulo", "anio"], as_index=False).importe_constante.sum().rename(columns={"capitulo": "id", "importe_constante": "importe"})
    agr = [pc[pc.id.isin(c)].groupby("anio", as_index=False).importe.sum().assign(id=n) for n, c in AGREGADOS_CAP.items()]
    niveles["capitulo"] = (pd.concat([pc, *agr], ignore_index=True),
                           {**{k: f"Cap. {k} · {v}" for k, v in CAPITULOS.items()}, **{n: n for n in AGREGADOS_CAP}})

    niveles["funcion"] = (constantes(panel(f, "funciones", por="codigo")), (et("funciones") + " (" + et("funciones").index + ")").to_dict())
    e = datos.seccion_estructura.groupby(["seccion_destino", "anio"], as_index=False).importe_constante.sum()
    e = e.rename(columns={"seccion_destino": "id", "importe_constante": "importe"})
    e = e[~e.id.str.startswith("sin_equivalente")]     # artefacto de la retroproyección, no una consejería
    et_e = datos.seccion_estructura.drop_duplicates("seccion_destino").set_index("seccion_destino").denominacion_destino
    niveles["consejeria"] = (e, (et_e + " (" + et_e.index + ")").to_dict())
    niveles["subfuncion"] = (constantes(panel(f, "subfunciones", por="codigo")), (et("subfunciones") + " (" + et("subfunciones").index + ")").to_dict())
    dp = datos.dims["programa"].sort_values("anio_hasta").drop_duplicates("id_estable", keep="last")
    cont = set(dp[dp.comparabilidad == "continua"].id_estable)
    pp = constantes(panel(f, "programas", por="id_estable"))
    niveles["programa"] = (pp[pp.id.isin(cont)], dict(zip(dp.id_estable, dp.denominacion_std + " (" + dp.codigo + ")")))
    return niveles


# ----------------------------------------------------------------------------------------------- medidas
def medidas(p: pd.DataFrame, total: pd.Series, E: list[int]) -> pd.DataFrame:
    """Por (id, anio): g, dif, peso y exceso; por id y año electoral: anomalía frente a su legislatura."""
    w = p.pivot_table(index="id", columns="anio", values="importe", aggfunc="sum")
    anios = sorted(w.columns)
    filas = []
    for a0, a1 in zip(anios, anios[1:]):
        if a1 != a0 + 1:
            continue
        gt = 100 * (total[a1] / total[a0] - 1)
        g = 100 * (w[a1] / w[a0].where(w[a0] > 0) - 1)
        filas.append(pd.DataFrame({"id": w.index, "anio": a1, "g": g.values, "g_tot": gt, "dif": (g - gt).values,
                                   "peso": (100 * w[a1] / total[a1]).values,
                                   "exceso": (w[a1] - w[a0] * total[a1] / total[a0]).values}))
    return pd.concat(filas, ignore_index=True)


def benjamini_hochberg(p: pd.Series) -> pd.Series:
    p = p.dropna()
    if p.empty:
        return p
    orden = p.sort_values()
    m = len(orden)
    q = (orden * m / np.arange(1, m + 1))[::-1].cummin()[::-1].clip(upper=1)
    return q.reindex(p.index)


def resumen_nivel(m: pd.DataFrame, etiquetas: dict, E: list[int], peso_min: float | None) -> pd.DataFrame:
    obs = sorted({a for a in E if a in set(m.anio)})
    filas = []
    for idu, g in m.groupby("id"):
        d = g.set_index("anio")
        ultimo = d.index.max()
        if peso_min is not None and (pd.isna(d.peso.get(ultimo)) or d.peso.get(ultimo) < peso_min):
            continue
        fila = {"id": idu, "etiqueta": etiquetas.get(idu, idu), "peso_ultimo": d.peso.get(ultimo)}
        anomalias = []
        for a in obs:
            previos = [x for x in (a - 3, a - 2, a - 1) if x in d.index and pd.notna(d.dif.get(x))]
            if a in d.index and pd.notna(d.dif.get(a)) and previos:
                an = d.dif[a] - d.dif[previos].mean()
                fila[f"dif_{a}"], fila[f"anomalia_{a}"], fila[f"exceso_{a}"] = d.dif[a], an, d.exceso[a]
                anomalias.append(an)
        if not anomalias:
            continue
        r = permutacion(d.dif, obs)
        fila.update({"anomalia_media": float(np.mean(anomalias)), "p": r.get("p_unilateral"),
                     "p_contraccion": float(permutacion(-d.dif, obs).get("p_unilateral", np.nan)),
                     "patron": "se acentúa" if all(x > 0 for x in anomalias) and len(anomalias) == len(obs)
                     else "se contrae" if all(x < 0 for x in anomalias) and len(anomalias) == len(obs) else "mixto"})
        filas.append(fila)
    r = pd.DataFrame(filas)
    if len(r):
        r["q"] = benjamini_hochberg(r.p)
        r["q_contraccion"] = benjamini_hochberg(r.p_contraccion)
    return r


# ----------------------------------------------------------------------------------------------- programa
def main() -> int:
    a = argumentos(__doc__.split("\n")[0])
    datos = recortar(leer(a.fuente, a.confirmar_produccion), a.anio_actual)
    E = cfg()["hipotesis_electoral"]["anios_electorales"]
    tot_p = constantes(panel(datos.fact, "programas", por="perimetro"))
    total = tot_p.groupby("anio").importe.sum()
    obs = [x for x in E if x in total.index and x - 1 in total.index]

    niveles = unidades(datos)
    tidy, res = [], {}
    for nivel, (p, et) in niveles.items():
        m = medidas(p, total, E)
        tidy.append(m.assign(nivel=nivel, etiqueta=m.id.map(et), electoral=m.anio.isin(E)))
        res[nivel] = resumen_nivel(m, et, E, None if nivel in ("capitulo", "funcion", "consejeria") else PESO_MIN)

    # total: ¿el presupuesto electoral es más expansivo?
    g_tot = 100 * total.pct_change()
    g_tot = g_tot[g_tot.index.isin(total.index[1:]) & (g_tot.index - 1).isin(total.index)]
    r_tot = permutacion(g_tot, obs)
    leg_tot = []
    for x in obs:
        previos = [y for y in (x - 3, x - 2, x - 1) if y in g_tot.index]
        leg_tot.append({"anio": x, "g": g_tot[x], "media_previos": g_tot[previos].mean()})

    largo = pd.concat(tidy, ignore_index=True).melt(id_vars=["nivel", "id", "etiqueta", "anio", "electoral"],
                                                     value_vars=["g", "g_tot", "dif", "peso", "exceso"], var_name="metrica", value_name="valor")
    SALIDA.mkdir(parents=True, exist_ok=True)
    largo.dropna(subset=["valor"]).to_csv(SALIDA / "preelectoral.csv", index=False)
    pd.concat([r.assign(nivel=n) for n, r in res.items() if len(r)], ignore_index=True).to_csv(SALIDA / "patrones_preelectorales.csv", index=False)
    (SALIDA / "informe_preelectoral.md").write_text(informe(res, r_tot, leg_tot, g_tot, obs, E, total, fase_por_anio(datos.fact)),
                                                    encoding="utf-8")
    inf.escribir_xlsx(SALIDA / "tablas_preelectoral.xlsx", tablas_apa(res, obs))
    log_evento("analisis_preelectoral", filas=len(largo))
    print(f"preelectoral: {len(largo):,} filas tidy · niveles {', '.join(f'{n}={len(r)}' for n, r in res.items())} · salidas/preelectoral/")
    for n in ("capitulo", "funcion", "consejeria"):
        r = res[n]
        print(f"  {n}: se acentúa {', '.join(r[r.patron == 'se acentúa'].etiqueta.str[:28])} | se contrae {', '.join(r[r.patron == 'se contrae'].etiqueta.str[:28])}")
    return 0


# ----------------------------------------------------------------------------------------------- informe
def _tabla(r: pd.DataFrame, obs: list[int], patron: str | None = None, n: int | None = None, por="anomalia_media",
           asc=False) -> pd.DataFrame:
    if r.empty:
        return r
    x = r if patron is None else r[r.patron == patron]
    x = x.sort_values(por, ascending=asc)
    if n:
        x = x.head(n)
    out = pd.DataFrame({"Partida": x.etiqueta})
    for a in obs:
        out[f"Anomalía {a} (pp)"] = x.get(f"anomalia_{a}").map(inf.num) if f"anomalia_{a}" in x else "—"
        out[f"Exceso {a} (M€)"] = x.get(f"exceso_{a}").map(inf.meur).str.replace(" M€", "") if f"exceso_{a}" in x else "—"
    out["Peso último año (%)"] = x.peso_ultimo.map(lambda v: inf.num(v, 2))
    out["p / q"] = [f"{inf.num(p, 2)} / {inf.num(q, 2)}" for p, q in zip(x.p, x.q)]
    out["Patrón"] = x.patron
    return out


def informe(res, r_tot, leg_tot, g_tot, obs, E, total, fases) -> str:
    pend = [a for a in E if a not in obs and a > max(total.index)]
    ultimo = max(total.index)
    serie = "Ley" if fases.get(ultimo) == "ley" else f"Ley; {ultimo}: Proyecto"
    puesto = g_tot.rank(ascending=False)
    k_obs = len(obs)
    cuenta = lambda n, pat: int((res[n].patron == pat).sum()) if len(res[n]) else 0  # noqa: E731
    sig = {n: r[(r.q <= 0.10)] for n, r in res.items() if len(r)}
    sig_c = {n: r[(r.q_contraccion <= 0.10)] for n, r in res.items() if len(r)}
    t_leg = pd.DataFrame([{"Año": d["anio"], "Var. real del total (%)": inf.num(d["g"]),
                           "Media de los 3 previos de su legislatura (%)": inf.num(d["media_previos"])} for d in leg_tot])
    t_g = pd.DataFrame({"Año": [f"**{a}** ⚑" if a in E else str(a) for a in g_tot.index], "Var. real del total (%)": g_tot.map(inf.num).values})
    cap = res["capitulo"]
    k = lambda nombre: cap[cap.etiqueta == nombre].iloc[0] if (cap.etiqueta == nombre).any() else None  # noqa: E731
    corr, capi = k("Gasto corriente (caps. 1-4)"), k("Gasto de capital (caps. 6-7)")

    def linea_cap(fila, nombre):
        if fila is None:
            return ""
        partes_ = [f"{a}: {inf.num(fila.get(f'anomalia_{a}'))} pp" for a in obs]
        return f"- **{nombre}**: anomalía {' · '.join(partes_)} → *{fila.patron}*."

    p = [
        "# ¿Qué suele pasar en los presupuestos preelectorales?", "",
        f"Generado {ahora()} por `analisis_preelectoral.py`. Serie oficial {min(total.index)}-{ultimo} ({serie}), euros constantes de 2025. "
        f"Presupuestos electorales observables: {', '.join(map(str, obs))}" + (f"; pendiente: {', '.join(map(str, pend))}." if pend else "."), "",
        "## Resumen", "",
        "**Estatus:** verificado (descripción de cifras) · cualquier lectura sobre la intención electoral es *hipótesis*.", "",
        "- **Tamaño del presupuesto.** El total crece en términos reales "
        + ", ".join(f"un {inf.num(g_tot.get(a))} % en {a}" for a in obs)
        + f", frente a una media del {inf.num(r_tot.get('media_resto'))} % en los demás presupuestos (permutación p = {inf.num(r_tot.get('p_unilateral'), 2)}). "
        f"Puesto en crecimiento real (de {len(g_tot)}): " + " · ".join(f"{a}: {int(puesto[a])}.º" for a in obs) + ".",
        linea_cap(corr, "Gasto corriente (caps. 1-4)"),
        linea_cap(capi, "Gasto de capital (caps. 6-7)"),
        f"- **Partidas con el mismo signo en todos los años electorales:** funciones {cuenta('funcion', 'se acentúa')} se acentúan y "
        f"{cuenta('funcion', 'se contrae')} se contraen (de {len(res['funcion'])}); consejerías {cuenta('consejeria', 'se acentúa')} / "
        f"{cuenta('consejeria', 'se contrae')} (de {len(res['consejeria'])}); programas con peso ≥ 0,5 %: {cuenta('programa', 'se acentúa')} / "
        f"{cuenta('programa', 'se contrae')} (de {len(res['programa'])}).",
        f"- **Tras corregir por comparaciones múltiples** (q de Benjamini-Hochberg ≤ 0,10): "
        + (", ".join(f"{n}: {len(s)}" for n, s in sig.items()) or "ninguna") + " partidas con acentuación y "
        + (", ".join(f"{n}: {len(s)}" for n, s in sig_c.items()) or "ninguna") + " con contracción distinguibles del azar.",
        "",
        f"**Cómo leerlo.** Con {k_obs} casos, una regularidad «en todos los años» puede ser casualidad: si las anomalías fueran ruido "
        f"simétrico, una de cada {2 ** k_obs} partidas tendría el mismo signo positivo en los {k_obs} años y otra de cada {2 ** k_obs}, el "
        "negativo. El interés está en las partidas que repiten patrón **con importe relevante** y en si el patrón aparece "
        "en la naturaleza del gasto (capítulos), que es lo que predice la literatura sobre ciclos políticos presupuestarios: "
        "más gasto visible (inversión, transferencias) antes de las elecciones.",
        "",
        "## Lo que se repite con importe relevante", "",
        "Partidas (consejerías y subfunciones) con el mismo signo de anomalía en todos los años electorales y al menos "
        f"{inf.num(UMBRAL_EUR / 1e6, 0)} M€ de exceso acumulado. **«Se contrae» significa que crece menos que el total, no que se recorte.**", "",
        inf.tabla_md(relevantes(res, obs)),
        "", "## 1. El tamaño del presupuesto", "",
        inf.tabla_md(t_g), inf.tabla_md(t_leg),
        "Factor de confusión principal: la financiación autonómica (entregas a cuenta y liquidaciones) y los fondos MRR/REACT-EU, "
        "que determinan cuánto se puede presupuestar con independencia del calendario electoral.", "",
        "## 2. Naturaleza económica del gasto (capítulos, tabla 2.11)", "",
        "Anomalía = diferencial del año electoral frente a la media de los tres presupuestos previos de su legislatura. "
        "Exceso = euros por encima (+) o por debajo (−) de lo que habría tenido el capítulo creciendo como el total.", "",
        inf.tabla_md(_tabla(res["capitulo"], obs)),
        "## 3. Funciones de gasto", "",
        inf.tabla_md(_tabla(res["funcion"], obs)),
        "## 4. Consejerías (estructura actual, retroproyectada)", "",
        inf.tabla_md(_tabla(res["consejeria"], obs)),
        "## 5. Subfunciones con peso ≥ 0,5 % que repiten patrón", "",
        "**Se acentúan en todos los años electorales**", "", inf.tabla_md(_tabla(res["subfuncion"], obs, "se acentúa")),
        "**Se contraen en todos los años electorales**", "", inf.tabla_md(_tabla(res["subfuncion"], obs, "se contrae", asc=True)),
        "## 6. Programas (series continuas, peso ≥ 0,5 %) que repiten patrón", "",
        "**Se acentúan**", "", inf.tabla_md(_tabla(res["programa"], obs, "se acentúa", n=15)),
        "**Se contraen**", "", inf.tabla_md(_tabla(res["programa"], obs, "se contrae", n=15, asc=True)),
        "## 7. Qué vigilar en el Proyecto 2027", "",
        "- Las partidas que se acentúan en todos los años electorales y tienen importe relevante (secciones 3-6): si en 2027 "
        "vuelven a crecer por encima del total y de su propia tendencia 2024-2026, el patrón se repetiría por tercera vez.",
        "- El equilibrio entre gasto corriente y de capital: un salto del capítulo 6-7 sobre su tendencia sería la señal clásica de ciclo electoral.",
        "- Contrastar después con la **ejecución** (liquidación de 2019 y 2023): un presupuesto inicial expansivo que no se ejecuta es anuncio, no gasto.", "",
        "## 8. Limitaciones", "",
        f"- {k_obs} casos electorales: la permutación no puede bajar de p ≈ {inf.num(r_tot.get('p_minimo'), 3)} y la mayoría de efectos no serán distinguibles del azar.",
        ("- 2019, 2023 y 2027 los elaboraron gobiernos distintos (CC en minoría, PSOE-NC-Podemos-ASG y CC-PP)" if 2027 in obs else
         "- 2019 y 2023 los elaboraron gobiernos distintos (CC en minoría y PSOE-NC-Podemos-ASG)")
        + ": un patrón común no es atribuible a un partido.",
        "- 2023 se presupuestó con inflación alta y fondos europeos extraordinarios; 2019, en plena recuperación de ingresos.",
        ("- 2027 es el primer presupuesto casi sin fondos MRR/REACT-EU (447 M€ en 2026, 9 M€ en 2027; 316 M€ de ellos en Transición "
         "Ecológica y Energía): las consejerías que los gestionaban «se contraen» por esa salida, que no es una decisión del año electoral."
         if 2027 in obs else None),
        "- Deuda pública y capítulo 3 (gastos financieros): el salto de 2023 coincide con la subida de tipos de interés de 2022-2023, no con una decisión de gasto.",
        "- Diversas Consejerías (sección 19) agrupa fondos y créditos de reserva con oscilaciones muy grandes: su anomalía no es interpretable como prioridad.",
        "- Las elecciones autonómicas coinciden con las municipales y las insulares (mismo día de mayo): las transferencias a cabildos y ayuntamientos son el canal en el que cabría esperar un efecto electoral, pero el pipeline no puede separarlo del calendario de la financiación local.",
        "- Presupuesto inicial, no ejecutado; programas solo con series continuas (los reestructurados quedan fuera de la sección 6).",
        "",
    ]
    return "\n".join(x for x in p if x is not None)


UMBRAL_EUR = 20e6


def relevantes(res, obs) -> pd.DataFrame:
    filas = []
    for nivel in ("consejeria", "subfuncion"):
        r = res[nivel]
        if r.empty:
            continue
        exc = r[[f"exceso_{a}" for a in obs if f"exceso_{a}" in r]].sum(axis=1)
        sel = r[((r.patron == "se acentúa") & (exc >= UMBRAL_EUR)) | ((r.patron == "se contrae") & (exc <= -UMBRAL_EUR))]
        for i, x in sel.iterrows():
            filas.append({"Nivel": nivel, "Partida": x.etiqueta, "Patrón": x.patron,
                          "Exceso acumulado (M€)": inf.meur(exc[i]).replace(" M€", ""),
                          "Anomalía media (pp)": inf.num(x.anomalia_media), "p": inf.num(x.p if x.patron == "se acentúa" else x.p_contraccion, 2),
                          "_orden": exc[i]})
    t = pd.DataFrame(filas)
    return t.sort_values("_orden", ascending=False).drop(columns="_orden") if len(t) else t


def tablas_apa(res, obs):
    out = []
    for n, titulo in (("capitulo", "Capítulos"), ("funcion", "Funciones"), ("consejeria", "Consejerías (estructura actual)")):
        r = res[n].sort_values("anomalia_media", ascending=False)
        cols = ["etiqueta", *[c for a in obs for c in (f"anomalia_{a}", f"exceso_{a}")], "anomalia_media", "p", "q", "patron"]
        t = r[[c for c in cols if c in r]].copy()
        for c in t.columns:
            if c.startswith("exceso"):
                t[c] = (t[c] / 1e6).round(1)
            elif t[c].dtype.kind == "f":
                t[c] = t[c].round(3)
        out.append((f"{titulo}: anomalía de los presupuestos electorales frente a su legislatura", t,
                    "Anomalía en pp (diferencial frente al total, año electoral menos media de los 3 previos). Exceso en M€ constantes de 2025. "
                    "Fuente: Tomo 3. Elaboración propia, ODESOCAN."))
    return out


if __name__ == "__main__":
    sys.exit(main())
