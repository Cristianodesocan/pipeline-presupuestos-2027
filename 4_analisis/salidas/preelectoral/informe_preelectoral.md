# ¿Qué suele pasar en los presupuestos preelectorales?

Generado 2026-10-30T13:07:41+00:00 por `analisis_preelectoral.py`. Serie oficial 2015-2027 (Ley; 2027: Proyecto), euros constantes de 2025. Presupuestos electorales observables: 2019, 2023, 2027.

## Resumen

**Estatus:** verificado (descripción de cifras) · cualquier lectura sobre la intención electoral es *hipótesis*.

- **Tamaño del presupuesto.** El total crece en términos reales un 7,0 % en 2019, un 7,7 % en 2023, un 2,1 % en 2027, frente a una media del 3,5 % en los demás presupuestos (permutación p = 0,18). Puesto en crecimiento real (de 12): 2019: 4.º · 2023: 3.º · 2027: 8.º.
- **Gasto corriente (caps. 1-4)**: anomalía 2019: 1,9 pp · 2023: -2,4 pp · 2027: 5,4 pp → *mixto*.
- **Gasto de capital (caps. 6-7)**: anomalía 2019: -18,3 pp · 2023: 13,0 pp · 2027: -25,9 pp → *mixto*.
- **Partidas con el mismo signo en todos los años electorales:** funciones 2 se acentúan y 3 se contraen (de 21); consejerías 3 / 4 (de 16); programas con peso ≥ 0,5 %: 6 / 4 (de 24).
- **Tras corregir por comparaciones múltiples** (q de Benjamini-Hochberg ≤ 0,10): capitulo: 0, funcion: 0, consejeria: 0, subfuncion: 0, programa: 0 partidas con acentuación y capitulo: 0, funcion: 0, consejeria: 0, subfuncion: 0, programa: 0 con contracción distinguibles del azar.

**Cómo leerlo.** Con 3 casos, una regularidad «en todos los años» puede ser casualidad: si las anomalías fueran ruido simétrico, una de cada 8 partidas tendría el mismo signo positivo en los 3 años y otra de cada 8, el negativo. El interés está en las partidas que repiten patrón **con importe relevante** y en si el patrón aparece en la naturaleza del gasto (capítulos), que es lo que predice la literatura sobre ciclos políticos presupuestarios: más gasto visible (inversión, transferencias) antes de las elecciones.

## Lo que se repite con importe relevante

Partidas (consejerías y subfunciones) con el mismo signo de anomalía en todos los años electorales y al menos 20 M€ de exceso acumulado. **«Se contrae» significa que crece menos que el total, no que se recorte.**

| Nivel | Partida | Patrón | Exceso acumulado (M€) | Anomalía media (pp) | p |
|---|---|---|---|---|---|
| consejeria | TRANSFERENCIAS A CORPORACIONES LOCALES (20) | se acentúa | 145,5 | 8,1 | 0,02 |
| subfuncion | Transferencias a Corporaciones Locales (942) | se acentúa | 145,5 | 8,1 | 0,02 |
| consejeria | DEUDA PÚBLICA (05) | se acentúa | 52,4 | 49,3 | 0,08 |
| subfuncion | Deuda Pública (951) | se acentúa | 52,4 | 49,3 | 0,08 |
| subfuncion | Promoción del Empleo (241) | se acentúa | 23,6 | 19,0 | 0,02 |
| subfuncion | Administración General de Economía y Hacienda (923) | se contrae | -53,4 | -35,0 | 0,01 |
| consejeria | HACIENDA Y RELACIONES CON LA UNIÓN EUROPEA (10) | se contrae | -62,0 | -20,7 | 0,01 |
| consejeria | TRANSICIÓN ECOLÓGICA Y ENERGÍA (12) | se contrae | -289,1 | -39,2 | 0,05 |


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
| **2027** ⚑ | 2,1 |

| Año | Var. real del total (%) | Media de los 3 previos de su legislatura (%) |
|---|---|---|
| 2019 | 7,0 | 4,9 |
| 2023 | 7,7 | 1,2 |
| 2027 | 2,1 | 4,4 |

Factor de confusión principal: la financiación autonómica (entregas a cuenta y liquidaciones) y los fondos MRR/REACT-EU, que determinan cuánto se puede presupuestar con independencia del calendario electoral.

## 2. Naturaleza económica del gasto (capítulos, tabla 2.11)

