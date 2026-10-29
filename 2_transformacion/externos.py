"""Series externas de Canarias: IPC (deflactor), población y PIB → 2_transformacion/externos/externos_canarias.csv

    python 2_transformacion/externos.py              # usa el CSV si ya existe
    python 2_transformacion/externos.py --actualizar # vuelve a consultar la API del INE

- IPC: INE, serie IPC293884 (Canarias, índice general, base 2025 = 100), media anual de los meses
  publicados. Un año con menos de 12 meses queda como «estimacion».
- Población: INE ECP, serie ECP115498 (Canarias, total), a 1 de enero del año del presupuesto.
- PIB nominal: INE CRE vía el fichero de Canarias en Datos (solo lectura); sin dato para años recientes.
El CSV resultante se versiona: así el pipeline es reproducible sin red.
"""
import argparse
import sys
from collections import defaultdict
from datetime import datetime, timezone

import pandas as pd
import requests

from _tcomun import EXTERNOS, ahora, cfg, log_evento

API = "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{serie}?date=20140101:20271231"
SALIDA = EXTERNOS / "externos_canarias.csv"


def serie_ine(codigo: str) -> list[dict]:
    r = requests.get(API.format(serie=codigo), timeout=60,
                     headers={"User-Agent": "ODESOCAN-presupuestos-2027/1.0"})
    r.raise_for_status()
    return r.json()["Data"]


def ipc_anual(datos: list[dict]) -> pd.DataFrame:
    meses = defaultdict(list)
    for x in datos:
        meses[x["Anyo"]].append(x["Valor"])
    return pd.DataFrame([{"anio": a, "ipc_media": sum(v) / len(v), "ipc_meses": len(v)} for a, v in sorted(meses.items())])


def poblacion_1_enero(datos: list[dict]) -> pd.DataFrame:
    """Los puntos de la ECP se fechan a 1 de enero/abril/julio/octubre (la marca UTC cae el día anterior)."""
    filas = []
    for x in datos:
        f = datetime.fromtimestamp(x["Fecha"] / 1000, tz=timezone.utc)
        if (f.month, f.day) == (12, 31):          # 1 de enero del año siguiente
            filas.append({"anio": f.year + 1, "poblacion": int(x["Valor"])})
        elif (f.month, f.day) == (1, 1):
            filas.append({"anio": f.year, "poblacion": int(x["Valor"])})
    return pd.DataFrame(filas).drop_duplicates("anio", keep="last")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--actualizar", action="store_true")
    args = ap.parse_args()
    if SALIDA.exists() and not args.actualizar:
        print(f"{SALIDA.name} ya existe (usa --actualizar para volver a consultar el INE)")
        return 0

    c = cfg()
    ipc = ipc_anual(serie_ine(c["deflactor"]["serie_ine"]))
    pob = poblacion_1_enero(serie_ine(c["poblacion"]["serie_ine"]))
    pib = pd.read_csv(c["pib"]["fichero_ced"])
    pib = pib[pib.ccaa_id3 == c["pib"]["ccaa_id3"]][["anio", "pib_regional_eur"]].rename(
        columns={"pib_regional_eur": "pib_nominal"})

    df = pd.DataFrame({"anio": range(2014, 2028)})
    df = df.merge(ipc, on="anio", how="left").merge(pob, on="anio", how="left").merge(pib, on="anio", how="left")
    df["ipc_estatus"] = df.ipc_meses.map(lambda m: "verificado" if m == 12 else "estimacion" if m == m else None)

    # IPC: años futuros por tasa de previsión (o repitiendo la última tasa)
    for anio in df.anio[df.ipc_media.isna()]:
        previo = df.loc[df.anio == anio - 1, "ipc_media"].iloc[0]
        if pd.isna(previo):
            continue
        tasa = (c["deflactor"].get("tasa_prevision") or {}).get(anio)
        if tasa is None:
            ant = df.loc[df.anio == anio - 2, "ipc_media"].iloc[0]
            tasa = previo / ant - 1
        df.loc[df.anio == anio, ["ipc_media", "ipc_meses", "ipc_estatus"]] = [previo * (1 + tasa), 0, "estimacion"]

    # Población: el último 1 de enero disponible se proyecta con la variación del año anterior
    df["poblacion_estatus"] = df.poblacion.map(lambda p: "verificado" if p == p else None)
    for anio in df.anio[df.poblacion.isna()]:
        p1 = df.loc[df.anio == anio - 1, "poblacion"].iloc[0]
        p2 = df.loc[df.anio == anio - 2, "poblacion"].iloc[0]
        if pd.notna(p1) and pd.notna(p2):
            df.loc[df.anio == anio, ["poblacion", "poblacion_estatus"]] = [round(p1 * p1 / p2), "estimacion"]
    df["pib_estatus"] = df.pib_nominal.map(lambda p: "verificado" if p == p else None)
    df["fuente"] = (f"INE {c['deflactor']['serie_ine']} (IPC base 2025) · INE {c['poblacion']['serie_ine']} (ECP, 1 enero)"
                    " · PIB: INE CRE vía Canarias en Datos")
    df["consultado_en"] = ahora()

    EXTERNOS.mkdir(parents=True, exist_ok=True)
    df.to_csv(SALIDA, index=False)
    print(df[["anio", "ipc_media", "ipc_meses", "ipc_estatus", "poblacion", "poblacion_estatus", "pib_nominal"]].to_string(index=False))
    log_evento("externos", filas=len(df))
    return 0


if __name__ == "__main__":
    sys.exit(main())
