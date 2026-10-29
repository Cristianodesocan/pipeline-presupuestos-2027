# ¿Qué suele pasar en los presupuestos preelectorales?

Generado 2026-10-29T10:53:39+00:00 por `analisis_preelectoral.py`. Serie oficial 2015-2026 (Ley), euros constantes de 2025. Presupuestos electorales observables: 2019, 2023; pendiente: 2027.

## Resumen

**Estatus:** verificado (descripción de cifras) · cualquier lectura sobre la intención electoral es *hipótesis*.

- **Tamaño del presupuesto.** El total crece en términos reales un 7,0 % en 2019 y un 7,7 % en 2023, frente a una media del 3,5 % en los demás presupuestos (permutación p = 0,11). Los dos presupuestos electorales están entre los más expansivos de la serie.
- **Gasto corriente (caps. 1-4)**: anomalía 2019: 1,9 pp · 2023: -2,4 pp → *mixto*.
- **Gasto de capital (caps. 6-7)**: anomalía 2019: -18,3 pp · 2023: 13,0 pp → *mixto*.
- **Partidas con el mismo signo en todos los años electorales:** funciones 3 se acentúan y 7 se contraen (de 21); consejerías 4 / 7 (de 16); programas con peso ≥ 0,5 %: 7 / 9 (de 26).
- **Tras corregir por comparaciones múltiples** (q de Benjamini-Hochberg ≤ 0,10): capitulo: 0, funcion: 0, consejeria: 0, subfuncion: 0, programa: 0 partidas con acentuación y capitulo: 0, funcion: 0, consejeria: 0, subfuncion: 0, programa: 0 con contracción distinguibles del azar.

**Cómo leerlo.** Con dos casos, una regularidad «en ambos años» puede ser casualidad: si las anomalías fueran ruido simétrico, una de cada cuatro partidas tendría el mismo signo positivo en los dos años y otra de cada cuatro, el negativo. El interés está en las partidas que repiten patrón **con importe relevante** y en si el patrón aparece en la naturaleza del gasto (capítulos), que es lo que predice la literatura sobre ciclos políticos presupuestarios: más gasto visible (inversión, transferencias) antes de las elecciones.

## Lo que se repite con importe relevante

Partidas (consejerías y subfunciones) con el mismo signo de anomalía en todos los años electorales y al menos 20 M€ de exceso acumulado. **«Se contrae» significa que crece menos que el total, no que se recorte.**

| Nivel | Partida | Patrón | Exceso acumulado (M€) | Anomalía media (pp) | p |
|---|---|---|---|---|---|
| consejeria | TRANSFERENCIAS A CORPORACIONES LOCALES (20) | se acentúa | 127,5 | 11,4 | 0,02 |
| subfuncion | Transferencias a Corporaciones Locales (942) | se acentúa | 127,5 | 11,4 | 0,02 |
| subfuncion | Fondo de desarrollo de Canarias (943) | se acentúa | 61,5 | 55,1 | 0,11 |
| subfuncion | Imprev., situac. transitorias y conting. de ejec. (929) | se acentúa | 57,3 | 32,3 | 0,22 |
| consejeria | TURISMO Y EMPLEO (16) | se acentúa | 53,8 | 17,9 | 0,02 |
| subfuncion | Promoción del Empleo (241) | se acentúa | 29,1 | 25,7 | 0,02 |
| subfuncion | Ordenación y promoción turística (432) | se acentúa | 27,4 | 12,9 | 0,04 |
| consejeria | OBRAS PÚBLICAS, VIVIENDA Y MOVILIDAD (11) | se contrae | -34,6 | -16,5 | 0,36 |
| subfuncion | Administración General de Economía y Hacienda (923) | se contrae | -35,3 | -34,2 | 0,04 |
| subfuncion | Infraestructuras del transporte terrestre (453) | se contrae | -37,7 | -27,1 | 0,36 |
| consejeria | HACIENDA Y RELACIONES CON LA UNIÓN EUROPEA (10) | se contrae | -39,4 | -19,8 | 0,04 |
| subfuncion | Subvenciones al transporte (441) | se contrae | -41,2 | -24,7 | 0,07 |
| consejeria | EDUCAC.,FORMAC.PROFESIONAL,ACTIV. FÍSICA Y DEPORT (18) | se contrae | -119,0 | -3,4 | 0,16 |
| subfuncion | Enseñanza (322) | se contrae | -139,8 | -3,7 | 0,15 |
| subfuncion | Hospitales, serv. asistenciales y centros de salud (312) | se contrae | -191,5 | -1,6 | 0,15 |
| consejeria | SANIDAD (14) | se contrae | -191,6 | -1,6 | 0,13 |


