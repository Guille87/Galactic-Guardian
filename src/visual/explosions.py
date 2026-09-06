import pygame


class Explosion(pygame.sprite.Sprite):
    FRAME_MS = 40  # duración de cada fotograma de la animación

    def __init__(self, center, frames):
        super().__init__()
        self.frames = frames
        self.frame = 0
        self.image = self.frames[self.frame]
        self.rect = self.image.get_rect(center=center)
        self._acumulado = 0.0  # ms acumulados en el fotograma actual

    def update(self, dt=0):
        # dt viene en segundos; la animación avanza aunque cambien los FPS y se
        # congela sola durante la pausa (no se llama a update mientras pausado).
        self._acumulado += dt * 1000
        while self._acumulado >= self.FRAME_MS:
            self._acumulado -= self.FRAME_MS
            self.frame += 1
            if self.frame >= len(self.frames):
                self.kill()
                return
            self.image = self.frames[self.frame]
            self.rect = self.image.get_rect(center=self.rect.center)
