"""Mapa de teclas reasignable: acciones, valores por defecto y nombres.

Las flechas y Esc son fijas (siempre funcionan, no se pueden tocar): son la
red de seguridad para no quedarse sin poder moverse o pausar si la
reasignación se lía. Lo reasignable es la tecla "principal" de cada acción,
con los valores de hoy (WASD + Espacio + P) como valores por defecto.

Este módulo es lógica pura (sin tocar `config.ini`): la persistencia vive en
`src/core/config.py` (`cargar_controles` / `guardar_configuracion`), igual que
el resto de opciones de usuario.
"""

import pygame

ACCIONES = ("arriba", "abajo", "izquierda", "derecha", "disparar", "pausa")

ETIQUETAS = {
    "arriba": "Arriba", "abajo": "Abajo",
    "izquierda": "Izquierda", "derecha": "Derecha",
    "disparar": "Disparar", "pausa": "Pausa",
}

POR_DEFECTO = {
    "arriba": pygame.K_w,
    "abajo": pygame.K_s,
    "izquierda": pygame.K_a,
    "derecha": pygame.K_d,
    "disparar": pygame.K_SPACE,
    "pausa": pygame.K_p,
}


def nombre_tecla(codigo):
    """Nombre legible de una tecla (p.ej. "w", "espacio")."""
    if codigo == pygame.K_SPACE:
        return "Espacio"
    return pygame.key.name(codigo).capitalize()
