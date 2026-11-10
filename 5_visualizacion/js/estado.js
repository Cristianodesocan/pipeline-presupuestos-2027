/* Estado de la vista en la URL (#tab=peso&dim=programas&anio=2026&precios=constantes&foco=P312F_2015…)
   para compartir vistas concretas. */

const POR_DEFECTO = { tab: "peso", dim: "funciones", vista: "", anio: "", precios: "corrientes", color: "categoria",
  medida: "importe", social: "0", zoom: "", sel: "", foco: "", desde: "", hasta: "", paso: "" };
const VALIDOS = {
  tab: ["peso", "evolucion"], dim: ["funciones", "secciones", "programas", "entes"],
  precios: ["corrientes", "constantes"], color: ["categoria", "delta"], medida: ["importe", "por_habitante", "pct_pib", "var_pct"], social: ["0", "1"],
  paso: ["1", "2", "3", "4", "5"],
};

export function leerEstado() {
  const p = new URLSearchParams(location.hash.slice(1));
  const e = { ...POR_DEFECTO };
  for (const k of Object.keys(POR_DEFECTO)) {
    const v = p.get(k);
    if (v == null) continue;
    if ((k === "desde" || k === "hasta" || k === "anio") && !/^\d{4}$/.test(v)) continue;
    if (!VALIDOS[k] || VALIDOS[k].includes(v)) e[k] = v;
  }
  // selección de series: posición = ranura de color (los huecos se conservan para no repintar a nadie)
  e.sel = e.sel ? e.sel.split("~").map((x) => x || null).slice(0, 7) : null;
  e.zoom = e.zoom ? e.zoom.split("~") : [];
  e.foco = e.foco || null;     // partida fijada en el donut de capítulos (pestaña Peso)
  return e;
}

/** Estado limpio (lo usa el recorrido guiado antes de aplicar cada paso). */
export function estadoBase() {
  return { ...POR_DEFECTO, zoom: [], sel: null, foco: null };
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
