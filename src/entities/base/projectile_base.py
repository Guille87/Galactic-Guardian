import pygame

from .movimiento import MovimientoSubpixel


class Proyectil(pygame.sprite.Sprite, MovimientoSubpixel):
    """Base común de balas. Recibe una `Surface` ya escalada y orientada
    (cacheada por el `ResourceManager`); nunca carga desde disco.

    La colisión la resuelve `CollisionManager` con `pygame.sprite.collide_circle`,
    que usa el atributo `radius`.
    """

    def __init__(self, imagen, x, y, danio, velocidad):
        super().__init__()
        self.image = imagen
        self.rect = self.image.get_rect(center=(x, y))

        self.danio = danio
        self.velocidad = velocidad
        self.radius = 16  # Hitbox circular estándar
        self._init_subpixel()

    def update(self, dt=0):
        """Función que sobreescribirán los hijos."""
        pass