Anomalía = diferencial del año electoral frente a la media de los tres presupuestos previos de su legislatura. Exceso = euros por encima (+) o por debajo (−) de lo que habría tenido el capítulo creciendo como el total.

| Partida | Anomalía 2019 (pp) | Exceso 2019 (M€) | Anomalía 2023 (pp) | Exceso 2023 (M€) | Anomalía 2027 (pp) | Exceso 2027 (M€) | Peso último año (%) | p / q | Patrón |
|---|---|---|---|---|---|---|---|---|---|
| Cap. 3 · Gastos financieros | 11,3 | -9,1 | 124,6 | 23,6 | 8,4 | 37,8 | 1,21 | 0,08 / 0,51 | se acentúa |
| Cap. 2 · Bienes corrientes y servicios | -1,5 | -3,4 | 9,7 | 34,2 | 6,4 | 30,6 | 4,66 | 0,11 / 0,51 | mixto |
| Gasto corriente (caps. 1-4) | 1,9 | -4,6 | -2,4 | -232,0 | 5,4 | 551,8 | 87,48 | 0,20 / 0,52 | mixto |
| Cap. 4 · Transferencias corrientes | 1,3 | -3,2 | -2,1 | -155,0 | 4,9 | 372,9 | 61,27 | 0,23 / 0,52 | mixto |
| Cap. 1 · Personal | 2,9 | 11,2 | -8,0 | -134,8 | 5,9 | 110,6 | 20,34 | 0,46 / 0,81 | mixto |
| Cap. 6 · Inversiones reales | -27,9 | -29,1 | 11,5 | 86,1 | -3,9 | -74,7 | 4,80 | 0,54 / 0,81 | mixto |
| Gasto de capital (caps. 6-7) | -18,3 | 38,6 | 13,0 | 244,3 | -25,9 | -547,5 | 12,41 | 0,81 / 0,91 | mixto |
| Cap. 7 · Transferencias de capital | -18,8 | 67,7 | 13,8 | 158,2 | -37,9 | -472,7 | 7,61 | 0,77 / 0,91 | mixto |
| Cap. 8 · Activos financieros | -44,3 | -34,0 | -85,3 | -12,2 | -62,2 | -4,4 | 0,11 | 0,98 / 0,98 | se contrae |

## 3. Funciones de gasto

