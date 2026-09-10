import pygame

from src.core import settings


class Item(pygame.sprite.Sprite):
    TAMANO_ESTANDAR = (48, 48)

    # Mapeo de efectos a funciones de jugador
    EFECTOS = {
        "curacion": lambda jugador: jugador.curar(1),
        "potenciador_cadencia": lambda jugador: jugador.mejorar_cadencia(25),
        "potenciador_danio": lambda jugador: jugador.mejorar_danio(1),
        "potenciador_velocidad": lambda jugador: jugador.mejorar_velocidad(0.5)
    }

    def __init__(self, tipo, imagen_surface, x, y):
        super().__init__()
        self.tipo = tipo
        self.image = imagen_surface
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 2  # px/frame-a-60fps
        self._resto_y = 0.0

    def update(self, dt=0):
        # Desplazamiento hacia abajo independiente de FPS
        dy = self.speed * dt * settings.FPS + self._resto_y
        iy = int(dy)
        self.rect.y += iy
        self._resto_y = dy - iy

    def aplicar_efecto(self, jugador):
        if self.tipo in self.EFECTOS:
            self.EFECTOS[self.tipo](jugador)
