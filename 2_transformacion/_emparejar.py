"""Motor de emparejamiento entre años consecutivos (diseno_pipeline_presupuestos_2027.md §5.3.1).

Para cada unidad p del año t y cada candidata q del año t-1:
  s_importe  1 - min(1, |ajustado_t(p) - inicial_{t-1}(q)| / inicial_{t-1}(q))   ← señal más fuerte:
             el tomo t reexpresa t-1 en la estructura nueva
  s_nombre   rapidfuzz token_set_ratio sobre nombres normalizados / 100
  s_codigo   1 si el código es idéntico
  s_grupo    1 si comparten prefijo jerárquico (subfunción del programa, función de la subfunción)
  s_seccion  1 si alguna sección de p es heredera (por el crosswalk de secciones) de una sección de q
score = Σ peso × señal. Pesos por dimensión en config/transformacion.yml.

Una unidad con el mismo código y nombre casi idéntico (≥ identidad_nombre) se enlaza como «identico»
aunque cambie su importe: es la misma unidad con un cambio de perímetro (Δ_reestr ≠ 0).
"""
from itertools import combinations

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

CONTINUIDAD = {"identico", "renombrado", "recodificado"}
TABLA_DIMENSION = {"seccion": "secciones", "funcion": "funciones", "subfuncion": "subfunciones",
                   "programa": "programas", "ente": "entes"}