| Partida | Anomalía 2019 (pp) | Exceso 2019 (M€) | Anomalía 2023 (pp) | Exceso 2023 (M€) | Anomalía 2027 (pp) | Exceso 2027 (M€) | Peso último año (%) | p / q | Patrón |
|---|---|---|---|---|---|---|---|---|---|
| Deuda Pública (95) | 10,8 | -9,7 | 127,6 | 23,6 | 9,5 | 38,4 | 1,20 | 0,08 / 0,57 | se acentúa |
| Fomento del Empleo (24) | 38,3 | 17,9 | 13,1 | 11,2 | 5,7 | -5,4 | 0,77 | 0,02 / 0,48 | se acentúa |
| Investigación, desarrollo e innovación (46) | 28,2 | 2,6 | 11,6 | 11,5 | -6,7 | -10,3 | 0,68 | 0,18 / 0,78 | mixto |
| Transferencias a otras Administraciones Públicas (94) | -2,8 | 69,8 | 23,6 | 119,2 | 1,5 | 9,9 | 9,73 | 0,19 / 0,78 | mixto |
| Servicios Sociales y Promoción Social (23) | 4,3 | 56,8 | -1,0 | 15,7 | 17,6 | 144,1 | 8,27 | 0,06 / 0,57 | mixto |
| Seguridad ciudadana e instituciones penitenciarias (13) | -1,1 | -0,8 | -0,7 | 3,7 | 14,5 | 10,0 | 0,64 | 0,25 / 0,82 | mixto |
| Alta Dirección (91) | 8,5 | 6,2 | -11,6 | -9,9 | 12,8 | 17,4 | 1,03 | 0,27 / 0,82 | mixto |
| Acceso a la vivienda y fomento de la edificación (26) | 33,2 | 20,6 | -14,7 | 1,2 | -10,2 | -16,1 | 1,29 | 0,41 / 0,85 | mixto |
| Justicia (11) | 1,1 | -1,0 | -4,7 | -12,4 | 5,6 | 8,8 | 1,89 | 0,41 / 0,85 | mixto |
| Educación (32) | -0,4 | -62,8 | -6,2 | -96,2 | 6,1 | 94,7 | 22,71 | 0,52 / 0,85 | mixto |
| Sanidad (31) | -1,7 | -129,6 | -1,6 | -61,9 | 1,8 | 135,8 | 39,29 | 0,59 / 0,85 | mixto |
| Cultura y Deportes (33) | -10,6 | 2,7 | 4,8 | 6,6 | 3,9 | -1,1 | 0,60 | 0,52 / 0,85 | mixto |
| Agricultura, Pesca y Alimentación (41) | 2,1 | 4,9 | -5,8 | 5,2 | 0,7 | -10,7 | 1,01 | 0,62 / 0,85 | mixto |
| Servicios de carácter general (92) | -2,8 | 23,1 | 8,1 | 6,4 | -15,3 | -28,4 | 2,84 | 0,64 / 0,85 | mixto |
| Administración Financiera y Tributaria (93) | 5,1 | 1,1 | -12,2 | -6,6 | -5,1 | -4,9 | 0,87 | 0,81 / 0,85 | mixto |
| Subvenciones al transporte (44) | -9,0 | -1,1 | -40,5 | -40,1 | 32,7 | 29,0 | 1,16 | 0,65 / 0,85 | mixto |
| Política Exterior (14) | -13,0 | 0,6 | -4,4 | -0,4 | -4,1 | -0,2 | 0,11 | 0,72 / 0,85 | se contrae |
| Comercio, Turismo y Pymes (43) | 18,0 | 19,9 | -12,6 | -0,8 | -28,4 | -64,2 | 1,32 | 0,81 / 0,85 | mixto |
| Infraestructuras (45) | -24,6 | -20,5 | 3,1 | 17,2 | -19,8 | -113,4 | 3,13 | 0,79 / 0,85 | mixto |
| Otras actuaciones de carácter económico (49) | -53,6 | -0,3 | -3,5 | 2,7 | -3,7 | -7,3 | 0,92 | 0,68 / 0,85 | se contrae |
| Industria y Energía (42) | -32,7 | -0,5 | -10,2 | 3,9 | -122,1 | -226,1 | 0,53 | 0,98 / 0,98 | se contrae |

## 4. Consejerías (estructura actual, retroproyectada)

| Partida | Anomalía 2019 (pp) | Exceso 2019 (M€) | Anomalía 2023 (pp) | Exceso 2023 (M€) | Anomalía 2027 (pp) | Exceso 2027 (M€) | Peso último año (%) | p / q | Patrón |
|---|---|---|---|---|---|---|---|---|---|
| DEUDA PÚBLICA (05) | 10,8 | -9,7 | 127,6 | 23,6 | 9,5 | 38,4 | 1,20 | 0,08 / 0,44 | se acentúa |
| TRANSFERENCIAS A CORPORACIONES LOCALES (20) | 10,5 | 84,0 | 12,3 | 43,5 | 1,3 | 18,1 | 8,42 | 0,02 / 0,29 | se acentúa |
| BIENESTAR SOC,IGUALDAD,JUVENT.,INFANCIA Y FAMILIAS (23) | 4,4 | 57,4 | -1,4 | 14,5 | 17,8 | 144,0 | 8,25 | 0,07 / 0,44 | mixto |
| TURISMO Y EMPLEO (16) | 29,2 | 34,2 | 6,5 | 19,6 | -20,6 | -67,1 | 1,64 | 0,29 / 0,78 | mixto |
| UNIVERSIDADES, CIENCIA E INNOVACIÓN Y CULTURA (17) | 4,1 | -10,1 | 0,3 | -5,1 | 2,9 | -8,4 | 3,49 | 0,14 / 0,56 | se acentúa |
| AGRICULTURA,GANADERÍA,PESCA Y SOBERNÍA ALIMENTARIA (13) | 2,8 | 4,9 | -6,3 | 3,6 | 2,9 | -9,1 | 1,23 | 0,59 / 0,94 | mixto |
| EDUCAC.,FORMAC.PROFESIONAL,ACTIV. FÍSICA Y DEPORT (18) | -0,4 | -49,4 | -6,3 | -69,6 | 6,0 | 89,5 | 20,19 | 0,55 / 0,94 | mixto |
| SANIDAD (14) | -1,7 | -129,7 | -1,6 | -61,9 | 1,8 | 136,1 | 39,30 | 0,59 / 0,94 | mixto |
| CONSEJ. PRESIDENCIA, ADMONES. PÚBL.,JUSTICIA Y SEG (08) | 2,4 | 4,6 | -6,4 | -8,5 | 0,3 | 21,9 | 3,43 | 0,55 / 0,94 | mixto |
| ECONOMÍA, INDUSTRIA, COMERCIO Y AUTÓNOMOS (15) | 12,3 | 5,7 | -32,5 | -15,1 | -1,1 | -2,5 | 0,76 | 0,79 / 1,00 | mixto |
| PRESIDENCIA DEL GOBIERNO (06) | -16,8 | -2,4 | -6,6 | -5,3 | -1,8 | -7,7 | 1,81 | 0,90 / 1,00 | se contrae |
| OBRAS PÚBLICAS, VIVIENDA Y MOVILIDAD (11) | -24,7 | -1,1 | -8,4 | -33,5 | 7,3 | 0,4 | 4,39 | 0,67 / 0,98 | mixto |
| POLÍTICA TERRITORIAL, COHESIÓN TERRITORIAL Y AGUAS (09) | -11,5 | -1,1 | -15,9 | 0,4 | -8,0 | -15,5 | 0,86 | 0,91 / 1,00 | se contrae |
| HACIENDA Y RELACIONES CON LA UNIÓN EUROPEA (10) | -30,1 | -33,0 | -9,9 | -6,4 | -22,1 | -22,6 | 1,78 | 1,00 / 1,00 | se contrae |
| TRANSICIÓN ECOLÓGICA Y ENERGÍA (12) | -15,2 | 0,7 | -4,1 | 20,6 | -98,4 | -310,4 | 1,16 | 0,95 / 1,00 | se contrae |
| DIVERSAS CONSEJERÍAS (19) | -207,9 | 38,8 | 63,5 | 79,8 | 3,9 | -4,8 | 2,08 | 0,28 / 0,78 | mixto |

