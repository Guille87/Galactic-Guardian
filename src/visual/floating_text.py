import pygame

from src.core import settings


class CifraFlotante(pygame.sprite.Sprite):
    """Cifra de daño que sube desde el punto del impacto y se desvanece.

    Vive en `entity_manager.efectos`: se mueve con el `dt` del juego, así que se congela
    en pausa como el resto de efectos. Se dibuja con un borde oscuro para leerse sobre
    cualquier fondo. El texto se renderiza una vez (y otra si se le suma daño).
    """

    _fuentes = {}

    def __init__(self, centro, valor, color, tamano=settings.CIFRA_TAMANO):
        super().__init__()
        self.valor = int(valor)
        self.color = color
        self.tamano = tamano
        self.edad_ms = 0.0
        self._x = float(centro[0])
        self._y = float(centro[1])
        self._dibujar()

    @classmethod
    def _fuente(cls, tamano):
        if tamano not in cls._fuentes:
            cls._fuentes[tamano] = pygame.font.Font(None, tamano)
        return cls._fuentes[tamano]

    def _dibujar(self):
        fuente = self._fuente(self.tamano)
        texto = str(self.valor)
        frente = fuente.render(texto, True, self.color)
        borde = fuente.render(texto, True, (15, 15, 20))
        w, h = frente.get_size()
        superficie = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
        for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):      # contorno de 1 px
            superficie.blit(borde, (dx, dy))
        superficie.blit(frente, (1, 1))
        self.image = superficie
        self.rect = self.image.get_rect(center=(round(self._x), round(self._y)))

    def sumar(self, cantidad):
        """Suma daño a una cifra recién creada (varias balas en el mismo golpe)."""
        self.valor += int(cantidad)
        self._dibujar()

    def update(self, dt=0):
        self.edad_ms += dt * 1000
        if self.edad_ms >= settings.CIFRA_DURACION_MS:
            self.kill()
            return
        self._y -= settings.CIFRA_VELOCIDAD * dt
        self.rect.center = (round(self._x), round(self._y))
        # opaca la primera mitad, luego se desvanece
        mitad = settings.CIFRA_DURACION_MS / 2
        if self.edad_ms > mitad:
            self.image.set_alpha(round(255 * (1 - (self.edad_ms - mitad) / mitad)))
