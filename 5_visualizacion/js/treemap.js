/* Pestaña «Peso»: treemap con zoom por niveles (§8.3 del diseño).
   Área = importe. Color: categoría (función, sección, sección del programa, tipo de ente) o Δ peso en la ventana del
   gobierno actual (escala divergente centrada en 0). 2px de separación en el color de la superficie; etiquetas solo si caben.
   Señalar una celda (ratón o foco) avisa al donut de capítulos; clic la fija (o amplía, si es una función).
   En programas, la leyenda filtra: clic en una sección deja solo sus programas (y el donut y su composición los siguen). */
/* global d3 */
import {
  anchoTexto, claveCategoria, fmt, mostrarTooltip, moverTooltip, ocultarTooltip, paleta, tintaSobre, tono, varAbs, VARIAS,
} from "./comun.js";

const ALTO_CABECERA = 24;

/** Categoría (sección) por la que se filtra desde la leyenda, o null si no hay filtro o la dimensión no lo admite. */
export const filtroSeccion = (cfg, estado) => (cfg.filtroCategoria && estado.seccion) || null;
/** Nombre legible de la sección filtrada («14 · SANIDAD», «Varias secciones», «Sin sección asignada») o null. */
export function nombreFiltroSeccion(cfg, estado) {
  const sec = filtroSeccion(cfg, estado);
  return sec ? cfg.nombreCategoria(+estado.anio, estado.vista)(sec === "sin" ? null : sec) : null;
}

function filasBase(datos, cfg, estado, dim) {
  const vista = cfg.vistas ? estado.vista : cfg.vistaFija;
  const sec = filtroSeccion(cfg, estado);
  return datos.treemap.filter((d) => d.dimension === dim && d.vista === vista && d.anio === +estado.anio
    && d.precios === estado.precios && d.id_estable !== "__total__" && d.importe > 0
    && (!(cfg.social && estado.social === "1") || d.concepto_ced)
    && (!sec || claveCategoria(cfg.categoria(d)) === sec));
}

/** Nivel de zoom válido para la dimensión (capas: funciones → subfunciones; niveles: grupos de la propia tabla). */
export function zoomEfectivo(cfg, estado) {
  return estado.zoom.slice(0, cfg.capas ? cfg.capas.length - 1 : cfg.niveles.length);
}

/** Filas de la capa actual, sin aplicar el zoom de grupos (dominio de color estable al ampliar). */
export function filasTreemap(datos, cfg, estado) {
  if (!cfg.capas) return filasBase(datos, cfg, estado, cfg.treemapDim);
  const z = zoomEfectivo(cfg, estado);
  const capa = cfg.capas[z.length];
  return filasBase(datos, cfg, estado, capa.dim).filter((d) => !capa.campo || d[capa.campo] === z[z.length - 1]);
}

/** Lo que se ve en el treemap: la capa actual con el zoom aplicado. */
export function filasVisibles(datos, cfg, estado) {
  const filas = filasTreemap(datos, cfg, estado);
  if (cfg.capas) return filas;
  const z = zoomEfectivo(cfg, estado);
  return filas.filter((d) => z.every((v, i) => d[cfg.niveles[i]] === v));
}

/** Ruta de zoom que deja ver una partida lo más grande posible (la usa el buscador). */
export function rutaHasta(cfg, d) {
  if (cfg.capas) return d.dimension === cfg.capas[0].dim ? [] : [d[cfg.capas[1].campo]];
  return cfg.niveles.map((n) => d[n]).filter((v) => v != null);
}

