# Hipótesis: ¿se acentúa el gasto social en los presupuestos de años electorales?

Generado 2026-10-30T13:07:39+00:00 por `analisis_hipotesis_electoral.py`. Serie oficial 2015-2027 (Ley; 2027: Proyecto), euros constantes de 2025.

## Resumen

**Estatus:** verificado (descripción) · la atribución a la intención electoral es *hipótesis*.

Con 3 presupuestos electorales observables (2019, 2023, 2027), 6 de 9 perímetros muestran una acentuación del gasto social distinguible del resto de años (p ≤ 0,10 en la permutación exacta).

- Perímetro A (consejería de bienestar social, estructura actual): diferencial medio en años electorales 10,6 pp frente a 3,7 pp en el resto (p = 0,07).
- Perímetro B (función 23): 10,6 pp frente a 3,7 pp (p = 0,06).

**Lectura por año electoral** (diferencial real frente a los tres presupuestos previos de la misma legislatura):

- **2019**: **acentuación clara**: supera el máximo de su legislatura en 4 de 4 perímetros amplios (función 23: puesto 2 de 12 en diferencial).
- **2023**: **sin acentuación**: por debajo de la media de su legislatura en 4 de 4 perímetros amplios (función 23: puesto 9 de 12 en diferencial).
- **2027**: **acentuación clara**: supera el máximo de su legislatura en 4 de 4 perímetros amplios (función 23: puesto 1 de 12 en diferencial).

**Comparaciones múltiples.** El desglose por programas hace 5 contrastes adicionales: con un umbral de 0,10, cabe esperar alrededor de uno «significativo» por azar. Un bloque aislado a favor no basta para sostener la hipótesis.

**Advertencia de potencia.** Con 3 casos electorales frente a 9 no electorales, la permutación exacta solo puede bajar hasta p = 0,005 y el contraste detecta únicamente efectos muy grandes. Un resultado no significativo **no prueba** que el efecto no exista; un resultado significativo con 3 casos tampoco lo prueba.

## 1. Definiciones

- **Año electoral:** año de elecciones autonómicas (mayo). Su presupuesto lo diseña el gobierno saliente en otoño del año anterior: 2019 (Clavijo I), 2023 (Torres) y 2027 (Clavijo II).
- **Gasto social:** tres perímetros estables. A = lo que hoy gestiona la Consejería de Bienestar Social (sección 23) retroproyectado a todos los años; B = función 23 de la clasificación funcional; C = subfunción 231 *Acción social* y sus programas.
- **Acentuación:** que el gasto social crezca **más que el presupuesto total** ese año (diferencial, en pp) o gane peso. Se usa el diferencial y no la variación bruta porque los presupuestos electorales también suelen ser expansivos.

## 2. Contraste principal (diferencial real, euros constantes)

| Perímetro | Dif. media años electorales (pp) | Dif. media resto (pp) | Diferencia (pp) | Rango 2019 / 2023 / 2027 (de 12) | p permutación | Lectura |
|---|---|---|---|---|---|---|
| A · Consejería de bienestar social (estructura actual) | 10,6 | 3,7 | 6,9 | 2 / 9 / 1 | 0,07 | a favor |
| A' · Consejería de bienestar social, sin fondos MRR/REACT-EU | 10,4 | 3,8 | 6,6 | 2 / 10 / 1 | 0,08 | a favor |
| B · Función 23: servicios sociales y promoción social | 10,6 | 3,7 | 7,0 | 2 / 9 / 1 | 0,06 | a favor |
| C · Subfunción 231: acción social | 11,2 | 3,8 | 7,3 | 2 / 8 / 1 | 0,06 | a favor |
| C · Dependencia y mayores | 18,5 | 7,3 | 11,3 | 3 / 11 / 1 | 0,10 | a favor |
| C · Discapacidad | 3,5 | -1,0 | 4,5 | 1 / 11 / 10 | 0,25 | débil (positivo, no distinguible del azar) |
| C · Inclusión y prestaciones | -0,3 | 10,2 | -10,5 | 11 / 6 / 8 | 0,77 | en contra |
| C · Infancia, familia y menores | 12,0 | -3,4 | 15,4 | 4 / 1 / 3 | 0,02 | a favor |
| C · Planificación y coordinación | -0,6 | 4,7 | -5,4 | 8 / 6 / 10 | 0,71 | en contra |

