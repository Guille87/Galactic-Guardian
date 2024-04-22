import os

import pygame
from galactic_guardian.resources.resource_manager import ResourceManager


# Instancia global de ResourceManager
resource_manager = ResourceManager()


class Item(pygame.sprite.Sprite):
    def __init__(self, image_name, folder_name):
        super().__init__()
        self.image_name = os.path.splitext(image_name)[0]
        self.folder_name = folder_name
        self.load_image(50, 50)
        self.speed = 1  # Velocidad de desplazamiento del objeto

    def load_image(self, width, height):
        # Obtener la imagen del ResourceManager
        original_image = resource_manager.get_image(self.image_name)
        # Escalar la imagen a las dimensiones especificadas
        self.image = pygame.transform.scale(original_image, (width, height))
        # Obtener el rectángulo de la imagen
        self.rect = self.image.get_rect()

    def update(self):
        # Desplazar hacia abajo
        self.rect.y += self.speed

    def set_posicion(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def aplicar_efecto(self, jugador):
        if self.image_name == "curacion":
            jugador.aumentar_salud(1)
            if jugador.salud > jugador.salud_maxima:
                jugador.salud = jugador.salud_maxima
        elif self.image_name == "potenciador_cadencia":
            jugador.cadencia_disparo -= 25
            if jugador.cadencia_disparo <= jugador.cadencia_disparo_maxima:
                jugador.cadencia_disparo = jugador.cadencia_disparo_maxima
            print(f"cadencia actual: {jugador.cadencia_disparo}")
        elif self.image_name == "potenciador_danio":
            if jugador.disparo_doble and not jugador.disparo_triple:
                jugador.disparo_triple = True
            if not jugador.disparo_doble and jugador.danio >= jugador.danio_maximo:
                jugador.disparo_doble = True
            jugador.danio += 1
            if jugador.danio >= jugador.danio_maximo:
                jugador.danio = jugador.danio_maximo
            print(f"daño actual: {jugador.danio}")
        elif self.image_name == "potenciador_velocidad":
            jugador.velocidad += 0.25
            if jugador.velocidad >= jugador.velocidad_maxima:
                jugador.velocidad = jugador.velocidad_maxima
            print(f"velocidad actual: {jugador.velocidad}")
