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
        # La apariencia del botón es inmutable: se renderiza una sola vez.
        self._cache = None

    def _render(self, fuente):
        superficie = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        r = self.radio_borde
        # Esquinas redondeadas
        pygame.draw.circle(superficie, self.color_fondo, (r, r), r)
        pygame.draw.circle(superficie, self.color_fondo, (self.ancho - r, r), r)
        pygame.draw.circle(superficie, self.color_fondo, (r, self.alto - r), r)
        pygame.draw.circle(superficie, self.color_fondo, (self.ancho - r, self.alto - r), r)
        # Rellenos centrales
        pygame.draw.rect(superficie, self.color_fondo, (r, 0, self.ancho - 2 * r, self.alto))
        pygame.draw.rect(superficie, self.color_fondo, (0, r, self.ancho, self.alto - 2 * r))
        # Borde opcional
        if self.color_borde:
            pygame.draw.circle(superficie, self.color_borde, (r, r), r, self.grosor_borde)
            pygame.draw.circle(superficie, self.color_borde, (self.ancho - r, r), r, self.grosor_borde)
            pygame.draw.circle(superficie, self.color_borde, (r, self.alto - r), r, self.grosor_borde)
            pygame.draw.circle(superficie, self.color_borde, (self.ancho - r, self.alto - r), r, self.grosor_borde)
            pygame.draw.rect(superficie, self.color_borde, (r, 0, self.ancho - 2 * r, self.alto), self.grosor_borde)
            pygame.draw.rect(superficie, self.color_borde, (0, r, self.ancho, self.alto - 2 * r), self.grosor_borde)
        # Texto
        texto_surface = fuente.render(self.texto, True, self.color_texto)
        superficie.blit(texto_surface, texto_surface.get_rect(center=(self.ancho / 2, self.alto / 2)))
        return superficie

    def dibujar(self, pantalla, fuente):
        if self._cache is None:
            self._cache = self._render(fuente)
        pantalla.blit(self._cache, (self.x, self.y))

    def clic_en_boton(self, pos):
        return self.rect.collidepoint(pos)
