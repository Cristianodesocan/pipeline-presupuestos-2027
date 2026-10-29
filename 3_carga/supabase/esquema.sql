-- GENERADO por 3_carga/supabase/cargar_supabase.py --escribir-esquema a partir de modelo_bd.py
-- y vistas_viz.sql. No editar a mano: cambia el modelo y regenera.

CREATE SCHEMA IF NOT EXISTS presupuestos_cac;

CREATE TABLE IF NOT EXISTS presupuestos_cac.dim_anio (
  anio BIGINT NOT NULL,
  ipc_media DOUBLE PRECISION,
  ipc_meses BIGINT,
  ipc_estatus TEXT,
  deflactor DOUBLE PRECISION,
  deflactor_base BIGINT,
  poblacion BIGINT,
  poblacion_estatus TEXT,
  pib_nominal DOUBLE PRECISION,
  pib_estatus TEXT,
  ventana TEXT,
  presidencia TEXT,
  coalicion TEXT,
  base_comparacion BIGINT,
  ventana_actual BOOLEAN,
  fuente TEXT,
  run_id TEXT,
  cargado_en TIMESTAMPTZ,
  PRIMARY KEY (anio)
);

CREATE TABLE IF NOT EXISTS presupuestos_cac.dim_seccion (
  dimension TEXT,
  id_estable TEXT NOT NULL,
  codigo TEXT NOT NULL,
  denominacion_raw TEXT,
  denominacion_std TEXT,
  anio_desde BIGINT,
  anio_hasta BIGINT,
  anio_hasta_activo BIGINT,
  padre_codigo TEXT,
  familia_id TEXT,
  comparabilidad TEXT,
  concepto_ced TEXT,
  n_codigos_id BIGINT,
  run_id TEXT,
  cargado_en TIMESTAMPTZ,
  PRIMARY KEY (id_estable, codigo)
);

CREATE TABLE IF NOT EXISTS presupuestos_cac.dim_funcion (
  dimension TEXT,
  id_estable TEXT NOT NULL,
  codigo TEXT NOT NULL,
  denominacion_raw TEXT,
  denominacion_std TEXT,
  anio_desde BIGINT,
  anio_hasta BIGINT,
  anio_hasta_activo BIGINT,
  padre_codigo TEXT,
  familia_id TEXT,
  comparabilidad TEXT,
  concepto_ced TEXT,
  n_codigos_id BIGINT,
  run_id TEXT,
  cargado_en TIMESTAMPTZ,
  PRIMARY KEY (id_estable, codigo)
);

CREATE TABLE IF NOT EXISTS presupuestos_cac.dim_subfuncion (
  dimension TEXT,
  id_estable TEXT NOT NULL,
  codigo TEXT NOT NULL,
  denominacion_raw TEXT,
  denominacion_std TEXT,
  anio_desde BIGINT,
  anio_hasta BIGINT,
  anio_hasta_activo BIGINT,
  padre_codigo TEXT,
  familia_id TEXT,
  comparabilidad TEXT,
  concepto_ced TEXT,
  n_codigos_id BIGINT,
  run_id TEXT,
  cargado_en TIMESTAMPTZ,
  PRIMARY KEY (id_estable, codigo)
);

CREATE TABLE IF NOT EXISTS presupuestos_cac.dim_programa (
  dimension TEXT,
  id_estable TEXT NOT NULL,
  codigo TEXT NOT NULL,
  denominacion_raw TEXT,
  denominacion_std TEXT,
  anio_desde BIGINT,
  anio_hasta BIGINT,
  anio_hasta_activo BIGINT,
  padre_codigo TEXT,
  familia_id TEXT,
  comparabilidad TEXT,
  concepto_ced TEXT,
  n_codigos_id BIGINT,
  run_id TEXT,
  cargado_en TIMESTAMPTZ,
  PRIMARY KEY (id_estable, codigo)
);

