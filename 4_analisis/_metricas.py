"""Métricas del análisis (diseno_pipeline_presupuestos_2027.md §7.2). Funciones PURAS: sin E/S ni estado.

Entrada común: un «panel» largo con una fila por (id, anio, precios) y las columnas
    id, anio, precios, importe            obligatorias
    ajustado                              t-1 reexpresado en el tomo t (opcional: métricas homogéneas)
    padre                                 id del nivel superior (opcional: peso_padre_pct)
Salida común: filas tidy (id, anio, precios, ventana, metrica, valor, unidad).
Los porcentajes se expresan en % (38,1, no 0,381) como en los tomos.
"""
import numpy as np
import pandas as pd

COLS = ["id", "anio", "precios", "ventana", "metrica", "valor", "unidad"]
TOTAL = "__total__"   # id de las métricas de toda la dimensión (hhi, total)


def _filas(df: pd.DataFrame, metrica: str, valor: str, unidad: str, ventana: str = "anual") -> pd.DataFrame:
    out = df[["id", "anio", "precios"]].copy()
    out["ventana"], out["metrica"], out["valor"], out["unidad"] = ventana, metrica, df[valor].astype(float), unidad
    return out[out.valor.notna() & np.isfinite(out.valor)][COLS]


def _pivot(p: pd.DataFrame, col: str = "importe") -> pd.DataFrame:
    """id × anio por precios (MultiIndex en filas: precios, id)."""
    return p.pivot_table(index=["precios", "id"], columns="anio", values=col, aggfunc="sum")


# ------------------------------------------------------------------------------------------ anuales
def importe_y_peso(p: pd.DataFrame) -> pd.DataFrame:
    total = p.groupby(["anio", "precios"]).importe.transform("sum")
    d = p.assign(peso=100 * p.importe / total)
    partes = [_filas(d, "importe", "importe", "eur"), _filas(d, "peso_total_pct", "peso", "pct")]
    if "padre" in p and p.padre.notna().any():
        tp = p.groupby(["anio", "precios", "padre"]).importe.transform("sum")
        partes.append(_filas(d.assign(pp=100 * p.importe / tp.replace(0, np.nan)), "peso_padre_pct", "pp", "pct"))
    d["rank"] = d.groupby(["anio", "precios"]).importe.rank(ascending=False, method="min")
    partes.append(_filas(d, "rank_peso", "rank", "posicion"))
    return pd.concat(partes, ignore_index=True)


def por_habitante_y_pib(p: pd.DataFrame, poblacion: dict, pib: dict) -> pd.DataFrame:
    d = p.assign(pc=p.importe / p.anio.map(poblacion), pib=100 * p.importe / p.anio.map(pib))
    pib_ok = d[d.precios == "corrientes"]   # el PIB es nominal: % PIB solo en corrientes
    return pd.concat([_filas(d, "per_capita", "pc", "eur_hab"), _filas(pib_ok, "pct_pib", "pib", "pct")], ignore_index=True)


def variaciones(p: pd.DataFrame, anio_base: int = 2015) -> pd.DataFrame:
    """var_abs / var_pct entre años consecutivos (un hueco deja NaN) e índice base = 100."""
    w = _pivot(p)
    anios = sorted(w.columns)
    filas = []
    for a0, a1 in zip(anios, anios[1:]):
        if a1 != a0 + 1:
            continue
        va = w[a1] - w[a0]
        vp = 100 * va / w[a0].where(w[a0] != 0)
        filas += [pd.DataFrame({"precios": w.index.get_level_values(0), "id": w.index.get_level_values(1), "anio": a1,
                                "var_abs": va.values, "var_pct": vp.values})]
    d = pd.concat(filas, ignore_index=True) if filas else pd.DataFrame(columns=["precios", "id", "anio", "var_abs", "var_pct"])
    out = [_filas(d, "var_abs", "var_abs", "eur"), _filas(d, "var_pct", "var_pct", "pct")]
    if anio_base in w.columns:
        base = w[anio_base].where(w[anio_base] > 0)
        idx = w.div(base, axis=0) * 100
        li = idx.stack().rename("indice").reset_index()
        out.append(_filas(li, f"indice_{anio_base}", "indice", "indice"))
    return pd.concat(out, ignore_index=True)


