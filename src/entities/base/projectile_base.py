import pygame


class Proyectil(pygame.sprite.Sprite):
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

    def update(self):
        """Función que sobreescribirán los hijos."""
        pass