function escalaColor(filas, cfg, estado, pal) {
  if (estado.color === "delta") {
    const vals = filas.map((d) => d.delta_peso_pp_clavijo_ii).filter((v) => v != null).map(Math.abs).sort(d3.ascending);
    const m = Math.max(0.05, d3.quantile(vals, 0.95) || 0.5);
    const s = d3.scaleDiverging([-m, 0, m], d3.piecewise(d3.interpolateLab, [pal.neg, pal.mid, pal.pos])).clamp(true);
    return { tipo: "delta", m, color: (d) => (d.delta_peso_pp_clavijo_ii == null ? pal.mid : s(d.delta_peso_pp_clavijo_ii)) };
  }
  const presentes = [...new Set(filas.map(cfg.categoria))];
  if (cfg.colorCategoria) {   // color fijo por código (sección o función): no depende de qué más haya en pantalla
    const cats = presentes.sort(cfg.ordenCategoria);
    const color = new Map(cats.map((c) => [c, cfg.colorCategoria(c, pal)]));
    return { tipo: "categoria", cats, color: (d) => color.get(cfg.categoria(d)), colorDe: color,
      nombre: cfg.nombreCategoria(+estado.anio, estado.vista) };
  }
  // tipo de ente: orden por tamaño, así un filtro no repinta a nadie
  const resto = presentes.sort((a, b) => d3.descending(d3.sum(filas.filter((d) => cfg.categoria(d) === a), (d) => d.importe),
    d3.sum(filas.filter((d) => cfg.categoria(d) === b), (d) => d.importe)));
  const color = new Map(resto.map((c, i) => [c, pal.series[i % pal.series.length]]));
  return { tipo: "categoria", cats: resto, color: (d) => color.get(cfg.categoria(d)), colorDe: color, nombre: (c) => c };
}

/* Peso de un programa en su sección: importe / suma de TODOS los programas de esa sección (la misma con la que se
   colorea y se filtra en la leyenda) en ese año, vista y precios. El denominador no depende de lo que se vea: ignora el
   zoom, «Solo gasto social» y el filtro de sección, así que un mismo programa da siempre el mismo valor y los de una
   sección suman 100 %. Los programas de «varias secciones» se miden sobre ese grupo. */
const totalesSeccion = new Map();   // "dimensión|vista|año|precios" → Map(sección → importe)
export function pesoEnSeccion(d, datos, cfg) {
  if (!cfg.filtroCategoria || d.importe == null) return null;
  const k = `${d.dimension}|${d.vista}|${d.anio}|${d.precios}`;
  if (!totalesSeccion.has(k)) {
    totalesSeccion.set(k, d3.rollup(datos.treemap.filter((x) => x.dimension === d.dimension && x.vista === d.vista
      && x.anio === d.anio && x.precios === d.precios && x.id_estable !== "__total__" && x.importe > 0),
    (l) => d3.sum(l, (x) => x.importe), cfg.categoria));
  }
  const total = totalesSeccion.get(k).get(cfg.categoria(d));
  return total > 0 ? (100 * d.importe) / total : null;
}

/** Filas del tooltip de una partida (también las usa la ficha del donut). */
export function filasDetalle(d, datos, cfg, estado) {
  const v = datos.ventanaActual;
  const filas = [["Importe", fmt.meur(d.importe)], ["Peso sobre el total", fmt.pct(d.peso_total_pct, 2)]];
  if (d.dimension !== "funcion" && d.peso_padre_pct != null) {
    filas.push([`Peso en ${d.nivel_2 || d.nivel_1 || "su grupo"}`, fmt.pct(d.peso_padre_pct, 1)]);
  }
  if (cfg.nombre === "programas") {
    // sección con la que se colorea y se filtra; si el programa se reparte, se dice qué parte gestiona la principal
    const secs = datos.seccionesDe(d.vista, d.anio, d.id_estable);
    const c = datos.seccionDe(d.vista, d.anio, d.id_estable);
    const cuota = secs.length > 1 ? secs[0].importe / d3.sum(secs, (x) => x.importe) : 1;
    if (c && c !== VARIAS) {
      filas.push(["Sección", `${c} · ${datos.nombreSeccion(c, d.anio)}${cuota < 1 ? ` (principal, ${fmt.pct(100 * cuota, 0)} de su gasto)` : ""}`]);
    } else if (c === VARIAS) filas.push(["Sección", `varias (${secs.length})`]);
    const pe = pesoEnSeccion(d, datos, cfg);
    if (pe != null) filas.push([c === VARIAS ? "Peso en «Varias secciones»" : "Peso en su sección", fmt.pct(pe, 1)]);
  }
  const va = varAbs(d);
  filas.push(["Var. interanual (€)", fmt.meurSigno(va), null, tono(va)],
    ["Var. interanual (%)", fmt.var(d.var_pct_interanual), null, tono(d.var_pct_interanual)],
    [`Δ peso ${v.base}→${v.fin}`, fmt.pp(d.delta_peso_pp_clavijo_ii), null, tono(d.delta_peso_pp_clavijo_ii)],
    [`Var. ${v.base}→${v.fin}`, fmt.var(d.var_pct_clavijo_ii), null, tono(d.var_pct_clavijo_ii)]);
  return filas;
}

