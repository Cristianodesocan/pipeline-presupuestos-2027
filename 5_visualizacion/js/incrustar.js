/* Modo incrustado: la herramienta vive en un iframe del bloque Divi (divi/bloque-divi.html) que crece con su contenido.
   Mensajes (postMessage, objeto con fuente "odesocan-presupuestos"):
     iframe → página   { tipo: "altura", valor }        alto del contenido en px: la página ajusta el iframe
                       { tipo: "desplazar", y }         llevar a la vista el punto y (px desde arriba del iframe)
                       { tipo: "estado", hash }         estado de la vista, para que el enlace de la página lo conserve
     página → iframe   { tipo: "vista", fin }           px desde arriba del iframe hasta el borde inferior de la ventana:
                                                        ahí se apoya el recorrido guiado (en un iframe sin scroll,
                                                        «position: fixed» quedaría al final del documento)
   Ningún mensaje lleva datos personales; la página solo acepta los que llegan del origen de la herramienta. */

const FUENTE = "odesocan-presupuestos";
export const incrustada = document.documentElement.classList.contains("incrustada") && window.parent !== window;

const enviar = (tipo, datos) => { if (incrustada) window.parent.postMessage({ fuente: FUENTE, tipo, ...datos }, "*"); };

export function iniciarIncrustacion() {
  if (!incrustada) return;
  let ultima = 0;
  const medir = () => {
    const alto = Math.ceil(document.body.getBoundingClientRect().height);
    if (alto !== ultima) { ultima = alto; enviar("altura", { valor: alto }); }
  };
  new ResizeObserver(medir).observe(document.body);
  addEventListener("load", medir);
  medir();
  addEventListener("message", (e) => {
    const m = e.data;
    if (e.source !== window.parent || !m || m.fuente !== `${FUENTE}-pagina`) return;
    if (m.tipo === "vista" && Number.isFinite(m.fin)) {
      const fin = Math.max(0, Math.min(m.fin, document.body.scrollHeight));
      document.documentElement.style.setProperty("--vista-fin", `${Math.round(fin)}px`);
    }
  });
  enviar("lista", {});
}

/** Lleva un elemento a la vista: en el iframe lo hace la página (scrollIntoView no siempre cruza el iframe). */
export function desplazarElemento(el) {
  if (!el) return;
  if (incrustada) { enviar("desplazar", { y: Math.round(el.getBoundingClientRect().top + window.scrollY) }); return; }
  el.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
}

export function comunicarEstado(hash) { enviar("estado", { hash }); }
