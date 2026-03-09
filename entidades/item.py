import pygame


class Item(pygame.sprite.Sprite):
    TAMANO_ESTANDAR = (48, 48)

    # Mapeo de efectos a funciones de jugador
    EFECTOS = {
        "curacion": lambda jugador: jugador.aumentar_salud(1),
        "potenciador_cadencia": lambda jugador: jugador.modificar_cadencia(-25),
        "potenciador_danio": lambda jugador: jugador.modificar_danio(1),
        "potenciador_velocidad": lambda jugador: jugador.modificar_velocidad(0.25)
    }

    def __init__(self, tipo, imagen_surface, x, y):
        super().__init__()
        self.tipo = tipo
        self.image = imagen_surface
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 2  # Velocidad de desplazamiento del objeto

    def update(self):
        # Desplazar hacia abajo
        self.rect.y += self.speed

    def aplicar_efecto(self, jugador):
        if self.tipo in self.EFECTOS:
            self.EFECTOS[self.tipo](jugador)
