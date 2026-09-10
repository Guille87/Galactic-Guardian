"""src/core/updates.py — comprobación de nueva versión y descarga del instalador."""
import json
import os
import time

import pytest

from src.core import updates


@pytest.mark.parametrize("texto,esperado", [
    ("v0.1.3", (0, 1, 3)),
    ("0.1.3", (0, 1, 3)),
    ("v1.2.0-beta", (1, 2, 0)),
    ("2.0", (2, 0)),
    ("", None),
    ("no-es-version", None),
])
def test_parsear_version(texto, esperado):
    assert updates._parsear_version(texto) == esperado


@pytest.mark.parametrize("instalada,publicada,esperado", [
    ("0.1.3", "0.1.4", True),
    ("0.1.3", "v0.2.0", True),
    ("0.1.3", "0.1.3", False),
    ("0.1.3", "0.1.2", False),
    ("0.1.3", "basura", False),
    ("0.1.10", "0.1.9", False),      # comparación numérica, no de cadenas
])
def test_hay_version_mas_nueva(instalada, publicada, esperado):
    assert updates.hay_version_mas_nueva(instalada, publicada) is esperado


@pytest.fixture
def cache_temporal(tmp_path, monkeypatch):
    ruta = tmp_path / "comprobacion.json"
    monkeypatch.setattr(updates, "_CACHE", str(ruta))
    return ruta


def test_usa_la_cache_si_esta_fresca(cache_temporal, monkeypatch):
    cache_temporal.write_text(json.dumps({
        "tag": "v9.9.9", "url": "http://x", "instalador_url": "http://x/setup.exe",
        "ts": time.time(),
    }))
    def _no_llamar():
        raise AssertionError("no debería consultar la API con caché fresca")
    monkeypatch.setattr(updates, "_consultar_api", _no_llamar)

    c = updates.ComprobadorActualizaciones()
    c._comprobar()
    assert c.resultado == {
        "version": "9.9.9", "url": "http://x", "instalador_url": "http://x/setup.exe",
    }


def test_url_instalador_elige_el_asset_setup():
    cuerpo = {"assets": [
        {"name": "GalacticGuardian-v1.0.0-windows.zip", "browser_download_url": "z"},
        {"name": "GalacticGuardian-v1.0.0-setup.exe", "browser_download_url": "s"},
    ]}
    assert updates._url_instalador(cuerpo) == "s"
    assert updates._url_instalador({"assets": []}) is None


def test_cache_caducada_consulta_la_api(cache_temporal, monkeypatch):
    cache_temporal.write_text(json.dumps({
        "tag": "v0.0.1", "url": "http://viejo", "ts": time.time() - 999999,
    }))
    monkeypatch.setattr(updates, "_consultar_api",
                        lambda: {"tag": "v0.0.1", "url": "http://nuevo"})
    monkeypatch.setattr(updates, "__version__", "9.9.9")

    c = updates.ComprobadorActualizaciones()
    c._comprobar()
    assert c.resultado is False        # 9.9.9 > 0.0.1: al día


def test_fallo_de_red_no_rompe_nada(cache_temporal, monkeypatch):
    def _revienta():
        raise OSError("sin red")
    monkeypatch.setattr(updates, "_consultar_api", _revienta)

    c = updates.ComprobadorActualizaciones()
    c._comprobar()
    assert c.resultado is None         # silencioso


def test_desactivado_por_variable_de_entorno(monkeypatch):
    monkeypatch.setattr(updates, "_DESACTIVADO", True)
    c = updates.ComprobadorActualizaciones()
    c.comprobar_en_segundo_plano()
    assert c._hilo is None


# --- Descarga del instalador ---

class _RespuestaFalsa:
    def __init__(self, datos, longitud=None):
        self._datos = datos
        self.headers = {"Content-Length": str(longitud if longitud is not None else len(datos))}
        self._pos = 0
    def read(self, n):
        trozo = self._datos[self._pos:self._pos + n]
        self._pos += len(trozo)
        return trozo
    def __enter__(self): return self
    def __exit__(self, *a): return False


def test_descarga_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(updates.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(updates.urllib.request, "urlopen",
                        lambda req, timeout=0: _RespuestaFalsa(b"x" * 5000))

    d = updates.DescargaActualizacion("http://x/setup.exe")
    d._descargar()

    assert d.terminada and not d.error
    assert d.progreso == 1.0
    assert os.path.getsize(d.ruta) == 5000


def test_descarga_incompleta_es_error(tmp_path, monkeypatch):
    monkeypatch.setattr(updates.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(updates.urllib.request, "urlopen",
                        lambda req, timeout=0: _RespuestaFalsa(b"x" * 10, longitud=9999))

    d = updates.DescargaActualizacion("http://x/setup.exe")
    d._descargar()
    assert d.error and not d.terminada


def test_lanzar_instalador_usa_flags_silenciosos(monkeypatch):
    llamadas = []
    monkeypatch.setattr(updates.subprocess, "Popen",
                        lambda args, **kw: llamadas.append(args))
    updates.lanzar_instalador(r"C:\tmp\setup.exe")
    assert llamadas and "/SILENT" in llamadas[0] and "/CLOSEAPPLICATIONS" in llamadas[0]


def test_puede_autoactualizar_segun_frozen(monkeypatch):
    monkeypatch.setattr(updates.sys, "frozen", False, raising=False)
    assert updates.puede_autoactualizar() is False
    monkeypatch.setattr(updates.sys, "frozen", True, raising=False)
    assert updates.puede_autoactualizar() is True
