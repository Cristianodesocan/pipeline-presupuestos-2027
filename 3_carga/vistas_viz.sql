-- Vistas de la visualización (contrato: diseno_pipeline_presupuestos_2027.md §8.2).
-- SQL común a DuckDB (local) y PostgreSQL (Supabase): una sola definición para los dos destinos.
-- {esquema} se sustituye al aplicarlas. Se alimentan de ana_metricas (4_analisis): hasta que el
-- análisis se cargue, v_viz_treemap y v_viz_series están vacías; v_viz_meta ya tiene contenido.
-- Convenciones que 4_analisis debe respetar en ana_metricas:
--   ventana = 'anual' para métricas de un año; el id de la ventana (p. ej. 'clavijo_ii') para las de ventana
--   incluye_mrr = 'si' en la variante principal; 'no' en la variante sin fondos MRR/REACT-EU
--   ruta_jerarquia = etiquetas de los niveles superiores separadas por '|' (de la raíz al padre)

CREATE OR REPLACE VIEW {esquema}.v_viz_treemap AS
WITH anual AS (
  SELECT dimension, vista, anio, fase, precios, id_estable, etiqueta, ruta_jerarquia, concepto_ced, comparabilidad,
         MAX(CASE WHEN metrica = 'importe' THEN valor END)        AS importe,
         MAX(CASE WHEN metrica = 'peso_total_pct' THEN valor END) AS peso_total_pct,
         MAX(CASE WHEN metrica = 'peso_padre_pct' THEN valor END) AS peso_padre_pct,
         MAX(CASE WHEN metrica = 'var_pct' THEN valor END)        AS var_pct_interanual
  FROM {esquema}.ana_metricas
  WHERE ventana = 'anual' AND incluye_mrr = 'si'
  GROUP BY dimension, vista, anio, fase, precios, id_estable, etiqueta, ruta_jerarquia, concepto_ced, comparabilidad
),
ventana_actual AS (
  SELECT dimension, vista, precios, id_estable,
         MAX(CASE WHEN metrica = 'delta_peso_pp_ventana' THEN valor END) AS delta_peso_pp_clavijo_ii,
         MAX(CASE WHEN metrica = 'var_pct_ventana' THEN valor END)       AS var_pct_clavijo_ii
  FROM {esquema}.ana_metricas
  WHERE ventana = 'clavijo_ii' AND incluye_mrr = 'si'
  GROUP BY dimension, vista, precios, id_estable
)
SELECT a.dimension, a.vista, a.anio, a.fase, a.precios,
       NULLIF(split_part(a.ruta_jerarquia, '|', 1), '') AS nivel_1,
       NULLIF(split_part(a.ruta_jerarquia, '|', 2), '') AS nivel_2,
       NULLIF(split_part(a.ruta_jerarquia, '|', 3), '') AS nivel_3,
       a.id_estable, a.etiqueta, a.importe, a.peso_total_pct, a.peso_padre_pct, a.var_pct_interanual,
       v.delta_peso_pp_clavijo_ii, v.var_pct_clavijo_ii, a.concepto_ced, a.comparabilidad
FROM anual a
LEFT JOIN ventana_actual v
  ON v.dimension = a.dimension AND v.vista = a.vista AND v.precios = a.precios AND v.id_estable = a.id_estable;

CREATE OR REPLACE VIEW {esquema}.v_viz_series AS
SELECT m.dimension, m.vista, m.id_estable, m.etiqueta, m.padre_etiqueta, m.anio, m.fase, m.precios,
       MAX(CASE WHEN m.metrica = 'importe' THEN m.valor END)     AS importe,
       MAX(CASE WHEN m.metrica = 'var_abs' THEN m.valor END)     AS var_abs,
       MAX(CASE WHEN m.metrica = 'var_pct' THEN m.valor END)     AS var_pct,
       MAX(CASE WHEN m.metrica = 'indice_2015' THEN m.valor END) AS indice_2015,
       d.ventana, m.comparabilidad
