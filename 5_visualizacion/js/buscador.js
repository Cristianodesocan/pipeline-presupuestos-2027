/* Buscador con lista agrupada (combobox accesible). Lo usan las dos pestañas.
   opciones: [{ id, etiqueta, codigo?, grupo?, color? }] YA ORDENADAS; los grupos salen en el orden en que aparecen.
   Escribir filtra por nombre, código o grupo (sin tildes); flechas para moverse, Intro para elegir, Esc para cerrar. */
import { normalizar } from "./comun.js";

let serie = 0;

export function crearBuscador({ contenedor, opciones, alElegir, placeholder, etiqueta, deshabilitado = false }) {
  const uid = `bus-${++serie}`;
  const caja = document.createElement("div"); caja.className = "buscador";
  const input = Object.assign(document.createElement("input"), { type: "search", placeholder, disabled: deshabilitado, autocomplete: "off" });
  input.setAttribute("role", "combobox");
  input.setAttribute("aria-label", etiqueta);
  input.setAttribute("aria-autocomplete", "list");
  input.setAttribute("aria-expanded", "false");
  input.setAttribute("aria-controls", uid);
  const lista = document.createElement("div"); lista.className = "sugerencias"; lista.id = uid; lista.hidden = true;
  lista.setAttribute("role", "listbox");
  lista.setAttribute("aria-label", etiqueta);
  const indice = opciones.map((o) => normalizar(`${o.codigo || ""} ${o.etiqueta} ${o.grupo || ""}`));
  let visibles = [], activa = -1;

  const abrir = (si) => { lista.hidden = !si; input.setAttribute("aria-expanded", String(si)); };
  const marcar = (i) => {
    activa = i;
    lista.querySelectorAll(".opc").forEach((n, j) => n.classList.toggle("activa", j === i));
    const n = lista.querySelectorAll(".opc")[i];
    if (n) { input.setAttribute("aria-activedescendant", n.id); n.scrollIntoView({ block: "nearest" }); }
    else input.removeAttribute("aria-activedescendant");
  };
  const elegir = (o) => { input.value = ""; abrir(false); alElegir(o); };

  function pintar() {
    const q = normalizar(input.value.trim());
    const palabras = q.split(/\s+/).filter(Boolean);
    visibles = opciones.filter((o, i) => palabras.every((p) => indice[i].includes(p)));
    lista.replaceChildren();
    let grupo;
    visibles.forEach((o, i) => {
      if (o.grupo && o.grupo !== grupo) {
        grupo = o.grupo;
        const g = document.createElement("div"); g.className = "grupo"; g.setAttribute("role", "presentation");
        if (o.color) { const sw = document.createElement("span"); sw.className = "sw"; sw.style.background = o.color; g.append(sw); }
        g.append(document.createTextNode(o.grupo));
        lista.append(g);
      }
      const b = document.createElement("div"); b.className = "opc"; b.id = `${uid}-${i}`; b.setAttribute("role", "option");
      if (o.codigo) { const c = document.createElement("span"); c.className = "cod"; c.textContent = o.codigo; b.append(c); }
      b.append(document.createTextNode(o.etiqueta));
      b.addEventListener("mousedown", (e) => e.preventDefault());   // que el input no pierda el foco antes del clic
      b.addEventListener("click", () => elegir(o));
      lista.append(b);
    });
    if (!visibles.length) {
      const v = document.createElement("div"); v.className = "vacio"; v.textContent = "Sin resultados"; lista.append(v);
    }
    marcar(-1);
    abrir(true);
  }

  input.addEventListener("focus", pintar);
  input.addEventListener("input", pintar);
  input.addEventListener("blur", () => setTimeout(() => abrir(false), 120));
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (lista.hidden) pintar();
      const n = visibles.length;
      if (n) marcar(e.key === "ArrowDown" ? (activa + 1) % n : (activa - 1 + n) % n);
    } else if (e.key === "Enter") {
      e.preventDefault();
      const o = visibles[activa >= 0 ? activa : 0];
      if (o && !lista.hidden) elegir(o);
    } else if (e.key === "Escape") { abrir(false); }
  });
  caja.append(input, lista);
  contenedor.append(caja);
  return input;
}
