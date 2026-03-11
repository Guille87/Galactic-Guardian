import pygame


class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, frames):
        super().__init__()
        self.frames = frames
        self.frame = 0
        self.image = self.frames[self.frame]
        self.rect = self.image.get_rect(center=center)
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 40  # Velocidad de la animación

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(self.frames):
                self.kill()
            else:
                self.image = self.frames[self.frame]
                # Re-centramos por si los frames tienen tamaños distintos
                self.rect = self.image.get_rect(center=self.rect.center)
