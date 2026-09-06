import pygame

from src.core import settings


class Destello(pygame.sprite.Sprite):
    """Destello rojo efímero sobre el jugador al recibir daño."""

    def __init__(self, jugador):
        super().__init__()
        self.radius = 30
        self.jugador = jugador
        self._color = (255, 0, 0)
        self.alpha = 200.0
        self.fade_speed = 10  # alpha/frame-a-60fps

        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=jugador.rect.center)
        self._redibujar()

    def _redibujar(self):
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(
            self.image, (*self._color, int(max(0, self.alpha))),
            (self.radius, self.radius), self.radius
        )

    def update(self, dt=0):
        self.rect.center = self.jugador.rect.center
        self.alpha -= self.fade_speed * dt * settings.FPS
        if self.alpha <= 0:
            self.kill()
        else:
            self._redibujar()
