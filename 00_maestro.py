"""Orquestador del pipeline de Presupuestos de Canarias (diseno_pipeline_presupuestos_2027.md §9).

    python 00_maestro.py                                   # todo, destino local
    python 00_maestro.py --pasos transformacion,carga      # solo esas fases (en orden del DAG)
    python 00_maestro.py --anio 2027 --fase proyecto       # extracción incremental de un documento
    python 00_maestro.py --destino ambos --confirmar-produccion   # también Supabase (producción)
    python 00_maestro.py --solo programas --paralelo       # análisis de una dimensión / análisis en paralelo
    python 00_maestro.py --dry-run                          # muestra el plan sin ejecutar nada

El DAG (fases, tareas, dependencias, entradas y salidas) está en config/pipeline.yml. Cada tarea es un script
independiente lanzado como subproceso con el mismo intérprete, así que también puede ejecutarse suelto.
- Caché por fase: huella SHA-256 de sus entradas (código, configuración y artefactos previos). Si no cambia
  desde la última ejecución correcta y sus salidas existen, la fase se omite. --forzar la ignora (y se pasa a
  los scripts que tienen caché propia).
- Fail-fast: una tarea bloqueante (puertas de calidad) que falla detiene el pipeline antes de cargar nada.
- Log: una línea JSON por tarea en logs/pipeline.jsonl y la salida completa en logs/maestro/<run_id>.log.
Código de salida: 0 bien · 1 error o puerta de calidad fallida · 2 bien, pero con avisos.
"""
import argparse
import glob
import hashlib
import json
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent
CONFIG = RAIZ / "config" / "pipeline.yml"
LOGS = RAIZ / "logs"
CACHE = LOGS / "cache_maestro.json"


def ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def cargar_dag(ruta: Path = CONFIG) -> dict:
    dag = yaml.safe_load(ruta.read_text(encoding="utf-8"))["fases"]
    for nombre, f in dag.items():
        for d in f.get("depende", []):
            if d not in dag:
                raise ValueError(f"La fase {nombre} depende de una fase inexistente: {d}")
    return dag


def orden_topologico(dag: dict) -> list[str]:
    orden, visitadas = [], set()

    def visitar(n, pila=()):
        if n in pila:
            raise ValueError(f"Ciclo en el DAG: {' → '.join(pila + (n,))}")
        if n in visitadas:
            return
        for d in dag[n].get("depende", []):
            visitar(d, pila + (n,))
        visitadas.add(n)
        orden.append(n)

    for n in dag:          # respeta el orden del fichero entre fases independientes
        visitar(n)
    return orden


def destinos(valor: str) -> set[str]:
    return {"local", "supabase"} if valor == "ambos" else {valor}


def plan(dag: dict, pasos: list[str] | None, args) -> list[tuple[str, list[dict]]]:
    """[(fase, [tareas con su línea de comandos])] en orden del DAG, filtrado por pasos, destino y --solo."""
    fases = [f for f in orden_topologico(dag) if not pasos or f in pasos]
    if pasos:
        desconocidas = set(pasos) - set(dag)
        if desconocidas:
            raise ValueError(f"Fases desconocidas: {sorted(desconocidas)} (válidas: {', '.join(dag)})")
    dest = destinos(args.destino)
    out = []
    for fase in fases:
        tareas = []
        for t in dag[fase]["tareas"]:
            if t.get("destino") and t["destino"] not in dest:
                continue
            if args.solo and t.get("dimension") and t["dimension"] not in args.solo:
                continue
            cmd = [sys.executable, str(RAIZ / t["script"]), *[str(a) for a in t.get("args", [])]]
            if t.get("filtro") and args.anio:
                cmd += ["--anio", str(args.anio)]
            if t.get("filtro") and args.fase:
                cmd += ["--fase", args.fase]
            if t.get("forzar") and args.forzar:
                cmd.append("--forzar")
            if t.get("estricto") and args.estricto:
                cmd.append("--estricto")
            if t.get("destino") == "supabase" and args.confirmar_produccion:
                cmd.append("--confirmar-produccion")
            tareas.append({**t, "cmd": cmd})
        out.append((fase, tareas))
    return out


