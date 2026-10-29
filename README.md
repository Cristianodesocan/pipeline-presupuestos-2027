# Pipeline · Presupuestos Generales de la CAC 2027

Pipeline de análisis de los Presupuestos de Canarias 2015-2027. Diseño: `../../1. Diseño de informe /diseno_pipeline_presupuestos_2027.md` y, para la extracción, `diseno_extraccion_tomo3.md`.

**Estado (28-10-2026):**
- ✅ **1 · Extracción**: construida y validada. 15 documentos y 10 tablas cada uno (incluida 2.2 *Servicios*), con todas las puertas en verde.
- ✅ **2 · Transformación**: construida y validada.
  - Los crosswalks quedan **pendientes de revisión humana**: 11 enlaces de secciones, 7 de programas y 1 de entes.
  - La cobertura de programas comparables es del 96,9 % del importe de 2026.
- ✅ **3 · Carga**: la carga local en DuckDB y CSV está hecha. La de Supabase está **probada contra un PostgreSQL local de prueba; producción todavía no se ha cargado**.
- ✅ **4 · Análisis**: los cuatro scripts (funciones, secciones, programas, entes) escriben `ana_metricas` (141.723 filas), los insights y las tablas APA. Los CSV de la web ya tienen datos.
- ✅ **5 · Visualización**: web D3 en `5_visualizacion/` con dos pestañas, Peso (treemap) y Evolución (líneas). Lee los `viz_*.csv`.
- ✅ **Maestro** `00_maestro.py`: ejecuta todo el pipeline siguiendo el DAG de `config/pipeline.yml`. Tiene caché por fase, se detiene si falla una puerta de calidad (*fail-fast*) y guarda un log estructurado. La serie completa tarda unos 50 s, casi todo en las comprobaciones web.

