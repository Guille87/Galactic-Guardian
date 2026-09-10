"""Rutas del juego, robustas frente a PyInstaller.

Dos tipos de ruta:

- **Recursos** (`recurso`): archivos de solo lectura que se distribuyen con el
  juego (`data/assets/`). En desarrollo salen de la raíz del proyecto; congelado
  con PyInstaller, de la carpeta donde este descomprime/coloca los datos
  (`sys._MEIPASS`).
- **Datos de usuario** (`dir_datos_usuario`): archivos que el juego escribe
  (`config.ini`, puntuaciones). En desarrollo van a la raíz del proyecto (como
  siempre). Congelado, a la carpeta estándar del sistema operativo, para que
  sobrevivan a una actualización que reemplace la carpeta del juego y para poder
  escribir aunque el ejecutable esté en una ruta protegida.
"""

import os
import sys

_APP = "GalacticGuardian"

# Raíz del proyecto: este archivo es src/core/paths.py -> subir tres niveles.
_RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _congelado():
    return getattr(sys, "frozen", False)


def _raiz_recursos():
    if _congelado():
        # onefile: carpeta temporal de extracción; onedir: carpeta del ejecutable.
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return _RAIZ_PROYECTO


def recurso(*partes):
    """Ruta absoluta a un recurso empaquetado (p. ej. `recurso("data", "assets")`)."""
    return os.path.join(_raiz_recursos(), *partes)


def _dir_datos_so():
    """Carpeta de datos de usuario según el sistema operativo."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, _APP)


def dir_datos_usuario():
    """Carpeta donde el juego guarda config y puntuaciones. Se crea si no existe."""
    base = _dir_datos_so() if _congelado() else _RAIZ_PROYECTO
    os.makedirs(base, exist_ok=True)
    return base
