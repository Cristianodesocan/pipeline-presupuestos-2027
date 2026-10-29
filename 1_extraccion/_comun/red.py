"""Sesión HTTP común: User-Agent identificable, reintentos y ritmo pausado."""
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = "ODESOCAN-presupuestos-2027/1.0 (+https://odesocan.org)"
PAUSA = 1.0          # segundos entre peticiones al mismo servidor
TIMEOUT = (10, 120)  # conexión, lectura

_ultima = 0.0


def sesion() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    reintentos = Retry(total=3, backoff_factor=2, status_forcelist=(500, 502, 503, 504),
                       allowed_methods=("GET", "HEAD"))
    s.mount("https://", HTTPAdapter(max_retries=reintentos))
    return s


def pausar() -> None:
    global _ultima
    espera = PAUSA - (time.monotonic() - _ultima)
    if espera > 0:
        time.sleep(espera)
    _ultima = time.monotonic()
