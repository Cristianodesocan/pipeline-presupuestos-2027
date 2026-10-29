"""Conversión de cifras en formato es-ES tal como aparecen en el Tomo 3.

    4.536.754.790 -> 4536754790 (int)      38,09   -> 38.09
    0,71-         -> -0.71                 100,00- -> -100.0
    0             -> 0  (cero NO es vacío)  -       -> None
    110,02*       -> 110.02 con asterisco («el porcentaje es superior al 10.000 %»)
"""
import re

RE_NUMERO = re.compile(
    r"^-?(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d+)?-?\*?$"  # miles con punto o sin separador, decimales con coma
)


def es_numero(token: str) -> bool:
    """True si el token es una cifra (o el guion de celda vacía)."""
    return token == "-" or bool(RE_NUMERO.match(token))


def a_numero(token: str) -> tuple[int | float | None, bool]:
    """Devuelve (valor, asterisco). Enteros si no hay coma decimal."""
    t = token.strip()
    asterisco = t.endswith("*")
    t = t.rstrip("*")
    if t in ("", "-"):
        return None, asterisco
    if not RE_NUMERO.match(t):
        raise ValueError(f"No es una cifra es-ES: {token!r}")
    negativo = t.startswith("-") or t.endswith("-")
    t = t.strip("-")
    if "," in t:
        valor = float(t.replace(".", "").replace(",", "."))
    else:
        valor = int(t.replace(".", ""))
    return (-valor if negativo else valor), asterisco
