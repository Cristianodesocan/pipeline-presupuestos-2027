"""Sirve la web en http://localhost y la abre en el navegador.

    python 5_visualizacion/servir.py              # puerto 8027 (o el siguiente libre)
    python 5_visualizacion/servir.py --puerto 9000 --sin-abrir

Abrir index.html con doble clic (file://) no funciona: el navegador bloquea los módulos JS y la lectura
de data/*.csv fuera de un servidor. Ctrl+C para parar.
"""
import argparse
import functools
import http.server
import socket
import webbrowser
from pathlib import Path

WEB = Path(__file__).resolve().parent


def puerto_libre(desde: int) -> int:
    for p in range(desde, desde + 50):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    raise SystemExit(f"No hay puertos libres entre {desde} y {desde + 49}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--puerto", type=int, default=8027)
    ap.add_argument("--sin-abrir", action="store_true")
    args = ap.parse_args()

    puerto = puerto_libre(args.puerto)
    manejador = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(WEB))
    with http.server.ThreadingHTTPServer(("127.0.0.1", puerto), manejador) as srv:
        url = f"http://localhost:{puerto}/"
        print(f"Web en {url} (Ctrl+C para parar)")
        if not args.sin_abrir:
            webbrowser.open(url)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor parado.")


if __name__ == "__main__":
    main()
