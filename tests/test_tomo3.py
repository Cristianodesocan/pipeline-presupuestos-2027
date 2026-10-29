"""Tests del motor contra los PDF reales (diseno_extraccion_tomo3.md §8).

Se omiten si el tomo no está descargado (python 1_extraccion/descargar_tomos.py).
"""
import pytest
import yaml

from _comun.portada import leer_portada
from _comun.rutas import CONFIG
from _comun.tomo3 import leer_indice, parsear_tabla

REF = yaml.safe_load((CONFIG / "referencias_tomo3.yml").read_text(encoding="utf-8"))


def tabla(abrir_pdf, cfg, anio, id_tabla, fase="ley"):
    pdf = abrir_pdf(anio, fase)
    return parsear_tabla(pdf, leer_indice(pdf), cfg["tablas"][id_tabla])


def detalle(filas, codigo, padre=None):
    out = [f for f in filas if f.nivel == "detalle" and f.codigo == codigo and (padre is None or f.padre == padre)]
    assert len(out) == 1, f"{codigo}: {len(out)} filas"
    return out[0]


def total(filas):
    return [f for f in filas if f.nivel == "total"][-1]


@pytest.mark.parametrize("fase, anio, esperado",
                         [(f, a, v) for f, d in REF["total_programas_inicial"].items() for a, v in d.items()])
def test_totales_210(abrir_pdf, cfg, fase, anio, esperado):
    filas, _ = tabla(abrir_pdf, cfg, anio, "programas", fase)
    assert total(filas).valores["inicial"] == esperado
    assert sum(f.valores.get("inicial") or 0 for f in filas if f.nivel == "detalle") == esperado


def test_312A_2015(abrir_pdf, cfg):
    filas, _ = tabla(abrir_pdf, cfg, 2015, "programas")
    assert detalle(filas, "312A").valores["inicial"] == 2_454_229_799


def test_programa_extinguido_es_cero(abrir_pdf, cfg):
    """261B 2026: inicial 0 (CED le asignaba el ajustado de 2025)."""
    filas, _ = tabla(abrir_pdf, cfg, 2026, "programas")
    f = detalle(filas, "261B")
    assert f.valores["inicial"] == 0
    assert f.valores["ajustado_prev"] == 1_000_000


def test_celda_vacia_no_desplaza(abrir_pdf, cfg):
    """231D 2026: ajustado 0 sin variación; el resto no se desplaza."""
    filas, _ = tabla(abrir_pdf, cfg, 2026, "programas")
    f = detalle(filas, "231D")
    assert f.valores["ajustado_prev"] == 0
    assert f.valores["inicial"] == 16_167_596
    assert "var_pct" not in f.valores


@pytest.mark.parametrize("anio", [2016, 2018])
def test_pagina_solo_total(abrir_pdf, cfg, anio):
    """Las anclas por tabla evitan el desplazamiento de la última página con solo la fila TOTAL."""
    filas, cont = tabla(abrir_pdf, cfg, anio, "programas")
    assert total(filas).valores["inicial"] == REF["total_programas_inicial"]["ley"][anio]
    assert cont["tokens_fuera_ancla"] == 0


def test_entes_grupos_y_porcentaje_con_espacio(abrir_pdf, cfg):
    filas, _ = tabla(abrir_pdf, cfg, 2026, "entes")
    grupos = [f for f in filas if f.nivel == "grupo"]
    assert len(grupos) == 4
    assert len([f for f in filas if f.nivel == "detalle"]) == 15
    t = total(filas)
    assert t.valores["pct_inicial"] == 100.0 and t.valores["inicial"] == 5_608_176_929
    assert detalle(filas, "SCS").padre == "Organismos Autónomos"


def test_912A_por_seccion(abrir_pdf, cfg):
    filas, _ = tabla(abrir_pdf, cfg, 2026, "secc_prog_cap")
    f912 = [f for f in filas if f.nivel == "detalle" and f.codigo == "912A"]
    assert len(f912) == 13
    assert len({f.padre for f in f912}) == 13


def test_primera_fila_tras_cabecera(abrir_pdf, cfg):
    filas, _ = tabla(abrir_pdf, cfg, 2026, "secciones_cap")
    assert detalle(filas, "05").valores["cap_9"] == 646_436_058


def test_denominacion_partida(abrir_pdf, cfg):
    filas, _ = tabla(abrir_pdf, cfg, 2026, "secciones_cap")
    assert detalle(filas, "13").denominacion == "AGRICULTURA,GANADERÍA,PESCA Y SOBERNÍA ALIMENTARIA"
    assert detalle(filas, "08").denominacion == "CONSEJ. PRESIDENCIA, ADMONES. PÚBL.,JUSTICIA Y SEG"


def test_ente_desde_cabecera(abrir_pdf, cfg):
    filas, _ = tabla(abrir_pdf, cfg, 2026, "entes_prog_cap")
    scs = [f for f in filas if f.ente == "Servicio Canario de la Salud" and f.nivel == "total"]
    assert len(scs) == 1 and scs[0].valores["total"] == 4_833_515_057


def test_indice_2015_con_pag(abrir_pdf):
    indice = leer_indice(abrir_pdf(2015))
    assert len(indice) == 25 and indice["2.10"][1] == 47


@pytest.mark.parametrize("fase", ["proyecto", "ley"])
def test_portada_fase(abrir_pdf, fase):
    p = leer_portada(abrir_pdf(2026, fase))
    assert (p["fase"], p["anio"], p["tomo"]) == (fase, 2026, 3)


def test_perimetros(abrir_pdf, cfg):
    """Caps. 1-8 (comparativas) frente a 1-9 (tablas por capítulos): la diferencia es el cap. 9."""
    progs, _ = tabla(abrir_pdf, cfg, 2026, "programas")
    caps, _ = tabla(abrir_pdf, cfg, 2026, "secciones_cap")
    t = total(caps).valores
    assert t["total"] - t["cap_9"] == total(progs).valores["inicial"]