export function pintarTreemap({ contenedor, leyenda, migas, datos, cfg, estado, alZoom, alSenalar, alFijar, alFiltrar }) {
  const pal = paleta();
  const zoom = zoomEfectivo(cfg, estado);
  const filas = filasVisibles(datos, cfg, estado);
  const nivelesRestantes = cfg.capas ? [] : cfg.niveles.slice(zoom.length);
  const ampliaHoja = cfg.capas && zoom.length < cfg.capas.length - 1;   // clic en una función = ver sus subfunciones
  // la escala y la leyenda se calculan sin el filtro de sección: los colores y la escala Δ no cambian al filtrar,
  // y la leyenda sigue ofreciendo las demás secciones para cambiar de una a otra
  const sec = filtroSeccion(cfg, estado);
  const sinFiltro = sec ? { ...estado, seccion: null } : estado;
  const escala = escalaColor(filasTreemap(datos, cfg, sinFiltro), cfg, estado, pal);
  const enLeyenda = new Set((sec ? filasVisibles(datos, cfg, sinFiltro) : filas).map(cfg.categoria));
  const filtro = cfg.filtroCategoria && alFiltrar ? { activa: sec, alElegir: alFiltrar } : null;
  const leyendaCompleta = () => pintarLeyenda(leyenda, escala, datos, enLeyenda, cfg, filtro);

  // migas de pan
  migas.replaceChildren();
  const raiz = document.createElement("button");
  raiz.type = "button";
  raiz.textContent = `${cfg.art === "los" ? "Todos los" : "Todas las"} ${cfg.unidad}`;
  raiz.addEventListener("click", () => alZoom([]));
  migas.append(raiz);
  zoom.forEach((z, i) => {
    const sep = document.createElement("span"); sep.textContent = "›"; migas.append(sep);
    const b = document.createElement("button"); b.type = "button"; b.textContent = z;
    b.addEventListener("click", () => alZoom(zoom.slice(0, i + 1)));
    migas.append(b);
  });

  contenedor.replaceChildren();
  if (!filas.length) {
    const p = document.createElement("p"); p.className = "cargando";
    p.textContent = sec && enLeyenda.size
      ? `${nombreFiltroSeccion(cfg, estado)} no tiene programas en esta selección: elige otra sección en la leyenda o quita el filtro.`
      : "Sin datos para esta combinación de filtros.";
    contenedor.append(p);
    if (sec && enLeyenda.size) leyendaCompleta(); else leyenda.replaceChildren();
    return;
  }
  const activar = (n) => (ampliaHoja ? alZoom([...zoom, n.data.etiqueta]) : alFijar(n.data.id_estable));

  // móvil (vertical): en un treemap estrecho la mayoría de celdas no tiene sitio para su nombre; se dibuja la misma
  // información como lista de barras ordenada, con nombre y peso en cada fila y los mismos toques (ampliar o fijar)
  if (contenedor.clientWidth < 640) {
    pintarListaMovil({ contenedor, filas, escala, estado, zoom, nivel: nivelesRestantes[0], ampliaHoja, pal,
      alGrupo: (g) => alZoom([...zoom, g]), alHoja: (d) => activar({ data: d }) });
    // la leyenda solo hace falta si el color no lo explica ya la propia fila: Δ peso, o programas (color = su sección,
    // y la leyenda sirve además de filtro); en secciones el color es el nombre de la fila y en entes, el encabezado de su grupo
    if (escala.tipo === "delta" || cfg.filtroCategoria) leyendaCompleta();
    else { leyenda.replaceChildren(); leyenda.className = ""; }
    return;
  }

  const ancho = Math.max(280, contenedor.clientWidth);
  const alto = Math.round(Math.min(580, Math.max(380, ancho * 0.48)));

  // se muestra un nivel de grupos (con cabecera clicable) y todas las hojas que contiene
  const agrupar = nivelesRestantes.length ? d3.group(filas, (d) => d[nivelesRestantes[0]] ?? "—") : null;
  const jerarquia = agrupar
    ? d3.hierarchy({ hijos: [...agrupar].map(([k, v]) => ({ grupo: k, hijos: v })) }, (n) => n.hijos)
    : d3.hierarchy({ hijos: filas }, (n) => n.hijos);
  jerarquia.sum((n) => (n.importe != null && !n.hijos ? n.importe : 0)).sort((a, b) => b.value - a.value);
  d3.treemap().tile(d3.treemapSquarify.ratio(1.3)).size([ancho, alto]).paddingInner(2)
    .paddingTop((n) => (n.depth === 1 && n.children ? ALTO_CABECERA : 0)).round(true)(jerarquia);

  const svg = d3.select(contenedor).append("svg").attr("viewBox", `0 0 ${ancho} ${alto}`).attr("role", "img")
    .attr("aria-label", `Treemap del peso de ${cfg.art} ${cfg.unidad} en ${estado.anio}. Usa «Ver tabla» para leer todos los valores.`);
  svg.append("rect").attr("width", ancho).attr("height", alto).attr("fill", pal.surface);

  // cabeceras de grupo (clic = ampliar)
  if (agrupar) {
    const grupos = svg.selectAll("g.grupo").data(jerarquia.children).join("g").attr("class", "grupo");
    grupos.append("rect").attr("x", (n) => n.x0).attr("y", (n) => n.y0).attr("width", (n) => n.x1 - n.x0)
      .attr("height", ALTO_CABECERA - 2).attr("rx", 4).attr("fill", pal.band);
    grupos.each(function (n) {
      const w = n.x1 - n.x0 - 8;
      // mismo denominador que las celdas (total de la tabla), aunque haya filtro o zoom
      const texto = `${n.data.grupo} · ${fmt.pct(d3.sum(n.leaves(), (h) => h.data.peso_total_pct))}`;
      const t = d3.select(this).append("text").attr("x", n.x0 + 4).attr("y", n.y0 + 16).attr("fill", pal.text)
        .style("font", "600 13px Inter");
      const corto = recortar(n.data.grupo, w, "600 13px Inter");
      if (corto) t.text(anchoTexto(texto, "600 13px Inter") <= w ? texto : corto);
    });
    grupos.style("cursor", "pointer").attr("tabindex", 0).attr("role", "button")
      .attr("aria-label", (n) => `Ampliar ${n.data.grupo}`)
      .on("click", (e, n) => alZoom([...zoom, n.data.grupo]))
      .on("keydown", (e, n) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); alZoom([...zoom, n.data.grupo]); } });
  }

  const hayFoco = estado.foco && filas.some((d) => d.id_estable === estado.foco);
  const hojas = svg.selectAll("g.hoja").data(jerarquia.leaves()).join("g").attr("class", "hoja")
    .attr("transform", (n) => `translate(${n.x0},${n.y0})`).attr("tabindex", 0).attr("role", "button")
    .attr("aria-label", (n) => `${n.data.etiqueta}: ${fmt.meur(n.data.importe)}, ${fmt.pct(n.data.peso_total_pct, 1)} del total. `
      + (ampliaHoja ? "Intro para ver sus subfunciones." : "Intro para fijarla en el gráfico de capítulos."))
    .style("cursor", "pointer").attr("opacity", (n) => (hayFoco && n.data.id_estable !== estado.foco ? 0.5 : 1));
  hojas.append("rect").attr("width", (n) => Math.max(0, n.x1 - n.x0)).attr("height", (n) => Math.max(0, n.y1 - n.y0))
    .attr("rx", 4).attr("fill", (n) => escala.color(n.data));
  hojas.each(function (n) {
    const w = n.x1 - n.x0, h = n.y1 - n.y0, d = n.data, g = d3.select(this);
    const tinta = tintaSobre(escala.color(d));
    if (w < 52 || h < 32) return;                                  // no cabe: se queda en tooltip y tabla
    const nombre = recortar(d.etiqueta, w - 12, "600 14px Inter");
    if (!nombre) return;
    g.append("text").attr("x", 6).attr("y", 19).attr("fill", tinta).style("font", "600 14px Inter").text(nombre);
    if (h >= 50) g.append("text").attr("x", 6).attr("y", 37).attr("fill", tinta).style("font", "400 13px Inter")
      .style("opacity", 0.9).text(fmt.pct(d.peso_total_pct, 1));
  });
  // contorno de la partida fijada: anillo de superficie + trazo fuerte, encima de todo
  if (hayFoco) {
    const n = jerarquia.leaves().find((h) => h.data.id_estable === estado.foco);
    const marco = svg.append("g").attr("pointer-events", "none").attr("transform", `translate(${n.x0},${n.y0})`);
    marco.append("rect").attr("x", -1).attr("y", -1).attr("width", n.x1 - n.x0 + 2).attr("height", n.y1 - n.y0 + 2).attr("rx", 5)
      .attr("fill", "none").attr("stroke", pal.surface).attr("stroke-width", 4);
    marco.append("rect").attr("x", 1).attr("y", 1).attr("width", Math.max(0, n.x1 - n.x0 - 2)).attr("height", Math.max(0, n.y1 - n.y0 - 2))
      .attr("rx", 4).attr("fill", "none").attr("stroke", pal.strong).attr("stroke-width", 2.5);
  }

  hojas.on("pointerenter focus", function (e, n) {
    d3.select(this).select("rect").attr("stroke", pal.strong).attr("stroke-width", 2);
    const d = n.data;
    const ruta = d.dimension === "funcion" ? "" : `${d.nivel_1 || ""}${d.nivel_2 ? " › " + d.nivel_2 : ""} · `;
    mostrarTooltip(e, d.etiqueta, filasDetalle(d, datos, cfg, estado),
      `${ruta}comparabilidad: ${d.comparabilidad || "—"} · ${ampliaHoja ? "clic: ver sus subfunciones" : "clic: fijar en capítulos"}`);
    alSenalar(d);
  }).on("pointermove", moverTooltip)
    .on("pointerleave blur", function () { d3.select(this).select("rect").attr("stroke", null); ocultarTooltip(); alSenalar(null); })
    .on("click", (e, n) => activar(n))
    .on("keydown", (e, n) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); activar(n); } });

  leyendaCompleta();
}

