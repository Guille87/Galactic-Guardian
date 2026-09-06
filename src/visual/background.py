import pygame

from src.core import settings


class ScrollingBackground(pygame.sprite.Sprite):
    def __init__(self, imagen1, imagen2, pantalla_alto, velocidad=0.5):
        super().__init__()
        self.pantalla_alto = pantalla_alto
        self.velocidad = velocidad  # px/frame-a-60fps

        # Guardamos ambas imágenes
        self.img1 = imagen1
        self.img2 = imagen2

        # Posiciones iniciales
        self.y1 = 0.0
        self.y2 = -float(self.pantalla_alto)

    def update(self, dt=0):
        """Mueve las piezas del fondo y las resetea cuando salen de pantalla."""
        avance = self.velocidad * dt * settings.FPS
        self.y1 += avance
        self.y2 += avance

        if self.y1 >= self.pantalla_alto:
            self.y1 = self.y2 - self.pantalla_alto

        if self.y2 >= self.pantalla_alto:
            self.y2 = self.y1 - self.pantalla_alto

    def draw(self, superficie):
        """Función personalizada de dibujo para el fondo doble."""
        superficie.blit(self.img1, (0, round(self.y1)))
        superficie.blit(self.img2, (0, round(self.y2)))