CREATE TABLE IF NOT EXISTS presupuestos_cac.dim_ente (
  dimension TEXT,
  id_estable TEXT NOT NULL,
  codigo TEXT NOT NULL,
  denominacion_raw TEXT,
  denominacion_std TEXT,
  anio_desde BIGINT,
  anio_hasta BIGINT,
  anio_hasta_activo BIGINT,
  padre_codigo TEXT,
  familia_id TEXT,
  comparabilidad TEXT,
  concepto_ced TEXT,
  n_codigos_id BIGINT,
  run_id TEXT,
  cargado_en TIMESTAMPTZ,
  PRIMARY KEY (id_estable, codigo)
);

CREATE TABLE IF NOT EXISTS presupuestos_cac.fact_presupuesto (
  anio BIGINT NOT NULL,
  anio_presupuesto BIGINT NOT NULL,
  fase TEXT NOT NULL,
  serie_oficial BOOLEAN,
  dimension TEXT NOT NULL,
  tabla TEXT NOT NULL,
  codigo TEXT NOT NULL,
  codigo_unidad TEXT,
  codigo_padre TEXT,
  denominacion_raw TEXT,
  capitulo TEXT NOT NULL,
  version_importe TEXT NOT NULL,
  perimetro TEXT NOT NULL,
  importe_corriente DOUBLE PRECISION,
  importe_constante DOUBLE PRECISION,
  deflactor DOUBLE PRECISION,
  precios_base BIGINT,
  es_fondo_extraordinario BOOLEAN,
  id_estable TEXT,
  familia_id TEXT,
  id_padre TEXT,
  estatus_dato TEXT,
  estatus_constante TEXT,
  doc_id TEXT,
  pagina BIGINT,
  run_id TEXT,
  cargado_en TIMESTAMPTZ,
  PRIMARY KEY (anio, anio_presupuesto, fase, tabla, dimension, codigo, capitulo, version_importe, perimetro)
);

CREATE TABLE IF NOT EXISTS presupuestos_cac.fact_seccion_estructura (
  vista TEXT NOT NULL,
  anio BIGINT NOT NULL,
  seccion_destino TEXT NOT NULL,
  denominacion_destino TEXT,
  metodo TEXT NOT NULL,
  n_pares BIGINT,
  importe_corriente DOUBLE PRECISION,
  importe_constante DOUBLE PRECISION,
  run_id TEXT,
  cargado_en TIMESTAMPTZ,
  PRIMARY KEY (vista, anio, seccion_destino, metodo)
);

CREATE TABLE IF NOT EXISTS presupuestos_cac.xwalk (
  dimension TEXT NOT NULL,
  anio_origen BIGINT NOT NULL,
  codigo_origen TEXT NOT NULL,
  anio_destino BIGINT NOT NULL,
  codigo_destino TEXT NOT NULL,
  tipo_enlace TEXT NOT NULL,
  estado TEXT,
  estado_final TEXT,
  score DOUBLE PRECISION,
  s_importe DOUBLE PRECISION,
  s_nombre DOUBLE PRECISION,
  s_codigo DOUBLE PRECISION,
  s_grupo DOUBLE PRECISION,
  s_seccion DOUBLE PRECISION,
  denominacion_origen TEXT,
  denominacion_destino TEXT,
  inicial_origen DOUBLE PRECISION,
  ajustado_destino DOUBLE PRECISION,
  inicial_destino DOUBLE PRECISION,
  run_id TEXT,
  cargado_en TIMESTAMPTZ,
  PRIMARY KEY (dimension, anio_origen, codigo_origen, anio_destino, codigo_destino, tipo_enlace)
);

CREATE TABLE IF NOT EXISTS presupuestos_cac.fondos_extraordinarios (
  anio_presupuesto BIGINT NOT NULL,
  fase TEXT NOT NULL,
  serie_oficial BOOLEAN,
  codigo TEXT NOT NULL,
  codigo_padre TEXT,
  denominacion_raw TEXT,
  importe_corriente DOUBLE PRECISION,
  pagina BIGINT,
  run_id TEXT,
  cargado_en TIMESTAMPTZ,
  PRIMARY KEY (anio_presupuesto, fase, codigo)
);

