/* Recorrido guiado: 5 claves del presupuesto. Cada paso fija una vista (estado de la URL, compartible con #paso=N)
   y cuenta en dos frases lo que se ve. Las cifras se calculan con los datos cargados: si cambian, el texto cambia.
   Si falta algún dato que un paso necesita, ese paso no se muestra. */
/* global d3 */
import { CAPITULOS, codigoFuncion, codigoSeccion, configDimension, fmt } from "./comun.js";
import { calcularRanking } from "./ranking.js";

const fila = (datos, dim, vista, anio, pred) => datos.treemap.find((d) => d.dimension === dim && d.vista === vista && d.anio === anio
  && d.precios === "corrientes" && d.id_estable !== "__total__" && pred(d));
const pctCap = (caps, n) => { const t = d3.sum(CAPITULOS, (c) => caps[c.n] || 0); return t ? (100 * (caps[n] || 0)) / t : null; };

export function construirPasos(datos) {
  const ley = datos.ultimaLey, primero = datos.anios[0], { base, fin } = datos.ventanaActual;
  const finTxt = `${fin}${datos.fases.get(fin) === "proyecto" ? " (Proyecto)" : ""}`;
  const pasos = [];

  // 1. a qué se destina: sanidad y educación
  const f = (c) => fila(datos, "funcion", "individual", ley, (d) => codigoFuncion(d.id_estable) === c);
  const [san, edu, tra, soc] = ["31", "32", "94", "23"].map(f);
  if (san && edu) {
    const suma = san.peso_total_pct + edu.peso_total_pct;
    pasos.push({ titulo: `Sanidad y Educación: ${Math.round(suma / 10)} de cada 10 euros`,
      texto: `En ${ley}, Sanidad (${fmt.pct(san.peso_total_pct)}) y Educación (${fmt.pct(edu.peso_total_pct)}) suman el ${fmt.pct(suma)} `
        + `del gasto de la Comunidad (capítulos 1-8)`
        + (tra && soc ? `; les siguen las transferencias a otras administraciones (${fmt.pct(tra.peso_total_pct)}) y los servicios sociales (${fmt.pct(soc.peso_total_pct)}).` : ".")
        + " Pasa el ratón por cada rectángulo para ver su detalle.",
      estado: { tab: "peso", dim: "funciones", anio: String(ley) }, destino: "panel-peso" });
  }
  // 2. la Consejería de Sanidad transfiere: sigue el dinero
  const s14 = fila(datos, "seccion", "organica", ley, (d) => codigoSeccion(d.id_estable) === "14");
  const c14 = s14 && datos.capitulos("seccion", "organica", ley, s14.id_estable, "corrientes");
  if (c14) {
    pasos.push({ titulo: "La Consejería de Sanidad casi no gasta: transfiere",
      texto: `El ${fmt.pct(pctCap(c14, 4) + pctCap(c14, 7))} del presupuesto de la sección 14 Sanidad son transferencias: la Consejería pasa `
        + "el dinero al Servicio Canario de la Salud, que es quien contrata y paga. «Sigue el dinero» enlaza las dos cosas.",
      estado: { tab: "peso", dim: "secciones", vista: "organica", anio: String(ley), foco: s14.id_estable }, destino: "bloque-flujo" });
  }
  // 3. dentro del SCS: personal
  const scs = fila(datos, "ente", "individual", ley, (d) => /^ESCS/.test(d.id_estable));
  const cs = scs && datos.capitulos("ente", "individual", ley, scs.id_estable, "corrientes");
  if (cs) {
    const c0 = datos.capitulos("ente", "individual", primero, scs.id_estable, "corrientes");
    pasos.push({ titulo: `En el Servicio Canario de la Salud, ${Math.round(pctCap(cs, 1))} de cada 100 euros son personal`,
      texto: `En ${ley} dedica el ${fmt.pct(pctCap(cs, 1))} a personal (${fmt.meur(cs[1])}) y el ${fmt.pct(pctCap(cs, 2))} a bienes y servicios.`
        + (c0 ? ` En ${primero}, el personal sumaba ${fmt.meur(c0[1])}: las barras muestran cómo ha cambiado la composición.` : ""),
      estado: { tab: "peso", dim: "entes", anio: String(ley), foco: scs.id_estable }, destino: "bloque-composicion" });
  }
  // 4. qué ha cambiado con el gobierno actual
  const cfgF = configDimension("funciones", datos);
  const r = calcularRanking(datos, cfgF, { precios: "corrientes", social: "0", vista: "" }, new Set(), base, fin);
  if (r.suben.length) {
    const s = r.suben[0], b = r.bajan[0];
    pasos.push({ titulo: "¿Qué ha cambiado con el gobierno actual?",
      texto: `Entre ${base} y ${finTxt}, lo que más crece en euros es ${s.etiqueta} (${fmt.meurSigno(s.dif)}, ${fmt.var(s.pct)})`
        + (b ? ` y lo que más baja, ${b.etiqueta} (${fmt.meurSigno(b.dif)}).` : "; ninguna función baja.")
        + " Haz clic en una barra para añadirla al gráfico de líneas.",
      estado: { tab: "evolucion", dim: "funciones", desde: String(base), hasta: String(fin) }, destino: "card-ranking" });
  }
  // 5. por habitante y sin inflación
  const serie = (c) => datos.series.filter((d) => d.dimension === "funcion" && d.precios === "constantes" && codigoFuncion(d.id_estable) === c);
  const sSan = serie("31"), a = sSan.find((d) => d.anio === primero), z = sSan.find((d) => d.anio === ley);
  const pa = datos.poblacion(primero), pz = datos.poblacion(ley);
  if (a && z && a.importe && z.importe && pa && pz) {
    const v0 = a.importe / pa, v1 = z.importe / pz;
    const ids = ["31", "32", "23"].map((c) => (serie(c)[0] || {}).id_estable).filter(Boolean);
    pasos.push({ titulo: "Por habitante y sin inflación",
      texto: `En euros de 2025, el gasto en Sanidad por habitante pasa de ${fmt.entero(v0)} € en ${primero} a ${fmt.entero(v1)} € en ${ley} `
        + `(${fmt.var(100 * (v1 / v0 - 1))}). Así se comparan años sin el efecto de los precios ni del crecimiento de la población.`,
      estado: { tab: "evolucion", dim: "funciones", medida: "por_habitante", precios: "constantes", sel: ids }, destino: "card-lineas" });
  }
  return pasos;
}