Rango: posición del año entre los 12 presupuestos con variación calculable (1 = mayor diferencial). p: proporción de combinaciones de 3 años cuya media es ≥ la de 2019+2023+2027.

## 3. Cada año electoral frente a su propia legislatura

| Perímetro | Año | Dif. año electoral (pp) | Media de los 3 anteriores (pp) | Máximo de los 3 anteriores (pp) |
|---|---|---|---|---|
| A · Consejería de bienestar social (estructura actual) | 2019 | 12,0 | 7,6 | 10,3 |
| A · Consejería de bienestar social (estructura actual) | 2023 | 2,2 | 3,6 | 8,4 |
| A · Consejería de bienestar social (estructura actual) | 2027 | 17,7 | -0,1 | 4,8 |
| A' · Consejería de bienestar social, sin fondos MRR/REACT-EU | 2019 | 12,0 | 7,6 | 10,3 |
| A' · Consejería de bienestar social, sin fondos MRR/REACT-EU | 2023 | 0,1 | 2,3 | 8,4 |
| A' · Consejería de bienestar social, sin fondos MRR/REACT-EU | 2027 | 19,2 | 1,6 | 9,0 |
| B · Función 23: servicios sociales y promoción social | 2019 | 11,9 | 7,5 | 10,2 |
| B · Función 23: servicios sociales y promoción social | 2023 | 2,4 | 3,4 | 8,0 |
| B · Función 23: servicios sociales y promoción social | 2027 | 17,6 | 0,1 | 5,1 |
| C · Subfunción 231: acción social | 2019 | 12,8 | 8,0 | 11,4 |
| C · Subfunción 231: acción social | 2023 | 2,6 | 3,3 | 6,9 |
| C · Subfunción 231: acción social | 2027 | 18,2 | 0,2 | 5,6 |
| C · Dependencia y mayores | 2019 | 21,8 | 13,5 | 25,6 |
| C · Dependencia y mayores | 2023 | -1,5 | -0,2 | 2,0 |
| C · Dependencia y mayores | 2027 | 35,2 | 8,5 | 11,4 |
| C · Discapacidad | 2019 | 26,2 | -2,7 | -0,0 |
| C · Discapacidad | 2023 | -10,6 | 4,7 | 6,3 |
| C · Discapacidad | 2027 | -5,1 | -4,9 | -0,4 |
| C · Inclusión y prestaciones | 2019 | -3,7 | 16,8 | 47,2 |
| C · Inclusión y prestaciones | 2023 | 5,8 | 10,4 | 37,3 |
| C · Inclusión y prestaciones | 2027 | -2,9 | 3,5 | 14,1 |
| C · Infancia, familia y menores | 2019 | 6,3 | -2,1 | 3,9 |
| C · Infancia, familia y menores | 2023 | 17,5 | 3,7 | 16,3 |
| C · Infancia, familia y menores | 2027 | 12,2 | -11,6 | -6,2 |
| C · Planificación y coordinación | 2019 | 1,5 | 11,4 | 26,2 |
| C · Planificación y coordinación | 2023 | 4,0 | 15,1 | 22,3 |
| C · Planificación y coordinación | 2027 | -7,4 | -12,2 | 3,2 |


## 4. Robustez (otras medidas y precios corrientes)

