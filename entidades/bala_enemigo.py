from entidades.proyectil_base import Proyectil


class BalaEnemigo(Proyectil):
    def __init__(self, ruta_imagen, x, y, dir_x, dir_y, danio, velocidad):
        super().__init__(ruta_imagen, x, y, danio, velocidad)
        self.dir_x = dir_x
        self.dir_y = dir_y

    def update(self):
        """Movimiento basado en vector de dirección."""
        self.rect.x += self.velocidad * self.dir_x
        self.rect.y += self.velocidad * self.dir_y
