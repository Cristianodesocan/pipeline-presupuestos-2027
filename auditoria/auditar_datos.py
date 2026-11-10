"""Auditoría de los datos de la web (5_visualizacion/data/viz_*.csv).

    .venv/bin/python auditoria/auditar_datos.py            # todo (lee los PDF de 1_extraccion/raw: ~2 min)
    .venv/bin/python auditoria/auditar_datos.py --sin-pdf  # solo coherencia interna y cálculos de la web

Tres niveles, cada uno independiente del anterior:
  1. FUENTE      los CSV frente al Tomo 3 oficial, leído con un lector propio (auditoria/fuente_pdf.py), distinto del
                 extractor del pipeline: importes, pesos, variaciones y capítulos, documento a documento.
  2. COHERENCIA  invariantes entre y dentro de los CSV: totales iguales entre dimensiones, pesos que suman 100,
                 precios constantes = corrientes × deflactor, capítulos que cuadran, fases, ventanas, duplicados…
  3. CÁLCULOS    lo que la web calcula en el navegador (variación en euros, donut, por habitante, % del PIB, ranking,
                 «Sigue el dinero», recorrido), recalculado aquí de forma independiente y contrastado con el pipeline.
Salida: auditoria/resultados_datos.json (lo usa auditoria/auditar_web.cjs para el nivel 4, la pantalla).
Código de salida: 0 sin errores; 1 si alguna comprobación da ERROR (los AVISO son diferencias explicadas).
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DATA = RAIZ / "5_visualizacion" / "data"
RAW = RAIZ / "1_extraccion" / "raw"
SALIDA = Path(__file__).resolve().parent / "resultados_datos.json"
CAPS18 = [1, 2, 3, 4, 6, 7, 8]
CAPS = CAPS18 + [9]
TOL_EUR = 0.5          # céntimos de redondeo en importes enteros
TOL_PCT = 0.0051       # el Tomo publica los % con 2 decimales

resultados = []


def eur(v, decimales=0):
    """Cifra en formato español para los ejemplos del informe: 3301248249 → «3.301.248.249»."""
    return f"{v:,.{decimales}f}".replace(",", "~").replace(".", ",").replace("~", ".")


def registrar(nivel, cid, titulo, comprobados, fallos, ejemplos=(), estado=None, nota=""):
    estado = estado or ("OK" if not fallos else "ERROR")
    resultados.append({"nivel": nivel, "id": cid, "titulo": titulo, "comprobados": int(comprobados), "fallos": int(fallos),
                       "estado": estado, "nota": nota, "ejemplos": [str(e) for e in list(ejemplos)[:6]]})
    marca = {"OK": "✔", "AVISO": "▲", "ERROR": "✘"}[estado]
    print(f"  {marca} [{cid}] {titulo}: {comprobados} comprobados, {fallos} con diferencia{(' · ' + nota) if nota else ''}")
    for e in list(ejemplos)[:3] if fallos else []:
        print(f"        {e}")


# ------------------------------------------------------------------------------------------------ datos
def cargar():
    tipos = {"id_estable": str, "id_grupo": str, "seccion": str, "programa": str, "nivel_1": str, "nivel_2": str}
    t = pd.read_csv(DATA / "viz_treemap.csv", dtype=tipos)
    s = pd.read_csv(DATA / "viz_series.csv", dtype=tipos)
    c = pd.read_csv(DATA / "viz_capitulos.csv", dtype=tipos)
    a = pd.read_csv(DATA / "viz_anios.csv")
    m = pd.read_csv(DATA / "viz_meta.csv")
    for df in (t, s, c):
        df["anio"] = df["anio"].astype(int)
    return t[t.id_estable != "__total__"].copy(), s[s.id_estable != "__total__"].copy(), c, a, m


def codigo(df, dimension):
    if dimension == "seccion":
        return df.id_estable.str.extract(r"^S?(\d{2})(?:_|$)")[0]
    if dimension == "funcion":
        return df.id_estable.str.extract(r"^F(\d{2})_")[0]
    if dimension == "subfuncion":
        return df.id_estable.str.extract(r"^SF(\d{3})_")[0]
    return df.etiqueta.str.extract(r"\(([0-9A-Z]{2,6})\)\s*$")[0]      # programas (312A) y entes (SCS)


def documentos():
    """Documento de la serie oficial de cada año: la Ley si existe; si no, el Proyecto."""
    out = {}
    for d in sorted(RAW.iterdir()) if RAW.exists() else []:
        if not d.name.isdigit():
            continue
        for fase in ("ley", "proyecto"):
            pdfs = sorted((d / fase).glob("*.pdf")) if (d / fase).exists() else []
            if pdfs:
                out[int(d.name)] = (fase, pdfs[-1])
                break
    return out


# ------------------------------------------------------------------------------------------------ nivel 1
def nivel_fuente(t, c):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from fuente_pdf import leer_documento
    docs = documentos()
    if not docs:
        registrar(1, "F0", "PDF del Tomo 3 disponibles", 0, 0, estado="AVISO", nota="no hay 1_extraccion/raw: ejecuta la extracción")
        return
    print(f"  leyendo {len(docs)} documentos del Tomo 3 con el lector independiente…")
    leidos = {anio: leer_documento(ruta) for anio, (fase, ruta) in docs.items()}
    fases_csv = t.groupby("anio").fase.first().to_dict()
    malas = [f"{a}: PDF {f} · web {fases_csv.get(a)}" for a, (f, _) in docs.items() if fases_csv.get(a) != f]
    registrar(1, "F0", "Documento de cada año = fase que muestra la web (Ley, o Proyecto si no hay Ley)", len(docs), len(malas), malas)

    tc = t[t.precios == "corrientes"]
    previo = tc.set_index(["dimension", "vista", "id_estable", "anio"]).importe
    pares = [("secciones", "seccion", "organica", "F1"), ("funciones", "funcion", "individual", "F2"),
             ("subfunciones", "subfuncion", "individual", "F3"), ("programas", "programa", "individual", "F4"),
             ("entes", "ente", "individual", "F5")]
    for tabla, dim, vista, cid in pares:
        n = fi = np_ = fp = nv = fv = expl = 0
        ej_i, ej_p, ej_v = [], [], []
        enlaces = []        # diferencias en que la web compara con OTRO código del año anterior (enlace del crosswalk)
        for anio, doc in leidos.items():
            pdf = doc[tabla]["filas"]
            w = tc[(tc.dimension == dim) & (tc.vista == vista) & (tc.anio == anio)].copy()
            w["cod"] = codigo(w, dim)
            web = w.set_index("cod")
            for cod, v in pdf.items():
                ini, pct, var, ajust = v[2], v[3], v[4], v[0]
                if not ini:
                    continue
                n += 1
                if cod not in web.index:
                    fi += 1; ej_i.append(f"{anio} {cod}: en el Tomo ({eur(ini, 0)} €) y no en la web"); continue
                r = web.loc[cod]
                if isinstance(r, pd.DataFrame):
                    r = r.iloc[0]
                if abs(r.importe - ini) > TOL_EUR:
                    fi += 1; ej_i.append(f"{anio} {cod}: Tomo {eur(ini, 0)} € · web {eur(r.importe, 2)} €")
                if pct is not None:
                    np_ += 1
                    if abs(r.peso_total_pct - pct) > TOL_PCT:
                        fp += 1; ej_p.append(f"{anio} {cod}: Tomo {pct} % · web {r.peso_total_pct:.4f} %")
                if var is not None and pd.notna(r.var_pct_interanual):
                    nv += 1
                    if abs(r.var_pct_interanual - var) > TOL_PCT:
                        ant = previo.get((dim, vista, r.id_estable, anio - 1))
                        if ajust is not None and ant is not None and abs(ajust - ant) > TOL_EUR:
                            expl += 1            # el Tomo compara con el «ajustado» (reestructurado), la web con el inicial
                            prev = leidos.get(anio - 1, {}).get(tabla, {}).get("filas", {}).get(cod)
                            if not (prev and prev[2] is not None and abs(prev[2] - ant) <= TOL_EUR):
                                enlaces.append(f"{anio} {cod} «{r.etiqueta}»: la web compara con {eur(ant, 0)} € del año anterior "
                                               f"(otro código, enlazado por el crosswalk); el Tomo, con {eur(ajust, 0)} € ajustados")
                        else:
                            fv += 1; ej_v.append(f"{anio} {cod}: Tomo {var} % · web {r.var_pct_interanual:.4f} %")
            sobran = [c_ for c_ in web.index if c_ not in pdf and web.loc[c_].importe.sum() > 0] if len(web) else []
            for c_ in sobran:
                fi += 1; ej_i.append(f"{anio} {c_}: en la web y no en el Tomo")
        nombre = {"secciones": "secciones (tabla 2.1)", "funciones": "funciones (2.8)", "subfunciones": "subfunciones (2.9)",
                  "programas": "programas (2.10)", "entes": "entes (3.1)"}[tabla]
        registrar(1, cid + "a", f"Importe inicial de cada fila de {nombre} = Tomo, al euro", n, fi, ej_i)
        registrar(1, cid + "b", f"Peso sobre el total de {nombre} = % del Tomo", np_, fp, ej_p)
        registrar(1, cid + "c", f"Variación interanual de {nombre} = % «2/1» del Tomo", nv, fv, ej_v,
                  estado=("ERROR" if fv else ("AVISO" if expl else "OK")),
                  nota=(f"{expl} diferencias explicadas: el Tomo compara con el presupuesto anterior AJUSTADO a la nueva estructura "
                        "y la web, con el inicial de la misma partida" if expl else ""))
        registrar(1, cid + "d", f"De esas diferencias, cuántas vienen de enlazar {nombre.split(' (')[0]} de códigos distintos entre años "
                  "(a revisar)", expl, len(enlaces), enlaces, estado=("AVISO" if enlaces else "OK"),
                  nota="el resto compara el mismo código en los dos años" if expl else "")

    # totales del Tomo frente a la suma de la web, por dimensión
    n = f = 0; ej = []
    for anio, doc in leidos.items():
        tot = doc["secciones"]["total"]
        if not tot:
            continue
        for dim, vista in (("seccion", "organica"), ("funcion", "individual"), ("subfuncion", "individual"),
                           ("programa", "individual"), ("programa", "familia"), ("seccion", None)):
            vistas = [vista] if vista else [v for v in tc[tc.dimension == "seccion"].vista.unique() if v.startswith("estructura")]
            for vi in vistas:
                suma = tc[(tc.dimension == dim) & (tc.vista == vi) & (tc.anio == anio)].importe.sum()
                n += 1
                if abs(suma - tot[2]) > 1:
                    f += 1; ej.append(f"{anio} {dim}/{vi}: web {eur(suma, 0)} € · Tomo {eur(tot[2], 0)} €")
    registrar(1, "F6", "Total de cada dimensión y vista = «TOTAL CAPÍTULOS DEL 1 AL 8» del Tomo", n, f, ej)

    # capítulos: secciones (2.11) y funciones (2.13) frente a viz_capitulos
    for tabla, dim, vista, cid, nombre in (("secciones_cap", "seccion", "organica", "F7", "secciones (2.11)"),
                                           ("funciones_cap", "funcion", "individual", "F8", "funciones (2.13)")):
        n = f = 0; ej = []
        for anio, doc in leidos.items():
            w = c[(c.dimension == dim) & (c.vista == vista) & (c.anio == anio)].copy()
            w["cod"] = codigo(w, dim)
            web = w.set_index("cod")
            for cod, v in doc[tabla]["filas"].items():
                if not v[-1]:
                    continue
                for i, cap in enumerate(CAPS):
                    n += 1
                    val = web.loc[cod, f"cap_{cap}"] if cod in web.index else None
                    if val is None or abs(val - (v[i] or 0)) > TOL_EUR:
                        f += 1; ej.append(f"{anio} {cod} cap. {cap}: Tomo {v[i]} · web {val}")
            tot = doc[tabla]["total"]
            for i, cap in enumerate(CAPS):
                n += 1
                suma = c[(c.dimension == dim) & (c.vista == vista) & (c.anio == anio)][f"cap_{cap}"].sum()
                if tot is None or abs(suma - (tot[i] or 0)) > 1:
                    f += 1; ej.append(f"{anio} total cap. {cap}: Tomo {tot[i] if tot else None} · web {eur(suma, 0)}")
        registrar(1, cid, f"Capítulos 1-9 de {nombre} y su fila Total = Tomo, al euro", n, f, ej)

    # entes: el total de capítulos (tabla 3.2) frente al comparativo (3.1)
    n = f = 0; ej = []
    ce = c[(c.dimension == "ente") & (c.vista == "individual")].copy()
    ce["c18"] = ce[[f"cap_{k}" for k in CAPS18]].sum(axis=1)
    te = tc[tc.dimension == "ente"].set_index(["anio", "id_estable"]).importe
    for r in ce.itertuples():
        imp = te.get((r.anio, r.id_estable))
        if imp is None:
            continue
        n += 1
        if abs(imp - r.c18) > TOL_EUR:
            f += 1; ej.append(f"{r.anio} {r.id_estable}: tabla 3.1 {eur(imp, 0)} € · capítulos (3.2) {eur(r.c18, 0)} € ({'+' if r.c18 >= imp else '−'}{eur(abs(r.c18 - imp), 0)} €)")
    registrar(1, "F9", "Entes: capítulos de la tabla 3.2 = importe de la tabla 3.1", n, f, ej,
              estado=("AVISO" if f else "OK"),
              nota="discrepancia dentro del propio Tomo: la web muestra la 3.1 en el treemap y la 3.2 en el donut" if f else "")
    return leidos


# ------------------------------------------------------------------------------------------------ nivel 2
def nivel_coherencia(t, s, c, a, m):
    defl = a.set_index("anio").deflactor
    # I1 claves únicas
    n = f = 0; ej = []
    for nombre, df, k in (("treemap", t, ["dimension", "vista", "anio", "precios", "id_estable"]),
                          ("series", s, ["dimension", "vista", "id_estable", "anio", "precios"]),
                          ("capitulos", c, ["dimension", "vista", "anio", "id_estable", "id_grupo", "seccion", "programa"])):
        d = df.duplicated(k, keep=False)
        n += len(df); f += int(d.sum())
        if d.any():
            ej.append(f"{nombre}: {int(d.sum())} filas repetidas, p. ej. {df[d].iloc[0][k].tolist()}")
    registrar(2, "I1", "Sin filas duplicadas en los CSV", n, f, ej)
    # I2 sin negativos ni vacíos donde no debe
    neg = (t.importe < 0).sum() + (s.importe < 0).sum() + sum((c[f"cap_{k}"] < -TOL_EUR).sum() for k in CAPS)
    vac = t.etiqueta.isna().sum() + s.etiqueta.isna().sum()
    registrar(2, "I2", "Sin importes negativos ni partidas sin nombre", len(t) + len(s) + len(c), int(neg + vac))
    # I3 totales iguales entre dimensiones (mismo perímetro caps. 1-8)
    n = f = 0; ej = []
    base = t[(t.dimension == "funcion")].groupby(["anio", "precios"]).importe.sum()
    for (dim, vista), g in t[t.dimension.isin(["subfuncion", "seccion", "programa", "area"])].groupby(["dimension", "vista"]):
        if vista == "concepto_ced":
            continue
        tot = g.groupby(["anio", "precios"]).importe.sum()
        for k, v in tot.items():
            n += 1
            if abs(v - base[k]) > 1:
                f += 1; ej.append(f"{dim}/{vista} {k}: {eur(v, 0)} € frente a funciones {eur(base[k], 0)} €")
    registrar(2, "I3", "Mismo total por año en funciones, subfunciones, áreas, secciones (2 vistas) y programas (2 vistas)", n, f, ej)
    # I4 pesos: suman 100 y = importe / total
    n = f = 0; ej = []
    for k, g in t[~t.vista.eq("concepto_ced")].groupby(["dimension", "vista", "anio", "precios"]):
        tot = g.importe.sum()
        err = (g.peso_total_pct - 100 * g.importe / tot).abs()
        n += len(g); f += int((err > 1e-6).sum())
        if (err > 1e-6).any():
            ej.append(f"{k}: peso con error máx. {err.max():.6f} pp")
    registrar(2, "I4", "Peso sobre el total = importe / total de la tabla × 100 (y suman 100)", n, f, ej)
    # I5 precios constantes = corrientes × deflactor del año
    n = f = 0; ej = []
    for nombre, df, k in (("treemap", t, ["dimension", "vista", "anio", "id_estable"]),
                          ("series", s, ["dimension", "vista", "anio", "id_estable"])):
        p = df.pivot_table(index=k, columns="precios", values="importe", aggfunc="first").dropna().reset_index()
        esp = p.corrientes * p.anio.map(defl)
        err = (p.constantes - esp).abs() / esp.abs().clip(lower=1)
        n += len(p); f += int((err > 1e-9).sum())
        if (err > 1e-9).any():
            ej.append(f"{nombre}: {int((err > 1e-9).sum())} filas, p. ej. {p[err > 1e-9].iloc[0][k].tolist()}")
    registrar(2, "I5", "Euros constantes = corrientes × deflactor del año (viz_anios)", n, f, ej)
    # I6 treemap y series cuentan lo mismo
    k = ["dimension", "vista", "id_estable", "anio", "precios"]
    j = t.merge(s, on=k, suffixes=("_t", "_s"))
    err = (j.importe_t - j.importe_s).abs() > TOL_EUR
    errv = ((j.var_pct_interanual - j.var_pct).abs() > 1e-9) & j.var_pct.notna()
    registrar(2, "I6", "Treemap y series: mismo importe y misma variación % para cada partida y año", len(j) * 2,
              int(err.sum() + errv.sum()), j[err | errv][k].head(3).values.tolist())
    # I7 variación interanual = importe del año / importe del año anterior (misma partida) − 1
    n = f = 0; ej = []
    for kk, g in s.groupby(["dimension", "vista", "id_estable", "precios"]):
        g = g.sort_values("anio")
        ant = g.importe.shift(1)
        ok = g.var_pct.notna() & ant.notna() & (g.anio.diff() == 1)
        esp = 100 * (g.importe / ant - 1)
        err = ((g.var_pct - esp).abs() > 1e-6) & ok
        n += int(ok.sum()); f += int(err.sum())
        if err.any():
            ej.append(f"{kk} {g[err].anio.tolist()}")
        erra = ((g.var_abs - (g.importe - ant)).abs() > TOL_EUR) & ok
        f += int(erra.sum())
    registrar(2, "I7", "Variación interanual (% y €) = frente al presupuesto inicial anterior de la misma partida", n, f, ej)
    # I8 ventana del gobierno actual: Δ peso y variación = último año frente a la base
    ven = m[m.tipo == "ventana"].set_index("id")
    base_a, fin_a = int(ven.loc["clavijo_ii", "inicio"]) - 1, int(min(ven.loc["clavijo_ii", "fin"], t.anio.max()))
    n = f = 0; ej = []
    for kk, g in t[~t.vista.eq("concepto_ced")].groupby(["dimension", "vista", "id_estable", "precios"]):
        g = g.set_index("anio")
        if base_a not in g.index or fin_a not in g.index:
            continue
        d_esp = g.loc[fin_a, "peso_total_pct"] - g.loc[base_a, "peso_total_pct"]
        v_esp = 100 * (g.loc[fin_a, "importe"] / g.loc[base_a, "importe"] - 1) if g.loc[base_a, "importe"] else np.nan
        dd, vv = g.delta_peso_pp_clavijo_ii.dropna(), g.var_pct_clavijo_ii.dropna()
        if dd.empty:
            continue
        n += 1
        if abs(dd.iloc[0] - d_esp) > 1e-6 or (not vv.empty and pd.notna(v_esp) and abs(vv.iloc[0] - v_esp) > 1e-6):
            f += 1; ej.append(f"{kk}: Δ {dd.iloc[0]:.4f} frente a {d_esp:.4f}")
    registrar(2, "I8", f"Δ peso y variación del gobierno actual = {fin_a} frente a {base_a}", n, f, ej)
    # I9 fases y ventanas por año
    fases = s.groupby("anio").fase.unique()
    raras = [f"{a}: {list(v)}" for a, v in fases.items() if len(v) != 1 or (v[0] == "proyecto") != (a == s.anio.max())]
    vent = s.groupby("anio").ventana.unique()
    import yaml
    leg = yaml.safe_load(open(RAIZ / "config" / "legislaturas.yml", encoding="utf-8"))["ventanas"]
    esperada = {a: v["id"] for v in leg for a in range(v["presupuestos"][0], v["presupuestos"][1] + 1)}
    raras += [f"{a}: ventana {list(v)} y legislaturas.yml dice {esperada.get(a)}" for a, v in vent.items() if list(v) != [esperada.get(a)]]
    registrar(2, "I9", "Fase (solo el último año en Proyecto) y gobierno de cada año = config/legislaturas.yml", len(fases) * 2, len(raras), raras)
    # I10 capítulos: caps. 1-8 = importe del treemap (salvo entes, ver F9)
    cc = c.copy(); cc["c18"] = cc[[f"cap_{k}" for k in CAPS18]].sum(axis=1)
    tc = t[t.precios == "corrientes"]
    n = f = 0; ej = []
    agregados = [("funcion", "individual", cc[(cc.dimension == "funcion")], "id_estable"),
                 ("subfuncion", "individual", cc[cc.dimension == "subfuncion"], "id_estable"),
                 ("seccion", "organica", cc[(cc.dimension == "seccion") & (cc.vista == "organica")], "id_estable"),
                 ("programa", "individual", cc[cc.dimension == "programa"], "id_estable"),
                 ("programa", "familia", cc[cc.dimension == "programa"], "id_grupo")]
    agregados += [("seccion", v, cc[(cc.dimension == "seccion") & (cc.vista == v)], "id_estable")
                  for v in cc.vista.unique() if str(v).startswith("estructura")]
    for dim, vista, df, clave in agregados:
        sumas = df.groupby(["anio", clave]).c18.sum()
        w = tc[(tc.dimension == dim) & (tc.vista == vista)].set_index(["anio", "id_estable"]).importe
        jj = pd.concat([sumas.rename("caps"), w.rename("imp")], axis=1).fillna(0)
        jj = jj[(jj.caps.abs() > TOL_EUR) | (jj.imp.abs() > TOL_EUR)]
        err = (jj.caps - jj.imp).abs() > 1
        n += len(jj); f += int(err.sum())
        ej += [f"{dim}/{vista} {i}: caps {eur(r.caps, 0)} · importe {eur(r.imp, 0)}" for i, r in jj[err].head(2).iterrows()]
    registrar(2, "I10", "Capítulos 1-8 de cada partida (todas las dimensiones y vistas menos entes) = su importe en la web", n, f, ej)
    # I11 coherencia interna de los capítulos
    n = f = 0; ej = []
    secc = cc[(cc.dimension == "seccion") & (cc.vista == "organica")]
    pares = cc[cc.dimension == "programa"]
    for cap in CAPS:
        x = pares.groupby(["anio", "seccion"])[f"cap_{cap}"].sum()
        y = secc.assign(cod=codigo(secc, "seccion")).groupby(["anio", "cod"])[f"cap_{cap}"].sum()
        jj = pd.concat([x, y], axis=1).fillna(0)
        n += len(jj); err = (jj.iloc[:, 0] - jj.iloc[:, 1]).abs() > 1; f += int(err.sum())
        ej += [f"cap. {cap} {i}: programas {eur(r.iloc[0], 0)} · sección {eur(r.iloc[1], 0)}" for i, r in jj[err].head(1).iterrows()]
    ent = cc[(cc.dimension == "ente") & (cc.vista == "individual")].set_index(["anio", "id_estable"])
    ep = cc[(cc.dimension == "ente") & (cc.vista == "programa")].groupby(["anio", "id_estable"])[[f"cap_{k}" for k in CAPS]].sum()
    dif = (ent[[f"cap_{k}" for k in CAPS]] - ep.reindex(ent.index).fillna(0)).abs().max(axis=1)
    n += len(dif); f += int((dif > 1).sum())
    for v in [x for x in cc.vista.unique() if str(x).startswith("estructura")]:
        a1 = cc[(cc.dimension == "seccion") & (cc.vista == v)].groupby("anio").c18.sum()
        a2 = secc.groupby("anio").c18.sum()
        err = (a1 - a2).abs() > 1
        n += len(a1); f += int(err.sum())
        ej += [f"estructura {i}: {eur(a1[i], 0)} · orgánica {eur(a2[i], 0)}" for i in a1[err].index[:2]]
    defl_c = (cc.deflactor - cc.anio.map(defl)).abs() > 1e-12
    n += len(cc); f += int(defl_c.sum())
    registrar(2, "I11", "Capítulos: pares sección×programa = secciones; programas de cada ente = ente; estructura = orgánica; "
                       "deflactor = viz_anios", n, f, ej)
    # I12 jerarquía de programas: función y subfunción coinciden con el código del programa
    p = t[(t.dimension == "programa") & (t.vista == "individual") & (t.precios == "corrientes")].copy()
    p["cod"] = codigo(p, "programa")
    fun = t[t.dimension == "funcion"].assign(cod=lambda d: codigo(d, "funcion")).drop_duplicates(["anio", "cod"]).set_index(["anio", "cod"]).etiqueta
    sub = t[t.dimension == "subfuncion"].assign(cod=lambda d: codigo(d, "subfuncion")).drop_duplicates(["anio", "cod"]).set_index(["anio", "cod"]).etiqueta
    mal = []
    for r in p.itertuples():
        f_ = fun.get((r.anio, r.cod[:2])); s_ = sub.get((r.anio, r.cod[:3]))
        if (f_ is not None and f_ != r.nivel_1) or (s_ is not None and s_ != r.nivel_2):
            mal.append(f"{r.anio} {r.cod}: función «{r.nivel_1}» / subfunción «{r.nivel_2}» frente a «{f_}» / «{s_}»")
    registrar(2, "I12", "Cada programa cuelga de la función y subfunción que indica su código", len(p), len(mal), mal)
    # I14 peso en el grupo = importe / suma de su grupo (el nivel inmediatamente superior)
    n = f = 0; ej = []
    for (dim, vista), g in t[~t.vista.eq("concepto_ced")].groupby(["dimension", "vista"]):
        padre = "nivel_2" if g.nivel_2.notna().any() else "nivel_1"
        if g[padre].isna().all() or g.peso_padre_pct.isna().all():
            continue
        tot = g.groupby(["anio", "precios", padre]).importe.transform("sum")
        err = ((g.peso_padre_pct - 100 * g.importe / tot).abs() > 1e-6) & g.peso_padre_pct.notna()
        n += int(g.peso_padre_pct.notna().sum()); f += int(err.sum())
        if err.any():
            ej.append(f"{dim}/{vista}: {int(err.sum())} filas, p. ej. {g[err].iloc[0][['anio', 'id_estable']].tolist()}")
    registrar(2, "I14", "Peso en el grupo = importe / total de su grupo inmediato × 100", n, f, ej)
    # I13 años: deflactor 1 en el año base, población y PIB presentes donde hay dato
    base = int(m[m.id == "precios_base"].valor.iloc[0])
    raras = []
    if abs(defl.get(base, np.nan) - 1) > 1e-12:
        raras.append(f"deflactor de {base} = {defl.get(base)}")
    anios_web = sorted(t.anio.unique())
    raras += [f"{y}: sin población" for y in anios_web if pd.isna(a.set_index("anio").poblacion.get(y))]
    est = a[a.poblacion_estatus.eq("estimacion") | a.ipc_estatus.eq("estimacion")].anio.tolist()
    registrar(2, "I13", f"Años: deflactor = 1 en {base} y población para todos los años de la web", len(anios_web) + 1, len(raras), raras,
              nota=f"son estimaciones: IPC o población de {est}")


def nivel_externos(a):
    """IPC (deflactor) y población frente a la API del INE, en línea; si no hay red, se indica y se sigue."""
    import urllib.request
    url = "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{}?date=20140101:20271231"
    try:
        datos = {s_: json.load(urllib.request.urlopen(url.format(s_), timeout=40))["Data"] for s_ in ("IPC293884", "ECP115498")}
    except Exception as e:
        registrar(2, "E1", "IPC y población = API del INE", 0, 0, estado="AVISO", nota=f"sin conexión con el INE ({type(e).__name__})")
        return
    import collections, datetime
    meses = collections.defaultdict(list)
    for x in datos["IPC293884"]:
        if x["Valor"] is not None:
            meses[x["Anyo"]].append(x["Valor"])
    media = {y: sum(v) / len(v) for y, v in meses.items()}
    enero = {datetime.datetime.fromtimestamp(x["Fecha"] / 1000 + 43200, datetime.timezone.utc).year: x["Valor"]
             for x in datos["ECP115498"] if datetime.datetime.fromtimestamp(x["Fecha"] / 1000 + 43200, datetime.timezone.utc).month == 1}
    base = 2025
    n = f = 0; ej = []
    for r in a.itertuples():
        if r.anio in media and base in media:
            n += 1
            if abs(r.deflactor - media[base] / media[r.anio]) > 1e-9:
                f += 1; ej.append(f"{r.anio}: deflactor {r.deflactor:.6f} · INE {media[base] / media[r.anio]:.6f}")
        if r.anio in enero:
            n += 1
            if abs(r.poblacion - enero[r.anio]) > 0.5:
                f += 1; ej.append(f"{r.anio}: población {eur(r.poblacion, 0)} · INE {eur(enero[r.anio], 0)}")
    sin = [y for y in a.anio if y not in enero]
    parcial = [f"{y} ({len(meses[y])} meses)" for y in a.anio if 0 < len(meses.get(y, [])) < 12]
    registrar(2, "E1", "Deflactor (IPC Canarias, base 2025) y población a 1 de enero = API del INE consultada hoy", n, f, ej,
              nota=f"IPC incompleto en {', '.join(parcial) or '—'}; sin dato del INE (estimados): población {sin}, IPC "
                   f"{[y for y in a.anio if y not in media]}")


# ------------------------------------------------------------------------------------------------ nivel 3
def nivel_calculos(t, s, c, a, leidos):
    """Fórmulas que aplica la web, recalculadas en Python. Devuelve las expectativas para el nivel 4 (pantalla)."""
    esperado = {}
    # W1 variación en euros del tooltip: importe − importe / (1 + var%) = importe − importe del año anterior
    tt = t[t.var_pct_interanual.notna() & (t.var_pct_interanual > -100)].copy()
    tt["var_eur"] = tt.importe - tt.importe / (1 + tt.var_pct_interanual / 100)
    j = tt.merge(s[["dimension", "vista", "id_estable", "anio", "precios", "var_abs"]],
                 on=["dimension", "vista", "id_estable", "anio", "precios"])
    err = (j.var_eur - j.var_abs).abs() > 0.01 + 1e-9 * j.importe.abs()
    registrar(3, "W1", "Variación interanual en € del tooltip = diferencia con el año anterior del pipeline", len(j), int(err.sum()),
              j[err][["dimension", "id_estable", "anio"]].head(3).values.tolist())
    # W1b frente al Tomo: inicial − ajustado anterior, en filas sin reestructuración
    if leidos:
        n = f = 0; ej = []
        tc = tt[(tt.precios == "corrientes")]
        for anio, doc in leidos.items():
            w = tc[(tc.dimension == "seccion") & (tc.vista == "organica") & (tc.anio == anio)].copy()
            w["cod"] = codigo(w, "seccion")
            for r in w.itertuples():
                v = doc["secciones"]["filas"].get(r.cod)
                if not v or v[0] is None or v[2] is None:
                    continue
                if abs((r.importe - r.var_eur) - v[0]) > 1:    # reestructurada: el Tomo usa otro anterior (ver F1c)
                    continue
                n += 1
                if abs(r.var_eur - (v[2] - v[0])) > 1:
                    f += 1; ej.append(f"{anio} {r.cod}: web {eur(r.var_eur, 0)} · Tomo {eur(v[2] - v[0], 0)}")
        registrar(3, "W1b", "Variación en € de las secciones = inicial − ajustado del Tomo (secciones sin reestructurar)", n, f, ej)
    # W2 por habitante y % del PIB frente a las métricas del análisis (calculadas por el pipeline, de forma independiente)
    try:
        import duckdb
        bd = RAIZ / "3_carga" / "local" / "presupuestos.duckdb"
        con = duckdb.connect(str(bd), read_only=True)
        am = con.execute("SELECT dimension, vista, id_estable, anio, precios, metrica, valor FROM presupuestos_can.ana_metricas "
                         "WHERE ventana = 'anual' AND incluye_mrr = 'si' AND metrica IN ('per_capita', 'pct_pib')").df()
        con.close()
    except Exception as e:     # sin base local: se omite el contraste
        am = None
        registrar(3, "W2", "Por habitante y % del PIB frente al análisis del pipeline", 0, 0, estado="AVISO", nota=f"sin base local ({e})")
    if am is not None and len(am):
        pob = a.set_index("anio").poblacion; pib = a.set_index("anio").pib_nominal
        ss = s.copy()
        ss["per_capita"] = ss.importe / ss.anio.map(pob)
        cor = s[s.precios == "corrientes"].set_index(["dimension", "vista", "id_estable", "anio"]).importe
        ss["pct_pib"] = 100 * ss.set_index(["dimension", "vista", "id_estable", "anio"]).index.map(cor).values / ss.anio.map(pib).values
        n = f = 0; ej = []
        for met in ("per_capita", "pct_pib"):
            x = am[am.metrica == met].merge(ss, on=["dimension", "vista", "id_estable", "anio", "precios"])
            x = x[x[met].notna() & x.valor.notna()]
            err = (x[met] - x.valor).abs() > 1e-6 * x.valor.abs().clip(lower=1)
            n += len(x); f += int(err.sum())
            ej += [f"{met} {r.dimension} {r.id_estable} {r.anio} {r.precios}: web {getattr(r, met):.4f} · análisis {r.valor:.4f}"
                   for r in x[err].head(2).itertuples()]
        registrar(3, "W2", "€ por habitante y % del PIB de la web = métricas per_capita y pct_pib del análisis", n, f, ej)
    # W3 donut: capítulos de todo lo visible en la raíz = fila Total del Tomo (caps. 1-8)
    if leidos:
        n = f = 0; ej = []
        for anio, doc in leidos.items():
            tot = doc["funciones_cap"]["total"]
            if not tot:
                continue
            for dim, vista in (("funcion", "individual"), ("seccion", "organica"), ("programa", "seccion")):
                d = c[(c.dimension == dim) & (c.vista == vista) & (c.anio == anio)]
                for i, cap in enumerate(CAPS18):
                    n += 1
                    if abs(d[f"cap_{cap}"].sum() - tot[i]) > 1:
                        f += 1; ej.append(f"{anio} {dim} cap. {cap}: {d[f'cap_{cap}'].sum():,.0f} · Tomo {eur(tot[i], 0)}")
        registrar(3, "W3", "Donut sin selección (raíz) = capítulos 1-8 de la fila Total del Tomo, en las 3 dimensiones", n, f, ej)
    # expectativas para la pantalla (nivel 4)
    esperado["donut_raiz"] = {}
    for dim, vista in (("funcion", "individual"), ("seccion", "organica"), ("programa", "seccion"), ("ente", "individual")):
        for anio in (2015, 2020, 2026, int(t.anio.max())):
            for precios in ("corrientes", "constantes"):
                d = c[(c.dimension == dim) & (c.vista == vista) & (c.anio == anio)]
                f_ = d.deflactor if precios == "constantes" else 1
                esperado["donut_raiz"][f"{dim}|{anio}|{precios}"] = {str(k): float((d[f"cap_{k}"] * f_).sum()) for k in CAPS}
    # ranking 2023 → último año (funciones y programas familia, corrientes)
    def ranking(dim, vista, desde, hasta, precios="corrientes"):
        x = s[(s.dimension == dim) & (s.vista == vista) & (s.precios == precios)]
        p = x.pivot_table(index=["id_estable"], columns="anio", values="importe", aggfunc="first")
        et = x.drop_duplicates("id_estable", keep="last").set_index("id_estable").etiqueta
        p = p[[desde, hasta]].dropna()
        p["dif"] = p[hasta] - p[desde]
        sube = p[p.dif > 0].sort_values("dif", ascending=False).head(10)
        baja = p[p.dif < 0].sort_values("dif").head(10)
        fila = lambda r, i: {"etiqueta": et[i], "dif": float(r.dif), "pct": float(100 * (r[hasta] / r[desde] - 1)) if r[desde] else None}
        return {"suben": [fila(r, i) for i, r in sube.iterrows()], "bajan": [fila(r, i) for i, r in baja.iterrows()]}
    fin = int(t.anio.max())
    esperado["ranking"] = {"funcion|individual|2023|%d" % fin: ranking("funcion", "individual", 2023, fin),
                           "programa|familia|2023|%d" % fin: ranking("programa", "familia", 2023, fin)}
    # tablas de la pestaña Peso (valores de cada fila) para varias combinaciones
    esperado["tablas_peso"] = {}
    for dim, vista in (("funcion", "individual"), ("seccion", "organica"), ("seccion", [v for v in t.vista.unique() if str(v).startswith("estructura")][0]),
                       ("programa", "individual"), ("programa", "familia"), ("ente", "individual")):
        for anio in (2015, 2019, 2023, 2026, fin):
            for precios in ("corrientes", "constantes"):
                d = t[(t.dimension == dim) & (t.vista == vista) & (t.anio == anio) & (t.precios == precios) & (t.importe > 0)]
                esperado["tablas_peso"][f"{dim}|{vista}|{anio}|{precios}"] = {
                    r.etiqueta: {"importe": r.importe, "peso": r.peso_total_pct,
                                 "var_eur": None if pd.isna(r.var_pct_interanual) or r.var_pct_interanual <= -100
                                 else r.importe - r.importe / (1 + r.var_pct_interanual / 100),
                                 "var_pct": None if pd.isna(r.var_pct_interanual) else r.var_pct_interanual}
                    for r in d.itertuples()}
    # por habitante y % del PIB de las funciones (para la tabla de la pestaña Evolución)
    pob = a.set_index("anio").poblacion; pib = a.set_index("anio").pib_nominal
    esperado["evolucion"] = {}
    for precios in ("corrientes", "constantes"):
        x = s[(s.dimension == "funcion") & (s.precios == precios)]
        esperado["evolucion"][f"por_habitante|{precios}"] = {f"{r.etiqueta}|{r.anio}": r.importe / pob[r.anio] for r in x.itertuples()}
    x = s[(s.dimension == "funcion") & (s.precios == "corrientes")]
    esperado["evolucion"]["pct_pib"] = {f"{r.etiqueta}|{r.anio}": (100 * r.importe / pib[r.anio] if pd.notna(pib.get(r.anio)) else None)
                                       for r in x.itertuples()}
    # recorrido guiado: cifras de cada clave
    ley = int(s[s.fase == "ley"].anio.max())
    fun = t[(t.dimension == "funcion") & (t.anio == ley) & (t.precios == "corrientes")].assign(cod=lambda d: codigo(d, "funcion")).set_index("cod")
    sec = c[(c.dimension == "seccion") & (c.vista == "organica") & (c.anio == ley)].assign(cod=lambda d: codigo(d, "seccion")).set_index("cod")
    scs = c[(c.dimension == "ente") & (c.vista == "individual") & c.id_estable.str.startswith("ESCS")].set_index("anio")
    c18 = lambda r: sum(r[f"cap_{k}"] for k in CAPS18)
    san = s[(s.dimension == "funcion") & (s.precios == "constantes") & s.id_estable.str.startswith("F31")].set_index("anio").importe
    p0 = int(s.anio.min())
    rk = esperado["ranking"]["funcion|individual|2023|%d" % fin]
    esperado["recorrido"] = {
        "clave1": {"sanidad": fun.loc["31", "peso_total_pct"], "educacion": fun.loc["32", "peso_total_pct"],
                   "suma": fun.loc["31", "peso_total_pct"] + fun.loc["32", "peso_total_pct"],
                   "transferencias": fun.loc["94", "peso_total_pct"], "sociales": fun.loc["23", "peso_total_pct"]},
        "clave2": {"transferencias_pct": 100 * (sec.loc["14", "cap_4"] + sec.loc["14", "cap_7"]) / c18(sec.loc["14"])},
        "clave3": {"personal_pct": 100 * scs.loc[ley, "cap_1"] / c18(scs.loc[ley]), "personal": scs.loc[ley, "cap_1"],
                   "bienes_pct": 100 * scs.loc[ley, "cap_2"] / c18(scs.loc[ley]), "personal_inicio": scs.loc[p0, "cap_1"]},
        "clave4": {"sube": rk["suben"][0], "baja": rk["bajan"][0] if rk["bajan"] else None},
        "clave5": {"inicio": san[p0] / pob[p0], "fin": san[ley] / pob[ley], "var_pct": 100 * ((san[ley] / pob[ley]) / (san[p0] / pob[p0]) - 1)},
    }
    # flujo de Sanidad (sección 14) en el último año de Ley: transferencias y gasto del SCS en las mismas subfunciones
    par = c[(c.dimension == "programa") & (c.anio == ley) & (c.seccion == "14")].copy()
    par["sf"] = par.programa.str[:3]
    tr = (par.cap_4 + par.cap_7).groupby(par.sf).sum()
    tr = tr[tr > 0]
    ep = c[(c.dimension == "ente") & (c.vista == "programa") & (c.anio == ley)].copy()
    ep["sf"] = ep.programa.str[:3]
    ep["c18"] = ep[[f"cap_{k}" for k in CAPS18]].sum(axis=1)
    scs_sf = ep[ep.id_estable.str.startswith("ESCS") & ep.sf.isin(tr.index)]
    esperado["flujo_s14"] = {"anio": ley, "transferencias": float(tr.sum()), "scs_gasto": float(scs_sf.c18.sum()),
                             "scs_sfs": sorted(scs_sf.sf.unique().tolist())}
    registrar(3, "W4", "Cifras del recorrido, ranking, flujo y tablas recalculadas para contrastar con la pantalla (nivel 4)",
              len(esperado["tablas_peso"]) + 5, 0, nota="ver auditoria/auditar_web.cjs")
    return esperado


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sin-pdf", action="store_true")
    args = ap.parse_args()
    t, s, c, a, m = cargar()
    print("Nivel 1 · fuente (Tomo 3 oficial)")
    leidos = None if args.sin_pdf else nivel_fuente(t, c)
    print("Nivel 2 · coherencia interna")
    nivel_coherencia(t, s, c, a, m)
    nivel_externos(a)
    print("Nivel 3 · cálculos de la web")
    esperado = nivel_calculos(t, s, c, a, leidos)
    SALIDA.write_text(json.dumps({"resultados": resultados, "esperado": esperado}, ensure_ascii=False, indent=1, default=float),
                      encoding="utf-8")
    errores = sum(r["estado"] == "ERROR" for r in resultados)
    print(f"\n{len(resultados)} comprobaciones · {errores} con ERROR · "
          f"{sum(r['estado'] == 'AVISO' for r in resultados)} con AVISO → {SALIDA.relative_to(RAIZ)}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