| Perímetro | Precios | Medida | Electorales | Resto | p | Lectura |
|---|---|---|---|---|---|---|
| A · Consejería de bienestar social (estructura actual) | constantes | diferencial | 10,6 | 3,7 | 0,07 | a favor |
| A · Consejería de bienestar social (estructura actual) | constantes | Δ peso | 0,7 | 0,2 | 0,06 | a favor |
| A · Consejería de bienestar social (estructura actual) | constantes | variación | 16,3 | 7,2 | 0,04 | a favor |
| A · Consejería de bienestar social (estructura actual) | corrientes | diferencial | 10,9 | 3,8 | 0,07 | a favor |
| A · Consejería de bienestar social (estructura actual) | corrientes | Δ peso | 0,7 | 0,2 | 0,06 | a favor |
| A · Consejería de bienestar social (estructura actual) | corrientes | variación | 19,3 | 9,7 | 0,02 | a favor |
| A' · Consejería de bienestar social, sin fondos MRR/REACT-EU | constantes | diferencial | 10,4 | 3,8 | 0,08 | a favor |
| A' · Consejería de bienestar social, sin fondos MRR/REACT-EU | constantes | Δ peso | 0,6 | 0,2 | 0,09 | a favor |
| A' · Consejería de bienestar social, sin fondos MRR/REACT-EU | constantes | variación | 16,1 | 7,3 | 0,05 | a favor |
| A' · Consejería de bienestar social, sin fondos MRR/REACT-EU | corrientes | diferencial | 10,7 | 3,8 | 0,08 | a favor |
| A' · Consejería de bienestar social, sin fondos MRR/REACT-EU | corrientes | Δ peso | 0,6 | 0,2 | 0,09 | a favor |
| A' · Consejería de bienestar social, sin fondos MRR/REACT-EU | corrientes | variación | 19,1 | 9,8 | 0,02 | a favor |
| B · Función 23: servicios sociales y promoción social | constantes | diferencial | 10,6 | 3,7 | 0,06 | a favor |
| B · Función 23: servicios sociales y promoción social | constantes | Δ peso | 0,7 | 0,2 | 0,07 | a favor |
| B · Función 23: servicios sociales y promoción social | constantes | variación | 16,3 | 7,2 | 0,03 | a favor |
| B · Función 23: servicios sociales y promoción social | corrientes | diferencial | 10,9 | 3,7 | 0,07 | a favor |
| B · Función 23: servicios sociales y promoción social | corrientes | Δ peso | 0,7 | 0,2 | 0,07 | a favor |
| B · Función 23: servicios sociales y promoción social | corrientes | variación | 19,3 | 9,7 | 0,02 | a favor |
| C · Subfunción 231: acción social | constantes | diferencial | 11,2 | 3,8 | 0,06 | a favor |
| C · Subfunción 231: acción social | constantes | Δ peso | 0,7 | 0,2 | 0,06 | a favor |
| C · Subfunción 231: acción social | constantes | variación | 16,8 | 7,3 | 0,03 | a favor |
| C · Subfunción 231: acción social | corrientes | diferencial | 11,4 | 3,9 | 0,06 | a favor |
| C · Subfunción 231: acción social | corrientes | Δ peso | 0,7 | 0,2 | 0,06 | a favor |
| C · Subfunción 231: acción social | corrientes | variación | 19,9 | 9,8 | 0,02 | a favor |


## 5. Series anuales

### A · Consejería de bienestar social (estructura actual)

| Año | Legislatura | Importe (M€ const.) | Var. real (%) | Var. real total (%) | Diferencial (pp) | Δ peso (pp) |
|---|---|---|---|---|---|---|
| 2015 | base | 337,2 | — | — | — | — |
| 2016 | clavijo_i | 374,9 | 11,2 | 0,9 | 10,3 | 0,47 |
| 2017 | clavijo_i | 401,1 | 7,0 | 4,3 | 2,7 | 0,13 |
| 2018 | clavijo_i | 477,7 | 19,1 | 9,3 | 9,7 | 0,46 |
| **2019** ⚑ | clavijo_i | 568,2 | 19,0 | 7,0 | 12,0 | 0,63 |
| 2020 | torres | 626,7 | 10,3 | 1,9 | 8,4 | 0,51 |
| 2021 | torres | 618,1 | -1,4 | 2,3 | -3,6 | -0,24 |
| 2022 | torres | 652,8 | 5,6 | -0,5 | 6,1 | 0,40 |
| **2023** ⚑ | torres | 717,8 | 10,0 | 7,7 | 2,2 | 0,14 |
| 2024 | clavijo_ii | 730,2 | 1,7 | 7,8 | -6,0 | -0,40 |
| 2025 | clavijo_ii | 774,2 | 6,0 | 1,3 | 4,8 | 0,31 |
| 2026 | clavijo_ii | 814,7 | 5,2 | 4,3 | 1,0 | 0,06 |
| **2027** ⚑ | clavijo_ii | 976,2 | 19,8 | 2,1 | 17,7 | 1,22 |