## 1. El tamaño del presupuesto

| Año | Var. real del total (%) |
|---|---|
| 2016 | 0,9 |
| 2017 | 4,3 |
| 2018 | 9,3 |
| **2019** ⚑ | 7,0 |
| 2020 | 1,9 |
| 2021 | 2,3 |
| 2022 | -0,5 |
| **2023** ⚑ | 7,7 |
| 2024 | 7,8 |
| 2025 | 1,3 |
| 2026 | 4,3 |

| Año | Var. real del total (%) | Media de los 3 previos de su legislatura (%) |
|---|---|---|
| 2019 | 7,0 | 4,9 |
| 2023 | 7,7 | 1,2 |

Factor de confusión principal: la financiación autonómica (entregas a cuenta y liquidaciones) y los fondos MRR/REACT-EU, que determinan cuánto se puede presupuestar con independencia del calendario electoral.

## 2. Naturaleza económica del gasto (capítulos, tabla 2.11)

Anomalía = diferencial del año electoral frente a la media de los tres presupuestos previos de su legislatura. Exceso = euros por encima (+) o por debajo (−) de lo que habría tenido el capítulo creciendo como el total.

| Partida | Anomalía 2019 (pp) | Exceso 2019 (M€) | Anomalía 2023 (pp) | Exceso 2023 (M€) | Peso último año (%) | p / q | Patrón |
|---|---|---|---|---|---|---|---|
| Cap. 3 · Gastos financieros | 11,3 | -9,1 | 124,6 | 23,6 | 0,89 | 0,16 / 0,74 | se acentúa |
| Cap. 2 · Bienes corrientes y servicios | -1,5 | -3,4 | 9,7 | 34,2 | 4,40 | 0,18 / 0,74 | mixto |
| Gasto corriente (caps. 1-4) | 1,9 | -4,6 | -2,4 | -232,0 | 82,81 | 0,73 / 0,94 | mixto |
| Cap. 4 · Transferencias corrientes | 1,3 | -3,2 | -2,1 | -155,0 | 58,12 | 0,73 / 0,94 | mixto |
| Cap. 7 · Transferencias de capital | -18,8 | 67,7 | 13,8 | 158,2 | 11,61 | 0,31 / 0,74 | mixto |
| Cap. 1 · Personal | 2,9 | 11,2 | -8,0 | -134,8 | 19,40 | 0,84 / 0,94 | mixto |
| Gasto de capital (caps. 6-7) | -18,3 | 38,6 | 13,0 | 244,3 | 17,04 | 0,42 / 0,75 | mixto |
| Cap. 6 · Inversiones reales | -27,9 | -29,1 | 11,5 | 86,1 | 5,43 | 0,33 / 0,74 | mixto |
| Cap. 8 · Activos financieros | -44,3 | -34,0 | -85,3 | -12,2 | 0,15 | 1,00 / 1,00 | se contrae |

## 3. Funciones de gasto

