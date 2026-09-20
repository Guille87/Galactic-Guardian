"""Preferencias de usuario que el juego consulta en tiempo de ejecución.

Estado de módulo, como `i18n`: `main.py` lo fija al arrancar desde `config.ini`,
Opciones lo cambia al instante (vista previa) y solo "Guardar" lo escribe en
disco. No lee ni escribe la configuración por sí mismo.
"""

_temblor = True


def temblor_activado():
    """True si el temblor de pantalla está activado."""
    return _temblor


def establecer_temblor(activos):
    global _temblor
    _temblor = bool(activos)