CREATE TABLE IF NOT EXISTS presupuestos_cac.ana_metricas (
  dimension TEXT NOT NULL,
  vista TEXT NOT NULL,
  id_estable TEXT NOT NULL,
  etiqueta TEXT,
  nivel BIGINT,
  padre_id TEXT,
  padre_etiqueta TEXT,
  ruta_jerarquia TEXT,
  anio BIGINT NOT NULL,
  fase TEXT NOT NULL,
  precios TEXT NOT NULL,
  ventana TEXT NOT NULL,
  metrica TEXT NOT NULL,
  valor DOUBLE PRECISION,
  unidad TEXT,
  comparabilidad TEXT,
  estatus_dato TEXT,
  concepto_ced TEXT,
  incluye_mrr TEXT NOT NULL,
  run_id TEXT,
  cargado_en TIMESTAMPTZ,
  PRIMARY KEY (dimension, vista, id_estable, anio, fase, precios, ventana, metrica, incluye_mrr)
);

CREATE TABLE IF NOT EXISTS presupuestos_cac.carga_registro (
  run_id TEXT NOT NULL,
  tabla TEXT NOT NULL,
  destino TEXT,
  filas BIGINT, nuevas BIGINT, borradas BIGINT,
  cargado_en TIMESTAMPTZ,
  PRIMARY KEY (run_id, tabla)
);

-- Vistas de la visualización (contrato: diseno_pipeline_presupuestos_2027.md §8.2).
-- SQL común a DuckDB (local) y PostgreSQL (Supabase): una sola definición para los dos destinos.
-- presupuestos_cac se sustituye al aplicarlas. Se alimentan de ana_metricas (4_analisis): hasta que el
-- análisis se cargue, v_viz_treemap y v_viz_series están vacías; v_viz_meta ya tiene contenido.
-- Convenciones que 4_analisis debe respetar en ana_metricas:
--   ventana = 'anual' para métricas de un año; el id de la ventana (p. ej. 'clavijo_ii') para las de ventana
--   incluye_mrr = 'si' en la variante principal; 'no' en la variante sin fondos MRR/REACT-EU
--   ruta_jerarquia = etiquetas de los niveles superiores separadas por '|' (de la raíz al padre)

