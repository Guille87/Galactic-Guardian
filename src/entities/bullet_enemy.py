from src.entities.base.projectile_base import Proyectil


class BalaEnemigo(Proyectil):
    # Tamaño al que se escala la imagen de las balas enemigas.
    TAMANO = (24, 24)

    def __init__(self, imagen, x, y, dir_x, dir_y, danio, velocidad):
        super().__init__(imagen, x, y, danio, velocidad)
        self.dir_x = dir_x
        self.dir_y = dir_y

    def update(self):
        """Movimiento basado en vector de dirección."""
        self.rect.x += self.velocidad * self.dir_x
        self.rect.y += self.velocidad * self.dir_y