FROM {esquema}.ana_metricas m
LEFT JOIN {esquema}.dim_anio d ON d.anio = m.anio
WHERE m.ventana = 'anual' AND m.incluye_mrr = 'si'
GROUP BY m.dimension, m.vista, m.id_estable, m.etiqueta, m.padre_etiqueta, m.anio, m.fase, m.precios,
         d.ventana, m.comparabilidad;

CREATE OR REPLACE VIEW {esquema}.v_viz_meta AS
SELECT 'ventana' AS tipo, ventana AS id, MIN(anio) AS inicio, MAX(anio) AS fin,
       MAX(presidencia) || ' · ' || MAX(coalicion) AS etiqueta, CAST(NULL AS TEXT) AS valor
FROM {esquema}.dim_anio
WHERE ventana IS NOT NULL
GROUP BY ventana
UNION ALL
SELECT 'serie', 'fase_ultimo_anio', MAX(anio_presupuesto), MAX(anio_presupuesto),
       'Fase del último presupuesto de la serie oficial', MAX(fase)
FROM {esquema}.fact_presupuesto
WHERE serie_oficial AND anio_presupuesto = (SELECT MAX(anio_presupuesto) FROM {esquema}.fact_presupuesto)
UNION ALL
SELECT 'metodologia', 'precios_base', MAX(deflactor_base), MAX(deflactor_base),
       'Año base de los euros constantes (IPC Canarias, INE)', CAST(MAX(deflactor_base) AS TEXT)
FROM {esquema}.dim_anio
UNION ALL
SELECT 'carga', 'ultima_carga', CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
       'Fecha de la última carga', CAST(MAX(cargado_en) AS TEXT)
FROM {esquema}.carga_registro;

