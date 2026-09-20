"""src/core/i18n.py — textos por idioma y coherencia del catálogo."""
import json
import os
import re

import pytest

from src.core import controles, i18n, paths

RAIZ_SRC = paths.recurso("src")
EXTENSIONES = {"json", "ini", "py", "png", "ogg", "wav", "ico", "txt"}


def _claves_es():
    with open(paths.recurso("data", "assets", "idiomas", "es.json"), encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def catalogos_falsos(monkeypatch):
    """Catálogos en memoria: `es` (referencia) y `xx` (incompleto)."""
    monkeypatch.setattr(i18n, "_catalogos", {
        "es": {"a": "hola", "b": "nivel {n}", "solo_es": "solo español"},
        "xx": {"a": "hello", "b": "level {n}"},
    })


def test_devuelve_el_texto_del_idioma_actual(catalogos_falsos):
    i18n.establecer_idioma("xx")
    assert i18n.t("a") == "hello"
    assert i18n.idioma_actual() == "xx"


def test_los_huecos_se_rellenan_con_los_datos(catalogos_falsos):
    assert i18n.t("b", n=3) == "nivel 3"
    i18n.establecer_idioma("xx")
    assert i18n.t("b", n=3) == "level 3"


def test_clave_que_falta_en_el_idioma_cae_al_espanol(catalogos_falsos):
    i18n.establecer_idioma("xx")
    assert i18n.t("solo_es") == "solo español"


def test_clave_inexistente_devuelve_la_propia_clave(catalogos_falsos):
    assert i18n.t("no.existe") == "no.existe"


def test_datos_que_no_cuadran_no_rompen(catalogos_falsos):
    assert i18n.t("b") == "nivel {n}"              # sin datos: texto tal cual
    assert i18n.t("b", otro=1) == "nivel {n}"      # hueco que falta: no lanza


def test_idioma_sin_archivo_usa_el_espanol():
    i18n.establecer_idioma("zz")
    assert i18n.t("comun.si") == "Sí"


def test_catalogo_espanol_real_carga():
    assert i18n.t("menu.jugar") == "Jugar"
    assert i18n.t("nivel_completado.titulo", n=2) == "NIVEL 2 COMPLETADO"
    assert i18n.t("nivel_completado.tiempo", s=12.34) == "Tiempo: 12.3 s"


def test_todas_las_claves_usadas_en_el_codigo_existen_en_el_catalogo():
    """Cualquier literal "espacio.nombre" del código cuyo espacio esté en el
    catálogo debe ser una clave real (evita erratas que saldrían como clave)."""
    claves = set(_claves_es())
    espacios = {c.split(".")[0] for c in claves}
    patron = re.compile(r'"(' + "|".join(sorted(espacios)) + r')\.([a-z_]+)"')
    usadas = set()
    for carpeta, _, archivos in os.walk(RAIZ_SRC):
        for nombre in archivos:
            if nombre.endswith(".py"):
                with open(os.path.join(carpeta, nombre), encoding="utf-8") as f:
                    usadas |= {f"{a}.{b}" for a, b in patron.findall(f.read())
                               if b not in EXTENSIONES}   # "puntuaciones.json" no es una clave
    assert usadas, "el test no encontró ninguna clave: ¿cambió la forma de llamar a t()?"
    assert usadas - claves == set()


def test_claves_dinamicas_existen():
    claves = set(_claves_es())
    assert {f"controles.{a}" for a in controles.ACCIONES} <= claves
    assert {"hud.ataque", "hud.vel_ataque", "hud.velocidad"} <= claves
