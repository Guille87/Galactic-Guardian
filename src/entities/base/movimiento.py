"""Utilidad de movimiento independiente de los FPS.

El `rect` de pygame trabaja con enteros, así que un desplazamiento fraccionario
por frame (p. ej. 2.4 px) perdería la parte decimal en cada paso. `MovimientoSubpixel`
acumula ese resto y lo aplica cuando suma un píxel entero.

El `rect` sigue siendo la fuente de verdad: si otro código lo reposiciona
directamente (reaparición del jugador, rebote del jefe...), el siguiente
desplazamiento parte de esa nueva posición sin desincronizarse.
"""

import math

import pygame

from src.core import settings


class MovimientoSubpixel:
    def _init_subpixel(self):
        self._resto = pygame.Vector2()
        # Píxeles realmente movidos en el último frame (para el HUD de debug).
        self._ultimo_desplazamiento = pygame.Vector2()

    def _desplazar(self, vx, vy, dt):
        """Desplaza el rect según una velocidad en px/frame-a-60fps y el dt real."""
        factor = dt * settings.FPS
        dx = vx * factor + self._resto.x
        dy = vy * factor + self._resto.y

        # Redondeo al entero más cercano (no truncado hacia cero): el resto queda
        # en [-0.5, 0.5), así que el rect nunca se aleja más de medio píxel de su
        # posición ideal. Con int() podía quedarse hasta 1 px por detrás y en un
        # ángulo poco inclinado eso se veía como escalones / "la bala se estanca".
        ix = math.floor(dx + 0.5)
        iy = math.floor(dy + 0.5)
        self.rect.x += ix
        self.rect.y += iy

        self._resto.x = dx - ix
        self._resto.y = dy - iy
        self._ultimo_desplazamiento.update(ix, iy)
