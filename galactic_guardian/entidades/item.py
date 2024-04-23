import os

import pygame
from galactic_guardian.resources.resource_manager import ResourceManager


# Instancia global de ResourceManager
resource_manager = ResourceManager()


class Item(pygame.sprite.Sprite):
    # Mapeo de efectos a funciones de jugador
    EFECTOS = {
        "curacion": lambda jugador: jugador.aumentar_salud(1),
        "potenciador_cadencia": lambda jugador: jugador.modificar_cadencia(-25),
        "potenciador_danio": lambda jugador: jugador.modificar_danio(1),
        "potenciador_velocidad": lambda jugador: jugador.modificar_velocidad(0.25)
    }

    def __init__(self, image_name, folder_name, width=50, height=50):
        super().__init__()
        self.image_name = os.path.splitext(image_name)[0]
        self.folder_name = folder_name
        self.load_image(width, height)
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
        if self.image_name in self.EFECTOS:
            self.EFECTOS[self.image_name](jugador)