| Partida | Anomalía 2019 (pp) | Exceso 2019 (M€) | Anomalía 2023 (pp) | Exceso 2023 (M€) | Peso último año (%) | p / q | Patrón |
|---|---|---|---|---|---|---|---|
| Deuda Pública (95) | 10,8 | -9,7 | 127,6 | 23,6 | 0,88 | 0,16 / 0,76 | se acentúa |
| Fomento del Empleo (24) | 38,3 | 17,9 | 13,1 | 11,2 | 0,81 | 0,02 / 0,38 | se acentúa |
| Investigación, desarrollo e innovación (46) | 28,2 | 2,6 | 11,6 | 11,5 | 0,77 | 0,11 / 0,76 | se acentúa |
| Transferencias a otras Administraciones Públicas (94) | -2,8 | 69,8 | 23,6 | 119,2 | 9,64 | 0,16 / 0,76 | mixto |
| Acceso a la vivienda y fomento de la edificación (26) | 33,2 | 20,6 | -14,7 | 1,2 | 1,43 | 0,18 / 0,76 | mixto |
| Comercio, Turismo y Pymes (43) | 18,0 | 19,9 | -12,6 | -0,8 | 1,86 | 0,29 / 0,87 | mixto |
| Servicios de carácter general (92) | -2,8 | 23,1 | 8,1 | 6,4 | 3,08 | 0,45 / 0,91 | mixto |
| Servicios Sociales y Promoción Social (23) | 4,3 | 56,8 | -1,0 | 15,7 | 7,05 | 0,25 / 0,87 | mixto |
| Seguridad ciudadana e instituciones penitenciarias (13) | -1,1 | -0,8 | -0,7 | 3,7 | 0,56 | 0,53 / 0,91 | se contrae |
| Alta Dirección (91) | 8,5 | 6,2 | -11,6 | -9,9 | 0,89 | 0,75 / 0,94 | mixto |
| Sanidad (31) | -1,7 | -129,6 | -1,6 | -61,9 | 38,14 | 0,89 / 0,95 | se contrae |
| Justicia (11) | 1,1 | -1,0 | -4,7 | -12,4 | 1,82 | 0,76 / 0,94 | mixto |
| Agricultura, Pesca y Alimentación (41) | 2,1 | 4,9 | -5,8 | 5,2 | 1,10 | 0,38 / 0,89 | mixto |
| Cultura y Deportes (33) | -10,6 | 2,7 | 4,8 | 6,6 | 0,61 | 0,36 / 0,89 | mixto |
| Educación (32) | -0,4 | -62,8 | -6,2 | -96,2 | 21,91 | 0,85 / 0,95 | se contrae |
| Administración Financiera y Tributaria (93) | 5,1 | 1,1 | -12,2 | -6,6 | 0,92 | 0,76 / 0,94 | mixto |
| Política Exterior (14) | -13,0 | 0,6 | -4,4 | -0,4 | 0,11 | 0,69 / 0,94 | se contrae |
| Infraestructuras (45) | -24,6 | -20,5 | 3,1 | 17,2 | 4,09 | 0,56 / 0,91 | mixto |
| Industria y Energía (42) | -32,7 | -0,5 | -10,2 | 3,9 | 2,45 | 0,91 / 0,95 | se contrae |
| Subvenciones al transporte (44) | -9,0 | -1,1 | -40,5 | -40,1 | 0,91 | 0,95 / 0,95 | se contrae |
| Otras actuaciones de carácter económico (49) | -53,6 | -0,3 | -3,5 | 2,7 | 0,98 | 0,51 / 0,91 | se contrae |

## 4. Consejerías (estructura actual, retroproyectada)

| Partida | Anomalía 2019 (pp) | Exceso 2019 (M€) | Anomalía 2023 (pp) | Exceso 2023 (M€) | Peso último año (%) | p / q | Patrón |
|---|---|---|---|---|---|---|---|
| DEUDA PÚBLICA (05) | 10,8 | -9,7 | 127,6 | 23,6 | 0,88 | 0,16 / 0,70 | se acentúa |
| TURISMO Y EMPLEO (16) | 29,2 | 34,2 | 6,5 | 19,6 | 2,20 | 0,02 / 0,15 | se acentúa |
| TRANSFERENCIAS A CORPORACIONES LOCALES (20) | 10,5 | 84,0 | 12,3 | 43,5 | 8,27 | 0,02 / 0,15 | se acentúa |
| UNIVERSIDADES, CIENCIA E INNOVACIÓN Y CULTURA (17) | 4,1 | -10,1 | 0,3 | -5,2 | 3,56 | 0,18 / 0,70 | se acentúa |
| BIENESTAR SOC,IGUALDAD,JUVENT.,INFANCIA Y FAMILIAS (23) | 4,5 | 57,6 | -1,4 | 14,3 | 7,03 | 0,27 / 0,73 | mixto |
| SANIDAD (14) | -1,7 | -129,7 | -1,6 | -61,9 | 38,15 | 0,89 / 0,95 | se contrae |
| AGRICULTURA,GANADERÍA,PESCA Y SOBERNÍA ALIMENTARIA (13) | 2,8 | 4,9 | -6,3 | 3,5 | 1,31 | 0,38 / 0,87 | mixto |
| CONSEJ. PRESIDENCIA, ADMONES. PÚBL.,JUSTICIA Y SEG (08) | 2,5 | 4,7 | -6,4 | -8,6 | 3,25 | 0,65 / 0,95 | mixto |
| EDUCAC.,FORMAC.PROFESIONAL,ACTIV. FÍSICA Y DEPORT (18) | -0,4 | -49,3 | -6,3 | -69,6 | 19,44 | 0,85 / 0,95 | se contrae |
| ECONOMÍA, INDUSTRIA, COMERCIO Y AUTÓNOMOS (15) | 12,1 | 5,8 | -32,4 | -15,5 | 0,78 | 0,75 / 0,95 | mixto |
| TRANSICIÓN ECOLÓGICA Y ENERGÍA (12) | -14,6 | 1,4 | -5,7 | 19,3 | 3,83 | 0,82 / 0,95 | se contrae |
| PRESIDENCIA DEL GOBIERNO (06) | -16,8 | -2,4 | -6,4 | -5,0 | 1,87 | 0,85 / 0,95 | se contrae |
| POLÍTICA TERRITORIAL, COHESIÓN TERRITORIAL Y AGUAS (09) | -12,4 | -1,8 | -14,0 | 1,6 | 0,94 | 0,75 / 0,95 | se contrae |
| OBRAS PÚBLICAS, VIVIENDA Y MOVILIDAD (11) | -24,7 | -1,1 | -8,4 | -33,5 | 4,39 | 0,65 / 0,95 | se contrae |
| HACIENDA Y RELACIONES CON LA UNIÓN EUROPEA (10) | -29,7 | -32,8 | -9,9 | -6,6 | 1,97 | 0,98 / 0,98 | se contrae |
| DIVERSAS CONSEJERÍAS (19) | -235,9 | 38,0 | 65,4 | 80,6 | 2,12 | 0,22 / 0,70 | mixto |

