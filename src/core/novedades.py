"""Contenido de las pantallas "Novedades" e "Historial de versiones".

`HISTORIAL` es el historial completo, **de la más reciente a la más antigua**: se
actualiza en cada release (ver CONTRIBUTING.md) añadiendo una entrada al principio con un
resumen, para el jugador, de lo que cambió — normalmente un subconjunto de lo que ya
cuenta el CHANGELOG, en un tono más cercano; las entradas anteriores no se tocan. Una
versión sin nada que contar (p. ej. un PATCH pequeño) simplemente no añade entrada.

`src/ui/menu.py` usa `claves_version_actual()` para la pantalla que se muestra una única
vez tras actualizar (`config.cargar_version_vista`/`guardar_version_vista` llevan la
cuenta de cuál fue la última vista) y `HISTORIAL` entero para la pantalla de historial,
que se puede abrir en cualquier momento desde el menú principal.
"""
from src.core.version import __version__

# Claves de texto `novedades.<clave>` de cada versión, en el orden en que se muestran
# (únicas entre sí: no hace falta que lo sean solo dentro de su versión).
HISTORIAL = (
    ("0.12.0", (
        "monedas_resumen",
        "resumen_salida",
        "economia",
    )),
    ("0.11.0", (
        "guardado_campana",
        "disparo_automatico",
    )),
    ("0.10.0", (
        "arbol_mejoras",
        "cifras_dano",
        "reequilibrio_general",
    )),
)


def claves_version_actual():
    """Claves de la versión que corre ahora mismo, o `()` si no encabeza `HISTORIAL`
    (todavía no se le añadió su entrada, o esta versión no tiene nada que anunciar)."""
    if HISTORIAL and HISTORIAL[0][0] == __version__:
        return HISTORIAL[0][1]
    return ()