export function pintarRecorrido({ contenedor, pasos, i, alIr, alCerrar }) {
  contenedor.replaceChildren();
  const p = pasos[i];
  const cab = document.createElement("div"); cab.className = "rec-cab";
  const num = document.createElement("span"); num.className = "rec-num"; num.textContent = `Clave ${i + 1} de ${pasos.length}`;
  const puntos = document.createElement("span"); puntos.className = "rec-puntos";
  pasos.forEach((_, j) => {
    const b = Object.assign(document.createElement("button"), { type: "button", className: j === i ? "activo" : "" });
    b.setAttribute("aria-label", `Ir a la clave ${j + 1}: ${pasos[j].titulo}`);
    if (j === i) b.setAttribute("aria-current", "step");
    b.addEventListener("click", () => alIr(j));
    puntos.append(b);
  });
  const cerrar = Object.assign(document.createElement("button"), { type: "button", className: "rec-cerrar", textContent: "×" });
  cerrar.setAttribute("aria-label", "Cerrar el recorrido");
  cerrar.addEventListener("click", alCerrar);
  cab.append(num, puntos, cerrar);
  const h = document.createElement("h3"); h.textContent = p.titulo;
  const t = document.createElement("p"); t.textContent = p.texto;
  const nav = document.createElement("div"); nav.className = "rec-nav";
  const ant = Object.assign(document.createElement("button"), { type: "button", className: "btn", textContent: "‹ Anterior", disabled: i === 0 });
  ant.addEventListener("click", () => alIr(i - 1));
  const sig = Object.assign(document.createElement("button"), { type: "button", className: "btn primario",
    textContent: i === pasos.length - 1 ? "Terminar" : "Siguiente ›" });
  sig.addEventListener("click", () => (i === pasos.length - 1 ? alCerrar() : alIr(i + 1)));
  nav.append(ant, sig);
  contenedor.append(cab, h, t, nav);
}
