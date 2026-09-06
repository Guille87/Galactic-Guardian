import math

import pygame


class Proyectil(pygame.sprite.Sprite):
    """Base común de balas. Recibe una `Surface` ya escalada y orientada
    (cacheada por el `ResourceManager`); nunca carga desde disco."""

    def __init__(self, imagen, x, y, danio, velocidad):
        super().__init__()
        self.image = imagen
        self.rect = self.image.get_rect(center=(x, y))

        self.danio = danio
        self.velocidad = velocidad
        self.radio = 16  # Hitbox circular estándar

    def comprobar_colision(self, objeto):
        """Lógica de colisión circular genérica."""
        if objeto:
            distancia = math.hypot(
                self.rect.centerx - objeto.rect.centerx,
                self.rect.centery - objeto.rect.centery
            )
            return distancia < self.radio + objeto.radio
        return False

    def update(self):
        """Función que sobreescribirán los hijos."""
        pass