def huella(patrones: list[str], raiz: Path = RAIZ) -> str:
    """SHA-256 del contenido (y la ruta) de todos los ficheros que casan con los patrones."""
    h = hashlib.sha256()
    for ruta in sorted({p for pat in patrones for p in glob.glob(str(raiz / pat))}):
        r = Path(ruta)
        h.update(str(r.relative_to(raiz) if r.is_relative_to(raiz) else r).encode())
        with open(ruta, "rb") as f:
            for bloque in iter(lambda: f.read(1 << 20), b""):
                h.update(bloque)
    return h.hexdigest()


def salidas_existen(fase_cfg: dict, raiz: Path = RAIZ) -> bool:
    return all(glob.glob(str(raiz / pat)) for pat in fase_cfg.get("salidas", []))


def leer_cache(ruta: Path = CACHE) -> dict:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def clave_cache(fase: str, args) -> str:
    """La caché depende también de los parámetros que cambian el resultado de la fase."""
    return f"{fase}|destino={args.destino}|solo={','.join(sorted(args.solo or []))}|anio={args.anio}|fase={args.fase}"


def ejecutar(tarea: dict, run_id: str, registro) -> dict:
    t0 = time.monotonic()
    p = subprocess.run(tarea["cmd"], cwd=RAIZ, capture_output=True, text=True)
    dur = round(time.monotonic() - t0, 2)
    ok = p.returncode in tarea.get("codigos_ok", [0]) or p.returncode in tarea.get("avisos", [])
    res = {"ts": ahora(), "paso": "maestro", "run_id": run_id, "script": tarea["script"], "args": tarea["cmd"][2:],
           "codigo": p.returncode, "duracion_s": dur, "ok": ok, "aviso": p.returncode in tarea.get("avisos", []),
           "bloqueante": bool(tarea.get("bloqueante"))}
    registro.write(f"\n===== {tarea['script']} {' '.join(tarea['cmd'][2:])} → {p.returncode} ({dur} s)\n{p.stdout}{p.stderr}")
    registro.flush()
    res["ultimas_lineas"] = (p.stdout + p.stderr).strip().splitlines()[-6:]
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pasos", help="fases separadas por comas (por defecto, todas)")
    ap.add_argument("--destino", choices=["local", "supabase", "ambos"], default="local")
    ap.add_argument("--confirmar-produccion", action="store_true", help="necesario para cargar o leer Supabase remoto")
    ap.add_argument("--anio", type=int, help="limita descarga y extracción a un año")
    ap.add_argument("--fase", choices=["proyecto", "ley"], help="limita descarga y extracción a una fase")
    ap.add_argument("--solo", help="análisis: dimensiones separadas por comas (funciones, secciones, programas, entes)")
    ap.add_argument("--forzar", action="store_true", help="ignora todas las cachés")
    ap.add_argument("--estricto", action="store_true", help="los avisos de las puertas de calidad también bloquean")
    ap.add_argument("--paralelo", action="store_true", help="ejecuta a la vez las tareas marcadas como paralelas")
    ap.add_argument("--dry-run", action="store_true", help="muestra el plan y no ejecuta nada")
    ap.add_argument("--config", type=Path, default=CONFIG, help=argparse.SUPPRESS)   # tests: otro DAG
    ap.add_argument("--logs", type=Path, default=LOGS, help=argparse.SUPPRESS)       # tests: otra carpeta de logs
    args = ap.parse_args()
    logs, cache_ruta = args.logs, args.logs / "cache_maestro.json"
    args.solo = [s.strip() for s in args.solo.split(",")] if args.solo else None
    pasos = [p.strip() for p in args.pasos.split(",")] if args.pasos else None

    dag = cargar_dag(args.config)
    try:
        el_plan = plan(dag, pasos, args)
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1
    if args.destino != "local" and not args.confirmar_produccion:
        print("AVISO: destino Supabase sin --confirmar-produccion: las tareas de Supabase se negarán a usar un host remoto.")

    run_id = uuid.uuid4().hex[:10]
    cache = leer_cache(cache_ruta)
    print(f"Pipeline Presupuestos CAC · run {run_id} · destino {args.destino}")
    if args.dry_run:
        for fase, tareas in el_plan:
            f = dag[fase]
            en_cache = (f.get("cache") and not args.forzar and salidas_existen(f)
                        and cache.get(clave_cache(fase, args)) == huella(f.get("entradas", [])))
            print(f"\n[{fase}]{' (en caché: se omitiría)' if en_cache else ''}")
            for t in tareas:
                print(("  ║ " if args.paralelo and t.get("paralelo") else "  · ") + " ".join(["python", t["script"], *t["cmd"][2:]]))
        return 0

    logs.mkdir(parents=True, exist_ok=True)
    (logs / "maestro").mkdir(exist_ok=True)
    resultados, avisos, inicio = [], [], time.monotonic()
    with open(logs / "maestro" / f"{run_id}.log", "w", encoding="utf-8") as registro, \
            open(logs / "pipeline.jsonl", "a", encoding="utf-8") as jsonl:
        for fase, tareas in el_plan:
            f = dag[fase]
            for d in f.get("depende", []):
                if d not in [x for x, _ in el_plan] and not salidas_existen(dag[d]):
                    print(f"ERROR: la fase {fase} necesita las salidas de {d}, que no existen. Ejecuta antes --pasos {d}.")
                    return 1
            h = huella(f.get("entradas", [])) if f.get("cache") else None
            if h and not args.forzar and salidas_existen(f) and cache.get(clave_cache(fase, args)) == h:
                print(f"[{fase}] en caché (sus entradas no han cambiado)")
                jsonl.write(json.dumps({"ts": ahora(), "paso": "maestro", "run_id": run_id, "fase": fase, "cache": True}) + "\n")
                continue
            print(f"[{fase}]")
            secuenciales = [t for t in tareas if not (args.paralelo and t.get("paralelo"))]
            paralelas = [t for t in tareas if args.paralelo and t.get("paralelo")]
            lotes = [[t] for t in secuenciales] + ([paralelas] if paralelas else [])
            fallo = False
            for lote in lotes:
                if len(lote) > 1:
                    with ThreadPoolExecutor(max_workers=len(lote)) as ex:
                        res_lote = list(ex.map(lambda t: ejecutar(t, run_id, registro), lote))
                else:
                    res_lote = [ejecutar(lote[0], run_id, registro)]
                for t, r in zip(lote, res_lote):
                    r["fase"] = fase
                    jsonl.write(json.dumps(r, ensure_ascii=False) + "\n")
                    jsonl.flush()
                    resultados.append(r)
                    marca = "✅" if r["ok"] and not r["aviso"] else ("⚠️ " if r["ok"] else "❌")
                    print(f"  {marca} {t['script']} {' '.join(r['args'])} ({r['duracion_s']} s)")
                    if r["aviso"]:
                        avisos.append(f"{t['script']}: {t.get('nota', f'código {r['codigo']}')}")
                    if not r["ok"]:
                        for linea in r["ultimas_lineas"]:
                            print(f"      {linea}")
                        fallo = True
                if fallo:
                    break
            if fallo:
                bloq = any(not r["ok"] and r["bloqueante"] for r in resultados)
                print(f"\nDETENIDO en la fase «{fase}»{' por una puerta de calidad' if bloq else ''}. "
                      f"Detalle: logs/maestro/{run_id}.log")
                return 1
            if h:
                cache[clave_cache(fase, args)] = h
                cache_ruta.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    total = round(time.monotonic() - inicio, 1)
    print(f"\nPipeline completado en {total} s · {len(resultados)} tareas · log: logs/maestro/{run_id}.log")
    for a in avisos:
        print(f"AVISO {a}")
    return 2 if avisos else 0


if __name__ == "__main__":
    sys.exit(main())
