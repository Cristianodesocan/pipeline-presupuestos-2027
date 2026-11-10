/* Utilidades comunes: datos, configuración por dimensión, formato es-ES, paleta, capítulos y tooltip.
   Las etiquetas vienen de CSV: siempre se insertan con textContent (nunca innerHTML). */
/* global d3 */

const NUM_TREEMAP = ["anio", "importe", "peso_total_pct", "peso_padre_pct", "var_pct_interanual",
  "delta_peso_pp_clavijo_ii", "var_pct_clavijo_ii"];
const NUM_SERIES = ["anio", "importe", "var_abs", "var_pct", "indice_2015"];
/** Capítulos de gasto (clasificación económica). El 5 no existe en los presupuestos de la CAC. */
export const CAPITULOS = [
  { n: 1, nombre: "Gastos de personal",
    ayuda: "Sueldos y cotizaciones sociales del personal público: docentes, sanitarios, funcionarios, laborales y altos cargos." },
  { n: 2, nombre: "Bienes corrientes y servicios",
    ayuda: "Lo necesario para funcionar cada día: suministros, alquileres, limpieza, mantenimiento y servicios contratados o concertados." },
  { n: 3, nombre: "Gastos financieros", ayuda: "Intereses y comisiones que se pagan por la deuda pública." },
  { n: 4, nombre: "Transferencias corrientes",
    ayuda: "Dinero que se entrega sin contraprestación para gasto corriente: ayudas a familias, subvenciones y fondos para cabildos, ayuntamientos y otros entes." },
  { n: 6, nombre: "Inversiones reales", ayuda: "Obras, equipamientos y otros bienes duraderos que compra o construye la propia Administración." },
  { n: 7, nombre: "Transferencias de capital",
    ayuda: "Ayudas a otras administraciones, empresas o familias para que financien sus propias inversiones." },
  { n: 8, nombre: "Activos financieros",
    ayuda: "Préstamos, anticipos y aportaciones de capital a empresas y entes públicos, que en principio se recuperan." },
];
export const CAPITULO_9 = { n: 9, nombre: "Pasivos financieros", ayuda: "Devolución del principal de la deuda (amortización)." };
const NUM_CAPS = ["anio", "cap_1", "cap_2", "cap_3", "cap_4", "cap_6", "cap_7", "cap_8", "cap_9", "deflactor"];

/* Color por ámbito de política: el mismo hueco de la paleta ampliada (--c1…--c21) para la sección y la función
   que se corresponden (Sanidad: sección 14 y función 31; Educación: 18 y 32…). Programas = color de su sección. */
const HUECO_SECCION = { "01": 15, "05": 20, "06": 9, "08": 12, "09": 17, 10: 13, 11: 5, 12: 6, 13: 16, 14: 1, 15: 19, 16: 8,
  17: 7, 18: 2, 19: 18, 20: 3, 23: 4 };
const HUECO_FUNCION = { 11: 12, 13: 11, 14: 9, 23: 4, 24: 8, 26: 5, 31: 1, 32: 2, 33: 21, 41: 16, 42: 6, 43: 19, 44: 14,
  45: 17, 46: 7, 49: 10, 91: 15, 92: 18, 93: 13, 94: 3, 95: 20 };
export const VARIAS = "varias";
/** Un programa se colorea con su sección si esta concentra al menos este peso de su gasto; si no, «varias». */
const CUOTA_SECCION_PRINCIPAL = 0.75;

function tipar(cols) {
  // No se usa d3.autoType: convertiría códigos como «05» en números.
  return (d) => {
    for (const c of cols) d[c] = d[c] === "" || d[c] == null ? null : +d[c];
    for (const k of Object.keys(d)) if (d[k] === "") d[k] = null;
    return d;
  };
}

export const codigoSeccion = (id) => {
  const m = /^S(\d{2})_/.exec(id || "") || /^(\d{2})$/.exec(id || "");
  return m ? m[1] : null;
};
export const codigoFuncion = (id) => {
  const m = /^S?F(\d{2})/.exec(id || "");
  return m ? m[1] : null;
};
/** «SANIDAD (14)» → «SANIDAD»; «Tribunales de Justicia (112A)» → «Tribunales de Justicia». */
export const sinCodigo = (t) => (t || "").replace(/\s*\([^()]*\)\s*$/, "");

