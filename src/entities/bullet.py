from src.entities.base.projectile_base import Proyectil


class Bala(Proyectil):
    # Tamaño al que se escala la imagen de la bala del jugador.
    TAMANO = (18, 18)
    # Ángulo fijo de la bala del jugador (siempre hacia arriba).
    ANGULO = 90

    def __init__(self, imagen, x, y, danio):
        super().__init__(imagen, x, y, danio, velocidad=10)

    def update(self):
        """Movimiento vertical simple para el jugador."""
        self.rect.y -= self.velocidad