function recortar(texto, ancho, fuente) {
  if (!texto || ancho < 20) return null;
  if (anchoTexto(texto, fuente) <= ancho) return texto;
  let s = texto;
  while (s.length > 3 && anchoTexto(s + "…", fuente) > ancho) s = s.slice(0, -1);
  return s.length > 3 ? s.trimEnd() + "…" : null;
}

/** filtro (solo programas): { activa: clave de la sección filtrada o null, alElegir(clave) }. Con filtro, cada entrada
    de la leyenda es un botón: clic = ver solo esa sección; clic en la activa (o en «Todas las secciones») = quitarlo. */
function pintarLeyenda(cont, escala, datos, visibles, cfg, filtro) {
  cont.replaceChildren();
  cont.className = "";
  if (escala.tipo === "categoria") {
    const cats = escala.cats.filter((c) => visibles.has(c));   // solo lo que se ve; el color no cambia al ampliar
    const activa = filtro && filtro.activa;
    if (cats.length < 2 && !activa) return;
    const t = document.createElement("div"); t.className = "leyenda-t";
    t.textContent = `Color: ${cfg.colorNombre}${filtro ? (activa ? " · filtrado por una sección" : " · clic para ver solo sus programas") : ""}`;
    const l = document.createElement("div"); l.className = cats.length > 6 ? "leyenda larga" : "leyenda";
    if (filtro) { l.classList.add("filtrable"); l.setAttribute("role", "group"); l.setAttribute("aria-label", `Filtrar por ${cfg.colorNombre}`); }
    for (const c of cats) {
      const clave = claveCategoria(c);
      const it = document.createElement(filtro ? "button" : "span"); it.className = "item";
      const sw = document.createElement("span"); sw.className = "sw"; sw.style.background = escala.colorDe.get(c);
      it.append(sw, document.createTextNode(escala.nombre(c)));
      if (filtro) {
        const elegida = activa === clave;
        it.type = "button";
        it.setAttribute("aria-pressed", elegida);
        it.title = elegida ? "Quitar el filtro y ver todas las secciones" : "Ver solo los programas de esta sección";
        if (activa) it.classList.add(elegida ? "activa" : "atenuada");
        it.addEventListener("click", () => filtro.alElegir(elegida ? null : clave));
      }
      l.append(it);
    }
    if (activa) {
      const todas = Object.assign(document.createElement("button"), { type: "button", className: "item quitar",
        textContent: "× Todas las secciones" });
      todas.addEventListener("click", () => filtro.alElegir(null));
      l.append(todas);
    }
    cont.append(t, l);
    return;
  }
  const pal = paleta();
  cont.className = "escala";
  const a = document.createElement("span"); a.textContent = `Pierde ${fmt.pp(-escala.m)}`;
  const barra = document.createElement("span"); barra.className = "barra";
  barra.style.background = `linear-gradient(90deg, ${pal.neg}, ${pal.mid}, ${pal.pos})`;
  const b = document.createElement("span"); b.textContent = `Gana ${fmt.pp(escala.m)}`;
  const n = document.createElement("span");
  n.textContent = `· Cambio de peso ${datos.ventanaActual.base}→${datos.ventanaActual.fin} (gobierno actual); gris = sin dato comparable`;
  cont.append(a, barra, b, n);
}

