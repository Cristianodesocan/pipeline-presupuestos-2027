/* Pestaña «Peso», gráfico 2: reparto por capítulos (clasificación económica) de lo que se señala en el treemap.
   Anillo en orden fijo de capítulo (1→8, no por tamaño), 2px de superficie entre sectores, total en el centro y,
   al lado, la lista con nombre, importe y % (los valores siempre se leen en texto, no solo en el ángulo).
   Perímetro caps. 1-8, el mismo que el treemap; el cap. 9 (devolución de deuda) se indica aparte. */
/* global d3 */
import { CAPITULO_9, CAPITULOS, fmt, mostrarAyuda, mostrarTooltip, moverTooltip, ocultarTooltip, paleta } from "./comun.js";

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

/* ---------- composición por capítulos año a año (columnas apiladas: euros o % del total)
   Columnas ≤ 24 px desde una sola línea base, capítulos en el mismo orden y color que el donut, 2px de superficie
   entre segmentos. El año elegido arriba se marca bajo el eje; clic en una columna = ver ese año. */
export function pintarComposicion({ contenedor, serie, anioSel, modo, fases, alElegirAnio }) {
  const pal = paleta();
  contenedor.replaceChildren();
  const filas = serie.map((s) => ({ ...s, total: s.caps ? d3.sum(CAPITULOS, (c) => Math.max(0, s.caps[c.n] || 0)) : 0 }))
    .filter((s) => s.total > 0);
  if (filas.length < 2) {
    const p = document.createElement("p"); p.className = "cargando";
    p.textContent = filas.length ? "Solo hay un año con desglose para esta selección." : "Sin desglose por capítulos para esta selección.";
    contenedor.append(p);
    return;
  }
  const pct = modo === "pct";
  const ancho = Math.max(300, contenedor.clientWidth), estrecho = ancho < 640;
  const alto = estrecho ? 230 : 270;
  const m = { t: 26, r: 8, b: 30, l: pct ? 44 : 58 };
  const x = d3.scaleBand(filas.map((f) => f.anio), [m.l, ancho - m.r]).paddingInner(0.35).paddingOuter(0.15);
  const bw = Math.min(24, x.bandwidth());
  const y = d3.scaleLinear([0, pct ? 100 : d3.max(filas, (f) => f.total)], [alto - m.b, m.t]).nice();
  const svg = d3.select(contenedor).append("svg").attr("viewBox", `0 0 ${ancho} ${alto}`).attr("role", "img")
    .attr("aria-label", `Composición por capítulos de ${filas[0].anio} a ${filas[filas.length - 1].anio}, ${pct ? "en % del total" : "en euros"}.`);
  const gy = svg.append("g").attr("transform", `translate(${m.l},0)`)
    .call(d3.axisLeft(y).ticks(estrecho ? 4 : 5).tickSize(-(ancho - m.l - m.r)).tickFormat(pct ? (v) => `${v} %` : fmt.meurEje));
  gy.select(".domain").remove();
  gy.selectAll("line").attr("stroke", pal.grid);
  gy.selectAll("text").attr("fill", pal.muted).style("font", "400 11px Inter").style("font-variant-numeric", "tabular-nums");
  if (!pct) svg.append("text").attr("x", m.l - 8).attr("y", 10).attr("text-anchor", "end").attr("fill", pal.muted)
    .style("font", "400 11px Inter").text("M€");
  const paso = estrecho ? 2 : 1, ult = filas[filas.length - 1].anio;
  const gx = svg.append("g").attr("transform", `translate(0,${alto - m.b})`)
    .call(d3.axisBottom(x).tickValues(filas.map((f) => f.anio).filter((a) => (ult - a) % paso === 0))
      .tickFormat((a) => `${a}${fases.get(a) === "proyecto" ? "*" : ""}`).tickSize(0).tickPadding(8));
  gx.select(".domain").attr("stroke", pal.muted);
  gx.selectAll("text").attr("fill", (a) => (a === anioSel ? pal.strong : pal.muted))
    .style("font", (a) => (a === anioSel ? "700 11px Inter" : "400 11px Inter"));

  const columnas = svg.append("g").selectAll("g").data(filas).join("g")
    .attr("transform", (f) => `translate(${x(f.anio) + (x.bandwidth() - bw) / 2},0)`);
  columnas.each(function (f) {
    let acc = 0;
    const g = d3.select(this);
    CAPITULOS.forEach((c, i) => {
      const v = Math.max(0, f.caps[c.n] || 0), h = pct ? (100 * v) / f.total : v;
      if (h <= 0) return;
      g.append("rect").attr("x", 0).attr("width", bw).attr("y", y(acc + h)).attr("height", Math.max(0, y(acc) - y(acc + h)))
        .attr("fill", pal.series[i]).attr("stroke", pal.surface).attr("stroke-width", 1);
      acc += h;
    });
    if (f.anio === anioSel) g.append("path").attr("d", `M${bw / 2 - 5},${alto - m.b + 22} l5,-6 l5,6 z`).attr("fill", pal.strong);
  });
  // capa de lectura: toda la franja del año es zona activa (más grande que la columna)
  svg.append("g").selectAll("rect").data(filas).join("rect")
    .attr("x", (f) => x(f.anio) - (x.step() - x.bandwidth()) / 2).attr("width", x.step()).attr("y", m.t).attr("height", alto - m.b - m.t)
    .attr("fill", "transparent").style("cursor", "pointer")
    .on("pointerenter", (e, f) => mostrarTooltip(e, `${f.anio}${fases.get(f.anio) === "proyecto" ? " · Proyecto" : ""} · ${fmt.meur(f.total)}`,
      CAPITULOS.map((c, i) => [`Cap. ${c.n} ${c.nombre}`, `${fmt.meur(f.caps[c.n] || 0)} · ${fmt.pct((100 * (f.caps[c.n] || 0)) / f.total)}`,
        pal.series[i]]).filter((r, i) => (f.caps[CAPITULOS[i].n] || 0) > 0), f.anio === anioSel ? "año elegido arriba" : "clic: ver este año"))
    .on("pointermove", moverTooltip).on("pointerleave", ocultarTooltip)
    .on("click", (e, f) => { ocultarTooltip(); if (f.anio !== anioSel) alElegirAnio(f.anio); });
}