### A' · Consejería de bienestar social, sin fondos MRR/REACT-EU

| Año | Legislatura | Importe (M€ const.) | Var. real (%) | Var. real total (%) | Diferencial (pp) | Δ peso (pp) |
|---|---|---|---|---|---|---|
| 2015 | base | 337,2 | — | — | — | — |
| 2016 | clavijo_i | 374,9 | 11,2 | 0,9 | 10,3 | 0,47 |
| 2017 | clavijo_i | 401,1 | 7,0 | 4,3 | 2,7 | 0,13 |
| 2018 | clavijo_i | 477,7 | 19,1 | 9,3 | 9,7 | 0,46 |
| **2019** ⚑ | clavijo_i | 568,2 | 19,0 | 7,0 | 12,0 | 0,63 |
| 2020 | torres | 626,7 | 10,3 | 1,9 | 8,4 | 0,51 |
| 2021 | torres | 618,1 | -1,4 | 2,3 | -3,6 | -0,24 |
| 2022 | torres | 627,5 | 1,5 | -0,5 | 2,0 | 0,13 |
| **2023** ⚑ | torres | 676,8 | 7,9 | 7,7 | 0,1 | 0,01 |
| 2024 | clavijo_ii | 688,5 | 1,7 | 7,8 | -6,1 | -0,37 |
| 2025 | clavijo_ii | 709,6 | 3,1 | 1,3 | 1,8 | 0,11 |
| 2026 | clavijo_ii | 803,6 | 13,2 | 4,3 | 9,0 | 0,55 |
| **2027** ⚑ | clavijo_ii | 975,0 | 21,3 | 2,1 | 19,2 | 1,30 |


### B · Función 23: servicios sociales y promoción social

| Año | Legislatura | Importe (M€ const.) | Var. real (%) | Var. real total (%) | Diferencial (pp) | Δ peso (pp) |
|---|---|---|---|---|---|---|
| 2015 | base | 338,2 | — | — | — | — |
| 2016 | clavijo_i | 375,8 | 11,1 | 0,9 | 10,2 | 0,46 |
| 2017 | clavijo_i | 402,0 | 7,0 | 4,3 | 2,6 | 0,13 |
| 2018 | clavijo_i | 478,8 | 19,1 | 9,3 | 9,8 | 0,46 |
| **2019** ⚑ | clavijo_i | 568,9 | 18,8 | 7,0 | 11,9 | 0,62 |
| 2020 | torres | 625,4 | 9,9 | 1,9 | 8,0 | 0,49 |
| 2021 | torres | 616,1 | -1,5 | 2,3 | -3,7 | -0,25 |
| 2022 | torres | 650,2 | 5,5 | -0,5 | 6,0 | 0,39 |
| **2023** ⚑ | torres | 716,2 | 10,1 | 7,7 | 2,4 | 0,15 |
| 2024 | clavijo_ii | 728,1 | 1,7 | 7,8 | -6,1 | -0,40 |
| 2025 | clavijo_ii | 774,5 | 6,4 | 1,3 | 5,1 | 0,33 |
| 2026 | clavijo_ii | 816,5 | 5,4 | 4,3 | 1,2 | 0,08 |
| **2027** ⚑ | clavijo_ii | 978,1 | 19,8 | 2,1 | 17,6 | 1,22 |


