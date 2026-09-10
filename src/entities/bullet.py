from src.core import settings
from src.entities.base.projectile_base import Proyectil


class Bala(Proyectil):
    # Tamaño al que se escala la imagen de la bala del jugador.
    TAMANO = (50, 50)
    # Ángulo fijo de la bala del jugador (siempre hacia arriba).
    ANGULO = 90
    RADIUS = settings.RADIO_BALA_JUGADOR

    def __init__(self, imagen, x, y, danio):
        super().__init__(imagen, x, y, danio, velocidad=10)

    def update(self, dt=0):
        """Movimiento vertical simple para el jugador (independiente de FPS)."""
        self._desplazar(0, -self.velocidad, dt)
