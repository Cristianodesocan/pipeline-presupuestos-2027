/* Pestaña «Peso»: treemap con zoom por niveles (§8.3 del diseño).
   Área = importe. Color: categoría (área de gasto / grupo / tipo de ente) o Δ peso en la ventana del gobierno actual
   (escala divergente centrada en 0). 2px de separación en el color de la superficie; etiquetas solo si caben. */
/* global d3 */
import { anchoTexto, fmt, mostrarTooltip, moverTooltip, ocultarTooltip, paleta, tintaSobre } from "./comun.js";

const ALTO_CABECERA = 20;

export function filasTreemap(datos, cfg, estado) {
  const vista = cfg.vistas ? estado.vista : cfg.vistaFija;
  return datos.treemap.filter((d) => d.dimension === cfg.treemapDim && d.vista === vista && d.anio === +estado.anio
    && d.precios === estado.precios && d.id_estable !== "__total__" && d.importe > 0
    && (!(cfg.social && estado.social === "1") || d.concepto_ced));
}

function escalaColor(filas, cfg, estado, pal) {
  if (estado.color === "delta") {
    const vals = filas.map((d) => d.delta_peso_pp_clavijo_ii).filter((v) => v != null).map(Math.abs).sort(d3.ascending);
    const m = Math.max(0.05, d3.quantile(vals, 0.95) || 0.5);
    const s = d3.scaleDiverging([-m, 0, m], d3.piecewise(d3.interpolateLab, [pal.neg, pal.mid, pal.pos])).clamp(true);
    return { tipo: "delta", m, color: (d) => (d.delta_peso_pp_clavijo_ii == null ? pal.mid : s(d.delta_peso_pp_clavijo_ii)) };
  }
  // categoría: orden fijo (no por rango), así un filtro no repinta a nadie
  const presentes = [...new Set(filas.map(cfg.categoria))];
  const orden = (cfg.orden || []).filter((c) => presentes.includes(c));
  const resto = presentes.filter((c) => !orden.includes(c))
    .sort((a, b) => d3.descending(d3.sum(filas.filter((d) => cfg.categoria(d) === a), (d) => d.importe),
      d3.sum(filas.filter((d) => cfg.categoria(d) === b), (d) => d.importe)));
  const cats = [...orden, ...resto];
  const color = new Map(cats.map((c, i) => [c, pal.series[i % pal.series.length]]));
  return { tipo: "categoria", cats, color: (d) => color.get(cfg.categoria(d)), colorDe: color };
}

