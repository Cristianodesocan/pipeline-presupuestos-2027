# Bloque Divi · Presupuestos de Canarias 2015-2027

Cómo meter la herramienta en una página de la web de Odesocan (WordPress + Divi).

## Por qué un iframe

La herramienta pesa unos 5 MB de datos (`data/*.csv`) y usa módulos JavaScript. Si se pegara el HTML directamente en
Divi, los estilos de la web y los de la herramienta se pisarían, y el editor de Divi altera algunos scripts. El bloque
carga la herramienta publicada en GitHub Pages dentro de un iframe que:

- **ajusta su altura al contenido**: no hay doble barra de desplazamiento, ni en móvil ni en escritorio;
- **tiene el fondo transparente**: toma el fondo de la sección de Divi, y además oculta el pie propio de la herramienta;
- **coloca el recorrido guiado** siempre en la parte visible de la ventana, y al pasar de clave desplaza la página
  hasta el gráfico, dejando sitio para el menú fijo;
- **conserva la vista en el enlace**: si alguien comparte `…/presupuestos/#tab=evolucion&dim=secciones`, la herramienta
  se abre en esa vista.

No pone cookies ni guarda nada en el navegador. La comunicación entre la página y el iframe solo acepta mensajes del
origen de la herramienta (`https://cristianodesocan.github.io`).

## Pasos

1. Edita la página con el Constructor de Divi.
2. Crea una **sección normal** con **una fila de una columna**.
3. Ajustes de la **fila** → Diseño → Tamaño:
   - **Usar ancho de canalón personalizado**: sí, valor **1**.
   - **Ancho**: **100 %** (en escritorio, tableta y móvil; en móvil Divi pone un 80 % por defecto y la herramienta
     quedaría estrecha).
   - **Ancho máximo**: **1280px**.
4. Ajustes de la **sección** → Diseño → Espaciado: relleno superior e inferior al gusto (p. ej. 40 px), **laterales a 0**
   (la herramienta ya trae 16 px de margen interior). Fondo: blanco o el gris de la web (`#F7F7F7`); la herramienta es
   transparente y se adapta a cualquiera de los dos.
5. Añade a la columna un módulo **Código** y pega **todo** el contenido de [`bloque-divi.html`](bloque-divi.html).
6. Guarda y comprueba en la vista previa: la altura debe ajustarse sola al cargar (si se queda en 1.800 px con barra
   interior, el script no se está ejecutando; revisa que se haya pegado en un módulo Código y no en uno de Texto).

## Ajustes del bloque

Están al principio del `<script>` de `bloque-divi.html`:

| Variable    | Para qué                                                                      | Valor   |
|-------------|-------------------------------------------------------------------------------|---------|
| `ORIGEN`    | Dominio de la herramienta. Si se publica en otro dominio, cámbialo aquí **y** en el `src` del iframe. | `https://cristianodesocan.github.io` |
| `MENU_FIJO` | Alto en px del menú fijo de la web; al desplazar, el gráfico queda justo debajo. | `90` |

El script no usa `&&`, `<` ni `>`, ni deja líneas en blanco, porque WordPress puede alterar esos caracteres al guardar.
Si lo modificas, mantén esa precaución.

## Probar sin Divi

`?incrustada` en la URL activa el aspecto de incrustada (sin fondo ni pie) aunque la página no esté dentro de un iframe:

```
https://cristianodesocan.github.io/pipeline-presupuestos-2027/5_visualizacion/?incrustada
```

## Qué cambia en la herramienta

- **Solo modo claro**: no hay botón de tema ni se sigue el modo oscuro del sistema.
- **Cabecera clara**: logo oficial en color, sobre fondo transparente.
- **Texto accesible**: cuerpo de 16 px; textos secundarios, leyendas, tablas y rótulos de los gráficos de 13-15 px
  (antes 10-12,5 px); controles de 40 px de alto (44 px en móvil).
- **Versión móvil (< 640 px)**:
  - el treemap pasa a ser una **lista de barras** ordenada, con el nombre y el peso en cada fila (con los mismos toques:
    ampliar una función o fijar una partida); se muestran las 15 primeras y el botón «Ver las N restantes». En secciones
    y entes las partidas van bajo el encabezado de su grupo (tocarlo muestra solo ese grupo); en programas, con 140
    partidas, se ve una fila por grupo;
  - los **filtros se pliegan** tras un botón que resume la selección («Funciones · 2027 (Proyecto) · Corrientes»);
  - el ranking pone el nombre de cada partida en su propia línea, sobre la barra;
  - el recorrido guiado aparece como una hoja inferior a todo lo ancho, y sus textos hablan de tocar, no de pasar el ratón.

## Si tras una actualización la herramienta no carga

Desde que los ficheros llevan versión (`versionar.py`) no debería pasar. Si se ve sin datos o con el aspecto anterior,
el navegador conserva ficheros de la versión previa: recarga forzando (Ctrl+Mayús+R; en Mac, Cmd+Mayús+R) o espera
10 minutos, que es lo que GitHub Pages deja guardarlos.
