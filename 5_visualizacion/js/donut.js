/* Pestaña «Peso», gráfico 2: reparto por capítulos (clasificación económica) de lo que se señala en el treemap.
   Anillo en orden fijo de capítulo (1→8, no por tamaño), 2px de superficie entre sectores, total en el centro y,
   al lado, la lista con nombre, importe y % (los valores siempre se leen en texto, no solo en el ángulo).
   Perímetro caps. 1-8, el mismo que el treemap; el cap. 9 (devolución de deuda) se indica aparte. */
/* global d3 */
import { CAPITULO_9, CAPITULOS, fmt, mostrarAyuda, moverTooltip, ocultarTooltip, paleta } from "./comun.js";

/** Suma los capítulos de varias partidas. Devuelve { caps: {n: €}, faltan } (faltan = partidas sin desglose). */
export function sumarCapitulos(datos, cfg, estado, filas) {
  const vista = cfg.vistas ? estado.vista : cfg.vistaFija;
  const caps = Object.fromEntries([...CAPITULOS, CAPITULO_9].map((c) => [c.n, 0]));
  let faltan = 0;
  for (const d of filas) {
    const c = datos.capitulos(cfg.capDim(d), vista, d.anio, d.id_estable, estado.precios);
    if (!c) { faltan++; continue; }
    for (const k of Object.keys(caps)) caps[k] += c[k] || 0;
  }
  return { caps, faltan };
}

export function pintarDonut({ contenedor, nota, caps, faltan, n }) {
  const pal = paleta();
  contenedor.replaceChildren();
  nota.textContent = "";
  const partes = CAPITULOS.map((c, i) => ({ ...c, valor: Math.max(0, caps[c.n] || 0), color: pal.series[i] }));
  const total = d3.sum(partes, (p) => p.valor);
  if (!(total > 0)) {
    const p = document.createElement("p"); p.className = "cargando";
    p.textContent = "Sin desglose por capítulos para esta selección.";
    contenedor.append(p);
    return { total: 0, cuota4: 0 };
  }
  const lado = 260, r = lado / 2, grosor = 46;
  const arcos = d3.pie().sort(null).value((p) => p.valor).padAngle(0)(partes);
  const arco = d3.arc().innerRadius(r - grosor).outerRadius(r).cornerRadius(3);
  const arcoAct = d3.arc().innerRadius(r - grosor - 4).outerRadius(r + 4).cornerRadius(3);

  const svg = d3.select(contenedor).append("svg").attr("viewBox", `${-r - 6} ${-r - 6} ${lado + 12} ${lado + 12}`)
    .attr("role", "img").attr("aria-label", `Reparto por capítulos: ${partes.filter((p) => p.valor > 0)
      .map((p) => `capítulo ${p.n}, ${fmt.pct((100 * p.valor) / total)}`).join("; ")}.`);
  const sectores = svg.append("g").selectAll("path").data(arcos.filter((a) => a.value > 0)).join("path")
    .attr("d", arco).attr("fill", (a) => a.data.color).attr("stroke", pal.surface).attr("stroke-width", 2);
  svg.append("text").attr("text-anchor", "middle").attr("y", -4).attr("fill", pal.strong)
    .style("font", "700 22px 'Space Grotesk'").text(fmt.meur(total));
  svg.append("text").attr("text-anchor", "middle").attr("y", 18).attr("fill", pal.muted)
    .style("font", "400 12px Inter").text("capítulos 1-8");

  const lista = document.createElement("ul"); lista.className = "lista-caps";
  const items = partes.map((p) => {
    const li = document.createElement("li"); li.tabIndex = 0;
    if (!p.valor) li.classList.add("cero");
    const sw = document.createElement("span"); sw.className = "sw"; sw.style.background = p.color;
    const nombre = document.createElement("span");
    const cap = document.createElement("span"); cap.className = "cap"; cap.textContent = `Cap. ${p.n}`;
    nombre.append(cap, document.createTextNode(p.nombre));
    const v = document.createElement("span"); v.className = "n"; v.textContent = fmt.meur(p.valor);
    const pc = document.createElement("span"); pc.className = "p"; pc.textContent = fmt.pct((100 * p.valor) / total);
    li.append(sw, nombre, v, pc);
    lista.append(li);
    return li;
  });

  // resaltar a la vez el sector y su fila; la ayuda explica el capítulo en una frase
  const resaltar = (p, e, ancla) => {
    sectores.attr("d", (a) => (p && a.data.n === p.n ? arcoAct(a) : arco(a)))
      .attr("opacity", (a) => (!p || a.data.n === p.n ? 1 : 0.45));
    items.forEach((li, i) => li.classList.toggle("activa", !!p && partes[i].n === p.n));
    if (p && e) mostrarAyuda(e, `Capítulo ${p.n} · ${p.nombre}`,
      `${p.ayuda} ${fmt.meur(p.valor)} (${fmt.pct((100 * p.valor) / total)} de lo seleccionado).`, ancla);
    else ocultarTooltip();
  };
  sectores.style("cursor", "help").on("pointerenter", (e, a) => resaltar(a.data, e)).on("pointermove", moverTooltip)
    .on("pointerleave", () => resaltar(null));
  items.forEach((li, i) => {
    li.addEventListener("pointerenter", (e) => resaltar(partes[i], e, li));
    li.addEventListener("pointerleave", () => resaltar(null));
    li.addEventListener("focus", (e) => resaltar(partes[i], e, li));
    li.addEventListener("blur", () => resaltar(null));
  });
  contenedor.append(lista);

  const avisos = [];
  if (caps[9] > 0) avisos.push(`Además, ${fmt.meur(caps[9])} en el capítulo 9, ${CAPITULO_9.nombre.toLowerCase()} `
    + `(devolución de deuda), fuera del perímetro de los gráficos.`);
  if (faltan) avisos.push(`${faltan} de ${n} partidas no tienen desglose por capítulos en el Tomo y no se suman.`);
  nota.textContent = avisos.join(" ");
  return { total, cuota4: (caps[4] || 0) / total };
}
