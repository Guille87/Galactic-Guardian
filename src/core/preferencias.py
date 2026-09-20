"""Preferencias de usuario que el juego consulta en tiempo de ejecución.

Estado de módulo, como `i18n`: `main.py` lo fija al arrancar desde `config.ini`,
Opciones lo cambia al instante (vista previa) y solo "Guardar" lo escribe en
disco. No lee ni escribe la configuración por sí mismo.
"""

_efectos_pantalla = True


def efectos_pantalla():
    """True si están activados los efectos de pantalla (temblor y hit-stop)."""
    return _efectos_pantalla


def establecer_efectos_pantalla(activos):
    global _efectos_pantalla
    _efectos_pantalla = bool(activos)
