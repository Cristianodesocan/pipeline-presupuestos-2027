/* «Sigue el dinero» (pestaña Peso, bajo el donut): qué parte de lo seleccionado se gasta directamente y qué parte se
   transfiere (caps. 4 y 7), y qué entes con presupuesto propio gastan en las mismas subfunciones.
   El Tomo 3 no publica el destinatario de cada transferencia: el enlace es por subfunción (3 primeras cifras del
   programa) y se dice así en el gráfico. Barras a la misma escala en euros; capítulos con los colores del donut. */
/* global d3 */
import { CAPITULOS, codigoFuncion, codigoSeccion, fmt, mostrarTooltip, moverTooltip, ocultarTooltip, paleta, tintaSobre } from "./comun.js";

const DIRECTOS = [1, 2, 3, 6, 8], TRANSFERENCIAS = [4, 7];
const caps18 = (d, f) => Object.fromEntries(CAPITULOS.map((c) => [c.n, (d[`cap_${c.n}`] || 0) * f]));

/** Clave con la que se reconoce si un par (sección, programa) pertenece a lo seleccionado; null si no se puede. */
function clavePar(cfg, estado, fila) {
  if (cfg.nombre === "funciones") {
    const c = fila.dimension === "subfuncion" ? (/^SF(\d{3})/.exec(fila.id_estable) || [])[1] : codigoFuncion(fila.id_estable);
    return c ? { k: c, de: (p) => (p.programa || "").startsWith(c) } : null;
  }
  if (cfg.nombre === "secciones") {
    if (estado.vista !== "organica") return null;                 // la vista estructura reparte pares: no se sigue
    const c = codigoSeccion(fila.id_estable);
    return c ? { k: c, de: (p) => p.seccion === c } : null;
  }
  if (cfg.nombre === "programas") {
    const campo = estado.vista === "familia" ? "id_grupo" : "id_estable";
    return { k: fila.id_estable, de: (p) => p[campo] === fila.id_estable };
  }
  return null;
}

/** Calcula el flujo de una lista de partidas (una seleccionada o todas las visibles) en el año y precios del estado. */
export function calcularFlujo(datos, cfg, estado, filas) {
  if (cfg.nombre === "entes" || !filas.length) return null;
  const claves = filas.map((f) => clavePar(cfg, estado, f));
  if (claves.some((c) => !c)) return null;
  const anio = +estado.anio, constantes = estado.precios === "constantes";
  const pares = datos.paresDe(anio).filter((p) => p.programa && claves.some((c) => c.de(p)));
  if (!pares.length) return null;
  const porSf = new Map();
  for (const p of pares) {
    const f = constantes ? p.deflactor || 1 : 1;
    const t = ((p.cap_4 || 0) + (p.cap_7 || 0)) * f;
    if (t > 0) porSf.set(p.programa.slice(0, 3), (porSf.get(p.programa.slice(0, 3)) || 0) + t);
  }
  const transf = d3.sum(porSf.values());
  // gasto de cada ente en esas subfunciones (por capítulo) y parte de la transferencia que «casa» con él
  const entes = new Map(), gastoSf = new Map();
  for (const e of datos.entesProgramaDe(anio)) {
    const sf = (e.programa || "").slice(0, 3);
    if (!porSf.has(sf)) continue;
    const f = constantes ? e.deflactor || 1 : 1;
    const c = caps18(e, f), g = d3.sum(Object.values(c));
    if (g <= 0) continue;
    const o = entes.get(e.id_estable) || { id: e.id_estable, caps: Object.fromEntries(CAPITULOS.map((k) => [k.n, 0])), gasto: 0, sfs: new Map() };
    for (const k of CAPITULOS) o.caps[k.n] += c[k.n];
    o.gasto += g;
    o.sfs.set(sf, (o.sfs.get(sf) || 0) + g);
    entes.set(e.id_estable, o);
    gastoSf.set(sf, (gastoSf.get(sf) || 0) + g);
  }
  // la transferencia de cada subfunción se reparte entre sus entes según su gasto, hasta lo que gastan
  for (const o of entes.values()) {
    o.casado = d3.sum([...o.sfs], ([sf, g]) => Math.min(porSf.get(sf), gastoSf.get(sf)) * (g / gastoSf.get(sf)));
  }
  const umbral = Math.max(0.5e6, 0.02 * transf);
  const todos = [...entes.values()].filter((o) => o.casado > 0).sort((a, b) => b.casado - a.casado);
  const principales = todos.filter((o) => o.casado >= umbral).slice(0, 3);
  const casado = d3.sum(todos, (o) => o.casado);
  return { transf, porSf, entes: principales, otrosEntes: casado - d3.sum(principales, (o) => o.casado), otros: Math.max(0, transf - casado) };
}

