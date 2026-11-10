/* Auditoría nivel 4: lo que MUESTRA la web frente a lo que debería mostrar (calculado en Python por auditar_datos.py).
   Abre la web real en un navegador sin ventana (Playwright), recorre combinaciones de filtros y lee la pantalla:
   tablas de la pestaña Peso, donut, tooltip, «Sigue el dinero», ranking, tabla de Evolución (por habitante y % del PIB),
   recorrido guiado y el CSV descargado. Compara cada cifra con la esperada dentro de la precisión con que se muestra.

     .venv/bin/python auditoria/auditar_datos.py   # antes: genera auditoria/resultados_datos.json
     node auditoria/auditar_web.cjs                 # requiere Playwright (npm i -D playwright; npx playwright install chromium)

   Salida: auditoria/resultados_web.json. Código 0 sin diferencias; 1 si hay alguna. */
const fs = require("fs");
const http = require("http");
const path = require("path");
const { chromium } = require("playwright");

const RAIZ = path.resolve(__dirname, "..");
const WEB = path.join(RAIZ, "5_visualizacion");
const { esperado } = JSON.parse(fs.readFileSync(path.join(__dirname, "resultados_datos.json"), "utf8"));
const resultados = [];

/* ---------- utilidades */
const TIPOS = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".csv": "text/csv", ".json": "application/json", ".svg": "image/svg+xml" };
function servir() {
  return new Promise((ok) => {
    const s = http.createServer((req, res) => {
      const ruta = path.join(WEB, decodeURIComponent(req.url.split("?")[0].split("#")[0]).replace(/\/$/, "/index.html"));
      if (!ruta.startsWith(WEB) || !fs.existsSync(ruta)) { res.writeHead(404); return res.end(); }
      res.writeHead(200, { "Content-Type": TIPOS[path.extname(ruta)] || "application/octet-stream" });
      fs.createReadStream(ruta).pipe(res);
    }).listen(0, "127.0.0.1", () => ok(s));
  });
}
/** «+4.542,9 M€» → 4542.9 ; «−22,1» → -22.1 ; «38,15 %» → 38.15. Devuelve { v, dec } (dec = decimales mostrados). */
function num(t) {
  if (t == null) return null;
  const limpio = String(t).replace(/[▲▼\s]|M€|€|%|pp/g, "").replace("−", "-").replace("+", "");
  if (!/^-?[\d.]+(,\d+)?$/.test(limpio)) return null;
  const dec = limpio.includes(",") ? limpio.split(",")[1].length : 0;
  return { v: parseFloat(limpio.replace(/\./g, "").replace(",", ".")), dec };
}
const cerca = (mostrado, esperado, escala = 1) => {
  if (mostrado == null || esperado == null) return mostrado == null && esperado == null;
  return Math.abs(mostrado.v - esperado / escala) <= 0.5 * 10 ** -mostrado.dec + 1e-9;
};
function registrar(id, titulo, comprobados, fallos) {
  const estado = fallos.length ? "ERROR" : "OK";
  resultados.push({ nivel: 4, id, titulo, comprobados, fallos: fallos.length, estado, ejemplos: fallos.slice(0, 6) });
  console.log(`  ${fallos.length ? "✘" : "✔"} [${id}] ${titulo}: ${comprobados} comprobados, ${fallos.length} con diferencia`);
  fallos.slice(0, 3).forEach((f) => console.log(`        ${f}`));
}