-- Desglose por capítulos (clasificación económica) del donut de la pestaña «Peso».
-- Presupuesto inicial de la serie oficial en euros corrientes; constantes = corrientes × deflactor del año.
-- La web suma los caps. 1-8 (mismo perímetro que el treemap) y muestra el cap. 9 aparte.
--   programa / seccion          un par (sección, programa) de la tabla 2.16: la web agrega por programa (id_estable)
--                               o por familia (id_grupo) y colorea cada programa por su sección
--   seccion / organica          tabla 2.11
--   seccion / estructura_<T>    pares de 2.16 repartidos como en retroproyectar_secciones.py
--   funcion, subfuncion         tabla 2.14; la función de cada subfunción es la de ana_metricas (id_grupo)
--   ente / individual           tabla 3.2, suma de los programas de cada ente
--   ente / programa             tabla 3.2, cada programa de cada ente (programa = código del año)
-- «programa» (código del año) va en los pares y en ente / programa: con su subfunción (3 primeras cifras) la web
-- enlaza las transferencias (caps. 4 y 7) de una sección con el gasto de los entes en la misma subfunción.
CREATE OR REPLACE VIEW {esquema}.v_viz_capitulos AS
WITH cap AS (
  SELECT anio, fase, tabla, codigo_unidad, codigo_padre, id_estable, familia_id, id_padre, capitulo,
         importe_corriente, deflactor
  FROM {esquema}.fact_presupuesto
  WHERE serie_oficial AND version_importe = 'inicial' AND capitulo <> 'TOTAL'
    AND tabla IN ('secc_prog_cap', 'secciones_cap', 'subfunciones_cap', 'entes_prog_cap')
),
subfuncion_padre AS (
  SELECT DISTINCT id_estable, anio, padre_id
  FROM {esquema}.ana_metricas
  WHERE dimension = 'subfuncion' AND ventana = 'anual' AND metrica = 'importe' AND incluye_mrr = 'si'
),
filas AS (
  SELECT 'programa' AS dimension, 'seccion' AS vista, anio, fase, id_estable, familia_id AS id_grupo,
         codigo_padre AS seccion, codigo_unidad AS programa, capitulo, importe_corriente, deflactor
  FROM cap WHERE tabla = 'secc_prog_cap'
  UNION ALL
  SELECT 'seccion', 'organica', anio, fase, id_estable, CAST(NULL AS TEXT), codigo_unidad, CAST(NULL AS TEXT), capitulo,
         importe_corriente, deflactor
  FROM cap WHERE tabla = 'secciones_cap'
  UNION ALL
  SELECT 'seccion', e.vista, c.anio, c.fase, e.seccion_destino, CAST(NULL AS TEXT), e.seccion_destino, CAST(NULL AS TEXT),
         c.capitulo, c.importe_corriente * e.peso_reparto, c.deflactor
  FROM cap c
  JOIN {esquema}.fact_seccion_estructura_detalle e
    ON e.anio = c.anio AND e.seccion_origen = c.codigo_padre AND e.programa = c.codigo_unidad
  WHERE c.tabla = 'secc_prog_cap'
  UNION ALL
  SELECT 'subfuncion', 'individual', c.anio, c.fase, c.id_estable, p.padre_id, CAST(NULL AS TEXT), CAST(NULL AS TEXT),
         c.capitulo, c.importe_corriente, c.deflactor
  FROM cap c LEFT JOIN subfuncion_padre p ON p.id_estable = c.id_estable AND p.anio = c.anio
  WHERE c.tabla = 'subfunciones_cap'
  UNION ALL
  SELECT 'funcion', 'individual', c.anio, c.fase, p.padre_id, CAST(NULL AS TEXT), CAST(NULL AS TEXT), CAST(NULL AS TEXT),
         c.capitulo, c.importe_corriente, c.deflactor
  FROM cap c JOIN subfuncion_padre p ON p.id_estable = c.id_estable AND p.anio = c.anio
  WHERE c.tabla = 'subfunciones_cap'
  UNION ALL
  SELECT 'ente', 'individual', anio, fase, id_padre, CAST(NULL AS TEXT), CAST(NULL AS TEXT), CAST(NULL AS TEXT), capitulo,
         importe_corriente, deflactor
  FROM cap WHERE tabla = 'entes_prog_cap'
  UNION ALL
  SELECT 'ente', 'programa', anio, fase, id_padre, CAST(NULL AS TEXT), CAST(NULL AS TEXT), codigo_unidad, capitulo,
         importe_corriente, deflactor
  FROM cap WHERE tabla = 'entes_prog_cap'
)
SELECT dimension, vista, anio, fase, id_estable, id_grupo, seccion, programa,
       SUM(CASE WHEN capitulo = '1' THEN importe_corriente ELSE 0 END) AS cap_1,
       SUM(CASE WHEN capitulo = '2' THEN importe_corriente ELSE 0 END) AS cap_2,
       SUM(CASE WHEN capitulo = '3' THEN importe_corriente ELSE 0 END) AS cap_3,
       SUM(CASE WHEN capitulo = '4' THEN importe_corriente ELSE 0 END) AS cap_4,
       SUM(CASE WHEN capitulo = '6' THEN importe_corriente ELSE 0 END) AS cap_6,
       SUM(CASE WHEN capitulo = '7' THEN importe_corriente ELSE 0 END) AS cap_7,
       SUM(CASE WHEN capitulo = '8' THEN importe_corriente ELSE 0 END) AS cap_8,
       SUM(CASE WHEN capitulo = '9' THEN importe_corriente ELSE 0 END) AS cap_9,
       MAX(deflactor) AS deflactor
FROM filas
WHERE id_estable IS NOT NULL
GROUP BY dimension, vista, anio, fase, id_estable, id_grupo, seccion, programa
HAVING SUM(ABS(importe_corriente)) > 0;

-- Población, PIB nominal y deflactor por año (euros por habitante y % del PIB en la pestaña «Evolución»).
-- Los *_estatus indican si el dato es verificado o una estimación; sin PIB publicado, pib_nominal queda vacío.
CREATE OR REPLACE VIEW {esquema}.v_viz_anios AS
SELECT anio, deflactor, ipc_estatus, poblacion, poblacion_estatus, pib_nominal, pib_estatus, ventana
FROM {esquema}.dim_anio;
