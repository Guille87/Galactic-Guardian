import pygame


class DestelloConstante(pygame.sprite.Sprite):
    def __init__(self, jugador):
        super().__init__()
        self.radius = 30  # Radio del destello
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 255, 255, 128), (self.radius, self.radius), self.radius)  # Círculo blanco semitransparente
        self.rect = self.image.get_rect(center=jugador.rect.center)  # Posición inicial centrada en el jugador
        self.jugador = jugador  # Referencia al jugador

    def update(self):
        # Actualizar la posición del destello para que siga al jugador
        self.rect.center = self.jugador.rect.center
