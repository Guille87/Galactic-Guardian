"""src/core/updates.py — comprobación de nueva versión (solo aviso)."""
import json
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
        "tag": "v9.9.9", "url": "http://x", "ts": time.time(),
    }))
    def _no_llamar():
        raise AssertionError("no debería consultar la API con caché fresca")
    monkeypatch.setattr(updates, "_consultar_api", _no_llamar)

    c = updates.ComprobadorActualizaciones()
    c._comprobar()
    assert c.resultado == {"version": "9.9.9", "url": "http://x"}


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