## 5. Subfunciones con peso ≥ 0,5 % que repiten patrón

**Se acentúan en todos los años electorales**

| Partida | Anomalía 2019 (pp) | Exceso 2019 (M€) | Anomalía 2023 (pp) | Exceso 2023 (M€) | Peso último año (%) | p / q | Patrón |
|---|---|---|---|---|---|---|---|
| Deuda Pública (951) | 10,8 | -9,7 | 127,6 | 23,6 | 0,88 | 0,16 / 0,60 | se acentúa |
| Fondo de desarrollo de Canarias (943) | 2,9 | -14,2 | 107,3 | 75,7 | 1,37 | 0,11 / 0,51 | se acentúa |
| Imprev., situac. transitorias y conting. de ejec. (929) | 41,6 | 51,5 | 23,0 | 5,7 | 1,03 | 0,22 / 0,60 | se acentúa |
| Promoción del Empleo (241) | 38,3 | 17,9 | 13,1 | 11,2 | 0,81 | 0,02 / 0,21 | se acentúa |
| Ordenación y promoción turística (432) | 19,8 | 14,3 | 6,1 | 13,1 | 1,23 | 0,04 / 0,28 | se acentúa |
| Transferencias a Corporaciones Locales (942) | 10,5 | 84,0 | 12,3 | 43,5 | 8,27 | 0,02 / 0,21 | se acentúa |
| Administración General (921) | 5,7 | 5,9 | 3,9 | 1,2 | 0,88 | 0,07 / 0,42 | se acentúa |

**Se contraen en todos los años electorales**

| Partida | Anomalía 2019 (pp) | Exceso 2019 (M€) | Anomalía 2023 (pp) | Exceso 2023 (M€) | Peso último año (%) | p / q | Patrón |
|---|---|---|---|---|---|---|---|
| Comunicaciones (491) | -85,9 | -2,4 | -2,9 | 4,6 | 0,84 | 0,56 / 0,98 | se contrae |
| Ordenación y eficiencia energética (425) | -61,2 | 0,1 | -12,4 | 6,1 | 2,40 | 0,91 / 0,98 | se contrae |
| Administración General de Economía y Hacienda (923) | -60,7 | -34,3 | -7,8 | -1,0 | 1,14 | 0,98 / 0,98 | se contrae |
| Infraestructuras del transporte terrestre (453) | -51,9 | -29,5 | -2,4 | -8,2 | 1,91 | 0,65 / 0,98 | se contrae |
| Subvenciones al transporte (441) | -9,0 | -1,1 | -40,5 | -40,1 | 0,91 | 0,95 / 0,98 | se contrae |
| Enseñanza (322) | -0,6 | -50,1 | -6,8 | -89,7 | 18,67 | 0,87 / 0,98 | se contrae |
| Hospitales, serv. asistenciales y centros de salud (312) | -1,7 | -129,7 | -1,6 | -61,8 | 38,09 | 0,87 / 0,98 | se contrae |
| Seguridad y Orden Público (132) | -1,1 | -0,8 | -0,7 | 3,7 | 0,56 | 0,53 / 0,98 | se contrae |

## 6. Programas (series continuas, peso ≥ 0,5 %) que repiten patrón

**Se acentúan**