## 5. Subfunciones con peso ≥ 0,5 % que repiten patrón

**Se acentúan en todos los años electorales**

| Partida | Anomalía 2019 (pp) | Exceso 2019 (M€) | Anomalía 2023 (pp) | Exceso 2023 (M€) | Anomalía 2027 (pp) | Exceso 2027 (M€) | Peso último año (%) | p / q | Patrón |
|---|---|---|---|---|---|---|---|---|---|
| Deuda Pública (951) | 10,8 | -9,7 | 127,6 | 23,6 | 9,5 | 38,4 | 1,20 | 0,08 / 0,33 | se acentúa |
| Promoción del Empleo (241) | 38,3 | 17,9 | 13,1 | 11,2 | 5,7 | -5,4 | 0,77 | 0,02 / 0,26 | se acentúa |
| Transferencias a Corporaciones Locales (942) | 10,5 | 84,0 | 12,3 | 43,5 | 1,3 | 18,1 | 8,42 | 0,02 / 0,26 | se acentúa |
| Administración General (921) | 5,7 | 5,9 | 3,9 | 1,2 | 5,3 | -0,8 | 0,87 | 0,08 / 0,33 | se acentúa |

**Se contraen en todos los años electorales**

| Partida | Anomalía 2019 (pp) | Exceso 2019 (M€) | Anomalía 2023 (pp) | Exceso 2023 (M€) | Anomalía 2027 (pp) | Exceso 2027 (M€) | Peso último año (%) | p / q | Patrón |
|---|---|---|---|---|---|---|---|---|---|
| Administración General de Economía y Hacienda (923) | -60,7 | -34,3 | -7,8 | -1,0 | -36,5 | -18,0 | 0,99 | 1,00 / 1,00 | se contrae |
| Comunicaciones (491) | -85,9 | -2,4 | -2,9 | 4,6 | -4,2 | -6,8 | 0,78 | 0,73 / 0,88 | se contrae |

## 6. Programas (series continuas, peso ≥ 0,5 %) que repiten patrón

**Se acentúan**

