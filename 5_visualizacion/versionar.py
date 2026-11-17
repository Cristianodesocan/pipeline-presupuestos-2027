"""Pone a cada CSS y JS de la web una versión (huella de su contenido) para que el navegador no mezcle ficheros nuevos
con otros guardados en caché de una versión anterior.

GitHub Pages deja guardar cada fichero 10 minutos (cache-control: max-age=600). Sin versión, tras publicar un cambio
el navegador puede usar el index.html nuevo con el app.js o el CSS antiguos, y la web se queda sin datos o con el
aspecto anterior. Con versión, cada cambio de contenido cambia la URL y obliga a descargar el fichero.

    python 5_visualizacion/versionar.py               # actualiza index.html (ejecutar tras tocar css/ o js/)
    python 5_visualizacion/versionar.py --comprobar   # sale con error si index.html no está al día (lo usa el test)

Qué escribe en index.html:
  - css/odesocan.css?v=… y js/app.js?v=… en sus etiquetas;
  - un mapa de importación (<script type="importmap">) que da versión a los módulos que importa app.js: así los
    import "./comun.js" de los módulos no hay que tocarlos. Los navegadores sin mapas de importación (anteriores a
    2023) lo ignoran y cargan los módulos sin versión: la web funciona igual, solo sin esta protección.
Solo usa la biblioteca estándar.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parent
INDEX = WEB / "index.html"
INICIO, FIN = "<!-- versiones:inicio -->", "<!-- versiones:fin -->"


def huella(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()[:10]


def versionar(html: str) -> str:
    css = WEB / "css" / "odesocan.css"
    modulos = sorted((WEB / "js").glob("*.js"))
    html = re.sub(r'href="css/odesocan\.css(\?v=[0-9a-f]+)?"', f'href="css/odesocan.css?v={huella(css)}"', html)
    html = re.sub(r'src="js/app\.js(\?v=[0-9a-f]+)?"', f'src="js/app.js?v={huella(WEB / "js" / "app.js")}"', html)
    mapa = {"imports": {f"./js/{m.name}": f"./js/{m.name}?v={huella(m)}" for m in modulos if m.name != "app.js"}}
    bloque = (f'{INICIO}\n  <script type="importmap">\n  {json.dumps(mapa, ensure_ascii=False)}\n  </script>\n  {FIN}')
    if INICIO in html:
        return re.sub(re.escape(INICIO) + r".*?" + re.escape(FIN), lambda _: bloque, html, flags=re.S)
    # primera vez: el mapa tiene que ir antes del primer <script type="module">
    return html.replace('  <script type="module"', f"  {bloque}\n  <script type=\"module\"", 1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--comprobar", action="store_true", help="no escribe; error si index.html no está al día")
    args = ap.parse_args()
    actual = INDEX.read_text(encoding="utf-8")
    nuevo = versionar(actual)
    if args.comprobar:
        if nuevo != actual:
            sys.exit("index.html no tiene las versiones al día: ejecuta python 5_visualizacion/versionar.py")
        print("index.html: versiones al día")
        return
    if nuevo != actual:
        INDEX.write_text(nuevo, encoding="utf-8")
        print("index.html actualizado")
    else:
        print("index.html ya estaba al día")


if __name__ == "__main__":
    main()