## Puesta en marcha

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python 00_maestro.py --paralelo        # todo el pipeline, destino local
```

## Orquestador (`00_maestro.py`)

```bash
.venv/bin/python 00_maestro.py --dry-run                         # plan sin ejecutar (indica qué fases están en caché)
.venv/bin/python 00_maestro.py --pasos transformacion,analisis   # solo esas fases, en el orden del DAG
.venv/bin/python 00_maestro.py --anio 2027 --fase proyecto       # extracción incremental de un documento
.venv/bin/python 00_maestro.py --pasos analisis --solo programas
.venv/bin/python 00_maestro.py --destino ambos --confirmar-produccion   # también Supabase (producción)
.venv/bin/python 00_maestro.py --forzar --estricto               # sin cachés; los avisos de calidad también bloquean
```

- **DAG:** `config/pipeline.yml` contiene las fases `extraccion → transformacion → carga → analisis → carga_analisis → viz`, sus tareas, dependencias, entradas y salidas. Cada tarea es un script que se lanza como subproceso con el mismo intérprete, así que sigue pudiendo ejecutarse suelto.
- **Caché por fase:**
  - **Cuándo se omite una fase:** cuando la huella SHA-256 de sus entradas (código, configuración, crosswalks validados y artefactos previos) no ha cambiado desde la última ejecución correcta y sus salidas existen.
  - **Qué cuenta en la caché:** también los parámetros (`--destino`, `--solo`, `--anio`, `--fase`).
  - **Extracción:** no se cachea a nivel de fase, porque tiene su propia caché por documento y comprueba la web.
- **Fail-fast:** si `validar_extraccion.py` o `2_transformacion/validar.py` fallan, el pipeline se detiene antes de cargar nada. El maestro nunca lanza una fase cuyas dependencias no tienen salidas.
- **Log:**
  - `logs/pipeline.jsonl` guarda una línea por tarea (`run_id`, script, código, duración).
  - `logs/maestro/<run_id>.log` guarda la salida completa.
- **Códigos de salida:** 0 = bien; 1 = error o puerta de calidad fallida; 2 = bien, pero con avisos. Por ejemplo, `descubrir_fuentes.py` encontró URLs nuevas que hay que revisar en `config/fuentes_propuestas.yml`.
- **Supabase:** solo se toca con `--destino supabase|ambos` y, contra producción, además con `--confirmar-produccion`.
- **No implementado:** el disparo automático desde `alerta-presupuestos-2027` (`repository_dispatch`). Requiere que este pipeline tenga su propio repositorio en GitHub.

## Extracción

Los pasos se ejecutan en este orden, siempre desde la raíz del pipeline:

```bash
.venv/bin/python 1_extraccion/descubrir_fuentes.py     # propone URLs nuevas (no descarga)
.venv/bin/python 1_extraccion/descargar_tomos.py       # catálogo → raw/ + logs/manifest.jsonl
.venv/bin/python 1_extraccion/extraer_tomo3.py         # raw/ → staging/stg_tomo3/*.parquet
.venv/bin/python 1_extraccion/validar_extraccion.py    # puertas E0-E10 → logs/validacion_extraccion.json
.venv/bin/python -m pytest tests                        # 90 tests (extracción, transformación, carga, análisis y maestro; la web se prueba en el navegador)
```

| Script | Lee | Escribe | Código de salida |
|---|---|---|---|
| `descubrir_fuentes.py` | portal web (2023+), `config/fuentes.yml` | `config/fuentes_propuestas.yml` | 2 si hay propuestas |
| `descargar_tomos.py` | `config/fuentes.yml` | `1_extraccion/raw/<año>/<fase>/tomo3_<sha8>.pdf`, `logs/manifest.jsonl` | 1 si algún documento se rechaza |
| `extraer_tomo3.py` | manifest + `config/tablas_tomo3.yml` | `1_extraccion/staging/stg_tomo3/<doc_id>.parquet` | 1 si algún documento falla |
| `validar_extraccion.py` | staging + `config/referencias_tomo3.yml` | `logs/validacion_extraccion.json` | 1 si hay errores (`--estricto`: también con avisos) |

Opciones comunes: `--anio 2027 --fase proyecto` filtra; `--forzar` ignora la caché, o el ETag en el caso de la descarga.

### Configuración

- `config/fuentes.yml` es el **catálogo canónico** de URLs y SHA-256. Los nombres de fichero no siguen ningún patrón, así que no se construyen a mano.
- `config/tablas_tomo3.yml` es la especificación declarativa de las tablas. Para añadir una tabla basta con añadir una entrada.
- `config/referencias_tomo3.yml` contiene las cifras de regresión leídas en los PDF. **No se usan las de Canarias en Datos**: tenían un error con los programas extinguidos.

### Salida tidy

Hay una fila por celda de cada tabla. Campos principales:

- `tabla`, `nivel` (`detalle` / `grupo` / `total`), `codigo`, `codigo_padre`, `ente`, `denominacion_raw`;
- `columna`, `anio_importe`, `version_importe` (`inicial` / `ajustado`), `capitulo`, `valor`, `unidad` (`eur` / `pct`);
- `perimetro` (`cac_cap_1_8` / `cac_cap_1_9` / `entes`), más la trazabilidad (`sha256`, `pagina`, `version_extractor`).

Para leer el staging desde Python:

```python
import sys; sys.path.insert(0, "1_extraccion")
from _comun.staging import leer_staging
programas = leer_staging(tabla="programas", fase="ley")
```

⚠ **No hay que sumar perímetros distintos.** Las tablas comparativas (2.1, 2.8, 2.9, 2.10, 3.1) excluyen el capítulo 9; las de capítulos (2.11, 2.14, 2.16, 3.2) lo incluyen.

### Avisos conocidos (esperados)

- **E8 · 2017:** el ajustado de 2016 en el tomo de 2017 supera en 159,2 M€ al inicial de la Ley 2016. Es un cambio de perímetro y está pendiente de investigar.
- **E5 · 2018:** «Agencia Canaria de Protección del Medio Natural» tiene otro nombre en 3.1, así que se empareja por importe.

## Transformación

Los pasos se ejecutan en este orden, siempre desde la raíz:

```bash
.venv/bin/python 2_transformacion/externos.py              # IPC, población y PIB (CSV versionado; --actualizar consulta el INE)
.venv/bin/python 2_transformacion/normalizar.py            # staging → fact_base, dim_anio, fondos_extraordinarios
.venv/bin/python 2_transformacion/crosswalks.py            # propone enlaces entre años (5 dimensiones)
.venv/bin/python 2_transformacion/construir_modelo.py      # id_estable, familias, dim_*, fact_presupuesto (+ € constantes)
.venv/bin/python 2_transformacion/retroproyectar_secciones.py   # vista de secciones en la estructura del último año
.venv/bin/python 2_transformacion/validar.py               # puertas T1-T13 → logs/validacion_transformacion.json
```

| Salida (`2_transformacion/staging/`) | Contenido |
|---|---|
| `fact_presupuesto.parquet` | Hechos en € corrientes y constantes (base 2025). Llevan `dimension`, `codigo`, `id_estable`, `familia_id`, `id_padre`, `serie_oficial` (Ley o, si no hay, Proyecto), `perimetro` y `es_fondo_extraordinario` |
| `dim_{seccion,funcion,subfuncion,programa,ente}.parquet` | Vigencia, `denominacion_std`, `familia_id`, `comparabilidad` (continua · familia · parcial · subfuncion · pendiente) y `concepto_ced` |
| `dim_anio.parquet` | IPC, deflactor, población, PIB y ventana de gobierno (`config/legislaturas.yml`) |
| `fact_seccion_estructura.parquet` | Secciones de cada año en la estructura de consejerías del último año (método de asignación por fila) |
| `fondos_extraordinarios.{parquet,csv}` | Servicios MRR / REACT-EU de la tabla 2.2 |
| `xwalk_<dim>.parquet` | Enlaces efectivos y su estado (`auto`, `validado`, `pendiente`, `rechazado`, `sin_enlace`) |

### Revisión humana de los crosswalks

1. Lee `2_transformacion/crosswalks/revision_<dim>.md`. Tiene los casos pendientes ordenados por importe y las unidades sin origen.
2. Copia la fila que quieras decidir de `xwalk_<dim>_propuesto.csv` a `xwalk_<dim>_validado.csv`. Rellena `decision=aceptar|rechazar`, `validado_por` y `validado_en`. Si quieres, corrige también `tipo_enlace`.
3. Para enlaces que el algoritmo no vio, añade la fila a mano con `decision=aceptar`.
4. Vuelve a ejecutar `crosswalks.py`, `construir_modelo.py`, `retroproyectar_secciones.py` y `validar.py`.

Los enlaces `auto` se usan salvo que se rechacen. Los que están en revisión sin decidir dejan sus series como `comparabilidad=pendiente`. Los `*_validado.csv` y `externos/externos_canarias.csv` se versionan, porque son decisiones metodológicas o datos fijados.

### Hallazgos de la transformación

- **FDCAN:** el cambio de perímetro de 2017 (+159,2 M€, aviso E8/T7) es el **Fondo de Desarrollo de Canarias** (`943A`). Aparece con el ajustado exacto.
- **Parlamento:** en 2022 los programas `911x` se funden en `912L` y salen de las secciones (pasan a la tabla de entes).
- **Fondos MRR / REACT-EU** (servicios 70-71 de la tabla 2.2): 170 M€ en 2022, 280 M€ en 2023, 378 M€ en 2024, 418 M€ en 2025 y 447 M€ en 2026. **No** se limitan a 2021-2023. La Ley 2021 no los etiqueta.
- **Retroproyección a la estructura de 2026:** el 94 % del importe se asigna sin ambigüedad (familia en una sola sección). Lo que queda sin equivalente pesa un 1,5 % en 2015 y un 0 % desde 2022.

## Carga

```bash
.venv/bin/python 3_carga/local/cargar_local.py           # DuckDB 3_carga/local/presupuestos.duckdb + espejo CSV en 3_carga/local/csv/
.venv/bin/python 3_carga/exportar_viz.py                 # vistas v_viz_* → 5_visualizacion/data/viz_*.csv
.venv/bin/python 3_carga/supabase/cargar_supabase.py --escribir-esquema   # regenera 3_carga/supabase/esquema.sql (sin conexión)
.venv/bin/python 3_carga/supabase/cargar_supabase.py --confirmar-produccion  # carga en Supabase (requiere .env)
```

- **Un solo modelo.** Tablas, tipos y claves naturales se definen en `3_carga/modelo_bd.py`, y de ahí sale el DDL de los dos destinos. Las vistas de la web están en `3_carga/vistas_viz.sql`, con un SQL común a DuckDB y PostgreSQL. `supabase/esquema.sql` se **genera**, no se edita a mano.
- **Idempotente y espejo.** Cada tabla se vuelca a una temporal, se hace `INSERT … ON CONFLICT DO UPDATE` y se borra lo que ya no está en el origen, todo en una sola transacción. Si se ejecuta dos veces, queda igual. Cada carga se anota en `carga_registro` (`run_id`, filas nuevas y borradas).
- **`--que base|analisis|todo`.** La primera pasada carga la transformación; la segunda, `ana_metricas`, cuando exista la fase 4.
- **Seguridad en Supabase:**
  - RLS activado en todas las tablas y sin políticas para `anon`/`authenticated`; solo las vistas `v_viz_*` tienen `GRANT SELECT`.
  - Contra un host que no sea localhost, la carga se niega sin `--confirmar-produccion`.
  - Credenciales en `.env`; la plantilla es `.env.example`.
  - Para exponer el esquema por la API REST, añade `presupuestos_cac` a *Exposed schemas* en el panel de Supabase.
- **Probado** contra un PostgreSQL 17 local que imita los roles de Supabase. Resultados:
  - las dos pasadas son idempotentes;
  - `anon` no puede leer las tablas y sí las vistas;
  - los totales cuadran con DuckDB;
  - `viz_meta.csv` sale idéntico desde las dos fuentes.

  El test `test_postgres_rls_solo_vistas` se ejecuta si `PG_TEST_URL` apunta a un PostgreSQL de prueba en localhost.
- **Convenciones de `ana_metricas`.** Las vistas de la web dependen de ellas (`ventana`, `incluye_mrr`, `ruta_jerarquia`), que están al principio de `vistas_viz.sql`.
- **DuckDB 2.0.0 reemplaza cada tabla completa.** El anti-join (`NOT EXISTS`/`EXCEPT`) contra una tabla con clave primaria daba resultados erróneos dentro de una transacción de escritura: la primera carga de `ana_metricas` quedó vacía sin error. Las altas y bajas se cuentan ahora en pandas y se comprueba que se escriben todas las filas. PostgreSQL mantiene el *upsert*.

## Análisis

Cada script es independiente y lee de la carga local, o de Supabase con `--fuente supabase --confirmar-produccion`:

```bash
.venv/bin/python 4_analisis/analisis_funciones.py    # área → función → subfunción · capítulos del crecimiento · gasto social
.venv/bin/python 4_analisis/analisis_secciones.py    # vistas orgánica y estructura_<último año> · reorganización · sin MRR
.venv/bin/python 4_analisis/analisis_programas.py    # individual · familia · concepto CED · altas y bajas · calidad
.venv/bin/python 4_analisis/analisis_entes.py        # tabla 3.1 (no aditiva con la CAC) · tipos de ente · consolidación
.venv/bin/python 3_carga/local/cargar_local.py --que analisis && .venv/bin/python 3_carga/exportar_viz.py
```

**Salidas:**
- `4_analisis/salidas/<dim>/` contiene `ana_<dim>.csv` (tidy, §7.1 del diseño), `insights_<dim>.md` (hallazgos con estatus) y `tablas_<dim>.xlsx` (tablas APA).
- `4_analisis/salidas/ana_<dim>.parquet` es lo que carga `3_carga`.
- `--anio-actual` limita la serie a un año (útil para comparar con informes anteriores).

**Módulos comunes:**
- `_metricas.py`: funciones **puras** de §7.2 (pesos, variaciones, homogéneas y reestructuración, ventanas, TCAC, Δ peso, elasticidad, ruptura de tendencia, HHI, volatilidad, saltos, per cápita, % PIB). Todas se calculan en corrientes y en constantes.
- `_lectura.py`: E/S y paneles.
- `_informes.py`: insights comunes y tablas APA.
- `config/analisis.yml`: áreas de gasto, secciones no departamentales, tipos de ente y umbrales.

**Notas de método:**
- **Ventana actual incompleta.** `clavijo_ii` es 2023→2026 hasta que salga 2027, y los insights lo indican. La ventana completa se llama `<primer año>_<último año>`.
- **Métricas de ventana de programas por familia.** Se calculan sobre la vista `familia`, que agrega divisiones y fusiones aceptadas.
- **Reorganizaciones de secciones por código.** Se calculan con el código y no con el `id_estable`, porque los enlaces de secciones pendientes de revisión cortan los id.
- **Estatus `estimacion`.** Lo llevan todas las métricas en constantes que tocan 2026, cuyo IPC solo tiene 9 meses. La atribución causal al gobierno (`hipotesis`) no la genera el pipeline.

**Hallazgos destacados (serie 2015-2026, ventana actual 2023→2026):**
- **Crecimiento real frente a nominal.** El total crece un 13,8 % real (22,8 % nominal), frente al 11,7 % real de 2019→2023 (8,5 % sin MRR/REACT-EU) y al 23,1 % de 2015→2019.
- **Quién gana y quién pierde peso.** Ganan Industria y Energía (+1,6 pp, programa 425A *Desarrollo Energético*), Sanidad (+1,3 pp) y Dependencia (+0,6 pp). Pierde sobre todo Educación (−1,5 pp: Infantil/Primaria y Secundaria/FP), seguida de Infraestructuras, Empleo y Agricultura.
- **Reorganización de 2024.** Nace *Universidades, Ciencia e Innovación y Cultura* con 395 M€, sobre todo de Educación (−324 M€). Presidencia recibe 156 M€ y Política Territorial, 114 M€.
- **Fondos MRR / REACT-EU.** Son el 3,8 % del total en 2025-2026.
- **Gasto social.** Las áreas 2 y 3 pesan un 70 % (74 % en 2015). Su crecimiento se canaliza sobre todo por transferencias corrientes (capítulo 4: la CAC financia al Servicio Canario de la Salud).
- **Programas nuevos.** El mayor de la legislatura es *Reconstrucción de La Palma* (929B), con 53 M€ en 2026.

## Visualización

```bash
python3 -m http.server 8765 --directory 5_visualizacion   # y abre http://localhost:8765
```

Hace falta un servidor, porque el navegador no deja leer los CSV desde `file://`. Los datos son `5_visualizacion/data/viz_*.csv`: la exportación de las vistas `v_viz_*` (`3_carga/exportar_viz.py`). La web no necesita credenciales ni conexión con Supabase. Puede publicarse tal cual en GitHub Pages o integrarse en el Hub de Canarias en Datos.

