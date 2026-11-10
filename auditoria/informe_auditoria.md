# Auditoría de datos · Presupuestos de Canarias 2015-2027

Fecha: 10/11/2026 · Datos de la web cargados el 10/11/2026 · Código: `f2ec503`

## Resultado

**54 comprobaciones sobre 169.801 cifras: 0 errores y 6 avisos explicados.**

Los datos que muestra la web coinciden con el Tomo 3 oficial al euro en todos los años, dimensiones y capítulos, y lo que se ve en pantalla coincide con lo que debe mostrarse.

### 1 · Fuente: los datos frente al Tomo 3 oficial

| Id | Comprobación | Comprobados | Con diferencia | Estado |
|---|---|---:|---:|---|
| F0 | Documento de cada año = fase que muestra la web (Ley, o Proyecto si no hay Ley) | 13 | 0 | ✅ OK |
| F1a | Importe inicial de cada fila de secciones (tabla 2.1) = Tomo, al euro | 195 | 0 | ✅ OK |
| F1b | Peso sobre el total de secciones (tabla 2.1) = % del Tomo | 195 | 0 | ✅ OK |
| F1c | Variación interanual de secciones (tabla 2.1) = % «2/1» del Tomo <br>*24 diferencias explicadas: el Tomo compara con el presupuesto anterior AJUSTADO a la nueva estructura y la web, con el inicial de la misma partida* | 166 | 0 | ⚠️ Aviso |
| F1d | De esas diferencias, cuántas vienen de enlazar secciones de códigos distintos entre años (a revisar) <br>*el resto compara el mismo código en los dos años* | 24 | 0 | ✅ OK |
| F2a | Importe inicial de cada fila de funciones (2.8) = Tomo, al euro | 273 | 0 | ✅ OK |
| F2b | Peso sobre el total de funciones (2.8) = % del Tomo | 273 | 0 | ✅ OK |
| F2c | Variación interanual de funciones (2.8) = % «2/1» del Tomo <br>*39 diferencias explicadas: el Tomo compara con el presupuesto anterior AJUSTADO a la nueva estructura y la web, con el inicial de la misma partida* | 252 | 0 | ⚠️ Aviso |
| F2d | De esas diferencias, cuántas vienen de enlazar funciones de códigos distintos entre años (a revisar) <br>*el resto compara el mismo código en los dos años* | 39 | 0 | ✅ OK |
| F3a | Importe inicial de cada fila de subfunciones (2.9) = Tomo, al euro | 678 | 0 | ✅ OK |
| F3b | Peso sobre el total de subfunciones (2.9) = % del Tomo | 678 | 0 | ✅ OK |
| F3c | Variación interanual de subfunciones (2.9) = % «2/1» del Tomo <br>*61 diferencias explicadas: el Tomo compara con el presupuesto anterior AJUSTADO a la nueva estructura y la web, con el inicial de la misma partida* | 618 | 0 | ⚠️ Aviso |
| F3d | De esas diferencias, cuántas vienen de enlazar subfunciones de códigos distintos entre años (a revisar) <br>*el resto compara el mismo código en los dos años* | 61 | 0 | ✅ OK |
| F4a | Importe inicial de cada fila de programas (2.10) = Tomo, al euro | 1.809 | 0 | ✅ OK |
| F4b | Peso sobre el total de programas (2.10) = % del Tomo | 1.809 | 0 | ✅ OK |
| F4c | Variación interanual de programas (2.10) = % «2/1» del Tomo <br>*86 diferencias explicadas: el Tomo compara con el presupuesto anterior AJUSTADO a la nueva estructura y la web, con el inicial de la misma partida* | 1.567 | 0 | ⚠️ Aviso |
| F4d | De esas diferencias, cuántas vienen de enlazar programas de códigos distintos entre años (a revisar) <br>*el resto compara el mismo código en los dos años* | 86 | 0 | ✅ OK |
| F5a | Importe inicial de cada fila de entes (3.1) = Tomo, al euro | 198 | 0 | ✅ OK |
| F5b | Peso sobre el total de entes (3.1) = % del Tomo | 198 | 0 | ✅ OK |
| F5c | Variación interanual de entes (3.1) = % «2/1» del Tomo <br>*16 diferencias explicadas: el Tomo compara con el presupuesto anterior AJUSTADO a la nueva estructura y la web, con el inicial de la misma partida* | 181 | 0 | ⚠️ Aviso |
| F5d | De esas diferencias, cuántas vienen de enlazar entes de códigos distintos entre años (a revisar) <br>*el resto compara el mismo código en los dos años* | 16 | 0 | ✅ OK |
| F6 | Total de cada dimensión y vista = «TOTAL CAPÍTULOS DEL 1 AL 8» del Tomo | 78 | 0 | ✅ OK |
| F7 | Capítulos 1-9 de secciones (2.11) y su fila Total = Tomo, al euro | 1.664 | 0 | ✅ OK |
| F8 | Capítulos 1-9 de funciones (2.13) y su fila Total = Tomo, al euro | 2.288 | 0 | ✅ OK |
| F9 | Entes: capítulos de la tabla 3.2 = importe de la tabla 3.1 <br>*discrepancia dentro del propio Tomo: la web muestra la 3.1 en el treemap y la 3.2 en el donut* | 198 | 1 | ⚠️ Aviso |

### 2 · Coherencia interna y datos externos

