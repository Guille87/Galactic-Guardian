import random

from src.core import settings


class Temblor:
    """Temblor de pantalla por "trauma" (0..1).

    Cada golpe suma trauma (`agregar`), que decae solo con el tiempo de juego
    (`actualizar(dt)`, así que se congela en pausa). El desplazamiento en píxeles
    es `TEMBLOR_MAX_PX * trauma² * aleatorio(-1..1)` por eje: los golpes pequeños
    apenas se notan, los grandes sí, y el final se apaga suavemente.

    No dibuja nada: `RenderManager` pide `desplazamiento()` cada frame.
    """

    def __init__(self, rng=None):
        self.trauma = 0.0
        self._rng = rng or random

    @property
    def activo(self):
        return self.trauma > 0

    def agregar(self, cantidad):
        self.trauma = min(1.0, self.trauma + cantidad)

    def actualizar(self, dt):
        if self.trauma > 0:
            self.trauma = max(0.0, self.trauma - settings.TEMBLOR_DECAIMIENTO * dt)

    def reiniciar(self):
        self.trauma = 0.0

    def desplazamiento(self):
        """`(dx, dy)` en píxeles enteros para este frame; `(0, 0)` en reposo."""
        if self.trauma <= 0:
            return (0, 0)
        amplitud = settings.TEMBLOR_MAX_PX * self.trauma ** 2
        return (round(self._rng.uniform(-amplitud, amplitud)),
                round(self._rng.uniform(-amplitud, amplitud)))
