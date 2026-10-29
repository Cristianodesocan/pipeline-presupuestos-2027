/* Pestaña «Evolución»: líneas con bandas de gobierno (§8.4 del diseño).
   Una sola escala Y. Medidas: euros, variación % interanual o índice 2015 = 100. Huecos (line.defined) donde no hay
   serie comparable; tramo discontinuo en los años en fase de Proyecto. Crosshair que se ajusta al año más cercano. */
/* global d3 */
import { anchoTexto, fmt, mostrarTooltip, ocultarTooltip, paleta } from "./comun.js";

export const MAX_SERIES = 7;
const ETIQUETA_VENTANA = { base: "Rivero", clavijo_i: "Clavijo I", torres: "Torres", clavijo_ii: "Clavijo II" };
const ETIQUETA_CORTA = { base: "R.", clavijo_i: "C. I", torres: "T.", clavijo_ii: "C. II" };

export function filasSeries(datos, cfg, estado, idsSociales) {
  const vista = cfg.vistas ? estado.vista : cfg.vistaFija;
  return datos.series.filter((d) => d.dimension === cfg.lineasDim && d.vista === vista && d.precios === estado.precios
    && d.id_estable !== "__total__" && (!(cfg.social && estado.social === "1") || idsSociales.has(d.id_estable)));
}

/** Candidatas ordenadas por importe del último año (corrientes, para que el orden no cambie con los precios). */
export function candidatas(datos, cfg, estado, idsSociales) {
  const vista = cfg.vistas ? estado.vista : cfg.vistaFija;
  const ult = d3.max(datos.series, (d) => d.anio);
  const peso = new Map();
  const etiqueta = new Map();
  for (const d of datos.series) {
    if (d.dimension !== cfg.lineasDim || d.vista !== vista || d.id_estable === "__total__") continue;
    if (cfg.social && estado.social === "1" && !idsSociales.has(d.id_estable)) continue;
    etiqueta.set(d.id_estable, d.etiqueta);
    if (d.precios === "corrientes" && d.anio === ult) peso.set(d.id_estable, d.importe || 0);
  }
  return [...etiqueta.keys()].map((id) => ({ id, etiqueta: etiqueta.get(id), peso: peso.get(id) || 0 }))
    .sort((a, b) => b.peso - a.peso);
}

