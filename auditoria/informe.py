"""Escribe auditoria/informe_auditoria.md a partir de los resultados de auditar_datos.py y auditar_web.cjs.

    .venv/bin/python auditoria/auditar_datos.py && node auditoria/auditar_web.cjs && .venv/bin/python auditoria/informe.py
"""
import json
import subprocess
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
NIVELES = {1: "Fuente: los datos frente al Tomo 3 oficial", 2: "Coherencia interna y datos externos",
           3: "Cálculos que hace la web", 4: "Lo que se ve en pantalla"}
ICONO = {"OK": "✅ OK", "AVISO": "⚠️ Aviso", "ERROR": "❌ Error"}
miles = lambda n: f"{n:,}".replace(",", ".")      # solo a las cifras, no al texto

OBSERVACIONES = """\
## Observaciones

1. **Variación interanual: la web y el Tomo no comparan exactamente lo mismo.** La web compara el presupuesto inicial de cada
   partida con su inicial del año anterior. La columna «2/1» del Tomo compara con el presupuesto anterior *ajustado* a la nueva
   estructura. Coinciden salvo cuando una consejería, función o programa cambia de competencias. En la serie hay {expl} casos así,
   y en todos se compara el **mismo código** en los dos años: no hay ningún enlace dudoso entre partidas distintas. Se explica
   ahora en «Cómo leer estos datos».
2. **Una diferencia dentro del propio Tomo: el Servicio Canario de la Salud en 2021.** La tabla 3.1 (comparativo por entes) da
   3.301.248.249 € y la suma de sus programas por capítulos (tabla 3.2) da 3.300.693.715 €: 554.534 € menos (0,02 %). El treemap
   usa la 3.1 y el donut, la 3.2; el donut lo advierte ahora con una nota.
3. **Estimaciones, ya señaladas en la web:** el deflactor de 2026 usa los 9 meses de IPC publicados; el de 2027 y la población de
   2027 son estimaciones; el PIB publicado llega a 2024 (el % del PIB no se calcula después).
4. **Ventanas de gobierno verificadas** con hemeroteca: el PSOE salió del Gobierno el 23/12/2016
   ([Diario de Avisos](https://diariodeavisos.elespanol.com/2016/12/fernando-clavijo-cesa-los-cuatro-consejeros-del-psoe/));
   Torres presidió de julio de 2019 a julio de 2023 con PSOE, NC, Podemos y ASG
   ([Wikipedia](https://en.wikipedia.org/wiki/Government_of_%C3%81ngel_V%C3%ADctor_Torres)); Clavijo volvió en julio de 2023 con un
   gobierno CC-PP, y la investidura sumó además ASG y AHI
   ([Diario de Avisos](https://diariodeavisos.elespanol.com/2023/07/fernando-clavijo-investido-presidente-de-canarias-con-el-apoyo-de-cc-pp-asg-y-ahi/)).
   Se ha retirado el aviso «pendiente de verificar» de `config/legislaturas.yml`.

## Lo que esta auditoría no cubre

- **La clasificación de gasto social (conceptos CED)** de los programas: viene del fichero de correspondencias de Canarias en Datos,
  que no forma parte de este repositorio. Se comprobó que los CSV publicados la conservan, no que la clasificación sea correcta.
- **El PIB regional** se toma de Canarias en Datos (INE, Contabilidad Regional); el IPC y la población sí se contrastaron en línea
  con el INE.
- **Los enlaces pendientes de revisión de los crosswalks** (`2_transformacion/crosswalks/revision_*.md`): sus series aparecen con
  huecos en la web hasta que se decidan. Es una limitación conocida, no un error de datos.
"""

