"""La web versiona sus CSS y JS (5_visualizacion/versionar.py) para que, tras publicar, el navegador no mezcle
ficheros nuevos con otros guardados en caché: si index.html no está al día, la web puede quedarse sin datos."""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_versiones_de_la_web_al_dia():
    r = subprocess.run([sys.executable, str(RAIZ / "5_visualizacion" / "versionar.py"), "--comprobar"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr or r.stdout
