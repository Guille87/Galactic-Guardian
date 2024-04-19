import pygame


class Boton:
    def __init__(self, texto, color_fondo, color_texto, x, y, ancho, alto):
        self.texto = texto
        self.color_fondo = color_fondo
        self.color_texto = color_texto
        self.x = x
        self.y = y
        self.ancho = ancho
        self.alto = alto

    def dibujar(self, pantalla, fuente):
        pygame.draw.rect(pantalla, self.color_fondo, (self.x, self.y, self.ancho, self.alto))
        texto_surface = fuente.render(self.texto, True, self.color_texto)
        texto_rect = texto_surface.get_rect(center=(self.x + self.ancho / 2, self.y + self.alto / 2))
        pantalla.blit(texto_surface, texto_rect)

    def clic_en_boton(self, pos):
        return self.x < pos[0] < self.x + self.ancho and self.y < pos[1] < self.y + self.alto
