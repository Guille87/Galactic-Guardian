import math
import pygame


class Proyectil(pygame.sprite.Sprite):
    def __init__(self, ruta_imagen, x, y, danio, velocidad, tamano=(50, 50)):
        super().__init__()
        # Carga inyectada (puedes pasar el Surface directamente si prefieres)
        img = pygame.image.load(ruta_imagen).convert_alpha()
        self.image = pygame.transform.scale(img, tamano)
        self.rect = self.image.get_rect(center=(x, y))

        self.danio = danio
        self.velocidad = velocidad
        self.radio = 16  # Hitbox circular estándar

    def girar(self, angulo):
        """Gira la imagen manteniendo el centro."""
        self.image = pygame.transform.rotate(self.image, angulo)
        self.rect = self.image.get_rect(center=self.rect.center)

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