/* Pestaña «Evolución», gráfico 4: ¿qué ha cambiado entre dos años? Las 10 partidas que más suben y las 10 que más
   bajan en euros (con los filtros de arriba). Barras divergentes desde un eje central (verde sube ▲, rojo baja ▼),
   nombres a la izquierda y valores en una columna alineada a la derecha. Clic = añadir la partida a las líneas. */
/* global d3 */
import { anchoTexto, fmt, mostrarTooltip, moverTooltip, ocultarTooltip, paleta, tono } from "./comun.js";
import { filasSeries } from "./lineas.js";

const N = 10;

export function calcularRanking(datos, cfg, estado, idsSociales, desde, hasta) {
  const porId = d3.group(filasSeries(datos, cfg, estado, idsSociales), (d) => d.id_estable);
  const comparables = [];
  let excluidas = 0;
  for (const [id, l] of porId) {
    const a = l.find((d) => d.anio === desde), b = l.find((d) => d.anio === hasta);
    const va = a ? a.importe : null, vb = b ? b.importe : null;
    if (va == null || vb == null) { if (va || vb) excluidas++; continue; }
    comparables.push({ id, etiqueta: (b || a).etiqueta, v0: va, v1: vb, dif: vb - va, pct: va ? 100 * (vb / va - 1) : null });
  }
  return {
    suben: comparables.filter((d) => d.dif > 0).sort((x, y) => y.dif - x.dif).slice(0, N),
    bajan: comparables.filter((d) => d.dif < 0).sort((x, y) => x.dif - y.dif).slice(0, N),
    excluidas, n: comparables.length,
  };
}

const corta = (t, ancho, fuente) => {
  if (anchoTexto(t, fuente) <= ancho) return t;
  let s = t;
  while (s.length > 4 && anchoTexto(s + "…", fuente) > ancho) s = s.slice(0, -1);
  return s.trimEnd() + "…";
};

export function pintarRanking({ contenedor, res, desde, hasta, enLineas, alElegir }) {
  const pal = paleta();
  const cs = getComputedStyle(document.documentElement);
  const verde = cs.getPropertyValue("--pos-text").trim(), rojo = cs.getPropertyValue("--neg-text").trim();
  contenedor.replaceChildren();
  if (!res.suben.length && !res.bajan.length) {
    const p = document.createElement("p"); p.className = "cargando"; p.textContent = "Sin partidas comparables entre esos dos años.";
    contenedor.append(p); return;
  }
  const ancho = Math.max(300, contenedor.clientWidth), estrecho = ancho < 640;
  const colNombre = Math.min(estrecho ? ancho * 0.42 : 330, ancho * 0.42), colValor = estrecho ? 70 : 150;
  const x0 = colNombre + 8, x1 = ancho - colValor - 8, centro = (x0 + x1) / 2;
  const max = d3.max([...res.suben, ...res.bajan], (d) => Math.abs(d.dif));
  const k = (x1 - x0) / 2 / max;
  const fila = 26, cab = 26;
  const bloques = [["Más suben", res.suben], ["Más bajan", res.bajan]].filter(([, l]) => l.length);
  const alto = d3.sum(bloques, ([, l]) => cab + l.length * fila) + 6;
  const svg = d3.select(contenedor).append("svg").attr("viewBox", `0 0 ${ancho} ${alto}`).attr("role", "img")
    .attr("aria-label", `Partidas que más suben y más bajan entre ${desde} y ${hasta}. Usa «Ver tabla» del gráfico 3 para las series.`);
  svg.append("line").attr("x1", centro).attr("x2", centro).attr("y1", 0).attr("y2", alto).attr("stroke", pal.muted);
  let y = 0;
  for (const [titulo, lista] of bloques) {
    svg.append("text").attr("x", 0).attr("y", y + 17).attr("fill", pal.muted).style("font", "700 10.5px 'Space Grotesk'")
      .style("letter-spacing", ".1em").text(titulo.toUpperCase());
    y += cab;
    const g = svg.append("g").selectAll("g").data(lista).join("g").attr("transform", (d, i) => `translate(0,${y + i * fila})`)
      .style("cursor", "pointer").attr("tabindex", 0).attr("role", "button")
      .attr("aria-label", (d) => `${d.etiqueta}: ${fmt.meurSigno(d.dif)} (${fmt.var(d.pct)}). ${enLineas.has(d.id) ? "Ya está en el gráfico de líneas." : "Intro para añadirla al gráfico de líneas."}`);
    g.append("rect").attr("x", 0).attr("y", 0).attr("width", ancho).attr("height", fila).attr("fill", "transparent");
    g.append("text").attr("x", colNombre).attr("y", fila / 2 + 4).attr("text-anchor", "end").attr("fill", pal.text)
      .style("font", (d) => `${enLineas.has(d.id) ? 700 : 400} 12px Inter`).text((d) => corta(d.etiqueta, colNombre, "400 12px Inter"));
    g.append("rect").attr("x", (d) => (d.dif > 0 ? centro : centro + d.dif * k)).attr("y", (fila - 14) / 2)
      .attr("width", (d) => Math.max(1, Math.abs(d.dif) * k)).attr("height", 14).attr("rx", 3)
      .attr("fill", (d) => (d.dif > 0 ? verde : rojo));
    g.append("text").attr("x", ancho).attr("y", fila / 2 + 4).attr("text-anchor", "end")
      .attr("fill", (d) => (d.dif > 0 ? verde : rojo)).style("font", "600 12px Inter").style("font-variant-numeric", "tabular-nums")
      .text((d) => (estrecho ? fmt.meurSigno(d.dif) : `${fmt.meurSigno(d.dif)} · ${fmt.var(d.pct)}`));
    g.on("pointerenter focus", (e, d) => mostrarTooltip(e, d.etiqueta, [[`${desde}`, fmt.meur(d.v0)], [`${hasta}`, fmt.meur(d.v1)],
      ["Diferencia", fmt.meurSigno(d.dif), null, tono(d.dif)], ["Variación", fmt.var(d.pct), null, tono(d.pct)]],
      enLineas.has(d.id) ? "ya está en el gráfico de líneas" : "clic: añadir al gráfico de líneas"))
      .on("pointermove", moverTooltip).on("pointerleave blur", ocultarTooltip)
      .on("click", (e, d) => { ocultarTooltip(); alElegir(d.id); })
      .on("keydown", (e, d) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); alElegir(d.id); } });
    y += lista.length * fila;
  }
}