export function pintarTreemap({ contenedor, leyenda, migas, datos, cfg, estado, alZoom }) {
  const pal = paleta();
  const todas = filasTreemap(datos, cfg, estado);
  const zoom = estado.zoom.slice(0, cfg.niveles.length);
  const filas = todas.filter((d) => zoom.every((z, i) => d[cfg.niveles[i]] === z));
  const nivelesRestantes = cfg.niveles.slice(zoom.length);
  const escala = escalaColor(todas, cfg, estado, pal);

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
    const p = document.createElement("p"); p.className = "cargando"; p.textContent = "Sin datos para esta combinación de filtros.";
    contenedor.append(p);
    leyenda.replaceChildren();
    return;
  }
  const ancho = Math.max(280, contenedor.clientWidth);
  const alto = Math.round(ancho < 640 ? ancho * 1.25 : Math.min(620, Math.max(380, ancho * 0.52)));

  // se muestra un nivel de grupos (con cabecera clicable) y todas las hojas que contiene
  const agrupar = nivelesRestantes.length ? d3.group(filas, (d) => d[nivelesRestantes[0]] ?? "—") : null;
  const jerarquia = agrupar
    ? d3.hierarchy({ hijos: [...agrupar].map(([k, v]) => ({ grupo: k, hijos: v })) }, (n) => n.hijos)
    : d3.hierarchy({ hijos: filas }, (n) => n.hijos);
  jerarquia.sum((n) => (n.importe != null && !n.hijos ? n.importe : 0)).sort((a, b) => b.value - a.value);
  d3.treemap().tile(d3.treemapSquarify.ratio(1.3)).size([ancho, alto]).paddingInner(2)
    .paddingTop((n) => (n.depth === 1 && n.children ? ALTO_CABECERA : 0)).round(true)(jerarquia);

  const svg = d3.select(contenedor).append("svg").attr("viewBox", `0 0 ${ancho} ${alto}`).attr("role", "img")
    .attr("aria-label", `Treemap del peso de las ${cfg.unidad} en ${estado.anio}. Usa «Ver tabla» para leer todos los valores.`);
  svg.append("rect").attr("width", ancho).attr("height", alto).attr("fill", pal.surface);

  // cabeceras de grupo (clic = ampliar)
  if (agrupar) {
    const grupos = svg.selectAll("g.grupo").data(jerarquia.children).join("g").attr("class", "grupo");
    grupos.append("rect").attr("x", (n) => n.x0).attr("y", (n) => n.y0).attr("width", (n) => n.x1 - n.x0)
      .attr("height", ALTO_CABECERA - 2).attr("rx", 4).attr("fill", pal.band);
    grupos.each(function (n) {
      const w = n.x1 - n.x0 - 8;
      const texto = `${n.data.grupo} · ${fmt.pct(100 * n.value / jerarquia.value)}`;
      const t = d3.select(this).append("text").attr("x", n.x0 + 4).attr("y", n.y0 + 13).attr("fill", pal.text)
        .style("font", "600 11.5px Inter");
      const corto = recortar(n.data.grupo, w, "600 11.5px Inter");
      if (corto) t.text(anchoTexto(texto, "600 11.5px Inter") <= w ? texto : corto);
    });
    if (nivelesRestantes.length) {
      grupos.style("cursor", "pointer").attr("tabindex", 0).attr("role", "button")
        .attr("aria-label", (n) => `Ampliar ${n.data.grupo}`)
        .on("click", (e, n) => alZoom([...zoom, n.data.grupo]))
        .on("keydown", (e, n) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); alZoom([...zoom, n.data.grupo]); } });
    }
  }

  const hojas = svg.selectAll("g.hoja").data(jerarquia.leaves()).join("g").attr("class", "hoja")
    .attr("transform", (n) => `translate(${n.x0},${n.y0})`).attr("tabindex", 0);
  hojas.append("rect").attr("width", (n) => Math.max(0, n.x1 - n.x0)).attr("height", (n) => Math.max(0, n.y1 - n.y0))
    .attr("rx", 4).attr("fill", (n) => escala.color(n.data));
  hojas.each(function (n) {
    const w = n.x1 - n.x0, h = n.y1 - n.y0, d = n.data, g = d3.select(this);
    const tinta = tintaSobre(escala.color(d));
    if (w < 46 || h < 30) return;                                  // no cabe: se queda en tooltip y tabla
    const nombre = recortar(d.etiqueta, w - 12, "600 12px Inter");
    if (!nombre) return;
    g.append("text").attr("x", 6).attr("y", 17).attr("fill", tinta).style("font", "600 12px Inter").text(nombre);
    if (h >= 46) g.append("text").attr("x", 6).attr("y", 33).attr("fill", tinta).style("font", "400 11.5px Inter")
      .style("opacity", 0.9).text(fmt.pct(d.peso_total_pct, 1));
  });
  hojas.on("pointerenter focus", function (e, n) {
    d3.select(this).select("rect").attr("stroke", pal.strong).attr("stroke-width", 2);
    const d = n.data;
    mostrarTooltip(e, d.etiqueta, [
      ["Importe", fmt.meur(d.importe)],
      ["Peso sobre el total", fmt.pct(d.peso_total_pct, 2)],
      [`Peso en ${d.nivel_2 || d.nivel_1 || "su grupo"}`, fmt.pct(d.peso_padre_pct, 1)],
      ["Var. interanual", fmt.var(d.var_pct_interanual)],
      [`Δ peso ${datos.ventanaActual.base}→${datos.ventanaActual.fin}`, fmt.pp(d.delta_peso_pp_clavijo_ii)],
      [`Var. ${datos.ventanaActual.base}→${datos.ventanaActual.fin}`, fmt.var(d.var_pct_clavijo_ii)],
    ], `${d.nivel_1 || ""}${d.nivel_2 ? " › " + d.nivel_2 : ""} · comparabilidad: ${d.comparabilidad || "—"}`);
  }).on("pointermove", moverTooltip)
    .on("pointerleave blur", function () { d3.select(this).select("rect").attr("stroke", null); ocultarTooltip(); });

  pintarLeyenda(leyenda, escala, datos, new Set(filas.map(cfg.categoria)));
}

function recortar(texto, ancho, fuente) {
  if (!texto || ancho < 20) return null;
  if (anchoTexto(texto, fuente) <= ancho) return texto;
  let s = texto;
  while (s.length > 3 && anchoTexto(s + "…", fuente) > ancho) s = s.slice(0, -1);
  return s.length > 3 ? s.trimEnd() + "…" : null;
}

function pintarLeyenda(cont, escala, datos, visibles) {
  cont.replaceChildren();
  if (escala.tipo === "categoria") {
    const cats = escala.cats.filter((c) => visibles.has(c));   // solo lo que se ve; el color no cambia al ampliar
    if (cats.length < 2) return;
    cont.className = "leyenda";
    for (const c of cats) {
      const it = document.createElement("span"); it.className = "item";
      const sw = document.createElement("span"); sw.className = "sw"; sw.style.background = escala.colorDe.get(c);
      it.append(sw, document.createTextNode(c));
      cont.append(it);
    }
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
