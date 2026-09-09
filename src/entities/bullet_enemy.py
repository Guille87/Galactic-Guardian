from src.core import settings
from src.entities.base.projectile_base import Proyectil


class BalaEnemigo(Proyectil):
    # Tamaño al que se escala la imagen de las balas enemigas.
    TAMANO = (36, 36)
    RADIUS = settings.RADIO_BALA_ENEMIGO

    def __init__(self, imagen, x, y, dir_x, dir_y, danio, velocidad):
        super().__init__(imagen, x, y, danio, velocidad)
        self.dir_x = dir_x
        self.dir_y = dir_y

    def update(self, dt=0):
        """Movimiento según vector de dirección (independiente de FPS)."""
        self._desplazar(self.velocidad * self.dir_x, self.velocidad * self.dir_y, dt)