| Partida | Anomalía 2019 (pp) | Exceso 2019 (M€) | Anomalía 2023 (pp) | Exceso 2023 (M€) | Peso último año (%) | p / q | Patrón |
|---|---|---|---|---|---|---|---|
| Amortiz y gtos fros deuda pública moneda nacional (951M) | 10,8 | -9,7 | 127,6 | 23,6 | 0,88 | 0,16 / 0,61 | se acentúa |
| Otras Transferencias a Corporaciones Locales (942D) | 64,0 | 45,5 | 6,9 | -7,4 | 0,57 | 0,16 / 0,61 | se acentúa |
| Gastos imprevistos y funciones no clasificadas (929A) | 41,6 | 51,5 | 23,0 | 5,7 | 0,59 | 0,20 / 0,63 | se acentúa |
| Fomento del Empleo (241C) | 38,3 | 17,9 | 13,1 | 11,2 | 0,78 | 0,02 / 0,24 | se acentúa |
| Prevenc. e Interv. en área del Menor y la Familia (231H) | 12,6 | 5,2 | 16,9 | 14,4 | 0,56 | 0,04 / 0,32 | se acentúa |
| Fondo Canario de Financiación Municipal (942C) | 1,6 | 19,6 | 16,6 | 30,8 | 3,91 | 0,05 / 0,35 | se acentúa |
| Transferencias a Cabildos traspaso de competencias (942A) | 6,4 | 19,0 | 7,5 | 20,0 | 3,80 | 0,02 / 0,24 | se acentúa |

**Se contraen**

| Partida | Anomalía 2019 (pp) | Exceso 2019 (M€) | Anomalía 2023 (pp) | Exceso 2023 (M€) | Peso último año (%) | p / q | Patrón |
|---|---|---|---|---|---|---|---|
| Planificación Turistíca y Sistema de Información (432H) | -67,8 | -0,3 | -41,6 | 17,1 | 0,53 | 0,62 / 0,95 | se contrae |
| Infraestruct. y Serv. de Comunicac. e Informática (491A) | -85,9 | -2,4 | -2,9 | 4,6 | 0,84 | 0,56 / 0,95 | se contrae |
| Desarrollo Energético (425A) | -61,2 | 0,1 | -12,4 | 6,1 | 2,40 | 0,91 / 0,95 | se contrae |
| Convenio de Carreteras con Ministerio de Fomento (453D) | -48,9 | -18,1 | -14,7 | -30,6 | 1,80 | 0,73 / 0,95 | se contrae |
| Fomento de la Inclusión Social (231I) | -23,1 | -2,3 | -2,0 | 7,4 | 1,09 | 0,69 / 0,95 | se contrae |
| Gestión Patrimonial y contratación pública (923B) | -8,0 | -2,0 | -8,5 | 0,1 | 0,85 | 0,96 / 0,96 | se contrae |
| Enseñanza Secundaria y Formación Profesional (322C) | -4,8 | -35,7 | -7,2 | -14,6 | 8,32 | 0,89 / 0,95 | se contrae |
| Financiación de las Universidades Canarias (322F) | -1,8 | -13,2 | -3,8 | -18,6 | 2,37 | 0,82 / 0,95 | se contrae |
| Asistencia Sanitaria (312A) | -1,7 | -129,5 | -1,6 | -61,6 | 38,09 | 0,89 / 0,95 | se contrae |

## 7. Qué vigilar en el Proyecto 2027

- Las partidas que se acentúan en todos los años electorales y tienen importe relevante (secciones 3-6): si en 2027 vuelven a crecer por encima del total y de su propia tendencia 2024-2026, el patrón se repetiría por tercera vez.
- El equilibrio entre gasto corriente y de capital: un salto del capítulo 6-7 sobre su tendencia sería la señal clásica de ciclo electoral.
- Contrastar después con la **ejecución** (liquidación de 2019 y 2023): un presupuesto inicial expansivo que no se ejecuta es anuncio, no gasto.

## 8. Limitaciones

- Dos casos electorales (tres en 2027): la permutación no puede bajar de p ≈ 0,02 y la mayoría de efectos no serán distinguibles del azar.
- 2019 y 2023 los elaboraron gobiernos distintos (CC en minoría y PSOE-NC-Podemos-ASG): un patrón común no es atribuible a un partido.
- 2023 se presupuestó con inflación alta y fondos europeos extraordinarios; 2019, en plena recuperación de ingresos.
- Deuda pública y capítulo 3 (gastos financieros): el salto de 2023 coincide con la subida de tipos de interés de 2022-2023, no con una decisión de gasto.
- Diversas Consejerías (sección 19) agrupa fondos y créditos de reserva con oscilaciones muy grandes: su anomalía no es interpretable como prioridad.
- Las elecciones autonómicas coinciden con las municipales y las insulares (mismo día de mayo): las transferencias a cabildos y ayuntamientos son el canal en el que cabría esperar un efecto electoral, pero el pipeline no puede separarlo del calendario de la financiación local.
- Presupuesto inicial, no ejecutado; programas solo con series continuas (los reestructurados quedan fuera de la sección 6).
