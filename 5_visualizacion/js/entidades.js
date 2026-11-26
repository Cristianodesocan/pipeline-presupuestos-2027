/* Pestaña «Peso», gráfico 3: ¿a quién se transfiere? Desglose de las porciones 4 (transferencias corrientes) y 7
   (transferencias de capital) del donut por tipo de entidad receptora, con los Tomos 7 y 8 («Anexo de Transferencias
   Corrientes» y «Anexo de Operaciones de Capital»), que sí publican el destinatario de cada proyecto.
   Misma selección que el donut (señalado › fijado › todo lo visible). Barras horizontales agrupadas por sector,
   apiladas cap. 4 / cap. 7 con los colores de esas porciones del donut; debajo, los proyectos de mayor importe.
   Los datos los genera el pipeline «transferencias a entidades» (4_carga/exportar_viz.py), que comprueba que cuadran
   al euro con los caps. 4 y 7 de viz_capitulos.csv. */
/* global d3 */
import { anchoTexto, CAPITULOS, fmt, mostrarTooltip, moverTooltip, ocultarTooltip, paleta } from "./comun.js";
import { clavePar } from "./flujo.js";

const N_PROYECTOS = 10;
const NATURALEZAS = ["Transferencia", "Subvención", "Sin distinguir"];
const colorCap = (pal, n) => pal.series[CAPITULOS.findIndex((c) => c.n === n)];

/* ---------- proyectos: se piden la primera vez que hacen falta (1,2 MB) */
let proyectos = null, pidiendo = null;
function cargarProyectos(datos) {
  if (!pidiendo) {
    pidiendo = d3.csv("data/viz_transferencias_proyectos.csv", (d) => ({ ...d, anio: +d.anio, capitulo: +d.capitulo, importe: +d.importe }))
      .then((filas) => { for (const p of filas) Object.assign(p, datos.idsPrograma(p.anio, p.seccion, p.programa)); proyectos = filas; return filas; })
      .catch(() => { proyectos = []; return []; });
  }
  return pidiendo;
}

/** Filas de transferencias (agregadas o proyectos) que pertenecen a la selección; null si no se puede seguir. */
function deLaSeleccion(cfg, estado, filas, candidatas) {
  if (cfg.nombre === "entes" || !filas.length) return null;
  const claves = filas.map((f) => clavePar(cfg, estado, f));
  if (claves.some((c) => !c)) return null;
  return candidatas.filter((p) => claves.some((c) => c.de(p)));
}

/** Agrega por tipo de entidad: [{id, sector, sector_orden, tipo, c4, c7, total, nat:{…}}] y el total. */
export function calcularEntidades(datos, cfg, estado, filas) {
  const anio = +estado.anio;
  const sel = deLaSeleccion(cfg, estado, filas, datos.transferenciasDe(anio));
  if (!sel) return null;
  const f = estado.precios === "constantes" ? datos.deflactorDe(anio) : 1;
  const porTipo = new Map();
  for (const r of sel) {
    const o = porTipo.get(r.tipo_entidad_id) || { id: r.tipo_entidad_id, sector: r.sector, sector_orden: r.sector_orden,
      tipo: r.tipo_entidad, c4: 0, c7: 0, total: 0, nat: Object.fromEntries(NATURALEZAS.map((n) => [n, 0])) };
    const v = r.importe * f;
    if (r.capitulo === 4) o.c4 += v; else o.c7 += v;
    o.total += v;
    o.nat[r.naturaleza] = (o.nat[r.naturaleza] || 0) + v;
    porTipo.set(r.tipo_entidad_id, o);
  }
  const tipos = [...porTipo.values()].filter((o) => o.total > 0)
    .sort((a, b) => a.sector_orden - b.sector_orden || b.total - a.total);
  return { tipos, total: d3.sum(tipos, (o) => o.total), factor: f };
}

