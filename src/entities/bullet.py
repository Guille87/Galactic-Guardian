from src.entities.base.projectile_base import Proyectil


class Bala(Proyectil):
    def __init__(self, ruta_imagen, x, y, danio):
        super().__init__(ruta_imagen, x, y, danio, velocidad=10)

    def update(self):
        """Movimiento vertical simple para el jugador."""
        self.rect.y -= self.velocidad
