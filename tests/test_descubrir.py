"""Descubrimiento de enlaces sin red, con HTML que reproduce la maqueta del portal."""
from descubrir_fuentes import candidatas, enlaces_tomo3, fase_de

BASE = "https://www.gobiernodecanarias.org/cmsgob1/export/sites/hacienda/planificacionypresupuesto/galeria/Presupuestos/"
PAGINA = "https://www.gobiernodecanarias.org/hacienda/planificacionypresupuesto/presupuestos/2027/index.html"

HTML = """
<h2>Año Presupuestario 2027</h2>
<h3>Ley de Presupuestos de la Comunidad Autónoma Canaria 2027</h3>
<a href="/cmsgob1/export/sites/hacienda/planificacionypresupuesto/galeria/Presupuestos/2027/ley/TOMO-3-Resumenes.pdf">Resúmenes</a>
<h3>Resumen Gráfico de la Ley de Presupuestos de la CAC 2027</h3>
<a href="/x/resumen-grafico.pdf">Resumen Gráfico</a>
<h3>Proyecto de Ley de Presupuestos de la Comunidad Autónoma Canaria 2027</h3>
<a href="/cmsgob1/export/sites/hacienda/planificacionypresupuesto/galeria/Presupuestos/2027/TOMO-3-Resumenes.pdf">TOMO 3 : Resúmenes</a>
<h3>Límite de gasto no financiero para 2027</h3>
<a href="/x/limite.pdf">Límite de gasto</a>
"""


def test_fase_por_encabezado():
    assert fase_de("Proyecto de Ley de Presupuestos de la Comunidad Autónoma Canaria 2027") == "proyecto"
    assert fase_de("Ley de Presupuestos de la Comunidad Autónoma Canaria 2027") == "ley"
    assert fase_de("Límite de gasto no financiero para 2027") is None


def test_enlaces_tomo3():
    enlaces = enlaces_tomo3(HTML, PAGINA)
    assert [(e["fase"], e["url"].split("Presupuestos/")[1]) for e in enlaces] == [
        ("ley", "2027/ley/TOMO-3-Resumenes.pdf"),
        ("proyecto", "2027/TOMO-3-Resumenes.pdf"),
    ]


def test_candidatas_reparan_enlace_2024():
    roto = "https://www.gobiernodecanarias.org/hacienda/planificacionypresupuesto/galeria/Presupuestos/2024/ley/TOMO-3-Resumenes.html"
    assert BASE + "2024/ley/TOMO-3-Resumenes.pdf" in candidatas(roto, BASE)
