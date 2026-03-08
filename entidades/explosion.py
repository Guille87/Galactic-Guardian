import pygame


class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, explosion_images):
        super().__init__()
        self.explosion_images = explosion_images
        self.image = self.explosion_images[0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50  # Velocidad de la animación

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(self.explosion_images):
                self.kill()
            else:
                self.image = self.explosion_images[self.frame]
