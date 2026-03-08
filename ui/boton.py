import pygame


class Boton:
    def __init__(self, texto, color_fondo, color_texto, centro_x, y, ancho, alto, radio_borde=0, color_borde=None, grosor_borde=0):
        self.texto = texto
        self.color_fondo = color_fondo
        self.color_texto = color_texto
        self.x = centro_x - ancho / 2  # Calcular la posición x del botón
        self.y = y
        self.ancho = ancho
        self.alto = alto
        self.radio_borde = radio_borde
        self.color_borde = color_borde
        self.grosor_borde = grosor_borde
        # Calcular el rectángulo del botón
        self.rect = pygame.Rect(self.x, self.y, self.ancho, self.alto)

    def dibujar(self, pantalla, fuente):
        # Crear una superficie transparente para el botón
        superficie = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        # Dibujar círculos en las esquinas
        pygame.draw.circle(superficie, self.color_fondo, (self.radio_borde, self.radio_borde), self.radio_borde)
        pygame.draw.circle(superficie, self.color_fondo, (self.ancho - self.radio_borde, self.radio_borde), self.radio_borde)
        pygame.draw.circle(superficie, self.color_fondo, (self.radio_borde, self.alto - self.radio_borde), self.radio_borde)
        pygame.draw.circle(superficie, self.color_fondo, (self.ancho - self.radio_borde, self.alto - self.radio_borde), self.radio_borde)
        # Dibujar rectángulos adicionales para completar el borde redondeado
        pygame.draw.rect(superficie, self.color_fondo, (self.radio_borde, 0, self.ancho - 2 * self.radio_borde, self.alto))
        pygame.draw.rect(superficie, self.color_fondo, (0, self.radio_borde, self.ancho, self.alto - 2 * self.radio_borde))
        # Dibujar el borde del botón si se especifica
        if self.color_borde:
            pygame.draw.circle(superficie, self.color_borde, (self.radio_borde, self.radio_borde), self.radio_borde, self.grosor_borde)
            pygame.draw.circle(superficie, self.color_borde, (self.ancho - self.radio_borde, self.radio_borde), self.radio_borde, self.grosor_borde)
            pygame.draw.circle(superficie, self.color_borde, (self.radio_borde, self.alto - self.radio_borde), self.radio_borde, self.grosor_borde)
            pygame.draw.circle(superficie, self.color_borde, (self.ancho - self.radio_borde, self.alto - self.radio_borde), self.radio_borde, self.grosor_borde)
            pygame.draw.rect(superficie, self.color_borde, (self.radio_borde, 0, self.ancho - 2 * self.radio_borde, self.alto), self.grosor_borde)
            pygame.draw.rect(superficie, self.color_borde, (0, self.radio_borde, self.ancho, self.alto - 2 * self.radio_borde), self.grosor_borde)
        # Dibujar el texto en la superficie transparente
        texto_surface = fuente.render(self.texto, True, self.color_texto)
        texto_rect = texto_surface.get_rect(center=(self.ancho / 2, self.alto / 2))
        superficie.blit(texto_surface, texto_rect)
        # Dibujar la superficie transparente en la pantalla
        pantalla.blit(superficie, (self.x, self.y))

    def clic_en_boton(self, pos):
        return self.rect.collidepoint(pos)
