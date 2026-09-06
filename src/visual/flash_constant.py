import pygame


class DestelloConstante(pygame.sprite.Sprite):
    """Halo blanco constante mientras el jugador es invulnerable."""

    def __init__(self, jugador):
        super().__init__()
        self.radius = 30
        self.jugador = jugador
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 255, 255, 128), (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center=jugador.rect.center)

    def update(self, dt=0):
        # Sigue al jugador
        self.rect.center = self.jugador.rect.center