**Estructura:**
- `index.html` y `css/odesocan.css`, con la identidad ODESOCAN (Space Grotesk/Inter, paleta teal/navy, modo claro y oscuro).
- `js/comun.js`: datos, formato es-ES, paleta y tooltip.
- `js/estado.js`: el estado en la URL.
- `js/treemap.js` y `js/lineas.js`: los dos gráficos.
- `js/app.js`: filtros, tablas, CSV y tema.
- D3 7.9.0 fijo, desde cdnjs.

**Funcionalidades:**
- **Filtros.** Van en una sola fila encima de los gráficos:
  - dimensión (funciones · secciones · programas · entes);
  - vista (secciones: orgánica / estructura del último año; programas: programa / familia);
  - año, precios (corrientes / constantes 2025) y filtro de gasto social (programas, conceptos CED).
  - El estado se guarda en la URL (`#dim=programas&anio=2026…`) para compartir vistas concretas.
- **Peso.**
  - **Jerarquía:** área → función → subfunción; grupo → sección; función → subfunción → programa; tipo → ente.
  - **Ampliar:** clic en la cabecera de un grupo; las migas de pan permiten volver.
  - **Color:** por categoría, o por **Δ peso del gobierno actual** (escala divergente rojo · gris · teal centrada en 0).
  - **Tooltip:** importe, pesos, variación interanual y cambio en la ventana.