### C · Subfunción 231: acción social

| Año | Legislatura | Importe (M€ const.) | Var. real (%) | Var. real total (%) | Diferencial (pp) | Δ peso (pp) |
|---|---|---|---|---|---|---|
| 2015 | base | 313,9 | — | — | — | — |
| 2016 | clavijo_i | 352,5 | 12,3 | 0,9 | 11,4 | 0,48 |
| 2017 | clavijo_i | 375,3 | 6,5 | 4,3 | 2,1 | 0,10 |
| 2018 | clavijo_i | 449,9 | 19,9 | 9,3 | 10,6 | 0,46 |
| **2019** ⚑ | clavijo_i | 538,7 | 19,7 | 7,0 | 12,8 | 0,63 |
| 2020 | torres | 586,3 | 8,8 | 1,9 | 6,9 | 0,40 |
| 2021 | torres | 575,8 | -1,8 | 2,3 | -4,0 | -0,25 |
| 2022 | torres | 612,7 | 6,4 | -0,5 | 6,9 | 0,42 |
| **2023** ⚑ | torres | 675,8 | 10,3 | 7,7 | 2,6 | 0,15 |
| 2024 | clavijo_ii | 686,3 | 1,6 | 7,8 | -6,2 | -0,38 |
| 2025 | clavijo_ii | 733,6 | 6,9 | 1,3 | 5,6 | 0,35 |
| 2026 | clavijo_ii | 773,8 | 5,5 | 4,3 | 1,2 | 0,08 |
| **2027** ⚑ | clavijo_ii | 931,4 | 20,4 | 2,1 | 18,2 | 1,19 |


### C · Dependencia y mayores

| Año | Legislatura | Importe (M€ const.) | Var. real (%) | Var. real total (%) | Diferencial (pp) | Δ peso (pp) |
|---|---|---|---|---|---|---|
| 2015 | base | 121,0 | — | — | — | — |
| 2016 | clavijo_i | 131,1 | 8,4 | 0,9 | 7,5 | 0,12 |
| 2017 | clavijo_i | 146,3 | 11,6 | 4,3 | 7,3 | 0,12 |
| 2018 | clavijo_i | 197,4 | 35,0 | 9,3 | 25,6 | 0,44 |
| **2019** ⚑ | clavijo_i | 254,2 | 28,8 | 7,0 | 21,8 | 0,47 |
| 2020 | torres | 264,1 | 3,9 | 1,9 | 2,0 | 0,05 |
| 2021 | torres | 260,6 | -1,3 | 2,3 | -3,6 | -0,10 |
| 2022 | torres | 262,2 | 0,6 | -0,5 | 1,1 | 0,03 |
| **2023** ⚑ | torres | 278,6 | 6,2 | 7,7 | -1,5 | -0,04 |
| 2024 | clavijo_ii | 311,6 | 11,9 | 7,8 | 4,1 | 0,10 |
| 2025 | clavijo_ii | 351,0 | 12,6 | 1,3 | 11,4 | 0,32 |
| 2026 | clavijo_ii | 400,8 | 14,2 | 4,3 | 10,0 | 0,30 |
| **2027** ⚑ | clavijo_ii | 550,5 | 37,3 | 2,1 | 35,2 | 1,19 |


### C · Discapacidad