(async () => {
  const servidor = await servir();
  const URL = `http://127.0.0.1:${servidor.address().port}/index.html`;
  const navegador = await chromium.launch(process.env.HTTPS_PROXY
    ? { proxy: { server: process.env.HTTPS_PROXY, bypass: "127.0.0.1,localhost" } } : {});
  const ctx = await navegador.newContext({ viewport: { width: 1280, height: 900 }, ignoreHTTPSErrors: true, acceptDownloads: true });
  const page = await ctx.newPage();
  const erroresJs = [];
  page.on("pageerror", (e) => erroresJs.push(e.message));
  page.on("console", (m) => { if (m.type() === "error") erroresJs.push(m.text()); });
  let n = 0;
  const ir = async (hash, espera = "#treemap svg, #lineas svg") => {
    await page.goto(`${URL}?a=${++n}#${hash}`, { waitUntil: "networkidle" });
    await page.waitForSelector(espera, { timeout: 30000 });
  };
  const DIM = { funcion: "funciones", seccion: "secciones", programa: "programas", ente: "entes" };

  /* D1 · tablas de la pestaña Peso */
  {
    let c = 0; const f = [];
    for (const [clave, filas] of Object.entries(esperado.tablas_peso)) {
      const [dim, vista, anio, precios] = clave.split("|");
      const v = dim === "funcion" || dim === "ente" ? "" : `&vista=${vista}`;
      await ir(`dim=${DIM[dim]}${v}&anio=${anio}&precios=${precios}`);
      await page.click("#ver-tabla-peso");
      const tabla = await page.$$eval("#tabla-peso table", (ts) => {
        const t = ts[0];
        const cab = [...t.tHead.rows[0].cells].map((c) => c.textContent);
        return { cab, filas: [...t.tBodies[0].rows].map((r) => [...r.cells].map((c) => c.textContent)) };
      });
      const col = (n) => tabla.cab.indexOf(n);
      const esperadas = Object.keys(filas).length;
      if (tabla.filas.length !== esperadas) f.push(`${clave}: ${tabla.filas.length} filas en pantalla y ${esperadas} en los datos`);
      for (const fila of tabla.filas) {
        const e = filas[fila[0]];
        c++;
        if (!e) { f.push(`${clave}: «${fila[0]}» no está en los datos`); continue; }
        const ver = [["Importe (M€)", e.importe, 1e6], ["Peso total", e.peso, 1], ["Var. interanual (M€)", e.var_eur, 1e6], ["Var. interanual (%)", e.var_pct, 1]];
        for (const [nombre, valor, escala] of ver) {
          const m = num(fila[col(nombre)]);
          if (!cerca(m, valor, escala)) f.push(`${clave} «${fila[0]}» ${nombre}: pantalla ${fila[col(nombre)]} · esperado ${valor == null ? "—" : (valor / escala).toFixed(3)}`);
        }
      }
    }
    registrar("D1", `Tablas de la pestaña Peso (${Object.keys(esperado.tablas_peso).length} combinaciones de dimensión, vista, año y precios)`, c, f);
  }

  /* D2 · donut sin selección: importe y % de cada capítulo */
  {
    let c = 0; const f = [];
    for (const [clave, caps] of Object.entries(esperado.donut_raiz)) {
      const [dim, anio, precios] = clave.split("|");
      await ir(`dim=${DIM[dim]}&anio=${anio}&precios=${precios}`, "#donut svg");
      const lista = await page.$$eval(".lista-caps li", (ls) => ls.map((l) => [...l.children].map((x) => x.textContent)));
      const total = [1, 2, 3, 4, 6, 7, 8].reduce((s, k) => s + caps[k], 0);
      const centro = num(await page.$eval("#donut svg text", (t) => t.textContent));
      c++;
      if (!cerca(centro, total, 1e6)) f.push(`${clave}: total en el centro ${centro && centro.v} · esperado ${(total / 1e6).toFixed(1)}`);
      for (const fila of lista) {
        const cap = +(/Cap\. (\d)/.exec(fila[1]) || [])[1];
        const imp = num(fila[2]), pct = num(fila[3]);
        c += 2;
        if (!cerca(imp, caps[cap], 1e6)) f.push(`${clave} cap. ${cap}: ${fila[2]} · esperado ${(caps[cap] / 1e6).toFixed(2)} M€`);
        if (!cerca(pct, (100 * caps[cap]) / total)) f.push(`${clave} cap. ${cap}: ${fila[3]} · esperado ${((100 * caps[cap]) / total).toFixed(2)} %`);
      }
      const nota = await page.$eval("#nota-donut", (p) => p.textContent);
      const c9 = num((/Además, ([\d.,]+ M€) en el capítulo 9/.exec(nota) || [])[1]);
      c++;
      if (caps[9] > 0.05e6 ? !cerca(c9, caps[9], 1e6) : c9 != null) f.push(`${clave} cap. 9: nota «${nota.slice(0, 60)}» · esperado ${(caps[9] / 1e6).toFixed(1)} M€`);
    }
    registrar("D2", "Donut por capítulos sin selección (total del centro, importe y % de cada capítulo y nota del cap. 9)", c, f);
  }

  /* D3 · tooltip de la celda mayor de cada dimensión */
  {
    let c = 0; const f = [];
    for (const dim of ["funcion", "seccion", "programa", "ente"]) {
      const vista = { funcion: "individual", seccion: "organica", programa: "individual", ente: "individual" }[dim];
      await ir(`dim=${DIM[dim]}&anio=2026`);
      const hoja = page.locator("#treemap g.hoja").first();
      await hoja.hover({ position: { x: 20, y: 20 } });
      await page.waitForTimeout(120);
      const tt = await page.$eval("#tooltip", (t) => ({ titulo: t.querySelector(".tt").textContent,
        filas: [...t.querySelectorAll(".fila")].map((r) => [r.querySelector(".k").textContent, r.querySelector("b").textContent]) }));
      const e = esperado.tablas_peso[`${dim}|${vista}|2026|corrientes`][tt.titulo];
      c++;
      if (!e) { f.push(`${dim}: «${tt.titulo}» no está en los datos`); continue; }
      const val = Object.fromEntries(tt.filas);
      for (const [k, valor, escala] of [["Importe", e.importe, 1e6], ["Peso sobre el total", e.peso, 1], ["Var. interanual (€)", e.var_eur, 1e6], ["Var. interanual (%)", e.var_pct, 1]]) {
        c++;
        if (!cerca(num(val[k]), valor, escala)) f.push(`${dim} «${tt.titulo}» ${k}: ${val[k]} · esperado ${(valor / escala).toFixed(3)}`);
        const signo = val[k] && (val[k].includes("▲") ? 1 : val[k].includes("▼") ? -1 : 0);
        if (k.startsWith("Var.") && valor && signo !== Math.sign(valor)) f.push(`${dim} «${tt.titulo}» ${k}: flecha ${val[k]} no corresponde al signo`);
      }
    }
    registrar("D3", "Tooltip de la mayor partida de cada dimensión (importe, peso, variación € y %, flecha verde/roja)", c, f);
  }

  /* D4 · «Sigue el dinero» de la sección 14 Sanidad */
  {
    const e = esperado.flujo_s14; const f = [];
    await ir(`dim=secciones&vista=organica&anio=${e.anio}&foco=S14_2015`, "#flujo svg");
    const etiqueta = await page.$eval("#flujo svg", (s) => s.getAttribute("aria-label"));
    const tr = num((/de los que ([\d.,]+ M€) son transferencias/.exec(etiqueta) || [])[1]);
    const scs = num((/Servicio Canario de la Salud \(SCS\) gasta ([\d.,]+ M€)/.exec(etiqueta) || [])[1]);
    if (!cerca(tr, e.transferencias, 1e6)) f.push(`transferencias: «${etiqueta.slice(0, 120)}» · esperado ${(e.transferencias / 1e6).toFixed(0)} M€`);
    if (!cerca(scs, e.scs_gasto, 1e6)) f.push(`gasto del SCS: «${etiqueta.slice(0, 160)}» · esperado ${(e.scs_gasto / 1e6).toFixed(0)} M€`);
    registrar("D4", `«Sigue el dinero» de Sanidad (14) en ${e.anio}: transferencias y gasto del SCS en las mismas subfunciones`, 2, f);
  }

  /* D5 · ranking «¿qué ha cambiado?» */
  {
    let c = 0; const f = [];
    for (const [clave, rk] of Object.entries(esperado.ranking)) {
      const [dim, vista, desde, hasta] = clave.split("|");
      await ir(`tab=evolucion&dim=${DIM[dim]}${dim === "programa" ? `&vista=${vista}` : ""}&desde=${desde}&hasta=${hasta}`, "#ranking svg");
      const filas = await page.$$eval("#ranking svg g[role=button]", (gs) => gs.map((g) => [...g.querySelectorAll("text")].map((t) => t.textContent)));
      const lista = [...rk.suben, ...rk.bajan];
      if (filas.length !== lista.length) f.push(`${clave}: ${filas.length} barras · esperado ${lista.length}`);
      lista.forEach((e, i) => {
        const [nombre, valores] = filas[i] || [];
        c++;
        const base = (nombre || "").replace("…", "");
        if (!e.etiqueta.startsWith(base)) f.push(`${clave} puesto ${i + 1}: «${nombre}» · esperado «${e.etiqueta}»`);
        const [eur, pct] = (valores || "").split(" · ");
        if (!cerca(num(eur), e.dif, 1e6)) f.push(`${clave} «${e.etiqueta}»: ${eur} · esperado ${(e.dif / 1e6).toFixed(1)} M€`);
        if (pct && e.pct != null && !cerca(num(pct), e.pct)) f.push(`${clave} «${e.etiqueta}»: ${pct} · esperado ${e.pct.toFixed(1)} %`);
      });
    }
    registrar("D5", "Ranking «¿qué ha cambiado?» 2023→último año (orden, diferencia en € y en %)", c, f);
  }

  /* D6 · tabla de Evolución: € por habitante y % del PIB */
  {
    let c = 0; const f = [];
    for (const [medida, precios, clave] of [["por_habitante", "constantes", "por_habitante|constantes"], ["por_habitante", "corrientes", "por_habitante|corrientes"], ["pct_pib", "corrientes", "pct_pib"]]) {
      await ir(`tab=evolucion&dim=funciones&medida=${medida}&precios=${precios}`, "#lineas svg");
      await page.click("#ver-tabla-evo");
      const t = await page.$eval("#tabla-evo table", (t) => ({ cab: [...t.tHead.rows[0].cells].map((c) => c.textContent),
        filas: [...t.tBodies[0].rows].map((r) => [...r.cells].map((c) => c.textContent)) }));
      for (const fila of t.filas) {
        t.cab.slice(1).forEach((anio, j) => {
          const e = esperado.evolucion[clave][`${fila[0]}|${anio}`];
          const m = num(fila[j + 1]);
          c++;
          if (e == null ? m != null : !cerca(m, e)) f.push(`${clave} «${fila[0]}» ${anio}: ${fila[j + 1]} · esperado ${e == null ? "—" : e.toFixed(2)}`);
        });
      }
    }
    registrar("D6", "Tabla de Evolución en € por habitante (corrientes y constantes) y % del PIB", c, f);
  }

  /* D7 · recorrido guiado: las cifras de cada clave */
  {
    const r = esperado.recorrido; const f = []; let c = 0;
    await ir("", "#treemap svg");
    await page.click("#abrir-recorrido"); await page.waitForTimeout(400);
    const textos = [];
    for (let i = 0; i < 5; i++) {
      textos.push(await page.$eval("#recorrido", (p) => p.querySelector("h3").textContent + " | " + p.querySelector("p").textContent));
      if (i < 4) { await page.click("#recorrido .btn.primario"); await page.waitForTimeout(400); }
    }
    const cifras = (t) => [...t.matchAll(/[+−-]?\d[\d.]*(?:,\d+)?(?= ?(?:%|M€|€))/g)].map((m) => num(m[0]));
    const comprobar = (i, nombre, valor, escala = 1) => {
      c++;
      if (!cifras(textos[i]).some((m) => cerca(m, valor, escala))) f.push(`clave ${i + 1} ${nombre}: esperado ${(valor / escala).toFixed(2)} en «${textos[i].slice(0, 160)}»`);
    };
    comprobar(0, "Sanidad %", r.clave1.sanidad); comprobar(0, "Educación %", r.clave1.educacion); comprobar(0, "suma %", r.clave1.suma);
    comprobar(0, "transferencias %", r.clave1.transferencias); comprobar(0, "servicios sociales %", r.clave1.sociales);
    comprobar(1, "transferencias de Sanidad %", r.clave2.transferencias_pct);
    comprobar(2, "personal SCS %", r.clave3.personal_pct); comprobar(2, "personal SCS M€", r.clave3.personal, 1e6);
    comprobar(2, "bienes SCS %", r.clave3.bienes_pct); comprobar(2, "personal inicio M€", r.clave3.personal_inicio, 1e6);
    comprobar(3, "mayor subida M€", r.clave4.sube.dif, 1e6);
    if (r.clave4.baja) comprobar(3, "mayor bajada M€", r.clave4.baja.dif, 1e6);
    comprobar(4, "€/hab. inicio", r.clave5.inicio); comprobar(4, "€/hab. fin", r.clave5.fin); comprobar(4, "variación %", r.clave5.var_pct);
    c++;
    if (!textos[3].includes(r.clave4.sube.etiqueta)) f.push(`clave 4: no nombra «${r.clave4.sube.etiqueta}»`);
    registrar("D7", "Recorrido guiado: cifras y nombres de las 5 claves", c, f);
  }

  /* D8 · CSV descargado = tabla en pantalla */
  {
    const f = [];
    await ir("dim=programas&anio=2026");
    const [descarga] = await Promise.all([page.waitForEvent("download"), page.click("#csv-peso")]);
    const csv = fs.readFileSync(await descarga.path(), "utf8").replace(/^﻿/, "").trim().split("\n");
    const e = esperado.tablas_peso["programa|individual|2026|corrientes"];
    if (csv.length - 1 !== Object.keys(e).length) f.push(`CSV con ${csv.length - 1} filas · esperado ${Object.keys(e).length}`);
    const cab = csv[0].split(",");
    const iImp = cab.indexOf("Importe (M€)");
    if (iImp < 0) f.push("el CSV no tiene la columna «Importe (M€)»");
    registrar("D8", "CSV descargado de la pestaña Peso (programas 2026): una fila por partida", 1, f);
  }

  registrar("D9", "Sin errores de JavaScript durante toda la auditoría", 1, erroresJs.map((e) => e.slice(0, 160)));
  fs.writeFileSync(path.join(__dirname, "resultados_web.json"), JSON.stringify(resultados, null, 1));
  await navegador.close(); servidor.close();
  const errores = resultados.filter((r) => r.estado === "ERROR").length;
  console.log(`\n${resultados.length} comprobaciones en pantalla · ${errores} con diferencias → auditoria/resultados_web.json`);
  process.exit(errores ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
