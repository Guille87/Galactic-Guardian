"""Comprobación de actualizaciones (solo aviso, no aplica nada).

Al abrir el menú se consulta en segundo plano la última Release de GitHub y, si
hay una versión más nueva que `__version__`, el menú muestra un aviso con un
botón que abre la página de descargas.

Todo es *best-effort*: cualquier fallo (sin red, timeout, límite de la API,
respuesta rara) se traga en silencio y el juego sigue igual. El resultado se
cachea en la carpeta de datos de usuario para no consultar en cada arranque.
"""

import json
import os
import threading
import time
import urllib.request

from src.core import paths
from src.core.version import __version__

_REPO = "Guille87/Galactic-Guardian"
_API_LATEST = f"https://api.github.com/repos/{_REPO}/releases/latest"
_RELEASES_WEB = f"https://github.com/{_REPO}/releases/latest"
_CACHE = os.path.join(paths.dir_datos_usuario(), "comprobacion-actualizacion.json")
_CACHE_TTL = 24 * 3600      # segundos: como mucho una consulta al día
_TIMEOUT = 5               # segundos
_DESACTIVADO = bool(os.environ.get("GG_SIN_COMPROBAR_ACTUALIZACIONES"))


def _parsear_version(texto):
    """'v0.1.3', '0.1.3', '0.1.3-beta' -> (0, 1, 3). None si no cuadra."""
    if not texto:
        return None
    limpio = texto.strip().lstrip("vV").split("-")[0].split("+")[0]
    trozos = limpio.split(".")
    try:
        return tuple(int(t) for t in trozos[:3]) if trozos else None
    except ValueError:
        return None


def hay_version_mas_nueva(instalada, publicada):
    """True solo si `publicada` es estrictamente mayor y ambas se entienden."""
    a = _parsear_version(instalada)
    b = _parsear_version(publicada)
    if a is None or b is None:
        return False
    return b > a


def _leer_cache():
    try:
        with open(_CACHE, "r", encoding="utf-8") as f:
            datos = json.load(f)
        if time.time() - datos.get("ts", 0) < _CACHE_TTL:
            return datos
    except (OSError, ValueError):
        pass
    return None


def _guardar_cache(datos):
    try:
        os.makedirs(os.path.dirname(_CACHE), exist_ok=True)
        with open(_CACHE, "w", encoding="utf-8") as f:
            json.dump(datos, f)
    except OSError:
        pass


def _consultar_api():
    peticion = urllib.request.Request(
        _API_LATEST,
        headers={
            "User-Agent": f"GalacticGuardian/{__version__}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(peticion, timeout=_TIMEOUT) as respuesta:
        cuerpo = json.load(respuesta)
    datos = {
        "tag": cuerpo.get("tag_name", ""),
        "url": cuerpo.get("html_url") or _RELEASES_WEB,
        "ts": time.time(),
    }
    _guardar_cache(datos)
    return datos


class ComprobadorActualizaciones:
    """Lanza la comprobación en un hilo y expone el resultado.

    `resultado`:
      - ``None``  -> aún sin comprobar (o fallo silencioso)
      - ``False`` -> comprobado, el juego está al día
      - ``dict``  -> {"version": "0.1.4", "url": "..."} hay una más nueva
    """

    def __init__(self):
        self.resultado = None
        self._hilo = None

    def comprobar_en_segundo_plano(self):
        if _DESACTIVADO or self._hilo is not None:
            return
        self._hilo = threading.Thread(target=self._comprobar, daemon=True)
        self._hilo.start()

    def _comprobar(self):
        try:
            datos = _leer_cache() or _consultar_api()
        except Exception:      # noqa: BLE001 — best-effort, nunca debe romper el menú
            return
        if not datos or not datos.get("tag"):
            return
        if hay_version_mas_nueva(__version__, datos["tag"]):
            self.resultado = {
                "version": datos["tag"].lstrip("vV"),
                "url": datos.get("url", _RELEASES_WEB),
            }
        else:
            self.resultado = False
