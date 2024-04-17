import pygame


class Destello(pygame.sprite.Sprite):
    def __init__(self, jugador):
        super().__init__()
        self.radius = 30  # Radio del destello
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 255, 255, 128), (self.radius, self.radius), self.radius)  # Círculo blanco semitransparente
        self.rect = self.image.get_rect(center=jugador.rect.center)  # Posición inicial centrada en el jugador
        self.alpha = 255  # Transparencia inicial
        self.fade_speed = 10  # Velocidad de atenuación
        self.jugador = jugador  # Referencia al jugador

    def update(self):
        # Actualizar la posición del destello para que siga al jugador
        self.rect.center = self.jugador.rect.center
        self.alpha -= self.fade_speed  # Reducir la transparencia
        if self.alpha <= 0:
            self.kill()  # Eliminar el destello si la transparencia es menor o igual a 0
        else:
            self.image.set_alpha(self.alpha)  # Actualizar la transparencia del destello
