"""Preferencias de usuario que el juego consulta en tiempo de ejecución.

Estado de módulo, como `i18n`: `main.py` lo fija al arrancar desde `config.ini`,
Opciones lo cambia al instante (vista previa) y solo "Guardar" lo escribe en
disco. No lee ni escribe la configuración por sí mismo.
"""

_temblor = True
_cifras_dano = True
_disparo_automatico = False
_mostrar_fps = True


def temblor_activado():
    """True si el temblor de pantalla está activado."""
    return _temblor


def establecer_temblor(activos):
    global _temblor
    _temblor = bool(activos)


def cifras_dano_activadas():
    """True si se muestran las cifras flotantes de daño."""
    return _cifras_dano


def establecer_cifras_dano(activas):
    global _cifras_dano
    _cifras_dano = bool(activas)


def disparo_automatico():
    """True si la nave dispara sola, sin pulsar ningún botón."""
    return _disparo_automatico


def establecer_disparo_automatico(activo):
    global _disparo_automatico
    _disparo_automatico = bool(activo)


def mostrar_fps():
    """True si se muestran los FPS en partida."""
    return _mostrar_fps


def establecer_mostrar_fps(activos):
    global _mostrar_fps
    _mostrar_fps = bool(activos)
