import pygame


class ScrollingBackground(pygame.sprite.Sprite):
    def __init__(self, imagen1, imagen2, pantalla_alto, velocidad=0.5):
        super().__init__()
        self.pantalla_alto = pantalla_alto
        self.velocidad = velocidad

        # Guardamos ambas imágenes
        self.img1 = imagen1
        self.img2 = imagen2

        # Posiciones iniciales
        self.y1 = 0
        self.y2 = -self.pantalla_alto

    def update(self):
        """Mueve las piezas del fondo y las resetea cuando salen de pantalla."""
        self.y1 += self.velocidad
        self.y2 += self.velocidad

        if self.y1 >= self.pantalla_alto:
            self.y1 = self.y2 - self.pantalla_alto

        if self.y2 >= self.pantalla_alto:
            self.y2 = self.y1 - self.pantalla_alto

    def draw(self, superficie):
        """Función personalizada de dibujo para el fondo doble."""
        superficie.blit(self.img1, (0, self.y1))
        superficie.blit(self.img2, (0, self.y2))