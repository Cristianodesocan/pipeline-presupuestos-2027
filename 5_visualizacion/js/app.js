/* Orquestación: filtros (una fila, encima de todo), pestañas, estado en la URL, tablas, CSV y tema. */
/* global d3 */
import { cargarDatos, configDimension, descargarCSV, fmt, pintarTabla } from "./comun.js";
import { escribirEstado, leerEstado } from "./estado.js";
import { candidatas, filasSeries, MAX_SERIES, pintarLineas } from "./lineas.js";
import { filasTreemap, pintarTreemap } from "./treemap.js";

const $ = (id) => document.getElementById(id);
const estado = leerEstado();
let datos, cfg, seriesPintadas = [];

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
  const peso = estado.tab === "peso";
  $("campo-anio").hidden = !peso; $("campo-color").hidden = !peso; $("campo-medida").hidden = peso;
  $("tab-peso").setAttribute("aria-selected", peso); $("tab-evolucion").setAttribute("aria-selected", !peso);
  $("panel-peso").hidden = !peso; $("panel-evolucion").hidden = peso;
}

$("filtros").addEventListener("change", (e) => {
  const { name, value, checked } = e.target;
  if (name === "dim") { estado.dim = value; estado.zoom = []; estado.sel = null; }
  else if (name === "vista") { estado.vista = value; estado.zoom = []; estado.sel = null; }
  else if (e.target.id === "anio") estado.anio = value;
  else if (e.target.id === "social") { estado.social = checked ? "1" : "0"; estado.zoom = []; estado.sel = null; }
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

const COLS_PESO = [
  { titulo: "Partida", valor: (d) => d.etiqueta },
  { titulo: "Grupo", valor: (d) => [d.nivel_1, d.nivel_2].filter(Boolean).join(" › ") },
  { titulo: "Importe (M€)", valor: (d) => d.importe, fmt: (v) => fmt.meur(v).replace(" M€", ""), numero: true },
  { titulo: "Peso total", valor: (d) => d.peso_total_pct, fmt: (v) => fmt.pct(v, 2), numero: true },
  { titulo: "Peso en el grupo", valor: (d) => d.peso_padre_pct, fmt: fmt.pct, numero: true },
  { titulo: "Var. interanual", valor: (d) => d.var_pct_interanual, fmt: fmt.var, numero: true, signo: true },
  { titulo: "Δ peso gobierno actual", valor: (d) => d.delta_peso_pp_clavijo_ii, fmt: fmt.pp, numero: true, signo: true },
  { titulo: "Comparabilidad", valor: (d) => d.comparabilidad },
];

function pintarPeso() {
  const anio = +estado.anio;
  const fase = datos.fases.get(anio) === "proyecto" ? " (Proyecto)" : "";
  $("titulo-treemap").textContent = `Peso de ${cfg.art} ${cfg.unidad} en ${anio}${fase}${cfg.vistas ? ` · vista ${vistaNombre()}` : ""}`;
  $("sub-treemap").textContent = `${preciosTxt()[0].toUpperCase()}${preciosTxt().slice(1)} · ${estado.color === "delta"
    ? `color = cambio de peso ${datos.ventanaActual.base}→${datos.ventanaActual.fin}` : "color = " + cfg.colorNombre}`
    + (cfg.niveles.length > estado.zoom.length ? " · clic en un grupo para ampliar" : "")
    + (estado.dim === "entes" ? " · no aditivo con la Administración general" : "");
  pintarTreemap({ contenedor: $("treemap"), leyenda: $("leyenda-peso"), migas: $("migas"), datos, cfg, estado,
    alZoom: (z) => { estado.zoom = z; actualizar(); } });
  const filas = filasTreemap(datos, cfg, estado).filter((d) => estado.zoom.every((z, i) => d[cfg.niveles[i]] === z))
    .sort((a, b) => b.importe - a.importe);
  pintarTabla($("tabla-peso"), COLS_PESO, filas);
  $("csv-peso").onclick = () => descargarCSV(`peso_${estado.dim}_${anio}_${estado.precios}.csv`,
    [{ titulo: "id_estable", valor: (d) => d.id_estable }, ...COLS_PESO.map((c) => ({ titulo: c.titulo, valor: c.valor }))], filas);
}

function pintarEvolucion() {
  const soc = idsSociales();
  const cands = candidatas(datos, cfg, estado, soc);
  const validos = new Set(cands.map((c) => c.id));
  if (!estado.sel || !estado.sel.some((id) => id && validos.has(id))) estado.sel = cands.slice(0, 6).map((c) => c.id);
  estado.sel = estado.sel.map((id) => (id && validos.has(id) ? id : null));
  const medidaTxt = { importe: "en euros", var_pct: "variación % interanual", indice_2015: "índice 2015 = 100" }[estado.medida];
  $("titulo-lineas").textContent = `Evolución de ${cfg.artLineas} ${cfg.unidadLineas}${cfg.vistas ? ` · vista ${vistaNombre()}` : ""}`;
  $("sub-lineas").textContent = `${medidaTxt[0].toUpperCase()}${medidaTxt.slice(1)} · ${preciosTxt()}`;
  seriesPintadas = pintarLineas({ contenedor: $("lineas"), leyenda: $("leyenda-evo"), datos, cfg, estado, idsSociales: soc, seleccion: estado.sel });
  pintarSelector(cands, new Set(seriesPintadas.filter((s) => s.familia).map((s) => s.id)));
  const unidad = estado.medida === "importe" ? (v) => fmt.meur(v).replace(" M€", "") : estado.medida === "var_pct" ? fmt.var : fmt.num;
  const cols = [{ titulo: "Partida", valor: (s) => s.etiqueta },
    ...datos.anios.map((a) => ({ titulo: String(a), valor: (s) => (s.valores.find((p) => p.anio === a) || {}).v, fmt: unidad, numero: true }))];
  pintarTabla($("tabla-evo"), cols, seriesPintadas);
  const largas = filasSeries(datos, cfg, estado, soc).filter((d) => estado.sel.includes(d.id_estable));
  $("csv-evo").onclick = () => descargarCSV(`evolucion_${estado.dim}_${estado.precios}.csv`,
    ["id_estable", "etiqueta", "anio", "fase", "importe", "var_abs", "var_pct", "indice_2015", "ventana", "comparabilidad"]
      .map((k) => ({ titulo: k, valor: (d) => d[k] })), largas);
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
  const buscador = document.createElement("div"); buscador.className = "buscador";
  const input = Object.assign(document.createElement("input"), { type: "search",
    placeholder: ocupadas >= MAX_SERIES ? `Máximo ${MAX_SERIES} partidas` : "Añadir partida…", disabled: ocupadas >= MAX_SERIES });
  input.setAttribute("aria-label", "Buscar partida para añadir");
  const lista = document.createElement("div"); lista.className = "sugerencias"; lista.hidden = true;
  const sugerir = () => {
    const q = input.value.trim().toLowerCase();
    const opciones = cands.filter((c) => !estado.sel.includes(c.id) && (!q || c.etiqueta.toLowerCase().includes(q))).slice(0, 30);
    lista.replaceChildren(...opciones.map((c) => {
      const b = document.createElement("button"); b.type = "button"; b.textContent = c.etiqueta;
      b.addEventListener("mousedown", (e) => e.preventDefault());
      b.addEventListener("click", () => {
        const libre = estado.sel.indexOf(null);
        if (libre >= 0) estado.sel[libre] = c.id; else if (estado.sel.length < MAX_SERIES) estado.sel.push(c.id);
        actualizar();
      });
      return b;
    }));
    lista.hidden = !opciones.length;
  };
  input.addEventListener("focus", sugerir);
  input.addEventListener("input", sugerir);
  input.addEventListener("blur", () => setTimeout(() => { lista.hidden = true; }, 150));
  buscador.append(input, lista);
  cont.append(buscador);
}

/* ---------- ciclo de pintado */
function pintar() {
  if (!datos) return;
  if (estado.tab === "peso") pintarPeso(); else pintarEvolucion();
  escribirEstado(estado);
}
function actualizar() { prepararControles(); pintar(); }

let temporizador;
new ResizeObserver(() => { clearTimeout(temporizador); temporizador = setTimeout(pintar, 150); }).observe(document.querySelector("main"));

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
