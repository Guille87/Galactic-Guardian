import pygame

from .bala import Bala


class Jugador(pygame.sprite.Sprite):
    # Constantes de clase para configuración (Mantenible)
    CONFIG = {
        "tamano": (50, 50),
        "salud_max": 5,
        "vidas_init": 3,
        "vel_max": 6,
        "cadencia_max": 150,
        "danio_max": 3
    }

    def __init__(self, ruta_imagen, pantalla_ancho, pantalla_alto, grupo_sprites):
        super().__init__(grupo_sprites)
        # 1. Configuración de Imagen (Recibimos la ruta, pero cargamos vía Pygame o pasamos la superficie)
        # Nota: Idealmente el ResourceManager debería darte el Surface directamente
        self.image = pygame.transform.scale(pygame.image.load(ruta_imagen), self.CONFIG["tamano"])
        self.rect = self.image.get_rect(centerx=pantalla_ancho // 2, bottom=pantalla_alto - 10)

        # 2. Atributos de Estado (Estadísticas)
        self.vidas = self.CONFIG["vidas_init"]
        self.salud = self.CONFIG["salud_max"]
        self.salud_maxima = self.CONFIG["salud_max"]
        self.velocidad = 4
        self.danio = 1

        # 3. Sistema de Armas
        self.cadencia_disparo = 350
        self.ultimo_disparo = 0
        self.tipo_disparo = "simple"  # simple, doble, triple

        # 4. Estado Físico
        self.invulnerable = False
        self.tiempo_invulnerable = 0
        self.destello_constante = None
        self.radio = 16

    @property
    def danio_maximo(self):
        return self.CONFIG["danio_max"]

    @property
    def velocidad_maxima(self):
        return self.CONFIG["vel_max"]

    @property
    def cadencia_disparo_maxima(self):
        return self.CONFIG["cadencia_max"]

    def mover(self, teclas, pantalla):
        """Mueve al jugador según las teclas presionadas."""
        dx = (teclas[pygame.K_RIGHT] or teclas[pygame.K_d]) - (teclas[pygame.K_LEFT] or teclas[pygame.K_a])
        dy = (teclas[pygame.K_DOWN] or teclas[pygame.K_s]) - (teclas[pygame.K_UP] or teclas[pygame.K_w])

        self.rect.x += dx * self.velocidad
        self.rect.y += dy * self.velocidad

        # Obtenemos el rect de la superficie si es necesario
        if isinstance(pantalla, pygame.Surface):
            rect_limite = pantalla.get_rect()
        else:
            rect_limite = pantalla

        # Limita el movimiento del jugador para que no salga de los bordes de la pantalla
        self.rect.clamp_ip(rect_limite.inflate(-15, -45))

    def disparar(self, tiempo_actual, ruta_bala):
        """Lógica de control de tiempo para disparar."""
        if tiempo_actual - self.ultimo_disparo > self.cadencia_disparo:
            self.ultimo_disparo = tiempo_actual
            return self._generar_balas(ruta_bala)
        return []

    def _generar_balas(self, ruta_bala):
        """Crea las instancias de balas según el power-up actual."""
        balas = []
        # Ángulo por defecto (hacia arriba)
        angulo = 90

        pos_x = self.rect.centerx
        pos_y = self.rect.top + 10

        if self.tipo_disparo == "triple":
            offsets = [-15, 0, 15]
        elif self.tipo_disparo == "doble":
            offsets = [-10, 10]
        else:
            offsets = [0]

        for offset in offsets:
            b = Bala(ruta_bala, pos_x + offset, pos_y, self.danio)
            b.girar(angulo)
            balas.append(b)

        return balas

    def recibir_danio(self, cantidad):
        if not self.invulnerable:  # Verificar si la nave es vulnerable
            self.salud = max(0, self.salud - cantidad)
            return True
        return False

    def curar(self, cantidad):
        """
        Aumenta la salud del jugador.
        :param cantidad: Cantidad de salud que se va a aumentar.
        """
        self.salud = min(self.salud_maxima, self.salud + cantidad)

    def mejorar_danio(self, cantidad=1):
        # Evolución automática del tipo de disparo
        if self.danio < self.CONFIG["danio_max"]:
            self.danio += cantidad
        elif self.tipo_disparo == "simple":
            self.tipo_disparo = "doble"
        elif self.tipo_disparo == "doble":
            self.tipo_disparo = "triple"

    def mejorar_velocidad(self,cantidad=1):
        self.velocidad = min(self.CONFIG["vel_max"], self.velocidad + cantidad)

    def mejorar_cadencia(self, decremento):
        self.cadencia_disparo = max(self.CONFIG["cadencia_max"], self.cadencia_disparo - decremento)

    def reducir_vidas(self, cantidad):
        self.vidas = max(0, self.vidas - cantidad)

    def update(self):
        """Actualiza el estado del jugador en cada fotograma."""
        # Comprobar si la invulnerabilidad ha expirado
        if self.invulnerable and pygame.time.get_ticks() > self.tiempo_invulnerable:
            self.invulnerable = False
            if self.destello_constante:
                self.destello_constante.kill()
                self.destello_constante = None
