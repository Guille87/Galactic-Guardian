"""Textos del juego por idioma.

Cada idioma es un JSON plano en `data/assets/idiomas/<codigo>.json` (clave ->
texto). El español (`REFERENCIA`) es el idioma de referencia: todas las claves
existen ahí, y es el respaldo si a otro idioma le falta alguna. Los huecos van
con `str.format` (`"Nivel {n}"` + `t("clave", n=3)`).

`t()` nunca lanza: una clave que no existe en ningún idioma devuelve la propia
clave (se ve raro en pantalla, pero el juego no se cae por un texto).
"""

import json

from src.core import paths

REFERENCIA = "es"

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
