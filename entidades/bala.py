import math

import pygame


class Bala(pygame.sprite.Sprite):
    def __init__(self, imagen, x, y, danio):
        super().__init__()
        self.imagen_original = pygame.image.load(imagen)
        # Escala la imagen a una fracción de su tamaño original
        self.image = pygame.transform.scale(self.imagen_original, (50, 50))
        self.rect = self.image.get_rect(centerx=x, bottom=y)
        self.velocidad = 10
        self.radio = 16  # Radio de la hitbox circular
        self.danio = danio  # Guarda el daño que inflige la bala

    def bala_jugador(self):
        self.rect.y -= self.velocidad

    def girar(self, angulo):
        # Rotar la imagen de la bala
        self.image = pygame.transform.rotate(self.image, angulo)
        self.rect = self.image.get_rect(center=self.rect.center)

    def comprobar_colision(self, objeto):
        """
        Comprueba si hay colisión entre la bala y otro objeto.
        """
        if objeto is not None:  # Verifica si objeto no es None
            # Calcular la distancia entre los centros de la bala y el objeto
            distancia_x = self.rect.centerx - objeto.rect.centerx
            distancia_y = self.rect.centery - objeto.rect.centery
            distancia = math.hypot(distancia_x, distancia_y)

            # Si la distancia es menor que la suma de los radios de las hitboxes circulares, hay colisión
            if distancia < self.radio + objeto.radio:
                return True
        return False