export async function cargarDatos() {
  const [treemap, series, meta, capitulos] = await Promise.all([
    d3.csv("data/viz_treemap.csv", tipar(NUM_TREEMAP)),
    d3.csv("data/viz_series.csv", tipar(NUM_SERIES)),
    d3.csv("data/viz_meta.csv", tipar(["inicio", "fin"])),
    d3.csv("data/viz_capitulos.csv", tipar(NUM_CAPS)).catch(() => []),   // opcional: sin él no hay donut
  ]);
  const vistaEstructura = [...new Set(treemap.map((d) => d.vista))].find((v) => v && v.startsWith("estructura_")) || "estructura";
  const anios = [...new Set(series.map((d) => d.anio))].sort((a, b) => a - b);
  const ventanas = meta.filter((d) => d.tipo === "ventana").sort((a, b) => a.inicio - b.inicio);
  const actual = ventanas.find((d) => d.id === "clavijo_ii") || ventanas[ventanas.length - 1];
  const ultimo = anios[anios.length - 1];
  const fases = new Map(series.map((d) => [d.anio, d.fase]));

  // nombres de sección por año y código (vista orgánica) y de la estructura del último año; nombres de función
  const nombreSeccionAnio = new Map(), nombreSeccionUlt = new Map(), nombreFuncion = new Map();
  for (const d of treemap) {
    if (d.precios !== "corrientes") continue;
    if (d.dimension === "seccion") {
      const c = codigoSeccion(d.id_estable);
      if (!c) continue;
      if (d.vista === "organica") nombreSeccionAnio.set(`${d.anio}|${c}`, sinCodigo(d.etiqueta));
      if (!nombreSeccionUlt.has(c) || d.vista !== "organica") nombreSeccionUlt.set(c, sinCodigo(d.etiqueta));
    } else if (d.dimension === "funcion" && d.id_estable !== "__total__") nombreFuncion.set(codigoFuncion(d.id_estable), d.etiqueta);
  }

  // capítulos: índice por dimensión|vista|año|id; los programas se agregan desde los pares (sección, programa)
  const caps = new Map(), seccionesPrograma = new Map();
  const sumar = (k, d, factor = 1) => {
    let o = caps.get(k);
    if (!o) { o = { deflactor: d.deflactor }; for (const c of [...CAPITULOS, CAPITULO_9]) o[c.n] = 0; caps.set(k, o); }
    for (const c of [...CAPITULOS, CAPITULO_9]) o[c.n] += (d[`cap_${c.n}`] || 0) * factor;
  };
  for (const d of capitulos) {
    if (d.dimension === "programa") {
      sumar(`programa|individual|${d.anio}|${d.id_estable}`, d);
      if (d.id_grupo) sumar(`programa|familia|${d.anio}|${d.id_grupo}`, d);
      const imp = CAPITULOS.reduce((s, c) => s + (d[`cap_${c.n}`] || 0), 0);
      for (const [vista, id] of [["individual", d.id_estable], ["familia", d.id_grupo]]) {
        if (!id) continue;
        const k = `${vista}|${d.anio}|${id}`;
        const l = seccionesPrograma.get(k) || [];
        const ya = l.find((x) => x.seccion === d.seccion);
        if (ya) ya.importe += imp; else l.push({ seccion: d.seccion, importe: imp });
        seccionesPrograma.set(k, l);
      }
    } else sumar(`${d.dimension}|${d.vista}|${d.anio}|${d.id_estable}`, d);
  }
  for (const l of seccionesPrograma.values()) l.sort((a, b) => b.importe - a.importe || d3.ascending(a.seccion, b.seccion));

  return {
    treemap, series, meta, anios, ultimo, fases, ventanas, actual, vistaEstructura,
    ventanaActual: { base: actual ? actual.inicio - 1 : ultimo - 3, fin: Math.min(actual ? actual.fin : ultimo, ultimo) },
    ultimaCarga: (meta.find((d) => d.id === "ultima_carga") || {}).valor,
    hayCapitulos: capitulos.length > 0,
    /** Capítulos de una partida: {1: €, 2: €, …, 9: €} en los precios pedidos, o null si no hay desglose. */
    capitulos(dimension, vista, anio, id, precios) {
      const o = caps.get(`${dimension}|${vista}|${anio}|${id}`);
      if (!o) return null;
      const f = precios === "constantes" ? o.deflactor || 1 : 1;
      return Object.fromEntries([...CAPITULOS, CAPITULO_9].map((c) => [c.n, o[c.n] * f]));
    },
    /** Secciones de un programa (o familia) en un año, de mayor a menor gasto: [{seccion, importe}]. */
    seccionesDe: (vista, anio, id) => seccionesPrograma.get(`${vista}|${anio}|${id}`) || [],
    /** Sección con la que se colorea el programa: la principal si concentra ≥ 75 % de su gasto; si no, «varias». */
    seccionDe(vista, anio, id) {
      const l = seccionesPrograma.get(`${vista}|${anio}|${id}`);
      if (!l || !l.length) return null;
      const total = d3.sum(l, (x) => x.importe);
      return l.length === 1 || (total > 0 && l[0].importe / total >= CUOTA_SECCION_PRINCIPAL) ? l[0].seccion : VARIAS;
    },
    nombreSeccion: (codigo, anio) => nombreSeccionAnio.get(`${anio}|${codigo}`) || nombreSeccionUlt.get(codigo) || codigo,
    nombreFuncion: (codigo) => nombreFuncion.get(codigo) || codigo,
  };
}

