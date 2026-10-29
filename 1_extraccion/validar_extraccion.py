"""Puertas de calidad del staging tidy (diseno_extraccion_tomo3.md §5).

    python 1_extraccion/validar_extraccion.py            # documentos vigentes
    python 1_extraccion/validar_extraccion.py --estricto # los avisos también bloquean

Errores (bloquean): E1 Σ detalle = total · E2 Σ grupos = total · E3 cuadre caps. 1-8 entre tablas ·
E4 cuadre caps. 1-9 entre tablas · E5 entes 3.2 = 3.1 · E6 filas mínimas · E9 unicidad ·
E10 regresión contra config/referencias_tomo3.yml.
Avisos: E7 degradación del parseo · E8 ajustado t = inicial t-1 · E0 documentos del catálogo sin extraer.
Salida: logs/validacion_extraccion.json; código 1 si hay errores.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _comun.rutas import CONFIG, LOGS, ahora, cargar_fuentes, cargar_tablas, log_evento  # noqa: E402
from _comun.staging import leer_indice_staging, leer_staging  # noqa: E402

TOL = 1.0  # €


class Informe:
    def __init__(self):
        self.errores, self.avisos, self.ok, self.es_aviso = [], [], {}, set()

    def comprobar(self, regla: str, condicion: bool, mensaje: str, aviso: bool = False):
        self.ok.setdefault(regla, [0, 0])
        if aviso:
            self.es_aviso.add(regla)
        self.ok[regla][0 if condicion else 1] += 1
        if not condicion:
            (self.avisos if aviso else self.errores).append(f"{regla} {mensaje}")


def _total(df: pd.DataFrame, tabla: str, columna: str) -> float | None:
    v = df[(df.tabla == tabla) & (df.nivel == "total") & (df.columna == columna)].valor
    return v.iloc[-1] if len(v) else None


def validar_documento(doc: pd.DataFrame, cfg: dict, inf: Informe) -> None:
    did = doc.doc_id.iloc[0]
    eur = doc[doc.unidad == "eur"]
    for tabla, spec in cfg["tablas"].items():
        t = eur[eur.tabla == tabla]
        det = t[t.nivel == "detalle"]
        # E6 · filas mínimas
        n = det.drop_duplicates(["orden"]).shape[0]
        inf.comprobar("E6", n >= spec["min_filas"], f"{did} {tabla}: {n} filas < {spec['min_filas']}")
        # E1 · Σ detalle = total (por ente en 3.2)
        if spec.get("ente_en_cabecera"):
            for (ente, col), g in t.groupby(["ente", "columna"]):
                tot = g[g.nivel == "total"].valor
                ok = len(tot) == 1 and abs(g[g.nivel == "detalle"].valor.sum() - tot.iloc[0]) <= TOL
                inf.comprobar("E1", ok, f"{did} {tabla} {ente} {col}: Σ detalle ≠ Total Ente")
        else:
            for col, g in t.groupby("columna"):
                tot = _total(t, tabla, col)
                ok = tot is not None and abs(g[g.nivel == "detalle"].valor.sum() - tot) <= TOL
                inf.comprobar("E1", ok, f"{did} {tabla} {col}: Σ detalle {g[g.nivel == 'detalle'].valor.sum():,.0f} ≠ total {tot}")
        # E2 · Σ grupos = total (2.16 secciones, 3.1 tipos de ente)
        if (t.nivel == "grupo").any() and not spec.get("ente_en_cabecera"):
            for col, g in t.groupby("columna"):
                tot = _total(t, tabla, col)
                ok = tot is not None and abs(g[g.nivel == "grupo"].valor.sum() - tot) <= TOL
                inf.comprobar("E2", ok, f"{did} {tabla} {col}: Σ grupos ≠ total")
        # E9 · unicidad de la clave natural
        clave = ["ente", "codigo"] if spec.get("ente_en_cabecera") else ["codigo_padre", "codigo"] \
            if spec.get("codigo_grupo") else ["codigo"]
        dup = det.drop_duplicates(["orden"]).duplicated(clave).sum()
        inf.comprobar("E9", dup == 0, f"{did} {tabla}: {dup} claves {clave} duplicadas")

    # E3 · caps. 1-8: 2.1 = 2.8 = 2.9 = 2.10 (inicial y ajustado)
    for col in ("inicial", "ajustado_prev"):
        tots = {t: _total(eur, t, col) for t in ("secciones", "funciones", "subfunciones", "programas")}
        inf.comprobar("E3", len(set(tots.values())) == 1, f"{did} {col}: {tots}")
    # E4 · caps. 1-9: 2.11 = 2.14 = 2.16
    tots = {t: _total(eur, t, "total") for t in ("secciones_cap", "subfunciones_cap", "secc_prog_cap")}
    inf.comprobar("E4", len(set(tots.values())) == 1, f"{did}: {tots}")
    # E5 · cada «Total Ente» de 3.2 = «inicial» del ente en 3.1 (por nombre; si no, por importe)
    t32 = eur[(eur.tabla == "entes_prog_cap") & (eur.nivel == "total") & (eur.columna == "total")]
    t32 = t32.set_index("ente").valor
    t31 = eur[(eur.tabla == "entes") & (eur.nivel == "detalle") & (eur.columna == "inicial")]
    t31 = t31.set_index("denominacion_raw").valor
    por_importe = sorted(t31.values)
    for ente, v in t32.items():
        if ente in t31.index:
            inf.comprobar("E5", abs(t31[ente] - v) <= TOL, f"{did} {ente}: 3.2 {v:,.0f} ≠ 3.1 {t31[ente]:,.0f}")
        else:
            casa = any(abs(x - v) <= TOL for x in por_importe)
            inf.comprobar("E5", casa, f"{did} {ente}: sin equivalente en 3.1")
            if casa:
                inf.avisos.append(f"E5 {did} {ente!r}: emparejado por importe (nombre distinto en 3.1)")
    inf.comprobar("E5", len(t32) == len(t31), f"{did}: {len(t32)} entes en 3.2 y {len(t31)} en 3.1")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--estricto", action="store_true")
    args = ap.parse_args()

    cfg, _ = cargar_tablas()
    df = leer_staging()
    inf = Informe()
    if df.empty:
        print("Staging vacío: ejecuta extraer_tomo3.py.")
        return 1
    for _, doc in df.groupby("doc_id"):
        validar_documento(doc, cfg, inf)

    # E0 · documentos del catálogo sin extraer
    extraidos = set(zip(df.anio_presupuesto, df.fase))
    for d in cargar_fuentes()["documentos"]:
        inf.comprobar("E0", (d["anio"], d["fase"]) in extraidos, f"{d['anio']} {d['fase']}: no está en staging", aviso=True)

    # E7 · degradación del parseo
    for did, info in leer_indice_staging().items():
        if did not in set(df.doc_id):
            continue
        for tabla, c in info["contadores"].items():
            malos = {k: c[k] for k in ("tokens_fuera_ancla", "huerfanas_descartadas") if c.get(k)}
            inf.comprobar("E7", not malos, f"{did} {tabla}: {malos}", aviso=True)

    # E8 · continuidad: ajustado del tomo t = inicial del tomo t-1 (Ley)
    eur = df[(df.unidad == "eur") & (df.tabla == "programas") & (df.nivel == "total") & (df.fase == "ley")]
    ini = eur[eur.columna == "inicial"].set_index("anio_presupuesto").valor
    aj = eur[eur.columna == "ajustado_prev"].set_index("anio_presupuesto").valor
    for anio in sorted(aj.index):
        if anio - 1 in ini.index:
            d = aj[anio] - ini[anio - 1]
            inf.comprobar("E8", abs(d) <= TOL, f"{anio}: ajustado {aj[anio]:,.0f} − inicial {anio - 1} = {d:+,.0f} € (cambio de perímetro)", aviso=True)

    # E10 · regresión
    ref = yaml.safe_load((CONFIG / "referencias_tomo3.yml").read_text(encoding="utf-8"))
    progs = df[(df.tabla == "programas") & (df.nivel == "total") & (df.columna == "inicial")]
    for fase, por_anio in ref["total_programas_inicial"].items():
        for anio, valor in por_anio.items():
            v = progs[(progs.fase == fase) & (progs.anio_presupuesto == anio)].valor
            inf.comprobar("E10", len(v) == 1 and abs(v.iloc[0] - valor) <= TOL,
                          f"total 2.10 {fase} {anio}: {v.tolist()} ≠ {valor:,}")
    for r in ref["filas"]:
        v = df[(df.tabla == r["tabla"]) & (df.anio_presupuesto == r["anio"]) & (df.fase == r["fase"]) &
               (df.codigo == r["codigo"]) & (df.columna == r["columna"]) & (df.nivel == "detalle")].valor
        ok = len(v) == 1 and ((r["valor"] is None and math.isnan(v.iloc[0])) or
                              (r["valor"] is not None and abs(v.iloc[0] - r["valor"]) <= TOL))
        inf.comprobar("E10", ok, f"{r['tabla']} {r['anio']} {r['codigo']} {r['columna']}: {v.tolist()} ≠ {r['valor']}")

    resultado = {"ts": ahora(), "documentos": int(df.doc_id.nunique()), "reglas": inf.ok,
                 "errores": inf.errores, "avisos": inf.avisos}
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / "validacion_extraccion.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    log_evento("validar_extraccion", errores=len(inf.errores), avisos=len(inf.avisos))

    print(f"Documentos: {resultado['documentos']}")
    for regla, (bien, mal) in sorted(inf.ok.items(), key=lambda x: int(x[0][1:])):
        marca = "✅" if mal == 0 else "⚠️ " if regla in inf.es_aviso else "❌"
        print(f"  {regla:4s} {marca} {bien} correctas, {mal} fallidas")
    for a in inf.avisos:
        print("AVISO", a)
    for e in inf.errores[:30]:
        print("ERROR", e)
    if len(inf.errores) > 30:
        print(f"… y {len(inf.errores) - 30} errores más (logs/validacion_extraccion.json)")
    bloquea = inf.errores or (args.estricto and inf.avisos)
    return 1 if bloquea else 0


if __name__ == "__main__":
    sys.exit(main())