- **Evolución.**
  - **Medidas:** euros, variación % interanual o índice 2015 = 100.
  - **Partidas:** hasta 7, elegidas con el buscador. Cada una conserva su color al quitar otras.
  - **Contexto político:** bandas por ventana de gobierno, con la actual destacada.
  - **Honestidad de la serie:** huecos donde la serie no es comparable; tramo discontinuo si el año está en fase de Proyecto.
  - **Tooltip:** una cruceta con todas las series del año.
- **Accesibilidad.**
  - Vista de tabla en las dos pestañas y descarga del CSV filtrado.
  - Celdas del treemap navegables con el teclado.
  - Las etiquetas solo se pintan si caben.
  - Paleta categórica **validada** con `validate_palette.js` (contraste, daltonismo y visión normal) en los dos modos.
  - Textos con contraste ≥ 4,5:1.
  - Probado en escritorio y móvil (375 px, sin desplazamiento horizontal).

**Limitación conocida:** en la vista orgánica de secciones, las series de varias consejerías empiezan en 2024. Es así hasta que se revisen los enlaces pendientes del crosswalk de secciones. La vista estructura no tiene ese corte.

## Cuando salga el Proyecto 2027

1. Ejecuta `00_maestro.py --pasos extraccion --anio 2027`: sale con código 2 y deja `config/fuentes_propuestas.yml`. Revísalo y copia la entrada a `config/fuentes.yml`. Después ejecuta `00_maestro.py --paralelo`, que equivale a los pasos 2 y 4.
2. Ejecuta `descargar_tomos.py --anio 2027 --fase proyecto`, después `extraer_tomo3.py` y por último `validar_extraccion.py`.
3. **Si falla, ha cambiado la maqueta.** Ajusta `config/tablas_tomo3.yml` o los parámetros de `_comun/tomo3.py`. Después vuelve a ejecutar toda la serie con `--forzar` y los tests.
4. Ejecuta la cadena de transformación. El Proyecto 2027 entra solo en la serie oficial, porque todavía no hay Ley. Después:
   1. Revisa `revision_<dim>.md`: aparecerán los cambios 2026 → 2027.
   2. Fija `deflactor.tasa_prevision.2027` en `config/transformacion.yml` con el cuadro macroeconómico del Tomo 4.
   3. Fija `validacion.techo_gasto_no_financiero.2027` con el límite aprobado.
   4. Ejecuta `externos.py --actualizar`.
5. Lo mismo con la Ley 2027 (`--fase ley`) a finales de diciembre. Al existir Ley, sustituye al Proyecto en la serie oficial.