export function pintarEntidades({ contenedor, leyenda, nota, lista, tituloLista, res, capsDonut, nombre, alListo }) {
  const pal = paleta();
  contenedor.replaceChildren();
  leyenda.replaceChildren();
  nota.textContent = "";
  if (!res || !res.tipos.length) {
    const p = document.createElement("p"); p.className = "cargando";
    p.textContent = res ? "Esta selección no tiene transferencias (caps. 4 y 7)." : "";
    contenedor.append(p);
    lista.replaceChildren(); tituloLista.hidden = true;
    return;
  }
  // leyenda de capítulos (mismos colores que el donut)
  for (const n of [4, 7]) {
    const s = document.createElement("span"); s.className = "item";
    const i = document.createElement("span"); i.className = "sw"; i.style.background = colorCap(pal, n);
    s.append(i, document.createTextNode(`Cap. ${n} · ${CAPITULOS.find((c) => c.n === n).nombre}`));
    leyenda.append(s);
  }

  const ancho = Math.max(300, contenedor.clientWidth);
  const fuenteT = "500 13px Inter", fuenteS = "600 11px Inter", fuenteV = "600 13px Inter";
  const fila = 40, cabecera = 26, H = 12;
  const sectores = d3.groups(res.tipos, (o) => o.sector);
  const alto = sectores.length * cabecera + res.tipos.length * fila + 4;
  const k = ancho / d3.max(res.tipos, (o) => o.total);
  const svg = d3.select(contenedor).append("svg").attr("viewBox", `0 0 ${ancho} ${alto}`).attr("role", "img")
    .attr("aria-label", `${nombre}: ${fmt.meur(res.total)} transferidos. `
      + res.tipos.map((o) => `${o.tipo}, ${fmt.meur(o.total)}`).join("; ") + ".");
  const recorta = (t, max, fuente) => {
    let s = t;
    while (s.length > 4 && anchoTexto(s, fuente) > max) s = s.slice(0, -2).trimEnd() + "…";
    return s;
  };
  let y = 0;
  for (const [sector, tipos] of sectores) {
    const tot = d3.sum(tipos, (o) => o.total);
    svg.append("text").attr("x", 0).attr("y", y + 17).attr("fill", pal.muted).style("font", fuenteS)
      .style("text-transform", "uppercase").style("letter-spacing", ".04em")
      .text(recorta(`${sector} · ${fmt.meur(tot)} (${fmt.pct((100 * tot) / res.total)})`, ancho, fuenteS));
    y += cabecera;
    for (const o of tipos) {
      const g = svg.append("g").attr("transform", `translate(0,${y})`).attr("tabindex", 0).attr("role", "listitem")
        .style("cursor", "default")
        .attr("aria-label", `${o.tipo}: ${fmt.meur(o.total)}, ${fmt.pct((100 * o.total) / res.total)} de lo transferido`);
      const valor = `${fmt.meur(o.total)} · ${fmt.pct((100 * o.total) / res.total)}`;
      const anchoValor = anchoTexto(valor, fuenteV) + 12;
      g.append("text").attr("x", 0).attr("y", 13).attr("fill", pal.text).style("font", fuenteT)
        .text(recorta(o.tipo, ancho - anchoValor, fuenteT));
      g.append("text").attr("x", ancho).attr("y", 13).attr("text-anchor", "end").attr("fill", pal.strong).style("font", fuenteV).text(valor);
      g.append("rect").attr("x", 0).attr("y", 20).attr("width", ancho).attr("height", H).attr("rx", 2).attr("fill", pal.grid).attr("opacity", 0.35);
      let x = 0;
      for (const [n, v] of [[4, o.c4], [7, o.c7]]) {
        if (v <= 0) continue;
        const w = Math.max(1, v * k);
        g.append("rect").attr("x", x).attr("y", 20).attr("width", w).attr("height", H).attr("rx", 2).attr("fill", colorCap(pal, n));
        x += w + (v * k > 3 ? 2 : 0);                         // 2px de superficie entre segmentos
      }
      const tt = (e) => mostrarTooltip(e, o.tipo, [
        ["Cap. 4 · corrientes", fmt.meur(o.c4), colorCap(pal, 4)], ["Cap. 7 · capital", fmt.meur(o.c7), colorCap(pal, 7)],
        ...NATURALEZAS.filter((n) => o.nat[n] > 0).map((n) => [n === "Sin distinguir" ? "Sin distinguir (hasta 2018)" : n, fmt.meur(o.nat[n])]),
        ["Parte de lo transferido", fmt.pct((100 * o.total) / res.total)]], `Sector: ${o.sector}`);
      g.on("mouseenter focus", tt).on("mousemove", moverTooltip).on("mouseleave blur", ocultarTooltip);
      y += fila;
    }
  }
  // cuadre con el donut (caps. 4 + 7): deben coincidir al euro; si no, se dice
  const donut = (capsDonut[4] || 0) + (capsDonut[7] || 0);
  const cuadra = Math.abs(donut - res.total) <= 1000;
  nota.textContent = `Total transferido: ${fmt.meur(res.total)}`
    + (cuadra ? ", igual que las porciones 4 y 7 del gráfico 2. "
      : `; el gráfico 2 suma ${fmt.meur(donut)} en esos capítulos (la diferencia está en partidas sin desglose). `)
    + "Tipo de entidad según el concepto económico del subconcepto (p. ej. 460 = cabildos); la naturaleza "
    + "(transferencia o subvención) solo se distingue desde 2019.";
  alListo && alListo();
}

/** Proyectos de la selección (de mayor a menor importe). Devuelve null mientras se cargan. */
export function proyectosDe(datos, cfg, estado, filas) {
  if (!proyectos) { cargarProyectos(datos); return null; }
  const anio = +estado.anio;
  const f = estado.precios === "constantes" ? datos.deflactorDe(anio) : 1;
  const sel = deLaSeleccion(cfg, estado, filas, proyectos.filter((p) => p.anio === anio)) || [];
  return sel.map((p) => ({ ...p, valor: p.importe * f })).sort((a, b) => b.valor - a.valor);
}

export function esperarProyectos(datos) { return cargarProyectos(datos); }

export function pintarListaProyectos({ lista, titulo, filas, nombresTipo, total }) {
  lista.replaceChildren();
  titulo.hidden = !filas || !filas.length;
  if (!filas) {
    const li = document.createElement("li"); li.className = "cargando"; li.textContent = "Cargando proyectos…"; lista.append(li);
    titulo.hidden = false;
    return;
  }
  titulo.textContent = filas.length > N_PROYECTOS
    ? `Los ${N_PROYECTOS} proyectos con mayor importe (de ${filas.length}; todos en «Ver tabla»)`
    : `Proyectos (${filas.length})`;
  for (const p of filas.slice(0, N_PROYECTOS)) {
    const li = document.createElement("li");
    const cab = document.createElement("div"); cab.className = "lp-cab";
    const nom = document.createElement("span"); nom.className = "lp-nombre"; nom.textContent = p.proyecto_den;
    const imp = document.createElement("b"); imp.textContent = fmt.meur(p.valor);
    cab.append(nom, imp);
    const meta = document.createElement("div"); meta.className = "lp-meta";
    const lugar = [p.municipio, p.isla].filter((x) => x && !/^(Varios municipios|Sin especificar)$/.test(x)).join(" · ") || p.isla;
    meta.textContent = `${nombresTipo.get(p.tipo_entidad_id) || p.tipo_entidad_id} · cap. ${p.capitulo} · ${lugar}`
      + (total > 0 ? ` · ${fmt.pct((100 * p.valor) / total)}` : "");
    li.append(cab, meta);
    lista.append(li);
  }
}
