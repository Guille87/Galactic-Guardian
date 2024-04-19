import math

import pygame


class BalaEnemigo(pygame.sprite.Sprite):
    def __init__(self, imagen, x, y, direccion_x, direccion_y, velocidad, danio):
        super().__init__()
        self.image_original = pygame.image.load(imagen)
        self.image = self.image_original.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.direccion_x = direccion_x
        self.direccion_y = direccion_y
        self.velocidad = velocidad
        self.danio = danio
        self.radio = 16  # Radio de la hitbox circular

    def bala_enemigo(self):
        # Mueve la bala en la dirección especificada por direccion_x y direccion_y
        self.rect.x += self.velocidad * self.direccion_x
        self.rect.y += self.velocidad * self.direccion_y

    def girar(self, angulo):
        # Girar la imagen de la bala
        self.image = pygame.transform.rotate(self.image_original, angulo)
        self.rect = self.image.get_rect(center=self.rect.center)

    def comprobar_colision(self, objeto):
        """
        Comprueba si hay colisión entre la bala y otro objeto.
        """
        # Calcular la distancia entre los centros de la bala y el objeto
        distancia_x = self.rect.centerx - objeto.rect.centerx
        distancia_y = self.rect.centery - objeto.rect.centery
        distancia = math.sqrt(distancia_x ** 2 + distancia_y ** 2)

        # Si la distancia es menor que la suma de los radios de las hitboxes circulares, hay colisión
        if distancia < self.radio + objeto.radio:
            return True
        else:
            return False
