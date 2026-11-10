/* Orquestación: filtros (una fila, encima de todo) con ayuda emergente, pestañas, estado en la URL, buscadores,
   donut de capítulos enlazado al treemap, tablas, CSV y tema. */
/* global d3 */
import { crearBuscador } from "./buscador.js";
import {
  cargarDatos, codigoFuncion, codigoSeccion, configDimension, descargarCSV, fmt, mostrarAyuda, ocultarTooltip,
  paleta, pintarTabla, sinCodigo, tono, varAbs, VARIAS,
} from "./comun.js";
import { pintarDonut, sumarCapitulos } from "./donut.js";
import { escribirEstado, leerEstado } from "./estado.js";
import { candidatas, filasSeries, MAX_SERIES, pintarLineas } from "./lineas.js";
import { filasDetalle, filasTreemap, filasVisibles, pintarTreemap, rutaHasta, zoomEfectivo } from "./treemap.js";

const $ = (id) => document.getElementById(id);
const estado = leerEstado();
let datos, cfg, seriesPintadas = [], senalado = null;

/* ---------- tema (preferencia del sistema o elección guardada) */
function aplicarTema(t) {
  if (t) document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme;
  const oscuro = t ? t === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  $("tema").textContent = oscuro ? "Modo claro" : "Modo oscuro";
}
try { aplicarTema(localStorage.getItem("tema-presupuestos")); } catch { aplicarTema(null); }
$("tema").addEventListener("click", () => {
  const oscuro = document.documentElement.dataset.theme
    ? document.documentElement.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  const nuevo = oscuro ? "light" : "dark";
  try { localStorage.setItem("tema-presupuestos", nuevo); } catch { /* sin almacenamiento: solo esta sesión */ }
  aplicarTema(nuevo);
  pintar();
});
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { aplicarTema(document.documentElement.dataset.theme); pintar(); });