| Año | Legislatura | Importe (M€ const.) | Var. real (%) | Var. real total (%) | Diferencial (pp) | Δ peso (pp) |
|---|---|---|---|---|---|---|
| 2015 | base | 41,0 | — | — | — | — |
| 2016 | clavijo_i | 41,3 | 0,9 | 0,9 | -0,0 | -0,00 |
| 2017 | clavijo_i | 41,9 | 1,3 | 4,3 | -3,0 | -0,02 |
| 2018 | clavijo_i | 43,7 | 4,3 | 9,3 | -5,0 | -0,02 |
| **2019** ⚑ | clavijo_i | 58,1 | 33,1 | 7,0 | 26,2 | 0,13 |
| 2020 | torres | 62,3 | 7,2 | 1,9 | 5,3 | 0,03 |
| 2021 | torres | 67,6 | 8,6 | 2,3 | 6,3 | 0,04 |
| 2022 | torres | 69,0 | 2,0 | -0,5 | 2,5 | 0,02 |
| **2023** ⚑ | torres | 67,0 | -2,9 | 7,7 | -10,6 | -0,07 |
| 2024 | clavijo_ii | 63,6 | -5,1 | 7,8 | -12,9 | -0,08 |
| 2025 | clavijo_ii | 64,2 | 0,9 | 1,3 | -0,4 | -0,00 |
| 2026 | clavijo_ii | 65,9 | 2,7 | 4,3 | -1,6 | -0,01 |
| **2027** ⚑ | clavijo_ii | 64,0 | -2,9 | 2,1 | -5,1 | -0,03 |


### C · Inclusión y prestaciones

| Año | Legislatura | Importe (M€ const.) | Var. real (%) | Var. real total (%) | Diferencial (pp) | Δ peso (pp) |
|---|---|---|---|---|---|---|
| 2015 | base | 43,9 | — | — | — | — |
| 2016 | clavijo_i | 65,0 | 48,1 | 0,9 | 47,2 | 0,28 |
| 2017 | clavijo_i | 72,1 | 11,0 | 4,3 | 6,7 | 0,06 |
| 2018 | clavijo_i | 76,5 | 6,0 | 9,3 | -3,4 | -0,03 |
| **2019** ⚑ | clavijo_i | 78,9 | 3,2 | 7,0 | -3,7 | -0,03 |
| 2020 | torres | 109,9 | 39,2 | 1,9 | 37,3 | 0,32 |
| 2021 | torres | 66,1 | -39,9 | 2,3 | -42,1 | -0,49 |
| 2022 | torres | 89,5 | 35,5 | -0,5 | 36,0 | 0,25 |
| **2023** ⚑ | torres | 101,6 | 13,6 | 7,7 | 5,8 | 0,05 |
| 2024 | clavijo_ii | 106,4 | 4,7 | 7,8 | -3,1 | -0,03 |
| 2025 | clavijo_ii | 122,7 | 15,4 | 1,3 | 14,1 | 0,13 |
| 2026 | clavijo_ii | 127,2 | 3,7 | 4,3 | -0,6 | -0,01 |
| **2027** ⚑ | clavijo_ii | 126,2 | -0,8 | 2,1 | -2,9 | -0,03 |


### C · Infancia, familia y menores

| Año | Legislatura | Importe (M€ const.) | Var. real (%) | Var. real total (%) | Diferencial (pp) | Δ peso (pp) |
|---|---|---|---|---|---|---|
| 2015 | base | 74,2 | — | — | — | — |
| 2016 | clavijo_i | 77,8 | 4,8 | 0,9 | 3,9 | 0,04 |
| 2017 | clavijo_i | 76,6 | -1,5 | 4,3 | -5,9 | -0,06 |
| 2018 | clavijo_i | 80,4 | 4,9 | 9,3 | -4,4 | -0,04 |
| **2019** ⚑ | clavijo_i | 91,0 | 13,3 | 7,0 | 6,3 | 0,06 |
| 2020 | torres | 88,9 | -2,3 | 1,9 | -4,2 | -0,04 |
| 2021 | torres | 105,4 | 18,5 | 2,3 | 16,3 | 0,15 |
| 2022 | torres | 103,8 | -1,6 | -0,5 | -1,1 | -0,01 |
| **2023** ⚑ | torres | 129,9 | 25,2 | 7,7 | 17,5 | 0,18 |
| 2024 | clavijo_ii | 118,4 | -8,8 | 7,8 | -16,6 | -0,20 |
| 2025 | clavijo_ii | 105,6 | -10,8 | 1,3 | -12,1 | -0,13 |
| 2026 | clavijo_ii | 103,5 | -1,9 | 4,3 | -6,2 | -0,06 |
| **2027** ⚑ | clavijo_ii | 118,4 | 14,4 | 2,1 | 12,2 | 0,11 |


