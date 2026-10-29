"""Tests del orquestador 00_maestro.py: DAG, plan, huella y ejecución con un DAG de juguete (fail-fast, avisos, caché)."""
import importlib.util
import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("maestro", RAIZ / "00_maestro.py")
maestro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(maestro)


def args(**kw):
    base = dict(destino="local", solo=None, anio=None, fase=None, forzar=False, estricto=False, confirmar_produccion=False)
    return Namespace(**{**base, **kw})


def test_dag_real_valido_y_en_orden():
    dag = maestro.cargar_dag()
    assert maestro.orden_topologico(dag) == ["extraccion", "transformacion", "carga", "analisis", "carga_analisis", "viz"]


def test_ciclo_detectado():
    with pytest.raises(ValueError, match="Ciclo"):
        maestro.orden_topologico({"a": {"depende": ["b"]}, "b": {"depende": ["a"]}})


def test_plan_filtra_destino_solo_y_pasa_opciones():
    dag = maestro.cargar_dag()
    p = dict(maestro.plan(dag, None, args()))
    assert all(t.get("destino") != "supabase" for ts in p.values() for t in ts)
    p = dict(maestro.plan(dag, ["analisis"], args(solo=["programas"])))
    assert [t["script"] for t in p["analisis"]] == ["4_analisis/analisis_programas.py"]
    p = dict(maestro.plan(dag, ["extraccion", "carga"], args(anio=2027, fase="proyecto", forzar=True,
                                                             destino="ambos", confirmar_produccion=True)))
    descarga = next(t for t in p["extraccion"] if t["script"].endswith("descargar_tomos.py"))
    assert descarga["cmd"][-5:] == ["--anio", "2027", "--fase", "proyecto", "--forzar"]
    supa = next(t for t in p["carga"] if t.get("destino") == "supabase")
    assert supa["cmd"][-1] == "--confirmar-produccion"


def test_fases_desconocidas():
    with pytest.raises(ValueError, match="desconocidas"):
        maestro.plan(maestro.cargar_dag(), ["nada"], args())


def test_huella_cambia_con_el_contenido(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("a")
    h1 = maestro.huella([str(f)])
    f.write_text("b")
    assert maestro.huella([str(f)]) != h1


# --------------------------------------------------------------------------- ejecución con un DAG de juguete
@pytest.fixture
def juguete(tmp_path):
    for nombre, codigo in (("ok", 0), ("falla", 1), ("aviso", 2)):
        (tmp_path / f"{nombre}.py").write_text(f"import sys\nprint('{nombre}')\nsys.exit({codigo})\n")
    entrada = tmp_path / "entrada.txt"
    entrada.write_text("v1")

    def config(fases):
        ruta = tmp_path / "pipeline.yml"
        ruta.write_text(yaml.safe_dump({"fases": fases}), encoding="utf-8")
        return ruta

    def correr(fases, *extra):
        p = subprocess.run([sys.executable, str(RAIZ / "00_maestro.py"), "--config", str(config(fases)),
                            "--logs", str(tmp_path / "logs"), *extra], capture_output=True, text=True)
        filas = [json.loads(l) for l in (tmp_path / "logs" / "pipeline.jsonl").read_text().splitlines()] \
            if (tmp_path / "logs" / "pipeline.jsonl").exists() else []
        return p, filas

    return tmp_path, entrada, correr


def test_fail_fast_en_puerta_de_calidad(juguete):
    d, _, correr = juguete
    p, filas = correr({
        "a": {"depende": [], "tareas": [{"script": str(d / "ok.py")}]},
        "b": {"depende": ["a"], "tareas": [{"script": str(d / "falla.py"), "bloqueante": True}]},
        "c": {"depende": ["b"], "tareas": [{"script": str(d / "ok.py")}]},
    })
    assert p.returncode == 1 and "puerta de calidad" in p.stdout
    assert [f.get("fase") for f in filas if "script" in f] == ["a", "b"]      # c nunca se ejecuta


def test_avisos_no_detienen_pero_salen_con_codigo_2(juguete):
    d, _, correr = juguete
    p, _ = correr({"a": {"depende": [], "tareas": [{"script": str(d / "aviso.py"), "avisos": [2], "nota": "propuestas"}]},
                   "b": {"depende": ["a"], "tareas": [{"script": str(d / "ok.py")}]}})
    assert p.returncode == 2 and "AVISO" in p.stdout and "propuestas" in p.stdout


def test_cache_omite_si_no_cambian_las_entradas(juguete):
    d, entrada, correr = juguete
    fases = {"a": {"depende": [], "cache": True, "entradas": [str(entrada)], "tareas": [{"script": str(d / "ok.py")}]}}
    correr(fases)
    p, _ = correr(fases)
    assert "en caché" in p.stdout
    entrada.write_text("v2")
    p, _ = correr(fases)
    assert "en caché" not in p.stdout
    p, _ = correr(fases, "--forzar")
    assert "en caché" not in p.stdout
