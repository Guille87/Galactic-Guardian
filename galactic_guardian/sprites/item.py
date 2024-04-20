import os

import pygame


class Item(pygame.sprite.Sprite):
    def __init__(self, image_name, folder_name, tipo):
        super().__init__()
        self.image_name = image_name
        self.folder_name = folder_name
        self.load_image(50, 50)
        self.speed = 1  # Velocidad de desplazamiento del objeto
        self.tipo = tipo

    def load_image(self, width, height):
        folder_path = os.path.join('imagenes', self.folder_name)
        image_path = os.path.join(folder_path, self.image_name)
        original_image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(original_image, (width, height))
        self.rect = self.image.get_rect()

    def update(self):
        # Desplazar hacia abajo
        self.rect.y += self.speed

    def set_posicion(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def aplicar_efecto(self, jugador):
        if self.tipo == "curacion.png":
            jugador.aumentar_salud(1)
            if jugador.salud > jugador.salud_maxima:
                jugador.salud = jugador.salud_maxima
        elif self.tipo == "potenciador_cadencia.png":
            jugador.cadencia_disparo -= 25
            if jugador.cadencia_disparo <= jugador.cadencia_disparo_maxima:
                jugador.cadencia_disparo = jugador.cadencia_disparo_maxima
            print(f"cadencia actual: {jugador.cadencia_disparo}")
        elif self.tipo == "potenciador_danio.png":
            if jugador.disparo_doble and not jugador.disparo_triple:
                jugador.disparo_triple = True
            if not jugador.disparo_doble and jugador.danio >= jugador.danio_maximo:
                jugador.disparo_doble = True
            jugador.danio += 1
            if jugador.danio >= jugador.danio_maximo:
                jugador.danio = jugador.danio_maximo
            print(f"daño actual: {jugador.danio}")
        elif self.tipo == "potenciador_velocidad.png":
            jugador.velocidad += 0.25
            if jugador.velocidad >= jugador.velocidad_maxima:
                jugador.velocidad = jugador.velocidad_maxima
            print(f"velocidad actual: {jugador.velocidad}")