| Id | Comprobación | Comprobados | Con diferencia | Estado |
|---|---|---:|---:|---|
| I1 | Sin filas duplicadas en los CSV | 26.117 | 0 | ✅ OK |
| I2 | Sin importes negativos ni partidas sin nombre | 26.117 | 0 | ✅ OK |
| I3 | Mismo total por año en funciones, subfunciones, áreas, secciones (2 vistas) y programas (2 vistas) | 156 | 0 | ✅ OK |
| I4 | Peso sobre el total = importe / total de la tabla × 100 (y suman 100) | 10.644 | 0 | ✅ OK |
| I5 | Euros constantes = corrientes × deflactor del año (viz_anios) | 10.982 | 0 | ✅ OK |
| I6 | Treemap y series: mismo importe y misma variación % para cada partida y año | 21.964 | 0 | ✅ OK |
| I7 | Variación interanual (% y €) = frente al presupuesto inicial anterior de la misma partida | 10.008 | 0 | ✅ OK |
| I8 | Δ peso y variación del gobierno actual = 2027 frente a 2023 | 774 | 0 | ✅ OK |
| I9 | Fase (solo el último año en Proyecto) y gobierno de cada año = config/legislaturas.yml | 26 | 0 | ✅ OK |
| I10 | Capítulos 1-8 de cada partida (todas las dimensiones y vistas menos entes) = su importe en la web | 4.984 | 0 | ✅ OK |
| I11 | Capítulos: pares sección×programa = secciones; programas de cada ente = ente; estructura = orgánica; deflactor = viz_anios | 5.924 | 0 | ✅ OK |
| I12 | Cada programa cuelga de la función y subfunción que indica su código | 1.823 | 0 | ✅ OK |
| I14 | Peso en el grupo = importe / total de su grupo inmediato × 100 | 6.774 | 0 | ✅ OK |
| I13 | Años: deflactor = 1 en 2025 y población para todos los años de la web <br>*son estimaciones: IPC o población de [2026, 2027]* | 14 | 0 | ✅ OK |
| E1 | Deflactor (IPC Canarias, base 2025) y población a 1 de enero = API del INE consultada hoy <br>*IPC incompleto en 2026 (9 meses); sin dato del INE (estimados): población [2027], IPC [2027]* | 26 | 0 | ✅ OK |

### 3 · Cálculos que hace la web

| Id | Comprobación | Comprobados | Con diferencia | Estado |
|---|---|---:|---:|---|
| W1 | Variación interanual en € del tooltip = diferencia con el año anterior del pipeline | 9.956 | 0 | ✅ OK |
| W1b | Variación en € de las secciones = inicial − ajustado del Tomo (secciones sin reestructurar) | 143 | 0 | ✅ OK |
| W2 | € por habitante y % del PIB de la web = métricas per_capita y pct_pib del análisis | 15.192 | 0 | ✅ OK |
| W3 | Donut sin selección (raíz) = capítulos 1-8 de la fila Total del Tomo, en las 3 dimensiones | 273 | 0 | ✅ OK |
| W4 | Cifras del recorrido, ranking, flujo y tablas recalculadas para contrastar con la pantalla (nivel 4) <br>*ver auditoria/auditar_web.cjs* | 65 | 0 | ✅ OK |

### 4 · Lo que se ve en pantalla

| Id | Comprobación | Comprobados | Con diferencia | Estado |
|---|---|---:|---:|---|
| D1 | Tablas de la pestaña Peso (60 combinaciones de dimensión, vista, año y precios) | 3.460 | 0 | ✅ OK |
| D2 | Donut por capítulos sin selección (total del centro, importe y % de cada capítulo y nota del cap. 9) | 512 | 0 | ✅ OK |
| D3 | Tooltip de la mayor partida de cada dimensión (importe, peso, variación € y %, flecha verde/roja) | 20 | 0 | ✅ OK |
| D4 | «Sigue el dinero» de Sanidad (14) en 2026: transferencias y gasto del SCS en las mismas subfunciones | 2 | 0 | ✅ OK |
| D5 | Ranking «¿qué ha cambiado?» 2023→último año (orden, diferencia en € y en %) | 36 | 0 | ✅ OK |
| D6 | Tabla de Evolución en € por habitante (corrientes y constantes) y % del PIB | 234 | 0 | ✅ OK |
| D7 | Recorrido guiado: cifras y nombres de las 5 claves | 16 | 0 | ✅ OK |
| D8 | CSV descargado de la pestaña Peso (programas 2026): una fila por partida | 1 | 0 | ✅ OK |
| D9 | Sin errores de JavaScript durante toda la auditoría | 1 | 0 | ✅ OK |

### Detalle de avisos y errores

- **F9** Entes: capítulos de la tabla 3.2 = importe de la tabla 3.1:
  - 2021 ESCS_2015: tabla 3.1 3.301.248.249 € · capítulos (3.2) 3.300.693.715 € (−554.534 €)

## Observaciones

1. **Variación interanual: la web y el Tomo no comparan exactamente lo mismo.** La web compara el presupuesto inicial de cada
   partida con su inicial del año anterior. La columna «2/1» del Tomo compara con el presupuesto anterior *ajustado* a la nueva
   estructura. Coinciden salvo cuando una consejería, función o programa cambia de competencias. En la serie hay 226 casos así,
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
