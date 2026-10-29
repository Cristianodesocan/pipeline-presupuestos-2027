/* Utilidades comunes: datos, configuración por dimensión, formato es-ES, paleta y tooltip.
   Las etiquetas vienen de CSV: siempre se insertan con textContent (nunca innerHTML). */
/* global d3 */

const NUM_TREEMAP = ["anio", "importe", "peso_total_pct", "peso_padre_pct", "var_pct_interanual",
  "delta_peso_pp_clavijo_ii", "var_pct_clavijo_ii"];
const NUM_SERIES = ["anio", "importe", "var_abs", "var_pct", "indice_2015"];

function tipar(cols) {
  // No se usa d3.autoType: convertiría códigos como «05» en números.
  return (d) => {
    for (const c of cols) d[c] = d[c] === "" || d[c] == null ? null : +d[c];
    for (const k of Object.keys(d)) if (d[k] === "") d[k] = null;
    return d;
  };
}

export async function cargarDatos() {
  const [treemap, series, meta] = await Promise.all([
    d3.csv("data/viz_treemap.csv", tipar(NUM_TREEMAP)),
    d3.csv("data/viz_series.csv", tipar(NUM_SERIES)),
    d3.csv("data/viz_meta.csv", tipar(["inicio", "fin"])),
  ]);
  const vistaEstructura = [...new Set(treemap.map((d) => d.vista))].find((v) => v && v.startsWith("estructura_")) || "estructura";
  const anios = [...new Set(series.map((d) => d.anio))].sort((a, b) => a - b);
  const ventanas = meta.filter((d) => d.tipo === "ventana").sort((a, b) => a.inicio - b.inicio);
  const actual = ventanas.find((d) => d.id === "clavijo_ii") || ventanas[ventanas.length - 1];
  const ultimo = anios[anios.length - 1];
  const fases = new Map(series.map((d) => [d.anio, d.fase]));
  // área de cada función (para colorear los programas igual que las funciones)
  const areaDeFuncion = new Map(treemap.filter((d) => d.dimension === "subfuncion" && d.nivel_2).map((d) => [d.nivel_2, d.nivel_1]));
  const areas = treemap.filter((d) => d.dimension === "area" && d.id_estable !== "__total__")
    .map((d) => [d.id_estable, d.etiqueta]).filter((v, i, a) => a.findIndex((x) => x[0] === v[0]) === i)
    .sort((a, b) => d3.ascending(a[0], b[0])).map((x) => x[1]);
  return {
    treemap, series, meta, anios, ultimo, fases, ventanas, actual, areaDeFuncion, areas, vistaEstructura,
    ventanaActual: { base: actual ? actual.inicio - 1 : ultimo - 3, fin: Math.min(actual ? actual.fin : ultimo, ultimo) },
    ultimaCarga: (meta.find((d) => d.id === "ultima_carga") || {}).valor,
  };
}

/* ---------- configuración de las cuatro dimensiones (§8.3-8.4 del diseño) */
export function configDimension(dim, datos) {
  const est = datos.vistaEstructura;
  return {
    funciones: {
      nombre: "funciones", treemapDim: "subfuncion", lineasDim: "funcion", vistas: null, vistaFija: "individual",
      niveles: ["nivel_1", "nivel_2"], unidad: "subfunciones", unidadLineas: "funciones", art: "las", artLineas: "las",
      colorNombre: "área de gasto",
      categoria: (d) => d.nivel_1, orden: datos.areas, nombreNivel: ["Área", "Función"],
    },
    secciones: {
      nombre: "secciones", treemapDim: "seccion", lineasDim: "seccion",
      vistas: [["organica", "Orgánica"], [est, `Estructura ${est.split("_")[1] || ""}`.trim()]],
      niveles: ["nivel_1"], unidad: "secciones", unidadLineas: "secciones", art: "las", artLineas: "las", colorNombre: "grupo",
      categoria: (d) => d.nivel_1, orden: ["Consejerías", "Secciones no departamentales"], nombreNivel: ["Grupo"],
    },
    programas: {
      nombre: "programas", treemapDim: "programa", lineasDim: "programa",
      vistas: [["individual", "Programa"], ["familia", "Familia"]],
      niveles: ["nivel_1", "nivel_2"], unidad: "programas", unidadLineas: "programas", social: true, art: "los", artLineas: "los",
      colorNombre: "área de gasto de su función",
      categoria: (d) => datos.areaDeFuncion.get(d.nivel_1) || "Otras", orden: datos.areas, nombreNivel: ["Función", "Subfunción"],
    },
    entes: {
      nombre: "entes", treemapDim: "ente", lineasDim: "ente", vistas: null, vistaFija: "individual",
      niveles: ["nivel_1"], unidad: "entes", unidadLineas: "entes", art: "los", artLineas: "los", colorNombre: "tipo de ente",
      categoria: (d) => d.nivel_1, orden: null, nombreNivel: ["Tipo de ente"],
    },
  }[dim];
}

/* ---------- formato es-ES */
const loc = d3.formatLocale({ decimal: ",", thousands: ".", grouping: [3], currency: ["", " €"] });
const f1 = loc.format(",.1f"), f0 = loc.format(",.0f"), f2 = loc.format(",.2f");
export const fmt = {
  meur: (v) => (v == null ? "—" : `${(Math.abs(v) >= 1e8 ? f0 : f1)(v / 1e6)} M€`),
  meurEje: (v) => `${f0(v / 1e6)}`,
  pct: (v, d = 1) => (v == null ? "—" : `${(d === 2 ? f2 : f1)(v)} %`),
  pp: (v) => (v == null ? "—" : `${v > 0 ? "+" : ""}${f2(v)} pp`),
  var: (v) => (v == null ? "—" : `${v > 0 ? "+" : ""}${f1(v)} %`),
  num: (v) => (v == null ? "—" : f1(v)),
  entero: (v) => (v == null ? "—" : f0(v)),
};

/* ---------- paleta (se lee de los tokens CSS, así el modo oscuro usa sus propios pasos validados) */
export function paleta() {
  const cs = getComputedStyle(document.documentElement);
  const v = (n) => cs.getPropertyValue(n).trim();
  return {
    series: [1, 2, 3, 4, 5, 6, 7].map((i) => v(`--s${i}`)),
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

/** filas: [[clave, valor]] o [[clave, valor, colorLinea]]; título en texto plano. */
export function mostrarTooltip(evento, titulo, filas, nota) {
  const t = tip();
  t.replaceChildren();
  const h = document.createElement("div");
  h.className = "tt";
  h.textContent = titulo;
  t.append(h);
  for (const [k, v, color] of filas) {
    const f = document.createElement("div");
    f.className = "fila";
    const kk = document.createElement("span");
    kk.className = "k";
    if (color) { const i = document.createElement("i"); i.style.background = color; kk.append(i); }
    kk.append(document.createTextNode(k));
    const b = document.createElement("b");
    b.textContent = v;
    f.append(kk, b);
    t.append(f);
  }
  if (nota) { const n = document.createElement("div"); n.style.opacity = ".75"; n.style.marginTop = "4px"; n.textContent = nota; t.append(n); }
  t.hidden = false;
  moverTooltip(evento);
}

export function moverTooltip(evento) {
  const t = tip();
  let x, y;
  if (evento && evento.clientX != null && evento.type !== "focus") { x = evento.clientX; y = evento.clientY; }
  else if (evento && evento.target && evento.target.getBoundingClientRect) {
    const r = evento.target.getBoundingClientRect(); x = r.left + r.width / 2; y = r.top + 10;
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
