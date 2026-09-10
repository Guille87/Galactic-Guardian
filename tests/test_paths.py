"""src/core/paths.py y coherencia de rutas de recursos y versión."""
import os
import sys
import tomllib
from pathlib import Path

import pytest

from src.core import paths
from src.core.config import (
    DIR_ASSETS, RECURSOS, EXPLOSIONES, SONIDOS, MUSICA,
)
from src.core.version import __version__

RAIZ = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("nombre,ruta", [
    *RECURSOS.items(), *EXPLOSIONES.items(), *SONIDOS.items(), *MUSICA.items(),
])
def test_cada_recurso_existe_en_disco(nombre, ruta):
    """Si esto falla, al empaquetar faltaría ese archivo en el bundle."""
    assert os.path.isfile(os.path.join(DIR_ASSETS, ruta)), nombre


def test_recurso_apunta_a_la_raiz_del_proyecto_en_desarrollo():
    assert Path(paths.recurso("data", "assets")) == RAIZ / "data" / "assets"


def test_dir_datos_usuario_en_desarrollo_es_la_raiz():
    assert Path(paths.dir_datos_usuario()) == RAIZ


def test_dir_datos_usuario_congelado_usa_carpeta_del_so(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))

    destino = Path(paths.dir_datos_usuario())

    assert destino != RAIZ
    assert destino.is_dir()               # se crea si no existe
    assert destino.name == "GalacticGuardian"


def test_version_coincide_con_pyproject():
    datos = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    assert datos["project"]["version"] == __version__