def variaciones_homogeneas(p: pd.DataFrame) -> pd.DataFrame:
    """Δ_homog = inicial_t − ajustado_t (estructura de t); efecto_reestr = ajustado_t − inicial_{t-1} (§5.4)."""
    if "ajustado" not in p:
        return pd.DataFrame(columns=COLS)
    d = p[p.ajustado.notna()].copy()
    d["vah"] = d.importe - d.ajustado
    d["vph"] = 100 * d.vah / d.ajustado.where(d.ajustado != 0)
    prev = p[["id", "precios", "anio", "importe"]].assign(anio=p.anio + 1).rename(columns={"importe": "ini_prev"})
    d = d.merge(prev, on=["id", "precios", "anio"], how="left")
    d["reestr"] = d.ajustado - d.ini_prev   # sin año anterior (unidad nueva o enlace pendiente): no se imputa
    return pd.concat([_filas(d, "var_abs_homog", "vah", "eur"), _filas(d, "var_pct_homog", "vph", "pct"),
                      _filas(d, "efecto_reestr", "reestr", "eur")], ignore_index=True)


def flag_salto(p: pd.DataFrame, umbral_var: float, umbral_peso: float) -> pd.DataFrame:
    total = p.groupby(["anio", "precios"]).importe.transform("sum")
    d = p.assign(peso=100 * p.importe / total).sort_values(["precios", "id", "anio"])
    d["prev"] = d.groupby(["precios", "id"]).importe.shift()
    d["prev_anio"] = d.groupby(["precios", "id"]).anio.shift()
    d["vp"] = np.where(d.prev_anio == d.anio - 1, 100 * (d.importe - d.prev) / d.prev.where(d.prev != 0), np.nan)
    d["flag"] = ((d.vp.abs() > umbral_var) & (d.peso >= umbral_peso)).astype(float)
    return _filas(d[d.vp.notna()], "flag_salto", "flag", "flag")


def hhi(p: pd.DataFrame) -> pd.DataFrame:
    """Índice de Herfindahl de la dimensión: Σ peso² (peso en %), de 0 a 10.000."""
    total = p.groupby(["anio", "precios"]).importe.transform("sum")
    d = p.assign(c=(100 * p.importe / total) ** 2).groupby(["anio", "precios"], as_index=False).c.sum()
    d["id"] = TOTAL
    return _filas(d, "hhi", "c", "indice")


# ------------------------------------------------------------------------------------------ ventanas
def _tcac(fin, base, n):
    with np.errstate(divide="ignore", invalid="ignore"):
        return 100 * (np.power(fin / base, 1 / n) - 1)


def metricas_ventana(p: pd.DataFrame, ventanas: list[dict]) -> pd.DataFrame:
    """ventanas: [{"id", "base", "fin"}]. Una fila por (id, precios, ventana, métrica), con anio = fin."""
    w = _pivot(p)
    tot = p.groupby(["precios", "anio"]).importe.sum().unstack()
    denom = tot.loc[w.index.get_level_values(0)].set_axis(w.index)
    peso = 100 * w / denom
    filas = []
    for v in ventanas:
        b, f = v["base"], v["fin"]
        if b not in w.columns or f not in w.columns or f <= b:
            continue
        n = f - b
        ib, if_ = w[b], w[f]
        tb, tf = tot[b].reindex(w.index.get_level_values(0)).values, tot[f].reindex(w.index.get_level_values(0)).values
        tcac_total = _tcac(tf, tb, n)
        tcac = _tcac(if_.values, ib.where(ib > 0).values, n)
        d = pd.DataFrame({"precios": w.index.get_level_values(0), "id": w.index.get_level_values(1), "anio": f,
                          "var_abs": (if_ - ib).values, "var_pct": (100 * (if_ - ib) / ib.where(ib > 0)).values,
                          "tcac": tcac, "delta": (peso[f] - peso[b]).values,
                          "elas": np.where(tcac_total != 0, tcac / tcac_total, np.nan)})
        d["rank_delta"] = d.groupby("precios").delta.rank(ascending=False, method="min")
        for met, col, uni in (("var_abs_ventana", "var_abs", "eur"), ("var_pct_ventana", "var_pct", "pct"),
                              ("tcac_ventana", "tcac", "pct"), ("delta_peso_pp_ventana", "delta", "pp"),
                              ("elasticidad_ventana", "elas", "ratio"), ("rank_delta_peso", "rank_delta", "posicion")):
            filas.append(_filas(d, met, col, uni, ventana=v["id"]))
        # total de la dimensión en la ventana
        dt = pd.DataFrame({"precios": tot.index, "id": TOTAL, "anio": f, "tcac": _tcac(tot[f].values, tot[b].values, n),
                           "var_pct": (100 * (tot[f] - tot[b]) / tot[b]).values})
        filas += [_filas(dt, "tcac_ventana", "tcac", "pct", v["id"]), _filas(dt, "var_pct_ventana", "var_pct", "pct", v["id"])]
    return pd.concat(filas, ignore_index=True) if filas else pd.DataFrame(columns=COLS)