/* ---------- configuración de las cuatro dimensiones (§8.3-8.4 del diseño) */
const porCodigo = (a, b) => (a === VARIAS) - (b === VARIAS) || (a == null) - (b == null) || d3.ascending(a, b);

export function configDimension(dim, datos) {
  const est = datos.vistaEstructura;
  const colorSeccion = (c, pal) => (HUECO_SECCION[c] ? pal.ext[HUECO_SECCION[c] - 1] : pal.otro);
  const nombreSeccion = (anio, vista) => (c) => (c === VARIAS ? "Varias secciones" : c == null ? "Sin equivalente"
    : `${c} · ${vista === est ? datos.nombreSeccion(c, datos.ultimo) : datos.nombreSeccion(c, anio)}`);
  return {
    funciones: {
      nombre: "funciones", treemapDim: "funcion", lineasDim: "funcion", vistas: null, vistaFija: "individual",
      // raíz: las funciones (Sanidad, Educación…); al ampliar una, sus subfunciones
      capas: [{ dim: "funcion" }, { dim: "subfuncion", campo: "nivel_2" }], niveles: [],
      unidad: "funciones", unidadLineas: "funciones", art: "las", artLineas: "las", singular: "función",
      colorNombre: "función", nombreNivel: ["Función"],
      categoria: (d) => codigoFuncion(d.id_estable),
      colorCategoria: (c, pal) => (HUECO_FUNCION[c] ? pal.ext[HUECO_FUNCION[c] - 1] : pal.otro),
      nombreCategoria: () => (c) => datos.nombreFuncion(c), ordenCategoria: porCodigo,
      capDim: (d) => (d.dimension === "subfuncion" ? "subfuncion" : "funcion"),
    },
    secciones: {
      nombre: "secciones", treemapDim: "seccion", lineasDim: "seccion",
      vistas: [["organica", "Orgánica"], [est, `Estructura ${est.split("_")[1] || ""}`.trim()]],
      niveles: ["nivel_1"], unidad: "secciones", unidadLineas: "secciones", art: "las", artLineas: "las", singular: "sección",
      colorNombre: "sección", nombreNivel: ["Grupo"],
      categoria: (d) => codigoSeccion(d.id_estable), colorCategoria: colorSeccion,
      nombreCategoria: nombreSeccion, ordenCategoria: porCodigo, capDim: () => "seccion",
    },
    programas: {
      nombre: "programas", treemapDim: "programa", lineasDim: "programa",
      vistas: [["individual", "Programa"], ["familia", "Familia"]],
      niveles: ["nivel_1", "nivel_2"], unidad: "programas", unidadLineas: "programas", social: true, art: "los", artLineas: "los",
      singular: "programa", colorNombre: "sección presupuestaria", nombreNivel: ["Función", "Subfunción"],
      categoria: (d) => datos.seccionDe(d.vista, d.anio, d.id_estable), colorCategoria: colorSeccion,
      nombreCategoria: nombreSeccion, ordenCategoria: porCodigo, capDim: () => "programa",
    },
    entes: {
      nombre: "entes", treemapDim: "ente", lineasDim: "ente", vistas: null, vistaFija: "individual",
      niveles: ["nivel_1"], unidad: "entes", unidadLineas: "entes", art: "los", artLineas: "los", singular: "ente",
      colorNombre: "tipo de ente", nombreNivel: ["Tipo de ente"],
      categoria: (d) => d.nivel_1, orden: null, capDim: () => "ente",
    },
  }[dim];
}

