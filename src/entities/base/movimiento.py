"""Utilidad de movimiento independiente de los FPS.

El `rect` de pygame trabaja con enteros, así que un desplazamiento fraccionario
por frame (p. ej. 2.4 px) perdería la parte decimal en cada paso. `MovimientoSubpixel`
acumula ese resto y lo aplica cuando suma un píxel entero.

El `rect` sigue siendo la fuente de verdad: si otro código lo reposiciona
directamente (reaparición del jugador, rebote del jefe...), el siguiente
desplazamiento parte de esa nueva posición sin desincronizarse.
"""

import pygame

from src.core import settings


class MovimientoSubpixel:
    def _init_subpixel(self):
        self._resto = pygame.Vector2()

    def _desplazar(self, vx, vy, dt):
        """Desplaza el rect según una velocidad en px/frame-a-60fps y el dt real."""
        factor = dt * settings.FPS
        dx = vx * factor + self._resto.x
        dy = vy * factor + self._resto.y

        ix, iy = int(dx), int(dy)
        self.rect.x += ix
        self.rect.y += iy

        self._resto.x = dx - ix
        self._resto.y = dy - iy
