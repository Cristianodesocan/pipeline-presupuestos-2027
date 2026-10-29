/* Estado de la vista en la URL (#tab=peso&dim=programas&anio=2026&precios=constantes…) para compartir vistas concretas. */

const POR_DEFECTO = { tab: "peso", dim: "funciones", vista: "", anio: "", precios: "corrientes", color: "categoria",
  medida: "importe", social: "0", zoom: "", sel: "" };
const VALIDOS = {
  tab: ["peso", "evolucion"], dim: ["funciones", "secciones", "programas", "entes"],
  precios: ["corrientes", "constantes"], color: ["categoria", "delta"], medida: ["importe", "var_pct", "indice_2015"], social: ["0", "1"],
};

export function leerEstado() {
  const p = new URLSearchParams(location.hash.slice(1));
  const e = { ...POR_DEFECTO };
  for (const k of Object.keys(POR_DEFECTO)) {
    const v = p.get(k);
    if (v != null && (!VALIDOS[k] || VALIDOS[k].includes(v))) e[k] = v;
  }
  // selección de series: posición = ranura de color (los huecos se conservan para no repintar a nadie)
  e.sel = e.sel ? e.sel.split("~").map((x) => x || null).slice(0, 7) : null;
  e.zoom = e.zoom ? e.zoom.split("~") : [];
  return e;
}

export function escribirEstado(e) {
  const p = new URLSearchParams();
  for (const k of Object.keys(POR_DEFECTO)) {
    let v = e[k];
    if (k === "sel") v = Array.isArray(v) ? v.map((x) => x || "").join("~").replace(/~+$/, "") : "";
    if (k === "zoom") v = (v || []).join("~");
    if (v != null && v !== "" && v !== POR_DEFECTO[k]) p.set(k, v);
  }
  const h = p.toString();
  history.replaceState(null, "", h ? `#${h}` : location.pathname + location.search);
}