/* ---------- formato es-ES */
const loc = d3.formatLocale({ decimal: ",", thousands: ".", grouping: [3], currency: ["", " €"] });
const f1 = loc.format(",.1f"), f0 = loc.format(",.0f"), f2 = loc.format(",.2f");
export const fmt = {
  meur: (v) => (v == null ? "—" : `${(Math.abs(v) >= 1e8 ? f0 : f1)(v / 1e6)} M€`),
  meurSigno: (v) => (v == null ? "—" : `${v > 0 ? "+" : v < 0 ? "−" : ""}${(Math.abs(v) >= 1e8 ? f0 : f1)(Math.abs(v) / 1e6)} M€`),
  meurEje: (v) => `${f0(v / 1e6)}`,
  pct: (v, d = 1) => (v == null ? "—" : `${(d === 2 ? f2 : f1)(v)} %`),
  pp: (v) => (v == null ? "—" : `${v > 0 ? "+" : ""}${f2(v)} pp`),
  var: (v) => (v == null ? "—" : `${v > 0 ? "+" : ""}${f1(v)} %`),
  num: (v) => (v == null ? "—" : f1(v)),
  entero: (v) => (v == null ? "—" : f0(v)),
};
/** Variación interanual en euros, coherente con la % publicada: importe − importe / (1 + var %). */
export const varAbs = (d) => (d.var_pct_interanual == null || d.importe == null || d.var_pct_interanual <= -100 ? null
  : d.importe - d.importe / (1 + d.var_pct_interanual / 100));
export const tono = (v) => (v == null || v === 0 ? null : v > 0 ? "pos" : "neg");

/* ---------- paleta (se lee de los tokens CSS, así el modo oscuro usa sus propios pasos validados) */
export function paleta() {
  const cs = getComputedStyle(document.documentElement);
  const v = (n) => cs.getPropertyValue(n).trim();
  return {
    series: [1, 2, 3, 4, 5, 6, 7].map((i) => v(`--s${i}`)),
    ext: d3.range(1, 22).map((i) => v(`--c${i}`)), otro: v("--c-otro"),
    neg: v("--div-neg"), mid: v("--div-mid"), pos: v("--div-pos"),
    surface: v("--surface"), grid: v("--grid"), text: v("--text"), muted: v("--text-muted"),
    strong: v("--text-strong"), band: v("--band"), bandActual: v("--band-actual"), accent: v("--accent"),
  };
}

/** Texto blanco o casi negro según la luminancia del relleno (excepción de «texto dentro de un relleno»). */
export function tintaSobre(color) {
  const c = d3.rgb(color);
  const lum = (x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; };
  const L = 0.2126 * lum(c.r) + 0.7152 * lum(c.g) + 0.0722 * lum(c.b);
  return (1.05) / (L + 0.05) > (L + 0.05) / 0.06 ? "#FFFFFF" : "#0D1B2A";
}

/* ---------- tooltip */
const tip = () => document.getElementById("tooltip");