/* ---------- ayudas de los filtros: 1-2 frases al pasar el ratón o al llegar con el teclado */
const AYUDA_VISTA = {
  organica: "Cada consejería tal como se aprobó en su año: el reparto real de cada presupuesto.",
  estructura: "Proyecta hacia atrás las consejerías actuales: cuánto se destinaba cada año a lo que hoy gestiona cada una. Sirve para comparar competencias en el tiempo.",
  individual: "Cada programa por separado, con su código de ese año.",
  familia: "Une los programas que se dividieron, fusionaron o cambiaron de código, para que la serie sea comparable en el tiempo.",
};
const AYUDA_COLOR = {
  funciones: "Cada función (sanidad, educación, servicios sociales…) tiene su color: el mismo que la sección que la gestiona principalmente.",
  secciones: "Cada sección o consejería tiene su propio color. Los programas usan estos mismos colores.",
  programas: "Cada programa toma el color de la sección que lo gestiona (los mismos colores que en Secciones); gris si se reparte entre varias.",
  entes: "Cada rectángulo toma el color de su tipo de ente: organismo autónomo, entidad pública, consorcio…",
};
const textoPropio = (el) => [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join("").trim();
function ayudaFiltro(e) {
  const el = e.target.closest && e.target.closest("[data-ayuda]");
  if (!el || !$("filtros").contains(el)) return;
  mostrarAyuda(e, textoPropio(el), el.dataset.ayuda, el);
}
$("filtros").addEventListener("pointerover", ayudaFiltro);
$("filtros").addEventListener("focusin", ayudaFiltro);
$("filtros").addEventListener("pointerout", (e) => {
  const desde = e.target.closest && e.target.closest("[data-ayuda]");
  if (desde && !desde.contains(e.relatedTarget)) ocultarTooltip();
});
$("filtros").addEventListener("focusout", ocultarTooltip);

/* ---------- controles */
function radio(nombre, valor) { const i = document.querySelector(`input[name="${nombre}"][value="${valor}"]`); if (i) i.checked = true; }

function prepararControles() {
  cfg = configDimension(estado.dim, datos);
  // vista
  const seg = $("seg-vista");
  seg.replaceChildren();
  $("campo-vista").hidden = !cfg.vistas;
  if (cfg.vistas) {
    if (!cfg.vistas.some(([v]) => v === estado.vista)) estado.vista = cfg.vistas[0][0];
    for (const [v, t] of cfg.vistas) {
      const l = document.createElement("label");
      l.dataset.ayuda = AYUDA_VISTA[v.startsWith("estructura") ? "estructura" : v] || "";
      const i = Object.assign(document.createElement("input"), { type: "radio", name: "vista", value: v, checked: v === estado.vista });
      l.append(i, document.createTextNode(t));
      seg.append(l);
    }
  } else estado.vista = "";
  // años disponibles para la dimensión
  const anios = [...new Set(datos.treemap.filter((d) => d.dimension === cfg.treemapDim).map((d) => d.anio))].sort((a, b) => b - a);
  if (!anios.includes(+estado.anio)) estado.anio = String(anios[0]);
  const sel = $("anio");
  sel.replaceChildren(...anios.map((a) => Object.assign(document.createElement("option"),
    { value: a, textContent: `${a}${datos.fases.get(a) === "proyecto" ? " (Proyecto)" : ""}`, selected: String(a) === estado.anio })));
  radio("dim", estado.dim); radio("precios", estado.precios); radio("color", estado.color); radio("medida", estado.medida);
  $("social").checked = estado.social === "1";
  $("campo-social").hidden = !cfg.social;
  $("ayuda-color-cat").dataset.ayuda = AYUDA_COLOR[estado.dim];
  const peso = estado.tab === "peso";
  $("campo-anio").hidden = !peso; $("campo-color").hidden = !peso; $("campo-medida").hidden = peso;
  for (const [id, activa] of [["tab-peso", peso], ["tab-evolucion", !peso]]) {
    $(id).setAttribute("aria-selected", activa); $(id).tabIndex = activa ? 0 : -1;
  }
  $("panel-peso").hidden = !peso; $("panel-evolucion").hidden = peso;
}

$("filtros").addEventListener("change", (e) => {
  const { name, value, checked } = e.target;
  if (name === "dim") { estado.dim = value; estado.zoom = []; estado.sel = null; estado.foco = null; }
  else if (name === "vista") { estado.vista = value; estado.zoom = []; estado.sel = null; estado.foco = null; }
  else if (e.target.id === "anio") estado.anio = value;
  else if (e.target.id === "social") { estado.social = checked ? "1" : "0"; estado.zoom = []; estado.sel = null; estado.foco = null; }
  else if (name) estado[name] = value;
  actualizar();
});
for (const [id, tab] of [["tab-peso", "peso"], ["tab-evolucion", "evolucion"]]) {
  $(id).addEventListener("click", () => { estado.tab = tab; actualizar(); });
  $(id).addEventListener("keydown", (e) => {
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") { estado.tab = estado.tab === "peso" ? "evolucion" : "peso"; actualizar(); $(`tab-${estado.tab}`).focus(); }
  });
}
for (const [boton, tabla] of [["ver-tabla-peso", "tabla-peso"], ["ver-tabla-evo", "tabla-evo"]]) {
  $(boton).addEventListener("click", () => {
    const t = $(tabla); t.hidden = !t.hidden;
    $(boton).setAttribute("aria-expanded", !t.hidden); $(boton).textContent = t.hidden ? "Ver tabla" : "Ocultar tabla";
  });
}

/* ---------- textos y tablas */
const vistaNombre = () => (cfg.vistas ? cfg.vistas.find(([v]) => v === estado.vista)[1].toLowerCase() : "");
const preciosTxt = () => (estado.precios === "corrientes" ? "euros corrientes" : "euros constantes de 2025");
const idsSociales = () => new Set(datos.treemap.filter((d) => d.dimension === "programa" && d.concepto_ced).map((d) => d.id_estable));
const codigoPrograma = (t) => (/\(([0-9]{3}[A-Z])\)\s*$/.exec(t || "") || [])[1] || "";
const nombreSeccionDe = (d) => {
  const c = datos.seccionDe(d.vista, d.anio, d.id_estable);
  return c === VARIAS ? "Varias" : c ? `${c} · ${datos.nombreSeccion(c, d.anio)}` : "—";
};

const COLS_PESO = [
  { titulo: "Partida", valor: (d) => d.etiqueta },
  { titulo: "Grupo", valor: (d) => (d.dimension === "funcion" ? "" : [d.nivel_1, d.nivel_2].filter(Boolean).join(" › ")) },
  { titulo: "Importe (M€)", valor: (d) => d.importe, fmt: (v) => fmt.meur(v).replace(" M€", ""), numero: true },
  { titulo: "Peso total", valor: (d) => d.peso_total_pct, fmt: (v) => fmt.pct(v, 2), numero: true },
  { titulo: "Peso en el grupo", valor: (d) => (d.dimension === "funcion" ? null : d.peso_padre_pct), fmt: fmt.pct, numero: true },
  { titulo: "Var. interanual (M€)", valor: varAbs, fmt: (v) => fmt.meurSigno(v).replace(" M€", ""), numero: true, signo: true },
  { titulo: "Var. interanual (%)", valor: (d) => d.var_pct_interanual, fmt: fmt.var, numero: true, signo: true },
  { titulo: "Δ peso gobierno actual", valor: (d) => d.delta_peso_pp_clavijo_ii, fmt: fmt.pp, numero: true, signo: true },
  { titulo: "Comparabilidad", valor: (d) => d.comparabilidad },
];

function tituloPeso() {
  const anio = +estado.anio;
  const fase = datos.fases.get(anio) === "proyecto" ? " (Proyecto)" : "";
  const zoom = zoomEfectivo(cfg, estado);
  const vista = cfg.vistas ? ` · vista ${vistaNombre()}` : "";
  if (cfg.capas && zoom.length) return `Peso de las subfunciones de ${zoom[zoom.length - 1]} en ${anio}${fase}`;
  return `Peso de ${cfg.art} ${cfg.unidad} en ${anio}${fase}${vista}`;
}

function pintarPeso() {
  const anio = +estado.anio;
  const zoom = zoomEfectivo(cfg, estado);
  $("titulo-treemap").textContent = tituloPeso();
  const pista = cfg.capas ? (zoom.length < cfg.capas.length - 1 ? " · clic en una función para ver sus subfunciones" : "")
    : (cfg.niveles.length > zoom.length ? " · clic en un grupo para ampliar" : "");
  $("sub-treemap").textContent = `${preciosTxt()[0].toUpperCase()}${preciosTxt().slice(1)} · ${estado.color === "delta"
    ? `color = cambio de peso ${datos.ventanaActual.base}→${datos.ventanaActual.fin}` : "color = " + cfg.colorNombre}${pista}`
    + (estado.dim === "entes" ? " · no aditivo con la Administración general" : "");
  ocultarTooltip();
  pintarTreemap({ contenedor: $("treemap"), leyenda: $("leyenda-peso"), migas: $("migas"), datos, cfg, estado,
    alZoom: (z) => { estado.zoom = z; senalado = null; actualizar(); },
    alSenalar: (d) => { senalado = d; pintarCapitulos(); },
    alFijar: (id) => { estado.foco = estado.foco === id ? null : id; senalado = null; pintar(); } });
  pintarBarraFoco();
  const filas = filasVisibles(datos, cfg, estado).sort((a, b) => b.importe - a.importe);
  const cols = cfg.nombre === "programas" ? [...COLS_PESO.slice(0, 2), { titulo: "Sección", valor: nombreSeccionDe }, ...COLS_PESO.slice(2)]
    : COLS_PESO;
  pintarTabla($("tabla-peso"), cols, filas);
  $("csv-peso").onclick = () => descargarCSV(`peso_${estado.dim}_${anio}_${estado.precios}.csv`,
    [{ titulo: "id_estable", valor: (d) => d.id_estable }, ...cols.map((c) => ({ titulo: c.titulo, valor: c.valor }))], filas);
  pintarCapitulos();
}

/* ---------- buscador de la pestaña Peso y partida fijada */
/** Partidas que se pueden buscar: en funciones, las funciones y sus subfunciones; si no, la capa entera (sin zoom). */
function filasBuscables() {
  if (!cfg.capas) return filasTreemap(datos, cfg, estado);
  const base = { ...estado, zoom: [] };
  const funciones = filasTreemap(datos, cfg, base);
  const subs = datos.treemap.filter((d) => d.dimension === cfg.capas[1].dim && d.vista === cfg.vistaFija && d.anio === +estado.anio
    && d.precios === estado.precios && d.id_estable !== "__total__" && d.importe > 0);
  return [...funciones, ...subs];
}

const colorSeccion = (c) => { const pal = paleta(); return configDimension("secciones", datos).colorCategoria(c, pal); };
const ordenEs = (a, b) => a.localeCompare(b, "es", { sensitivity: "base" });

function opcionesPeso(filas) {
  const anio = +estado.anio;
  if (cfg.nombre === "programas") {
    // por sección presupuestaria (orden numérico) y, dentro, por orden alfabético; un programa compartido sale en cada sección
    const out = [];
    for (const d of filas) {
      const secs = datos.seccionesDe(d.vista, d.anio, d.id_estable);
      for (const s of secs.length ? secs : [{ seccion: null }]) {
        out.push({ id: d.id_estable, fila: d, etiqueta: sinCodigo(d.etiqueta), codigo: codigoPrograma(d.etiqueta), orden: s.seccion ?? "99",
          grupo: s.seccion ? `${s.seccion} · ${datos.nombreSeccion(s.seccion, anio)}` : "Sin sección asignada",
          color: s.seccion ? colorSeccion(s.seccion) : null });
      }
    }
    return out.sort((a, b) => d3.ascending(a.orden, b.orden) || ordenEs(a.etiqueta, b.etiqueta));
  }
  if (cfg.nombre === "funciones") {
    const fun = filas.filter((d) => d.dimension === "funcion").map((d) => ({ id: d.id_estable, fila: d, etiqueta: d.etiqueta,
      codigo: codigoFuncion(d.id_estable), grupo: "Funciones", orden: "0" + codigoFuncion(d.id_estable) }));
    const sub = filas.filter((d) => d.dimension !== "funcion").map((d) => ({ id: d.id_estable, fila: d, etiqueta: d.etiqueta,
      codigo: (/^SF(\d{3})/.exec(d.id_estable) || [])[1] || "", grupo: `Subfunciones de ${d.nivel_2}`,
      orden: "1" + codigoFuncion(d.id_estable) }));
    return [...fun, ...sub].sort((a, b) => d3.ascending(a.orden, b.orden) || d3.ascending(a.codigo, b.codigo));
  }
  if (cfg.nombre === "secciones") {
    return filas.map((d) => ({ id: d.id_estable, fila: d, etiqueta: sinCodigo(d.etiqueta), codigo: codigoSeccion(d.id_estable) || "" }))
      .sort((a, b) => d3.ascending(a.codigo || "zz", b.codigo || "zz"));
  }
  return filas.map((d) => ({ id: d.id_estable, fila: d, etiqueta: d.etiqueta, grupo: d.nivel_1 || "Otros" }))
    .sort((a, b) => ordenEs(a.grupo, b.grupo) || ordenEs(a.etiqueta, b.etiqueta));
}

function pintarBarraFoco() {
  const cont = $("barra-foco");
  cont.replaceChildren();
  const filas = filasBuscables();
  crearBuscador({ contenedor: cont, opciones: opcionesPeso(filas),
    placeholder: cfg.nombre === "programas" ? "Buscar programa o sección…" : `Buscar ${cfg.singular}…`,
    etiqueta: `Buscar ${cfg.singular} y fijarlo en el gráfico de capítulos`,
    alElegir: (o) => { estado.zoom = rutaHasta(cfg, o.fila); estado.foco = o.id; senalado = null; actualizar(); } });
  const fijada = estado.foco && filas.find((d) => d.id_estable === estado.foco);
  if (fijada) {
    const chip = document.createElement("span"); chip.className = "chip foco";
    const t = document.createElement("span"); t.className = "t"; t.textContent = `Fijado: ${fijada.etiqueta}`;
    const x = document.createElement("button"); x.type = "button"; x.textContent = "×";
    x.setAttribute("aria-label", `Quitar ${fijada.etiqueta} del gráfico de capítulos`);
    x.addEventListener("click", () => { estado.foco = null; pintar(); });
    chip.append(t, x);
    cont.append(chip);
  } else {
    const p = document.createElement("span"); p.className = "pista";
    p.textContent = "o haz clic en un rectángulo para ver su reparto por capítulos";
    cont.append(p);
  }
}

/* ---------- donut de capítulos: lo señalado (ratón) › lo fijado (clic o buscador) › todo lo visible */
function pintarCapitulos() {
  if (!datos || estado.tab !== "peso") return;
  const card = $("card-capitulos");
  card.hidden = !datos.hayCapitulos;
  if (!datos.hayCapitulos) return;
  const visibles = filasVisibles(datos, cfg, estado);
  const fijada = estado.foco && filasBuscables().find((d) => d.id_estable === estado.foco);
  const objeto = senalado || fijada || null;
  const filas = objeto ? [objeto] : visibles;
  const zoom = zoomEfectivo(cfg, estado);
  const nombre = objeto ? objeto.etiqueta
    : zoom.length ? zoom[zoom.length - 1]
      : cfg.social && estado.social === "1" ? "los programas de gasto social"
        : `${cfg.art === "los" ? "todos los" : "todas las"} ${cfg.unidad}`;
  $("titulo-donut").textContent = `¿En qué tipo de gasto? Capítulos de ${nombre}`;
  const anio = +estado.anio;
  $("sub-donut").textContent = `${anio}${datos.fases.get(anio) === "proyecto" ? " (Proyecto)" : ""} · ${preciosTxt()} · `
    + (senalado ? "partida señalada" : fijada ? "partida fijada (× arriba para quitarla)" : `suma de ${visibles.length} partidas visibles`);
  const ficha = $("ficha-donut");
  ficha.replaceChildren();
  if (objeto) {
    for (const [k, v, , signo] of filasDetalle(objeto, datos, cfg, estado).filter(([k]) => /^(Importe|Peso sobre|Var\. interanual|Sección)/.test(k))) {
      const s = document.createElement("span"); s.append(document.createTextNode(`${k}: `));
      const b = document.createElement("b"); b.textContent = signo ? `${signo === "pos" ? "▲" : "▼"} ${v}` : v;
      if (signo) b.className = signo;
      s.append(b); ficha.append(s);
    }
  } else {
    const total = d3.sum(visibles, (d) => d.importe), va = d3.sum(visibles, (d) => varAbs(d) || 0);
    for (const [k, v, signo] of [["Importe", fmt.meur(total)], ["Var. interanual de las partidas comparables", fmt.meurSigno(va), tono(va)]]) {
      const s = document.createElement("span"); s.append(document.createTextNode(`${k}: `));
      const b = document.createElement("b"); b.textContent = signo ? `${signo === "pos" ? "▲" : "▼"} ${v}` : v;
      if (signo) b.className = signo;
      s.append(b); ficha.append(s);
    }
  }
  const { caps, faltan } = sumarCapitulos(datos, cfg, estado, filas);
  const { cuota4 } = pintarDonut({ contenedor: $("donut"), nota: $("nota-donut"), caps, faltan, n: filas.length });
  avisoTransferencias(cuota4, objeto);
}

/** Si más de la mitad es transferencia corriente (cap. 4), el gasto final lo hace otro: lo más frecuente, un organismo
    autónomo como el Servicio Canario de la Salud. Se explica y se ofrece ir a la dimensión Entes. */
const ENTE_POR_AMBITO = { 14: "ESCS_2015", 31: "ESCS_2015", 16: "ESCE_2015", 24: "ESCE_2015" };
function avisoTransferencias(cuota4, objeto) {
  const aviso = $("aviso-donut");
  aviso.replaceChildren();
  aviso.hidden = !(estado.dim !== "entes" && cuota4 > 0.5);
  if (aviso.hidden) return;
  const ambito = objeto && (cfg.nombre === "funciones" ? codigoFuncion(objeto.id_estable)
    : cfg.nombre === "secciones" ? codigoSeccion(objeto.id_estable) : null);
  const ente = ENTE_POR_AMBITO[ambito];
  const t = document.createElement("span");
  t.textContent = `El ${fmt.pct(100 * cuota4)} es transferencia corriente (cap. 4): dinero que se entrega para que lo gasten otros, `
    + (ente === "ESCS_2015" ? "aquí sobre todo el Servicio Canario de la Salud, que lo dedica en su mayor parte a personal."
      : "como el Servicio Canario de la Salud, el Servicio Canario de Empleo, cabildos, ayuntamientos, familias o empresas.")
    + " El reparto final de los organismos con presupuesto propio se ve en la dimensión Entes.";
  const b = Object.assign(document.createElement("button"), { type: "button", className: "btn", textContent: "Ver en Entes →" });
  b.addEventListener("click", () => {
    Object.assign(estado, { dim: "entes", zoom: [], sel: null, foco: ente || null });
    senalado = null; actualizar(); $("card-capitulos").scrollIntoView({ behavior: "smooth", block: "start" });
  });
  aviso.append(t, b);
}

/* ---------- pestaña Evolución */
function pintarEvolucion() {
  const soc = idsSociales();
  const cands = candidatas(datos, cfg, estado, soc);
  const validos = new Set(cands.map((c) => c.id));
  if (!estado.sel || !estado.sel.some((id) => id && validos.has(id))) estado.sel = cands.slice(0, 6).map((c) => c.id);
  estado.sel = estado.sel.map((id) => (id && validos.has(id) ? id : null));
  const medidaTxt = { importe: "en euros", var_pct: "variación % interanual" }[estado.medida];
  $("titulo-lineas").textContent = `Evolución de ${cfg.artLineas} ${cfg.unidadLineas}${cfg.vistas ? ` · vista ${vistaNombre()}` : ""}`;
  $("sub-lineas").textContent = `${medidaTxt[0].toUpperCase()}${medidaTxt.slice(1)} · ${preciosTxt()}`;
  seriesPintadas = pintarLineas({ contenedor: $("lineas"), leyenda: $("leyenda-evo"), datos, cfg, estado, idsSociales: soc, seleccion: estado.sel });
  pintarSelector(cands, new Set(seriesPintadas.filter((s) => s.familia).map((s) => s.id)));
  const unidad = estado.medida === "importe" ? (v) => fmt.meur(v).replace(" M€", "") : fmt.var;
  const cols = [{ titulo: "Partida", valor: (s) => s.etiqueta },
    ...datos.anios.map((a) => ({ titulo: String(a), valor: (s) => (s.valores.find((p) => p.anio === a) || {}).v, fmt: unidad, numero: true }))];
  pintarTabla($("tabla-evo"), cols, seriesPintadas);
  const largas = filasSeries(datos, cfg, estado, soc).filter((d) => estado.sel.includes(d.id_estable));
  $("csv-evo").onclick = () => descargarCSV(`evolucion_${estado.dim}_${estado.precios}.csv`,
    ["id_estable", "etiqueta", "anio", "fase", "importe", "var_abs", "var_pct", "ventana", "comparabilidad"]
      .map((k) => ({ titulo: k, valor: (d) => d[k] })), largas);
}

/** Secciones de un programa en el año más reciente en que tiene datos (para agrupar el buscador de Evolución). */
function seccionesRecientes(vista, id) {
  for (let i = datos.anios.length - 1; i >= 0; i--) {
    const l = datos.seccionesDe(vista, datos.anios[i], id);
    if (l.length) return { anio: datos.anios[i], secciones: l };
  }
  return { anio: datos.ultimo, secciones: [] };
}

function opcionesEvolucion(cands) {
  const libres = cands.filter((c) => !estado.sel.includes(c.id));
  if (cfg.nombre !== "programas") return libres.map((c) => ({ id: c.id, etiqueta: c.etiqueta }));
  const vista = cfg.vistas ? estado.vista : cfg.vistaFija;
  const out = [];
  for (const c of libres) {
    const { anio, secciones } = seccionesRecientes(vista, c.id);
    for (const s of secciones.length ? secciones : [{ seccion: null }]) {
      // un grupo por código de sección, con su nombre actual; si el programa ya no existe, se indica su último año
      out.push({ id: c.id, etiqueta: sinCodigo(c.etiqueta) + (anio < datos.ultimo ? ` (hasta ${anio})` : ""),
        codigo: codigoPrograma(c.etiqueta), orden: s.seccion ?? "99",
        grupo: s.seccion ? `${s.seccion} · ${datos.nombreSeccion(s.seccion, datos.ultimo)}` : "Sin sección asignada",
        color: s.seccion ? colorSeccion(s.seccion) : null });
    }
  }
  return out.sort((a, b) => d3.ascending(a.orden, b.orden) || ordenEs(a.etiqueta, b.etiqueta));
}

function pintarSelector(cands, familias = new Set()) {
  const cont = $("selector");
  cont.replaceChildren();
  const pal = getComputedStyle(document.documentElement);
  const porId = new Map(cands.map((c) => [c.id, c]));
  estado.sel.forEach((id, ranura) => {
    if (!id) return;
    const chip = document.createElement("span"); chip.className = "chip";
    const ln = document.createElement("span"); ln.className = "ln"; ln.style.background = pal.getPropertyValue(`--s${ranura + 1}`);
    const t = document.createElement("span"); t.className = "t";
    t.textContent = ((porId.get(id) || {}).etiqueta || id) + (familias.has(id) ? " ◆" : "");
    const x = document.createElement("button"); x.type = "button"; x.textContent = "×";
    x.setAttribute("aria-label", `Quitar ${t.textContent}`);
    x.addEventListener("click", () => { estado.sel[ranura] = null; actualizar(); });   // la ranura queda libre: nadie cambia de color
    chip.append(ln, t, x); cont.append(chip);
  });
  const ocupadas = estado.sel.filter(Boolean).length;
  const lleno = ocupadas >= MAX_SERIES;
  crearBuscador({ contenedor: cont, opciones: lleno ? [] : opcionesEvolucion(cands), deshabilitado: lleno,
    placeholder: lleno ? `Máximo ${MAX_SERIES} partidas` : cfg.nombre === "programas" ? "Añadir programa (por sección)…" : "Añadir partida…",
    etiqueta: "Buscar partida para añadir",
    alElegir: (o) => {
      const libre = estado.sel.indexOf(null);
      if (libre >= 0) estado.sel[libre] = o.id; else if (estado.sel.length < MAX_SERIES) estado.sel.push(o.id);
      actualizar();
    } });
}

/* ---------- ciclo de pintado */
function pintar() {
  if (!datos) return;
  if (estado.tab === "peso") pintarPeso(); else pintarEvolucion();
  escribirEstado(estado);
}
function actualizar() { prepararControles(); pintar(); }
// un enlace compartido o «Atrás» que cambie el #estado se aplica sin recargar (replaceState no dispara este evento)
addEventListener("hashchange", () => { Object.assign(estado, leerEstado()); senalado = null; if (datos) actualizar(); });

let temporizador, anchoPrevio = 0;
new ResizeObserver(([e]) => {
  const w = Math.round(e.contentRect.width);
  if (w === anchoPrevio) return;          // solo al cambiar el ancho (no al crecer la página con el donut o la tabla)
  anchoPrevio = w;
  clearTimeout(temporizador); temporizador = setTimeout(pintar, 150);
}).observe(document.querySelector("main"));

cargarDatos().then((d) => {
  datos = d;
  const ult = d.ultimo;
  $("rango-anios").textContent = `${d.anios[0]}-${ult}`;
  $("badge-fase").textContent = `Serie oficial ${d.anios[0]}-${ult} · ${ult} en fase de ${d.fases.get(ult) === "proyecto" ? "Proyecto" : "Ley"}`;
  if (d.ultimaCarga) $("pie-carga").textContent = `Datos actualizados el ${d.ultimaCarga.slice(0, 10).split("-").reverse().join("/")}`;
  actualizar();
}).catch((e) => {
  $("treemap").replaceChildren(Object.assign(document.createElement("p"), { className: "cargando",
    textContent: "No se pudieron cargar los datos. Abre la página desde un servidor (p. ej. python3 -m http.server) y comprueba data/*.csv." }));
  console.error(e);
});