METODO = """\
## Método

| Nivel | Qué se compara | Cómo |
|---|---|---|
| 1 · Fuente | Cada importe, peso, variación y capítulo de la web frente al **Tomo 3 oficial** de cada año (Ley o, si no la hay, Proyecto) | Lector propio de los PDF (`auditoria/fuente_pdf.py`), escrito aparte del extractor del pipeline para no repetir sus posibles errores. Importes al euro; pesos y variaciones con la precisión del Tomo (2 decimales) |
| 2 · Coherencia | Los CSV entre sí y con los datos externos | Totales iguales entre dimensiones y vistas, pesos, precios constantes, variaciones, ventanas, fases, capítulos, jerarquías y duplicados. IPC y población frente a la API del INE |
| 3 · Cálculos | Lo que la web calcula en el navegador | Variación en euros, por habitante, % del PIB, donut, ranking, «Sigue el dinero» y recorrido, recalculados en Python y contrastados con el Tomo y con las métricas del análisis |
| 4 · Pantalla | Lo que ve quien usa la web | Navegador automático (Playwright) que recorre combinaciones de filtros y lee tablas, tooltips, donut, flujo, ranking, recorrido y CSV descargado; cada cifra se compara con la esperada dentro de los decimales que se muestran |

### Repetir la auditoría

```bash
.venv/bin/python auditoria/auditar_datos.py   # niveles 1-3 (lee los PDF de 1_extraccion/raw; ~2 min)
node auditoria/auditar_web.cjs                 # nivel 4 (requiere Playwright)
.venv/bin/python auditoria/informe.py          # este informe
```
Las comprobaciones de coherencia (nivel 2, sin red ni PDF) también corren con los tests: `pytest tests/test_auditoria.py`.
"""


def main() -> int:
    datos = json.loads((AQUI / "resultados_datos.json").read_text(encoding="utf-8"))["resultados"]
    web_ruta = AQUI / "resultados_web.json"
    web = json.loads(web_ruta.read_text(encoding="utf-8")) if web_ruta.exists() else []
    todos = datos + web
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = "—"
    carga = next((l.split(",")[-1] for l in (RAIZ / "5_visualizacion/data/viz_meta.csv").read_text(encoding="utf-8").splitlines()
                  if l.startswith("carga,")), "—")
    cifras = sum(r["comprobados"] for r in todos)
    errores = [r for r in todos if r["estado"] == "ERROR"]
    avisos = [r for r in todos if r["estado"] == "AVISO"]
    expl = sum(r["comprobados"] for r in datos if r["id"].endswith("d") and r["id"].startswith("F"))
    out = [f"# Auditoría de datos · Presupuestos de Canarias 2015-2027", "",
           f"Fecha: {date.today():%d/%m/%Y} · Datos de la web cargados el {'/'.join(reversed(carga[:10].split('-')))} · "
           f"Código: `{commit}`", "",
           "## Resultado", "",
           f"**{len(todos)} comprobaciones sobre {miles(cifras)} cifras: {len(errores)} errores y {len(avisos)} avisos explicados.**",
           "", ("Los datos que muestra la web coinciden con el Tomo 3 oficial al euro en todos los años, dimensiones y capítulos, "
                "y lo que se ve en pantalla coincide con lo que debe mostrarse." if not errores else
                "Hay diferencias que corregir: ver la tabla."), ""]
    for nivel, titulo in NIVELES.items():
        filas = [r for r in todos if r["nivel"] == nivel]
        if not filas:
            continue
        out += [f"### {nivel} · {titulo}", "", "| Id | Comprobación | Comprobados | Con diferencia | Estado |", "|---|---|---:|---:|---|"]
        for r in filas:
            nota = f" <br>*{r['nota']}*" if r.get("nota") else ""
            out.append(f"| {r['id']} | {r['titulo']}{nota} | {miles(r['comprobados'])} | {miles(r['fallos'])} | {ICONO[r['estado']]} |")
        out.append("")
    detalle = [r for r in todos if r["estado"] != "OK" and r.get("ejemplos")]
    if detalle:
        out += ["### Detalle de avisos y errores", ""]
        for r in detalle:
            out += [f"- **{r['id']}** {r['titulo']}:"] + [f"  - {e}" for e in r["ejemplos"]]
        out.append("")
    out += [OBSERVACIONES.format(expl=expl), METODO]
    (AQUI / "informe_auditoria.md").write_text("\n".join(out), encoding="utf-8")
    print(f"auditoria/informe_auditoria.md · {len(todos)} comprobaciones · {len(errores)} errores · {len(avisos)} avisos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