### C · Planificación y coordinación

| Año | Legislatura | Importe (M€ const.) | Var. real (%) | Var. real total (%) | Diferencial (pp) | Δ peso (pp) |
|---|---|---|---|---|---|---|
| 2015 | base | 33,8 | — | — | — | — |
| 2016 | clavijo_i | 37,3 | 10,3 | 0,9 | 9,4 | 0,04 |
| 2017 | clavijo_i | 38,4 | 3,0 | 4,3 | -1,4 | -0,01 |
| 2018 | clavijo_i | 52,0 | 35,5 | 9,3 | 26,2 | 0,12 |
| **2019** ⚑ | clavijo_i | 56,4 | 8,5 | 7,0 | 1,5 | 0,01 |
| 2020 | torres | 61,1 | 8,2 | 1,9 | 6,3 | 0,04 |
| 2021 | torres | 76,1 | 24,6 | 2,3 | 22,3 | 0,14 |
| 2022 | torres | 88,3 | 16,0 | -0,5 | 16,5 | 0,13 |
| **2023** ⚑ | torres | 98,7 | 11,8 | 7,7 | 4,0 | 0,03 |
| 2024 | clavijo_ii | 86,3 | -12,6 | 7,8 | -20,3 | -0,18 |
| 2025 | clavijo_ii | 90,1 | 4,4 | 1,3 | 3,2 | 0,02 |
| 2026 | clavijo_ii | 76,4 | -15,3 | 4,3 | -19,5 | -0,15 |
| **2027** ⚑ | clavijo_ii | 72,4 | -5,2 | 2,1 | -7,4 | -0,05 |


## 6. ¿Lo acentúa el Parlamento? Proyecto frente a Ley 2023

Función 23: Proyecto 682,5 → Ley 682,5 (0,0); total: 9.701,0 → 9.701,0. Las enmiendas no cambian el total; cualquier diferencia es redistribución.

## 7. Qué mirar en el Proyecto 2027

Valores de referencia para juzgar si 2027 rompe el patrón de los años no electorales (diferencial real, pp):

| Perímetro | Dif. 2024-2026 (pp) | Máximo no electoral 2016-2026 (pp) | Media + 1 DE no electoral (pp) |
|---|---|---|---|
| A · Consejería de bienestar social (estructura actual) | -6,0 · 4,8 · 1,0 | 10,3 | 9,5 |
| A' · Consejería de bienestar social, sin fondos MRR/REACT-EU | -6,1 · 1,8 · 9,0 | 10,3 | 9,8 |
| B · Función 23: servicios sociales y promoción social | -6,1 · 5,1 · 1,2 | 10,2 | 9,4 |
| C · Subfunción 231: acción social | -6,2 · 5,6 · 1,2 | 11,4 | 9,9 |

Si el diferencial de 2027 supera el máximo no electoral, habría un indicio descriptivo de acentuación; si queda dentro del rango 2024-2026, el presupuesto preelectoral seguiría la tendencia de la legislatura.

## 8. Factores de confusión

- **Dependencia:** el programa 231M crece por el calendario de la Ley de Dependencia y la financiación estatal (nivel mínimo y acordado), no solo por decisión autonómica.
- **2023:** inflación de 2022-2023 (las cifras reales la descuentan) y fondos MRR/REACT-EU (perímetro A′ los resta, solo a nivel de sección).
- **2019:** expansión general del presupuesto (+7,3 % nominal) y reorganización de 2020 (la vista estructura evita el salto orgánico).
- **Presupuesto inicial, no ejecutado:** el anuncio electoral puede estar en el presupuesto inicial y no en la liquidación; contrastar con la ejecución sería el siguiente paso.
- Ciclo político ≠ causalidad: coinciden en el tiempo la posición en la legislatura, la coyuntura económica y las transferencias del Estado.