def ruptura_tendencia(ventana_tidy: pd.DataFrame, actual: str, anteriores: list[str]) -> pd.DataFrame:
    """tcac de la ventana actual − tcac de cada ventana anterior (pp). Positivo = acelera."""
    t = ventana_tidy[ventana_tidy.metrica == "tcac_ventana"]
    act = t[t.ventana == actual].set_index(["id", "precios"])
    filas = []
    for ant in anteriores:
        prev = t[t.ventana == ant].set_index(["id", "precios"]).valor
        d = act.assign(valor=act.valor - prev.reindex(act.index)).reset_index()
        d["metrica"], d["unidad"] = f"ruptura_tendencia_vs_{ant}", "pp"
        filas.append(d[d.valor.notna()][COLS])
    return pd.concat(filas, ignore_index=True) if filas else pd.DataFrame(columns=COLS)


def volatilidad(anual_tidy: pd.DataFrame, ventana: str, anio_fin: int) -> pd.DataFrame:
    """Coeficiente de variación de var_pct en toda la serie (std / |media|)."""
    v = anual_tidy[anual_tidy.metrica == "var_pct"]
    g = v.groupby(["id", "precios"]).valor.agg(["std", "mean", "count"]).reset_index()
    g = g[g["count"] >= 3]
    g["cv"] = g["std"] / g["mean"].abs().replace(0, np.nan)
    g["anio"] = anio_fin
    return _filas(g, "volatilidad_cv", "cv", "ratio", ventana=ventana)


def ventanas_desde(dim_anio: pd.DataFrame, anios_datos: list[int]) -> list[dict]:
    """Ventanas de config/legislaturas.yml acotadas a los años con datos + la serie completa."""
    ultimo, primero = max(anios_datos), min(anios_datos)
    out = []
    for vid, g in dim_anio.dropna(subset=["ventana"]).groupby("ventana", sort=False):
        base = g.base_comparacion.dropna()
        if base.empty:
            continue
        fin = min(int(g.anio.max()), ultimo)
        out.append({"id": vid, "base": int(base.iloc[0]), "fin": fin, "completa": fin == int(g.anio.max())})
    out = sorted(out, key=lambda v: v["base"])
    out.append({"id": f"{primero}_{ultimo}", "base": primero, "fin": ultimo, "completa": True})
    return out


def calcular_todo(p: pd.DataFrame, dim_anio: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Batería completa de §7.2 sobre un panel. Devuelve tidy (id, anio, precios, ventana, metrica, valor, unidad)."""
    anios = sorted(p.anio.unique())
    da = dim_anio.set_index("anio")
    ventanas = ventanas_desde(dim_anio, anios)
    partes = [importe_y_peso(p), variaciones(p), variaciones_homogeneas(p),
              por_habitante_y_pib(p, da.poblacion.to_dict(), da.pib_nominal.dropna().to_dict()),
              flag_salto(p, cfg["salto"]["var"], cfg["salto"]["peso"]), hhi(p)]
    anual = pd.concat([x for x in partes if len(x)], ignore_index=True)
    ven = metricas_ventana(p, ventanas)
    rup = ruptura_tendencia(ven, cfg["ventana_actual"], [cfg["ventana_anterior"], cfg["ventana_previa"]])
    completa = [v for v in ventanas if v["id"].endswith(f"_{max(anios)}") and v["base"] == min(anios)][0]["id"]
    vol = volatilidad(anual, completa, max(anios))
    return pd.concat([anual, ven, rup, vol], ignore_index=True)