| Partida | Anomalía 2019 (pp) | Exceso 2019 (M€) | Anomalía 2023 (pp) | Exceso 2023 (M€) | Anomalía 2027 (pp) | Exceso 2027 (M€) | Peso último año (%) | p / q | Patrón |
|---|---|---|---|---|---|---|---|---|---|
| Amortiz y gtos fros deuda pública moneda nacional (951M) | 10,8 | -9,7 | 127,6 | 23,6 | 9,5 | 38,4 | 1,20 | 0,08 / 0,30 | se acentúa |
| Otras Transferencias a Corporaciones Locales (942D) | 64,0 | 45,5 | 6,9 | -7,4 | 2,0 | -2,7 | 0,55 | 0,15 / 0,44 | se acentúa |
| Prevenc. e Interv. en área del Menor y la Familia (231H) | 12,6 | 5,2 | 16,9 | 14,4 | 33,1 | 12,4 | 0,66 | 0,01 / 0,11 | se acentúa |
| Fomento del Empleo (241C) | 38,3 | 17,9 | 13,1 | 11,2 | 6,8 | -5,4 | 0,73 | 0,02 / 0,14 | se acentúa |
| Enseñanzas Régimen Especial y Educación de Adultos (322K) | 5,2 | 0,7 | 8,0 | 4,7 | 15,9 | 4,9 | 0,54 | 0,02 / 0,14 | se acentúa |
| Transferencias a Cabildos traspaso de competencias (942A) | 6,4 | 19,0 | 7,5 | 20,0 | 3,3 | 16,0 | 3,93 | 0,00 / 0,11 | se acentúa |

**Se contraen**

| Partida | Anomalía 2019 (pp) | Exceso 2019 (M€) | Anomalía 2023 (pp) | Exceso 2023 (M€) | Anomalía 2027 (pp) | Exceso 2027 (M€) | Peso último año (%) | p / q | Patrón |
|---|---|---|---|---|---|---|---|---|---|
| Infraestruct. y Serv. de Comunicac. e Informática (491A) | -85,9 | -2,4 | -2,9 | 4,6 | -4,2 | -6,8 | 0,78 | 0,73 / 0,83 | se contrae |
| Gestión Patrimonial y contratación pública (923B) | -8,0 | -2,0 | -8,5 | 0,1 | -50,9 | -17,8 | 0,70 | 0,99 / 0,99 | se contrae |
| Convenio de Carreteras con Ministerio de Fomento (453D) | -48,9 | -18,1 | -14,7 | -30,6 | -1,5 | -10,7 | 1,71 | 0,76 / 0,83 | se contrae |
| Fomento de la Inclusión Social (231I) | -23,1 | -2,3 | -2,0 | 7,4 | -6,8 | -3,5 | 1,06 | 0,75 / 0,83 | se contrae |

## 7. Qué vigilar en el Proyecto 2027

- Las partidas que se acentúan en todos los años electorales y tienen importe relevante (secciones 3-6): si en 2027 vuelven a crecer por encima del total y de su propia tendencia 2024-2026, el patrón se repetiría por tercera vez.
- El equilibrio entre gasto corriente y de capital: un salto del capítulo 6-7 sobre su tendencia sería la señal clásica de ciclo electoral.
- Contrastar después con la **ejecución** (liquidación de 2019 y 2023): un presupuesto inicial expansivo que no se ejecuta es anuncio, no gasto.

## 8. Limitaciones

- 3 casos electorales: la permutación no puede bajar de p ≈ 0,005 y la mayoría de efectos no serán distinguibles del azar.
- 2019, 2023 y 2027 los elaboraron gobiernos distintos (CC en minoría, PSOE-NC-Podemos-ASG y CC-PP): un patrón común no es atribuible a un partido.
- 2023 se presupuestó con inflación alta y fondos europeos extraordinarios; 2019, en plena recuperación de ingresos.
- 2027 es el primer presupuesto casi sin fondos MRR/REACT-EU (447 M€ en 2026, 9 M€ en 2027; 316 M€ de ellos en Transición Ecológica y Energía): las consejerías que los gestionaban «se contraen» por esa salida, que no es una decisión del año electoral.
- Deuda pública y capítulo 3 (gastos financieros): el salto de 2023 coincide con la subida de tipos de interés de 2022-2023, no con una decisión de gasto.
- Diversas Consejerías (sección 19) agrupa fondos y créditos de reserva con oscilaciones muy grandes: su anomalía no es interpretable como prioridad.
- Las elecciones autonómicas coinciden con las municipales y las insulares (mismo día de mayo): las transferencias a cabildos y ayuntamientos son el canal en el que cabría esperar un efecto electoral, pero el pipeline no puede separarlo del calendario de la financiación local.
- Presupuesto inicial, no ejecutado; programas solo con series continuas (los reestructurados quedan fuera de la sección 6).