export function pintarLineas({ contenedor, leyenda, datos, cfg, estado, idsSociales, seleccion }) {
  const pal = paleta();
  const filas = filasSeries(datos, cfg, estado, idsSociales);
  const anios = datos.anios;
  const medida = estado.medida;
  const series = seleccion.map((id, ranura) => {
    if (!id) return null;
    const puntos = new Map(filas.filter((d) => d.id_estable === id).map((d) => [d.anio, d]));
    const etiqueta = (puntos.values().next().value || {}).etiqueta || id;
    return { id, ranura, etiqueta, color: pal.series[ranura], valores: anios.map((a) => ({ anio: a, fila: puntos.get(a) || null,
      v: puntos.get(a) ? puntos.get(a)[medida] : null, fase: datos.fases.get(a) })),
      familia: [...puntos.values()].some((d) => d.comparabilidad === "familia") };
  }).filter(Boolean);

  contenedor.replaceChildren();
  leyenda.replaceChildren();
  if (!series.length) {
    const p = document.createElement("p"); p.className = "cargando"; p.textContent = "Añade alguna partida con el buscador.";
    contenedor.append(p); return;
  }
  // La leyenda son los chips del selector (clave de línea + nombre en tinta de texto, siempre visibles);
  // aquí solo se explica el símbolo de las series agregadas por familia, si hay alguna.
  if (series.some((s) => s.familia)) leyenda.textContent = "◆ = serie agregada por familia de programas (incluye divisiones o fusiones)";

  const ancho = Math.max(300, contenedor.clientWidth);
  const estrecho = ancho < 640;
  const etiquetasFinales = !estrecho && series.length <= 4;
  const m = { t: 30, r: etiquetasFinales ? 170 : 18, b: 30, l: medida === "importe" ? 64 : 48 };
  const alto = estrecho ? 320 : 420;
  const x = d3.scaleLinear([anios[0], anios[anios.length - 1]], [m.l, ancho - m.r]);
  const todos = series.flatMap((s) => s.valores.map((p) => p.v)).filter((v) => v != null);
  let dom = d3.extent(todos);
  if (medida === "importe") dom = [0, dom[1]];
  if (medida === "var_pct") dom = [Math.min(0, dom[0]), Math.max(0, dom[1])];
  if (medida === "indice_2015") dom = [Math.min(100, dom[0]), Math.max(100, dom[1])];
  const y = d3.scaleLinear(dom, [alto - m.b, m.t]).nice();

  const svg = d3.select(contenedor).append("svg").attr("viewBox", `0 0 ${ancho} ${alto}`).attr("role", "img")
    .attr("aria-label", `Evolución ${medida === "importe" ? "en euros" : medida === "var_pct" ? "de la variación interanual" : "del índice 2015 = 100"} de ${series.length} partidas. Usa «Ver tabla» para leer los valores.`);

  // bandas de gobierno
  const bandas = svg.append("g");
  for (const v of datos.ventanas) {
    const x0 = x(Math.max(anios[0], v.inicio) - 0.5), x1 = x(Math.min(anios[anios.length - 1], v.fin) + 0.5);
    const xa = Math.max(m.l, x0), xb = Math.min(ancho - m.r, x1);
    if (xb <= xa) continue;
    const actual = datos.actual && v.id === datos.actual.id;
    bandas.append("rect").attr("x", xa).attr("y", m.t - 18).attr("width", xb - xa).attr("height", alto - m.b - m.t + 18)
      .attr("fill", actual ? pal.bandActual : (datos.ventanas.indexOf(v) % 2 ? pal.band : "transparent"));
    // la etiqueta solo se pinta si cabe en su banda (larga → corta → ninguna)
    const fuente = "700 10px 'Space Grotesk'";
    const opciones = [(ETIQUETA_VENTANA[v.id] || v.id) + (actual ? " · actual" : ""), ETIQUETA_VENTANA[v.id] || v.id, ETIQUETA_CORTA[v.id]]
      .filter(Boolean).map((t) => t.toUpperCase());
    const texto = opciones.find((t) => anchoTexto(t, fuente) * 1.12 + 6 <= xb - xa);
    if (texto) bandas.append("text").attr("x", (xa + xb) / 2).attr("y", m.t - 6).attr("text-anchor", "middle").attr("fill", pal.muted)
      .style("font", fuente).style("letter-spacing", ".08em").text(texto);
  }
  // rejilla y ejes (líneas finas, sólidas, recesivas)
  const fmtEje = medida === "importe" ? fmt.meurEje : medida === "var_pct" ? (v) => `${fmt.entero(v)} %` : fmt.entero;
  const gy = svg.append("g").attr("transform", `translate(${m.l},0)`)
    .call(d3.axisLeft(y).ticks(estrecho ? 5 : 6).tickSize(-(ancho - m.l - m.r)).tickFormat(fmtEje));
  gy.select(".domain").remove();
  gy.selectAll("line").attr("stroke", pal.grid);
  gy.selectAll("text").attr("fill", pal.muted).style("font", "400 11px Inter").style("font-variant-numeric", "tabular-nums");
  if (medida === "importe") svg.append("text").attr("x", m.l - 8).attr("y", m.t - 22 < 0 ? 10 : 12).attr("text-anchor", "end")
    .attr("fill", pal.muted).style("font", "400 11px Inter").text("M€");
  const ref = medida === "var_pct" ? 0 : medida === "indice_2015" ? 100 : null;
  if (ref != null) svg.append("line").attr("x1", m.l).attr("x2", ancho - m.r).attr("y1", y(ref)).attr("y2", y(ref))
    .attr("stroke", pal.muted).attr("stroke-width", 1);
  const paso = estrecho ? 2 : 1;
  const gx = svg.append("g").attr("transform", `translate(0,${alto - m.b})`)
    .call(d3.axisBottom(x).tickValues(anios.filter((a, i) => (anios.length - 1 - i) % paso === 0)).tickFormat(d3.format("d")).tickSize(4));
  gx.select(".domain").attr("stroke", pal.grid);
  gx.selectAll("line").attr("stroke", pal.grid);
  gx.selectAll("text").attr("fill", pal.muted).style("font", "400 11px Inter");

  // líneas: tramo Ley continuo; tramo Proyecto discontinuo desde el último año en Ley
  const linea = d3.line().defined((p) => p.v != null).x((p) => x(p.anio)).y((p) => y(p.v)).curve(d3.curveMonotoneX);
  const capa = svg.append("g");
  for (const s of series) {
    const ley = s.valores.map((p) => (p.fase === "proyecto" ? { ...p, v: null } : p));
    capa.append("path").attr("d", linea(ley)).attr("fill", "none").attr("stroke", s.color).attr("stroke-width", 2)
      .attr("stroke-linejoin", "round").attr("stroke-linecap", "round");
    const iProy = s.valores.findIndex((p) => p.fase === "proyecto");
    if (iProy > 0) capa.append("path").attr("d", linea(s.valores.slice(iProy - 1))).attr("fill", "none").attr("stroke", s.color)
      .attr("stroke-width", 2).attr("stroke-dasharray", "4 4");
    const ult = [...s.valores].reverse().find((p) => p.v != null);
    if (ult) {
      capa.append("circle").attr("cx", x(ult.anio)).attr("cy", y(ult.v)).attr("r", 4.5).attr("fill", s.color)
        .attr("stroke", pal.surface).attr("stroke-width", 2);
      if (etiquetasFinales) capa.append("text").attr("x", x(ult.anio) + 9).attr("y", y(ult.v) + 4).attr("fill", pal.text)
        .style("font", "600 11.5px Inter").text(corta(s.etiqueta, 24));
    }
  }
  if (etiquetasFinales) evitarSolapes(capa.selectAll("text").nodes());

  // crosshair + tooltip con todas las series del año
  const guia = svg.append("line").attr("y1", m.t - 18).attr("y2", alto - m.b).attr("stroke", pal.muted).attr("stroke-width", 1).style("display", "none");
  const marcas = svg.append("g");
  const unidadV = medida === "importe" ? fmt.meur : medida === "var_pct" ? fmt.var : fmt.num;
  svg.append("rect").attr("x", m.l).attr("y", m.t - 18).attr("width", ancho - m.l - m.r).attr("height", alto - m.b - m.t + 18)
    .attr("fill", "transparent").style("cursor", "crosshair")
    .on("pointermove", (e) => {
      const [px] = d3.pointer(e);
      const anio = Math.round(x.invert(px));
      if (anio < anios[0] || anio > anios[anios.length - 1]) return;
      guia.style("display", null).attr("x1", x(anio)).attr("x2", x(anio));
      const enAnio = series.map((s) => ({ s, p: s.valores.find((p) => p.anio === anio) })).filter((o) => o.p);
      marcas.selectAll("circle").data(enAnio.filter((o) => o.p.v != null)).join("circle").attr("cx", x(anio))
        .attr("cy", (o) => y(o.p.v)).attr("r", 4.5).attr("fill", (o) => o.s.color).attr("stroke", pal.surface).attr("stroke-width", 2);
      const filasTt = enAnio.sort((a, b) => (b.p.v ?? -Infinity) - (a.p.v ?? -Infinity))
        .map((o) => [corta(o.s.etiqueta, 34), o.p.v == null ? "no comparable" : unidadV(o.p.v), o.s.color]);
      const fase = datos.fases.get(anio);
      const vent = (enAnio[0] && enAnio[0].p.fila && enAnio[0].p.fila.ventana) || "";
      mostrarTooltip(e, `${anio}${fase === "proyecto" ? " · Proyecto" : ""}`, filasTt,
        `${ETIQUETA_VENTANA[vent] || vent}${estado.precios === "constantes" ? " · euros constantes 2025" : ""}`);
    })
    .on("pointerleave", () => { guia.style("display", "none"); marcas.selectAll("*").remove(); ocultarTooltip(); });
  return series;
}

function corta(t, n) { return t.length > n ? t.slice(0, n - 1).trimEnd() + "…" : t; }

/** Etiquetas finales (≤ 4 series): si dos se pisan no se desplazan (se despegarían de su línea): se quitan todas y
    la leyenda y el tooltip llevan la identidad. */
function evitarSolapes(nodos) {
  const ys = nodos.map((n) => +n.getAttribute("y")).sort((a, b) => a - b);
  if (ys.some((v, i) => i > 0 && v - ys[i - 1] < 14)) nodos.forEach((n) => n.remove());
}