def unidades(fact: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Una fila por (año, código) de la serie oficial: nombre, inicial del año y ajustado de t-1."""
    t = fact[fact.serie_oficial & (fact.tabla == TABLA_DIMENSION[dimension]) & (fact.capitulo == "TOTAL")]
    ini = t[t.version_importe == "inicial"].set_index(["anio_presupuesto", "codigo"])
    aj = t[t.version_importe == "ajustado"].set_index(["anio_presupuesto", "codigo"]).importe_corriente
    u = ini[["denominacion_raw", "nombre_norm", "importe_corriente"]].rename(columns={"importe_corriente": "inicial"})
    u["ajustado"] = aj.reindex(u.index).fillna(0.0)
    u = u.reset_index()
    u["grupo"] = {"programa": u.codigo.str[:3], "subfuncion": u.codigo.str[:2]}.get(dimension)
    if dimension == "programa":
        spc = fact[fact.serie_oficial & (fact.dimension == "seccion_programa") & (fact.capitulo == "TOTAL")]
        secc = spc.groupby(["anio_presupuesto", "codigo_unidad"]).codigo_padre.agg(lambda s: frozenset(s))
        u["secciones"] = [secc.get((a, c), frozenset()) for a, c in zip(u.anio_presupuesto, u.codigo)]
    return u


def _senales(prev: pd.DataFrame, act: pd.DataFrame, enlaces_seccion: dict | None) -> dict[str, np.ndarray]:
    aj = act.ajustado.to_numpy()[:, None]
    ini = prev.inicial.to_numpy()[None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        s_imp = np.where(ini > 0, 1 - np.minimum(1, np.abs(aj - ini) / np.where(ini > 0, ini, 1)),
                         np.where(aj == 0, 1.0, 0.0))
    s = {
        "importe": s_imp,
        "nombre": process.cdist(act.nombre_norm.tolist(), prev.nombre_norm.tolist(), scorer=fuzz.token_set_ratio) / 100,
        "codigo": (act.codigo.to_numpy()[:, None] == prev.codigo.to_numpy()[None, :]).astype(float),
    }
    if act.get("grupo") is not None and act.grupo.notna().all():
        s["grupo"] = (act.grupo.to_numpy()[:, None] == prev.grupo.to_numpy()[None, :]).astype(float)
    if "secciones" in act:
        enlaces_seccion = enlaces_seccion or {}   # sin crosswalk de secciones: herencia por código
        herederas = [frozenset(x for sec in q for x in enlaces_seccion.get(sec, {sec})) for q in prev.secciones]
        s["seccion"] = np.array([[float(bool(p & h)) for h in herederas] for p in act.secciones])
    return s


def _tamanos(n: int) -> range:
    return range(2, min(n, 6 if n <= 12 else 3) + 1)


def _tipo(mismo_codigo: bool, s_nombre: float, s_importe: float, ident: float) -> str:
    if mismo_codigo:
        if s_nombre >= ident:
            return "identico"
        return "renombrado"
    return "recodificado"


def emparejar_par(prev: pd.DataFrame, act: pd.DataFrame, dimension: str, pesos: dict, p: dict,
                  enlaces_seccion: dict | None = None) -> pd.DataFrame:
    """Propuestas de enlace entre el año t-1 (prev) y t (act)."""
    prev, act = prev.reset_index(drop=True), act.reset_index(drop=True)
    s = _senales(prev, act, enlaces_seccion)
    score = sum(pesos[k] * s[k] for k in pesos if k in s)
    filas, origen_usado, destino_usado = [], set(), set()

    def fila(i, j, tipo, estado):
        r = {"anio_origen": prev.anio_presupuesto[j] if j is not None else None,
             "codigo_origen": prev.codigo[j] if j is not None else None,
             "anio_destino": act.anio_presupuesto[i] if i is not None else None,
             "codigo_destino": act.codigo[i] if i is not None else None,
             "tipo_enlace": tipo, "estado": estado,
             "score": round(float(score[i, j]), 4) if i is not None and j is not None else None,
             "denominacion_origen": prev.denominacion_raw[j] if j is not None else None,
             "denominacion_destino": act.denominacion_raw[i] if i is not None else None,
             "inicial_origen": prev.inicial[j] if j is not None else None,
             "ajustado_destino": act.ajustado[i] if i is not None else None,
             "inicial_destino": act.inicial[i] if i is not None else None}
        for k in ("importe", "nombre", "codigo", "grupo", "seccion"):
            r[f"s_{k}"] = round(float(s[k][i, j]), 4) if k in s and i is not None and j is not None else None
        filas.append(r)

    for i in range(len(act)):
        mismo = np.where(s["codigo"][i] == 1)[0]
        j_mismo = int(mismo[0]) if len(mismo) else None
        # regla de identidad: mismo código y nombre casi idéntico
        if j_mismo is not None and s["nombre"][i, j_mismo] >= p["identidad_nombre"]:
            fila(i, j_mismo, "identico", "auto")
            origen_usado.add(j_mismo)
            destino_usado.add(i)
            continue
        j = int(np.argmax(score[i]))
        if j_mismo is not None and score[i, j_mismo] >= score[i, j] - 1e-9:
            j = j_mismo
        if score[i, j] >= p["umbral_revision"]:
            estado = "auto" if score[i, j] >= p["umbral_auto"] else "revision"
            fila(i, j, _tipo(j == j_mismo, s["nombre"][i, j], s["importe"][i, j], p["identidad_nombre"]), estado)
            origen_usado.add(j)
            destino_usado.add(i)

    props = pd.DataFrame(filas)
    # divisiones: varias unidades nuevas enlazadas a la misma antigua cuyos ajustados suman su inicial.
    # El enlace con el mismo código conserva su tipo (la unidad sigue, más pequeña); el resto es «division».
    if len(props):
        for codigo_origen, g in props.groupby("codigo_origen"):
            if len(g) > 1:
                j = int(prev.index[prev.codigo == codigo_origen][0])
                if abs(g.ajustado_destino.sum() - prev.inicial[j]) <= p["tolerancia_division"] * max(prev.inicial[j], 1):
                    otros = g.index[g.codigo_destino != codigo_origen]
                    for k in otros:
                        filas[k]["tipo_enlace"] = "division"

    # fusiones y divisiones entre unidades sin enlace: combinaciones de 2 a 6 (p. ej. los seis programas 911x
    # del Parlamento → 912L en 2022), preferentemente dentro del mismo grupo; k > 3 solo si hay pocas candidatas
    libres_q = [j for j in range(len(prev)) if j not in origen_usado and prev.inicial[j] > 0]
    libres_p = [i for i in range(len(act)) if i not in destino_usado and act.ajustado[i] > 0]
    tol = p["tolerancia_division"]
    for i in list(libres_p):
        cands = [j for j in libres_q if s.get("grupo") is None or s["grupo"][i, j] == 1] or libres_q
        for k in _tamanos(len(cands)):
            hallado = next((c for c in combinations(cands, k)
                            if abs(sum(prev.inicial[j] for j in c) - act.ajustado[i]) <= tol * act.ajustado[i]), None)
            if hallado:
                for j in hallado:
                    fila(i, j, "fusion", "revision")
                    libres_q.remove(j)
                libres_p.remove(i)
                destino_usado.add(i)
                origen_usado.update(hallado)
                break
    for j in list(libres_q):
        cands = [i for i in libres_p if s.get("grupo") is None or s["grupo"][i, j] == 1] or libres_p
        for k in _tamanos(len(cands)):
            hallado = next((c for c in combinations(cands, k)
                            if abs(sum(act.ajustado[i] for i in c) - prev.inicial[j]) <= tol * prev.inicial[j]), None)
            if hallado:
                for i in hallado:
                    fila(i, j, "division", "revision")
                    libres_p.remove(i)
                    destino_usado.add(i)
                origen_usado.add(j)
                libres_q.remove(j)
                break

    # sucesos sin enlace
    codigos_prev = set(prev.codigo)
    for i in range(len(act)):
        if i not in destino_usado:
            tipo = "reutilizado" if act.codigo[i] in codigos_prev else \
                ("nuevo" if act.ajustado[i] == 0 else "nuevo_sin_origen")
            fila(i, None, tipo, "sin_enlace")
    for j in range(len(prev)):
        if j not in origen_usado:
            fila(None, j, "extinguido", "sin_enlace")
    out = pd.DataFrame(filas)
    out.insert(0, "dimension", dimension)
    return out


def emparejar(u: pd.DataFrame, dimension: str, pesos: dict, p: dict,
              enlaces_seccion_por_anio: dict | None = None) -> pd.DataFrame:
    anios = sorted(u.anio_presupuesto.unique())
    partes = []
    for a0, a1 in zip(anios, anios[1:]):
        enl = (enlaces_seccion_por_anio or {}).get(a1)
        partes.append(emparejar_par(u[u.anio_presupuesto == a0], u[u.anio_presupuesto == a1],
                                    dimension, pesos, p, enl))
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