CREATE OR REPLACE VIEW presupuestos_cac.v_viz_treemap AS
WITH anual AS (
  SELECT dimension, vista, anio, fase, precios, id_estable, etiqueta, ruta_jerarquia, concepto_ced, comparabilidad,
         MAX(CASE WHEN metrica = 'importe' THEN valor END)        AS importe,
         MAX(CASE WHEN metrica = 'peso_total_pct' THEN valor END) AS peso_total_pct,
         MAX(CASE WHEN metrica = 'peso_padre_pct' THEN valor END) AS peso_padre_pct,
         MAX(CASE WHEN metrica = 'var_pct' THEN valor END)        AS var_pct_interanual
  FROM presupuestos_cac.ana_metricas
  WHERE ventana = 'anual' AND incluye_mrr = 'si'
  GROUP BY dimension, vista, anio, fase, precios, id_estable, etiqueta, ruta_jerarquia, concepto_ced, comparabilidad
),
ventana_actual AS (
  SELECT dimension, vista, precios, id_estable,
         MAX(CASE WHEN metrica = 'delta_peso_pp_ventana' THEN valor END) AS delta_peso_pp_clavijo_ii,
         MAX(CASE WHEN metrica = 'var_pct_ventana' THEN valor END)       AS var_pct_clavijo_ii
  FROM presupuestos_cac.ana_metricas
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

CREATE OR REPLACE VIEW presupuestos_cac.v_viz_series AS
SELECT m.dimension, m.vista, m.id_estable, m.etiqueta, m.padre_etiqueta, m.anio, m.fase, m.precios,
       MAX(CASE WHEN m.metrica = 'importe' THEN m.valor END)     AS importe,
       MAX(CASE WHEN m.metrica = 'var_abs' THEN m.valor END)     AS var_abs,
       MAX(CASE WHEN m.metrica = 'var_pct' THEN m.valor END)     AS var_pct,
       MAX(CASE WHEN m.metrica = 'indice_2015' THEN m.valor END) AS indice_2015,
       d.ventana, m.comparabilidad
FROM presupuestos_cac.ana_metricas m
LEFT JOIN presupuestos_cac.dim_anio d ON d.anio = m.anio
WHERE m.ventana = 'anual' AND m.incluye_mrr = 'si'
GROUP BY m.dimension, m.vista, m.id_estable, m.etiqueta, m.padre_etiqueta, m.anio, m.fase, m.precios,
         d.ventana, m.comparabilidad;

CREATE OR REPLACE VIEW presupuestos_cac.v_viz_meta AS
SELECT 'ventana' AS tipo, ventana AS id, MIN(anio) AS inicio, MAX(anio) AS fin,
       MAX(presidencia) || ' · ' || MAX(coalicion) AS etiqueta, CAST(NULL AS TEXT) AS valor
FROM presupuestos_cac.dim_anio
WHERE ventana IS NOT NULL
GROUP BY ventana
UNION ALL
SELECT 'serie', 'fase_ultimo_anio', MAX(anio_presupuesto), MAX(anio_presupuesto),
       'Fase del último presupuesto de la serie oficial', MAX(fase)
FROM presupuestos_cac.fact_presupuesto
WHERE serie_oficial AND anio_presupuesto = (SELECT MAX(anio_presupuesto) FROM presupuestos_cac.fact_presupuesto)
UNION ALL
SELECT 'metodologia', 'precios_base', MAX(deflactor_base), MAX(deflactor_base),
       'Año base de los euros constantes (IPC Canarias, INE)', CAST(MAX(deflactor_base) AS TEXT)
FROM presupuestos_cac.dim_anio
UNION ALL
SELECT 'carga', 'ultima_carga', CAST(NULL AS BIGINT), CAST(NULL AS BIGINT),
       'Fecha de la última carga', CAST(MAX(cargado_en) AS TEXT)
FROM presupuestos_cac.carga_registro;

-- Seguridad (Supabase)
ALTER TABLE presupuestos_cac.dim_anio ENABLE ROW LEVEL SECURITY;
ALTER TABLE presupuestos_cac.dim_seccion ENABLE ROW LEVEL SECURITY;
ALTER TABLE presupuestos_cac.dim_funcion ENABLE ROW LEVEL SECURITY;
ALTER TABLE presupuestos_cac.dim_subfuncion ENABLE ROW LEVEL SECURITY;
ALTER TABLE presupuestos_cac.dim_programa ENABLE ROW LEVEL SECURITY;
ALTER TABLE presupuestos_cac.dim_ente ENABLE ROW LEVEL SECURITY;
ALTER TABLE presupuestos_cac.fact_presupuesto ENABLE ROW LEVEL SECURITY;
ALTER TABLE presupuestos_cac.fact_seccion_estructura ENABLE ROW LEVEL SECURITY;
ALTER TABLE presupuestos_cac.xwalk ENABLE ROW LEVEL SECURITY;
ALTER TABLE presupuestos_cac.fondos_extraordinarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE presupuestos_cac.ana_metricas ENABLE ROW LEVEL SECURITY;
ALTER TABLE presupuestos_cac.carga_registro ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ALL TABLES IN SCHEMA presupuestos_cac FROM anon, authenticated;
GRANT USAGE ON SCHEMA presupuestos_cac TO anon, authenticated;
GRANT SELECT ON presupuestos_cac.v_viz_treemap TO anon, authenticated;
GRANT SELECT ON presupuestos_cac.v_viz_series TO anon, authenticated;
GRANT SELECT ON presupuestos_cac.v_viz_meta TO anon, authenticated;