/* ---------- versión móvil: lista de barras (misma área = importe, ahora como longitud) */
const PRIMERAS = 15;        // filas sueltas que se ven antes de «Ver las N restantes»
const MAX_AGRUPADA = 40;    // con grupos y hasta estas partidas, se ven todas bajo el encabezado de su grupo
let listaAbierta = "";      // clave de la lista que el usuario ha desplegado entera (se pliega al cambiar de vista)

/** Devuelve el modo pintado: «hojas» (partidas sueltas), «agrupada» (partidas bajo el encabezado de su grupo, como el
    treemap de escritorio) o «grupos» (una fila por grupo, si hay demasiadas partidas: p. ej. los 140 programas). */
function pintarListaMovil({ contenedor, filas, escala, estado, zoom, nivel, ampliaHoja, pal, alGrupo, alHoja }) {
  const clave = [estado.dim, estado.vista, estado.anio, estado.precios, estado.social, estado.seccion, ...zoom].join("|");
  const delta = escala.tipo === "delta";
  const colorDe = (l) => { const c = new Set(l.map((d) => escala.color(d))); return c.size === 1 ? [...c][0] : null; };
  const hoja = (d) => ({ nombre: d.etiqueta, importe: d.importe, peso: d.peso_total_pct, color: escala.color(d), d,
    foco: estado.foco === d.id_estable, ir: ampliaHoja, sub: fmt.meur(d.importe), alTocar: () => alHoja(d),
    aria: `${d.etiqueta}: ${fmt.meur(d.importe)}, ${fmt.pct(d.peso_total_pct, 1)} del total. `
      + (ampliaHoja ? "Toca para ver sus subfunciones." : "Toca para fijarla en el gráfico de capítulos.") });
  const grupos = nivel ? [...d3.group(filas, (d) => d[nivel] ?? "—")].map(([g, l]) => ({ g, l, importe: d3.sum(l, (d) => d.importe),
    peso: d3.sum(l, (d) => d.peso_total_pct), color: colorDe(l) })).sort((a, b) => b.importe - a.importe) : null;
  const modo = !nivel ? "hojas" : filas.length <= MAX_AGRUPADA ? "agrupada" : "grupos";

  const pista = document.createElement("p"); pista.className = "lista-pista";
  const ol = document.createElement("ol"); ol.className = "lista-barras";
  contenedor.append(pista, ol);

  if (modo === "agrupada") {
    pista.textContent = "Toca una partida para ver su reparto por capítulos, o un grupo para verlo solo";
    const max = d3.max(filas, (d) => d.importe) || 1;
    for (const gr of grupos) {
      const li = document.createElement("li"); li.className = "grupo-lista";
      const cab = Object.assign(document.createElement("button"), { type: "button", className: "grupo-cab" });
      cab.setAttribute("aria-label", `${gr.g}: ${gr.l.length} partidas, ${fmt.pct(gr.peso, 1)} del total. Toca para ver solo este grupo.`);
      if (gr.color && !delta) {
        const sw = document.createElement("span"); sw.className = "sw"; sw.style.background = gr.color; cab.append(sw);
      }
      cab.append(Object.assign(document.createElement("span"), { className: "gc-nombre", textContent: gr.g }),
        Object.assign(document.createElement("span"), { className: "gc-valor", textContent: `${fmt.pct(gr.peso, 1)} · ${fmt.meur(gr.importe)}` }),
        Object.assign(document.createElement("span"), { className: "gc-ir", textContent: "Ver solo ›" }));
      cab.addEventListener("click", () => alGrupo(gr.g));
      const sub = document.createElement("ol"); sub.className = "lista-barras";
      for (const d of [...gr.l].sort((a, b) => b.importe - a.importe)) sub.append(filaBarra(hoja(d), max, delta));
      li.append(cab, sub); ol.append(li);
    }
    return modo;
  }

  let items;
  if (modo === "grupos") {
    items = grupos.map((gr) => ({ nombre: gr.g, importe: gr.importe, peso: gr.peso, color: gr.color || pal.otro, ir: true,
      sub: `${gr.l.length} partidas · ${fmt.meur(gr.importe)}`, alTocar: () => alGrupo(gr.g),
      aria: `${gr.g}: ${gr.l.length} partidas, ${fmt.pct(gr.peso, 1)} del total. Toca para verlas.` }));
    pista.textContent = `Toca un grupo para ver sus partidas · ${items.length} grupos, ${filas.length} partidas`;
  } else {
    items = filas.map(hoja).sort((a, b) => b.importe - a.importe);
    pista.textContent = ampliaHoja ? "Toca una función para ver sus subfunciones" : "Toca una partida para ver su reparto por capítulos";
  }
  const max = d3.max(items, (i) => i.importe) || 1;
  const todas = listaAbierta === clave || items.length <= PRIMERAS + 3;
  for (const it of todas ? items : items.slice(0, PRIMERAS)) ol.append(filaBarra(it, max, delta));
  if (!todas) {
    const mas = Object.assign(document.createElement("button"), { type: "button", className: "btn lista-mas",
      textContent: `Ver las ${items.length - PRIMERAS} restantes (${fmt.pct(d3.sum(items.slice(PRIMERAS), (i) => i.peso), 1)} del total)` });
    mas.addEventListener("click", () => { listaAbierta = clave; contenedor.replaceChildren();
      pintarListaMovil({ contenedor, filas, escala, estado, zoom, nivel, ampliaHoja, pal, alGrupo, alHoja }); });
    contenedor.append(mas);
  }
  return modo;
}