export function pintarFlujo({ contenedor, flujo, caps, nombre, datos, alIrAEnte }) {
  const pal = paleta();
  contenedor.replaceChildren();
  const total = d3.sum(CAPITULOS, (c) => Math.max(0, caps[c.n] || 0));
  const color = new Map(CAPITULOS.map((c, i) => [c.n, pal.series[i]]));
  const ancho = Math.max(300, contenedor.clientWidth), estrecho = ancho < 640;
  const m = { l: 0, r: 0 }, H = 18, fila = 46;
  const maximo = d3.max([total, ...flujo.entes.map((o) => o.gasto), flujo.otros]);
  const k = (ancho - m.l - m.r) / maximo;
  const alto = fila + 40 + flujo.entes.length * fila + (flujo.otros > 0.5e6 ? fila : 0) + 4;
  const svg = d3.select(contenedor).append("svg").attr("viewBox", `0 0 ${ancho} ${alto}`).attr("role", "img")
    .attr("aria-label", `${nombre}: ${fmt.meur(total)}, de los que ${fmt.meur(flujo.transf)} son transferencias. `
      + flujo.entes.map((o) => `${datos.nombreEnte(o.id)} gasta ${fmt.meur(o.gasto)} en las mismas subfunciones`).join("; ") + ".");
  const etiqueta = (y, texto, peso = 600) => svg.append("text").attr("x", 0).attr("y", y).attr("fill", pal.text)
    .style("font", `${peso} 12.5px Inter`).text(texto);
  const barra = (y, orden, valores, alPasar, base) => {
    let x = m.l;
    const g = svg.append("g");
    for (const n of orden) {
      const w = Math.max(0, (valores[n] || 0) * k);
      if (w <= 0) continue;
      g.append("rect").attr("x", x).attr("y", y).attr("width", w).attr("height", H).attr("fill", color.get(n))
        .attr("stroke", pal.surface).attr("stroke-width", 1);
      // rótulo dentro del segmento solo si cabe: «Cap. 1 · 55 %» o «55 %»
      const p = fmt.pct((100 * valores[n]) / base, 0), largo = `Cap. ${n} · ${p}`;
      const txt = w >= largo.length * 6.4 + 10 ? largo : w >= p.length * 6.4 + 8 ? p : null;
      if (txt) g.append("text").attr("x", x + 5).attr("y", y + H / 2 + 4).attr("fill", tintaSobre(color.get(n)))
        .style("font", "600 11px Inter").style("pointer-events", "none").text(txt);
      x += w;
    }
    if (alPasar) g.style("cursor", "pointer").on("pointerenter", alPasar).on("pointermove", moverTooltip).on("pointerleave", ocultarTooltip);
    return g;
  };
  const filasCaps = (valores, base) => CAPITULOS.filter((c) => (valores[c.n] || 0) > 0)
    .map((c) => [`Cap. ${c.n} ${c.nombre}`, `${fmt.meur(valores[c.n])} · ${fmt.pct((100 * valores[c.n]) / base)}`, color.get(c.n)]);

  // 1. lo seleccionado: primero lo que gasta directamente, después lo que transfiere
  const directo = d3.sum(DIRECTOS, (n) => caps[n] || 0), transfiere = d3.sum(TRANSFERENCIAS, (n) => caps[n] || 0);
  etiqueta(13, estrecho ? `${nombre} · ${fmt.meur(total)}` : `${nombre} · ${fmt.meur(total)}: gasta directamente ${fmt.meur(directo)} `
    + `y transfiere ${fmt.meur(transfiere)} (${fmt.pct((100 * transfiere) / total)})`);
  barra(20, [...DIRECTOS, ...TRANSFERENCIAS], caps, (e) => mostrarTooltip(e, nombre, filasCaps(caps, total)), total);
  const tx0 = m.l + directo * k, tx1 = tx0 + transfiere * k;
  svg.append("path").attr("d", `M${tx0},${20 + H + 4} v4 H${tx1} v-4`).attr("fill", "none").attr("stroke", pal.muted);
  // 2. conector: de las transferencias a los entes que gastan en las mismas subfunciones
  const y2 = fila + 40;
  if (flujo.entes.length) {
    const ex1 = m.l + d3.max(flujo.entes, (o) => o.gasto) * k;
    svg.insert("path", ":first-child").attr("d", `M${tx0},${20 + H + 8} L${tx1},${20 + H + 8} L${ex1},${y2 - 6} L${m.l},${y2 - 6} Z`)
      .attr("fill", pal.band).attr("stroke", "none");
    svg.append("text").attr("x", Math.max(4, Math.min(ancho - 4, (tx0 + tx1) / 2))).attr("y", 20 + H + 22)
      .attr("text-anchor", (tx0 + tx1) / 2 > ancho * 0.6 ? "end" : "middle").attr("fill", pal.muted).style("font", "400 11.5px Inter")
      .text("Entes que gastan en las mismas subfunciones ↓");
  }
  flujo.entes.forEach((o, i) => {
    const y = y2 + i * fila;
    const sfs = [...o.sfs.keys()].sort();
    const sfTxt = sfs.length === 1 ? `subfunción ${sfs[0]} ${datos.nombreSubfuncion(sfs[0])}` : `subfunciones ${sfs.join(", ")}`;
    etiqueta(y + 13, `${datos.nombreEnte(o.id)} · ${fmt.meur(o.gasto)}${estrecho ? "" : ` en la ${sfTxt}`}`);
    barra(y + 20, CAPITULOS.map((c) => c.n), o.caps, (e) => mostrarTooltip(e, `${datos.nombreEnte(o.id)} · ${sfTxt}`,
      filasCaps(o.caps, o.gasto), "clic: ver el ente completo"), o.gasto).on("click", () => { ocultarTooltip(); alIrAEnte(o.id); });
  });
  if (flujo.otros > 0.5e6) {
    const y = y2 + flujo.entes.length * fila;
    etiqueta(y + 13, `Otros destinatarios (cabildos, ayuntamientos, familias, empresas…) · ${fmt.meur(flujo.otros)}`, 400);
    svg.append("rect").attr("x", m.l).attr("y", y + 20).attr("width", flujo.otros * k).attr("height", H).attr("fill", pal.otro);
  }
}
