"""Textos del juego por idioma.

Cada idioma es un JSON plano en `data/assets/idiomas/<codigo>.json` (clave ->
texto). El español (`REFERENCIA`) es el idioma de referencia: todas las claves
existen ahí, y es el respaldo si a otro idioma le falta alguna. Los huecos van
con `str.format` (`"Nivel {n}"` + `t("clave", n=3)`).

`t()` nunca lanza: una clave que no existe en ningún idioma devuelve la propia
clave (se ve raro en pantalla, pero el juego no se cae por un texto).
"""

import json
import locale
import os
import sys

from src.core import paths

REFERENCIA = "es"
IDIOMAS = ("es", "en")
# Cada idioma se muestra en su propio idioma (no se traduce): así el jugador
# lo encuentra aunque el juego esté en un idioma que no entiende.
NOMBRES = {"es": "Español", "en": "English"}

_idioma = REFERENCIA
_catalogos = {}


def _catalogo(codigo):
    """Catálogo de un idioma (cacheado). `{}` si el archivo falta o es inválido."""
    if codigo not in _catalogos:
        ruta = paths.recurso("data", "assets", "idiomas", f"{codigo}.json")
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
            _catalogos[codigo] = datos if isinstance(datos, dict) else {}
        except (OSError, ValueError):
            _catalogos[codigo] = {}
    return _catalogos[codigo]


def _idioma_windows():
    """Idioma de la interfaz de Windows ("en"/"es"), o None si no se sabe."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        primario = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
    except (OSError, AttributeError, ValueError):
        return None
    return {0x09: "en", 0x0A: "es"}.get(primario)


def _idioma_locale():
    """Idioma según la configuración regional / variables de entorno."""
    for variable in ("LC_ALL", "LC_MESSAGES", "LANG"):
        valor = os.environ.get(variable)
        if valor:
            return valor[:2].lower()
    try:
        return (locale.getlocale()[0] or "")[:2].lower() or None
    except (ValueError, TypeError):
        return None


def detectar_idioma_sistema():
    """Idioma para la primera vez que se abre el juego: el del sistema si está
    disponible (inglés/español) y, si no, el de referencia (español)."""
    codigo = _idioma_windows() or _idioma_locale()
    return codigo if codigo in IDIOMAS else REFERENCIA


def idioma_actual():
    return _idioma


def establecer_idioma(codigo):
    """Cambia el idioma de los textos (no toca la configuración en disco)."""
    global _idioma
    _idioma = codigo


def t(clave, **datos):
    """Texto de `clave` en el idioma actual (o en español, o la propia clave)."""
    texto = _catalogo(_idioma).get(clave)
    if texto is None:
        texto = _catalogo(REFERENCIA).get(clave)
    if texto is None:
        return clave
    if not datos:
        return texto
    try:
        return texto.format(**datos)
    except (KeyError, IndexError, ValueError):
        return texto