/** Una fila de la lista: nombre y peso, importe debajo y una barra proporcional al importe (con Δ peso si toca). */
function filaBarra(it, max, delta) {
  const li = document.createElement("li");
  const b = Object.assign(document.createElement("button"), { type: "button", className: `fila-barra${it.foco ? " foco" : ""}` });
  b.setAttribute("aria-label", it.aria);
  if (it.foco) b.setAttribute("aria-pressed", "true");
  const nombre = Object.assign(document.createElement("span"), { className: "fb-nombre", textContent: it.nombre });
  const valor = Object.assign(document.createElement("span"), { className: "fb-valor", textContent: fmt.pct(it.peso, 1) });
  if (delta && it.d && it.d.delta_peso_pp_clavijo_ii != null) {
    const v = it.d.delta_peso_pp_clavijo_ii, dl = document.createElement("span");
    dl.className = `fb-delta ${tono(v) || ""}`;
    dl.textContent = `${v > 0 ? "▲" : v < 0 ? "▼" : "="} ${fmt.pp(v)}`;
    valor.append(dl);
  }
  const sub = Object.assign(document.createElement("span"), { className: "fb-sub", textContent: it.sub });
  const barra = document.createElement("span"); barra.className = "fb-barra";
  const relleno = document.createElement("i");
  relleno.style.width = `${Math.max(1.5, (100 * it.importe) / max)}%`;
  relleno.style.background = it.color;
  barra.append(relleno);
  b.append(nombre, valor, sub, barra);
  if (it.ir) {
    const ir = Object.assign(document.createElement("span"), { className: "fb-ir", textContent: "›" });
    ir.setAttribute("aria-hidden", "true"); b.append(ir);
  }
  b.addEventListener("click", it.alTocar);
  li.append(b);
  return li;
}