/** filas: [clave, valor, colorLinea?, tono?] (tono «pos» / «neg» pinta el valor en verde / rojo con flecha). */
export function mostrarTooltip(evento, titulo, filas, nota) {
  const t = tip();
  t.replaceChildren();
  t.classList.remove("ayuda");
  const h = document.createElement("div");
  h.className = "tt";
  h.textContent = titulo;
  t.append(h);
  for (const [k, v, color, signo] of filas) {
    const f = document.createElement("div");
    f.className = "fila";
    const kk = document.createElement("span");
    kk.className = "k";
    if (color) { const i = document.createElement("i"); i.style.background = color; kk.append(i); }
    kk.append(document.createTextNode(k));
    const b = document.createElement("b");
    b.textContent = signo ? `${signo === "pos" ? "▲" : "▼"} ${v}` : v;
    if (signo) b.className = signo;
    f.append(kk, b);
    t.append(f);
  }
  if (nota) { const n = document.createElement("div"); n.className = "nota"; n.textContent = nota; t.append(n); }
  t.hidden = false;
  moverTooltip(evento);
}

/** Ayuda breve (filtros, capítulos): título y un párrafo. Con `ancla`, se coloca debajo del elemento y no lo tapa. */
export function mostrarAyuda(evento, titulo, texto, ancla) {
  const t = tip();
  t.replaceChildren();
  t.classList.add("ayuda");
  const h = document.createElement("div"); h.className = "tt"; h.textContent = titulo;
  const p = document.createElement("p"); p.textContent = texto;
  t.append(h, p);
  t.hidden = false;
  if (!ancla) { moverTooltip(evento); return; }
  const r = ancla.getBoundingClientRect(), w = t.offsetWidth, hh = t.offsetHeight;
  const abajo = r.bottom + 8 + hh <= window.innerHeight - 8;
  t.style.left = `${Math.max(8, Math.min(r.left, window.innerWidth - w - 8))}px`;
  t.style.top = `${abajo ? r.bottom + 8 : Math.max(8, r.top - hh - 8)}px`;
}

export function moverTooltip(evento) {
  const t = tip();
  let x, y;
  if (evento && evento.clientX != null && evento.type !== "focus" && evento.type !== "focusin") { x = evento.clientX; y = evento.clientY; }
  else if (evento && evento.target && evento.target.getBoundingClientRect) {
    const r = evento.target.getBoundingClientRect(); x = r.left + Math.min(r.width / 2, 40); y = r.bottom + 4;
  } else return;
  const w = t.offsetWidth, h = t.offsetHeight;
  const left = x + 16 + w > window.innerWidth - 8 ? x - w - 16 : x + 16;
  const top = Math.min(Math.max(8, y - h / 2), window.innerHeight - h - 8);
  t.style.left = `${Math.max(8, left)}px`;
  t.style.top = `${top}px`;
}

export function ocultarTooltip() { tip().hidden = true; }

/* ---------- tabla accesible y CSV */
export function pintarTabla(contenedor, columnas, filas) {
  contenedor.replaceChildren();
  const tabla = document.createElement("table");
  const thead = tabla.createTHead().insertRow();
  for (const c of columnas) { const th = document.createElement("th"); th.textContent = c.titulo; th.scope = "col"; thead.append(th); }
  const tb = tabla.createTBody();
  for (const f of filas) {
    const tr = tb.insertRow();
    for (const c of columnas) {
      const td = tr.insertCell();
      const v = c.valor(f);
      td.textContent = c.fmt ? c.fmt(v) : (v ?? "—");
      if (c.numero) td.className = "n" + (c.signo && v != null ? (v > 0 ? " pos" : v < 0 ? " neg" : "") : "");
    }
  }
  contenedor.append(tabla);
}

export function descargarCSV(nombre, columnas, filas) {
  const esc = (v) => { const s = v == null ? "" : String(v); return /[",;\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
  const txt = [columnas.map((c) => esc(c.titulo)).join(","), ...filas.map((f) => columnas.map((c) => esc(c.valor(f))).join(","))].join("\n");
  const url = URL.createObjectURL(new Blob(["﻿" + txt], { type: "text/csv;charset=utf-8" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: nombre });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Ancho de texto en px (para no recortar etiquetas: si no cabe, no se pinta). */
const lienzoMedida = document.createElement("canvas").getContext("2d");
export function anchoTexto(texto, fuente = "600 12px Inter") { lienzoMedida.font = fuente; return lienzoMedida.measureText(texto).width; }

/** Texto para buscar sin tildes ni mayúsculas. */
export const normalizar = (t) => (t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
