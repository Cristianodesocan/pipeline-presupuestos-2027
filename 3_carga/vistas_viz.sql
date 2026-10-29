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
